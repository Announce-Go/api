from __future__ import annotations

import json
from datetime import timedelta
from typing import Any, Optional

import redis.asyncio as redis

from app.core.session.session_store import AbstractSessionStore


class RedisSessionStore(AbstractSessionStore):
    """Redis 기반 세션 저장소"""

    def __init__(
        self,
        redis_url: str,
        default_expire: timedelta = timedelta(hours=24),
        ssl_cert_reqs: Optional[str] = None,
    ):
        self._redis_url = redis_url
        self._default_expire = default_expire
        self._ssl_cert_reqs = ssl_cert_reqs
        self._client: Optional[redis.Redis] = None
        self._prefix = "session:"

    async def connect(self) -> None:
        """Redis 연결"""
        kwargs: dict[str, Any] = {
            "encoding": "utf-8",
            "decode_responses": True,
        }
        if self._ssl_cert_reqs:
            kwargs["ssl_cert_reqs"] = self._ssl_cert_reqs
        self._client = redis.from_url(self._redis_url, **kwargs)
        # 연결 테스트
        await self._client.ping()

    async def disconnect(self) -> None:
        """Redis 연결 해제"""
        if self._client:
            await self._client.close()
            self._client = None

    def _make_key(self, session_id: str) -> str:
        """세션 키 생성"""
        return f"{self._prefix}{session_id}"

    async def get(self, session_id: str) -> Optional[dict[str, Any]]:
        """세션 데이터 조회"""
        if not self._client:
            raise RuntimeError("Redis not connected")

        data = await self._client.get(self._make_key(session_id))
        if data is None:
            return None

        return json.loads(data)

    async def set(
        self,
        session_id: str,
        data: dict[str, Any],
        expire: Optional[timedelta] = None,
    ) -> None:
        """세션 데이터 저장"""
        if not self._client:
            raise RuntimeError("Redis not connected")

        expire = expire or self._default_expire
        await self._client.setex(
            self._make_key(session_id),
            expire,
            json.dumps(data),
        )

    async def delete(self, session_id: str) -> None:
        """세션 삭제"""
        if not self._client:
            raise RuntimeError("Redis not connected")

        await self._client.delete(self._make_key(session_id))

    async def exists(self, session_id: str) -> bool:
        """세션 존재 여부 확인"""
        if not self._client:
            raise RuntimeError("Redis not connected")

        return await self._client.exists(self._make_key(session_id)) > 0

    async def refresh(self, session_id: str, expire: timedelta | None = None) -> bool:
        """세션 만료 시간 갱신"""
        if not self._client:
            raise RuntimeError("Redis not connected")

        expire = expire or self._default_expire
        return await self._client.expire(
            self._make_key(session_id),
            int(expire.total_seconds()),
        )
