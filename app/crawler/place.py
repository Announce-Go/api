from __future__ import annotations

import re


def extract_place_id(url: str) -> str | None:
    """URL에서 Place ID 추출"""
    patterns = [
        r'/place/(\d+)',
        r'place=(\d+)',
        r'id=(\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


async def get_place_rank(keyword: str, place_id: str) -> int | None:
    """
    네이버 지도에서 키워드 검색 후 place_id의 순위 반환
    (TODO: 실제 네이버 크롤링 구현 필요)

    Returns:
        int: 순위 (1부터 시작)
        None: 순위권 외
    """
    # TODO: 실제 네이버 API/크롤링 구현
    return 1
