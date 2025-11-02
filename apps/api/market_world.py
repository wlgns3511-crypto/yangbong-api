# apps/api/market_world.py
from fastapi import APIRouter
from typing import List
import requests
import csv
import io
import time

router = APIRouter(prefix="/market", tags=["market"])

# 9종 기본 맵
INDEXES = [
    {"id": "DOW", "name": "다우", "stooq": "^dji", "yahoo": "^DJI"},
    {"id": "IXIC", "name": "나스닥", "stooq": "^ixic", "yahoo": "^IXIC"},
    {"id": "SPX", "name": "S&P500", "stooq": "^spx", "yahoo": "^GSPC"},
    {"id": "N225", "name": "니케이225", "stooq": "^n225", "yahoo": "^N225"},
    {"id": "SSEC", "name": "상해종합", "stooq": "^ssec", "yahoo": "000001.SS"},
    {"id": "HSI", "name": "항셍", "stooq": "^hsi", "yahoo": "^HSI"},
    {"id": "FTSE", "name": "영국FTSE100", "stooq": "^ftse", "yahoo": "^FTSE"},
    {"id": "CAC40", "name": "프랑스CAC40", "stooq": "^cac40", "yahoo": "^FCHI"},
    {"id": "DAX", "name": "독일DAX", "stooq": "^dax", "yahoo": "^GDAXI"},
]

# --- 간단 캐시(60초) ---
_cache = {"ts": 0, "data": None}
TTL = 60


def _stooq_batch(symbols: List[str]):
    url = "https://stooq.com/q/l/?s=" + ",".join(symbols) + "&i=d"
    r = requests.get(url, timeout=6)
    r.raise_for_status()
    # CSV: Symbol,Date,Time,Open,High,Low,Close,Volume
    out = {}
    rd = csv.reader(io.StringIO(r.text))
    for row in rd:
        if not row or row[0].lower() == "symbol":
            continue
        sym, *_rest = row
        try:
            close = float(row[6])
        except:
            close = None
        out[sym.lower()] = {"close": close}
    return out


def _yahoo_batch(symbols: List[str]):
    url = "https://query1.finance.yahoo.com/v7/finance/quote"
    r = requests.get(url, params={"symbols": ",".join(symbols)}, timeout=6)
    r.raise_for_status()
    j = r.json().get("quoteResponse", {}).get("result", [])
    out = {}
    for item in j:
        sym = item.get("symbol")
        close = item.get("regularMarketPrice")
        change = item.get("regularMarketChange")
        pct = item.get("regularMarketChangePercent")
        out[sym] = {"close": close, "change": change, "pct": pct}
    return out


@router.get("/world")
def world():
    # 캐시
    now = time.time()
    if _cache["data"] and now - _cache["ts"] < TTL:
        return _cache["data"]

    # 1) Stooq 배치
    stooq_syms = [i["stooq"] for i in INDEXES]
    stooq = {}
    try:
        stooq = _stooq_batch(stooq_syms)
    except Exception:
        stooq = {}

    # 2) Yahoo 보강
    yahoo = {}
    try:
        yahoo = _yahoo_batch([i["yahoo"] for i in INDEXES])
    except Exception:
        yahoo = {}

    data = []
    for idx in INDEXES:
        s_sym = idx["stooq"]
        y_sym = idx["yahoo"]

        close = None
        change = None
        pct = None

        # stooq close 우선
        if s_sym.lower() in stooq and stooq[s_sym.lower()]["close"] is not None:
            close = stooq[s_sym.lower()]["close"]

        # yahoo로 change/pct 보강 (그리고 close 비어있으면 yahoo 값 사용)
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

    # 캐시 저장
    _cache["ts"] = now
    _cache["data"] = {"ok": True, "source": "stooq>yahoo", "items": data}
    return _cache["data"]
