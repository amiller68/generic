from fastapi import APIRouter
from . import auth

# Create main HTML router
router = APIRouter()

# Include sub-routers with prefixes
router.include_router(auth.router, prefix="/auth")
