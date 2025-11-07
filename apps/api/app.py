# apps/api/app.py
from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from .market_unified import router as market_router
from .market_scheduler import start_scheduler
from .news_scheduler import run_loop

app = FastAPI(title="yangbong-api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(market_router)


@app.on_event("startup")
def _on_startup():
    """앱 시작 시 백그라운드 태스크 시작"""
    # 뉴스 수집 스케줄러
    asyncio.create_task(run_loop())
    
    # 마켓 데이터 스케줄러
    start_scheduler()


@app.get("/health")
def health():
    return {"ok": True}
