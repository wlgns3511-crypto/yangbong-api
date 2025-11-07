# apps/api/cache.py
# 파일 기반 마켓 데이터 캐시 (스케줄러와 API 공유)

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

CACHE_DIR = Path(os.environ.get("MARKET_CACHE_DIR", "/tmp"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_file(seg: str) -> Path:
    """세그먼트별 캐시 파일 경로"""
    return CACHE_DIR / f"market_{seg.upper()}.json"


def load_cache(seg: str) -> Optional[Dict[str, Any]]:
    """캐시 로드: {"items": [...], "meta": {"ts": ..., "source": ...}}"""
    cache_file = _cache_file(seg)
    if not cache_file.exists():
        return None
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else None
    except Exception:
        return None


def save_cache(seg: str, items: List[Dict[str, Any]], meta: Dict[str, Any]) -> None:
    """캐시 저장"""
    cache_file = _cache_file(seg)
    tmp_file = cache_file.with_suffix(".tmp")
    try:
        data = {"items": items, "meta": meta}
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp_file.replace(cache_file)
    except Exception:
        if tmp_file.exists():
            tmp_file.unlink(missing_ok=True)


# 호환성을 위한 기존 함수들 (market_common.py에서 사용)
def get_cache(seg: str):
    """기존 get_cache 호환 (반환: (items, fresh))"""
    from .market_common import is_fresh, now_ts
    cached = load_cache(seg)
    if not cached:
        return [], False
    items = cached.get("items", [])
    ts = cached.get("meta", {}).get("ts")
    return items, is_fresh(ts)


def set_cache(seg: str, items: List[Dict[str, Any]]) -> None:
    """기존 set_cache 호환"""
    from .market_common import now_ts
    save_cache(seg, items, {"ts": now_ts(), "source": "api"})
