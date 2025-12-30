from app.routers.agency.common import router as common_router
from app.routers.agency.place_rank import router as place_rank_router
from app.routers.agency.cafe_rank import router as cafe_rank_router
from app.routers.agency.blog_rank import router as blog_rank_router
from app.routers.agency.dashboard import router as dashboard_router
from app.routers.agency.blog_posting import router as blog_posting_router
from app.routers.agency.press import router as press_router
from app.routers.agency.cafe_infiltration import router as cafe_infiltration_router

__all__ = [
    "common_router",
    "place_rank_router",
    "cafe_rank_router",
    "blog_rank_router",
    "dashboard_router",
    "blog_posting_router",
    "press_router",
    "cafe_infiltration_router",
]
