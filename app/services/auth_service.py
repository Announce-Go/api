from __future__ import annotations

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.session.session_store import AbstractSessionStore
from app.core.security import generate_session_id, verify_password
from app.models.user import ApprovalStatus, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    SessionResponse,
    UserInfo,
)


class AuthService:
    """인증 서비스"""

    def __init__(
        self,
        db_session: AsyncSession,
        session_store: AbstractSessionStore,
        settings: Settings,
    ):
        self._db = db_session
        self._session_store = session_store
        self._settings = settings
        self._user_repo = UserRepository(db_session)

    async def login(self, request: LoginRequest) -> tuple[str, LoginResponse]:
        """
        로그인 처리

        Args:
            request: 로그인 요청

        Returns:
            tuple[str, LoginResponse]: (세션 ID, 로그인 응답)

        Raises:
            ValueError: 로그인 ID/비밀번호 불일치
            PermissionError: 미승인 또는 비활성 사용자
        """
        # 1. 사용자 조회
        user = await self._user_repo.get_by_login_id(request.login_id)
        if user is None:
            raise ValueError("아이디가 올바르지 않습니다.")

        # 2. 비밀번호 검증
        if not verify_password(request.password, user.password_hash):
            raise ValueError("비밀번호가 올바르지 않습니다.")

        # 3. 승인 상태 확인 (admin은 제외)
        if (
            user.role != UserRole.ADMIN
            and user.approval_status != ApprovalStatus.APPROVED
        ):
            if user.approval_status == ApprovalStatus.PENDING:
                raise PermissionError("승인 대기 중인 계정입니다.")
            raise PermissionError("승인이 거절된 계정입니다.")

        # 4. 세션 생성
        session_id = generate_session_id()
        session_data = {
            "user_id": user.id,
            "login_id": user.login_id,
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "approval_status": user.approval_status.value,
            "categories": user.agency.categories if user.agency else None,
        }

        # Remember Me에 따른 만료 시간 설정
        if request.remember_me:
            expire = timedelta(seconds=self._settings.REMEMBER_ME_EXPIRE_SECONDS)
        else:
            expire = timedelta(seconds=self._settings.SESSION_EXPIRE_SECONDS)

        await self._session_store.set(session_id, session_data, expire=expire)

        return session_id, LoginResponse(
            user=UserInfo(
                id=user.id,
                login_id=user.login_id,
                email=user.email,
                name=user.name,
                role=user.role,
                approval_status=user.approval_status,
                categories=user.agency.categories if user.agency else None,
            ),
        )

    async def logout(self, session_id: str) -> bool:
        """로그아웃 (세션 삭제)"""
        await self._session_store.delete(session_id)
        return True

    async def get_session(self, session_id: str | None) -> SessionResponse:
        """현재 세션 정보 조회"""
        if not session_id:
            return SessionResponse(authenticated=False)

        session_data = await self._session_store.get(session_id)
        if session_data is None:
            return SessionResponse(authenticated=False)

        return SessionResponse(
            authenticated=True,
            user=UserInfo(
                id=session_data["user_id"],
                login_id=session_data["login_id"],
                email=session_data["email"],
                name=session_data["name"],
                role=session_data["role"],
                approval_status=session_data["approval_status"],
                categories=session_data.get("categories"),
            ),
        )

    async def refresh_session(self, session_id: str, remember_me: bool = False) -> bool:
        """세션 만료 시간 갱신"""
        if remember_me:
            expire = timedelta(seconds=self._settings.REMEMBER_ME_EXPIRE_SECONDS)
        else:
            expire = timedelta(seconds=self._settings.SESSION_EXPIRE_SECONDS)

        return await self._session_store.refresh(session_id, expire=expire)
