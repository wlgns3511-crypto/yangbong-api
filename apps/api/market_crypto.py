# apps/api/market_crypto.py

import time, requests



CG_URL = "https://api.coingecko.com/api/v3/simple/price"

IDS = {

    "BTC": "bitcoin",

    "ETH": "ethereum",

    "XRP": "ripple",

    "SOL": "solana",

}

_cache = {"ts": 0, "data": []}

TTL = 60



def get_crypto():

    now = time.time()

    if now - _cache["ts"] < TTL and _cache["data"]:

        return _cache["data"]



    params = {

        "ids": ",".join(IDS.values()),

        "vs_currencies": "usd,krw",

        "include_24hr_change": "true"

    }

    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(CG_URL, params=params, headers=headers, timeout=10)

    r.raise_for_status()

    j = r.json()



    result = []

    inv = {v:k for k,v in IDS.items()}

    for cg_id, obj in j.items():

        sym = inv.get(cg_id, cg_id).upper()

        # 기본은 KRW 기준으로 보여주고 싶으면 krw 사용

        price = obj.get("krw")

        change_rate = obj.get("krw_24h_change")

        result.append({

            "name": sym,

            "price": float(price) if price is not None else None,

            "change": None,

            "changeRate": float(change_rate) if change_rate is not None else None,

            "time": int(time.time())

        })

    _cache["ts"] = now

    _cache["data"] = result

    return result
