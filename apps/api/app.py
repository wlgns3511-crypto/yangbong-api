from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(
    title="Yangbong API",
    description="양봉클럽 데이터 API (국내/해외/코인 뉴스 포함)",
    version="1.0.0"
)

# -------------------------------
# 🔥 CORS 설정 (가장 중요)
# -------------------------------
origins = [
    "https://yangbong.club",            # Production 도메인 (Vercel)
    "https://yangbong-web.vercel.app",  # Preview 환경
    "http://localhost:3000",            # 개발용
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # 허용할 도메인들
    allow_credentials=True,
    allow_methods=["*"],         # 모든 메서드 허용 (GET, POST 등)
    allow_headers=["*"],         # 모든 헤더 허용
)

# -------------------------------
# ✅ 헬스체크 (테스트용)
# -------------------------------
@app.get("/health")
async def health():
    return {"ok": True}

# -------------------------------
# ✅ 뉴스 API 예시 엔드포인트 (연결 확인용)
# -------------------------------
@app.get("/news")
async def get_news(type: str = "kr", limit: int = 12):
    sample_data = [
        {"title": f"[{type.upper()}] 샘플 뉴스 {i+1}", "desc": f"{type} 뉴스 설명 {i+1}"} 
        for i in range(limit)
    ]
    return JSONResponse(content={"status": "ok", "data": sample_data})

# -------------------------------
# ✅ 실행 (로컬 or Railway용)
# -------------------------------
if __name__ == "__main__":
    uvicorn.run("apps.api.app:app", host="0.0.0.0", port=8000)
