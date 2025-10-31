from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import feedparser, time, hashlib, requests
from bs4 import BeautifulSoup

app = FastAPI(title="yangbong-api")

# CORS 설정
origins = [
    "https://yangbong.club",           # Vercel Production (메인 사이트)
    "https://yangbong-web.vercel.app", # Preview 환경 (테스트 배포용)
    "http://localhost:3000",           # 로컬 개발용
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # 허용할 프론트 주소들
    allow_credentials=True,
    allow_methods=["*"],          # 모든 HTTP 메서드 허용 (GET, POST 등)
    allow_headers=["*"],          # 모든 헤더 허용
)

class NewsItem(BaseModel):
    id: str
    title: str
    link: str
    source: str
    published_at: str
    thumbnail: Optional[str] = None
    summary: Optional[str] = None

FEEDS = {
    "kr": [
        # 경제/증시 위주 RSS (원하면 더 추가 가능)
        "https://rss.etnews.com/section020.xml",
        "https://www.hankyung.com/feed/all-news",
        "https://biz.chosun.com/arc/outboundfeeds/rss/category/economy/?outputType=xml",
    ],
    "us": [
        "https://feeds.marketwatch.com/marketwatch/topstories/",
        "https://www.wsj.com/news/markets?mod=rss_markets_main",
    ],
    "crypto": [
        "https://www.coindeskkorea.com/rss/allArticle.xml",
        "https://www.blockmedia.co.kr/rss/allArticle.xml",
    ],
}

def _clean_html(t: str) -> str:
    if not t: return ""
    return BeautifulSoup(t, "lxml").get_text(" ", strip=True)

def _og_image(url: str) -> str | None:
    try:
        html = requests.get(url, timeout=3).text
        soup = BeautifulSoup(html, "lxml")
        og = soup.find("meta", property="og:image")
        return og["content"] if og and og.get("content") else None
    except Exception:
        return None

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/api/news")
def api_news(
    type: str = Query("kr", pattern="^(kr|us|crypto)$"),
    limit: int = Query(12, ge=1, le=50),
    sort: str = Query("latest", pattern="^(latest|popular)$"),
):
    urls = FEEDS.get(type, [])
    items: list[NewsItem] = []

    for feed_url in urls:
        d = feedparser.parse(feed_url)
        for e in d.entries[:50]:
            title = e.get("title", "").strip()
            link = e.get("link", "").strip()
            source = (e.get("source", {}) or {}).get("title") or d.feed.get("title") or "news"
            summary = _clean_html(e.get("summary", ""))
            # published
            ts = e.get("published_parsed") or e.get("updated_parsed") or time.gmtime()
            published_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", ts)
            # id/thumbnail
            nid = hashlib.md5(link.encode()).hexdigest()
            thumb = _og_image(link)

            items.append(NewsItem(
                id=nid, title=title, link=link, source=source,
                published_at=published_at, thumbnail=thumb, summary=summary
            ))

    # 정렬: 최신
    items.sort(key=lambda x: x.published_at, reverse=True)
    return {
        "ok": True,
        "items": [i.model_dump() for i in items[:limit]],
        "total": len(items),
        "next_cursor": None,
    }

@app.get("/news", include_in_schema=False)
def list_news_compat(
    type: str = Query("kr"),
    limit: int = Query(12, ge=1, le=50),
    sort: Optional[str] = Query(None),
):
    # 내부에서 실제 /api/news 핸들러를 호출
    return api_news(type=type, limit=limit, sort=sort or "latest")