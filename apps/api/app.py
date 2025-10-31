# apps/api/app.py
from fastapi import FastAPI
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

if __name__ == "__main__":
    uvicorn.run("apps.api.app:app", host="0.0.0.0", port=8000)
