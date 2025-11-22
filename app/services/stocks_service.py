"""주식 서비스"""

from app.models.stocks import (
    PopularStocksResponse,
    SurgingStocksResponse,
    StockItem,
    MarketType,
)


class StocksService:
    """주식 관련 비즈니스 로직"""

    @staticmethod
    async def get_popular_stocks(market: MarketType, limit: int = 6) -> PopularStocksResponse:
        """인기 주식 조회 (Mock 데이터)"""
        # TODO: 실제 외부 API 연동으로 교체
        mock_stocks = []
        
        if market == "KR":
            mock_stocks = [
                StockItem(
                    symbol="005930",
                    name="삼성전자",
                    price=65000.0,
                    change=1000.0,
                    change_percent=1.56,
                    volume=10000000,
                    market="KR",
                ),
                StockItem(
                    symbol="000660",
                    name="SK하이닉스",
                    price=120000.0,
                    change=-2000.0,
                    change_percent=-1.64,
                    volume=5000000,
                    market="KR",
                ),
                StockItem(
                    symbol="035420",
                    name="NAVER",
                    price=200000.0,
                    change=3000.0,
                    change_percent=1.52,
                    volume=2000000,
                    market="KR",
                ),
            ]
        else:  # US
            mock_stocks = [
                StockItem(
                    symbol="AAPL",
                    name="Apple Inc.",
                    price=175.5,
                    change=2.3,
                    change_percent=1.33,
                    volume=50000000,
                    market="US",
                ),
                StockItem(
                    symbol="MSFT",
                    name="Microsoft Corporation",
                    price=380.2,
                    change=-1.5,
                    change_percent=-0.39,
                    volume=20000000,
                    market="US",
                ),
                StockItem(
                    symbol="GOOGL",
                    name="Alphabet Inc.",
                    price=140.8,
                    change=1.2,
                    change_percent=0.86,
                    volume=15000000,
                    market="US",
                ),
            ]

        # limit 적용
        mock_stocks = mock_stocks[:limit]

        return PopularStocksResponse(market=market, stocks=mock_stocks)

    @staticmethod
    async def get_surging_stocks(limit: int = 6, mix: bool = True) -> SurgingStocksResponse:
        """급등 주식 조회 (Mock 데이터)"""
        # TODO: 실제 외부 API 연동으로 교체
        mock_stocks = []
        
        if mix:
            # KR과 US 믹스
            mock_stocks = [
                StockItem(
                    symbol="035720",
                    name="카카오",
                    price=55000.0,
                    change=3500.0,
                    change_percent=6.80,
                    volume=8000000,
                    market="KR",
                ),
                StockItem(
                    symbol="TSLA",
                    name="Tesla, Inc.",
                    price=250.5,
                    change=12.3,
                    change_percent=5.16,
                    volume=100000000,
                    market="US",
                ),
                StockItem(
                    symbol="207940",
                    name="삼성바이오로직스",
                    price=750000.0,
                    change=20000.0,
                    change_percent=2.74,
                    volume=100000,
                    market="KR",
                ),
                StockItem(
                    symbol="NVDA",
                    name="NVIDIA Corporation",
                    price=500.2,
                    change=18.5,
                    change_percent=3.84,
                    volume=50000000,
                    market="US",
                ),
            ]
        else:
            # KR만
            mock_stocks = [
                StockItem(
                    symbol="035720",
                    name="카카오",
                    price=55000.0,
                    change=3500.0,
                    change_percent=6.80,
                    volume=8000000,
                    market="KR",
                ),
                StockItem(
                    symbol="207940",
                    name="삼성바이오로직스",
                    price=750000.0,
                    change=20000.0,
                    change_percent=2.74,
                    volume=100000,
                    market="KR",
                ),
            ]

        # limit 적용
        mock_stocks = mock_stocks[:limit]

        return SurgingStocksResponse(stocks=mock_stocks, mix=mix)

