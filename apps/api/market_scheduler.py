# apps/api/market_scheduler.py
# 30초 주기 마켓 데이터 수집 스케줄러

from __future__ import annotations
import os
import atexit
import logging
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from .market_unified import _fetch
from .market_common import now_ts
from .cache import save_cache

log = logging.getLogger("market.scheduler")

LOCK_FILE = Path("/tmp/yb_scheduler.lock")


def _acquire_lock() -> bool:
    """파일 락 획득 (단일 인스턴스 보장)"""
    try:
        if LOCK_FILE.exists():
            return False
        LOCK_FILE.write_text("1")
        return True
    except Exception:
        return False


def _release_lock():
    """파일 락 해제"""
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def _collect_all():
    """모든 세그먼트 데이터 수집"""
    try:
        for seg in ("KR", "US"):
            try:
                data = _fetch(seg)
                if data:
                    save_cache(seg, data, {"ts": now_ts(), "source": "scheduler"})
                    log.debug("market_scheduler: %s updated (%d items)", seg, len(data))
                else:
                    log.warning("market_scheduler: %s no data", seg)
            except Exception as e:
                log.error("market_scheduler: %s exception: %s", seg, e, exc_info=True)
    except Exception as e:
        log.error("market_scheduler: _collect_all exception: %s", e, exc_info=True)


def start_scheduler():
    """스케줄러 시작 (환경변수로 제어)"""
    if os.getenv("RUN_SCHEDULER", "false").lower() != "true":
        log.info("market_scheduler: RUN_SCHEDULER not set, skipping")
        return None
    
    if not _acquire_lock():
        log.warning("market_scheduler: lock file exists, another instance running?")
        return None
    
    try:
        scheduler = BackgroundScheduler(daemon=True, timezone="Asia/Seoul")
        scheduler.add_job(
            _collect_all,
            "interval",
            seconds=30,
            jitter=5,  # ±5초 랜덤 지연으로 동시 요청 방지
            max_instances=1,
            id="market_collector",
            replace_existing=True
        )
        scheduler.start()
        log.info("market_scheduler: started (30s interval)")
        
        atexit.register(lambda: (_release_lock(), scheduler.shutdown(wait=False)))
        return scheduler
    except Exception as e:
        log.error("market_scheduler: failed to start: %s", e, exc_info=True)
        _release_lock()
        return None
