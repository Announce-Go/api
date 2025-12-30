from fastapi import APIRouter

from .common import router as common_router
from .place_rank import router as place_rank_router
from .cafe_rank import router as cafe_rank_router
from .blog_rank import router as blog_rank_router
from .dashboard import router as dashboard_router
from .blog_posting import router as blog_posting_router
from .press import router as press_router
from .cafe_infiltration import router as cafe_infiltration_router

# 그룹 라우터 생성
agency_router = APIRouter()
agency_router.include_router(common_router)
agency_router.include_router(place_rank_router)
agency_router.include_router(cafe_rank_router)
agency_router.include_router(blog_rank_router)
agency_router.include_router(dashboard_router)
agency_router.include_router(blog_posting_router)
agency_router.include_router(press_router)
agency_router.include_router(cafe_infiltration_router)

__all__ = ["agency_router"]
