from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from app.core.interfaces.session_store import AbstractSessionStore


@dataclass
class SessionEntry:
    """세션 엔트리"""

    data: Dict[str, Any]
    expires_at: datetime


class MemorySessionStore(AbstractSessionStore):
    """인메모리 세션 저장소 (개발/테스트용)"""

    def __init__(self, default_expire: timedelta = timedelta(hours=24)):
        self._store: Dict[str, SessionEntry] = {}
        self._default_expire = default_expire
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

    async def connect(self) -> None:
        """만료된 세션 정리 태스크 시작"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def disconnect(self) -> None:
        """정리 태스크 종료 및 저장소 비우기"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        self._store.clear()

    async def _cleanup_loop(self) -> None:
        """주기적으로 만료된 세션 정리"""
        while True:
            await asyncio.sleep(60)  # 1분마다 정리
            await self._cleanup_expired()

    async def _cleanup_expired(self) -> None:
        """만료된 세션 삭제"""
        now = datetime.utcnow()
        async with self._lock:
            expired_keys = [
                key for key, entry in self._store.items() if entry.expires_at <= now
            ]
            for key in expired_keys:
                del self._store[key]

    async def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 데이터 조회"""
        async with self._lock:
            entry = self._store.get(session_id)
            if entry is None:
                return None

            # 만료 확인
            if entry.expires_at <= datetime.utcnow():
                del self._store[session_id]
                return None

            return entry.data.copy()

    async def set(
        self,
        session_id: str,
        data: Dict[str, Any],
        expire: Optional[timedelta] = None,
    ) -> None:
        """세션 데이터 저장"""
        expire = expire or self._default_expire
        expires_at = datetime.utcnow() + expire

        async with self._lock:
            self._store[session_id] = SessionEntry(
                data=data.copy(),
                expires_at=expires_at,
            )

    async def delete(self, session_id: str) -> None:
        """세션 삭제"""
        async with self._lock:
            self._store.pop(session_id, None)

    async def exists(self, session_id: str) -> bool:
        """세션 존재 여부 확인"""
        async with self._lock:
            entry = self._store.get(session_id)
            if entry is None:
                return False

            if entry.expires_at <= datetime.utcnow():
                del self._store[session_id]
                return False

            return True

    async def refresh(self, session_id: str, expire: Optional[timedelta] = None) -> bool:
        """세션 만료 시간 갱신"""
        expire = expire or self._default_expire
        expires_at = datetime.utcnow() + expire

        async with self._lock:
            entry = self._store.get(session_id)
            if entry is None:
                return False

            entry.expires_at = expires_at
            return True
