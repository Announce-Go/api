from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class BlogPostingCreateRequest(BaseModel):
    """블로그 포스팅 등록 요청"""

    keyword: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=1)
    advertiser_id: int
    posting_date: date


class BlogPostingUpdateRequest(BaseModel):
    """블로그 포스팅 수정 요청"""

    keyword: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[str] = Field(None, min_length=1)
    advertiser_id: Optional[int] = None
    posting_date: Optional[date] = None


class BlogPostingListItem(BaseModel):
    """블로그 포스팅 목록 항목"""

    id: int
    keyword: str
    url: str
    posting_date: date

    # 관계 정보
    agency_id: int
    agency_name: Optional[str] = None
    advertiser_id: int
    advertiser_name: Optional[str] = None

    created_at: datetime

    model_config = {"from_attributes": True}


class BlogPostingListResponse(BaseModel):
    """블로그 포스팅 목록 응답"""

    items: List[BlogPostingListItem]
    total: int


class BlogPostingDetailResponse(BaseModel):
    """블로그 포스팅 상세 응답"""

    id: int
    keyword: str
    url: str
    posting_date: date

    # 관계 정보
    agency_id: int
    agency_name: Optional[str] = None
    advertiser_id: int
    advertiser_name: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
