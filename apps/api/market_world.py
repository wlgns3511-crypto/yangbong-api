"""
🌍 해외 지수 수집 (Yahoo Finance → 실패 시 Stooq 폴백)
Author: Yangbong Club
Updated: 2025-11-05
"""

import requests
import logging
import time
from fastapi import APIRouter
from typing import Dict, Any, List
from .cache import upsert_market_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/market", tags=["market"])

YF_SYMBOLS = {
    "DOW": "^DJI",
    "NASDAQ": "^IXIC",
    "S&P500": "^GSPC",
}

STOOQ_SYMBOLS = {
    "DOW": "US.DJI",
    "NASDAQ": "US.IXIC",
    "S&P500": "US.SP500",
}


def get_yf_quote(symbols: list[str]) -> dict[str, float]:
    url = "https://query1.finance.yahoo.com/v7/finance/quote"
    qs = ",".join(symbols)
    try:
        r = requests.get(f"{url}?symbols={qs}", timeout=5)
        r.raise_for_status()
        j = r.json()
        result = {}
        for it in j.get("quoteResponse", {}).get("result", []):
            symbol = it.get("symbol")
            price = it.get("regularMarketPrice")
            if symbol and price:
                result[symbol] = float(price)
        logger.info(f"[YF] Got {len(result)}/{len(symbols)} quotes")
        return result
    except Exception as e:
        logger.warning(f"[YF] Yahoo Finance error: {e}")
        return {}


def get_stooq_quote(symbol: str) -> float:
    try:
        url = f"https://stooq.com/q/l/?s={symbol}&f=l1"
        r = requests.get(url, timeout=5)
        if r.status_code == 200 and r.text.strip():
            price = float(r.text.strip())
            logger.info(f"[STOOQ] {symbol} = {price}")
            return price
    except Exception as e:
        logger.warning(f"[STOOQ] Error {symbol}: {e}")
    return 0.0


def get_market_world() -> Dict[str, Any]:
    """해외 지수 (다우, 나스닥, S&P500)"""
    results: List[Dict[str, Any]] = []
    yf = get_yf_quote(list(YF_SYMBOLS.values()))

    for name, sym in YF_SYMBOLS.items():
        price = yf.get(sym, 0)
        source = "YF"
        
        if not price or price == 0:
            logger.info(f"[STOOQ] Falling back for {name}")
            stooq = get_stooq_quote(STOOQ_SYMBOLS[name])
            price = stooq
            source = "STOOQ"

        if price and price != 0:
            result = {
                "market": "US",
                "symbol": name,
                "name": name,
                "price": round(price, 2),
                "change": 0.0,
                "rate": 0.0,
                "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "source": source,
            }
            results.append(result)
            upsert_market_data("US", name, price=round(price, 2))
            logger.info(f"✅ {name} ({source}) = {price}")
        else:
            logger.warning(f"⚠️ {name} 값 없음 (YF+Stooq 실패)")

    return {"ok": True, "source": "YF" if any(yf.values()) else "STOOQ", "items": results}


@router.get("/us")
def market_world_endpoint() -> Dict[str, Any]:
    """해외 지수 전용 엔드포인트: /api/market/us"""
    return get_market_world()
