from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from market_world import router as world_router

app = FastAPI(title="Yangbong API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/ping")
def ping():
    return {"pong": "yangbong"}

app.include_router(world_router)

