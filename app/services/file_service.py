from __future__ import annotations

from typing import Optional, Tuple

from fastapi import UploadFile

from app.core.config import Settings
from app.core.storage.abstract_storage import AbstractStorage
from app.models.file import File, FileType
from app.repositories.file_repository import FileRepository


class FileService:
    """파일 서비스"""

    def __init__(
        self,
        file_repo: FileRepository,
        storage: AbstractStorage,
        settings: Settings,
    ):
        self._file_repo = file_repo
        self._storage = storage
        self._settings = settings

    async def upload(
        self,
        upload_file: UploadFile,
        file_type: FileType = FileType.OTHER,
    ) -> File:
        """
        파일 업로드

        Raises:
            ValueError: 파일 크기 초과 또는 허용되지 않은 타입
        """
        # 1. 파일 크기 검증
        content = await upload_file.read()
        if len(content) > self._settings.MAX_FILE_SIZE:
            max_mb = self._settings.MAX_FILE_SIZE // 1024 // 1024
            raise ValueError(f"파일 크기가 {max_mb}MB를 초과합니다.")

        # 2. MIME 타입 검증
        if upload_file.content_type not in self._settings.ALLOWED_FILE_TYPES:
            raise ValueError(f"허용되지 않은 파일 형식입니다: {upload_file.content_type}")

        # 3. 스토리지에 업로드
        await upload_file.seek(0)
        storage_path = await self._storage.upload(
            upload_file.file,
            upload_file.filename or "unknown",
            upload_file.content_type or "application/octet-stream",
        )

        # 4. DB에 메타데이터 저장
        file = File(
            original_filename=upload_file.filename or "unknown",
            stored_filename=storage_path.split("/")[-1],
            file_type=file_type,
            mime_type=upload_file.content_type or "application/octet-stream",
            storage_path=storage_path,
            file_size=len(content),
        )

        return await self._file_repo.create(file)

    async def download(self, file_id: int) -> Tuple[Optional[bytes], Optional[File]]:
        """
        파일 다운로드

        Returns:
            (file_content, file_metadata) 또는 (None, None)
        """
        file = await self._file_repo.get_by_id(file_id)
        if not file:
            return None, None

        content = await self._storage.download(file.storage_path)
        return content, file

    async def get_file_info(self, file_id: int) -> Optional[File]:
        """파일 정보 조회"""
        return await self._file_repo.get_by_id(file_id)

    async def delete(self, file_id: int) -> bool:
        """파일 삭제"""
        file = await self._file_repo.get_by_id(file_id)
        if not file:
            return False

        await self._storage.delete(file.storage_path)
        await self._file_repo.delete(file)
        return True
