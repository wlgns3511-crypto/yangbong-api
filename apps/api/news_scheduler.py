import asyncio, httpx, feedparser, logging
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from .news_model import SessionLocal, News
from .news_score import calc_score

logger = logging.getLogger(__name__)

SOURCES = {
    "kr": [
        "https://www.hankyung.com/feed/stock",
        "https://www.mk.co.kr/rss/30100041/",
        "https://www.edaily.co.kr/rss/news/stock.xml",
        "https://biz.chosun.com/rss/stock.xml",
        "https://www.etoday.co.kr/rss/news/economy.xml",
        "https://www.sedaily.com/rss/Economy.xml",
        "https://www.moneys.co.kr/rss/economy.xml",
    ],
    "crypto": [
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://cointelegraph.com/rss",
        "https://kr.investing.com/rss/news_301.rss",
    ],
    "world": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://www.reuters.com/world/rss",
    ],
}

def _first(*vals):
    for v in vals:
        if v:
            return v
    return None

def _to_datetime(dt):
    if not dt:
        return datetime.utcnow()
    try:
        if isinstance(dt, tuple):
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(feedparser._parse_date_rfc822(dt)).replace(tzinfo=None)
        if isinstance(dt, str):
            try:
                parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
                if parsed.tzinfo:
                    parsed = parsed.replace(tzinfo=None)
                return parsed
            except:
                return datetime.utcnow()
        if isinstance(dt, datetime):
            if dt.tzinfo:
                return dt.replace(tzinfo=None)
            return dt
    except Exception:
        pass
    return datetime.utcnow()

async def fetch_feed(client, url):
    r = await client.get(url, timeout=20)
    r.raise_for_status()
    parsed = feedparser.parse(r.content)
    out = []
    for e in parsed.entries[:50]:
        summary = (getattr(e, "summary", "") or "").strip()
        if summary:
            import re
            summary = re.sub("<.*?>", "", summary)
        
        thumb = _first(
            getattr(e, "media_thumbnail", [{}])[0].get("url") if hasattr(e, "media_thumbnail") else None,
            getattr(e, "media_content", [{}])[0].get("url") if hasattr(e, "media_content") else None,
            getattr(e, "image", None),
            getattr(e, "thumbnail", None),
        )
        
        published = _first(getattr(e, "published", None), getattr(e, "updated", None))
        
        out.append({
            "title": getattr(e, "title", "").strip(),
            "link": getattr(e, "link", ""),
            "summary": summary[:300],
            "source": parsed.feed.get("title", "")[:100],
            "thumbnail": thumb,
            "published_at": _to_datetime(published),
        })
    return out

async def collect_news():
    async with httpx.AsyncClient() as client:
        all_items = []
        for cat, urls in SOURCES.items():
            for u in urls:
                try:
                    items = await fetch_feed(client, u)
                    for item in items:
                        item["category"] = cat
                        item["score"] = calc_score(item)
                        all_items.append(item)
                except Exception as e:
                    logger.warning(f"❌ Feed fail {u}: {e}")

        db = SessionLocal()
        added_count = 0
        for n in all_items:
            try:
                db.add(News(**n))
                db.commit()
                added_count += 1
            except IntegrityError:
                db.rollback()
        db.close()
        logger.info(f"✅ 뉴스 수집 완료: {added_count}개 신규 추가 / {len(all_items)}개 전체")

async def run_loop():
    # 시작 시 즉시 한 번 실행
    await collect_news()
    # 이후 10분마다 반복
    while True:
        await asyncio.sleep(600)  # 10분마다 실행
        await collect_news()

