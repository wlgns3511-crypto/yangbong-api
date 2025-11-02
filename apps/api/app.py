# apps/api/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .market_kr import router as kr_router

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

app.include_router(kr_router)

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

app.include_router(debug)