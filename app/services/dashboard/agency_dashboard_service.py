from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.advertiser import Advertiser
from app.models.agency_advertiser_mapping import AgencyAdvertiserMapping
from app.models.tracking import RankTracking, TrackingStatus
from app.models.work_records import BlogPosting
from app.repositories.tracking import RankHistoryRepository
from app.schemas.dashboard.agency import AgencyDashboardResponse, RecentTracking


class AgencyDashboardService:
    """업체 대시보드 서비스"""

    def __init__(self, db_session: AsyncSession):
        self._db = db_session
        self._history_repo = RankHistoryRepository(db_session)

    async def get_dashboard(self, agency_id: int) -> AgencyDashboardResponse:
        """
        업체 대시보드 통합 조회

        Args:
            agency_id: 업체 ID

        Returns:
            AgencyDashboardResponse: 통계 + 최근 추적 현황 5건
        """
        # 매핑된 광고주 수
        mapped_count_stmt = select(func.count(AgencyAdvertiserMapping.advertiser_id)).where(
            AgencyAdvertiserMapping.agency_id == agency_id
        )
        mapped_result = await self._db.execute(mapped_count_stmt)
        mapped_advertiser_count = mapped_result.scalar_one()

        # 활성 추적 수
        active_tracking_stmt = select(func.count(RankTracking.id)).where(
            RankTracking.agency_id == agency_id,
            RankTracking.status == TrackingStatus.ACTIVE,
        )
        active_result = await self._db.execute(active_tracking_stmt)
        active_tracking_count = active_result.scalar_one()

        # 블로그 포스팅 수
        blog_posting_stmt = select(func.count(BlogPosting.id)).where(
            BlogPosting.agency_id == agency_id
        )
        blog_result = await self._db.execute(blog_posting_stmt)
        blog_posting_count = blog_result.scalar_one()

        # 최근 추적 현황 5건 (advertiser.user eager loading)
        recent_tracking_stmt = (
            select(RankTracking)
            .options(
                selectinload(RankTracking.advertiser).selectinload(Advertiser.user)
            )
            .where(
                RankTracking.agency_id == agency_id,
                RankTracking.status == TrackingStatus.ACTIVE,
            )
            .order_by(RankTracking.created_at.desc())
            .limit(5)
        )
        recent_result = await self._db.execute(recent_tracking_stmt)
        recent_trackings = recent_result.scalars().all()

        # 최신 히스토리 조회
        tracking_ids = [t.id for t in recent_trackings]
        latest_histories = {}
        if tracking_ids:
            latest_histories = await self._history_repo.get_latest_by_tracking_ids(
                tracking_ids
            )

        recent_tracking = []
        for tracking in recent_trackings:
            latest_history = latest_histories.get(tracking.id)
            advertiser_name = ""
            if tracking.advertiser and tracking.advertiser.user:
                advertiser_name = tracking.advertiser.user.company_name or ""

            recent_tracking.append(
                RecentTracking(
                    id=tracking.id,
                    type=tracking.type,
                    keyword=tracking.keyword,
                    latest_rank=latest_history.rank if latest_history else None,
                    advertiser_name=advertiser_name,
                )
            )

        return AgencyDashboardResponse(
            mapped_advertiser_count=mapped_advertiser_count,
            active_tracking_count=active_tracking_count,
            blog_posting_count=blog_posting_count,
            recent_tracking=recent_tracking,
        )
