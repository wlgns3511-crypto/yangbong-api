# apps/api/market_world.py

from fastapi import APIRouter, Query

from typing import Any, Dict, List

import logging, requests

from .market_common import get_cache, set_cache, normalize_item



log = logging.getLogger("market.us")

router = APIRouter(prefix="/api", tags=["market_world"])



UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}



U_NAV = {

    "DJI":  "https://finance.naver.com/world/sise.naver?symbol=DJI@DJI",

    "IXIC": "https://finance.naver.com/world/sise.naver?symbol=NAS@IXIC",

    "GSPC": "https://finance.naver.com/world/sise.naver?symbol=SPI@SPX",  # 필요시 다른 코드로 교체

}



def _scrape_price(url: str) -> float:

    r = requests.get(url, headers=UA, timeout=6)

    if r.status_code != 200: return 0.0

    import re

    m = re.search(r"[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?", r.text)

    return float(m.group(0).replace(",", "")) if m else 0.0



def fetch_from_naver_world() -> List[Dict[str, Any]]:

    out: List[Dict[str, Any]] = []

    for sym, url in U_NAV.items():

        try:

            price = _scrape_price(url)

            out.append({"symbol": sym, "name": sym, "price": price, "change": 0, "changeRate": 0, "time": None})

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
