# apps/api/market_kr.py
from fastapi import APIRouter
from .kis_client import get_index
import time
import logging
import requests
from typing import List, Dict, Any

log = logging.getLogger("market_kr")

router = APIRouter(prefix="/market", tags=["market"])

TTL = 30
_cache = {"ts": 0, "data": None}

CODES = {
    "KOSPI": "0001",
    "KOSDAQ": "1001",
    "KOSPI200": "2001",
}

# Yahoo Finance 심볼 매핑
YF_SYMBOLS = {
    "KOSPI": "^KS11",
    "KOSDAQ": "^KQ11",
    "KOSPI200": "^KS200",
}

def yf_quote(symbols: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Yahoo Finance 간단 쿼트 폴백.
    symbols: ['^KS11','^KQ11','^KS200']
    return: { '^KS11': {...}, ... }
    """
    url = "https://query1.finance.yahoo.com/v7/finance/quote"
    params = {"symbols": ",".join(symbols)}
    try:
        res = requests.get(url, params=params, headers={"User-Agent":"Mozilla/5.0"}, timeout=5)
        res.raise_for_status()
        out: Dict[str, Dict[str, Any]] = {}
        for q in res.json().get("quoteResponse", {}).get("result", []):
            out[q["symbol"]] = {
                "price": q.get("regularMarketPrice"),
                "change": q.get("regularMarketChange"),
                "rate": q.get("regularMarketChangePercent"),
                "ts": q.get("regularMarketTime"),
            }
        return out
    except Exception as e:
        log.error(f"Yahoo Finance fetch error: {e}", exc_info=True)
        return {}

def normalize_item(id_: str, price: float, change: float, rate: float) -> Dict[str, Any]:
    """통합 스키마로 정규화"""
    return {
        "id": id_,
        "name": id_,
        "close": float(price) if price is not None else 0.0,
        "change": float(change) if change is not None else 0.0,
        "pct": float(rate) if rate is not None else 0.0,
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

@router.get("/kr")
def market_kr(cache: int = 1):
    now = time.time()
    if cache and _cache["data"] and now - _cache["ts"] < TTL:
        return _cache["data"]

    ids = list(CODES.keys())
    items: List[Dict[str, Any]] = []
    kis_ok = False

    # 1) KIS 우선 시도
    try:
        for name, code in CODES.items():
            try:
                log.info(f"Fetching index from KIS: {name} (code={code})")
                res = get_index("U", code)
                log.info(f"Got response for {name}: keys={list(res.keys()) if isinstance(res, dict) else 'not dict'}")
                output = res.get("output", {})
                if not output:
                    log.warning(f"No 'output' key in response for {name}: response={res}")
                    break  # KIS 실패로 간주
                else:
                    items.append({
                        "id": name,
                        "name": output.get("bstp_nmix_prpr_name") or name,
                        "close": float(output.get("bstp_nmix_prpr") or 0),
                        "change": float(output.get("prdy_vrss") or 0),
                        "pct": float(output.get("prdy_ctrt") or 0),
                        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    })
        # 모든 항목이 성공적으로 가져왔는지 확인
        kis_ok = len(items) == len(ids) and all(item.get("close", 0) > 0 for item in items)
        if kis_ok:
            log.info(f"KIS success: got {len(items)} items")
    except Exception as e:
        log.error(f"KIS fetch error: {e}", exc_info=True)
        kis_ok = False

    # 2) 실패 시 YF 폴백
    if not kis_ok:
        log.info("KIS failed, falling back to Yahoo Finance")
        items = []  # KIS 데이터 리셋
        try:
            mapping = {k: YF_SYMBOLS[k] for k in ids}
            yf = yf_quote(list(mapping.values()))
            for k in ids:
                q = yf.get(mapping[k], {})
                price = q.get("price") or 0
                change = q.get("change") or 0
                rate = q.get("rate") or 0
                # rate가 % 단위로 오면 그대로 사용 (Yahoo Finance는 이미 %로 반환)
                items.append(normalize_item(k, price, change, rate))
            log.info(f"Yahoo Finance success: got {len(items)} items")
        except Exception as e:
            log.error(f"Yahoo Finance fallback error: {e}", exc_info=True)
            # 마지막 방어: 가격 0으로라도 스키마 유지
            for k in ids:
                items.append(normalize_item(k, 0, 0, 0))

    payload = {"ok": True, "source": "KIS" if kis_ok else "YF", "items": items}
    _cache.update({"ts": now, "data": payload})
    return payload
