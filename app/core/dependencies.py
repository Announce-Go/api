from __future__ import annotations

from typing import TYPE_CHECKING, Any, AsyncGenerator, Dict, Optional

from fastapi import Cookie, Depends, HTTPException, status

from app.core.config import Settings, get_settings
from app.core.factory import get_database, get_session_store

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.interfaces.database import AbstractDatabase
    from app.core.interfaces.session_store import AbstractSessionStore


# 싱글턴 인스턴스 참조
_database: Optional[AbstractDatabase] = None
_session_store: Optional[AbstractSessionStore] = None


async def init_dependencies(settings: Settings) -> None:
    """앱 시작 시 의존성 초기화"""
    global _database, _session_store
    _database = await get_database(settings)
    _session_store = await get_session_store(settings)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """DB 세션 의존성"""
    if _database is None:
        raise RuntimeError("Database not initialized")

    async for session in _database.get_session():
        yield session


async def get_session_store_dep() -> AbstractSessionStore:
    """Session Store 의존성"""
    if _session_store is None:
        raise RuntimeError("Session store not initialized")
    return _session_store


async def get_current_user(
    session_id: Optional[str] = Cookie(None, alias="session_id"),
    session_store: AbstractSessionStore = Depends(get_session_store_dep),
) -> Dict[str, Any]:
    """
    현재 로그인한 사용자 정보 반환

    인증 필수 엔드포인트에서 사용
    """
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다.",
        )

    session_data = await session_store.get(session_id)
    if session_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="세션이 만료되었습니다.",
        )

    return session_data


async def get_current_user_optional(
    session_id: Optional[str] = Cookie(None, alias="session_id"),
    session_store: AbstractSessionStore = Depends(get_session_store_dep),
) -> Optional[Dict[str, Any]]:
    """
    현재 로그인한 사용자 정보 반환 (선택적)

    인증 선택적 엔드포인트에서 사용
    """
    if not session_id:
        return None

    return await session_store.get(session_id)


def require_role(*roles: str):
    """
    특정 역할 필요 의존성 팩토리

    Usage:
        @router.get("/admin-only")
        async def admin_only(user: dict = Depends(require_role("admin"))):
            pass
    """

    async def checker(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        if current_user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="권한이 없습니다.",
            )
        return current_user

    return checker


def require_approved():
    """
    승인된 사용자만 접근 가능 의존성

    Usage:
        @router.get("/approved-only")
        async def approved_only(user: dict = Depends(require_approved())):
            pass
    """

    async def checker(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        if current_user["approval_status"] != "approved" and current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="승인된 사용자만 접근할 수 있습니다.",
            )
        return current_user

    return checker
