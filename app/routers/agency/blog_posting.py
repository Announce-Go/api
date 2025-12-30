from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_db_session, require_role
from app.repositories.agency_repository import AgencyRepository
from app.schemas.work_records import (
    BlogPostingCreateRequest,
    BlogPostingDetailResponse,
    BlogPostingListResponse,
    BlogPostingUpdateRequest,
)
from app.services.work_records import BlogPostingService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/agency/blog-posting", tags=["agency-blog-posting"])


def get_blog_posting_service(
    db: AsyncSession = Depends(get_db_session),
) -> BlogPostingService:
    return BlogPostingService(db)


async def get_agency_id(
    current_user: Dict[str, Any] = Depends(require_role("agency")),
    db: AsyncSession = Depends(get_db_session),
) -> int:
    """현재 로그인한 업체의 agency_id 반환"""
    agency_repo = AgencyRepository(db)
    agency = await agency_repo.get_by_id(current_user["user_id"])
    if not agency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="업체 정보를 찾을 수 없습니다.",
        )
    return agency.id


@router.get(
    "",
    response_model=BlogPostingListResponse,
)
async def list_blog_postings(
    keyword: Optional[str] = Query(None, description="키워드 검색"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    agency_id: int = Depends(get_agency_id),
    service: BlogPostingService = Depends(get_blog_posting_service),
) -> BlogPostingListResponse:
    """블로그 포스팅 목록 (본인 업체만)"""
    return await service.get_list(
        agency_id=agency_id,
        keyword=keyword,
        skip=skip,
        limit=limit,
    )


@router.post(
    "",
    response_model=BlogPostingDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_blog_posting(
    data: BlogPostingCreateRequest,
    agency_id: int = Depends(get_agency_id),
    service: BlogPostingService = Depends(get_blog_posting_service),
) -> BlogPostingDetailResponse:
    """블로그 포스팅 등록"""
    return await service.create(data, agency_id)


@router.get(
    "/{posting_id}",
    response_model=BlogPostingDetailResponse,
)
async def get_blog_posting_detail(
    posting_id: int,
    agency_id: int = Depends(get_agency_id),
    service: BlogPostingService = Depends(get_blog_posting_service),
) -> BlogPostingDetailResponse:
    """블로그 포스팅 상세"""
    result = await service.get_detail(posting_id, agency_id=agency_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="포스팅을 찾을 수 없습니다.",
        )
    return result


@router.put(
    "/{posting_id}",
    response_model=BlogPostingDetailResponse,
)
async def update_blog_posting(
    posting_id: int,
    data: BlogPostingUpdateRequest,
    agency_id: int = Depends(get_agency_id),
    service: BlogPostingService = Depends(get_blog_posting_service),
) -> BlogPostingDetailResponse:
    """블로그 포스팅 수정 (본인 것만)"""
    result = await service.update(posting_id, data, agency_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="포스팅을 찾을 수 없거나 권한이 없습니다.",
        )
    return result


@router.delete(
    "/{posting_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_blog_posting(
    posting_id: int,
    agency_id: int = Depends(get_agency_id),
    service: BlogPostingService = Depends(get_blog_posting_service),
) -> None:
    """블로그 포스팅 삭제 (본인 것만)"""
    success = await service.delete(posting_id, agency_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="포스팅을 찾을 수 없거나 권한이 없습니다.",
        )
