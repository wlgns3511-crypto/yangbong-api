# apps/api/market_kr.py

from fastapi import APIRouter

from typing import List, Dict, Any

import logging



from .kis_client import get_index



router = APIRouter(prefix="/api/market", tags=["market"])

log = logging.getLogger("market.kr")

log.setLevel(logging.INFO)



# KIS 지수 코드 매핑

IDX = [

    {"name": "KOSPI",   "mrkt": "U", "code": "0001"},

    {"name": "KOSDAQ",  "mrkt": "J", "code": "1001"},

    {"name": "KOSPI200","mrkt": "U", "code": "2001"},

]



def _parse_kis_payload(j: Dict[str, Any]) -> Dict[str, Any]:

    """

    KIS 지수 차트 응답은 표준화가 들쑥날쑥하다.

    가장 최근 봉을 선택해서, 종가/전일대비(%) 정도만 가볍게 뽑는다.

    가용키 예시:

      j["_json"]["output2"] : 일자별 OHLC 리스트 (가장 마지막 요소가 가장 최근)

      j["_json"]["output1"] : 기준일/지수명 등 메타

    """

    if "_json" not in j:

        raise ValueError("kis_no_json")



    output2 = j["_json"].get("output2") or []

    if not isinstance(output2, list) or not output2:

        raise ValueError("kis_empty")



    last = output2[-1]

    # 키 이름은 문서/버전에 따라 다를 수 있음 -> 보편적으로 쓰이는 후보만 안전 추출

    close = last.get("stck_prpr") or last.get("cmpprevdd_prc") or last.get("prpr") or last.get("close") or ""

    chg   = last.get("prdy_ctrt") or last.get("flt_rt") or last.get("rate") or ""  # %

    date  = last.get("stck_bsop_date") or last.get("bas_dt") or last.get("date") or ""



    return {

        "close": close,

        "change_pct": chg,

        "date": date,

    }



@router.get("/kr")

def get_market_kr():

    data: List[Dict[str, Any]] = []

    miss: List[Dict[str, Any]] = []



    for it in IDX:

        name = it["name"]

        res = get_index(it["mrkt"], it["code"])



        if res.get("_http") != 200 or "_json" not in res:

            miss.append({"name": name, "status": res.get("_http", 0), "raw": res.get("_raw", res.get("_err", ""))})

            continue



        try:

            parsed = _parse_kis_payload(res)

            data.append({

                "name": name,

                "close": parsed["close"],

                "change_pct": parsed["change_pct"],

                "date": parsed["date"],

            })

        except Exception as e:

            miss.append({"name": name, "status": 200, "raw": f"parse_err:{e}"})



    if not data:

        # 프론트가 깨지지 않도록 고정 포맷 유지

        return {"data": [], "error": "kis_no_data", "miss": miss}



    return {"data": data, "error": None, "miss": miss}





# ---------- 루트 디스패처 (404 방지용 임시 처리) ----------



@router.get("")

def market_root(seg: str = "KR"):

    seg = (seg or "KR").upper()

    if seg == "KR":

        return get_market_kr()

    elif seg == "US":

        return {"data": [], "error": "us_api_not_ready"}

    elif seg in ("CRYPTO", "CRYPTO"):

        return {"data": [], "error": "crypto_api_not_ready"}

    elif seg in ("CMDTY", "COMMODITY"):

        return {"data": [], "error": "commodity_api_not_ready"}

    else:

        return {"data": [], "error": f"unknown_segment:{seg}"}
