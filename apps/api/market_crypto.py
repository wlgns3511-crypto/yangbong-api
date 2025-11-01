# apps/api/market_crypto.py

from fastapi import APIRouter, Query
import httpx
import time

router = APIRouter()

CG = "https://api.coingecko.com/api/v3/simple/price"

# 간단 TTL 캐시 (30초)
_cache = {"ts": 0, "data": None}
TTL = 30

# 표시 심볼 → coingecko id 매핑
MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "XRP": "ripple",
    "SOL": "solana",
    "BNB": "binancecoin",
}


async def _fetch(ids: list[str]):
    params = {
        "ids": ",".join(ids),
        "vs_currencies": "usd",
        "include_24hr_change": "true",
    }
    async with httpx.AsyncClient(timeout=8.0) as client:
        r = await client.get(CG, params=params)
        r.raise_for_status()
        return r.json()


def _norm(symbol: str, payload: dict):
    d = payload.get(MAP[symbol], {})
    price = float(d.get("usd") or 0.0)
    chg_pct = float(d.get("usd_24h_change") or 0.0)
    # 전일 종가 기준 단순 계산 (대략치)
    prev = price / (1 + chg_pct / 100) if price else 0.0
    chg = price - prev
    return {
        "symbol": symbol,
        "name": symbol,
        "price": price,
        "change": chg,
        "change_pct": chg_pct,
    }


@router.get("/market/crypto")
async def market_crypto(symbols: str = Query("BTC,ETH,XRP,SOL,BNB")):
    global _cache
    now = time.time()
    want = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    ids = [MAP[s] for s in want if s in MAP]

    if not ids:
        return {"status": "ok", "type": "crypto", "items": []}

    if now - _cache["ts"] > TTL or _cache["data"] is None:
        payload = await _fetch(list(set(ids)))
        _cache = {"ts": now, "data": payload}

    items = [_norm(s, _cache["data"]) for s in want if s in MAP]
    return {"status": "ok", "type": "crypto", "items": items, "ts": int(now)}

