from app.routers.admin.members import router as members_router
from app.routers.admin.place_rank import router as place_rank_router
from app.routers.admin.cafe_rank import router as cafe_rank_router
from app.routers.admin.blog_rank import router as blog_rank_router
from app.routers.admin.dashboard import router as dashboard_router
from app.routers.admin.blog_posting import router as blog_posting_router
from app.routers.admin.press import router as press_router
from app.routers.admin.cafe_infiltration import router as cafe_infiltration_router

__all__ = [
    "members_router",
    "place_rank_router",
    "cafe_rank_router",
    "blog_rank_router",
    "dashboard_router",
    "blog_posting_router",
    "press_router",
    "cafe_infiltration_router",
]
