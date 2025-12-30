from app.routers.common import common_router
from app.routers.admin import admin_router
from app.routers.agency import agency_router
from app.routers.advertiser import advertiser_router

__all__ = [
    "common_router",
    "admin_router",
    "agency_router",
    "advertiser_router",
]
