from __future__ import annotations

from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.advertiser import Advertiser
from app.models.agency import Agency
from app.models.agency_advertiser_mapping import AgencyAdvertiserMapping
from app.models.user import ApprovalStatus, User, UserRole
from app.repositories.advertiser_repository import AdvertiserRepository
from app.repositories.agency_advertiser_mapping_repository import (
    AgencyAdvertiserMappingRepository,
)
from app.repositories.agency_repository import AgencyRepository
from app.repositories.user_repository import UserRepository


class AdminMemberService:
    """관리자 회원 관리 서비스"""

    def __init__(self, db_session: AsyncSession):
        self._db = db_session
        self._user_repo = UserRepository(db_session)
        self._advertiser_repo = AdvertiserRepository(db_session)
        self._agency_repo = AgencyRepository(db_session)
        self._mapping_repo = AgencyAdvertiserMappingRepository(db_session)

    # === 회원가입 승인 요청 ===

    async def get_pending_signups(
        self,
        role: Optional[UserRole] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[User], int]:
        """승인 대기 중인 회원가입 요청 목록"""
        users = await self._user_repo.get_pending_users(role, skip, limit)
        total = await self._user_repo.count_pending_users(role)
        return users, total

    async def get_signup_request_detail(self, user_id: int) -> Optional[User]:
        """회원가입 요청 상세 조회"""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            return None

        # 광고주/업체 프로필 로드
        if user.role == UserRole.ADVERTISER:
            await self._db.refresh(user, ["advertiser"])
            if user.advertiser:
                await self._db.refresh(
                    user.advertiser, ["business_license_file", "logo_file"]
                )
        elif user.role == UserRole.AGENCY:
            await self._db.refresh(user, ["agency"])

        return user

    async def approve_signup(
        self,
        user_id: int,
        advertiser_ids: Optional[List[int]] = None,
    ) -> User:
        """
        회원가입 승인 (업체인 경우 광고주 매핑 포함)

        Raises:
            ValueError: 사용자 없음 또는 대기 상태 아님
        """
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")

        if user.approval_status != ApprovalStatus.PENDING:
            raise ValueError("승인 대기 상태가 아닙니다.")

        # 승인 처리
        user.approval_status = ApprovalStatus.APPROVED
        user = await self._user_repo.update(user)

        # 업체인 경우 광고주 매핑
        if user.role == UserRole.AGENCY and advertiser_ids:
            agency = await self._agency_repo.get_by_user_id(user.id)
            if agency:
                # 유효한 광고주만 매핑
                for advertiser_id in advertiser_ids:
                    advertiser = await self._advertiser_repo.get_by_id(advertiser_id)
                    if advertiser:
                        # 중복 매핑 방지
                        if not await self._mapping_repo.exists(
                            agency.id, advertiser_id
                        ):
                            mapping = AgencyAdvertiserMapping(
                                agency_id=agency.id,
                                advertiser_id=advertiser_id,
                            )
                            await self._mapping_repo.create(mapping)

        await self._db.commit()
        return user

    async def reject_signup(self, user_id: int) -> User:
        """
        회원가입 거절

        Raises:
            ValueError: 사용자 없음 또는 대기 상태 아님
        """
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")

        if user.approval_status != ApprovalStatus.PENDING:
            raise ValueError("승인 대기 상태가 아닙니다.")

        user.approval_status = ApprovalStatus.REJECTED
        user = await self._user_repo.update(user)
        await self._db.commit()
        return user

    # === 광고주 관리 ===

    async def get_advertisers(
        self,
        approval_status: Optional[ApprovalStatus] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Advertiser], int]:
        """광고주 목록 조회"""
        advertisers = await self._advertiser_repo.get_all(
            approval_status, search, skip, limit
        )
        total = await self._advertiser_repo.count_all(approval_status, search)
        return advertisers, total

    async def get_advertiser_detail(
        self, advertiser_id: int
    ) -> Tuple[Optional[Advertiser], List[AgencyAdvertiserMapping]]:
        """광고주 상세 및 매핑된 업체 목록"""
        advertiser = await self._advertiser_repo.get_by_id(advertiser_id)
        if not advertiser:
            return None, []

        mappings = await self._mapping_repo.get_by_advertiser_id(advertiser_id)
        # Agency 정보 로드
        for mapping in mappings:
            if mapping.agency:
                await self._db.refresh(mapping.agency, ["user"])

        return advertiser, mappings

    # === 업체 관리 ===

    async def get_agencies(
        self,
        approval_status: Optional[ApprovalStatus] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Agency], int]:
        """업체 목록 조회"""
        agencies = await self._agency_repo.get_all(approval_status, search, skip, limit)
        total = await self._agency_repo.count_all(approval_status, search)
        return agencies, total

    async def get_agency_detail(
        self, agency_id: int
    ) -> Tuple[Optional[Agency], List[AgencyAdvertiserMapping]]:
        """업체 상세 및 매핑된 광고주 목록"""
        agency = await self._agency_repo.get_by_id(agency_id)
        if not agency:
            return None, []

        mappings = await self._mapping_repo.get_by_agency_id(agency_id)
        # Advertiser 정보 로드
        for mapping in mappings:
            if mapping.advertiser:
                await self._db.refresh(mapping.advertiser, ["user"])

        return agency, mappings
