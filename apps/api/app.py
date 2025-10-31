from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone

app = FastAPI(title="yangbong-api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yangbong.club", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NewsItem(BaseModel):
    id: str
    title: str
    link: str
    source: str
    published_at: str
    thumbnail: Optional[str] = None
    summary: Optional[str] = None

class ApiListResponse(BaseModel):
    ok: bool
    items: List[NewsItem]
    total: Optional[int] = None
    next_cursor: Optional[str] = None

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def normalize_type(t: str) -> str:
    t = (t or "kr").lower()
    if t.startswith("kr") or t == "k": return "kr"
    if t.startswith("us") or t == "u": return "us"
    if t.startswith("crypto") or t in {"c","co","coin"}: return "crypto"
    return "kr"

def build_mock_items(t: str, n: int, offset: int = 0) -> List[NewsItem]:
    seeds = {
        "kr": ("연합뉴스", "국내 증시/경제 요약"),
        "us": ("WSJ", "글로벌 시장 브리핑"),
        "crypto": ("코인데스크코리아", "암호화폐 주요 이슈"),
    }
    src, base = seeds.get(t, ("양봉클럽", "뉴스 요약"))
    out = []
    for i in range(n):
        idx = offset + i + 1
        out.append(NewsItem(
            id=f"{t}-{idx}",
            title=f"[{t.upper()}] 샘플 뉴스 {idx}",
            link="https://yangbong.club",
            source=src,
            published_at=now_iso(),
            thumbnail=f"https://picsum.photos/seed/{t}{idx}/800/450",
            summary=f"{base} — 샘플 데이터 {idx}",
        ))
    return out

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/news", response_model=ApiListResponse)
def list_news(
    type: str = Query("kr"),
    limit: int = Query(12, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    t = normalize_type(type)
    items = build_mock_items(t, limit, offset)
    return ApiListResponse(ok=True, items=items, total=1000, next_cursor=str(offset + limit))