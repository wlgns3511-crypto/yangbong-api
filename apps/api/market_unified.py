# 통합 마켓 라우터: /api/market?seg=KR|US|CRYPTO|CMDTY

from fastapi import APIRouter, Query

from .market_common import get_cache, set_cache, normalize_item

from .market_world import _get_world_logic

from .market_crypto import get_crypto

from .market_commodity import get_cmdty

from apps.api.naver_indices import fetch_kr_indices   # ← 새로 추가



router = APIRouter(prefix="/api/market", tags=["market"])



@router.get("")

def market(seg: str = Query(..., regex="^(KR|US|CRYPTO|CMDTY)$"), cache: int = Query(1)):

    s = seg.upper()

    if s == "KR":

        # 캐시 확인

        cached, fresh = get_cache(s)

        if cache and cached:

            return {"ok": True, "items": cached, "stale": not fresh, "source": "cache"}



        # 네이버에서 데이터 가져오기

        codes = ["KOSPI", "KOSDAQ", "KPI200"]

        name_map = {"KOSPI": "KOSPI", "KOSDAQ": "KOSDAQ", "KPI200": "KOSPI200"}

        data_map = fetch_kr_indices(codes)

        items = []

        errors = []



        for code in codes:

            name = name_map[code]

            data = data_map.get(code, {})

            if data and data.get("price", 0) > 0:

                items.append({"name": name, "symbol": name, **data})

            else:

                errors.append(f"{name}:naver_no_data")



        if items:

            # 정규화 후 캐시 저장

            normalized_items = [normalize_item(it) for it in items]

            set_cache(s, normalized_items)

            return {"ok": True, "items": normalized_items, "stale": False, "source": "naver"}



        # 공급자 실패 → 캐시라도 성공 처리

        if cached:

            return {"ok": True, "items": cached, "stale": True, "source": "cache", "error": ";".join(errors) or "provider_fail"}



        return {"ok": False, "items": [], "error": "kr_no_data", "miss": errors}



    if s == "US":

        # US 시장 데이터 가져오기 (캐시 로직 포함)

        return _get_world_logic(seg="US", cache=cache)



    if s in ("CMDTY", "CMTDY", "CM", "COMMODITY"):  # 오타 호환

        return get_cmdty(seg="CMDTY")



    if s in ("CRYPTO", "CRYP", "COIN"):

        return get_crypto(seg="CRYPTO")



    return {"ok": False, "items": [], "error": f"unknown_seg:{seg}"}
