"""애플리케이션 설정 관리"""

from typing import Literal, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # Supabase 설정 (선택적)
    supabase_url: Optional[str] = Field(default=None, alias="SUPABASE_URL")
    supabase_service_role_key: Optional[str] = Field(
        default=None, alias="SUPABASE_SERVICE_ROLE_KEY"
    )

    # OpenAI 설정 (선택적)
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")

    # 애플리케이션 설정
    environment: Literal["development", "staging", "production"] = Field(
        default="development", alias="ENVIRONMENT"
    )
    debug: bool = Field(default=False, alias="DEBUG")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # .env 파일이 없어도 에러 발생하지 않음 (환경변수에서 읽음)
        env_file_required = False


# 전역 설정 인스턴스 (에러 발생해도 기본값으로 생성)
try:
    settings = Settings()
except Exception:
    # 환경변수가 없어도 기본값으로 설정 생성
    settings = Settings(
        supabase_url=None,
        supabase_service_role_key=None,
        openai_api_key=None,
        environment="development",
        debug=False,
    )


