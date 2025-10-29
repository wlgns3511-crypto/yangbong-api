from fastapi import APIRouter, Query
import requests
from datetime import datetime

router = APIRouter(prefix="/api/crypto", tags=["crypto"])


async def fetch_crypto_tickers(symbols: list[str]) -> dict:
    """암호화폐 시세 조회 (업비트 KRW + 바이낸스 USDT)"""
    items = []
    
    # 원/달러 환율 조회 (예: 네이버 환율 또는 API)
    krw_usd = 1377.0  # 기본값 (실제로는 환율 API에서 조회)
    try:
        # 간단한 환율 조회 (스토크 등에서 USDKRW=X)
        url = "https://stooq.com/q/l/?s=usdkrw=x&f=sd2t2ohlcv&h&e=csv"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        lines = r.text.strip().split('\n')
        if len(lines) > 1:
            parts = lines[1].split(',')
            if len(parts) > 1 and parts[1]:
                krw_usd = float(parts[1])
    except Exception as e:
        print(f"[USDKRW fetch error] {e}, using default")
    
    for symbol in symbols:
        symbol_upper = symbol.upper().strip()
        if not symbol_upper:
            continue
        
        try:
            # 업비트 API (KRW 가격)
            upbit_url = f"https://api.upbit.com/v1/ticker?markets=KRW-{symbol_upper}"
            upbit_r = requests.get(upbit_url, timeout=10)
            
            price_krw = None
            if upbit_r.status_code == 200:
                upbit_data = upbit_r.json()
                if upbit_data and isinstance(upbit_data, list) and len(upbit_data) > 0:
                    price_krw = float(upbit_data[0].get("trade_price", 0))
            
            # 바이낸스 API (USDT 가격)
            binance_url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol_upper}USDT"
            binance_r = requests.get(binance_url, timeout=10)
            
            price_usdt = None
            if binance_r.status_code == 200:
                binance_data = binance_r.json()
                if binance_data and "price" in binance_data:
                    price_usdt = float(binance_data["price"])
            
            if price_krw and price_usdt:
                # 김프 계산: 100 * (업비트 KRW가격 / (바이낸스 USDT가격 × 원/달러) - 1)
                kimchi_pct = 100 * (price_krw / (price_usdt * krw_usd) - 1)
                
                items.append({
                    "symbol": symbol_upper,
                    "price_krw": round(price_krw, 0),
                    "price_usdt": round(price_usdt, 2),
                    "krw_usd": round(krw_usd, 2),
                    "kimchi_pct": round(kimchi_pct, 2)
                })
        except Exception as e:
            print(f"[Crypto {symbol_upper} fetch error] {e}")
            continue
    
    return {
        "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "items": items
    }


@router.get("/tickers")
async def tickers(list: str = Query(..., description="암호화폐 심볼 목록 (쉼표 구분)")):
    from cache import get_cache, put_cache
    
    cache_key = f"crypto_{list}"
    data = get_cache(cache_key)
    if data:
        return data
    
    symbols = [s.strip() for s in list.split(",")]
    data = await fetch_crypto_tickers(symbols)
    put_cache(cache_key, data, ttl=60)
    return data

