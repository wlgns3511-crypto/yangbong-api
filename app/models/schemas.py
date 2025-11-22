"""공통 API 스키마 정의"""

from typing import Generic, TypeVar, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """에러 상세 정보"""

    code: str = Field(..., description="에러 코드")
    message: str = Field(..., description="에러 메시지")
    details: Optional[Dict[str, Any]] = Field(default=None, description="추가 에러 정보")


class MetaInfo(BaseModel):
    """응답 메타 정보"""

    timestamp: str = Field(..., description="응답 생성 시각 (ISO 8601)")
    version: str = Field(default="v1", description="API 버전")


class APIResponse(BaseModel, Generic[T]):
    """공통 API 응답 포맷"""

    success: bool = Field(..., description="성공 여부")
    data: Optional[T] = Field(default=None, description="응답 데이터")
    error: Optional[ErrorDetail] = Field(default=None, description="에러 정보")
    meta: MetaInfo = Field(..., description="메타 정보")

    @classmethod
    def success_response(cls, data: T, version: str = "v1") -> "APIResponse[T]":
        """성공 응답 생성"""
        return cls(
            success=True,
            data=data,
            error=None,
            meta=MetaInfo(
                timestamp=datetime.utcnow().isoformat() + "Z",
                version=version,
            ),
        )

    @classmethod
    def error_response(
        cls,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        version: str = "v1",
    ) -> "APIResponse[None]":
        """에러 응답 생성"""
        return cls(
            success=False,
            data=None,
            error=ErrorDetail(code=code, message=message, details=details),
            meta=MetaInfo(
                timestamp=datetime.utcnow().isoformat() + "Z",
                version=version,
            ),
        )

