from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file import File


class FileRepository:
    """파일 저장소"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, file_id: int) -> File | None:
        """ID로 파일 조회"""
        stmt = select(File).where(File.id == file_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_storage_path(self, storage_path: str) -> File | None:
        """저장 경로로 파일 조회"""
        stmt = select(File).where(File.storage_path == storage_path)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, file: File) -> File:
        """파일 메타데이터 생성"""
        self._session.add(file)
        await self._session.flush()
        await self._session.refresh(file)
        return file

    async def delete(self, file: File) -> None:
        """파일 메타데이터 삭제"""
        await self._session.delete(file)
        await self._session.flush()
