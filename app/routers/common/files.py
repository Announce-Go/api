from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.core.config import Settings, get_settings
from app.core.dependencies import get_db_session, get_storage_dep
from app.core.storage.abstract_storage import AbstractStorage
from app.models.file import FileType
from app.repositories.file_repository import FileRepository
from app.schemas.file import FileUploadResponse
from app.services.file_service import FileService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/files", tags=["files"])


def get_file_service(
    db: AsyncSession = Depends(get_db_session),
    storage: AbstractStorage = Depends(get_storage_dep),
    settings: Settings = Depends(get_settings),
) -> FileService:
    return FileService(FileRepository(db), storage, settings)


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    file_type: FileType = FileType.OTHER,
    service: FileService = Depends(get_file_service),
) -> FileUploadResponse:
    """
    파일 업로드

    - file_type: business_license, logo, other

    Response:
        FileUploadResponse
    """
    try:
        uploaded = await service.upload(file, file_type)
        return FileUploadResponse.model_validate(uploaded)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{file_id}")
async def download_file(
    file_id: int,
    service: FileService = Depends(get_file_service),
):
    """파일 다운로드

    Response:
        Binary file content
    """
    content, file_meta = await service.download(file_id)

    if content is None or file_meta is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="파일을 찾을 수 없습니다.",
        )

    return Response(
        content=content,
        media_type=file_meta.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{file_meta.original_filename}"',
        },
    )
