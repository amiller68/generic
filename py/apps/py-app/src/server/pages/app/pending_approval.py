from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from py_core.database.models import User
from src.server.deps import get_logged_in_user, async_db
from src.server.handlers.page import PageResponse

page = PageResponse(
    template="pages/app/pending_approval.html",
    layout="layouts/minimal.html",
)


async def handler(
    request: Request,
    user: User = Depends(get_logged_in_user),
    db: AsyncSession = Depends(async_db),
):
    return page.render(request, {"user": user})
