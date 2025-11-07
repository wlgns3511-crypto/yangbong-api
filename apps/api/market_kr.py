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
    네이버 지수 페이지에서 가격, 등락률, 등락액 파싱
    index_name: "KOSPI", "KOSDAQ", "KOSPI200" - 특정 지수를 위한 최적화된 파싱
    """
    
    result = {"price": None, "change": 0.0, "changeRate": 0.0}
    
    # 각 지수의 예상 가격 범위
    price_ranges = {
        "KOSPI": (2000, 5000),
        "KOSDAQ": (500, 1500),
        "KOSPI200": (300, 1000),
    }
    
    min_price, max_price = price_ranges.get(index_name, (200, 10000)) if index_name else (200, 10000)
    
    # ✅ 등락률 파싱: "72.69 -1.81%" 같은 패턴 찾기
    # 네이버 지수 페이지는 보통 "등락액 등락률%" 형식
    change_pattern = re.compile(
        r'([-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s+([-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)%',
        re.IGNORECASE
    )
    change_matches = change_pattern.findall(html)
    if change_matches:
        # 첫 번째 매치 사용 (보통 메인 지수 정보)
        change_str, rate_str = change_matches[0]
        result["change"] = _to_float(change_str) or 0.0
        result["changeRate"] = _to_float(rate_str) or 0.0
    
    # ✅ 가격 파싱: <em> 태그 내부의 큰 숫자 (네이버 지수 페이지 메인 가격)
    em_pattern = re.compile(r'<em[^>]*class="[^"]*no_today[^"]*"[^>]*>([^<]+)</em>', re.IGNORECASE)
    em_matches = em_pattern.findall(html)
    for content in em_matches:
        v = _to_float(content.strip())
        if v and min_price <= v <= max_price:
            result["price"] = v
            break
    
    # 가격을 못 찾았으면 기존 로직 사용
    if result["price"] is None:
        # 1) 테이블에서 <td> 또는 <th> 내부의 큰 숫자 찾기
        table_cell_pattern = re.compile(r'<t[dh][^>]*>([^<]*[\d,]+\.?\d*[^<]*)</t[dh]>', re.IGNORECASE)
        table_matches = table_cell_pattern.findall(html)
        
        for match in table_matches:
            num_str = re.search(r'([\d,]+\.?\d*)', match)
            if num_str:
                v = _to_float(num_str.group(1))
                if v and min_price <= v <= max_price:
                    result["price"] = v
                    break
        
        # 2) <strong> 태그 내부의 숫자 찾기
        if result["price"] is None:
            strong_pattern = re.compile(r'<strong[^>]*>([^<]+)</strong>', re.IGNORECASE)
            strong_matches = strong_pattern.findall(html)
            for content in strong_matches:
                v = _to_float(content.strip())
                if v and min_price <= v <= max_price:
                    result["price"] = v
                    break
        
        # 3) Fallback: 모든 숫자 중 적절한 범위 선택
        if result["price"] is None:
            all_numbers = []
            for s in re.findall(r"[\d,]+\.?\d*", html):
                v = _to_float(s)
                if v and min_price <= v <= max_price:
                    all_numbers.append(v)
            
            if all_numbers:
                decimal_nums = [v for v in all_numbers if v != int(v)]
                if decimal_nums:
                    result["price"] = max(decimal_nums)
                else:
                    sorted_nums = sorted(all_numbers)
                    mid_idx = len(sorted_nums) // 2
                    result["price"] = sorted_nums[mid_idx]
    
    return result



def fetch_from_naver() -> List[Dict[str, Any]]:

    out: List[Dict[str, Any]] = []

    for sym, url in K_NAV.items():

        try:

            r = requests.get(url, headers=UA, timeout=6)

            if r.status_code != 200:

                log.warning("naver %s %s", sym, r.status_code); continue

            d = _parse_naver(r.text, index_name=sym)

            price = d.get("price")
            change = d.get("change", 0.0)
            change_rate = d.get("changeRate", 0.0)

            # 가격이 유효하지 않으면 캐시에 쓰지 않게 skip

            if not isinstance(price, (int, float)) or price <= 0:

                log.warning("naver %s invalid price -> skip", sym)

                continue

            out.append({

                "symbol": sym,

                "name": sym,

                "price": float(price),

                "change": float(change),

                "changeRate": float(change_rate),

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
