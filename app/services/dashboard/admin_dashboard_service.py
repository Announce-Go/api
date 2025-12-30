from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.advertiser import Advertiser
from app.models.agency import Agency
from app.models.user import ApprovalStatus, User, UserRole
from app.schemas.dashboard.admin import AdminDashboardResponse, RecentSignupRequest


class AdminDashboardService:
    """관리자 대시보드 서비스"""

    def __init__(self, db_session: AsyncSession):
        self._db = db_session

    async def get_dashboard(self) -> AdminDashboardResponse:
        """
        관리자 대시보드 통합 조회

        Returns:
            AdminDashboardResponse: 통계 + 최근 승인 요청 5건
        """
        # 승인 대기 수
        pending_count_stmt = select(func.count(User.id)).where(
            User.approval_status == ApprovalStatus.PENDING
        )
        pending_result = await self._db.execute(pending_count_stmt)
        pending_signup_count = pending_result.scalar_one()

        # 전체 광고주 수 (승인된)
        advertiser_count_stmt = (
            select(func.count(Advertiser.id))
            .join(User, Advertiser.id == User.id)
            .where(User.approval_status == ApprovalStatus.APPROVED)
        )
        advertiser_result = await self._db.execute(advertiser_count_stmt)
        advertiser_count = advertiser_result.scalar_one()

        # 전체 업체 수 (승인된)
        agency_count_stmt = (
            select(func.count(Agency.id))
            .join(User, Agency.id == User.id)
            .where(User.approval_status == ApprovalStatus.APPROVED)
        )
        agency_result = await self._db.execute(agency_count_stmt)
        agency_count = agency_result.scalar_one()

        # 최근 승인 요청 5건
        recent_requests_stmt = (
            select(User)
            .where(User.approval_status == ApprovalStatus.PENDING)
            .order_by(User.created_at.desc())
            .limit(5)
        )
        recent_result = await self._db.execute(recent_requests_stmt)
        recent_users = recent_result.scalars().all()

        recent_requests = [
            RecentSignupRequest(
                id=user.id,
                login_id=user.login_id,
                role=user.role.value,
                company_name=user.company_name or "",
                created_at=user.created_at,
            )
            for user in recent_users
        ]

        return AdminDashboardResponse(
            pending_signup_count=pending_signup_count,
            advertiser_count=advertiser_count,
            agency_count=agency_count,
            recent_requests=recent_requests,
        )
