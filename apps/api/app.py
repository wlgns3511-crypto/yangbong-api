from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
from contextlib import asynccontextmanager
from market_world import router as world_router

# 핵심: FastAPI 인스턴스는 app 이름으로 존재해야 함

async def start_background_tasks():
    try:
        await asyncio.sleep(0)
        # 스케줄러/크롤러 시작 등은 여기서 비동기로
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

# /health 라우트는 외부 의존 없이 즉시 200을 리턴
@app.get("/health")
def health():
    return JSONResponse({"ok": True})

@app.get("/ping")
def ping():
    return {"pong": "yangbong"}

app.include_router(world_router)

