from fastapi import APIRouter
import requests
import csv
import io
from datetime import datetime

router = APIRouter(prefix="/api/market", tags=["market"])


async def fetch_kr_indices() -> dict:
    """한국 주식 시장 지수 조회 (네이버/야후 등)"""
    items = []
    
    # KOSPI, KOSDAQ은 스토크에서 가져옴
    indices = [
        {"symbol": "kospi", "code": "KOSPI", "name": "코스피"},
        {"symbol": "kosdaq", "code": "KOSDAQ", "name": "코스닥"}
    ]
    
    for idx in indices:
        try:
            url = f"https://stooq.com/q/l/?s={idx['symbol']}&f=sd2t2ohlcv&h&e=csv"
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            content = r.content.decode("utf-8", errors="ignore")
            reader = csv.DictReader(io.StringIO(content))
            
            for row in reader:
                c = float(row.get("Close") or 0)
                o = float(row.get("Open") or 0)
                
                # 전일 종가를 대략적으로 계산 (Open이 전일 종가에 가까움)
                # 또는 별도로 전일 데이터 조회
                prev_close = o
                change = c - prev_close
                change_pct = (change / prev_close * 100) if prev_close and prev_close != 0 else 0.0
                
                # 전일 데이터 조회 시도 (더 정확한 계산)
                try:
                    prev_url = f"https://stooq.com/q/l/?s={idx['symbol']}&f=d1&e=csv"
                    prev_r = requests.get(prev_url, timeout=10)
                    if prev_r.status_code == 200:
                        prev_content = prev_r.content.decode("utf-8", errors="ignore")
                        prev_reader = csv.DictReader(io.StringIO(prev_content))
                        for prev_row in prev_reader:
                            prev_close = float(prev_row.get("Close") or o)
                            change = c - prev_close
                            change_pct = (change / prev_close * 100) if prev_close and prev_close != 0 else 0.0
                            break
                except:
                    pass
                
                items.append({
                    "code": idx["code"],
                    "name": idx["name"],
                    "price": round(c, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2)
                })
                break
        except Exception as e:
            print(f"[{idx['code']} fetch error] {e}")
    
    return {
        "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "items": items
    }


@router.get("/kr")
async def kr():
    """한국 주식 시장 지수 조회"""
    from cache import get_cache, put_cache
    
    data = get_cache("kr")
    if data:
        return data
    
    data = await fetch_kr_indices()
    put_cache("kr", data, ttl=60)
    return data

