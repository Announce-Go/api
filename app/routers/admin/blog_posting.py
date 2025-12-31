from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_db_session, require_role
from app.schemas.work_records import BlogPostingListResponse
from app.services.work_records import BlogPostingService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/blog-posting", tags=["admin-blog-posting"])


def get_blog_posting_service(
    db: AsyncSession = Depends(get_db_session),
) -> BlogPostingService:
    return BlogPostingService(db)


@router.get(
    "",
    response_model=BlogPostingListResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def list_blog_postings(
    keyword: Optional[str] = Query(None, description="키워드 검색"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=1000, description="페이지당 항목 수"),
    service: BlogPostingService = Depends(get_blog_posting_service),
) -> BlogPostingListResponse:
    """블로그 포스팅 목록 (전체 조회)"""
    return await service.get_list(
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
