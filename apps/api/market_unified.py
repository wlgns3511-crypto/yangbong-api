# apps/api/market_unified.py
# 통합 마켓 API: /api/market?seg=KR|US&cache=0|1

from __future__ import annotations
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from typing import Any, Dict, List
from .market_common import is_fresh, now_ts, normalize_item
from .cache import load_cache, save_cache
from .market_kr import fetch_from_naver as fetch_kr
from .market_world import fetch_from_naver_world as fetch_us

router = APIRouter(prefix="/api/market", tags=["market"])


def _fetch(seg: str) -> List[Dict[str, Any]]:
    """세그먼트별 데이터 수집"""
    if seg == "KR":
        raw = fetch_kr()
        return [normalize_item(it) for it in raw if it.get("price") is not None]
    if seg == "US":
        raw = fetch_us()
        return [normalize_item(it) for it in raw if it.get("price") is not None]
    # TODO: crypto/commodity 있으면 여기에 추가
    return []


@router.get("")
def get_market(
    seg: str = Query("KR", description="KR/US/CRYPTO/CMDTY"),
    cache: int = Query(1, description="0이면 캐시 우회")
):
    """마켓 데이터 조회"""
    seg = seg.upper()
    cached = load_cache(seg) or {}
    items = cached.get("items") or []
    meta = cached.get("meta") or {}
    ts = meta.get("ts")
    
    # 캐시 사용 허용 + 신선 → 캐시 반환
    if cache != 0 and is_fresh(ts):
        return JSONResponse({
            "ok": True,
            "items": items,
            "source": "cache",
            "stale": False
        })
    
    # 라이브 수집
    live = _fetch(seg)
    
    # 유효하면 저장 후 반환
    if live:
        save_cache(seg, live, {"ts": now_ts(), "source": "live"})
        return JSONResponse({
            "ok": True,
            "items": live,
            "source": "live",
            "stale": False
        })
    
    # 라이브 실패 시 캐시라도 반환 (stale)
    return JSONResponse({
        "ok": True,
        "items": items,
        "source": "cache",
        "stale": True
    })
