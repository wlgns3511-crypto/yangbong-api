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



def _to_float(txt: str):

    try:

        return float(txt.replace(',', '').strip())

    except Exception:

        return None



def _parse_naver(html: str) -> Dict[str, Any]:

    # 네이버 페이지에서 가격은 보통 <em> 태그나 특정 클래스에 있음
    # 예: <em>4,026.45</em> 또는 _4,026.45_ 형태

    # 1) <em> 태그 내부의 큰 숫자 찾기 (가격 후보)

    em_pattern = re.compile(r'<em[^>]*>([^<]+)</em>', re.IGNORECASE)

    em_matches = em_pattern.findall(html)

    for match in em_matches:

        v = _to_float(match.strip())

        if v and v > 100:  # 가격은 보통 100 이상

            return {"price": v}

    # 2) 언더스코어로 감싸진 숫자 찾기 (_4,026.45_ 형태)

    underscore_pattern = re.compile(r'_([\d,]+\.?\d*)_')

    underscore_matches = underscore_pattern.findall(html)

    for match in underscore_matches:

        v = _to_float(match)

        if v and v > 100:

            return {"price": v}

    # 3) '코스피' 또는 '코스닥' 키워드 주변의 큰 숫자 찾기

    index_pattern = re.compile(r'(코스피|코스닥|KOSPI|KOSDAQ)[^0-9]*([\d,]+\.?\d*)', re.IGNORECASE)

    index_matches = index_pattern.findall(html)

    for _, num_str in index_matches:

        v = _to_float(num_str)

        if v and v > 100:

            return {"price": v}

    # 4) 마지막 fallback: 양수 중 가장 큰 값 (100 이상만)

    cand = []

    for s in re.findall(r"[\d,]+\.?\d*", html):

        v = _to_float(s)

        if v and v >= 100 and v < 10_000_000:  # 현실적인 범위

            cand.append(v)

    if cand:

        return {"price": max(cand)}

    # 실패

    return {"price": None}



def fetch_from_naver() -> List[Dict[str, Any]]:

    out: List[Dict[str, Any]] = []

    for sym, url in K_NAV.items():

        try:

            r = requests.get(url, headers=UA, timeout=6)

            if r.status_code != 200:

                log.warning("naver %s %s", sym, r.status_code); continue

            d = _parse_naver(r.text)

            price = d.get("price")

            # 가격이 유효하지 않으면 캐시에 쓰지 않게 skip

            if not isinstance(price, (int, float)) or price <= 0:

                log.warning("naver %s invalid price -> skip", sym)

                continue

            out.append({

                "symbol": sym,

                "name": sym,

                "price": float(price),

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
