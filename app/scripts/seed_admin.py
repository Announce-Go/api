"""
Admin 계정 시드 스크립트

사용법:
    python -m app.scripts.seed_admin

환경변수:
    ADMIN_LOGIN_ID: 관리자 로그인 ID (기본값: admin)
    ADMIN_PASSWORD: 관리자 비밀번호 (필수)
    ADMIN_EMAIL: 관리자 이메일 (기본값: admin@example.com)
    ADMIN_NAME: 관리자 이름 (기본값: 관리자)
"""
from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.core.factory import get_database, close_all
from app.core.security import hash_password
from app.models.user import User, UserRole, ApprovalStatus
from app.repositories.user_repository import UserRepository


async def seed_admin() -> None:
    """Admin 계정 생성 (없으면)"""
    settings = get_settings()

    print("=" * 50)
    print("Admin Seed Script")
    print("=" * 50)
    print(f"Database: {settings.DB_TYPE.value}")
    print(f"Admin Login ID: {settings.ADMIN_LOGIN_ID}")
    print(f"Admin Email: {settings.ADMIN_EMAIL}")
    print("=" * 50)

    # 데이터베이스 연결
    db = await get_database(settings)

    # 테이블 생성 (없으면)
    await db.create_tables()
    print("Database tables created/verified")

    # 세션 열기
    async for session in db.get_session():
        user_repo = UserRepository(session)

        # 기존 admin 확인
        existing_admin = await user_repo.get_by_login_id(settings.ADMIN_LOGIN_ID)
        if existing_admin:
            print(f"Admin account already exists: {existing_admin.login_id}")
            return

        # Admin 계정 생성
        admin = User(
            login_id=settings.ADMIN_LOGIN_ID,
            email=settings.ADMIN_EMAIL,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            name=settings.ADMIN_NAME,
            role=UserRole.ADMIN,
            approval_status=ApprovalStatus.APPROVED,
            is_active=True,
        )

        await user_repo.create(admin)
        print(f"Admin account created: {admin.login_id}")
        print("=" * 50)


async def main() -> None:
    """메인 함수"""
    try:
        await seed_admin()
    finally:
        await close_all()


if __name__ == "__main__":
    asyncio.run(main())
