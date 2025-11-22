"""마켓 관련 모델 정의"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class MarketSegment(BaseModel):
    """마켓 세그먼트 타입"""
    pass


SegmentType = Literal["KR", "US", "CRYPTO", "COMMO"]


class MarketSummaryItem(BaseModel):
    """마켓 요약 항목"""

    index_name: str = Field(..., description="지수명")
    value: float = Field(..., description="현재 값")
    change: float = Field(..., description="변동")
    change_percent: float = Field(..., description="변동률 (%)")
    status: str = Field(..., description="상태 (UP/DOWN/FLAT)")


class MarketSummary(BaseModel):
    """마켓 요약 응답"""

    segment: SegmentType = Field(..., description="세그먼트")
    items: List[MarketSummaryItem] = Field(..., description="요약 항목 리스트")
    updated_at: str = Field(..., description="업데이트 시각")


class SectorItem(BaseModel):
    """섹터 항목"""

    sector_name: str = Field(..., description="섹터명")
    change_percent: float = Field(..., description="변동률 (%)")
    status: str = Field(..., description="상태 (UP/DOWN/FLAT)")


class MarketSectors(BaseModel):
    """마켓 섹터 응답"""

    segment: SegmentType = Field(..., description="세그먼트")
    sectors: List[SectorItem] = Field(..., description="섹터 리스트")
    updated_at: str = Field(..., description="업데이트 시각")


class FlowItem(BaseModel):
    """자금 흐름 항목"""

    name: str = Field(..., description="항목명")
    inflow: Optional[float] = Field(None, description="유입액")
    outflow: Optional[float] = Field(None, description="유출액")
    net: float = Field(..., description="순유입/순유출")


class MarketFlow(BaseModel):
    """마켓 자금 흐름 응답"""

    segment: SegmentType = Field(..., description="세그먼트")
    flows: List[FlowItem] = Field(..., description="자금 흐름 리스트")
    updated_at: str = Field(..., description="업데이트 시각")

