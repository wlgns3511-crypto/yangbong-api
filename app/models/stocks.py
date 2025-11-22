"""주식 관련 모델 정의"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


MarketType = Literal["KR", "US"]


class StockItem(BaseModel):
    """주식 항목"""

    symbol: str = Field(..., description="종목 코드")
    name: str = Field(..., description="종목명")
    price: float = Field(..., description="현재가")
    change: float = Field(..., description="변동액")
    change_percent: float = Field(..., description="변동률 (%)")
    volume: Optional[int] = Field(None, description="거래량")
    market: MarketType = Field(..., description="시장 (KR/US)")


class PopularStocksResponse(BaseModel):
    """인기 주식 응답"""

    market: MarketType = Field(..., description="시장")
    stocks: list[StockItem] = Field(..., description="주식 리스트")


class SurgingStocksResponse(BaseModel):
    """급등 주식 응답"""

    stocks: list[StockItem] = Field(..., description="주식 리스트")
    mix: bool = Field(..., description="믹스 여부")

