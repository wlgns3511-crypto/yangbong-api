# apps/api/kis_client.py
import os
import time
import logging
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

KIS_BASE_URL = os.getenv("KIS_BASE", "https://openapi.koreainvestment.com:9443")
KIS_APP_KEY = os.getenv("KIS_APP_KEY", "")
KIS_APP_SECRET = os.getenv("KIS_APP_SECRET", "")

# ✅ TR ID (지수 전용)
TR_ID_INDEX = "FHKUP03500100"

# ✅ 토큰 캐싱
_cached_token = None
_token_expiry = 0


def _get_access_token():
    """자동 갱신 포함 토큰 가져오기"""
    global _cached_token, _token_expiry

    if _cached_token and time.time() < _token_expiry:
        return _cached_token

    url = f"{KIS_BASE_URL}/oauth2/tokenP"
    payload = {
        "grant_type": "client_credentials",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET,
    }
    
    try:
        res = requests.post(url, json=payload, timeout=10)
        res.raise_for_status()
        data = res.json()

        if "access_token" not in data:
            raise RuntimeError(f"KIS 토큰 발급 실패: {data}")

        _cached_token = data["access_token"]
        _token_expiry = time.time() + int(data.get("expires_in", 3600)) - 60
        logger.info("[KIS] 새 access_token 발급 완료")
        return _cached_token
    except Exception as e:
        logger.error(f"[KIS] 토큰 발급 에러: {e}")
        raise


def get_access_token() -> str:
    """호환성을 위한 래퍼 함수"""
    return _get_access_token()


def kis_api(tr_id: str, params: dict):
    """KIS API 공통 호출"""
    token = _get_access_token()

    headers = {
        "authorization": f"Bearer {token}",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET,
        "tr_id": tr_id,
        "custtype": "P",
        "accept": "application/json",
        "Content-Type": "application/json",
    }

    # ✅ 최신 지수 조회 URL
    url = urljoin(KIS_BASE_URL, "/uapi/domestic-stock/v1/quotations/inquire-daily-indexprice")
    res = requests.get(url, headers=headers, params=params, timeout=5)

    if res.status_code != 200:
        logger.error(f"[KIS] HTTP {res.status_code}: {res.text}")
        raise RuntimeError(f"KIS HTTP {res.status_code}: {res.text}")

    data = res.json()
    return data


def get_index(mrkt: str, code: str):
    """국내 지수 조회 (KOSPI/KOSDAQ/KOSPI200)"""
    try:
        params = {
            "FID_COND_MRKT_DIV_CODE": mrkt,  # "U" or "J"
            "FID_INPUT_ISCD": code,           # "0001", "1001", "2001"
        }
        res = kis_api(TR_ID_INDEX, params)
        output = res.get("output", {})

        if not output:
            logger.warning(f"[KIS] output missing for {code}: {res}")
            return None

        name = output.get("IDX_NM", "")
        price = float(output.get("BAS_PRC", 0) or 0)
        change = float(output.get("CMPPREVDD_PRC", 0) or 0)
        rate = float(output.get("FLUC_RT", 0) or 0)

        logger.info(f"[KIS] ✅ {name} {price:,.2f} ({'+' if change >= 0 else ''}{change:.2f}, {rate:.2f}%)")

        return {
            "name": name,
            "price": price,
            "change": change,
            "rate": rate,
            "updated": output.get("BAS_TM", ""),
        }

    except Exception as e:
        logger.error(f"[KIS] Error for {code}: {e}")
        return None


def get_overseas_price(excd: str, symb: str) -> dict:
    """
    해외주식 현재체결가 (v1_해외주식-009)
    ex) EXCD: NAS/NYS/AMS/HKS/TSE ... , SYMB: AAPL, SPY, QQQ, 2800, 1321 등
    실패 시 예외를 던지지 않고 빈 dict 반환
    """
    path = "/uapi/overseas-price/v1/quotations/price"
    url = urljoin(KIS_BASE_URL, path)
    params = {"AUTH": "", "EXCD": excd, "SYMB": symb}

    try:
        token = _get_access_token()
        headers = {
            "authorization": f"Bearer {token}",
            "appkey": KIS_APP_KEY,
            "appsecret": KIS_APP_SECRET,
            "tr_id": "HHDFS00000300",
            "custtype": "P",
            "Content-Type": "application/json",
        }
        res = requests.get(url, headers=headers, params=params, timeout=10)
        res.raise_for_status()
        j = res.json()

        # output 스키마 보호적으로 파싱
        out = (j.get("output") or j.get("Output") or {})
        def num(keys, default=None):
            for k in keys:
                v = out.get(k)
                try:
                    if v is None or v == "": 
                        continue
                    return float(str(v).replace(',', ''))
                except Exception:
                    continue
            return default

        price  = num(["last", "ovrs_now_prc", "last_prc"])
        change = num(["prdy_vrss", "net_chg", "ovrs_prdy_vrss"])
        pct    = num(["prdy_ctrt", "rate", "ovrs_prdy_ctrt"])

        return {
            "raw": j,                 # 디버깅용 원본
            "price": price,
            "change": change,
            "pct": pct,
        }
    except Exception as e:
        logger.warning(f"[KIS] overseas price error for {excd}/{symb}: {e}")
        return {
            "raw": {},
            "price": None,
            "change": None,
            "pct": None,
        }
