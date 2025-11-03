from fastapi import APIRouter, Query
from sqlalchemy import desc
from datetime import datetime
from .news_model import SessionLocal, News

router = APIRouter(prefix="/api", tags=["news"])

def _to_dict(news_obj):
    """SQLAlchemy 객체를 딕셔너리로 변환 (published_at을 ISO8601로)"""
    d = {
        "id": news_obj.id,
        "title": news_obj.title,
        "link": news_obj.link,
        "source": news_obj.source,
        "summary": news_obj.summary,
        "thumbnail": news_obj.thumbnail,
        "category": news_obj.category,
        "views": news_obj.views,
        "score": news_obj.score,
    }
    # published_at을 ISO8601 문자열로 변환
    if news_obj.published_at:
        if isinstance(news_obj.published_at, datetime):
            d["published_at"] = news_obj.published_at.isoformat()
        else:
            d["published_at"] = str(news_obj.published_at)
    else:
        d["published_at"] = None
    return d

@router.get("/news")
def get_news(category: str = Query("kr", pattern="^(kr|world|crypto)$"),
             limit: int = Query(12, ge=1, le=50),
             sort: str = Query("score", pattern="^(score|views|published_at)$")):
    db = SessionLocal()
    try:
        q = db.query(News).filter(News.category == category)
        if sort == "score":
            q = q.order_by(desc(News.score))
        elif sort == "views":
            q = q.order_by(desc(News.views))
        else:
            q = q.order_by(desc(News.published_at))
        items = q.limit(limit).all()
        return {"ok": True, "count": len(items), "items": [_to_dict(n) for n in items]}
    finally:
        db.close()

@router.post("/news/view")
def add_view(id: int = Query(..., description="뉴스 ID")):
    db = SessionLocal()
    try:
        n = db.query(News).filter(News.id == id).first()
        if n:
            n.views += 1
            db.commit()
        return {"ok": True}
    finally:
        db.close()
