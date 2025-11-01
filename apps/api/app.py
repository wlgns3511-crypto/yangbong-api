# apps/api/app.py
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Literal, Optional
import uvicorn
import time
from .news import router as news_router
from .news_routes import router as news_routes
from .market_crypto import router as crypto_router
from .market_commodity import router as commodity_router
from .market_crypto import _fetch, _norm, MAP as CRYPTO_MAP, _cache as crypto_cache, TTL as CRYPTO_TTL

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

async def build_indices_payload():
    """통합 indices 데이터 구성"""
    # 한국 지수
    kr_list = [
        {"code": "KOSPI", "name": "코스피", "price": 2450.25, "change": 12.3, "change_pct": 0.5},
        {"code": "KOSDAQ", "name": "코스닥", "price": 820.14, "change": -5.7, "change_pct": -0.69},
        {"code": "KOSPI200", "name": "코스피200", "price": 325.33, "change": 2.1, "change_pct": 0.65},
    ]
    # 세계 지수
    world_list = [
        {"code": "DJI", "name": "다우", "price": 39000.5, "change": 150.2, "change_pct": 0.38},
        {"code": "IXIC", "name": "나스닥", "price": 17500.1, "change": -32.1, "change_pct": -0.18},
        {"code": "SPX", "name": "S&P500", "price": 5200.3, "change": 8.5, "change_pct": 0.16},
    ]
    # 코인 데이터
    crypto_list = []
    now = time.time()
    if now - crypto_cache["ts"] > CRYPTO_TTL or crypto_cache["data"] is None:
        try:
            default_symbols = ["BTC", "ETH", "XRP", "SOL", "BNB"]
            ids = [CRYPTO_MAP[s] for s in default_symbols if s in CRYPTO_MAP]
            if ids:
                payload = await _fetch(list(set(ids)))
                crypto_cache["ts"] = now
                crypto_cache["data"] = payload
                crypto_list = [_norm(s, payload) for s in default_symbols if s in CRYPTO_MAP]
        except Exception:
            crypto_list = []
    else:
        default_symbols = ["BTC", "ETH", "XRP", "SOL", "BNB"]
        crypto_list = [_norm(s, crypto_cache["data"]) for s in default_symbols if s in CRYPTO_MAP]
    
    return {
        "indices": {
            "kr": kr_list,
            "world": world_list,
            "crypto": crypto_list
        },
        "ts": int(time.time())
    }

@app.get("/market")
async def get_market(
    type: Optional[Literal["kr", "world", "crypto", "all"]] = Query("all"),
    cache: int = 0
):
    # 통합 데이터 구성
    payload = await build_indices_payload()
    indices = payload.get("indices", {})

    if type in ("kr", "world", "crypto"):
        return JSONResponse({
            "ok": True,
            "type": type,
            "items": indices.get(type, []),
            "ts": payload.get("ts"),
        })
    else:
        # all(기본): 기존 통합 형태 유지
        return JSONResponse({"ok": True, **payload})

if __name__ == "__main__":
    uvicorn.run("apps.api.app:app", host="0.0.0.0", port=8000)
