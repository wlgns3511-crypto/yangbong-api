# apps/api/utils_yf.py

import time

import random

import requests

from typing import List, Dict, Any



_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

_H = {

    "User-Agent": _UA,

    "Accept": "application/json, text/javascript, */*; q=0.01",

    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",

    "Connection": "keep-alive",

}



def _sleep(i: int):

    time.sleep((i + 1) * 0.7 + random.random() * 0.5)



def yf_quote_many(symbols: List[str], retry: int = 2) -> List[Dict[str, Any]]:

    """v7 quote (query1) → 실패시 query2 로 재시도"""

    base_list = ["https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com"]

    for host in base_list:

        url = f"{host}/v7/finance/quote"

        params = {"symbols": ",".join(symbols)}

        for i in range(retry + 1):

            try:

                r = requests.get(url, params=params, headers=_H, timeout=8)

                if r.status_code == 200:

                    res = r.json().get("quoteResponse", {}).get("result", [])

                    if res:

                        return res

                _sleep(i)

            except Exception:

                _sleep(i)

    return []



def yf_chart_one(symbol: str, retry: int = 2) -> Dict[str, Any] | None:

    """v8 chart 단건 (range=1d)로 종가/변동률 근사치 얻기"""

    base_list = ["https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com"]

    for host in base_list:

        url = f"{host}/v8/finance/chart/{symbol}"

        params = {"range": "1d", "interval": "1d"}

        for i in range(retry + 1):

            try:

                r = requests.get(url, params=params, headers=_H, timeout=8)

                if r.status_code == 200:

                    j = r.json()

                    result = (j.get("chart", {}).get("result") or [None])[0]

                    if not result:

                        _sleep(i); continue

                    meta = result.get("meta", {})

                    close = (result.get("indicators", {}).get("quote", [{}])[0]

                             .get("close") or [None])[-1]

                    if close is None:

                        _sleep(i); continue

                    prev = meta.get("chartPreviousClose")

                    chg = None if prev in (None, 0) else close - prev

                    pct = None if prev in (None, 0) else (chg / prev) * 100.0

                    return {

                        "symbol": symbol,

                        "regularMarketPrice": close,

                        "regularMarketChange": chg,

                        "regularMarketChangePercent": pct,

                        "regularMarketTime": meta.get("regularMarketTime"),

                    }

                _sleep(i)

            except Exception:

                _sleep(i)

    return None



def yf_hard_fallback(symbols: List[str]) -> List[Dict[str, Any]]:

    """v7이 비면 v8로 각 심볼을 순회해서라도 값 채우기"""

    rows = yf_quote_many(symbols)

    if rows:

        return rows

    out: List[Dict[str, Any]] = []

    for s in symbols:

        one = yf_chart_one(s)

        if one:

            out.append(one)

    return out
