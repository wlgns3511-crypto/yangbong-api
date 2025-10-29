from fastapi import APIRouter
import requests, csv, io

router = APIRouter(prefix="/market", tags=["market"])

STOOQ_MAP = {
    "DOW": {"symbol": "^dji", "name_kr": "다우산업"},
    "NASDAQ": {"symbol": "^ixic", "name_kr": "나스닥"},
    "SP500": {"symbol": "^spx", "name_kr": "S&P500"},
    "NIKKEI": {"symbol": "^n225", "name_kr": "니케이225"},
    "SSEC": {"symbol": "^ssec", "name_kr": "상해종합"},
    "HSI": {"symbol": "^hsi", "name_kr": "항셍"},
    "FTSE": {"symbol": "^ftse", "name_kr": "영국 FTSE100"},
    "CAC40": {"symbol": "^cac40", "name_kr": "프랑스 CAC40"},
    "DAX": {"symbol": "^dax", "name_kr": "독일 DAX"},
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

@router.get("/world")
def world_indices():
    result = {}
    
    for key, meta in STOOQ_MAP.items():
        try:
            row = _fetch_single(meta["symbol"])
            o = float(row.get("Open") or 0)
            c = float(row.get("Close") or 0)
            h = float(row.get("High") or 0)
            l = float(row.get("Low") or 0)
            v = int(float(row.get("Volume") or 0))
            chg = c - o
            chg_pct = (chg / o * 100) if o else 0.0
            result[key] = {
                "key": key, "name": meta["name_kr"],
                "price": round(c,2), "change": round(chg,2), "change_pct": round(chg_pct,2),
                "open": round(o,2), "high": round(h,2), "low": round(l,2), "close": round(c,2), "volume": v,
                "raw": row
            }
        except Exception as e:
            result[key] = {"key": key, "name": meta["name_kr"], "error": True, "error_msg": str(e)}
    
    return {"ok": True, "count": len(result), "data": result}

