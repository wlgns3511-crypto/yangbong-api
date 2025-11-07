# apps/api/market_kr.py

from __future__ import annotations

import re
import requests
from typing import Any, Dict, List
import logging
from fastapi import APIRouter, Query

# ✅ 캐시 유틸은 쓰지 않음. 여기서는 normalize_item만 필요
from .market_common import normalize_item



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



def _parse_naver(html: str, index_name: str = None) -> Dict[str, Any]:
    """
    네이버 지수 페이지에서 가격 파싱
    index_name: "KOSPI", "KOSDAQ", "KOSPI200" - 특정 지수를 위한 최적화된 파싱
    """
    
    # 각 지수의 예상 가격 범위
    price_ranges = {
        "KOSPI": (2000, 5000),
        "KOSDAQ": (500, 1500),
        "KOSPI200": (300, 1000),
    }
    
    min_price, max_price = price_ranges.get(index_name, (200, 10000)) if index_name else (200, 10000)
    
    # 1) 테이블에서 <td> 또는 <th> 내부의 큰 숫자 찾기
    # 네이버 지수 페이지는 보통 테이블 구조 사용
    table_cell_pattern = re.compile(r'<t[dh][^>]*>([^<]*[\d,]+\.?\d*[^<]*)</t[dh]>', re.IGNORECASE)
    table_matches = table_cell_pattern.findall(html)
    
    for match in table_matches:
        # 숫자 추출
        num_str = re.search(r'([\d,]+\.?\d*)', match)
        if num_str:
            v = _to_float(num_str.group(1))
            if v and min_price <= v <= max_price:
                return {"price": v}
    
    # 2) <em> 또는 <strong> 태그 내부의 숫자 찾기 (가격 강조 태그)
    em_pattern = re.compile(r'<(em|strong)[^>]*>([^<]+)</(em|strong)>', re.IGNORECASE)
    em_matches = em_pattern.findall(html)
    
    for tag, content, _ in em_matches:
        v = _to_float(content.strip())
        if v and min_price <= v <= max_price:
            return {"price": v}
    
    # 3) "코스피200", "KOSPI200" 등의 키워드 다음에 오는 숫자 찾기
    # 더 정확한 패턴: 키워드 뒤 500자 이내의 숫자 중 적절한 범위
    if index_name and "KOSPI200" in index_name.upper():
        # 코스피200 특화 파싱
        kospi200_pattern = re.compile(
            r'(?:코스피\s*200|KOSPI\s*200|KPI200)[^0-9]*?([\d,]+\.?\d*)',
            re.IGNORECASE
        )
        matches = kospi200_pattern.findall(html)
        for num_str in matches:
            v = _to_float(num_str)
            # 코스피200은 300~1000 범위
            if v and 300 <= v <= 1000:
                return {"price": v}
    
    # 4) 일반적인 인덱스 패턴 매칭
    index_keywords = {
        "KOSPI": r'(?:코스피|KOSPI)(?!\s*200)',
        "KOSDAQ": r'(?:코스닥|KOSDAQ)',
        "KOSPI200": r'(?:코스피\s*200|KOSPI\s*200|KPI200)',
    }
    
    if index_name and index_name.upper() in index_keywords:
        keyword = index_keywords[index_name.upper()]
        # 키워드 뒤 1000자 이내에서 숫자 찾기
        # 정규식 패턴을 문자열로 직접 구성 (f-string 사용 시 이스케이프 주의)
        pattern_str = keyword + r'[^0-9]{0,1000}?([\d,]{1,10}\.?\d*)'
        pattern = re.compile(pattern_str, re.IGNORECASE)
        matches = pattern.findall(html)
        for num_str in matches:
            v = _to_float(num_str)
            if v and min_price <= v <= max_price:
                return {"price": v}
    
    # 5) Fallback: 모든 숫자 중 적절한 범위 선택
    all_numbers = []
    for s in re.findall(r"[\d,]+\.?\d*", html):
        v = _to_float(s)
        if v and min_price <= v <= max_price:
            all_numbers.append(v)
    
    if all_numbers:
        # 소수점이 있는 값 우선 (가격은 보통 소수점 포함)
        decimal_nums = [v for v in all_numbers if v != int(v)]
        if decimal_nums:
            # 가장 큰 소수점 값 (보통 메인 가격)
            return {"price": max(decimal_nums)}
        # 소수점 없는 값만 있으면 중간값 선택
        sorted_nums = sorted(all_numbers)
        mid_idx = len(sorted_nums) // 2
        return {"price": sorted_nums[mid_idx]}
    
    # 실패
    return {"price": None}



def fetch_from_naver() -> List[Dict[str, Any]]:

    out: List[Dict[str, Any]] = []

    for sym, url in K_NAV.items():

        try:

            r = requests.get(url, headers=UA, timeout=6)

            if r.status_code != 200:

                log.warning("naver %s %s", sym, r.status_code); continue

            d = _parse_naver(r.text, index_name=sym)

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

    """레거시 엔드포인트 - market_unified.py 사용 권장"""

    seg = seg.upper()

    items: List[Dict[str, Any]] = []

    errors: List[str] = []



    try:

        nav = fetch_from_naver()

        if nav:

            items = [normalize_item(it) for it in nav]

    except Exception as e:

        errors.append(f"naver:{e}")



    if items:

        return {"ok": True, "items": items, "stale": False, "source": "naver"}



    return {"ok": False, "items": [], "error": "kr_no_data", "source": "KR"}
