from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from . import index, app
from .admin import router as admin_router

router = APIRouter()

# Home page
router.add_api_route(
    "/",
    index.handler,
    methods=["GET"],
    response_class=HTMLResponse,
)

# App routes (authenticated)
router.include_router(app.router, prefix="/app")

# Admin routes
router.include_router(admin_router, prefix="/_admin")
