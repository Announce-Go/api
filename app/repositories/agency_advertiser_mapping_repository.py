from __future__ import annotations

from typing import List, Tuple

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.advertiser import Advertiser
from app.models.agency import Agency
from app.models.agency_advertiser_mapping import AgencyAdvertiserMapping


class AgencyAdvertiserMappingRepository:
    """대행사-광고주 매핑 저장소"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_composite_key(
        self, agency_id: int, advertiser_id: int
    ) -> AgencyAdvertiserMapping | None:
        """복합키로 매핑 조회

        Note: 기존 get_by_id 대신 복합키(agency_id, advertiser_id)로 조회
        """
        stmt = (
            select(AgencyAdvertiserMapping)
            .options(
                joinedload(AgencyAdvertiserMapping.agency),
                joinedload(AgencyAdvertiserMapping.advertiser),
            )
            .where(
                and_(
                    AgencyAdvertiserMapping.agency_id == agency_id,
                    AgencyAdvertiserMapping.advertiser_id == advertiser_id,
                )
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_agency_id(self, agency_id: int) -> List[AgencyAdvertiserMapping]:
        """대행사 ID로 매핑 목록 조회"""
        stmt = (
            select(AgencyAdvertiserMapping)
            .options(
                joinedload(AgencyAdvertiserMapping.advertiser).joinedload(
                    Advertiser.user
                )
            )
            .where(AgencyAdvertiserMapping.agency_id == agency_id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_by_advertiser_id(
        self, advertiser_id: int
    ) -> List[AgencyAdvertiserMapping]:
        """광고주 ID로 매핑 목록 조회"""
        stmt = (
            select(AgencyAdvertiserMapping)
            .options(
                joinedload(AgencyAdvertiserMapping.agency).joinedload(Agency.user)
            )
            .where(AgencyAdvertiserMapping.advertiser_id == advertiser_id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())

    async def exists(self, agency_id: int, advertiser_id: int) -> bool:
        """매핑 존재 여부 확인"""
        stmt = select(AgencyAdvertiserMapping.agency_id).where(
            and_(
                AgencyAdvertiserMapping.agency_id == agency_id,
                AgencyAdvertiserMapping.advertiser_id == advertiser_id,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, mapping: AgencyAdvertiserMapping) -> AgencyAdvertiserMapping:
        """매핑 생성"""
        self._session.add(mapping)
        await self._session.flush()
        await self._session.refresh(mapping)
        return mapping

    async def create_bulk(
        self, mappings: List[AgencyAdvertiserMapping]
    ) -> List[AgencyAdvertiserMapping]:
        """매핑 일괄 생성"""
        self._session.add_all(mappings)
        await self._session.flush()
        for mapping in mappings:
            await self._session.refresh(mapping)
        return mappings

    async def delete(self, mapping: AgencyAdvertiserMapping) -> None:
        """매핑 삭제"""
        await self._session.delete(mapping)
        await self._session.flush()

    async def delete_by_composite_key(
        self, agency_id: int, advertiser_id: int
    ) -> bool:
        """복합키로 매핑 삭제"""
        mapping = await self.get_by_composite_key(agency_id, advertiser_id)
        if mapping:
            await self._session.delete(mapping)
            await self._session.flush()
            return True
        return False

    async def delete_by_agency_or_advertiser_id(self, user_id: int) -> int:
        """agency_id 또는 advertiser_id가 user_id인 모든 매핑 삭제

        Note: CASCADE DELETE 대체용 (애플리케이션 레벨 삭제)
        """
        # agency_id가 user_id인 매핑 조회 및 삭제
        agency_mappings = await self.get_by_agency_id(user_id)
        for mapping in agency_mappings:
            await self._session.delete(mapping)

        # advertiser_id가 user_id인 매핑 조회 및 삭제
        advertiser_mappings = await self.get_by_advertiser_id(user_id)
        for mapping in advertiser_mappings:
            await self._session.delete(mapping)

        await self._session.flush()
        return len(agency_mappings) + len(advertiser_mappings)
