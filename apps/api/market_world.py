# apps/api/market_world.py

from fastapi import APIRouter, Query

from typing import Any, Dict, List

import logging, requests

from .market_common import normalize_item
from .cache import get_cache, set_cache



log = logging.getLogger("market.us")

router = APIRouter(prefix="/api", tags=["market_world"])



UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}



U_NAV = {

    "DJI":  "https://finance.naver.com/world/sise.naver?symbol=DJI@DJI",

    "IXIC": "https://finance.naver.com/world/sise.naver?symbol=NAS@IXIC",

    "GSPC": "https://finance.naver.com/world/sise.naver?symbol=SPI@SPX",  # 필요시 다른 코드로 교체

}



def _scrape_world_data(url: str) -> Dict[str, Any]:
    """네이버 해외지수 페이지에서 가격, 등락률, 등락액 파싱"""
    r = requests.get(url, headers=UA, timeout=6)
    
    if r.status_code != 200:
        return {"price": 0.0, "change": 0.0, "changeRate": 0.0}
    
    import re
    html = r.text
    
    result = {"price": 0.0, "change": 0.0, "changeRate": 0.0}
    
    # ✅ 가격: <em class="no_today"> 태그 내부의 숫자
    em_pattern = re.compile(r'<em[^>]*class="[^"]*no_today[^"]*"[^>]*>([^<]+)</em>', re.IGNORECASE)
    em_matches = em_pattern.findall(html)
    for content in em_matches:
        v = _to_float(content.strip())
        if v and v > 0:
            result["price"] = v
            break
    
    # 가격을 못 찾았으면 첫 번째 큰 숫자 사용
    if result["price"] == 0.0:
        m = re.search(r"([-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)", html)
        if m:
            result["price"] = float(m.group(1).replace(",", ""))
    
    # ✅ 등락률 파싱: "등락액 등락률%" 패턴
    change_pattern = re.compile(
        r'([-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s+([-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)%',
        re.IGNORECASE
    )
    change_matches = change_pattern.findall(html)
    if change_matches:
        change_str, rate_str = change_matches[0]
        result["change"] = _to_float(change_str) or 0.0
        result["changeRate"] = _to_float(rate_str) or 0.0
    
    return result

def _to_float(txt: str):
    try:
        return float(txt.replace(',', '').strip())
    except Exception:
        return None



def fetch_from_naver_world() -> List[Dict[str, Any]]:

    out: List[Dict[str, Any]] = []

    for sym, url in U_NAV.items():

        try:

            data = _scrape_world_data(url)

            if data["price"] > 0:
                out.append({
                    "symbol": sym, 
                    "name": sym, 
                    "price": data["price"], 
                    "change": data["change"], 
                    "changeRate": data["changeRate"], 
                    "time": None
                })

        except Exception as e:

            log.warning("world err %s: %s", sym, e)

    return out



def _get_world_logic(seg: str = "US", cache: int = 1) -> Dict[str, Any]:
    """US 시장 데이터를 가져오는 실제 로직 (재사용 가능)"""
    seg = seg.upper()

    # cache=0이면 캐시 무시
    if cache != 0:
        cached, fresh = get_cache(seg)
        if cached:
            return {"ok": True, "items": cached, "stale": not fresh, "source": "cache"}
    else:
        cached, fresh = [], False  # 캐시 무시



    items: List[Dict[str, Any]] = []

    errors: List[str] = []



    try:

        us1 = fetch_from_naver_world()

        if us1: items = [normalize_item(it) for it in us1]

    except Exception as e:

        errors.append(f"naver:{e}")



    if items:

        set_cache(seg, items)

        return {"ok": True, "items": items, "stale": False, "source": "naver"}



    if cached:

        return {"ok": True, "items": cached, "stale": True, "source": "cache", "error": ";".join(errors) or "provider_fail"}



    return {"ok": False, "items": [], "error": "yf_no_data", "source": "YF"}



@router.get("/market")

def get_world(seg: str = Query("US"), cache: int = Query(1)) -> Dict[str, Any]:

    return _get_world_logic(seg, cache)
