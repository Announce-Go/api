from __future__ import annotations

from datetime import timedelta

from app.core.config import DatabaseType, SessionStoreType, Settings
from app.core.interfaces.database import AbstractDatabase
from app.core.interfaces.session_store import AbstractSessionStore


# 싱글턴 인스턴스 캐시
_database_instance: AbstractDatabase | None = None
_session_store_instance: AbstractSessionStore | None = None


async def get_database(settings: Settings) -> AbstractDatabase:
    """
    설정에 따른 Database 구현체 반환 (싱글턴)

    Args:
        settings: 애플리케이션 설정

    Returns:
        AbstractDatabase 구현체
    """
    global _database_instance

    if _database_instance is not None:
        return _database_instance

    if settings.DB_TYPE == DatabaseType.POSTGRESQL:
        from app.core.database.postgresql import PostgreSQLDatabase

        _database_instance = PostgreSQLDatabase(settings.database_url, echo=settings.DB_ECHO)
    else:
        from app.core.database.sqlite import SQLiteDatabase

        _database_instance = SQLiteDatabase(settings.database_url, echo=settings.DB_ECHO)

    await _database_instance.connect()
    return _database_instance


async def get_session_store(settings: Settings) -> AbstractSessionStore:
    """
    설정에 따른 SessionStore 구현체 반환 (싱글턴)

    Args:
        settings: 애플리케이션 설정

    Returns:
        AbstractSessionStore 구현체
    """
    global _session_store_instance

    if _session_store_instance is not None:
        return _session_store_instance

    default_expire = timedelta(seconds=settings.SESSION_EXPIRE_SECONDS)

    if settings.SESSION_STORE_TYPE == SessionStoreType.REDIS:
        from app.core.session.redis_store import RedisSessionStore

        _session_store_instance = RedisSessionStore(
            settings.redis_url,
            default_expire=default_expire,
        )
    else:
        from app.core.session.memory_store import MemorySessionStore

        _session_store_instance = MemorySessionStore(default_expire=default_expire)

    await _session_store_instance.connect()
    return _session_store_instance


async def close_all() -> None:
    """모든 인프라 연결 종료"""
    global _database_instance, _session_store_instance

    if _database_instance:
        await _database_instance.disconnect()
        _database_instance = None

    if _session_store_instance:
        await _session_store_instance.disconnect()
        _session_store_instance = None


def reset_instances() -> None:
    """
    인스턴스 초기화 (테스트용)

    주의: 연결 해제 없이 인스턴스만 초기화
    """
    global _database_instance, _session_store_instance
    _database_instance = None
    _session_store_instance = None
