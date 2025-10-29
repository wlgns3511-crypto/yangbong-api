from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import time, asyncio
from contextlib import asynccontextmanager

# ---------- 기본 앱 ----------
async def start_background_tasks():
    # 여기서 주기적 갱신 작업을 비동기로 돌리면 됨
    while True:
        try:
            # TODO: 실제 데이터 갱신 로직 (네이버/야후/업비트 등)
            pass
        except Exception as e:
            print("[refresh]", e)
        await asyncio.sleep(30)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 백그라운드 루프는 시작을 막지 않도록 태스크로 실행
    asyncio.get_event_loop().create_task(start_background_tasks())
    yield

app = FastAPI(lifespan=lifespan)

# CORS (프론트부터 붙일 수 있게 오픈)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yangbong.club",          # 프론트
        "http://localhost:3000",          # 로컬 개발
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- 기본 헬스/핑 ----------
@app.get("/health")
def health():
    return {"ok": True}

@app.get("/ping")
def ping():
    return {"pong": "yangbong"}

# ---------- 임시/동작 확인용 API (프론트 접속 테스트용) ----------
# 실제 연동 전까지는 이 값들이 그대로 내려감. 프론트 연결 확인되면 fetch_* 로직으로 교체.

@app.get("/api/market/world")
def api_market_world():
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    data = {
        "updated_at": now,
        "items": [
            {"code": "^DJI",  "name": "다우",   "price": 39000.0, "change": -120.3, "change_pct": -0.31},
            {"code": "^IXIC", "name": "나스닥", "price": 15500.0, "change":   45.1, "change_pct":  0.29},
            {"code": "^GSPC", "name": "S&P500","price": 5100.0,  "change":    3.2, "change_pct":  0.06},
            {"code": "^N225", "name": "니케이225","price": 38000.0,"change":  -80.0,"change_pct": -0.21},
            {"code": "000001.SS","name":"상해종합","price": 3000.0,"change": -10.0,"change_pct": -0.33},
            {"code": "^HSI",  "name": "항셍", "price": 17000.0, "change":   70.0, "change_pct":  0.41},
            {"code": "^FTSE", "name": "영국", "price": 8100.0,  "change":   -5.0, "change_pct": -0.06},
            {"code": "^FCHI", "name": "프랑스","price": 7600.0, "change":   10.0, "change_pct":  0.13},
            {"code": "^GDAXI","name": "독일", "price": 18500.0, "change":  -20.0, "change_pct": -0.11},
        ]
    }
    return JSONResponse(data)

@app.get("/api/market/kr")
def api_market_kr():
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return JSONResponse({
        "updated_at": now,
        "items": [
            {"code": "KOSPI",   "name": "코스피",   "price": 2500.0, "change": 12.3, "change_pct": 0.50},
            {"code": "KOSDAQ",  "name": "코스닥",   "price": 800.0,  "change": -3.1, "change_pct": -0.39},
            {"code": "KOSPI200","name": "코스피200","price": 330.0,  "change":  0.8, "change_pct": 0.24}
        ]
    })

@app.get("/api/crypto/tickers")
def api_crypto_tickers(list: str = Query(..., description="comma separated symbols, e.g. BTC,ETH,XRP")):
    # 임시 목업: KRW, USDT, 환율을 고정값으로 계산
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    symbols = [s.strip().upper() for s in list.split(",") if s.strip()]
    fx = 1377.0  # KRW/USD 임시
    prices_usdt = {"BTC": 71000.0, "ETH": 3500.0, "XRP": 0.52, "SOL": 180.0, "BNB": 600.0}
    prices_krw  = {"BTC": 98000000.0, "ETH": 4900000.0, "XRP":  730.0, "SOL": 245000.0, "BNB": 820000.0}

    items = []
    for s in symbols:
        p_usdt = prices_usdt.get(s, 100.0)
        p_krw  = prices_krw.get(s,  100000.0)
        kimchi = 100.0 * (p_krw / (p_usdt * fx) - 1.0)
        items.append({
            "symbol": s,
            "price_krw": p_krw,
            "price_usdt": p_usdt,
            "krw_usd": fx,
            "kimchi_pct": round(kimchi, 2)
        })
    return JSONResponse({"updated_at": now, "items": items})

@app.get("/api/news")
def api_news(tab: str = "kr", page: int = 1, page_size: int = 10):
    # 임시 데이터
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    items = [{
        "title": f"[{tab.upper()}] 샘플 뉴스 {i}",
        "summary": "요약 텍스트 (임시).",
        "source": "양봉클럽",
        "url": "https://yangbong.club",
        "image": None,
        "published_at": now
    } for i in range(page_size)]
    return JSONResponse({"updated_at": now, "tab": tab, "items": items})
