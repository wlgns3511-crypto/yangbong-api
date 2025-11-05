"""
📊 Market 통합 엔드포인트 (KR + US + CRYPTO + CMD)
Author: Yangbong Club
Updated: 2025-11-05
"""

import time
import logging
from fastapi import APIRouter, Query
from typing import Dict, Any, List, Optional

from .market_kr import get_market_kr
from .market_world import get_market_world
from .market_crypto import get_market_crypto
from .market_commodity import get_market_commodity

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["market"])


# ------------------------------------------------------------------------
# 🧩 공용 함수
# ------------------------------------------------------------------------

def safe_fetch(fn, *args, **kwargs) -> List[Dict[str, Any]]:
    """안전하게 개별 수집 실행"""
    try:
        result = fn(*args, **kwargs)
        # 응답 형식 통일: {ok: True, items: [...]} 또는 리스트
        if isinstance(result, dict):
            return result.get("items", [])
        elif isinstance(result, list):
            return result
        else:
            logger.warning(f"[safe_fetch] Unexpected result type from {fn.__name__}: {type(result)}")
            return []
    except Exception as e:
        logger.error(f"[safe_fetch] {fn.__name__} error: {e}", exc_info=True)
        return []


def merge_market_data(*segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """서브 리스트들을 하나로 합침"""
    merged: List[Dict[str, Any]] = []
    for seg in segments:
        if isinstance(seg, list):
            merged.extend(seg)
    return merged


# ------------------------------------------------------------------------
# 🌍 API 엔드포인트
# ------------------------------------------------------------------------

@router.get("/market")
def get_market(seg: Optional[str] = Query(None, description="시장 구분 (KR, US, CRYPTO, CMD)")):
    """
    통합 시세 API
    
    - seg 값이 없으면 전체(KR+US+CRYPTO+CMD)를 반환
    - 예: /api/market?seg=KR
    """
    start = time.time()
    items: List[Dict[str, Any]] = []

    # 시장 구분별 처리
    seg_upper = seg.upper() if seg else "ALL"
    
    if seg_upper == "KR":
        items = safe_fetch(get_market_kr)
    elif seg_upper == "US":
        items = safe_fetch(get_market_world)
    elif seg_upper == "CRYPTO":
        items = safe_fetch(get_market_crypto)
    elif seg_upper == "CMD":
        items = safe_fetch(get_market_commodity)
    else:
        # 전체 통합 (seg가 None이거나 "ALL")
        kr_items = safe_fetch(get_market_kr)
        us_items = safe_fetch(get_market_world)
        crypto_items = safe_fetch(get_market_crypto)
        cmd_items = safe_fetch(get_market_commodity)
        
        items = merge_market_data(kr_items, us_items, crypto_items, cmd_items)

    elapsed = round(time.time() - start, 2)
    
    logger.info(f"[MARKET] seg={seg_upper}, count={len(items)}, elapsed={elapsed}s")

    return {
        "items": items,
        "ok": True,
        "count": len(items),
        "elapsed": elapsed,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

