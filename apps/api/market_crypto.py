# apps/api/market_crypto.py

import time, requests

from fastapi import APIRouter, Query



router = APIRouter(prefix="/api", tags=["market_crypto"])



CG_IDS = [

    {"name": "BTC", "id": "bitcoin"},

    {"name": "ETH", "id": "ethereum"},

    {"name": "XRP", "id": "ripple"},

    {"name": "SOL", "id": "solana"},

    {"name": "BNB", "id": "binancecoin"},

]



@router.get("/market")

def get_crypto(seg: str = Query("", alias="seg")):

    if seg.upper() != "CRYPTO":

        return {"ok": False, "error": "bad_seg"}

    ids = ",".join(x["id"] for x in CG_IDS)

    url = "https://api.coingecko.com/api/v3/simple/price"

    r = requests.get(url, params={"ids": ids, "vs_currencies": "usd", "include_24hr_change": "true"}, timeout=8)

    r.raise_for_status()

    data = r.json()

    now = int(time.time())

    items = []

    for x in CG_IDS:

        row = data.get(x["id"])

        if not row: 

            continue

        price = row.get("usd")

        chg   = row.get("usd_24h_change", 0)

        items.append({

            "symbol": x["name"],

            "name": x["name"],

            "price": float(price),

            "change": 0.0,

            "changeRate": float(chg),

            "time": now

        })

    return {"ok": True, "source": "Coingecko", "items": items}
