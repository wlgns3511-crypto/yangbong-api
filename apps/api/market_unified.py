# 통합 마켓 라우터: /api/market?seg=KR|US|CRYPTO|CMDTY

from fastapi import APIRouter, Query

from apps.api.naver_indices import fetch_kr_indices   # ← 새로 추가



# 각 세그먼트 모듈에서 실제 핸들러 함수 import

from .market_world import get_world

from .market_crypto import get_crypto

from .market_commodity import get_cmdty



router = APIRouter(prefix="/api/market", tags=["market"])



@router.get("")

def market(seg: str = Query(..., regex="^(KR|US|CRYPTO|CMDTY)$")):

    s = seg.upper()

    if s == "KR":

        # ✅ KIS/YF 완전 제외, 네이버 1순위로 바로 응답

        codes = ["KOSPI", "KOSDAQ", "KPI200"]

        name_map = {"KOSPI": "KOSPI", "KOSDAQ": "KOSDAQ", "KPI200": "KOSPI200"}

        data_map = fetch_kr_indices(codes)

        items = []

        miss = []

        for code in codes:

            name = name_map[code]

            data = data_map.get(code, {})

            if data and data.get("price", 0) > 0:

                items.append({"name": name, **data})

            else:

                miss.append({"name": name, "status": 0, "raw": "naver_no_data"})

        if not items:

            return {"ok": False, "items": [], "error": "kr_no_data", "miss": miss}

        return {"ok": True, "items": items, "error": None, "miss": miss}

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
