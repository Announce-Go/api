from __future__ import annotations

from datetime import date
from typing import List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, joinedload

from app.models.advertiser import Advertiser
from app.models.agency import Agency
from app.models.user import User
from app.models.work_records import BlogPosting


class BlogPostingRepository:
    """블로그 포스팅 저장소"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, posting_id: int) -> BlogPosting | None:
        """ID로 포스팅 조회"""
        stmt = (
            select(BlogPosting)
            .options(
                joinedload(BlogPosting.agency).joinedload(Agency.user),
                joinedload(BlogPosting.advertiser).joinedload(Advertiser.user),
            )
            .where(BlogPosting.id == posting_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, posting: BlogPosting) -> BlogPosting:
        """포스팅 생성"""
        self._session.add(posting)
        await self._session.flush()
        await self._session.refresh(posting)
        return posting

    async def update(self, posting: BlogPosting) -> BlogPosting:
        """포스팅 업데이트"""
        await self._session.flush()
        await self._session.refresh(posting)
        return posting

    async def delete(self, posting: BlogPosting) -> None:
        """포스팅 삭제"""
        await self._session.delete(posting)
        await self._session.flush()

    async def get_list(
        self,
        agency_id: Optional[int] = None,
        advertiser_id: Optional[int] = None,
        keyword: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[BlogPosting]:
        """
        포스팅 목록 조회

        Args:
            agency_id: 업체 필터 (업체용)
            advertiser_id: 광고주 필터
            keyword: 검색어 (키워드, URL, 광고주명, 업체명으로 검색)
            skip: 건너뛸 개수
            limit: 가져올 개수
        """
        stmt = select(BlogPosting).options(
            joinedload(BlogPosting.agency).joinedload(Agency.user),
            joinedload(BlogPosting.advertiser).joinedload(Advertiser.user),
        )

        if agency_id:
            stmt = stmt.where(BlogPosting.agency_id == agency_id)

        if advertiser_id:
            stmt = stmt.where(BlogPosting.advertiser_id == advertiser_id)

        if keyword:
            AgencyUser = aliased(User)
            AdvertiserUser = aliased(User)
            search_term = f"%{keyword}%"

            stmt = (
                stmt.outerjoin(Agency, BlogPosting.agency_id == Agency.id)
                .outerjoin(AgencyUser, Agency.id == AgencyUser.id)
                .outerjoin(Advertiser, BlogPosting.advertiser_id == Advertiser.id)
                .outerjoin(AdvertiserUser, Advertiser.id == AdvertiserUser.id)
                .where(
                    or_(
                        BlogPosting.keyword.ilike(search_term),
                        BlogPosting.url.ilike(search_term),
                        AgencyUser.company_name.ilike(search_term),
                        AdvertiserUser.company_name.ilike(search_term),
                    )
                )
            )

        stmt = stmt.order_by(BlogPosting.posting_date.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.unique().scalars().all())

    async def count(
        self,
        agency_id: Optional[int] = None,
        advertiser_id: Optional[int] = None,
        keyword: Optional[str] = None,
    ) -> int:
        """포스팅 개수 조회"""
        stmt = select(func.count(BlogPosting.id))

        if agency_id:
            stmt = stmt.where(BlogPosting.agency_id == agency_id)

        if advertiser_id:
            stmt = stmt.where(BlogPosting.advertiser_id == advertiser_id)

        if keyword:
            AgencyUser = aliased(User)
            AdvertiserUser = aliased(User)
            search_term = f"%{keyword}%"

            stmt = (
                stmt.outerjoin(Agency, BlogPosting.agency_id == Agency.id)
                .outerjoin(AgencyUser, Agency.id == AgencyUser.id)
                .outerjoin(Advertiser, BlogPosting.advertiser_id == Advertiser.id)
                .outerjoin(AdvertiserUser, Advertiser.id == AdvertiserUser.id)
                .where(
                    or_(
                        BlogPosting.keyword.ilike(search_term),
                        BlogPosting.url.ilike(search_term),
                        AgencyUser.company_name.ilike(search_term),
                        AdvertiserUser.company_name.ilike(search_term),
                    )
                )
            )

        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def delete_by_agency_or_advertiser_id(self, user_id: int) -> int:
        """agency_id 또는 advertiser_id가 user_id인 모든 포스팅 삭제

        Note: CASCADE DELETE 대체용 (애플리케이션 레벨 삭제)
        """
        stmt = select(BlogPosting).where(
            or_(
                BlogPosting.agency_id == user_id,
                BlogPosting.advertiser_id == user_id,
            )
        )
        result = await self._session.execute(stmt)
        postings = list(result.scalars().all())

        for posting in postings:
            await self._session.delete(posting)

        await self._session.flush()
        return len(postings)
