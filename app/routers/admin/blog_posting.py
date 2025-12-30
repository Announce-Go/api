from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_db_session, require_role
from app.schemas.work_records import BlogPostingListResponse
from app.services.work_records import BlogPostingService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/admin/blog-posting", tags=["admin-blog-posting"])


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
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: BlogPostingService = Depends(get_blog_posting_service),
) -> BlogPostingListResponse:
    """블로그 포스팅 목록 (전체 조회)"""
    return await service.get_list(
        keyword=keyword,
        skip=skip,
        limit=limit,
    )
