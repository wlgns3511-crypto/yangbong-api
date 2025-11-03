from fastapi import APIRouter, Query
from datetime import datetime, timezone
import httpx, feedparser

router = APIRouter(prefix="/api", tags=["news"])

# 카테고리별 RSS 소스 (안정/무난한 조합)
SOURCES = {
    "kr": [
        "https://www.yna.co.kr/rss/all-section.xml",
        "https://www.hankyung.com/feed/all-news",
        "https://www.edaily.co.kr/rss/rss_news.xml",
    ],
    "world": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://www.reuters.com/world/rss",
    ],
    "crypto": [
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://cointelegraph.com/rss",
        "https://www.theblock.co/rss",
    ],
}

def _first(*vals):
    for v in vals:
        if v:
            return v
    return None

def _to_iso8601(dt):
    if not dt:
        return None
    try:
        # feedparser에서 제공하는 시간 구조체 → ISO8601
        if isinstance(dt, tuple):
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(feedparser._parse_date_rfc822(dt)).astimezone(timezone.utc).isoformat()
        if isinstance(dt, str):
            # 가끔 문자열로만 오는 경우
            return datetime.fromisoformat(dt.replace("Z","+00:00")).astimezone(timezone.utc).isoformat()
    except Exception:
        return None
    return None

async def fetch_feed(client: httpx.AsyncClient, url: str):
    r = await client.get(url, timeout=15)
    r.raise_for_status()
    parsed = feedparser.parse(r.content)
    items = []
    for e in parsed.entries[:50]:
        # 썸네일 후보
        thumb = _first(
            getattr(e, "media_thumbnail", [{}])[0].get("url") if hasattr(e, "media_thumbnail") else None,
            getattr(e, "media_content", [{}])[0].get("url") if hasattr(e, "media_content") else None,
            getattr(e, "image", None),
            getattr(e, "thumbnail", None),
        )
        # 발행시각
        published = _first(getattr(e, "published", None), getattr(e, "updated", None))
        # 설명 요약
        summary = (getattr(e, "summary", "") or "").strip()
        if summary:
            # HTML 태그 제거 가볍게
            import re
            summary = re.sub("<.*?>", "", summary)
        items.append({
            "title": getattr(e, "title", "").strip(),
            "link": getattr(e, "link", ""),
            "source": parsed.feed.get("title", "")[:60],
            "summary": summary[:200],
            "thumbnail": thumb,
            "published_at": _to_iso8601(published),
        })
    return items

@router.get("/news")
async def get_news(category: str = Query("kr", pattern="^(kr|world|crypto)$"),
                   limit: int = Query(12, ge=1, le=50)):
    urls = SOURCES.get(category, [])
    out = []
    async with httpx.AsyncClient() as client:
        for url in urls:
            try:
                items = await fetch_feed(client, url)
                out.extend(items)
            except Exception:
                continue
    # 최신순 정렬
    def key_fn(x):
        ts = x.get("published_at")
        try:
            return datetime.fromisoformat(ts.replace("Z","+00:00")) if ts else datetime(1970,1,1, tzinfo=timezone.utc)
        except Exception:
            return datetime(1970,1,1, tzinfo=timezone.utc)
    out.sort(key=key_fn, reverse=True)
    return {"ok": True, "count": min(limit, len(out)), "items": out[:limit]}
