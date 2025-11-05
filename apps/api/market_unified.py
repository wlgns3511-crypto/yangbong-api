# 통합 마켓 라우터: /api/market?seg=KR|US|CRYPTO|CMDTY

from fastapi import APIRouter, Query



# 각 세그먼트 모듈에서 실제 핸들러 함수 import

from .market_kr import get_market_kr

from .market_us import get_us_indices

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

        return {"ok": True, "source": "Yahoo", "items": get_us_indices()}

    if s in ("CMDTY", "CMTDY", "CM", "COMMODITY"):  # 오타 호환

        return {"ok": True, "source": "Yahoo", "items": get_cmdty()}

    if s in ("CRYPTO", "CRYP", "COIN"):

        return {"ok": True, "source": "Coingecko", "items": get_crypto()}

    return {"ok": False, "items": [], "error": f"unknown_seg:{seg}"}
