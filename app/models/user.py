from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SQLEnum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.advertiser import Advertiser
    from app.models.agency import Agency


class UserRole(str, Enum):
    """사용자 역할"""

    ADMIN = "admin"
    AGENCY = "agency"
    ADVERTISER = "advertiser"


class ApprovalStatus(str, Enum):
    """승인 상태"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base, TimestampMixin):
    """
    사용자 모델

    - admin: 초기 데이터로 생성, 회원가입 없음
    - agency: 회원가입 후 승인 필요
    - advertiser: 회원가입 후 승인 필요
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 로그인 정보
    login_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # 사용자 정보
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # 역할 및 상태
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        nullable=False,
        default=UserRole.ADVERTISER,
    )
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        SQLEnum(ApprovalStatus),
        nullable=False,
        default=ApprovalStatus.PENDING,
    )

    # Relationships
    advertiser: Mapped[Optional["Advertiser"]] = relationship(
        "Advertiser", back_populates="user", uselist=False
    )
    agency: Mapped[Optional["Agency"]] = relationship(
        "Agency", back_populates="user", uselist=False
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, login_id={self.login_id}, role={self.role})>"
