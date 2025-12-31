"""공통 페이지네이션 스키마"""

from math import ceil

from pydantic import BaseModel, Field


class PaginationMeta(BaseModel):
    """페이지네이션 메타데이터"""

    total: int = Field(..., description="전체 항목 수")
    page: int = Field(..., ge=1, description="현재 페이지 번호")
    page_size: int = Field(..., ge=1, description="페이지당 항목 수")
    total_pages: int = Field(..., ge=0, description="전체 페이지 수")
    has_next: bool = Field(..., description="다음 페이지 존재 여부")
    has_prev: bool = Field(..., description="이전 페이지 존재 여부")

    @classmethod
    def create(cls, total: int, page: int, page_size: int) -> "PaginationMeta":
        """팩토리 메서드로 페이지네이션 메타 생성"""
        total_pages = ceil(total / page_size) if page_size > 0 else 0
        return cls(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )
