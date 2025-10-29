from fastapi import APIRouter
import requests
import csv
import io
from datetime import datetime

router = APIRouter(prefix="/api/market", tags=["market"])

STOOQ_MAP = {
    "^DJI": {"symbol": "^dji", "name": "다우"},
    "^IXIC": {"symbol": "^ixic", "name": "나스닥"},
    "^SPX": {"symbol": "^spx", "name": "S&P500"},
    "^N225": {"symbol": "^n225", "name": "니케이225"},
    "^SSEC": {"symbol": "^ssec", "name": "상해종합"},
    "^HSI": {"symbol": "^hsi", "name": "항셍"},
    "^FTSE": {"symbol": "^ftse", "name": "영국 FTSE100"},
    "^CAC40": {"symbol": "^cac40", "name": "프랑스 CAC40"},
    "^DAX": {"symbol": "^dax", "name": "독일 DAX"},
}

def _fetch_single(symbol: str) -> dict:
    url = f"https://stooq.com/q/l/?s={symbol}&f=sd2t2ohlcv&h&e=csv"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    content = r.content.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(content))
    for row in reader:
        return row
    return {}

async def fetch_world_indices() -> dict:
    """세계 주식 시장 지수 조회"""
    items = []
    
    for code, meta in STOOQ_MAP.items():
        try:
            row = _fetch_single(meta["symbol"])
            c = float(row.get("Close") or 0)
            o = float(row.get("Open") or 0)
            
            # 스토크 CSV에는 전일 종가가 없으므로, Open과 Close의 차이로 대략 계산
            # 실제로는 전일 종가를 별도로 조회해야 하지만, 간단히 Open 기준 사용
            # 또는 1일 전 데이터를 조회할 수 있음 (d1 파라미터)
            change = c - o
            change_pct = (change / o * 100) if o and o != 0 else 0.0
            
            # 더 정확한 change 계산을 위해 1일 전 데이터 조회 시도
            try:
                prev_url = f"https://stooq.com/q/l/?s={meta['symbol']}&f=d1&e=csv"
                prev_r = requests.get(prev_url, timeout=10)
                if prev_r.status_code == 200:
                    prev_lines = prev_r.text.strip().split('\n')
                    if len(prev_lines) > 1:
                        prev_parts = prev_lines[1].split(',')
                        if len(prev_parts) > 1:
                            prev_close = float(prev_parts[1]) if prev_parts[1] else o
                            change = c - prev_close
                            change_pct = (change / prev_close * 100) if prev_close and prev_close != 0 else 0.0
            except:
                pass  # 전일 데이터 조회 실패 시 Open 기준 사용
            
            items.append({
                "code": code,
                "name": meta["name"],
                "price": round(c, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2)
            })
        except Exception as e:
            print(f"[World index {code} fetch error] {e}")
            continue
    
    return {
        "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "items": items
    }

@router.get("/world")
async def world():
    """세계 주식 시장 지수 조회"""
    from cache import get_cache, put_cache
    
    data = get_cache("world")
    if data:
        return data
    
    data = await fetch_world_indices()
    put_cache("world", data, ttl=60)
    return data

