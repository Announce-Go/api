from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseType(str, Enum):
    """데이터베이스 타입"""
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"


class SessionStoreType(str, Enum):
    """세션 저장소 타입"""
    REDIS = "redis"
    MEMORY = "memory"


class StorageType(str, Enum):
    """파일 저장소 타입"""
    LOCAL = "local"
    S3 = "s3"


class Settings(BaseSettings):
    """
    애플리케이션 설정

    환경변수 또는 .env 파일에서 로드
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # === App ===
    APP_NAME: str = "Announce-Go API"
    # === Database ===
    DB_TYPE: DatabaseType = DatabaseType.SQLITE
    DB_ECHO: bool = True  # SQL 쿼리 로깅

    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "announce_go"

    # SQLite
    SQLITE_PATH: str = "./local.db"

    # === Session Store ===
    SESSION_STORE_TYPE: SessionStoreType = SessionStoreType.MEMORY

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # === Session ===
    SESSION_EXPIRE_SECONDS: int = 60 * 60 * 24  # 24시간
    REMEMBER_ME_EXPIRE_SECONDS: int = 60 * 60 * 24 * 30  # 30일
    SESSION_COOKIE_NAME: str = "session_id"

    # === Admin Seed ===
    ADMIN_LOGIN_ID: str = "admin"
    ADMIN_PASSWORD: str = "admin123"  # 운영에서는 반드시 변경
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_NAME: str = "관리자"

    # === File Upload ===
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: list = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "application/pdf",
    ]

    # === Storage ===
    STORAGE_TYPE: StorageType = StorageType.LOCAL
    S3_BUCKET: str = ""
    S3_REGION: str = "ap-northeast-2"

    @property
    def database_url(self) -> str:
        """비동기 DB URL"""
        if self.DB_TYPE == DatabaseType.POSTGRESQL:
            return (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        return f"sqlite+aiosqlite:///{self.SQLITE_PATH}"

    @property
    def database_url_sync(self) -> str:
        """동기 DB URL (Alembic용)"""
        if self.DB_TYPE == DatabaseType.POSTGRESQL:
            return (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        return f"sqlite:///{self.SQLITE_PATH}"

    @property
    def redis_url(self) -> str:
        """Redis 연결 URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


@lru_cache
def get_settings() -> Settings:
    """싱글턴 Settings 인스턴스"""
    return Settings()
