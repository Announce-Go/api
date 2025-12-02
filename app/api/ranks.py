from fastapi import APIRouter, HTTPException

from app.crawler.place import get_place_rank, extract_place_id

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
