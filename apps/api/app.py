from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
from contextlib import asynccontextmanager
from market_world import router as world_router
from market_kr import router as kr_router
from crypto import router as crypto_router
from news import router as news_router

# 핵심: FastAPI 인스턴스는 app 이름으로 존재해야 함

async def refresh_loop():
    """백그라운드 갱신 루프"""
    await asyncio.sleep(5)  # 앱 시작 후 잠시 대기
    
    while True:
        try:
            # 세계 지수 갱신
            from market_world import fetch_world_indices
            from cache import put_cache
            data = await fetch_world_indices()
            put_cache("world", data, ttl=60)
            print("[refresh] world indices updated")
        except Exception as e:
            print(f"[refresh] world error: {e}")
        
        try:
            # 한국 지수 갱신
            from market_kr import fetch_kr_indices
            from cache import put_cache
            data = await fetch_kr_indices()
            put_cache("kr", data, ttl=60)
            print("[refresh] kr indices updated")
        except Exception as e:
            print(f"[refresh] kr error: {e}")
        
        try:
            # 암호화폐 갱신 (기본 목록)
            from crypto import fetch_crypto_tickers
            from cache import put_cache
            data = await fetch_crypto_tickers(["BTC", "ETH", "XRP", "SOL"])
            put_cache("crypto_BTC,ETH,XRP,SOL", data, ttl=60)
            print("[refresh] crypto updated")
        except Exception as e:
            print(f"[refresh] crypto error: {e}")
        
        # 30초마다 갱신
        await asyncio.sleep(30)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 백그라운드 갱신 루프 시작
    asyncio.create_task(refresh_loop())
    yield

app = FastAPI(title="Yangbong API", version="1.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 배포 후엔 도메인만 허용하도록 좁히면 됨
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# /health 라우트는 외부 의존 없이 즉시 200을 리턴
@app.get("/health")
def health():
    return JSONResponse({"ok": True})

@app.get("/ping")
def ping():
    return {"pong": "yangbong"}

# 라우터 등록
app.include_router(world_router)
app.include_router(kr_router)
app.include_router(crypto_router)
app.include_router(news_router)

