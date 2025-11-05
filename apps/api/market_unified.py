# 통합 마켓 라우터: /api/market?seg=KR|US|CRYPTO|CMDTY

from fastapi import APIRouter, Query



# 각 세그먼트 모듈에서 실제 핸들러 함수 import

from .market_kr import get_market_kr

from .market_world import get_world

from .market_crypto import get_crypto

from .market_commodity import get_cmdty



router = APIRouter(prefix="/api/market", tags=["market"])



@router.get("")

def market(seg: str = Query("KR")):

    s = seg.upper()

    if s == "KR":

        kr_result = get_market_kr()

        # get_market_kr()는 이미 items 키를 포함한 형식으로 반환

        return kr_result

    if s == "US":

        # get_world는 seg 파라미터를 받지만 여기서는 직접 호출하지 않고

        # market_world.py의 router에서 처리하도록 함

        # 하지만 통합 라우터에서 직접 처리하려면 아래처럼 호출

        return get_world(seg="US")

    if s in ("CMDTY", "CMTDY", "CM", "COMMODITY"):  # 오타 호환

        return get_cmdty(seg="CMDTY")

    if s in ("CRYPTO", "CRYP", "COIN"):

        return get_crypto(seg="CRYPTO")

    return {"ok": False, "items": [], "error": f"unknown_seg:{seg}"}
