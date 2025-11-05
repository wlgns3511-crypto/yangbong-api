"""
💰 암호화폐 시세 (Coingecko)
Author: Yangbong Club
Updated: 2025-11-05
"""

import requests
import time
import logging
from fastapi import APIRouter
from typing import Dict, Any, List
from .cache import upsert_market_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/market", tags=["market"])

COINS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "XRP": "ripple",
}


def get_crypto_prices() -> List[Dict[str, Any]]:
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": ",".join(COINS.values()), "vs_currencies": "usd"}
    try:
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        j = r.json()
        logger.info(f"[CG] Got response for {len(j)} coins")
    except Exception as e:
        logger.error(f"[CG] Coingecko error: {e}")
        return []

    results: List[Dict[str, Any]] = []
    for sym, cid in COINS.items():
        price = j.get(cid, {}).get("usd")
        if price and price > 0:
            result = {
                "market": "CRYPTO",
                "symbol": sym,
                "name": sym,
                "price": round(price, 2),
                "change": 0.0,
                "rate": 0.0,
                "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "source": "Coingecko",
            }
            results.append(result)
            upsert_market_data("CRYPTO", sym, price=round(price, 2))
            logger.info(f"✅ {sym} = {price}")
        else:
            logger.warning(f"⚠️ {sym} 값 없음")

    return results


def get_market_crypto() -> Dict[str, Any]:
    """암호화폐 시세 (비트코인, 이더리움, 리플)"""
    items = get_crypto_prices()
    return {"ok": True, "source": "Coingecko", "items": items}


@router.get("/crypto")
def market_crypto_endpoint() -> Dict[str, Any]:
    """암호화폐 전용 엔드포인트: /api/market/crypto"""
    return get_market_crypto()
