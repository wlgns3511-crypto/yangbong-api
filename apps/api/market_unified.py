# apps/api/market_unified.py
# 통합 마켓 API: /api/market?seg=KR|US&cache=0|1

from __future__ import annotations
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from typing import Any, Dict, List

# ✅ 캐시는 cache.py에서
from .cache import load_cache, save_cache
# ✅ 시간/신선도 유틸은 market_common에서
from .market_common import is_fresh, now_ts, normalize_item
from .market_crypto import fetch_crypto_markets

# 시장별 수집 함수
from .market_kr import fetch_from_naver as fetch_kr
from .market_world import fetch_from_naver_world as fetch_us

router = APIRouter(prefix="/api/market", tags=["market"])

# ✅ 캐시 차단 헤더 (전역 상수)
NO_STORE_HEADERS = {
    "Cache-Control": "no-store, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0"
}


def _fetch(seg: str) -> List[Dict[str, Any]]:
    """세그먼트별 데이터 수집"""
    if seg == "KR":
        raw = fetch_kr()
        return [normalize_item(it) for it in raw if it.get("price") is not None]
    if seg == "US":
        raw = fetch_us()
        return [normalize_item(it) for it in raw if it.get("price") is not None]
    if seg == "CRYPTO":
        try:
            return fetch_crypto_markets()
        except Exception:
            return []
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
        payload = {
            "ok": True,
            "items": items,
            "source": "cache",
            "stale": False,
            "ts": ts or now_ts(),  # ✅ 캐시 타임스탬프 또는 현재 시각
        }
        # 각 아이템에 time이 없으면 ts 세팅
        for it in payload["items"]:
            if not it.get("time"):
                it["time"] = payload["ts"]
        return JSONResponse(payload, headers=NO_STORE_HEADERS)
    
    # 라이브 수집
    live = _fetch(seg)
    
    # 유효하면 저장 후 반환
    if live:
        current_ts = now_ts()
        save_cache(seg, live, {"ts": current_ts, "source": "live"})
        
        # ✅ 응답 생성 시각(ts) 추가 + 각 아이템 time 채우기
        payload = {
            "ok": True,
            "items": live,
            "source": "live",
            "stale": False,
            "ts": current_ts,  # ✅ 응답 생성 시각 (epoch 초)
        }
        # 각 아이템에 time이 없으면 지금 시각 세팅
        for it in payload["items"]:
            if not it.get("time"):
                it["time"] = payload["ts"]
        
        return JSONResponse(payload, headers=NO_STORE_HEADERS)
    
    # ✅ 라이브 실패 시 캐시라도 반환 (stale 표시 유지)
    payload = {
        "ok": True,
        "items": items,
        "source": "cache",
        "stale": True,
        "ts": ts or now_ts(),  # ✅ 캐시 타임스탬프 또는 현재 시각
    }
    # 각 아이템에 time이 없으면 ts 세팅
    for it in payload["items"]:
        if not it.get("time"):
            it["time"] = payload["ts"]
    return JSONResponse(payload, headers=NO_STORE_HEADERS)
