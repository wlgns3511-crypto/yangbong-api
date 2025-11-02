# apps/api/kis_client.py
import time
import os
import httpx

KIS_BASE_URL = os.getenv("KIS_BASE_URL", "https://openapi.koreainvestment.com:9443")
KIS_APP_KEY = os.getenv("KIS_APP_KEY", "")
KIS_APP_SECRET = os.getenv("KIS_APP_SECRET", "")
KIS_SCOPE = os.getenv("KIS_SCOPE", "real")  # real or vts

# ====== ★★ 여기를 문서대로 채우면 끝 ★★ ======
# 지수 조회용 TR ID (실전/모의 다름 → 필요 시 분기)
TR_ID_INDEX = {
    "real": "FHKUP03500000",   # 예시(placeholder). 문서에서 '지수 시세' TR ID 확인 후 정확히 입력
    "vts":  "VTKUP03500000",   # 예시(placeholder)
}
# KIS 지수코드 매핑 (문서 기준 코드로 바꾸면 됨)
INDEX_CODES = {
    "KOSPI":   "0001",  # 예시
    "KOSDAQ":  "1001",  # 예시
    "KPI200":  "2001",  # 예시(코스피200)
}
# ===========================================

class KISClient:
    _token = None
    _token_exp = 0

    @classmethod
    async def _issue_token(cls):
        url = f"{KIS_BASE_URL}/oauth2/tokenP"
        payload = {
            "grant_type": "client_credentials",
            "appkey": KIS_APP_KEY,
            "appsecret": KIS_APP_SECRET,
        }
        async with httpx.AsyncClient(timeout=10) as s:
            r = await s.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
            # 표준 응답키(access_token, expires_in 등) 확인해 조정
            cls._token = data.get("access_token")
            # 만료 1시간 가정(문서에 맞게 조정)
            cls._token_exp = int(time.time()) + int(data.get("expires_in", 3600)) - 60

    @classmethod
    async def token(cls) -> str:
        if not cls._token or time.time() > cls._token_exp:
            await cls._issue_token()
        return cls._token

    @classmethod
    async def get_index_quote(cls, idx_code: str) -> dict:
        """
        KIS 지수 단건 시세 조회.
        - TR/쿼리파라미터는 KIS 문서대로 맞춰야 함.
        - 여기선 대표적인 형태로 FID_INPUT_ISCD에 지수코드 넣는 케이스 예시.
        """
        token = await cls.token()
        tr_id = TR_ID_INDEX.get(KIS_SCOPE, TR_ID_INDEX["real"])
        headers = {
            "authorization": f"Bearer {token}",
            "appkey": KIS_APP_KEY,
            "appsecret": KIS_APP_SECRET,
            "tr_id": tr_id,
        }
        params = {
            # KIS 문서 확인 후 파라미터 key 정확히 맞추기
            "FID_COND_MRKT_DIV_CODE": "U",   # 예시(지수구분)
            "FID_INPUT_ISCD": idx_code,      # 지수 코드
        }
        url = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-index"
        async with httpx.AsyncClient(timeout=10) as s:
            r = await s.get(url, headers=headers, params=params)
            r.raise_for_status()
            return r.json()

