from fastapi import APIRouter, Query
import requests
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/api/news", tags=["news"])


async def fetch_news(tab: str, page: int = 1, page_size: int = 10) -> dict:
    """뉴스 조회 (한국/글로벌/암호화폐)"""
    items = []
    
    # 간단한 RSS 피드 기반 구현
    feeds = {
        "kr": [
            "https://news.naver.com/main/rss/section.naver?sid=101",  # 경제
            "https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258"
        ],
        "global": [
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^DJI&region=US&lang=en-US",
            "https://www.cnbc.com/id/100003114/device/rss/rss.html"
        ],
        "crypto": [
            "https://cointelegraph.com/rss",
            "https://decrypt.co/feed"
        ]
    }
    
    feed_urls = feeds.get(tab, [])
    
    try:
        # 예시: RSS 피드 파싱 (간단한 버전)
        # 실제로는 feedparser 라이브러리를 사용하는 것이 좋음
        for url in feed_urls[:1]:  # 첫 번째 피드만 사용
            try:
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                # 실제 RSS 파싱은 feedparser 사용 권장
                # 여기서는 간단한 구조만 반환
            except Exception as e:
                print(f"[News feed error] {e}")
        
        # 임시 더미 데이터 (실제로는 RSS 파싱 결과)
        items = [
            {
                "title": f"{tab.upper()} 뉴스 샘플",
                "summary": "뉴스 요약 내용입니다.",
                "source": "연합" if tab == "kr" else "Reuters",
                "url": "https://example.com/news/1",
                "image": None,
                "published_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        ]
    except Exception as e:
        print(f"[News fetch error] {e}")
    
    # 페이지네이션
    start = (page - 1) * page_size
    end = start + page_size
    paginated_items = items[start:end]
    
    return {
        "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tab": tab,
        "items": paginated_items
    }


@router.get("")
async def news(
    tab: str = Query(..., description="뉴스 탭: kr, global, crypto"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    from cache import get_cache, put_cache
    
    cache_key = f"news_{tab}_{page}_{page_size}"
    data = get_cache(cache_key)
    if data:
        return data
    
    data = await fetch_news(tab, page, page_size)
    put_cache(cache_key, data, ttl=300)  # 뉴스는 5분 캐시
    return data

