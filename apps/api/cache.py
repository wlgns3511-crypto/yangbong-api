import time
from typing import Any, Optional

_cache: dict[str, tuple[Any, float]] = {}


def put_cache(key: str, data: Any, ttl: int = 60) -> None:
    """캐시에 데이터 저장"""
    _cache[key] = (data, time.time() + ttl)


def get_cache(key: str) -> Optional[Any]:
    """캐시에서 데이터 조회 (만료된 경우 None 반환)"""
    v = _cache.get(key)
    if not v:
        return None
    data, exp = v
    return data if time.time() < exp else None


def upsert_market_data(market: str, symbol: str, **kwargs) -> None:
    """시장 데이터 캐시 업데이트 (향후 DB 연동 대비)"""
    # 현재는 로깅만 수행 (필요시 DB 저장 로직 추가)
    key = f"{market}:{symbol}"
    # 향후 DB 저장 로직 추가 예정
    pass
