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
    # 단, 현실적인 지수 가격 범위만 (200 ~ 10,000)

    em_pattern = re.compile(r'<em[^>]*>([^<]+)</em>', re.IGNORECASE)

    em_matches = em_pattern.findall(html)

    for match in em_matches:

        v = _to_float(match.strip())

        # 지수 가격 범위: 200 ~ 10,000 (거래량/거래대금 제외)
        if v and v >= 200 and v <= 10_000:

            return {"price": v}

    # 2) 언더스코어로 감싸진 숫자 찾기 (_4,026.45_ 형태)
    # 현실적인 지수 가격 범위만 (200 ~ 10,000)

    underscore_pattern = re.compile(r'_([\d,]+\.?\d*)_')

    underscore_matches = underscore_pattern.findall(html)

    for match in underscore_matches:

        v = _to_float(match)

        # 지수 가격 범위: 200 ~ 10,000
        if v and v >= 200 and v <= 10_000:

            return {"price": v}

    # 3) '코스피200' 또는 '코스피 200' 같은 패턴은 제외하고, 실제 가격만 찾기
    # 네이버 페이지에서 가격은 보통 테이블의 첫 번째 큰 숫자

    # "코스피200" 같은 텍스트에서 "200"을 추출하지 않도록 주의
    # 대신 "코스피200" 다음에 오는 큰 숫자(실제 가격)를 찾기

    index_pattern = re.compile(r'(코스피200|KOSPI200|코스닥|KOSPI|KOSDAQ)[^0-9]*([\d,]+\.?\d*)', re.IGNORECASE)

    index_matches = index_pattern.findall(html)

    for keyword, num_str in index_matches:

        v = _to_float(num_str)

        # "KOSPI200" 다음에 오는 "200"은 제외 (실제 가격은 100 이상이어야 함)
        # 하지만 KOSPI200의 실제 가격은 500대이므로 200은 제외
        if v and v > 200:  # 200보다 큰 값만 (KOSPI200의 실제 가격은 500대)

            return {"price": v}

    # 4) 마지막 fallback: 현실적인 지수 가격 범위만 선택
    # KOSPI: 2,000 ~ 5,000
    # KOSDAQ: 500 ~ 1,500  
    # KOSPI200: 300 ~ 1,000
    # 거래량(천만 단위), 거래대금(억 단위) 제외

    cand = []

    for s in re.findall(r"[\d,]+\.?\d*", html):

        v = _to_float(s)

        # 지수 가격의 현실적인 범위: 200 ~ 10,000
        # 거래량(17,919,022)이나 거래대금(199,430) 같은 큰 값 제외
        if v and v >= 200 and v <= 10_000:

            cand.append(v)

    if cand:

        # 가장 큰 값이 아니라, 적절한 범위 내의 값 선택
        # 보통 가격은 소수점이 있으므로, 소수점이 있는 값 우선
        # 없으면 중간값 정도 선택 (거래량/거래대금은 보통 정수)
        decimal_cand = [v for v in cand if v != int(v)]
        if decimal_cand:
            return {"price": max(decimal_cand)}
        # 소수점 없는 값만 있으면 중간값 선택
        if cand:
            sorted_cand = sorted(cand)
            mid_idx = len(sorted_cand) // 2
            return {"price": sorted_cand[mid_idx]}

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
