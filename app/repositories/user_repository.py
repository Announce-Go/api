from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.user import ApprovalStatus, User, UserRole


class UserRepository:
    """사용자 저장소"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        """ID로 사용자 조회"""
        stmt = select(User).where(User.id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_login_id(self, login_id: str) -> User | None:
        """로그인 ID로 사용자 조회"""
        stmt = (
            select(User)
            .options(joinedload(User.agency))
            .where(User.login_id == login_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """이메일로 사용자 조회"""
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        """사용자 생성"""
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def exists_by_login_id(self, login_id: str) -> bool:
        """로그인 ID 존재 여부"""
        stmt = select(User.id).where(User.login_id == login_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def exists_by_email(self, email: str) -> bool:
        """이메일 존재 여부"""
        stmt = select(User.id).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_pending_users(
        self,
        role: Optional[UserRole] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        """승인 대기 중인 사용자 목록 (advertiser/agency 포함)"""
        stmt = (
            select(User)
            .options(joinedload(User.advertiser), joinedload(User.agency))
            .where(User.approval_status == ApprovalStatus.PENDING)
        )

        if role:
            stmt = stmt.where(User.role == role)

        stmt = stmt.order_by(User.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())

    async def count_pending_users(
        self,
        role: Optional[UserRole] = None,
    ) -> int:
        """승인 대기 중인 사용자 수"""
        stmt = select(func.count(User.id)).where(
            User.approval_status == ApprovalStatus.PENDING
        )

        if role:
            stmt = stmt.where(User.role == role)

        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def update(self, user: User) -> User:
        """사용자 업데이트"""
        await self._session.flush()
        await self._session.refresh(user)
        return user
