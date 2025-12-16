from fastapi import APIRouter, HTTPException

from app.crawler.naver import (
    get_place_rank,
    extract_place_id,
    get_blog_rank,
    extract_blog_id,
    get_cafe_rank,
    extract_cafe_id,
)

router = APIRouter(prefix="/api/v1/ranks", tags=["ranks"])


@router.get("/place")
async def check_place_rank(keyword: str, url: str) -> int:
    """
    플레이스 순위 조회

    Args:
        keyword: 검색어
        url: 플레이스 URL (Place ID 포함)

    Returns:
        int: 순위 (1부터 시작), 순위권 외면 -1
    """
    place_id = extract_place_id(url)
    if not place_id:
        raise HTTPException(status_code=400, detail="Invalid place URL")

    rank = await get_place_rank(keyword, place_id)

    if rank is None:
        return -1

    return rank


@router.get("/blog")
async def check_blog_rank(keyword: str, url: str) -> int:
    """
    블로그 순위 조회

    Args:
        keyword: 검색어
        url: 블로그 URL

    Returns:
        int: 순위 (1부터 시작), 순위권 외면 -1
    """
    blog_info = extract_blog_id(url)
    if not blog_info:
        raise HTTPException(status_code=400, detail="Invalid blog URL")

    blog_id, log_no = blog_info
    rank = await get_blog_rank(keyword, blog_id, log_no)

    if rank is None:
        return -1

    return rank


@router.get("/cafe")
async def check_cafe_rank(keyword: str, url: str) -> int:
    """
    카페 순위 조회

    Args:
        keyword: 검색어
        url: 카페 URL

    Returns:
        int: 순위 (1부터 시작), 순위권 외면 -1
    """
    cafe_info = extract_cafe_id(url)
    if not cafe_info:
        raise HTTPException(status_code=400, detail="Invalid cafe URL")

    cafe_id, article_id = cafe_info
    rank = await get_cafe_rank(keyword, cafe_id, article_id)

    if rank is None:
        return -1

    return rank
