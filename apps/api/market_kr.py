from fastapi import APIRouter, HTTPException
from os import getenv
import requests
from urllib.parse import urljoin

router = APIRouter(prefix="/market", tags=["market"])

# 후보들: (path, tr_id, 설명)
INDEX_CANDIDATES = [
    ("/uapi/domestic-stock/v1/quotations/inquire-index",      "FHKUP03500100", "index (문서에 따라 404 가능)"),
    ("/uapi/domestic-stock/v1/quotations/inquire-idxprice",   "FHKUP03500100", "idxprice (대체 이름)"),
    ("/uapi/domestic-stock/v1/quotations/inquire-daily-indexchartprice", "FHKUP03500100", "일봉 인덱스 차트"),
    # 필요하면 더 추가
]

# KOSPI/KOSDAQ/K200 코드
IDX = [
    ("코스피",  "0001"),
    ("코스닥",  "1001"),
    ("코스피200","2001"),
]

def _auth_headers():
    appkey = getenv("KIS_APP_KEY")
    appsec = getenv("KIS_APP_SECRET")
    if not appkey or not appsec:
        raise HTTPException(500, "KIS_APP_KEY/SECRET not set")

    # 토큰 캐시가 이미 구현돼 있다면 그걸 사용,
    # 임시로 토큰이 kis_client에서 자동 갱신된다고 가정하고 env에서 가져오는 함수만 호출
    from apps.api.kis_client import get_access_token  # 프로젝트 경로에 맞춰주세요
    token = get_access_token()

    return {
        "authorization": f"Bearer {token}",
        "appkey": appkey,
        "appsecret": appsec,
        "custtype": "P",
        # tr_id는 각각 요청별로 세팅
        "Content-Type": "application/json; charset=utf-8",
    }

def _try_one(base_url: str, path: str, tr_id: str, iscd: str):
    url = urljoin(base_url, path)
    headers = _auth_headers().copy()
    headers["tr_id"] = tr_id
    params = {
        "FID_COND_MRKT_DIV_CODE": "U",
        "FID_INPUT_ISCD": iscd,
    }
    r = requests.get(url, headers=headers, params=params, timeout=8)
    return r

@router.get("/kr")
def kr_indices():
    base = getenv("KIS_BASE_URL")
    if not base:
        raise HTTPException(500, "KIS_BASE_URL not set")

    results = []
    last_errors = []

    for name, code in IDX:
        found = None
        for path, tr_id, _desc in INDEX_CANDIDATES:
            try:
                r = _try_one(base, path, tr_id, code)
                if r.status_code == 200:
                    j = r.json()
                    # KIS 응답 포맷이 다양하므로, 대표값만 뽑고 원본도 함께 실어둠
                    price = None
                    for k in ("stck_prpr","IDX_PRPR","clos","close","price"):
                        if k in j:
                            price = j[k]; break
                        if isinstance(j, dict) and "output" in j and isinstance(j["output"], dict) and k in j["output"]:
                            price = j["output"][k]; break

                    found = {"name": name, "code": code, "path": path, "tr_id": tr_id, "raw": j, "price": price}
                    break
                else:
                    last_errors.append(
                        {"name": name, "code": code, "path": path, "tr_id": tr_id,
                         "status": r.status_code, "body": r.text[:500]}
                    )
            except Exception as e:
                last_errors.append({"name": name, "code": code, "path": path, "err": str(e)})

        if not found:
            results.append({"name": name, "code": code, "error": "no endpoint matched"})
        else:
            results.append(found)

    # 하나도 성공 없으면 진단을 그대로 보여줌
    if all("error" in x for x in results):
        raise HTTPException(502, {"message": "All index endpoints returned non-200", "trials": last_errors})

    return {"ok": True, "base": base, "results": results}
