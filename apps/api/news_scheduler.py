import asyncio, httpx, feedparser, logging
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from .news_model import SessionLocal, News
from .news_score import calc_score

logger = logging.getLogger(__name__)

SOURCES = {
    "kr": [
        # 구글 뉴스 RSS (가장 안정적)
        "https://news.google.com/rss/search?q=코스피+주가&hl=ko&gl=KR&ceid=KR:ko",
        "https://news.google.com/rss/search?q=코스닥+지수&hl=ko&gl=KR&ceid=KR:ko",
        "https://news.google.com/rss/search?q=한국증시+종합&hl=ko&gl=KR&ceid=KR:ko",
        # 직접 RSS (리다이렉트 처리됨)
        "https://www.hankyung.com/feed/news",           # 한국경제 (stock → news로 변경)
        "https://www.mk.co.kr/rss/stock/",              # 매일경제 증권
        "https://biz.chosun.com/rss.xml",               # 조선비즈 전체
        "https://www.edaily.co.kr/rss/stock.xml",       # 이데일리 증권
        "https://www.etoday.co.kr/rss/section.xml?sec_no=121", # 이투데이 증권
    ],
    "crypto": [
        # 구글 뉴스 RSS
        "https://news.google.com/rss/search?q=비트코인+가격&hl=ko&gl=KR&ceid=KR:ko",
        "https://news.google.com/rss/search?q=가상자산+시장&hl=ko&gl=KR&ceid=KR:ko",
        # 직접 RSS (리다이렉트 처리됨)
        "https://www.blockmedia.co.kr/feed",            # 블록미디어 (www 추가)
        "https://www.coindeskkorea.com/feed",           # 코인데스크코리아 (/rss → /feed)
        "https://www.tokenpost.kr/rss",                 # 토큰포스트
    ]
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
    # 리다이렉트 자동 처리 (httpx는 기본적으로 follow_redirects=True)
    r = await client.get(url, timeout=20, follow_redirects=True)
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

