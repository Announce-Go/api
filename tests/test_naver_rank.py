"""네이버 순위 조회 테스트"""

import pytest
from app.crawler.naver import (
    get_place_rank,
    extract_place_id,
    get_blog_rank,
    extract_blog_id,
)


@pytest.mark.asyncio
async def test_place_rank():
    """플레이스 순위 조회 테스트"""
    keyword = "강남 한의원"
    url = "https://map.naver.com/p/search/%EA%B0%95%EB%82%A8%EC%97%AD%20%ED%95%9C%EC%9D%98%EC%9B%90/place/1910250411"

    place_id = extract_place_id(url)
    rank = await get_place_rank(keyword, place_id)

    print(f"\n키워드: {keyword}")
    print(f"Place ID: {place_id}")
    print(f"순위: {rank}위" if rank else "순위권 외")

    assert place_id is not None


@pytest.mark.asyncio
async def test_blog_rank():
    """블로그 순위 조회 테스트"""
    keyword = "강남역 한의원"
    url = "https://blog.naver.com/dbsaltjd11/224094288224"

    blog_info = extract_blog_id(url)
    assert blog_info is not None

    blog_id, log_no = blog_info
    rank = await get_blog_rank(keyword, blog_id, log_no)

    print(f"\n키워드: {keyword}")
    print(f"Blog ID: {blog_id}, Log No: {log_no}")
    print(f"순위: {rank}위" if rank else "순위권 외")
