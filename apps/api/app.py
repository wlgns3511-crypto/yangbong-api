import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from market_world import router as world_router

# --- 절대: import 시점에 외부 네트워크/대용량 작업 금지! ---
# 예) from .crawler import warm_up   <-- OK(함수 import만), 하지만 여기서 warm_up() 호출 금지

# 예시용 백그라운드 작업 (네트워크/크롤러/스케줄러 시작 등)
async def start_background_tasks():
    # 여기에 APScheduler 시작, 크롤러 warm-up, 캐시 프리로드 등 넣기
    # 예시:
    # from .scheduler import get_scheduler
    # sched = get_scheduler()
    # sched.start()   # APScheduler는 BackgroundScheduler(daemon=True) 권장
    #
    # 초기 네트워크 콜은 짧게/예외 잡기
    try:
        await asyncio.sleep(0)  # 즉시 양보(이 줄은 구조 설명용)
        # await warm_up()  # 길면 여기서도 create_task로 더 쪼개기
    except Exception as e:
        # 절대 시작을 막지 않도록 예외 삼켜서 로그만 남기기
        print(f"[startup-bg] non-blocking init failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 백그라운드 태스크로 초기화 분리 → health가 즉시 200
    asyncio.create_task(start_background_tasks())
    yield
    # 종료 정리 필요하면 여기서
    # 예시: 
    # from .scheduler import get_scheduler
    # sched = get_scheduler()
    # if sched.running:
    #     sched.shutdown()

app = FastAPI(title="Yangbong API", version="1.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# --- 절대 의존성 없는 즉시 OK health ---
@app.get("/health")
def health():
    return JSONResponse({"ok": True})

@app.get("/ping")
def ping():
    return {"pong": "yangbong"}

# 여기에 기존 라우트들 import (단, import 시점에 외부 호출/대용량 작업 없음 보장!)
app.include_router(world_router)

