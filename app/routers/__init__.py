from app.routers.auth import router as auth_router
from app.routers.common import signup_router, files_router
from app.routers.admin import members_router as admin_router

__all__ = [
    "auth_router",
    "signup_router",
    "files_router",
    "admin_router",
]
