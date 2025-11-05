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
        # kr: id, name, price, change, rate (market_kr.py에서 이미 정규화됨)
        # price와 close 둘 다 지원
        price = raw.get("price") or raw.get("close") or 0
        return {
            "market": "KR",
            "symbol": code,
            "name": raw.get("name") or code,
            "price": float(price),
            "change": float(raw.get("change") or 0),
            "rate": float(raw.get("rate") or raw.get("pct") or 0),  # 백엔드는 %로 반환
            "updatedAt": raw.get("updatedAt") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    elif market_type == "WORLD":
        # world: symbol, name, price, change, rate (market_world.py에서 이미 정규화됨)
        price = raw.get("price") or raw.get("close") or 0
        return {
            "market": "US",  # 해외는 US로 통일
            "symbol": code,
            "name": raw.get("name") or code,
            "price": float(price),
            "change": float(raw.get("change") or 0),
            "rate": float(raw.get("rate") or raw.get("pct") or 0),  # 백엔드는 %로 반환
            "updatedAt": raw.get("updatedAt") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    elif market_type == "CMD" or market_type == "COMMODITY":
        # commodity: symbol, name, price, change, rate (market_commodity.py에서 이미 정규화됨)
        price = raw.get("price") or raw.get("close") or 0
        return {
            "market": "CMD",
            "symbol": code,
            "name": raw.get("name") or code,
            "price": float(price),
            "change": float(raw.get("change") or 0),
            "rate": float(raw.get("rate") or raw.get("pct") or 0),
            "updatedAt": raw.get("updatedAt") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    else:  # CRYPTO
        # crypto: symbol, name, price, change, rate (market_crypto.py에서 이미 정규화됨)
        return {
            "market": "CRYPTO",
            "symbol": code,
            "name": raw.get("name") or code,
            "price": float(raw.get("price") or 0),
            "change": float(raw.get("change") or 0),
            "rate": float(raw.get("rate") or raw.get("change_pct") or 0),  # 백엔드는 %로 반환
            "updatedAt": raw.get("updatedAt") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }


@router.get("/market")
def market_unified(seg: str = Query("ALL", description="ALL|KR|US|CRYPTO|CMD"), filter: str = Query(None)):
    """통합 시세 API - 프론트 프록시용"""
    # seg와 filter 모두 지원 (seg 우선)
    actual_filter = seg if seg else (filter or "ALL")
    
    from .market_kr import get_market_kr
    from .market_world import get_market_world
    from .market_crypto import get_market_crypto
    from .market_commodity import get_market_commodity
    
    all_items = []
    
    # 국내 (KR)
    if actual_filter.upper() in ("ALL", "KR"):
        try:
            kr_data = get_market_kr()
            if kr_data.get("ok") and kr_data.get("items"):
                all_items.extend([_normalize_item("KR", it) for it in kr_data["items"]])
        except Exception as e:
            log.error(f"KR fetch error: {e}", exc_info=True)
    
    # 해외 (US/WORLD)
    if actual_filter.upper() in ("ALL", "US", "WORLD"):
        try:
            world_data = get_market_world()
            if world_data.get("ok") and world_data.get("items"):
                all_items.extend([_normalize_item("WORLD", it) for it in world_data["items"]])
        except Exception as e:
            log.error(f"World fetch error: {e}", exc_info=True)
    
    # 코인 (CRYPTO)
    if actual_filter.upper() in ("ALL", "CRYPTO"):
        try:
            crypto_data = get_market_crypto()
            if crypto_data.get("ok") and crypto_data.get("items"):
                all_items.extend([_normalize_item("CRYPTO", it) for it in crypto_data["items"]])
        except Exception as e:
            log.error(f"Crypto fetch error: {e}", exc_info=True)
    
    # 원자재 (CMD/COMMODITY)
    if actual_filter.upper() in ("ALL", "CMD", "COMMODITY"):
        try:
            commodity_data = get_market_commodity()
            if commodity_data.get("ok") and commodity_data.get("items"):
                all_items.extend([_normalize_item("CMD", it) for it in commodity_data["items"]])
        except Exception as e:
            log.error(f"Commodity fetch error: {e}", exc_info=True)
    
    # 프론트 호환성을 위해 items 키로 반환
    return {"items": all_items, "ok": True}


