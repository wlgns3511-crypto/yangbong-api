"""뉴스 서비스"""

from app.models.news import NewsItem, NewsListResponse, NewsDetail
from datetime import datetime, timedelta


class NewsService:
    """뉴스 관련 비즈니스 로직"""

    @staticmethod
    async def get_news_list(
        category: str = "전체",
        page: int = 1,
        limit: int = 20,
    ) -> NewsListResponse:
        """뉴스 리스트 조회 (Mock 데이터)"""
        # TODO: 실제 Supabase 또는 외부 API 연동으로 교체
        
        # Mock 데이터 생성
        all_categories = ["전체", "증시", "경제", "산업", "정치", "국제"]
        if category != "전체":
            categories = [category]
        else:
            categories = all_categories[1:]  # "전체" 제외
        
        mock_items = []
        base_time = datetime.utcnow() - timedelta(hours=1)
        
        for i in range(limit):
            category_name = categories[i % len(categories)]
            item_time = base_time - timedelta(minutes=i * 10)
            
            mock_items.append(
                NewsItem(
                    id=f"news-{i+1:04d}",
                    title=f"{category_name} 관련 뉴스 제목 {i+1}",
                    summary=f"{category_name} 분야의 중요한 뉴스 요약 내용입니다.",
                    source=f"출처{i+1}",
                    category=category_name,
                    published_at=item_time.isoformat() + "Z",
                    url=f"https://example.com/news/{i+1}",
                    image_url=f"https://example.com/images/news-{i+1}.jpg",
                    is_breaking=(i < 2),  # 처음 2개를 속보로 설정
                )
            )
        
        # 페이지네이션 적용
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_items = mock_items[start_idx:end_idx]
        
        # Mock total (실제로는 DB 쿼리 결과)
        total = 100  # 예시값
        
        return NewsListResponse(
            items=paginated_items,
            total=total,
            page=page,
            limit=limit,
            has_more=end_idx < total,
        )

    @staticmethod
    async def get_breaking_news(limit: int = 5) -> list[NewsItem]:
        """속보 뉴스 조회 (Mock 데이터)"""
        # TODO: 실제 Supabase 또는 외부 API 연동으로 교체
        
        mock_items = []
        base_time = datetime.utcnow() - timedelta(minutes=10)
        
        for i in range(limit):
            item_time = base_time - timedelta(minutes=i * 2)
            mock_items.append(
                NewsItem(
                    id=f"breaking-{i+1:04d}",
                    title=f"속보: 중요 뉴스 제목 {i+1}",
                    summary="속보 뉴스의 요약 내용입니다.",
                    source=f"속보출처{i+1}",
                    category="증시",
                    published_at=item_time.isoformat() + "Z",
                    url=f"https://example.com/news/breaking-{i+1}",
                    image_url=f"https://example.com/images/breaking-{i+1}.jpg",
                    is_breaking=True,
                )
            )
        
        return mock_items

    @staticmethod
    async def get_news_detail(news_id: str) -> NewsDetail:
        """뉴스 상세 조회 (Mock 데이터)"""
        # TODO: 실제 Supabase 또는 외부 API 연동으로 교체
        
        return NewsDetail(
            id=news_id,
            title="뉴스 상세 제목",
            content=(
                "이것은 뉴스의 본문 내용입니다.\n\n"
                "여러 단락으로 구성된 뉴스 내용을 여기에 표시합니다.\n\n"
                "중요한 정보와 분석 내용이 포함되어 있습니다."
            ),
            summary="뉴스의 요약 내용입니다.",
            source="출처명",
            category="증시",
            published_at=(datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z",
            url=f"https://example.com/news/{news_id}",
            image_url=f"https://example.com/images/{news_id}.jpg",
            is_breaking=False,
            tags=["주식", "증시", "투자"],
        )

