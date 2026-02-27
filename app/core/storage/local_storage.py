from __future__ import annotations

import uuid
from pathlib import Path
from typing import BinaryIO, Optional

import aiofiles

from app.core.storage.abstract_storage import AbstractStorage
from app.core.timezone import now_kst


class LocalStorage(AbstractStorage):
    """로컬 파일시스템 저장소"""

    def __init__(self, base_path: str):
        self._base_path = Path(base_path)

    async def connect(self) -> None:
        """저장소 초기화 (디렉토리 생성)"""
        self._base_path.mkdir(parents=True, exist_ok=True)

    async def disconnect(self) -> None:
        """연결 해제 (로컬은 불필요)"""
        pass

    def _generate_storage_path(self, original_filename: str) -> str:
        """고유한 저장 경로 생성 (YYYY/MM/DD/uuid.ext)"""
        today = now_kst().strftime("%Y/%m/%d")
        ext = Path(original_filename).suffix
        unique_name = f"{uuid.uuid4().hex}{ext}"
        return f"{today}/{unique_name}"

    async def upload(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
    ) -> str:
        """파일 업로드"""
        storage_path = self._generate_storage_path(filename)
        full_path = self._base_path / storage_path

        # 디렉토리 생성
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # 파일 저장
        content = file.read()
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(content)

        return storage_path

    async def download(self, storage_path: str) -> Optional[bytes]:
        """파일 다운로드"""
        full_path = self._base_path / storage_path

        if not full_path.exists():
            return None

        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete(self, storage_path: str) -> bool:
        """파일 삭제"""
        full_path = self._base_path / storage_path

        if full_path.exists():
            full_path.unlink()
            return True
        return False

    async def exists(self, storage_path: str) -> bool:
        """파일 존재 여부 확인"""
        return (self._base_path / storage_path).exists()
