from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.advertiser import Advertiser
from app.models.agency import Agency
from app.models.user import ApprovalStatus, User, UserRole
from app.repositories.advertiser_repository import AdvertiserRepository
from app.repositories.agency_repository import AgencyRepository
from app.repositories.user_repository import UserRepository
from app.schemas.signup import AdvertiserSignupRequest, AgencySignupRequest


class SignupService:
    """회원가입 서비스"""

    def __init__(self, db_session: AsyncSession):
        self._db = db_session
        self._user_repo = UserRepository(db_session)
        self._advertiser_repo = AdvertiserRepository(db_session)
        self._agency_repo = AgencyRepository(db_session)

    async def check_id_available(self, login_id: str) -> bool:
        """ID 사용 가능 여부 확인"""
        return not await self._user_repo.exists_by_login_id(login_id)

    async def check_email_available(self, email: str) -> bool:
        """이메일 사용 가능 여부 확인"""
        return not await self._user_repo.exists_by_email(email)

    async def register_advertiser(self, request: AdvertiserSignupRequest) -> User:
        """
        광고주 회원가입

        Raises:
            ValueError: 중복 ID/이메일
        """
        # 1. 중복 확인
        if await self._user_repo.exists_by_login_id(request.login_id):
            raise ValueError("이미 사용 중인 아이디입니다.")

        if await self._user_repo.exists_by_email(request.email):
            raise ValueError("이미 등록된 이메일입니다.")

        # 2. 사용자 생성
        user = User(
            login_id=request.login_id,
            email=request.email,
            password_hash=hash_password(request.password),
            name=request.name,
            phone=request.phone,
            company_name=request.company_name,
            role=UserRole.ADVERTISER,
            approval_status=ApprovalStatus.PENDING,
        )
        user = await self._user_repo.create(user)

        # 3. 광고주 프로필 생성
        # Note: advertiser.id = user.id
        advertiser = Advertiser(
            id=user.id,
            business_license_file_id=request.business_license_file_id,
            logo_file_id=request.logo_file_id,
        )
        await self._advertiser_repo.create(advertiser)

        await self._db.commit()
        return user

    async def register_agency(self, request: AgencySignupRequest) -> User:
        """
        업체(대행사) 회원가입

        Raises:
            ValueError: 중복 ID/이메일
        """
        # 1. 중복 확인
        if await self._user_repo.exists_by_login_id(request.login_id):
            raise ValueError("이미 사용 중인 아이디입니다.")

        if await self._user_repo.exists_by_email(request.email):
            raise ValueError("이미 등록된 이메일입니다.")

        # 2. 사용자 생성
        user = User(
            login_id=request.login_id,
            email=request.email,
            password_hash=hash_password(request.password),
            name=request.name,
            phone=request.phone,
            company_name=request.company_name,
            role=UserRole.AGENCY,
            approval_status=ApprovalStatus.PENDING,
        )
        user = await self._user_repo.create(user)

        # 3. 업체 프로필 생성
        # Note: agency.id = user.id
        agency = Agency(
            id=user.id,
            categories=request.categories,
        )
        await self._agency_repo.create(agency)

        await self._db.commit()
        return user
