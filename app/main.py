from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.dependencies import init_dependencies
from app.core.factory import close_all, get_database
from app.routers import auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 수명주기 관리"""
    settings = get_settings()

    # 시작: 인프라 초기화
    print(f"Starting {settings.APP_NAME} ({settings.APP_ENV})...")
    print(f"Database: {settings.DB_TYPE.value}")
    print(f"Session Store: {settings.SESSION_STORE_TYPE.value}")

    await init_dependencies(settings)

    # 개발 모드에서 테이블 자동 생성
    if settings.DEBUG:
        db = await get_database(settings)
        await db.create_tables()
        print("Database tables created (DEBUG mode)")

    yield

    # 종료: 정리
    await close_all()
    print("Application shutdown complete")


app = FastAPI(
    title="Announce-Go API",
    description="광고 성과 트래킹 서비스 API",
    version="0.1.0",
    lifespan=lifespan,
)

# 라우터 등록
app.include_router(auth_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "ok"}


@app.get("/")
async def root():
    """루트"""
    settings = get_settings()
    return {
        "name": settings.APP_NAME,
        "env": settings.APP_ENV,
        "version": "0.1.0",
    }
