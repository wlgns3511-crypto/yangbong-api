# apps/api/app.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from .news import router as news_router
from .news_routes import router as news_routes
from .market_crypto import router as crypto_router
from .market_commodity import router as commodity_router

app = FastAPI()

# ✅ CORS 설정 (모든 도메인 허용 — 테스트용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 일단 전부 허용 (확실히 열기)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 뉴스 라우터 등록 (실제 기사 수집 모드)
app.include_router(news_router)
# 뉴스 저장/조회 라우터 등록 (인메모리 스토어)
app.include_router(news_routes)
# 코인 및 원자재 시세 라우터 등록
app.include_router(crypto_router)
app.include_router(commodity_router)

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/market")
def get_market(cache: int = 0):
    # 기존에 계산한 지수 리스트들을 kr_list, world_list 변수에 담았다고 가정
    kr_list = [
        {"code": "KOSPI", "name": "코스피", "price": 2450.25, "change": 12.3, "change_pct": 0.5},
        {"code": "KOSDAQ", "name": "코스닥", "price": 820.14, "change": -5.7, "change_pct": -0.69},
        {"code": "KOSPI200", "name": "코스피200", "price": 325.33, "change": 2.1, "change_pct": 0.65},
    ]
    world_list = [
        {"code": "DJI", "name": "다우", "price": 39000.5, "change": 150.2, "change_pct": 0.38},
        {"code": "IXIC", "name": "나스닥", "price": 17500.1, "change": -32.1, "change_pct": -0.18},
        {"code": "SPX", "name": "S&P500", "price": 5200.3, "change": 8.5, "change_pct": 0.16},
    ]

    # ✅ 프론트가 확정적으로 읽는 키: indices.kr / indices.world
    return {"indices": {"kr": kr_list, "world": world_list}}

if __name__ == "__main__":
    uvicorn.run("apps.api.app:app", host="0.0.0.0", port=8000)
