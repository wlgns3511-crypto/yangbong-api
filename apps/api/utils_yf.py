# apps/api/utils_yf.py
import time
import random
import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

UA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}

YF_QUOTE_URL = "https://query1.finance.yahoo.com/v7/finance/quote"


def _extract(item) -> Optional[dict]:
    try:
        price = item.get("regularMarketPrice")
        chg_pct = item.get("regularMarketChangePercent")
        if price is None:
            return None
        return {
            "price": float(price),
            "change_pct": float(chg_pct) if chg_pct is not None else None,
            "source": "YF",
        }
    except Exception as e:
        logger.warning(f"[YF] extract error: {e}")
        return None


def yf_quote(symbols: List[str]) -> Dict[str, Optional[dict]]:
    """
    Yahoo Finance 다건 조회. 심볼은 YF 포맷 사용 (예: ^KS11, ^IXIC, ^GSPC 등)
    401/429 대응: UA 헤더 + 짧은 백오프.
    """
    out: Dict[str, Optional[dict]] = {s: None for s in symbols}
    if not symbols:
        return out

    params = {"symbols": ",".join(symbols)}
    for attempt in range(3):
        try:
            res = requests.get(YF_QUOTE_URL, params=params, headers=UA_HEADERS, timeout=10)
            if res.status_code == 429:
                wait = 0.8 + attempt * 0.7
                logger.warning(f"[YF] 429 Too Many Requests. sleep {wait}s")
                time.sleep(wait)
                continue
            if res.status_code == 401:
                logger.warning("[YF] 401 Unauthorized. UA header may be blocked temporarily.")
                time.sleep(0.5)
                continue

            res.raise_for_status()
            js = res.json()
            result = js.get("quoteResponse", {}).get("result", [])
            by_sym = {r.get("symbol"): r for r in result}

            for s in symbols:
                item = by_sym.get(s)
                out[s] = _extract(item) if item else None

            return out
        except Exception as e:
            logger.warning(f"[YF] request error: {e}")
            time.sleep(0.5)

    # 실패 시 None 유지
    return out


def yf_quote_many(symbols: list[str], retry: int = 2):
    """
    Yahoo Finance 다건 조회 (리스트 반환)
    KIS 폴백용으로 사용
    """
    url = "https://query1.finance.yahoo.com/v7/finance/quote"
    params = {"symbols": ",".join(symbols)}
    _UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
    
    for i in range(retry + 1):
        try:
            r = requests.get(url, params=params, headers={"User-Agent": _UA}, timeout=10)
            if r.status_code == 200:
                return r.json().get("quoteResponse", {}).get("result", [])
            # 429 방지 백오프
            time.sleep((i + 1) * 0.8 + random.random() * 0.6)
        except Exception as e:
            logger.warning(f"[YF] quote_many error: {e}")
            if i < retry:
                time.sleep((i + 1) * 0.8)
    return []
