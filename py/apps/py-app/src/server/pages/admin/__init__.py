"""Admin dashboard routes."""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from .dashboard import router as dashboard_router
from .users import router as users_router
from .widgets import router as widgets_router
from .cron_jobs import router as cron_jobs_router
from .chat import router as chat_router

router = APIRouter()


# Redirect /_admin to /_admin/
@router.get("", response_class=RedirectResponse)
async def admin_redirect() -> RedirectResponse:
    return RedirectResponse(url="/_admin/", status_code=301)


# Include admin sub-routers
router.include_router(dashboard_router)
router.include_router(users_router, prefix="/users")
router.include_router(widgets_router, prefix="/widgets")
router.include_router(cron_jobs_router, prefix="/cron-jobs")
router.include_router(chat_router, prefix="/chat")
