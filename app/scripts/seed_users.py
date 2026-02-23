"""
통합 User 더미 데이터 시드 스크립트

Admin 1개, Agency 3개, Advertiser 3개 + 매핑을 한 번에 생성

사용법:
    python -m app.scripts.seed_users
"""
from __future__ import annotations

import asyncio
from typing import Dict, List, Tuple

import structlog

from app.core.config import get_settings
from app.core.factory import close_all, get_database
from app.core.logging import configure_logging
from app.core.security import hash_password
from app.models.advertiser import Advertiser
from app.models.agency import Agency, AgencyCategory
from app.models.agency_advertiser_mapping import AgencyAdvertiserMapping
from app.models.user import ApprovalStatus, User, UserRole
from app.repositories.advertiser_repository import AdvertiserRepository
from app.repositories.agency_advertiser_mapping_repository import (
    AgencyAdvertiserMappingRepository,
)
from app.repositories.agency_repository import AgencyRepository
from app.repositories.user_repository import UserRepository

# =============================================================================
# 시드 데이터 정의
# =============================================================================

SEED_PASSWORD = "admin123"

ADMIN_DATA = {
    "login_id": "admin",
    "email": "admin@example.com",
    "name": "관리자",
}

AGENCY_DATA: List[Dict] = [
    {
        "login_id": "agency1",
        "email": "agency1@example.com",
        "name": "업체담당자1",
        "company_name": "마케팅에이전시A",
        "categories": [AgencyCategory.PLACE_RANK.value, AgencyCategory.BLOG_RANK.value],
    },
    {
        "login_id": "agency2",
        "email": "agency2@example.com",
        "name": "업체담당자2",
        "company_name": "마케팅에이전시B",
        "categories": [AgencyCategory.CAFE_RANK.value, AgencyCategory.BLOG_POSTING.value],
    },
    {
        "login_id": "agency3",
        "email": "agency3@example.com",
        "name": "업체담당자3",
        "company_name": "마케팅에이전시C",
        "categories": [AgencyCategory.PLACE_RANK.value, AgencyCategory.NEWS_ARTICLE.value],
    },
]

ADVERTISER_DATA: List[Dict] = [
    {
        "login_id": "advertiser1",
        "email": "advertiser1@example.com",
        "name": "광고주담당자1",
        "company_name": "테스트상점A",
    },
    {
        "login_id": "advertiser2",
        "email": "advertiser2@example.com",
        "name": "광고주담당자2",
        "company_name": "테스트상점B",
    },
    {
        "login_id": "advertiser3",
        "email": "advertiser3@example.com",
        "name": "광고주담당자3",
        "company_name": "테스트상점C",
    },
]

logger = structlog.get_logger()

# 매핑: (agency_login_id, [advertiser_login_ids])
MAPPING_DATA: List[Tuple[str, List[str]]] = [
    ("agency1", ["advertiser1", "advertiser2"]),
    ("agency2", ["advertiser2", "advertiser3"]),
    ("agency3", ["advertiser1", "advertiser3"]),
]


# =============================================================================
# 시드 함수들
# =============================================================================


async def seed_admin(
    user_repo: UserRepository,
    password_hash: str,
) -> int:
    """Admin 계정 생성"""
    existing = await user_repo.get_by_login_id(ADMIN_DATA["login_id"])
    if existing:
        logger.warning("admin_already_exists", login_id=ADMIN_DATA["login_id"])
        return 0

    admin = User(
        login_id=ADMIN_DATA["login_id"],
        email=ADMIN_DATA["email"],
        password_hash=password_hash,
        name=ADMIN_DATA["name"],
        role=UserRole.ADMIN,
        approval_status=ApprovalStatus.APPROVED,
    )
    await user_repo.create(admin)
    logger.info("admin_created", login_id=ADMIN_DATA["login_id"])
    return 1


async def seed_agencies(
    user_repo: UserRepository,
    agency_repo: AgencyRepository,
    password_hash: str,
) -> Tuple[int, Dict[str, int]]:
    """Agency 계정 생성 (User + Agency)"""
    created = 0
    agency_id_map: Dict[str, int] = {}  # login_id -> agency_id

    for data in AGENCY_DATA:
        existing = await user_repo.get_by_login_id(data["login_id"])
        if existing:
            logger.warning("agency_already_exists", login_id=data["login_id"])
            # 기존 Agency ID 조회 (agency.id = user.id)
            agency = await agency_repo.get_by_id(existing.id)
            if agency:
                agency_id_map[data["login_id"]] = agency.id
            continue

        # User 생성
        user = User(
            login_id=data["login_id"],
            email=data["email"],
            password_hash=password_hash,
            name=data["name"],
            company_name=data["company_name"],
            role=UserRole.AGENCY,
            approval_status=ApprovalStatus.APPROVED,
        )
        await user_repo.create(user)

        # Agency 생성 (agency.id = user.id)
        agency = Agency(
            id=user.id,
            categories=data["categories"],
        )
        await agency_repo.create(agency)
        agency_id_map[data["login_id"]] = agency.id

        logger.info("agency_created", login_id=data["login_id"])
        created += 1

    return created, agency_id_map


async def seed_advertisers(
    user_repo: UserRepository,
    advertiser_repo: AdvertiserRepository,
    password_hash: str,
) -> Tuple[int, Dict[str, int]]:
    """Advertiser 계정 생성 (User + Advertiser)"""
    created = 0
    advertiser_id_map: Dict[str, int] = {}  # login_id -> advertiser_id

    for data in ADVERTISER_DATA:
        existing = await user_repo.get_by_login_id(data["login_id"])
        if existing:
            logger.warning("advertiser_already_exists", login_id=data["login_id"])
            # 기존 Advertiser ID 조회 (advertiser.id = user.id)
            advertiser = await advertiser_repo.get_by_id(existing.id)
            if advertiser:
                advertiser_id_map[data["login_id"]] = advertiser.id
            continue

        # User 생성
        user = User(
            login_id=data["login_id"],
            email=data["email"],
            password_hash=password_hash,
            name=data["name"],
            company_name=data["company_name"],
            role=UserRole.ADVERTISER,
            approval_status=ApprovalStatus.APPROVED,
        )
        await user_repo.create(user)

        # Advertiser 생성 (advertiser.id = user.id)
        advertiser = Advertiser(id=user.id)
        await advertiser_repo.create(advertiser)
        advertiser_id_map[data["login_id"]] = advertiser.id

        logger.info("advertiser_created", login_id=data["login_id"])
        created += 1

    return created, advertiser_id_map


async def seed_mappings(
    mapping_repo: AgencyAdvertiserMappingRepository,
    agency_id_map: Dict[str, int],
    advertiser_id_map: Dict[str, int],
) -> int:
    """Agency-Advertiser 매핑 생성"""
    created = 0

    for agency_login_id, advertiser_login_ids in MAPPING_DATA:
        agency_id = agency_id_map.get(agency_login_id)
        if not agency_id:
            logger.warning("mapping_agency_not_found", agency_login_id=agency_login_id)
            continue

        for advertiser_login_id in advertiser_login_ids:
            advertiser_id = advertiser_id_map.get(advertiser_login_id)
            if not advertiser_id:
                logger.warning("mapping_advertiser_not_found",
                    agency_login_id=agency_login_id,
                    advertiser_login_id=advertiser_login_id,
                )
                continue

            # 이미 존재하는지 확인
            exists = await mapping_repo.exists(agency_id, advertiser_id)
            if exists:
                logger.warning("mapping_already_exists",
                    agency_login_id=agency_login_id,
                    advertiser_login_id=advertiser_login_id,
                )
                continue

            mapping = AgencyAdvertiserMapping(
                agency_id=agency_id,
                advertiser_id=advertiser_id,
            )
            await mapping_repo.create(mapping)
            logger.info("mapping_created",
                agency_login_id=agency_login_id,
                advertiser_login_id=advertiser_login_id,
            )
            created += 1

    return created


# =============================================================================
# 메인 함수
# =============================================================================


async def seed_users() -> None:
    """통합 시드 데이터 생성"""
    settings = get_settings()

    logger.info("seed_users_starting", db=settings.DB_TYPE.value)

    # 공통 비밀번호 해시
    password_hash = hash_password(SEED_PASSWORD)

    # 데이터베이스 연결
    db = await get_database(settings)
    await db.create_tables()
    logger.info("db_tables_verified")

    # 결과 집계
    admin_count = 0
    agency_count = 0
    advertiser_count = 0
    mapping_count = 0

    async for session in db.get_session():
        user_repo = UserRepository(session)
        agency_repo = AgencyRepository(session)
        advertiser_repo = AdvertiserRepository(session)
        mapping_repo = AgencyAdvertiserMappingRepository(session)

        # 1. Admin 생성
        admin_count = await seed_admin(user_repo, password_hash)

        # 2. Agency 생성
        agency_count, agency_id_map = await seed_agencies(
            user_repo, agency_repo, password_hash
        )

        # 3. Advertiser 생성
        advertiser_count, advertiser_id_map = await seed_advertisers(
            user_repo, advertiser_repo, password_hash
        )

        # 4. 매핑 생성
        mapping_count = await seed_mappings(
            mapping_repo, agency_id_map, advertiser_id_map
        )

    logger.info("seed_users_done",
        admin=admin_count,
        agencies=agency_count,
        advertisers=advertiser_count,
        mappings=mapping_count,
    )


async def main() -> None:
    """메인 함수"""
    configure_logging()
    try:
        await seed_users()
    finally:
        await close_all()


if __name__ == "__main__":
    asyncio.run(main())
