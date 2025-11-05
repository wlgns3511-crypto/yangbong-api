# apps/api/market_world.py

from fastapi import APIRouter, Query

from .utils_yf import yf_quote



router = APIRouter(prefix="/api", tags=["market_world"])



# 네이버/야후 관용 심볼 매핑 (야후 기준)

WORLD_SYMBOLS = [

    {"name": "다우",      "symbol": "^DJI"},

    {"name": "나스닥",    "symbol": "^IXIC"},

    {"name": "S&P500",   "symbol": "^GSPC"},

    {"name": "니케이225","symbol": "^N225"},

    {"name": "상해종합",  "symbol": "000001.SS"},   # 또는 ^SSEC

    {"name": "항셍",     "symbol": "^HSI"},

    {"name": "영국 FTSE","symbol": "^FTSE"},

    {"name": "프랑스 CAC","symbol": "^FCHI"},

    {"name": "독일 DAX", "symbol": "^GDAXI"},

]



@router.get("/market")

def get_world(seg: str = Query("", alias="seg")):

    if seg.upper() != "US":

        return {"ok": False, "error": "bad_seg"}

    symbols = [x["symbol"] for x in WORLD_SYMBOLS]

    try:

        items = yf_quote(symbols)

    except Exception:

        items = []

    # 이름 매핑 덮어쓰기

    name_by_symbol = {x["symbol"]: x["name"] for x in WORLD_SYMBOLS}

    for it in items:

        it["name"] = name_by_symbol.get(it["symbol"], it.get("name", it["symbol"]))

    if not items:

        return {"ok": False, "items": [], "error": "yf_no_data", "source": "YF"}

    return {"ok": True, "source": "YF", "items": items}
