from __future__ import annotations

import re
import random
from urllib.parse import quote, parse_qs, urlparse

from app.crawler.browser_pool import BrowserPool


USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Firefox Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Safari Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]


def get_random_user_agent() -> str:
    """랜덤 User-Agent 반환"""
    return random.choice(USER_AGENTS)


# =============================================================================
# 플레이스 순위 조회
# =============================================================================

async def find_place_section(page):
    """
    플레이스 섹션 찾기

    1차: '플레이스' 텍스트가 포함된 헤더의 ancestor 섹션
    2차: 기존 셀렉터로 fallback
    """
    # 1차: 텍스트 기반 탐색
    place_header = await page.query_selector('h2:has-text("플레이스"), strong:has-text("플레이스"), span:has-text("플레이스")')
    if place_header:
        # 헤더의 부모 섹션 찾기 (최대 5단계 상위까지)
        section = await place_header.evaluate_handle('''
            (el) => {
                let current = el;
                for (let i = 0; i < 5; i++) {
                    current = current.parentElement;
                    if (!current) return null;
                    if (current.tagName === 'SECTION' ||
                        current.id?.includes('place') ||
                        current.id?.includes('loc') ||
                        current.className?.includes('place')) {
                        return current;
                    }
                }
                return current;  // 5단계 상위 요소 반환
            }
        ''')
        element = section.as_element()
        if element:
            return element

    # 2차: 기존 셀렉터 fallback
    fallback_selectors = [
        '#loc-main-section-root',
        'div[data-hveid="place"]',
        'section.sc_new.cs_common_module.case_place',
        'div.place_section'
    ]
    for selector in fallback_selectors:
        section = await page.query_selector(selector)
        if section:
            return section

    return None


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
    네이버 검색에서 키워드 검색 후 플레이스 섹션에서 place_id의 순위 반환

    Returns:
        int: 순위 (1부터 시작)
        None: 순위권 외
    """
    search_url = f"https://search.naver.com/search.naver?where=nexearch&query={quote(keyword)}"

    browser = await BrowserPool.get_browser()
    context = await browser.new_context(
        user_agent=get_random_user_agent()
    )
    page = await context.new_page()

    try:
        await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)

        # 플레이스 섹션 찾기
        place_section = await find_place_section(page)

        if not place_section:
            print(f"Error: 플레이스 섹션을 찾을 수 없음 (keyword: {keyword})")
            return None

        # 플레이스 섹션 내에서 업체명 링크들 찾기
        place_links = await place_section.query_selector_all('a[href*="map.naver.com"][href*="place/"]')

        # 중복 제거를 위해 이미 본 place_id 추적
        seen_ids = set()
        rank = 0

        for link in place_links:
            href = await link.get_attribute("href")
            if href:
                link_place_id = extract_place_id(href)
                if link_place_id and link_place_id not in seen_ids:
                    seen_ids.add(link_place_id)
                    rank += 1
                    if link_place_id == place_id:
                        return rank

        return None

    except Exception as e:
        print(f"Crawling error: {e}")
        return None

    finally:
        await context.close()


# =============================================================================
# 블로그 순위 조회
# =============================================================================

async def find_popular_section(page):
    """
    인기글 섹션 찾기

    '인기글' 텍스트가 포함된 헤더의 ancestor 섹션을 찾음
    """
    blog_header = await page.query_selector('h2:has-text("인기글"), strong:has-text("인기글"), span:has-text("인기글")')
    if blog_header:
        section = await blog_header.evaluate_handle('''
            (el) => {
                let current = el;
                for (let i = 0; i < 5; i++) {
                    current = current.parentElement;
                    if (!current) return null;
                    if (current.tagName === 'SECTION' ||
                        current.className?.includes('sc_new') ||
                        current.className?.includes('blog')) {
                        return current;
                    }
                }
                return current;
            }
        ''')
        element = section.as_element()
        if element:
            return element

    return None


def extract_blog_id(url: str) -> tuple[str, str] | None:
    """
    블로그 URL에서 블로그 ID와 글 번호 추출

    지원 URL 형식:
    - https://blog.naver.com/{blog_id}/{log_no}
    - https://m.blog.naver.com/{blog_id}/{log_no}
    - https://blog.naver.com/PostView.naver?blogId={blog_id}&logNo={log_no}
    - https://blog.naver.com/PostView.nhn?blogId={blog_id}&logNo={log_no}

    Returns:
        tuple[str, str]: (blog_id, log_no)
        None: 추출 실패
    """
    parsed = urlparse(url)

    # 쿼리 파라미터 형식: PostView.naver?blogId=xxx&logNo=xxx
    if 'PostView' in parsed.path:
        params = parse_qs(parsed.query)
        blog_id = params.get('blogId', [None])[0]
        log_no = params.get('logNo', [None])[0]
        if blog_id and log_no:
            return (blog_id, log_no)

    # 경로 형식: /blog_id/log_no
    path_parts = parsed.path.strip('/').split('/')
    if len(path_parts) >= 2:
        blog_id = path_parts[0]
        log_no = path_parts[1]
        # log_no가 숫자인지 확인
        if log_no.isdigit():
            return (blog_id, log_no)

    return None


async def get_blog_rank(keyword: str, blog_id: str, log_no: str) -> int | None:
    """
    네이버 검색 블로그 탭에서 특정 블로그 글의 순위 반환

    Args:
        keyword: 검색 키워드
        blog_id: 블로그 아이디
        log_no: 글 번호

    Returns:
        int: 순위 (1부터 시작)
        None: 순위권 외
    """
    search_url = f"https://search.naver.com/search.naver?where=blog&query={quote(keyword)}"

    browser = await BrowserPool.get_browser()
    context = await browser.new_context(
        user_agent=get_random_user_agent()
    )
    page = await context.new_page()

    try:
        await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)

        # 인기글 섹션 찾기
        popular_section = await find_popular_section(page)

        if not popular_section:
            print(f"Error: 인기글 섹션을 찾을 수 없음 (keyword: {keyword})")
            return None

        # 섹션 내에서 블로그 링크들 찾기
        blog_links = await popular_section.query_selector_all('a[href*="blog.naver.com"]')

        # 중복 제거를 위해 이미 본 blog_id 추적 (같은 블로거는 하나로 묶음)
        seen_blog_ids = set()
        rank = 0

        for link in blog_links:
            href = await link.get_attribute("href")
            if href:
                link_info = extract_blog_id(href)
                if link_info:
                    link_blog_id, link_log_no = link_info
                    if link_blog_id not in seen_blog_ids:
                        seen_blog_ids.add(link_blog_id)
                        rank += 1
                        if link_blog_id == blog_id and link_log_no == log_no:
                            return rank

        return None

    except Exception as e:
        print(f"Crawling error: {e}")
        return None

    finally:
        await context.close()
