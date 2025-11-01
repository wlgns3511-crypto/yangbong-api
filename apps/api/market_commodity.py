# apps/api/market_commodity.py

from fastapi import APIRouter, Query
import httpx
import csv
import io
import time

router = APIRouter()
TTL = 60
_cache = {"ts": 0, "data": {}}

# 표시 항목 → stooq 심볼 매핑
# (금:XAUUSD, 은:XAGUSD 는 stooq에선 직접 심볼이 없어 대체 심볼 사용)
MAP = {
    "WTI": "cl.f",      # WTI 원유 선물
    "BRENT": "br.f",    # Brent 원유 선물
    "GOLD": "xauusd",   # 금(대체 소스: stooq JSON 미흡 시 야후로 교체 가능)
    "SILVER": "xagusd", # 은
    "COPPER": "hg.f",   # 구리 선물
}


def _stooq_single(symbol: str):
    # 단건 CSV
    url = f"https://stooq.com/q/l/?s={symbol}&f=sd2t2ohlcv&h&e=csv"
    return url


async def _fetch(symbol: str):
    async with httpx.AsyncClient(timeout=8.0) as client:
        r = await client.get(_stooq_single(symbol))
        r.raise_for_status()
        txt = r.text
        rows = list(csv.DictReader(io.StringIO(txt)))
        return rows[0] if rows else {}


def _norm(name: str, row: dict):
    # row 키: Symbol, Date, Time, Open, High, Low, Close, Volume
    try:
        close = float(row.get("Close") or 0.0)
        open_ = float(row.get("Open") or 0.0)
    except Exception:
        close, open_ = 0.0, 0.0
    chg = close - open_ if open_ else 0.0
    chg_pct = (chg / open_ * 100) if open_ else 0.0
    return {
        "symbol": name,
        "name": name,
        "price": close,
        "change": chg,
        "change_pct": chg_pct,
    }


@router.get("/market/commodity")
async def market_commodity(symbols: str = Query("WTI,BRENT,GOLD,SILVER,COPPER")):
    global _cache
    now = time.time()
    want = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    need = [MAP[s] for s in want if s in MAP]

    # 캐시 만료 시 갱신
    if now - _cache["ts"] > TTL:
        data = {}
        async with httpx.AsyncClient(timeout=8.0) as client:
            for disp, sym in MAP.items():
                try:
                    r = await client.get(_stooq_single(sym))
                    r.raise_for_status()
                    rows = list(csv.DictReader(io.StringIO(r.text)))
                    data[disp] = rows[0] if rows else {}
                except Exception:
                    data[disp] = {}
        _cache = {"ts": now, "data": data}

    items = [_norm(disp, _cache["data"].get(disp, {})) for disp in want if disp in MAP]
    return {"status": "ok", "type": "commodity", "items": items, "ts": int(now)}

