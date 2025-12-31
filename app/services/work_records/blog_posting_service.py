from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.work_records import BlogPosting
from app.repositories.work_records import BlogPostingRepository
from app.schemas.pagination import PaginationMeta
from app.schemas.work_records.blog_posting import (
    BlogPostingCreateRequest,
    BlogPostingDetailResponse,
    BlogPostingListItem,
    BlogPostingListResponse,
    BlogPostingUpdateRequest,
)


class BlogPostingService:
    """블로그 포스팅 서비스"""

    def __init__(self, db_session: AsyncSession):
        self._db = db_session
        self._repo = BlogPostingRepository(db_session)

    async def get_list(
        self,
        agency_id: Optional[int] = None,
        advertiser_id: Optional[int] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> BlogPostingListResponse:
        """
        블로그 포스팅 목록 조회

        Args:
            agency_id: 업체 필터 (업체용)
            advertiser_id: 광고주 필터
            keyword: 검색어
            page: 페이지 번호 (1부터 시작)
            page_size: 페이지당 항목 수

        Returns:
            BlogPostingListResponse: 포스팅 목록
        """
        skip = (page - 1) * page_size
        postings = await self._repo.get_list(
            agency_id=agency_id,
            advertiser_id=advertiser_id,
            keyword=keyword,
            skip=skip,
            limit=page_size,
        )
        total = await self._repo.count(
            agency_id=agency_id,
            advertiser_id=advertiser_id,
            keyword=keyword,
        )

        items = []
        for posting in postings:
            item = BlogPostingListItem(
                id=posting.id,
                keyword=posting.keyword,
                url=posting.url,
                posting_date=posting.posting_date,
                agency_id=posting.agency_id,
                agency_name=(
                    posting.agency.user.company_name
                    if posting.agency and posting.agency.user
                    else None
                ),
                advertiser_id=posting.advertiser_id,
                advertiser_name=(
                    posting.advertiser.user.company_name
                    if posting.advertiser and posting.advertiser.user
                    else None
                ),
                created_at=posting.created_at,
            )
            items.append(item)

        pagination = PaginationMeta.create(total=total, page=page, page_size=page_size)
        return BlogPostingListResponse(items=items, total=total, pagination=pagination)

    async def get_detail(
        self,
        posting_id: int,
        agency_id: Optional[int] = None,
        advertiser_id: Optional[int] = None,
    ) -> Optional[BlogPostingDetailResponse]:
        """
        블로그 포스팅 상세 조회

        Args:
            posting_id: 포스팅 ID
            agency_id: 업체 ID (권한 체크용)
            advertiser_id: 광고주 ID (권한 체크용)

        Returns:
            BlogPostingDetailResponse: 포스팅 상세 (없거나 권한 없으면 None)
        """
        posting = await self._repo.get_by_id(posting_id)
        if not posting:
            return None

        # 권한 체크
        if agency_id and posting.agency_id != agency_id:
            return None
        if advertiser_id and posting.advertiser_id != advertiser_id:
            return None

        return BlogPostingDetailResponse(
            id=posting.id,
            keyword=posting.keyword,
            url=posting.url,
            posting_date=posting.posting_date,
            agency_id=posting.agency_id,
            agency_name=(
                posting.agency.user.company_name
                if posting.agency and posting.agency.user
                else None
            ),
            advertiser_id=posting.advertiser_id,
            advertiser_name=(
                posting.advertiser.user.company_name
                if posting.advertiser and posting.advertiser.user
                else None
            ),
            created_at=posting.created_at,
            updated_at=posting.updated_at,
        )

    async def create(
        self,
        data: BlogPostingCreateRequest,
        agency_id: int,
    ) -> BlogPostingDetailResponse:
        """
        블로그 포스팅 등록 (Agency 전용)

        Args:
            data: 등록 요청 데이터
            agency_id: 업체 ID

        Returns:
            BlogPostingDetailResponse: 등록된 포스팅
        """
        posting = BlogPosting(
            agency_id=agency_id,
            advertiser_id=data.advertiser_id,
            keyword=data.keyword,
            url=data.url,
            posting_date=data.posting_date,
        )
        posting = await self._repo.create(posting)
        await self._db.commit()

        # 관계 정보 로드를 위해 다시 조회
        posting = await self._repo.get_by_id(posting.id)

        return BlogPostingDetailResponse(
            id=posting.id,
            keyword=posting.keyword,
            url=posting.url,
            posting_date=posting.posting_date,
            agency_id=posting.agency_id,
            agency_name=(
                posting.agency.user.company_name
                if posting.agency and posting.agency.user
                else None
            ),
            advertiser_id=posting.advertiser_id,
            advertiser_name=(
                posting.advertiser.user.company_name
                if posting.advertiser and posting.advertiser.user
                else None
            ),
            created_at=posting.created_at,
            updated_at=posting.updated_at,
        )

    async def update(
        self,
        posting_id: int,
        data: BlogPostingUpdateRequest,
        agency_id: int,
    ) -> Optional[BlogPostingDetailResponse]:
        """
        블로그 포스팅 수정 (Agency 전용 + 본인 것만)

        Args:
            posting_id: 포스팅 ID
            data: 수정 요청 데이터
            agency_id: 업체 ID

        Returns:
            BlogPostingDetailResponse: 수정된 포스팅 (없거나 권한 없으면 None)
        """
        posting = await self._repo.get_by_id(posting_id)
        if not posting:
            return None

        # 본인 것만 수정 가능
        if posting.agency_id != agency_id:
            return None

        # 필드 업데이트
        if data.keyword is not None:
            posting.keyword = data.keyword
        if data.url is not None:
            posting.url = data.url
        if data.advertiser_id is not None:
            posting.advertiser_id = data.advertiser_id
        if data.posting_date is not None:
            posting.posting_date = data.posting_date

        posting = await self._repo.update(posting)
        await self._db.commit()

        # 관계 정보 로드를 위해 다시 조회
        posting = await self._repo.get_by_id(posting.id)

        return BlogPostingDetailResponse(
            id=posting.id,
            keyword=posting.keyword,
            url=posting.url,
            posting_date=posting.posting_date,
            agency_id=posting.agency_id,
            agency_name=(
                posting.agency.user.company_name
                if posting.agency and posting.agency.user
                else None
            ),
            advertiser_id=posting.advertiser_id,
            advertiser_name=(
                posting.advertiser.user.company_name
                if posting.advertiser and posting.advertiser.user
                else None
            ),
            created_at=posting.created_at,
            updated_at=posting.updated_at,
        )

    async def delete(
        self,
        posting_id: int,
        agency_id: int,
    ) -> bool:
        """
        블로그 포스팅 삭제 (Agency 전용 + 본인 것만)

        Args:
            posting_id: 포스팅 ID
            agency_id: 업체 ID

        Returns:
            bool: 삭제 성공 여부
        """
        posting = await self._repo.get_by_id(posting_id)
        if not posting:
            return False

        # 본인 것만 삭제 가능
        if posting.agency_id != agency_id:
            return False

        await self._repo.delete(posting)
        await self._db.commit()
        return True
