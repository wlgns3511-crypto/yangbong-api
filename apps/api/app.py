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
def market(cache: int = 0):
    kr = [
        {"code": "KOSPI",   "name": "코스피",   "price": 2450.25, "change": 12.3,  "change_pct": 0.50},
        {"code": "KOSDAQ",  "name": "코스닥",   "price": 820.14,  "change": -5.7,  "change_pct": -0.69},
        {"code": "KOSPI200","name": "코스피200","price": 325.33,  "change": 2.1,   "change_pct": 0.65},
    ]
    world = [
        {"code": "DJI",   "name": "다우",        "price": 39000.5, "change": 150.2, "change_pct": 0.38},
        {"code": "IXIC",  "name": "나스닥",      "price": 17500.1, "change": -32.1, "change_pct": -0.18},
        {"code": "SPX",   "name": "S&P500",     "price": 5200.3,  "change": 8.5,   "change_pct": 0.16},
        {"code": "N225",  "name": "니케이225",  "price": 38500.0, "change": 120.0, "change_pct": 0.31},
        {"code": "SSEC",  "name": "상해종합",    "price": 3050.6,  "change": -10.2, "change_pct": -0.33},
        {"code": "HSI",   "name": "항셍",        "price": 17880.4, "change": 45.7,  "change_pct": 0.26},
        {"code": "FTSE",  "name": "영국 FTSE100","price": 7550.2,  "change": -5.3,  "change_pct": -0.07},
        {"code": "CAC40", "name": "프랑스 CAC40","price": 7201.9,  "change": 11.4,  "change_pct": 0.16},
        {"code": "DAX",   "name": "독일 DAX",    "price": 15980.3, "change": -20.6, "change_pct": -0.13},
    ]
    # 호환키도 같이 내려주면 안전
    return {"kr": kr, "world": world, "indices": {"kr": kr, "world": world}}

if __name__ == "__main__":
    uvicorn.run("apps.api.app:app", host="0.0.0.0", port=8000)
