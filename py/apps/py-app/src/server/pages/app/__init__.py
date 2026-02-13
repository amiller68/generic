from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from . import dashboard, login, settings, pending_approval
from .widgets import router as widgets_router

router = APIRouter()


# Redirect /app to /app/dashboard
@router.get("")
async def app_root():
    return RedirectResponse(url="/app/dashboard", status_code=302)


router.add_api_route("/dashboard", dashboard.handler, methods=["GET"])
router.add_api_route("/login", login.handler, methods=["GET"])
router.add_api_route("/settings", settings.handler, methods=["GET"])
router.add_api_route("/pending-approval", pending_approval.handler, methods=["GET"])

# Widgets routes
router.include_router(widgets_router, prefix="/widgets")
