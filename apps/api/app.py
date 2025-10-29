from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
from contextlib import asynccontextmanager
from market_world import router as world_router

async def start_background_tasks():
    # 무거운 초기화는 여기에서 비동기로
    try:
        await asyncio.sleep(0)
        # 예: 스케줄러 start, warm-up 등
    except Exception as e:
        print(f"[startup-bg] {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.get_event_loop().create_task(start_background_tasks())
    yield

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

