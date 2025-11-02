# apps/api/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ 라우터 import 추가
from .market_kr import router as kr_router
from .market_world import router as world_router         # <-- 추가
from .market_crypto import router as crypto_router       # <-- 추가
from .news_routes import router as news_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yangbong.club", "https://www.yangbong.club", "http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

# ✅ 라우터 등록 (프리픽스는 각 파일 설계에 맞춰 선택)
app.include_router(kr_router)                                # 예: prefix="/market/kr" 가 router 쪽에 있을 가능성
app.include_router(world_router)                             # <-- 추가 (이미 prefix="/market" 포함, /world 엔드포인트)
app.include_router(crypto_router)                            # <-- 추가 (이미 /market/crypto 전체 경로 정의됨)
app.include_router(news_router)                              # /news

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
    # 가장 무난한 토큰 엔드포인트를 단순 호출 (실제 토큰 발급 함수가 있다면 그걸 호출해도 됨)
    return {"base": base, "ok": True}

@debug.get("/kis/test-index")
def kis_test_index(code: str = "0001"):
    """KIS 인덱스 조회를 직접 테스트 (디버깅용)"""
    from apps.api.kis_client import get_index, get_access_token, KIS_BASE
    try:
        token_info = {
            "has_token": bool(get_access_token()),
            "token_preview": get_access_token()[:20] + "..." if get_access_token() else None,
        }
        
        result = get_index("U", code)
        
        return {
            "ok": True,
            "kis_base": KIS_BASE,
            "code": code,
            "token_info": token_info,
            "response_keys": list(result.keys()) if isinstance(result, dict) else "not dict",
            "response_preview": str(result)[:500] if result else "empty",
        }
    except Exception as e:
        return {
            "ok": False,
            "kis_base": KIS_BASE,
            "code": code,
            "error": str(e),
            "error_type": type(e).__name__,
        }

app.include_router(debug)