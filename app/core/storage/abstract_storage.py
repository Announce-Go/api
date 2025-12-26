from __future__ import annotations

from abc import ABC, abstractmethod
from typing import BinaryIO, Optional


class AbstractStorage(ABC):
    """파일 저장소 추상 클래스"""

    @abstractmethod
    async def connect(self) -> None:
        """저장소 연결/초기화"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """저장소 연결 해제"""
        pass

    @abstractmethod
    async def upload(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
    ) -> str:
        """
        파일 업로드

        Args:
            file: 파일 바이너리
            filename: 저장할 파일명
            content_type: MIME 타입

        Returns:
            저장된 파일 경로 (storage_path)
        """
        pass

    @abstractmethod
    async def download(self, storage_path: str) -> Optional[bytes]:
        """
        파일 다운로드

        Args:
            storage_path: 저장된 파일 경로

        Returns:
            파일 바이너리 또는 None
        """
        pass

    @abstractmethod
    async def delete(self, storage_path: str) -> bool:
        """
        파일 삭제

        Args:
            storage_path: 저장된 파일 경로

        Returns:
            성공 여부
        """
        pass

    @abstractmethod
    async def exists(self, storage_path: str) -> bool:
        """
        파일 존재 여부 확인

        Args:
            storage_path: 저장된 파일 경로

        Returns:
            존재하면 True
        """
        pass
