# apps/api/market_kr.py
import time
from typing import Any, Dict, List, Optional

import requests
from fastapi import APIRouter
from .kis_client import get_index
from .utils_yf import yf_quote as yf_quote_util
import logging

log = logging.getLogger("market_kr")

router = APIRouter(prefix="/api/market", tags=["market"])

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
    """통합 스키마로 정규화 (market_unified.py와 호환)
    
    price가 None이거나 0이면 0.0으로 설정하지만, 호출 전에 이미 검증됨
    """
    # price는 이미 호출 전에 검증되었지만, 안전을 위해 한 번 더 확인
    price_val = float(price) if price is not None and float(price) > 0 else 0.0
    change_val = float(change) if change is not None else 0.0
    rate_val = float(rate) if rate is not None else 0.0
    
    return {
        "id": idx,  # 기존 호환성 유지
        "market": "KR",
        "symbol": idx,  # 내부 표준 심볼: KOSPI, KOSDAQ, KOSPI200
        "name": idx,
        "price": price_val,
        "change": change_val,
        "rate": rate_val,
        "close": price_val,  # 기존 호환성 유지
        "pct": rate_val,  # 기존 호환성 유지
        "updatedAt": _now_utc_iso(),
    }


def get_market_kr() -> Dict[str, Any]:
    ids = ["KOSPI", "KOSDAQ", "KOSPI200"]
    items: List[Dict[str, Any]] = []
    kis_success_count = 0
    
    # 1) KIS 우선 시도 (각 지수별로 개별 처리)
    kis_data: Dict[str, Dict[str, Any]] = {}
    
    for name, code in CODES.items():
        try:
            log.info(f"[KIS] Fetching index: {name} (code={code})")
            res = get_index("U", code)
            output = res.get("output", {})
            if output:
                price = output.get("bstp_nmix_prpr")
                # price가 None이거나 0이면 실패로 간주
                if price is not None and float(price) > 0:
                    kis_data[name] = {
                        "price": float(price),
                        "change": float(output.get("prdy_vrss") or 0),
                        "rate": float(output.get("prdy_ctrt") or 0),
                    }
                    kis_success_count += 1
                    log.info(f"[KIS] Success: {name} = {price}")
                else:
                    log.warning(f"[KIS] Invalid price for {name}: {price}")
            else:
                log.warning(f"[KIS] No 'output' key for {name}: response={res}")
        except Exception as e:
            log.error(f"[KIS] Error for {name}: {e}", exc_info=True)
    
    # KIS에서 성공한 항목만 먼저 추가
    for k in ids:
        d = kis_data.get(k)
        if d and d.get("price", 0) > 0:
            items.append(
                _normalize_item(
                    k,
                    d.get("price"),
                    d.get("change", 0),
                    d.get("rate", 0),
                )
            )
    
    # 2) KIS 실패한 항목만 YF 폴백 시도
    missing_ids = [k for k in ids if k not in kis_data or kis_data[k].get("price", 0) <= 0]
    
    if missing_ids:
        log.info(f"[YF] KIS failed for {missing_ids}, falling back to Yahoo Finance")
        try:
            mapping = {k: YF_SYMBOLS[k] for k in missing_ids}
            yf_results = yf_quote_util(list(mapping.values()))
            log.info(f"[YF] Response: {list(yf_results.keys())}")
            
            for k in missing_ids:
                yf_symbol = mapping[k]
                q = yf_results.get(yf_symbol)
                if q:
                    price = q.get("price")
                    change_pct = q.get("change_pct", 0)
                    # change_pct를 rate로 변환 (이미 퍼센트 값)
                    rate = change_pct
                    change = (price * change_pct / 100) if price and change_pct else 0
                    
                    # YF에서도 값이 0이거나 None이면 추가하지 않음 (기존값 유지)
                    if price is not None and float(price) > 0:
                        items.append(
                            _normalize_item(
                                k,
                                price,
                                change,
                                rate,
                            )
                        )
                        log.info(f"[YF] Success: {k} = {price}")
                    else:
                        log.warning(f"[YF] Invalid price for {k}: {price}")
                else:
                    log.warning(f"[YF] No data for {k}")
        except Exception as e:
            log.error(f"[YF] Fallback error: {e}", exc_info=True)
    
    # 최종 결과: 모든 항목이 성공했는지 확인
    kis_ok = kis_success_count == len(ids)
    source = "KIS" if kis_ok else ("YF" if kis_success_count < len(ids) else "NONE")
    
    log.info(f"[RESULT] Source: {source}, Items: {len(items)}/{len(ids)}")
    
    return {"ok": True, "source": source, "items": items}


# ✅ /api/market/kr 엔드포인트 추가
@router.get("/kr")
def market_kr_endpoint() -> Dict[str, Any]:
    """KR 시세 전용 엔드포인트: /api/market/kr"""
    return get_market_kr()
