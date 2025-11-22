"""애플리케이션 설정 관리"""

from typing import Literal
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # Supabase 설정
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_service_role_key: str = Field(..., alias="SUPABASE_SERVICE_ROLE_KEY")

    # OpenAI 설정
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")

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


# 전역 설정 인스턴스
settings = Settings()


