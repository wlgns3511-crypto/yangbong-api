"""뉴스 관련 모델 정의"""

from typing import Optional
from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    """뉴스 항목"""

    id: str = Field(..., description="뉴스 ID")
    title: str = Field(..., description="제목")
    summary: Optional[str] = Field(None, description="요약")
    source: str = Field(..., description="출처")
    category: str = Field(..., description="카테고리")
    published_at: str = Field(..., description="발행 시각 (ISO 8601)")
    url: Optional[str] = Field(None, description="링크 URL")
    image_url: Optional[str] = Field(None, description="이미지 URL")
    is_breaking: bool = Field(default=False, description="속보 여부")


class NewsListResponse(BaseModel):
    """뉴스 리스트 응답"""

    items: list[NewsItem] = Field(..., description="뉴스 항목 리스트")
    total: int = Field(..., description="전체 개수")
    page: int = Field(..., description="현재 페이지")
    limit: int = Field(..., description="페이지당 개수")
    has_more: bool = Field(..., description="다음 페이지 존재 여부")


class NewsDetail(BaseModel):
    """뉴스 상세"""

    id: str = Field(..., description="뉴스 ID")
    title: str = Field(..., description="제목")
    content: str = Field(..., description="본문")
    summary: Optional[str] = Field(None, description="요약")
    source: str = Field(..., description="출처")
    category: str = Field(..., description="카테고리")
    published_at: str = Field(..., description="발행 시각 (ISO 8601)")
    url: Optional[str] = Field(None, description="링크 URL")
    image_url: Optional[str] = Field(None, description="이미지 URL")
    is_breaking: bool = Field(default=False, description="속보 여부")
    tags: list[str] = Field(default_factory=list, description="태그 리스트")

