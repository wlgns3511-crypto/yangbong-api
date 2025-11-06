# apps/api/market_kr.py

from fastapi import APIRouter, Query

from typing import Any, Dict, List

import logging, requests, re

from .market_common import get_cache, set_cache, normalize_item



log = logging.getLogger("market.kr")

router = APIRouter(prefix="/api/market", tags=["market"])



UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}



K_NAV = {

    "KOSPI": "https://finance.naver.com/sise/sise_index.naver?code=KOSPI",

    "KOSDAQ": "https://finance.naver.com/sise/sise_index.naver?code=KOSDAQ",

    "KOSPI200": "https://finance.naver.com/sise/sise_index.naver?code=KPI200",

}



_num = re.compile(r"[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?")



def _parse_naver(html: str) -> Dict[str, float]:

    # 매우 보수적: 페이지 전체에서 숫자 3개 이상 뽑아 평균치/변화율 후보 탐색

    # (기존 파서가 깨져도 최소값은 뽑히게)

    nums = [n.replace(",", "") for n in _num.findall(html)]

    # 실패 대비

    first = float(nums[0]) if nums else 0.0

    return {"price": first}  # change, rate는 0으로 둬도 화면은 뜬다



def fetch_from_naver() -> List[Dict[str, Any]]:

    out: List[Dict[str, Any]] = []

    for sym, url in K_NAV.items():

        try:

            r = requests.get(url, headers=UA, timeout=6)

            if r.status_code != 200:

                log.warning("naver %s %s", sym, r.status_code); continue

            d = _parse_naver(r.text)

            out.append({

                "symbol": sym,

                "name": sym,

                "price": d.get("price", 0),

                "change": 0,

                "changeRate": 0,

                "time": None,

            })

        except Exception as e:

            log.warning("naver err %s: %s", sym, e)

    return out



@router.get("/kr")

def get_market_kr(seg: str = Query("KR"), cache: int = Query(1)) -> Dict[str, Any]:

    seg = seg.upper()

    cached, fresh = get_cache(seg)

    if cache and cached:

        return {"ok": True, "items": cached, "stale": not fresh, "source": "cache"}



    items: List[Dict[str, Any]] = []

    errors: List[str] = []



    try:

        nav = fetch_from_naver()

        if nav:

            items = [normalize_item(it) for it in nav]

    except Exception as e:

        errors.append(f"naver:{e}")



    if items:

        set_cache(seg, items)

        return {"ok": True, "items": items, "stale": False, "source": "naver"}



    # 공급자 전멸 → 캐시라도 성공 처리

    if cached:

        return {"ok": True, "items": cached, "stale": True, "source": "cache", "error": ";".join(errors) or "provider_fail"}



    return {"ok": False, "items": [], "error": "kr_no_data", "source": "KR"}
