# apps/api/scheduler.py (예시)
# APScheduler를 안전하게 사용하기 위한 헬퍼
#
# 사용법:
# 1. app.py의 start_background_tasks()에서:
#    from .scheduler import get_scheduler
#    sched = get_scheduler()
#    sched.start()
#
# 2. 스케줄 작업 추가 예시:
#    from .jobs import collect_market_data
#    sched.add_job(
#        collect_market_data,
#        'interval',
#        minutes=30,
#        id='collector',
#        replace_existing=True
#    )

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor

_scheduler = None

def get_scheduler():
    """
    싱글톤 APScheduler 인스턴스 반환
    
    주의: 이 함수는 import 시점에 start() 하지 않는다.
    start는 오직 start_background_tasks() 안에서 딱 한 번만 실행.
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(
            daemon=True,
            timezone="Asia/Seoul",
            executors={
                'default': ThreadPoolExecutor(2)
            }
        )
        # 예시: 스케줄 작업 등록
        # sched.add_job(run_all, 'interval', minutes=30, id='collector', replace_existing=True)
    return _scheduler

# 예시: 스케줄 작업 함수
# def collect_market_data():
#     """주기적으로 시장 데이터 수집"""
#     try:
#         # 여기에 데이터 수집 로직
#         pass
#     except Exception as e:
#         print(f"[scheduler] collect_market_data failed: {e}")

