# apps/api/news.py
import time
import logging
from typing import List, Dict

import requests
import feedparser

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ✅ 2025-11 기준 동작 확인한 피드들 (주식/경제 위주)
FEEDS = [
    "https://www.hankyung.com/feed/news",
    "https://www.mk.co.kr/rss/stock/",                    # 매일경제 증권
    "https://biz.chosun.com/rss.xml",                     # 조선비즈 전체
    "https://www.edaily.co.kr/rss/stock.xml",             # 이데일리 증권
    "https://www.etoday.co.kr/rss/section.xml?sec_no=121" # 이투데이 증권
]

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def _download(url: str) -> bytes:
    try:
        res = requests.get(url, headers=UA, timeout=10, allow_redirects=True)
        if res.status_code == 404:
            logger.warning(f"[RSS] 404 for {url}")
            return b""
        res.raise_for_status()
        return res.content
    except Exception as e:
        logger.warning(f"[RSS] fetch fail {url}: {e}")
        return b""


def fetch_hot_news(limit_per_feed: int = 20, total_limit: int = 60) -> List[Dict]:
    items: List[Dict] = []
    for url in FEEDS:
        raw = _download(url)
        if not raw:
            continue
        try:
            feed = feedparser.parse(raw)
            entries = feed.get("entries", [])[:limit_per_feed]
            for e in entries:
                title = e.get("title", "").strip()
                link = e.get("link")
                summary = (e.get("summary") or e.get("description") or "").strip()
                published = e.get("published") or e.get("updated")
                items.append({
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "published": published,
                    "source": feed.get("feed", {}).get("title", ""),
                })
        except Exception as pe:
            logger.warning(f"[RSS] parse fail {url}: {pe}")
        time.sleep(0.1)  # 너무 빠른 연속요청 방지

    # 간단 정렬: 최신순(발행일 문자열이 없으면 뒤로)
    def _key(x):
        return x.get("published") or ""

    items.sort(key=_key, reverse=True)
    return items[:total_limit]
