# apps/api/market_world.py
from fastapi import APIRouter, Query
from typing import List
import requests
import csv
import io
import time
import logging

router = APIRouter(prefix="/market", tags=["market"])

log = logging.getLogger("market_world")
headers = {"User-Agent": "Mozilla/5.0 (compatible; YangbongBot/1.0; +https://yangbong.club)"}

INDEXES = [
    {"id": "DOW",  "name": "다우",        "stooq": "^dji",   "yahoo": "^DJI"},
    {"id": "IXIC", "name": "나스닥",      "stooq": "^ixic",  "yahoo": "^IXIC"},
    {"id": "SPX",  "name": "S&P500",     "stooq": "^spx",   "yahoo": "^GSPC"},
    {"id": "N225", "name": "니케이225",   "stooq": "^n225",  "yahoo": "^N225"},
    {"id": "SSEC", "name": "상해종합",    "stooq": "^ssec",  "yahoo": "000001.SS"},
    {"id": "HSI",  "name": "항셍",        "stooq": "^hsi",   "yahoo": "^HSI"},
    {"id": "FTSE", "name": "영국FTSE100", "stooq": "^ftse",  "yahoo": "^FTSE"},
    {"id": "CAC40","name": "프랑스CAC40", "stooq": "^cac40", "yahoo": "^FCHI"},
    {"id": "DAX",  "name": "독일DAX",     "stooq": "^dax",   "yahoo": "^GDAXI"},
]

_cache = {"ts": 0, "data": None}
TTL = 60

def _stooq_batch(symbols: List[str]):
    url = "https://stooq.com/q/l/?s=" + ",".join(symbols) + "&i=d"
    r = requests.get(url, timeout=6, headers=headers)
    r.raise_for_status()
    out = {}
    rd = csv.reader(io.StringIO(r.text))
    for row in rd:
        if not row or row[0].lower() == "symbol":
            continue
        sym = row[0]
        try:
            close = float(row[6])
        except Exception:
            close = None  # N/D 등
        out[sym.lower()] = {"close": close}
    log.info(f"STOOQ filled {sum(1 for v in out.values() if v['close'] is not None)}/{len(symbols)}")
    return out

def _yahoo_batch(symbols: List[str]):
    url = "https://query1.finance.yahoo.com/v7/finance/quote"
    r = requests.get(url, params={"symbols": ",".join(symbols)}, timeout=6, headers=headers)
    r.raise_for_status()
    result = r.json().get("quoteResponse", {}).get("result", [])
    out = {}
    for item in result:
        sym = item.get("symbol")
        if not sym:
            continue
        out[sym] = {
            "close": item.get("regularMarketPrice"),
            "change": item.get("regularMarketChange"),
            "pct": item.get("regularMarketChangePercent"),
        }
    log.info(f"YAHOO filled {len(out)}/{len(symbols)}")
    return out

@router.get("/world")
def world(cache: int = Query(default=1, description="0=강제갱신")):
    now = time.time()
    if cache and _cache["data"] and now - _cache["ts"] < TTL:
        return _cache["data"]

    stooq_syms = [i["stooq"] for i in INDEXES]
    yahoo_syms = [i["yahoo"] for i in INDEXES]

    stooq = {}
    yahoo = {}
    source = []

    try:
        stooq = _stooq_batch(stooq_syms)
        source.append("stooq")
    except Exception as e:
        log.warning(f"stooq error: {e}")

    try:
        yahoo = _yahoo_batch(yahoo_syms)
        source.append("yahoo")
    except Exception as e:
        log.warning(f"yahoo error: {e}")

    data = []
    for idx in INDEXES:
        s_sym = idx["stooq"].lower()
        y_sym = idx["yahoo"]

        close = None
        change = None
        pct = None

        if s_sym in stooq and stooq[s_sym]["close"] is not None:
            close = stooq[s_sym]["close"]

        yrow = yahoo.get(y_sym)
        if yrow:
            change = yrow.get("change", change)
            pct = yrow.get("pct", pct)
            if close is None:
                close = yrow.get("close")

        data.append({
            "id": idx["id"],
            "name": idx["name"],
            "close": close,
            "change": change,
            "pct": pct,
        })

    payload = {"ok": True, "source": ">".join(source) or "none", "items": data}
    _cache["ts"] = now
    _cache["data"] = payload
    return payload
