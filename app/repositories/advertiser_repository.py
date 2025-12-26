from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.advertiser import Advertiser
from app.models.user import ApprovalStatus, User


class AdvertiserRepository:
    """광고주 저장소"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, advertiser_id: int) -> Advertiser | None:
        """ID로 광고주 조회 (User 포함)"""
        stmt = (
            select(Advertiser)
            .options(
                joinedload(Advertiser.user),
                joinedload(Advertiser.business_license_file),
                joinedload(Advertiser.logo_file),
            )
            .where(Advertiser.id == advertiser_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int) -> Advertiser | None:
        """User ID로 광고주 조회"""
        stmt = select(Advertiser).where(Advertiser.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        approval_status: Optional[ApprovalStatus] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Advertiser]:
        """광고주 목록 조회"""
        stmt = (
            select(Advertiser)
            .options(
                joinedload(Advertiser.user),
                joinedload(Advertiser.business_license_file),
                joinedload(Advertiser.logo_file),
            )
            .join(Advertiser.user)
        )

        if approval_status:
            stmt = stmt.where(User.approval_status == approval_status)

        if search:
            stmt = stmt.where(
                (User.name.ilike(f"%{search}%"))
                | (User.company_name.ilike(f"%{search}%"))
                | (User.email.ilike(f"%{search}%"))
            )

        stmt = stmt.order_by(User.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())

    async def count_all(
        self,
        approval_status: Optional[ApprovalStatus] = None,
        search: Optional[str] = None,
    ) -> int:
        """광고주 수 조회"""
        stmt = select(func.count(Advertiser.id)).join(Advertiser.user)

        if approval_status:
            stmt = stmt.where(User.approval_status == approval_status)

        if search:
            stmt = stmt.where(
                (User.name.ilike(f"%{search}%"))
                | (User.company_name.ilike(f"%{search}%"))
                | (User.email.ilike(f"%{search}%"))
            )

        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def create(self, advertiser: Advertiser) -> Advertiser:
        """광고주 생성"""
        self._session.add(advertiser)
        await self._session.flush()
        await self._session.refresh(advertiser)
        return advertiser
