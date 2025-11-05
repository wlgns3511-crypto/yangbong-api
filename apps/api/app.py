# apps/api/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

# ✅ 라우터 import
from . import market_kr, market_world, market_crypto, market_commodity
from .news_routes import router as news_router
from .news_scheduler import run_loop

app = FastAPI(
    title="양봉클럽 API",
    description="FastAPI backend for yangbong.club",
    version="1.0.0",
)

# ✅ CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yangbong.club", "https://www.yangbong.club", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 라우터 등록
app.include_router(market_kr.router, tags=["market_kr"])  # 이미 prefix="/api/market" 포함 → /api/market/kr
# 다른 라우터들은 이미 자체 prefix를 가지고 있음
app.include_router(market_world.router, tags=["market_world"])  # 이미 prefix="/api/market" 포함
app.include_router(market_crypto.router, tags=["market_crypto"])  # 이미 prefix="/api/market" 포함
app.include_router(market_commodity.router, tags=["market_commodity"])  # 이미 prefix="/api/market" 포함
app.include_router(news_router, tags=["news"])  # 이미 prefix="/api" 포함

@app.get("/health")
def health():
    return {"ok": True}

# 디버그 라우터
import httpx
from fastapi import APIRouter, HTTPException
from os import getenv

debug = APIRouter(prefix="/__debug", tags=["__debug"])

@debug.get("/ip")
def my_outbound_ip():
    try:
        ip = httpx.get("https://api.ipify.org", timeout=5).text
        return {"ip": ip}
    except Exception as e:
        raise HTTPException(500, f"ipify error: {e}")

@debug.get("/kis/ping")
def kis_ping():
    base = getenv("KIS_BASE_URL")
    if not base:
        raise HTTPException(500, "KIS_BASE_URL not set")
    return {"base": base, "ok": True}

@debug.get("/kis/test-index")
def kis_test_index(code: str = "0001"):
    """KIS 인덱스 조회를 직접 테스트 (디버깅용)"""
    from apps.api.kis_client import get_index, get_access_token, KIS_BASE_URL
    try:
        token_info = {
            "has_token": bool(get_access_token()),
            "token_preview": get_access_token()[:20] + "..." if get_access_token() else None,
        }
        
        status, result, raw = get_index("U", code)
        
        return {
            "ok": status == 200,
            "kis_base": KIS_BASE_URL,
            "code": code,
            "token_info": token_info,
            "status_code": status,
            "response": result,
            "raw_preview": raw[:500] if raw else "",
        }
    except Exception as e:
        return {
            "ok": False,
            "kis_base": KIS_BASE_URL,
            "code": code,
            "error": str(e),
            "error_type": type(e).__name__,
        }

@debug.get("/kis/overseas")
def kis_overseas_price(excd: str = "NAS", symb: str = "AAPL"):
    from .kis_client import get_overseas_price, KIS_BASE_URL
    try:
        data = get_overseas_price(excd, symb)
        return {"ok": True, "base": KIS_BASE_URL, "excd": excd, "symb": symb, **data}
    except Exception as e:
        return {"ok": False, "base": KIS_BASE_URL, "excd": excd, "symb": symb,
                "error": str(e), "type": type(e).__name__}

app.include_router(debug)

@app.on_event("startup")
async def start_news_collector():
    """뉴스 수집 스케줄러를 백그라운드 태스크로 시작"""
    asyncio.create_task(run_loop())
