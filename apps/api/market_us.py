# apps/api/market_us.py

import time, requests



YF_URL = "https://query1.finance.yahoo.com/v7/finance/quote"

# 한 번에 묶어서 요청 (429 회피용으로 콤마 1회 호출)

US_SYMBOLS = {

    "DOW": "^DJI",

    "NASDAQ": "^IXIC",

    "S&P500": "^GSPC",

}



_cache = {"ts": 0, "data": []}

TTL = 60  # 초



def _yahoo_quote(symbols:list[str]):

    params = {"symbols": ",".join(symbols)}

    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(YF_URL, params=params, headers=headers, timeout=10)

    r.raise_for_status()

    return r.json()



def get_us_indices():

    now = time.time()

    if now - _cache["ts"] < TTL and _cache["data"]:

        return _cache["data"]



    j = _yahoo_quote(list(US_SYMBOLS.values()))

    result = []

    by_symbol = {q["symbol"]: q for q in j["quoteResponse"]["result"]}

    for name, sym in US_SYMBOLS.items():

        q = by_symbol.get(sym)

        if not q: 

            continue

        price = q.get("regularMarketPrice")

        change = q.get("regularMarketChange")

        change_rate = q.get("regularMarketChangePercent")

        result.append({

            "name": name,

            "price": float(price) if price is not None else None,

            "change": float(change) if change is not None else None,

            "changeRate": float(change_rate) if change_rate is not None else None,

            "time": q.get("regularMarketTime")

        })

    _cache["ts"] = now

    _cache["data"] = result

    return result

