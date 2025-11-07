# 통합 마켓 라우터: /api/market?seg=KR|US|CRYPTO|CMDTY

from fastapi import APIRouter, Query

from typing import Any, Dict, List

from .market_common import get_cache, set_cache, normalize_item

from .market_world import _get_world_logic

from .market_crypto import get_crypto

from .market_commodity import get_cmdty

from .market_kr import fetch_from_naver   # HTML 파싱 fallback
from apps.api.naver_indices import fetch_kr_indices   # JSON API 우선 사용



router = APIRouter(prefix="/api/market", tags=["market"])



@router.get("")

def market(seg: str = Query(..., regex="^(KR|US|CRYPTO|CMDTY)$"), cache: int = Query(1)):

    s = seg.upper()

    if s == "KR":

        # 캐시 확인

        cached, fresh = get_cache(s)

        if cache and cached:

            return {"ok": True, "items": cached, "stale": not fresh, "source": "cache"}



        # 네이버에서 데이터 가져오기 (JSON API 우선, HTML fallback)

        items: List[Dict[str, Any]] = []

        errors: List[str] = []



        # 1순위: 네이버 JSON API 사용

        import logging

        log = logging.getLogger("market.unified")

        codes = ["KOSPI", "KOSDAQ", "KPI200"]

        name_map = {"KOSPI": "KOSPI", "KOSDAQ": "KOSDAQ", "KPI200": "KOSPI200"}

        failed_codes = []

        try:

            data_map = fetch_kr_indices(codes)

            for code in codes:

                name = name_map[code]

                data = data_map.get(code, {})

                if data and data.get("price", 0) > 0:

                    items.append({"name": name, "symbol": name, **data})

                    log.info("naver_json: %s OK price=%.2f", code, data.get("price"))

                else:

                    log.warning("naver_json: %s returned empty or invalid data: %s", code, data)

                    failed_codes.append(code)

        except Exception as e:

            log.error("naver_json error: %s", e)

            errors.append(f"naver_json:{e}")

            failed_codes = codes  # 전체 실패로 간주



        # 2순위: JSON API에서 실패한 항목에 대해 HTML 파싱 fallback

        # JSON API가 일부만 성공했거나 전체 실패한 경우 HTML fallback 시도

        if failed_codes:

            try:

                log.info("naver_html fallback: fetching all indices (failed: %s)", failed_codes)

                nav = fetch_from_naver()

                if nav:

                    nav_items = [normalize_item(it) for it in nav]

                    # 가격이 None인 아이템 필터링

                    nav_items = [it for it in nav_items if it.get("price") is not None]

                    

                    # 기존 items와 병합 (중복 제거)

                    existing_symbols = {it.get("symbol") for it in items}

                    for nav_item in nav_items:

                        symbol = nav_item.get("symbol")

                        if symbol not in existing_symbols:

                            items.append(nav_item)

                            log.info("naver_html: added %s price=%.2f", symbol, nav_item.get("price"))

                        elif symbol in [name_map.get(c) for c in failed_codes]:

                            # 실패한 항목은 HTML 데이터로 교체

                            for i, existing in enumerate(items):

                                if existing.get("symbol") == symbol:

                                    items[i] = nav_item

                                    log.info("naver_html: replaced %s with HTML data price=%.2f", symbol, nav_item.get("price"))

                                    break

            except Exception as e:

                log.error("naver_html fallback error: %s", e)

                errors.append(f"naver_html:{e}")

        

        # JSON API가 완전히 실패한 경우에만 전체 HTML fallback

        if not items:

            try:

                log.info("naver_html: full fallback (no JSON data)")

                nav = fetch_from_naver()

                if nav:

                    items = [normalize_item(it) for it in nav]

                    # 가격이 None인 아이템 필터링

                    items = [it for it in items if it.get("price") is not None]

            except Exception as e:

                errors.append(f"naver_html:{e}")



        if items:

            # 정상 수집된 경우에만 캐시 갱신

            set_cache(s, items)

            return {"ok": True, "items": items, "stale": False, "source": "naver"}



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
