# apps/api/market_unified.py
from fastapi import APIRouter, Query
import time
import logging
import asyncio

router = APIRouter(prefix="/api", tags=["market"])

log = logging.getLogger("market_unified")

# 통합 스키마: {market, symbol, name, price, change, rate, updatedAt}
def _normalize_item(market_type: str, raw: dict) -> dict:
    """백엔드 raw 응답을 통합 스키마로 변환"""
    code = raw.get("id") or raw.get("symbol") or ""
    
    if market_type == "KR":
        # kr: id, name, close, change, pct
        return {
            "market": "KR",
            "symbol": code,
            "name": raw.get("name") or code,
            "price": float(raw.get("close") or 0),
            "change": float(raw.get("change") or 0),
            "rate": float(raw.get("pct") or 0),  # 백엔드는 %로 반환
            "updatedAt": raw.get("updatedAt") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    elif market_type == "WORLD":
        # world: id, name, close, change, pct
        return {
            "market": "US",  # 해외는 US로 통일
            "symbol": code,
            "name": raw.get("name") or code,
            "price": float(raw.get("close") or 0),
            "change": float(raw.get("change") or 0),
            "rate": float(raw.get("pct") or 0),  # 백엔드는 %로 반환
            "updatedAt": raw.get("updatedAt") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    else:  # CRYPTO
        # crypto: symbol, name, price, change, change_pct
        return {
            "market": "CRYPTO",
            "symbol": code,
            "name": raw.get("name") or code,
            "price": float(raw.get("price") or 0),
            "change": float(raw.get("change") or 0),
            "rate": float(raw.get("change_pct") or 0),  # 백엔드는 %로 반환
            "updatedAt": raw.get("updatedAt") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }


@router.get("/market")
def market_unified(filter: str = Query("ALL", description="ALL|KR|US|CRYPTO")):
    """통합 시세 API - 프론트 프록시용"""
    from .market_kr import market_kr
    from .market_world import world
    from .market_crypto import market_crypto
    
    all_items = []
    
    # 국내 (KR)
    if filter in ("ALL", "KR"):
        try:
            kr_data = market_kr(cache=1)
            if kr_data.get("ok") and kr_data.get("items"):
                all_items.extend([_normalize_item("KR", it) for it in kr_data["items"]])
        except Exception as e:
            log.error(f"KR fetch error: {e}")
    
    # 해외 (US/WORLD)
    if filter in ("ALL", "US", "WORLD"):
        try:
            world_data = world(cache=1)
            if world_data.get("ok") and world_data.get("items"):
                all_items.extend([_normalize_item("WORLD", it) for it in world_data["items"]])
        except Exception as e:
            log.error(f"World fetch error: {e}")
    
    # 코인 (CRYPTO)
    if filter in ("ALL", "CRYPTO"):
        try:
            crypto_data = asyncio.run(market_crypto("BTC,ETH,XRP"))
            if crypto_data.get("status") == "ok" and crypto_data.get("items"):
                all_items.extend([_normalize_item("CRYPTO", it) for it in crypto_data["items"]])
        except Exception as e:
            log.error(f"Crypto fetch error: {e}")
    
    return all_items


