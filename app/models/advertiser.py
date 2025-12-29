from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.file import File
    from app.models.user import User


class Advertiser(Base, TimestampMixin):
    """광고주 모델"""

    __tablename__ = "advertisers"

    # PK = user.id (auto-increment 없음)
    id: Mapped[int] = mapped_column(primary_key=True)  # references: users.id

    # 파일 연결 (FK 제약 없음, 애플리케이션 레벨에서 관리)
    business_license_file_id: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )  # references: files.id
    logo_file_id: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )  # references: files.id

    # Relationships (FK 제약 없이 primaryjoin으로 연결)
    user: Mapped["User"] = relationship(
        "User",
        back_populates="advertiser",
        primaryjoin="Advertiser.id == User.id",
        foreign_keys="Advertiser.id",
    )
    business_license_file: Mapped[Optional["File"]] = relationship(
        "File",
        primaryjoin="Advertiser.business_license_file_id == File.id",
        foreign_keys="Advertiser.business_license_file_id",
    )
    logo_file: Mapped[Optional["File"]] = relationship(
        "File",
        primaryjoin="Advertiser.logo_file_id == File.id",
        foreign_keys="Advertiser.logo_file_id",
    )

    def __repr__(self) -> str:
        return f"<Advertiser(id={self.id})>"
