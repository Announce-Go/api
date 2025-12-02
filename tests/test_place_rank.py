"""플레이스 순위 조회 테스트"""

import asyncio
from app.crawler.place import get_place_rank, extract_place_id


if __name__ == "__main__":
    keyword = "강남 한의원"
    url = "https://map.naver.com/p/search/%EA%B0%95%EB%82%A8%EC%97%AD%20%ED%95%9C%EC%9D%98%EC%9B%90/place/1910250411"

    place_id = extract_place_id(url)
    rank = asyncio.run(get_place_rank(keyword, place_id))

    print(f"키워드: {keyword}")
    print(f"Place ID: {place_id}")
    print(f"순위: {rank}위" if rank else "순위권 외")
