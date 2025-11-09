"""KRW 기준 암호화폐 시세 조회 (Upbit)."""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List

import requests

UPBIT_TICKER_ENDPOINT = "https://api.upbit.com/v1/ticker"
DEFAULT_SYMBOLS = "BTC,ETH,XRP,SOL,BNB"


def _to_upbit_markets(symbol_csv: str | None) -> List[str]:
    """심볼 CSV → Upbit KRW 마켓 코드 리스트."""
    if not symbol_csv:
        symbol_csv = DEFAULT_SYMBOLS
    base_symbols = [
        sym.strip().upper()
        for sym in symbol_csv.split(",")
        if sym.strip()
    ]
    return [f"KRW-{symbol}" for symbol in base_symbols]


def _fetch_upbit(markets: List[str]) -> List[Dict[str, Any]]:
    """Upbit ticker API 호출."""
    if not markets:
        return []

    response = requests.get(
        UPBIT_TICKER_ENDPOINT,
        params={"markets": ",".join(markets)},
        timeout=3,
    )
    response.raise_for_status()
    data = response.json()
    now = int(time.time())

    items: List[Dict[str, Any]] = []
    for row in data:
        market_code = row.get("market", "")
        symbol = market_code.split("-")[-1] if market_code else ""
        timestamp_ms = row.get("timestamp")
        ts = int(timestamp_ms // 1000) if timestamp_ms else now

        trade_price = row.get("trade_price")
        change_rate = row.get("signed_change_rate")
        change_price = row.get("signed_change_price")

        if trade_price is None:
            continue

        items.append(
            {
                "symbol": symbol,
                "name": symbol,
                "price": float(trade_price),
                "change": float(change_price or 0.0),
                "changeRate": float(change_rate or 0.0) * 100.0,
                "time": ts,
            }
        )

    return items


def fetch_crypto_markets(symbol_csv: str | None = None) -> List[Dict[str, Any]]:
    """환경 변수 심볼 리스트를 KRW 마켓으로 변환 후 실시간 조회."""
    sym_csv = symbol_csv or os.getenv("NEXT_PUBLIC_CRYPTO_LIST", DEFAULT_SYMBOLS)
    markets = _to_upbit_markets(sym_csv)
    return _fetch_upbit(markets)

