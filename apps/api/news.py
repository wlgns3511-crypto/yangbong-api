# -*- coding: utf-8 -*-
import feedparser
from fastapi import APIRouter, Query
from urllib.parse import quote

router = APIRouter()


def _feed(url: str, limit: int, source_hint: str = ""):
    d = feedparser.parse(url)
    out = []
    for e in d.entries[:limit]:
        # Google News RSS는 언론사가 e.source.title 에 들어있음
        pub = ""
        try:
            pub = getattr(getattr(e, "source", None), "title", "") or source_hint
        except Exception:
            pub = source_hint

        out.append({
            "title": getattr(e, "title", "제목 없음"),
            "url": getattr(e, "link", "#"),
            "source": pub,  # ← 여기만 바뀜
            "published_at": getattr(e, "published", "") or getattr(e, "updated", ""),
            "image": None,
        })
    return out


def get_news_kr(limit: int):
    # 최근 12시간 한국어 경제/증시 기사 (Google News RSS)
    q = quote("증권 OR 코스피 OR 주식 when:12h")
    url = f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
    return _feed(url, limit, "Google News(ko)")


def get_news_us(limit: int):
    # 미국 증시 키워드
    q = quote("stock market OR nasdaq OR s&p500 when:12h")
    url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
    return _feed(url, limit, "Google News(en)")


def get_news_crypto(limit: int):
    urls = [
        "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml",
        "https://cointelegraph.com/rss",
    ]
    items = []
    for u in urls:
        items += _feed(u, limit, "Crypto")
        if len(items) >= limit: break
    return items[:limit]


@router.get("/news")
def news(type: str = Query("kr", regex="^(kr|us|crypto)$"), limit: int = 10):
    if type == "kr":
        data = get_news_kr(limit)
    elif type == "us":
        data = get_news_us(limit)
    else:
        data = get_news_crypto(limit)
    return {"status": "ok", "type": type, "limit": limit, "data": data}

