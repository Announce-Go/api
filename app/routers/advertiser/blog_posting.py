from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_db_session, require_role
from app.repositories.advertiser_repository import AdvertiserRepository
from app.schemas.work_records import BlogPostingListResponse
from app.services.work_records import BlogPostingService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/blog-posting", tags=["advertiser-blog-posting"])


def get_blog_posting_service(
    db: AsyncSession = Depends(get_db_session),
) -> BlogPostingService:
    return BlogPostingService(db)


async def get_advertiser_id(
    current_user: Dict[str, Any] = Depends(require_role("advertiser")),
    db: AsyncSession = Depends(get_db_session),
) -> int:
    """현재 로그인한 광고주의 advertiser_id 반환"""
    advertiser_repo = AdvertiserRepository(db)
    advertiser = await advertiser_repo.get_by_id(current_user["user_id"])
    if not advertiser:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="광고주 정보를 찾을 수 없습니다.",
        )
    return advertiser.id


@router.get(
    "",
    response_model=BlogPostingListResponse,
)
async def list_blog_postings(
    keyword: Optional[str] = Query(None, description="키워드 검색"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=1000, description="페이지당 항목 수"),
    advertiser_id: int = Depends(get_advertiser_id),
    service: BlogPostingService = Depends(get_blog_posting_service),
) -> BlogPostingListResponse:
    """블로그 포스팅 목록 (본인만)"""
    return await service.get_list(
        advertiser_id=advertiser_id,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
