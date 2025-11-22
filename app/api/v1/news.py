"""뉴스 API 라우터"""

from fastapi import APIRouter, Path, Query, HTTPException
from app.models.schemas import APIResponse
from app.services.news_service import NewsService

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/list")
async def get_news_list(
    category: str = Query(default="전체", description="카테고리"),
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=20, ge=1, le=100, description="페이지당 개수")
) -> APIResponse:
    """뉴스 리스트 조회"""
    try:
        data = await NewsService.get_news_list(category, page, limit)
        return APIResponse.success_response(data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.get("/breaking")
async def get_breaking_news(
    limit: int = Query(default=5, ge=1, le=50, description="조회 개수")
) -> APIResponse:
    """속보 뉴스 조회"""
    try:
        data = await NewsService.get_breaking_news(limit)
        return APIResponse.success_response(data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.get("/{news_id}")
async def get_news_detail(
    news_id: str = Path(..., description="뉴스 ID")
) -> APIResponse:
    """뉴스 상세 조회"""
    try:
        data = await NewsService.get_news_detail(news_id)
        return APIResponse.success_response(data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

