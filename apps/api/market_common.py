# apps/api/market_common.py
# 공통 유틸리티 함수

from __future__ import annotations
import time
import math
from typing import Any, Dict

TTL_SECONDS = 30  # 🔸실시간 캐시 TTL


def now_ts() -> int:
    """현재 타임스탬프 (초)"""
    return int(time.time())


def is_fresh(ts: int | None, ttl: int = TTL_SECONDS) -> bool:
    """캐시가 신선한지 확인"""
    if not ts:
        return False
    return (now_ts() - ts) < ttl


def is_valid_price(x) -> bool:
    """가격 값 검증"""
    try:
        v = float(x)
    except Exception:
        return False
    if not math.isfinite(v):
        return False
    if v <= 0:
        return False
    if v > 10_000_000:
        return False
    return True


def normalize_item(raw: Dict[str, Any]) -> Dict[str, Any]:
    """원시 데이터를 표준 포맷으로 정규화"""
    symbol = raw.get("symbol") or raw.get("code") or ""
    name = raw.get("name") or symbol
    
    # 가격 후보 통합
    src_price = raw.get("price") or raw.get("close") or raw.get("now") or raw.get("last")
    price = float(src_price) if is_valid_price(src_price) else None
    
    change = float(raw.get("change") or 0) if price is not None else 0.0
    rate = float(raw.get("changeRate") or raw.get("rate") or 0)
    
    return {
        "symbol": symbol,
        "name": name,
        "price": price,  # None이면 상위에서 필터됨
        "change": change,
        "changeRate": rate,
        "time": raw.get("time")  # epoch(초) 또는 None
    }


# 호환성을 위한 기존 함수들
CANON = {
    "KOSPI": ["코스피", "KS11"],
    "KOSDAQ": ["코스닥"],
    "KOSPI200": ["코스피200", "KPI200"],
    "DJI": ["DOW", "다우", "DJI@DJI", "^DJI"],
    "IXIC": ["NASDAQ", "나스닥", "NAS@IXIC", "^IXIC"],
    "GSPC": ["SPX", "S&P500", "SNP", "S&P", "^GSPC"],
}


def _norm(s: str | None) -> str:
    return (s or "").strip().upper()


REV = {k: k for k in CANON.keys()}
for c, aliases in CANON.items():
    for a in aliases:
        REV[_norm(a)] = c


def canonicalize(s: str | None) -> str:
    """심볼명 정규화"""
    k = _norm(s)
    return REV.get(k, k)
