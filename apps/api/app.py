# apps/api/app.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# ✅ CORS 설정 (모든 도메인 허용 — 테스트용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 일단 전부 허용 (확실히 열기)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/news")
async def news(type: str = "kr", limit: int = 12):
    return {
        "status": "ok",
        "type": type,
        "limit": limit,
        "data": [f"샘플 뉴스 {i+1}" for i in range(limit)],
    }

@app.get("/market")
async def market(cache: int = 0):
    try:
        snap = {
            "kr": [
                {"code": "KOSPI", "name": "코스피", "price": None, "change": None, "change_pct": None},
                {"code": "KOSDAQ", "name": "코스닥", "price": None, "change": None, "change_pct": None},
                {"code": "KOSPI200", "name": "코스피200", "price": None, "change": None, "change_pct": None},
            ],
            "world": [
                {"code": "DJI", "name": "다우", "price": None, "change": None, "change_pct": None},
                {"code": "IXIC", "name": "나스닥", "price": None, "change": None, "change_pct": None},
                {"code": "SPX", "name": "S&P500", "price": None, "change": None, "change_pct": None},
            ],
        }
        return snap
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"market endpoint error: {e}")

if __name__ == "__main__":
    uvicorn.run("apps.api.app:app", host="0.0.0.0", port=8000)
