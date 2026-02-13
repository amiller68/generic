from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from py_core.observability import Logger

from src.server.deps import logger, async_db

router = APIRouter()


@router.get("/readyz")
async def ready(
    logger: Logger = Depends(logger),
    db: AsyncSession = Depends(async_db),
):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="health check failed")


@router.get("/livez")
async def live(
    logger: Logger = Depends(logger),
):
    return {"status": "ok"}
