# apps/api/market_commodity.py

from fastapi import APIRouter, Query

from .utils_yf import yf_quote



router = APIRouter(prefix="/api", tags=["market_commodity"])



CMDTY_SYMBOLS = [

    {"name": "금",    "symbol": "GC=F"},

    {"name": "은",    "symbol": "SI=F"},

    {"name": "WTI",  "symbol": "CL=F"},

    {"name": "브렌트","symbol": "BZ=F"},  # 또는 CO=F

]



@router.get("/market")

def get_cmdty(seg: str = Query("", alias="seg")):

    if seg.upper() != "CMDTY":

        return {"ok": False, "error": "bad_seg"}

    symbols = [x["symbol"] for x in CMDTY_SYMBOLS]

    items = yf_quote(symbols)

    name_by_symbol = {x["symbol"]: x["name"] for x in CMDTY_SYMBOLS}

    for it in items:

        it["name"] = name_by_symbol.get(it["symbol"], it.get("name", it["symbol"]))

    return {"ok": True, "source": "YF", "items": items}
