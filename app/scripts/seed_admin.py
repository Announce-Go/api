"""
Admin 계정 시드 스크립트

사용법:
    python -m app.scripts.seed_admin
"""
from __future__ import annotations

import asyncio

import structlog

from app.core.config import get_settings
from app.core.factory import get_database, close_all
from app.core.logging import configure_logging
from app.core.security import hash_password
from app.models.user import User, UserRole, ApprovalStatus
from app.repositories.user_repository import UserRepository

logger = structlog.get_logger()

ADMIN_DATA = {
    "login_id": "admin",
    "email": "admin@example.com",
    "name": "관리자",
    "password": "admin123",
}


async def seed_admin() -> None:
    """Admin 계정 생성 (없으면)"""
    settings = get_settings()

    logger.info("seed_admin_starting",
        db=settings.DB_TYPE.value,
        login_id=ADMIN_DATA["login_id"],
        email=ADMIN_DATA["email"],
    )

    # 데이터베이스 연결
    db = await get_database(settings)

    # 테이블 생성 (없으면)
    await db.create_tables()
    logger.info("db_tables_verified")

    # 세션 열기
    async for session in db.get_session():
        user_repo = UserRepository(session)

        # 기존 admin 확인
        existing_admin = await user_repo.get_by_login_id(ADMIN_DATA["login_id"])
        if existing_admin:
            logger.warning("admin_already_exists", login_id=existing_admin.login_id)
            return

        # Admin 계정 생성
        admin = User(
            login_id=ADMIN_DATA["login_id"],
            email=ADMIN_DATA["email"],
            password_hash=hash_password(ADMIN_DATA["password"]),
            name=ADMIN_DATA["name"],
            role=UserRole.ADMIN,
            approval_status=ApprovalStatus.APPROVED,
        )

        await user_repo.create(admin)
        logger.info("admin_created", login_id=admin.login_id)


async def main() -> None:
    """메인 함수"""
    configure_logging()
    try:
        await seed_admin()
    finally:
        await close_all()


if __name__ == "__main__":
    asyncio.run(main())
