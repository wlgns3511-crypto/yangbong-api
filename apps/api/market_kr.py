# apps/api/market_kr.py
import time
from typing import Any, Dict, List, Optional

import requests
from fastapi import APIRouter
from .kis_client import get_index
import logging

log = logging.getLogger("market_kr")

router = APIRouter()

YF_SYMBOLS: Dict[str, str] = {
    "KOSPI": "^KS11",
    "KOSDAQ": "^KQ11",
    "KOSPI200": "^KS200",
}

CODES = {
    "KOSPI": "0001",
    "KOSDAQ": "1001",
    "KOSPI200": "2001",
}

def _now_utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _normalize_item(idx: str,
                    price: Optional[float],
                    change: Optional[float],
                    rate: Optional[float]) -> Dict[str, Any]:
    """통합 스키마로 정규화 (market_unified.py와 호환)"""
    return {
        "id": idx,  # 기존 호환성 유지
        "market": "KR",
        "symbol": idx,
        "name": idx,
        "price": float(price) if price is not None else 0.0,
        "change": float(change) if change is not None else 0.0,
        "rate": float(rate) if rate is not None else 0.0,
        "close": float(price) if price is not None else 0.0,  # 기존 호환성 유지
        "pct": float(rate) if rate is not None else 0.0,  # 기존 호환성 유지
        "updatedAt": _now_utc_iso(),
    }


def yf_quote(symbols: List[str]) -> Dict[str, Dict[str, Any]]:
    """Yahoo Finance 단건 호출 폴백."""
    url = "https://query1.finance.yahoo.com/v7/finance/quote"
    params = {"symbols": ",".join(symbols)}
    res = requests.get(
        url,
        params=params,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=5,
    )
    res.raise_for_status()
    out: Dict[str, Dict[str, Any]] = {}
    result = res.json().get("quoteResponse", {}).get("result", [])
    for q in result:
        symbol = q.get("symbol")
        if symbol:
            out[symbol] = {
                "price": q.get("regularMarketPrice"),
                "change": q.get("regularMarketChange"),
                "rate": q.get("regularMarketChangePercent"),
                "ts": q.get("regularMarketTime"),
            }
    return out


@router.get("/market/kr", tags=["market"])
def get_market_kr() -> Dict[str, Any]:
    ids = ["KOSPI", "KOSDAQ", "KOSPI200"]

    items: List[Dict[str, Any]] = []
    kis_ok = False

    # 1) KIS 우선 시도
    try:
        kis_data: Dict[str, Dict[str, Any]] = {}
        
        for name, code in CODES.items():
            try:
                log.info(f"Fetching index from KIS: {name} (code={code})")
                res = get_index("U", code)
                output = res.get("output", {})
                if output:
                    kis_data[name] = {
                        "price": float(output.get("bstp_nmix_prpr") or 0),
                        "change": float(output.get("prdy_vrss") or 0),
                        "rate": float(output.get("prdy_ctrt") or 0),
                    }
                else:
                    log.warning(f"No 'output' key in response for {name}: response={res}")
            except Exception as e:
                log.error(f"KIS fetch error for {name}: {e}", exc_info=True)

        if isinstance(kis_data, dict) and len(kis_data) > 0:
            for k in ids:
                d = kis_data.get(k)
                if d:
                    items.append(
                        _normalize_item(
                            k,
                            d.get("price"),
                            d.get("change", 0),
                            d.get("rate", 0),
                        )
                    )
        kis_ok = len(items) == len(ids) and all((it.get("price", 0) or 0) > 0 for it in items)
    except Exception as e:
        log.error(f"KIS fetch error: {e}", exc_info=True)
        kis_ok = False
        items = []

    # 2) 실패 시 YF 폴백
    if not kis_ok:
        log.info("KIS failed, falling back to Yahoo Finance")
        try:
            mapping = {k: YF_SYMBOLS[k] for k in ids}
            yf = yf_quote(list(mapping.values()))
            items = []
            for k in ids:
                q = yf.get(mapping[k], {})
                items.append(
                    _normalize_item(
                        k,
                        q.get("price"),
                        q.get("change", 0),
                        q.get("rate", 0),
                    )
                )
            log.info(f"Yahoo Finance success: got {len(items)} items")
        except Exception as e:
            log.error(f"Yahoo Finance fallback error: {e}", exc_info=True)
            # 마지막 방어 – 스키마만 유지
            items = [_normalize_item(k, 0, 0, 0) for k in ids]

    return {"ok": True, "source": "KIS" if kis_ok else "YF", "items": items}
