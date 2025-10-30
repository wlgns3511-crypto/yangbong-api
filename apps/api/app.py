# apps/api/app.py
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone

app = FastAPI(title="yangbong-api")

# ---- 모델 ----
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

# ---- 유틸 ----
def now_iso():
    return datetime.now(timezone.utc).isoformat()

def normalize_type(t: str) -> str:
    t = (t or "kr").lower()
    if t.startswith("kr") or t == "k": return "kr"
    if t.startswith("us") or t == "u": return "us"
    if t.startswith("crypto") or t in {"c", "co", "coin"}: return "crypto"
    return "kr"

def build_mock_items(t: str, n: int, offset: int = 0) -> List[NewsItem]:
    seeds = {"kr": ("연합뉴스", "국내 증시/경제 요약"),
             "us": ("WSJ", "글로벌 시장 브리핑"),
             "crypto": ("코인데스크코리아", "암호화폐 주요 이슈")}
    src, base = seeds.get(t, ("양봉클럽", "뉴스 요약"))
    items: List[NewsItem] = []
    for i in range(n):
        idx = offset + i + 1
        items.append(NewsItem(
            id=f"{t}-{idx}",
            title=f"[{t.upper()}] 샘플 뉴스 {idx}",
            link="https://yangbong.club",
            source=src,
            published_at=now_iso(),
            thumbnail=f"https://picsum.photos/seed/{t}{idx}/800/450",
            summary=f"{base} — 샘플 데이터 {idx}",
        ))
    return items

# ---- 헬스체크 ----
@app.get("/health")
def health():
    return {"ok": True}

# ---- 뉴스 목록 ----
@app.get("/news", response_model=ApiListResponse)
@app.get("/api/news", response_model=ApiListResponse)  # 하위호환
def list_news(
    type: str = Query("kr", description="kr | us | crypto (k/u/c 축약 허용)"),
    limit: int = Query(12, ge=1, le=50),
    offset: int = Query(0, ge=0),
    cursor: Optional[str] = Query(None),
    sort: Optional[str] = Query(None, description="latest | popular (옵션)"),
    image_only: Optional[int] = Query(None, description="1이면 썸네일 있는 항목만 (옵션)"),
):
    t = normalize_type(type)
    if cursor:
        try:
            offset = int(cursor)
        except Exception:
            offset = 0

    items = build_mock_items(t, n=limit, offset=offset)
    if image_only == 1:
        items = [it for it in items if it.thumbnail]

    next_cur = str(offset + limit) if limit > 0 else None
    return ApiListResponse(ok=True, items=items, total=10_000, next_cursor=next_cur)