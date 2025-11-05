# apps/api/news.py
import time
import logging
from typing import List, Dict

import feedparser
from .utils_feed import fetch_url

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ✅ 최신 RSS 소스 (구글 뉴스 RSS + 직접 RSS 혼합)
RSS_SOURCES = [
    # 구글 뉴스 RSS (가장 안정적)
    "https://news.google.com/rss/search?q=코스피+주가&hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/search?q=코스닥+지수&hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/search?q=한국증시+종합&hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/search?q=비트코인+가격&hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/search?q=가상자산+시장&hl=ko&gl=KR&ceid=KR:ko",
    # 직접 RSS (변동 가능 - 실패 시 miss에 기록)
    "https://www.blockmedia.co.kr/feed",
    "https://www.coindeskkorea.com/feed",
    "https://www.hankyung.com/feed/news",
    "https://www.mk.co.kr/rss/stock/",
    "https://biz.chosun.com/rss.xml",
    "https://www.edaily.co.kr/rss/stock.xml",
    "https://www.etoday.co.kr/rss/section.xml?sec_no=121",
]


def _download(url: str) -> bytes:
    """리다이렉트를 따라가며 RSS 피드 다운로드"""
    try:
        sc, final_url, body = fetch_url(url, max_hops=3, timeout=8)
        if sc != 200:
            logger.info(f"[RSS] {sc} for {url} (final: {final_url})")
            return b""
        return body.encode('utf-8') if isinstance(body, str) else body
    except Exception as e:
        logger.warning(f"[RSS] fetch fail {url}: {e}")
        return b""


def fetch_hot_news(limit_per_feed: int = 20, total_limit: int = 60) -> List[Dict]:
    """RSS 피드 수집 (리다이렉트 처리 포함)"""
    items: List[Dict] = []
    for url in RSS_SOURCES:
        raw = _download(url)
        if not raw:
            continue
        try:
            # feedparser가 자체적으로 리다이렉트/인코딩 처리
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
