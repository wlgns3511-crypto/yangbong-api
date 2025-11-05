# 통합 마켓 라우터: /api/market?seg=KR|US|CRYPTO|CMDTY

from fastapi import APIRouter, Query



# 각 세그먼트 모듈에서 실제 핸들러 함수 import

# (파일 내 함수명이 다르면 아래 호출부만 이름 맞춰 주세요.)

from .market_kr import get_market_kr

from .market_world import get_market_world

from .market_crypto import get_market_crypto

from .market_commodity import get_market_commodity



router = APIRouter(prefix="/api/market", tags=["market"])



@router.get("")

def market(seg: str = Query("KR")):

    s = seg.upper()

    if s == "KR":

        return get_market_kr()

    if s == "US":

        return get_market_world()

    if s in ("CRYPTO", "CRYP", "COIN"):

        return get_market_crypto()

    if s in ("CMDTY", "CM", "COMMODITY"):

        return get_market_commodity()

    return {"data": [], "error": f"unknown_seg:{seg}"}
