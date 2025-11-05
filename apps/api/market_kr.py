# apps/api/market_kr.py

from fastapi import APIRouter

from typing import List, Dict, Any

import logging

from .kis_client import get_index



router = APIRouter(prefix="/api/market", tags=["market"])

log = logging.getLogger("market.kr")



# ✅ 국내 지수 코드

IDX = [

    {"name": "KOSPI", "mrkt": "U", "code": "0001"},

    {"name": "KOSDAQ", "mrkt": "J", "code": "1001"},

    {"name": "KOSPI200", "mrkt": "U", "code": "2001"},

]





def _parse_kis_payload(j: Dict[str, Any]) -> Dict[str, Any]:

    """

    실시간 지수 데이터 구조 예시:

    {

      "rt_cd":"0",

      "msg_cd":"OPSP00000",

      "msg1":"정상처리되었습니다.",

      "output":{

        "bstp_nmix_prpr":"2499.53",

        "bstp_nmix_prdy_vrss":"-10.35",

        "bstp_nmix_prdy_ctrt":"-0.41",

        "stck_bsop_date":"20251105"

      }

    }

    """

    data = j.get("_json", {}).get("output")

    if not data:

        raise ValueError("kis_empty")



    return {

        "close": float(data.get("bstp_nmix_prpr", 0.0)),

        "change": float(data.get("bstp_nmix_prdy_vrss", 0.0)),

        "change_pct": float(data.get("bstp_nmix_prdy_ctrt", 0.0)),

        "date": data.get("stck_bsop_date", ""),

    }





@router.get("/kr")

def get_market_kr():

    results: List[Dict[str, Any]] = []

    miss: List[Dict[str, Any]] = []



    for it in IDX:

        name = it["name"]

        res = get_index(it["mrkt"], it["code"])



        if res.get("_http") != 200 or "_json" not in res:

            miss.append({"name": name, "status": res.get("_http", 0), "raw": res.get("_raw", res.get("_err", ""))})

            continue



        try:

            parsed = _parse_kis_payload(res)

            results.append({

                "name": name,

                "price": parsed["close"],

                "change": parsed["change"],

                "changeRate": parsed["change_pct"],

                "time": parsed["date"],

            })

        except Exception as e:

            miss.append({"name": name, "status": 200, "raw": f"parse_err:{e}"})



    if not results:

        return {"data": [], "error": "kis_no_data", "miss": miss}

    return {"data": results, "error": None, "miss": miss}





# ---------- 루트 디스패처 (404 방지용) ----------

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

    else:

        return {"data": [], "error": f"unknown_segment:{seg}"}
