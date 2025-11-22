"""FastAPI 애플리케이션 메인 진입점"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import router as v1_router
from app.core.config import settings

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="양봉클럽 API",
    description="양봉클럽 백엔드 API 서버",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yangbong.club",
        "https://www.yangbong.club",
        "http://localhost:5173",  # 개발 환경 (Vite 기본 포트)
        "http://localhost:3000",  # 개발 환경 대체 포트
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(v1_router.router)


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "양봉클럽 API 서버",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    try:
        # 환경변수 없이도 동작하도록 try-except 처리
        env = getattr(settings, 'environment', 'unknown')
    except Exception:
        env = 'unknown'
    
    return {
        "status": "healthy",
        "environment": env,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )

