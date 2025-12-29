from __future__ import annotations

from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, joinedload

from app.models.advertiser import Advertiser
from app.models.agency import Agency
from app.models.tracking import RankTracking, RankType, TrackingStatus
from app.models.user import User


class RankTrackingRepository:
    """순위 추적 저장소"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, tracking_id: int) -> RankTracking | None:
        """ID로 추적 조회"""
        stmt = (
            select(RankTracking)
            .options(
                joinedload(RankTracking.agency).joinedload(Agency.user),
                joinedload(RankTracking.advertiser).joinedload(Advertiser.user),
            )
            .where(RankTracking.id == tracking_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_with_histories(
        self,
        tracking_id: int,
        history_limit: int = 100,
    ) -> RankTracking | None:
        """ID로 추적 조회 (히스토리 포함)"""
        stmt = (
            select(RankTracking)
            .options(
                joinedload(RankTracking.agency).joinedload(Agency.user),
                joinedload(RankTracking.advertiser).joinedload(Advertiser.user),
                joinedload(RankTracking.histories),
            )
            .where(RankTracking.id == tracking_id)
        )
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def create(self, tracking: RankTracking) -> RankTracking:
        """추적 생성"""
        self._session.add(tracking)
        await self._session.flush()
        await self._session.refresh(tracking)
        return tracking

    async def update(self, tracking: RankTracking) -> RankTracking:
        """추적 업데이트"""
        await self._session.flush()
        await self._session.refresh(tracking)
        return tracking

    async def get_list(
        self,
        rank_type: RankType,
        status: Optional[TrackingStatus] = None,
        agency_id: Optional[int] = None,
        advertiser_id: Optional[int] = None,
        keyword: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[RankTracking]:
        """
        추적 목록 조회

        Args:
            rank_type: 순위 유형 (place/cafe/blog)
            status: 상태 필터
            agency_id: 업체 필터 (업체용)
            advertiser_id: 광고주 필터
            keyword: 검색어 (키워드, URL, 광고주명, 업체명으로 검색)
            skip: 건너뛸 개수
            limit: 가져올 개수
        """
        stmt = (
            select(RankTracking)
            .options(
                joinedload(RankTracking.agency).joinedload(Agency.user),
                joinedload(RankTracking.advertiser).joinedload(Advertiser.user),
            )
            .where(RankTracking.type == rank_type)
        )

        if status:
            stmt = stmt.where(RankTracking.status == status)

        if agency_id:
            stmt = stmt.where(RankTracking.agency_id == agency_id)

        if advertiser_id:
            stmt = stmt.where(RankTracking.advertiser_id == advertiser_id)

        if keyword:
            # 검색어로 키워드, URL, 광고주명, 업체명 검색
            # Note: agency.id = user.id, advertiser.id = user.id
            AgencyUser = aliased(User)
            AdvertiserUser = aliased(User)
            search_term = f"%{keyword}%"

            stmt = (
                stmt.outerjoin(Agency, RankTracking.agency_id == Agency.id)
                .outerjoin(AgencyUser, Agency.id == AgencyUser.id)  # agency.id = user.id
                .outerjoin(Advertiser, RankTracking.advertiser_id == Advertiser.id)
                .outerjoin(AdvertiserUser, Advertiser.id == AdvertiserUser.id)  # advertiser.id = user.id
                .where(
                    or_(
                        RankTracking.keyword.ilike(search_term),
                        RankTracking.url.ilike(search_term),
                        AgencyUser.company_name.ilike(search_term),
                        AdvertiserUser.company_name.ilike(search_term),
                    )
                )
            )

        stmt = stmt.order_by(RankTracking.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.unique().scalars().all())

    async def count(
        self,
        rank_type: RankType,
        status: Optional[TrackingStatus] = None,
        agency_id: Optional[int] = None,
        advertiser_id: Optional[int] = None,
        keyword: Optional[str] = None,
    ) -> int:
        """추적 개수 조회"""
        stmt = select(func.count(RankTracking.id)).where(RankTracking.type == rank_type)

        if status:
            stmt = stmt.where(RankTracking.status == status)

        if agency_id:
            stmt = stmt.where(RankTracking.agency_id == agency_id)

        if advertiser_id:
            stmt = stmt.where(RankTracking.advertiser_id == advertiser_id)

        if keyword:
            # 검색어로 키워드, URL, 광고주명, 업체명 검색
            # Note: agency.id = user.id, advertiser.id = user.id
            AgencyUser = aliased(User)
            AdvertiserUser = aliased(User)
            search_term = f"%{keyword}%"

            stmt = (
                stmt.outerjoin(Agency, RankTracking.agency_id == Agency.id)
                .outerjoin(AgencyUser, Agency.id == AgencyUser.id)  # agency.id = user.id
                .outerjoin(Advertiser, RankTracking.advertiser_id == Advertiser.id)
                .outerjoin(AdvertiserUser, Advertiser.id == AdvertiserUser.id)  # advertiser.id = user.id
                .where(
                    or_(
                        RankTracking.keyword.ilike(search_term),
                        RankTracking.url.ilike(search_term),
                        AgencyUser.company_name.ilike(search_term),
                        AdvertiserUser.company_name.ilike(search_term),
                    )
                )
            )

        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_active_trackings_by_type(
        self,
        rank_type: RankType,
    ) -> List[RankTracking]:
        """활성 추적 목록 조회 (배치용)"""
        stmt = (
            select(RankTracking)
            .where(RankTracking.type == rank_type)
            .where(RankTracking.status == TrackingStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_active_trackings(self) -> List[RankTracking]:
        """모든 활성 추적 목록 조회 (배치용)"""
        stmt = select(RankTracking).where(RankTracking.status == TrackingStatus.ACTIVE)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_agency_or_advertiser_id(self, user_id: int) -> int:
        """agency_id 또는 advertiser_id가 user_id인 모든 추적 삭제

        Note: CASCADE DELETE 대체용 (애플리케이션 레벨 삭제)
        """
        stmt = select(RankTracking).where(
            or_(
                RankTracking.agency_id == user_id,
                RankTracking.advertiser_id == user_id,
            )
        )
        result = await self._session.execute(stmt)
        trackings = list(result.scalars().all())

        for tracking in trackings:
            await self._session.delete(tracking)

        await self._session.flush()
        return len(trackings)
