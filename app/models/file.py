from __future__ import annotations

from enum import Enum

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class FileType(str, Enum):
    """파일 유형"""

    BUSINESS_LICENSE = "business_license"
    LOGO = "logo"
    OTHER = "other"


class File(Base, TimestampMixin):
    """파일 모델"""

    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[FileType] = mapped_column(String(50), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_path: Mapped[str] = mapped_column(
        String(500), nullable=False, unique=True, index=True
    )
    file_size: Mapped[int] = mapped_column(nullable=False)  # bytes

    def __repr__(self) -> str:
        return f"<File(id={self.id}, original_filename={self.original_filename})>"
