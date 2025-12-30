from app.routers.advertiser.common import router as common_router
from app.routers.advertiser.place_rank import router as place_rank_router
from app.routers.advertiser.cafe_rank import router as cafe_rank_router
from app.routers.advertiser.blog_rank import router as blog_rank_router
from app.routers.advertiser.dashboard import router as dashboard_router
from app.routers.advertiser.blog_posting import router as blog_posting_router
from app.routers.advertiser.press import router as press_router
from app.routers.advertiser.cafe_infiltration import router as cafe_infiltration_router

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
