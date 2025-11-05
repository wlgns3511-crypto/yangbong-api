# apps/api/market_kr.py

from fastapi import APIRouter

from typing import Any, Dict, List

import logging

from .kis_client import get_index

from .utils_yf import yf_quote_many



router = APIRouter(prefix="/api/market", tags=["market"])

log = logging.getLogger("market.kr")



IDX = [

    {"name": "KOSPI",   "mrkt": "U", "code": "0001", "yf": "^KS11"},

    {"name": "KOSDAQ",  "mrkt": "J", "code": "1001", "yf": "^KQ11"},

    {"name": "KOSPI200","mrkt": "U", "code": "2001", "yf": "^KS200"},

]



def _parse_kis_payload(j: Dict[str, Any]) -> Dict[str, Any] | None:

    out = j.get("_json", {}).get("output")

    if not out:

        return None

    return {

        "price": float(out.get("bstp_nmix_prpr", 0) or 0),

        "change": float(out.get("bstp_nmix_prdy_vrss", 0) or 0),

        "changeRate": float(out.get("bstp_nmix_prdy_ctrt", 0) or 0),

        "time": out.get("stck_bsop_date", ""),

    }



def _parse_yf_rows(rows: list[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:

    m: Dict[str, Dict[str, Any]] = {}

    for r in rows:

        sym = r.get("symbol")

        price = r.get("regularMarketPrice")

        chg = r.get("regularMarketChange")

        pct = r.get("regularMarketChangePercent")

        ts  = r.get("regularMarketTime")

        if price is None:

            continue

        m[sym] = {"price": float(price), "change": float(chg or 0), "changeRate": float(pct or 0), "time": ts}

    return m



@router.get("/kr")

def get_market_kr():

    results: List[Dict[str, Any]] = []

    miss: List[Dict[str, Any]] = []



    # 1) KIS 시도

    kis_ok = False

    for it in IDX:

        res = get_index(it["mrkt"], it["code"])

        if res.get("_http") == 200:

            parsed = _parse_kis_payload(res)

            if parsed and parsed["price"] > 0:

                results.append({"name": it["name"], **parsed})

                kis_ok = True

            else:

                miss.append({"name": it["name"], "status": 200, "raw": "parse_err:kis_empty"})

        else:

            miss.append({"name": it["name"], "status": res.get("_http", 0), "raw": res.get("_raw", "")})



    # 2) KIS 전부 실패/빈값이면 → YF 폴백

    if not results:

        rows = yf_quote_many([it["yf"] for it in IDX], retry=3)

        yfm = _parse_yf_rows(rows)

        for it in IDX:

            y = yfm.get(it["yf"])

            if y:

                results.append({"name": it["name"], **y})

            else:

                miss.append({"name": it["name"], "status": 0, "raw": "yf_no_data"})



    if not results:

        return {"data": [], "error": "kr_no_data", "miss": miss}

    return {"data": results, "error": None, "miss": miss}



# /api/market 루트 디스패처 (404 방지)

@router.get("")

def market_root(seg: str = "KR"):

    seg = (seg or "KR").upper()

    if seg == "KR":

        return get_market_kr()

    elif seg == "US":

        return {"data": [], "error": "us_api_not_ready"}

    elif seg in ("CRYPTO", "CRYPYO"):

        return {"data": [], "error": "crypto_api_not_ready"}

    elif seg in ("CMDTY", "COMMODITY"):

        return {"data": [], "error": "commodity_api_not_ready"}

    return {"data": [], "error": f"unknown_segment:{seg}"}
