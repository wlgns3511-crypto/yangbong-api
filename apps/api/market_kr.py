# apps/api/market_kr.py
from fastapi import APIRouter, HTTPException
from .kis_client import KISClient, INDEX_CODES

router = APIRouter(prefix="/market", tags=["market"])

def _map_index_payload(idx_name: str, kis_json: dict):
    """
    KIS 응답(JSON)에서 종가/전일대비/등락률 필드를 꺼내
    프론트에서 쓰는 공통 구조로 변환.
    ※ 실제 키 이름은 KIS 문서 응답 구조에 맞게 수정 필요.
    """
    # ---- 아래 키들은 '예시'입니다. KIS 실제 응답 키로 교체하세요. ----
    # 예: output = kis_json["output"]
    output = kis_json.get("output", {}) if isinstance(kis_json, dict) else {}
    close = float(output.get("bstp_nmix_prpr", 0))     # 지수 현재가(예시)
    change = float(output.get("prdy_vrss", 0))         # 전일대비(포인트, 예시)
    pct = float(output.get("prdy_ctrt", 0))            # 등락률(% 문자열일 수도 있음 → float로 변환)
    # --------------------------------------------------------------
    return {
        "id": idx_name,
        "name": {"KOSPI": "코스피", "KOSDAQ": "코스닥", "KPI200": "코스피200"}[idx_name],
        "close": close,
        "change": change,
        "pct": pct,
    }

@router.get("/kr")
async def market_kr():
    try:
        items = []
        for key in ("KOSPI", "KOSDAQ", "KPI200"):
            code = INDEX_CODES[key]
            raw = await KISClient.get_index_quote(code)
            items.append(_map_index_payload(key, raw))
        return {"ok": True, "source": "kis", "items": items}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"KIS error: {e}")
