from __future__ import annotations

from typing import BinaryIO, Optional

from app.core.storage.abstract_storage import AbstractStorage


class S3Storage(AbstractStorage):
    """S3 저장소 (미구현 - 스켈레톤)"""

    def __init__(self, bucket: str, region: str):
        self._bucket = bucket
        self._region = region
        self._client = None

    async def connect(self) -> None:
        """S3 클라이언트 초기화"""
        raise NotImplementedError("S3Storage is not yet implemented")

    async def disconnect(self) -> None:
        """S3 클라이언트 종료"""
        raise NotImplementedError("S3Storage is not yet implemented")

    async def upload(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
    ) -> str:
        """파일 업로드"""
        raise NotImplementedError("S3Storage is not yet implemented")

    async def download(self, storage_path: str) -> Optional[bytes]:
        """파일 다운로드"""
        raise NotImplementedError("S3Storage is not yet implemented")

    async def delete(self, storage_path: str) -> bool:
        """파일 삭제"""
        raise NotImplementedError("S3Storage is not yet implemented")

    async def exists(self, storage_path: str) -> bool:
        """파일 존재 여부 확인"""
        raise NotImplementedError("S3Storage is not yet implemented")
