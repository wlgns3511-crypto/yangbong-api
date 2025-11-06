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

    text = html  # HTML 파싱 없이 텍스트로 처리 (BeautifulSoup 의존성 제거)

    # 1) '현재가/지수/종가' 같은 단어 주변 우선 추출

    m = re.search(r"(현재|지수|종가)\D*([-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)", text)

    if m:

        v = _to_float(m.group(2))

        if v and v > 0:

            return {"price": v}

    # 2) 숫자 전부 수집 후 '양수이면서 가장 큰 값'을 가격 후보로

    cand = []

    for s in re.findall(r"-?\d{1,3}(?:,\d{3})*(?:\.\d+)?", text):

        v = _to_float(s)

        if v and v > 0:

            cand.append(v)

    if cand:

        # 변화량(보통 절대값이 작음)보다 가격(절대값 큼)을 선택

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
