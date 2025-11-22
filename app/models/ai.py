"""AI 관련 모델 정의"""

from pydantic import BaseModel, Field


class MarketBriefingResponse(BaseModel):
    """마켓 브리핑 응답"""

    briefing: str = Field(..., description="브리핑 내용")
    summary: str = Field(..., description="요약")
    key_points: list[str] = Field(..., description="핵심 포인트")
    generated_at: str = Field(..., description="생성 시각 (ISO 8601)")

