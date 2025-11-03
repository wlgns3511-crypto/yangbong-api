from fastapi import APIRouter, Query
from sqlalchemy import desc, or_
from datetime import datetime
from .news_model import SessionLocal, News

router = APIRouter(prefix="/api", tags=["news"])

WORLD_KWS = [
    # 지수/시장
    "나스닥", "다우", "S&P", "S&P500", "S&P 500", "미 증시", "뉴욕증시", "월가", "FOMC", "연준", "금리 인하", "고용지표",
    # 미국/해외 일반
    "미국", "유럽", "중국", "일본", "환율", "달러", "미 국채", "미 10년물",
    # 대표 종목/기업 (한글+영문 혼용)
    "테슬라", "TSLA", "아이온큐", "IonQ", "엔비디아", "NVIDIA", "NVDA",
    "애플", "Apple", "AAPL", "마이크로소프트", "MSFT", "아마존", "AMZN",
    "알파벳", "구글", "GOOGL", "메타", "META", "넷플릭스", "NFLX",
    "TSMC", "브로드컴", "AVGO", "ARM", "AMD", "퀄컴", "QUALCOMM",
    # 크립토 대형 키워드(원하면)
    "비트코인 ETF", "스팟 ETF", "SEC", "코인베이스", "Coinbase"
]

def _world_filter(q):
    like_conds = []
    for kw in WORLD_KWS:
        like = f"%{kw}%"
        like_conds.append(News.title.ilike(like))
        like_conds.append(News.summary.ilike(like))
    return q.filter(News.category == "kr").filter(or_(*like_conds))

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
        if category == "world":
            q = _world_filter(db.query(News))
        else:
            q = db.query(News).filter(News.category == category)

        if sort == "views":
            q = q.order_by(desc(News.views))
        elif sort == "score":
            q = q.order_by(desc(News.score))
        else:
            q = q.order_by(desc(News.published_at))

        items = q.limit(limit).all()

        # world가 비면 kr 상위로 폴백 (빈 화면 방지)
        if category == "world" and not items:
            items = (
                db.query(News)
                .filter(News.category == "kr")
                .order_by(desc(News.score))
                .limit(limit)
                .all()
            )

        return {"ok": True, "count": len(items), "items": [_to_dict(n) for n in items]}
    finally:
        db.close()

@router.get("/news/{id}")
def get_news_detail(id: int):
    db = SessionLocal()
    try:
        n = db.query(News).filter(News.id == id).first()
        if not n:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="News not found")
        # 조회수 증가
        n.views += 1
        db.commit()
        return _to_dict(n)
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
