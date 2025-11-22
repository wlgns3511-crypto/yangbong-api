"""Supabase 클라이언트"""

from typing import Optional
from supabase import create_client, Client
from app.core.config import settings


class SupabaseClient:
    """Supabase 클라이언트 싱글톤"""

    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Optional[Client]:
        """Supabase 클라이언트 인스턴스 반환"""
        # 환경변수가 없으면 None 반환
        if not settings.supabase_url or not settings.supabase_service_role_key:
            return None
        
        if cls._instance is None:
            cls._instance = create_client(
                settings.supabase_url, settings.supabase_service_role_key
            )
        return cls._instance


# 편의 함수
def get_supabase() -> Optional[Client]:
    """Supabase 클라이언트 반환"""
    return SupabaseClient.get_client()

