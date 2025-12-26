from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any, Dict, Optional


class AbstractSessionStore(ABC):
    """세션 저장소 추상 클래스"""

    @abstractmethod
    async def connect(self) -> None:
        """저장소 연결"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """저장소 연결 해제"""
        pass

    @abstractmethod
    async def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        세션 데이터 조회

        Args:
            session_id: 세션 ID

        Returns:
            세션 데이터 딕셔너리 또는 None (없거나 만료됨)
        """
        pass

    @abstractmethod
    async def set(
        self,
        session_id: str,
        data: Dict[str, Any],
        expire: Optional[timedelta] = None,
    ) -> None:
        """
        세션 데이터 저장

        Args:
            session_id: 세션 ID
            data: 저장할 데이터
            expire: 만료 시간 (None이면 기본값 사용)
        """
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """
        세션 삭제

        Args:
            session_id: 세션 ID
        """
        pass

    @abstractmethod
    async def exists(self, session_id: str) -> bool:
        """
        세션 존재 여부 확인

        Args:
            session_id: 세션 ID

        Returns:
            존재하면 True
        """
        pass

    @abstractmethod
    async def refresh(self, session_id: str, expire: Optional[timedelta] = None) -> bool:
        """
        세션 만료 시간 갱신

        Args:
            session_id: 세션 ID
            expire: 새 만료 시간

        Returns:
            성공하면 True
        """
        pass
