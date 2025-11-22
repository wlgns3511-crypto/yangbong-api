"""Supabase 클라이언트"""

from typing import Optional
from supabase import create_client, Client
from app.core.config import settings


class SupabaseClient:
    """Supabase 클라이언트 싱글톤"""

    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        """Supabase 클라이언트 인스턴스 반환"""
        if cls._instance is None:
            cls._instance = create_client(
                settings.supabase_url, settings.supabase_service_role_key
            )
        return cls._instance


# 편의 함수
def get_supabase() -> Client:
    """Supabase 클라이언트 반환"""
    return SupabaseClient.get_client()

