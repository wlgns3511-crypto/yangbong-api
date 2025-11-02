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
