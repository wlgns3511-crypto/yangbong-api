"""마켓 서비스"""

from typing import Literal
from app.models.market import (
    MarketSummary,
    MarketSectors,
    MarketFlow,
    SegmentType,
    MarketSummaryItem,
    SectorItem,
    FlowItem,
)
from datetime import datetime


class MarketService:
    """마켓 관련 비즈니스 로직"""

    @staticmethod
    async def get_market_summary(seg: SegmentType) -> MarketSummary:
        """마켓 요약 조회 (Mock 데이터)"""
        # TODO: 실제 외부 API 연동으로 교체
        mock_items = []
        
        if seg == "KR":
            mock_items = [
                MarketSummaryItem(
                    index_name="KOSPI",
                    value=2500.5,
                    change=15.2,
                    change_percent=0.61,
                    status="UP",
                ),
                MarketSummaryItem(
                    index_name="KOSDAQ",
                    value=850.3,
                    change=-5.1,
                    change_percent=-0.60,
                    status="DOWN",
                ),
            ]
        elif seg == "US":
            mock_items = [
                MarketSummaryItem(
                    index_name="S&P 500",
                    value=4500.2,
                    change=25.5,
                    change_percent=0.57,
                    status="UP",
                ),
                MarketSummaryItem(
                    index_name="NASDAQ",
                    value=14000.8,
                    change=45.3,
                    change_percent=0.32,
                    status="UP",
                ),
            ]
        elif seg == "CRYPTO":
            mock_items = [
                MarketSummaryItem(
                    index_name="BTC",
                    value=42000.5,
                    change=850.2,
                    change_percent=2.07,
                    status="UP",
                ),
                MarketSummaryItem(
                    index_name="ETH",
                    value=2200.3,
                    change=35.1,
                    change_percent=1.62,
                    status="UP",
                ),
            ]
        elif seg == "COMMO":
            mock_items = [
                MarketSummaryItem(
                    index_name="WTI",
                    value=75.5,
                    change=-1.2,
                    change_percent=-1.56,
                    status="DOWN",
                ),
                MarketSummaryItem(
                    index_name="Gold",
                    value=2000.8,
                    change=5.5,
                    change_percent=0.28,
                    status="UP",
                ),
            ]

        return MarketSummary(
            segment=seg,
            items=mock_items,
            updated_at=datetime.utcnow().isoformat() + "Z",
        )

    @staticmethod
    async def get_market_sectors(seg: SegmentType) -> MarketSectors:
        """마켓 섹터 조회 (Mock 데이터)"""
        # TODO: 실제 외부 API 연동으로 교체
        mock_sectors = []
        
        if seg == "KR":
            mock_sectors = [
                SectorItem(sector_name="기술", change_percent=1.5, status="UP"),
                SectorItem(sector_name="금융", change_percent=-0.8, status="DOWN"),
                SectorItem(sector_name="에너지", change_percent=2.1, status="UP"),
                SectorItem(sector_name="바이오", change_percent=0.3, status="UP"),
            ]
        elif seg == "US":
            mock_sectors = [
                SectorItem(sector_name="Technology", change_percent=1.2, status="UP"),
                SectorItem(sector_name="Finance", change_percent=-0.5, status="DOWN"),
                SectorItem(sector_name="Healthcare", change_percent=0.8, status="UP"),
            ]
        else:
            mock_sectors = [
                SectorItem(sector_name="Sector 1", change_percent=0.5, status="UP"),
                SectorItem(sector_name="Sector 2", change_percent=-0.3, status="DOWN"),
            ]

        return MarketSectors(
            segment=seg,
            sectors=mock_sectors,
            updated_at=datetime.utcnow().isoformat() + "Z",
        )

    @staticmethod
    async def get_market_flow(seg: SegmentType) -> MarketFlow:
        """마켓 자금 흐름 조회 (Mock 데이터)"""
        # TODO: 실제 외부 API 연동으로 교체
        mock_flows = []
        
        if seg == "KR":
            mock_flows = [
                FlowItem(name="기관", inflow=5000000000.0, outflow=3000000000.0, net=2000000000.0),
                FlowItem(name="외국인", inflow=3000000000.0, outflow=4000000000.0, net=-1000000000.0),
                FlowItem(name="개인", inflow=2000000000.0, outflow=3000000000.0, net=-1000000000.0),
            ]
        elif seg == "US":
            mock_flows = [
                FlowItem(name="Institutions", inflow=10000000000.0, outflow=8000000000.0, net=2000000000.0),
                FlowItem(name="Foreign", inflow=5000000000.0, outflow=3000000000.0, net=2000000000.0),
            ]
        else:
            mock_flows = [
                FlowItem(name="Flow 1", inflow=1000000.0, outflow=500000.0, net=500000.0),
                FlowItem(name="Flow 2", inflow=800000.0, outflow=900000.0, net=-100000.0),
            ]

        return MarketFlow(
            segment=seg,
            flows=mock_flows,
            updated_at=datetime.utcnow().isoformat() + "Z",
        )

