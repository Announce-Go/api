from app.routers.auth import router as auth_router
from app.routers.common import signup_router, files_router

# Admin routers
from app.routers.admin import members_router as admin_members_router
from app.routers.admin import (
    place_rank_router as admin_place_rank_router,
    cafe_rank_router as admin_cafe_rank_router,
    blog_rank_router as admin_blog_rank_router,
    dashboard_router as admin_dashboard_router,
    blog_posting_router as admin_blog_posting_router,
    press_router as admin_press_router,
    cafe_infiltration_router as admin_cafe_infiltration_router,
)

# Agency routers
from app.routers.agency import (
    common_router as agency_common_router,
    place_rank_router as agency_place_rank_router,
    cafe_rank_router as agency_cafe_rank_router,
    blog_rank_router as agency_blog_rank_router,
    dashboard_router as agency_dashboard_router,
    blog_posting_router as agency_blog_posting_router,
    press_router as agency_press_router,
    cafe_infiltration_router as agency_cafe_infiltration_router,
)

# Advertiser routers
from app.routers.advertiser import (
    common_router as advertiser_common_router,
    place_rank_router as advertiser_place_rank_router,
    cafe_rank_router as advertiser_cafe_rank_router,
    blog_rank_router as advertiser_blog_rank_router,
    dashboard_router as advertiser_dashboard_router,
    blog_posting_router as advertiser_blog_posting_router,
    press_router as advertiser_press_router,
    cafe_infiltration_router as advertiser_cafe_infiltration_router,
)

__all__ = [
    # Common
    "auth_router",
    "signup_router",
    "files_router",
    # Admin
    "admin_members_router",
    "admin_place_rank_router",
    "admin_cafe_rank_router",
    "admin_blog_rank_router",
    "admin_dashboard_router",
    "admin_blog_posting_router",
    "admin_press_router",
    "admin_cafe_infiltration_router",
    # Agency
    "agency_common_router",
    "agency_place_rank_router",
    "agency_cafe_rank_router",
    "agency_blog_rank_router",
    "agency_dashboard_router",
    "agency_blog_posting_router",
    "agency_press_router",
    "agency_cafe_infiltration_router",
    # Advertiser
    "advertiser_common_router",
    "advertiser_place_rank_router",
    "advertiser_cafe_rank_router",
    "advertiser_blog_rank_router",
    "advertiser_dashboard_router",
    "advertiser_blog_posting_router",
    "advertiser_press_router",
    "advertiser_cafe_infiltration_router",
]
