from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.file import FileType


class FileUploadResponse(BaseModel):
    """파일 업로드 응답"""

    id: int
    original_filename: str
    file_type: FileType
    mime_type: str
    file_size: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FileResponse(BaseModel):
    """파일 정보 응답"""

    id: int
    original_filename: str
    file_type: FileType
    mime_type: str
    file_size: int
    created_at: datetime

    model_config = {"from_attributes": True}
