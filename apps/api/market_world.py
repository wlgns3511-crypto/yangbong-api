# apps/api/market_world.py
from fastapi import APIRouter, Query
from typing import List
import requests
import csv
import io
import time
import logging
from .kis_client import get_overseas_price

router = APIRouter(prefix="/market", tags=["market"])

log = logging.getLogger("market_world")

ETF_MAP = [
    {"id": "DOW",  "name": "다우",     "excd": "NYS", "symb": "DIA"},
    {"id": "IXIC", "name": "나스닥100", "excd": "NAS", "symb": "QQQ"},
    {"id": "SPX",  "name": "S&P500",  "excd": "NYS", "symb": "SPY"},
    # TODO: 니케이/항셍/상해/FTSE/CAC/DAX는 master 코드 보고 EXCD/SYMB 확정
]

_cache = {"ts": 0, "data": None}
TTL = 60

# 기존 stooq/yahoo 백업용 (필요시 사용)
def _stooq_batch(symbols: List[str]):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; YangbongBot/1.0; +https://yangbong.club)"}
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
            close = None
        out[sym.lower()] = {"close": close}
    log.info(f"STOOQ filled {sum(1 for v in out.values() if v['close'] is not None)}/{len(symbols)}")
    return out

def _yahoo_batch(symbols: List[str]):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; YangbongBot/1.0; +https://yangbong.club)"}
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

    items = []
    for m in ETF_MAP:
        try:
            log.info(f"Fetching overseas: {m['id']} (excd={m['excd']}, symb={m['symb']})")
            p = get_overseas_price(m["excd"], m["symb"])
            items.append({
                "id": m["id"],
                "name": m["name"],
                "close": p["price"],
                "change": p["change"],
                "pct": p["pct"],
            })
            log.info(f"Success: {m['id']} price={p['price']}")
        except Exception as e:
            log.error(f"Error fetching {m['id']}: {e}", exc_info=True)
            items.append({
                "id": m["id"],
                "name": m["name"],
                "close": None,
                "change": None,
                "pct": None,
                "error": str(e)
            })

    payload = {"ok": True, "source": "kis(overseas-price)", "items": items}
    _cache["ts"] = now
    _cache["data"] = payload
    return payload
