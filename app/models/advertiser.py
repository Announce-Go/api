from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.file import File
    from app.models.user import User


class Advertiser(Base, TimestampMixin):
    """광고주 모델"""

    __tablename__ = "advertisers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 사용자 연결 (1:1)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # 파일 연결
    business_license_file_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("files.id", ondelete="SET NULL"),
        nullable=True,
    )
    logo_file_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("files.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="advertiser")
    business_license_file: Mapped[Optional["File"]] = relationship(
        "File", foreign_keys=[business_license_file_id]
    )
    logo_file: Mapped[Optional["File"]] = relationship(
        "File", foreign_keys=[logo_file_id]
    )

    def __repr__(self) -> str:
        return f"<Advertiser(id={self.id}, user_id={self.user_id})>"
