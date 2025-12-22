from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status

from app.core.config import Settings, get_settings
from app.core.dependencies import get_db_session, get_session_store_dep
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    SessionResponse,
)
from app.services.auth_service import AuthService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.interfaces.session_store import AbstractSessionStore


router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(
    db: AsyncSession = Depends(get_db_session),
    session_store: AbstractSessionStore = Depends(get_session_store_dep),
    settings: Settings = Depends(get_settings),
) -> AuthService:
    """AuthService 의존성"""
    return AuthService(db, session_store, settings)


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    """
    로그인

    성공 시 세션 ID를 쿠키에 설정
    """
    try:
        session_id, result = await auth_service.login(request)

        # 쿠키에 세션 ID 설정
        max_age = (
            settings.REMEMBER_ME_EXPIRE_SECONDS
            if request.remember_me
            else settings.SESSION_EXPIRE_SECONDS
        )
        response.set_cookie(
            key=settings.SESSION_COOKIE_NAME,
            value=session_id,
            max_age=max_age,
            httponly=True,
            samesite="lax",
            secure=settings.APP_ENV == "prod",
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    response: Response,
    session_id: Optional[str] = Cookie(None, alias="session_id"),
    auth_service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> LogoutResponse:
    """
    로그아웃

    세션 삭제 및 쿠키 제거
    """
    if session_id:
        await auth_service.logout(session_id)

    response.delete_cookie(settings.SESSION_COOKIE_NAME)

    return LogoutResponse(success=True, message="로그아웃되었습니다.")


@router.get("/session", response_model=SessionResponse)
async def get_session(
    session_id: Optional[str] = Cookie(None, alias="session_id"),
    auth_service: AuthService = Depends(get_auth_service),
) -> SessionResponse:
    """
    현재 세션 확인

    쿠키의 세션 ID로 인증 상태 확인
    """
    return await auth_service.get_session(session_id)
