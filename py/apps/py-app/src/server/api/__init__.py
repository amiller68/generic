from fastapi import APIRouter
from . import v0

# Create main HTML router
router = APIRouter()

# Include sub-routers with prefixes
router.include_router(v0.router, prefix="/v0")
