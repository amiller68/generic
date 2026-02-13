"""Admin user management pages."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from py_core.database.models import User
from py_core.database.models.user import UserRole
from py_core.observability import Logger

from src.server.deps import async_db, logger, require_admin_user
from src.tasks.jobs.send_welcome_notification import send_welcome_notification
from src.server.templates import templates

router = APIRouter()

USERS_PER_PAGE = 20


@router.get("", response_class=HTMLResponse)
async def list_users(
    request: Request,
    user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
    page: int = Query(1, ge=1),
    search: str = Query("", description="Search by email"),
) -> HTMLResponse:
    """List all users with pagination and search."""
    offset = (page - 1) * USERS_PER_PAGE

    users = await User.list_all(
        session=db,
        offset=offset,
        limit=USERS_PER_PAGE,
        search=search if search else None,
    )
    total_count = await User.count_all(session=db, search=search if search else None)
    total_pages = max(1, (total_count + USERS_PER_PAGE - 1) // USERS_PER_PAGE)

    context = {
        "request": request,
        "user": user,
        "users": users,
        "page": page,
        "total_pages": total_pages,
        "total_count": total_count,
        "search": search,
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "pages/admin/users/table.html",
            context,
        )

    return templates.TemplateResponse(
        "pages/admin/users/index.html",
        context,
    )


@router.post("/{user_id}/approve", response_class=HTMLResponse)
async def approve_user(
    request: Request,
    user_id: str,
    admin: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
) -> HTMLResponse:
    """Approve user for platform access."""
    target_user = await User.read(id=user_id, session=db, logger=log)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    await target_user.set_approved(True, session=db)
    await db.commit()

    log.info(f"User {target_user.email} approved by {admin.email}")

    # Dispatch welcome notification background task
    await send_welcome_notification.kiq(user_id=user_id)

    return templates.TemplateResponse(
        "pages/admin/users/row.html",
        {
            "request": request,
            "user": admin,
            "target_user": target_user,
        },
    )


@router.post("/{user_id}/revoke", response_class=HTMLResponse)
async def revoke_user(
    request: Request,
    user_id: str,
    admin: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
) -> HTMLResponse:
    """Revoke user's platform access."""
    target_user = await User.read(id=user_id, session=db, logger=log)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    if str(target_user.id) == str(admin.id):
        raise HTTPException(status_code=400, detail="Cannot revoke your own access")

    await target_user.set_approved(False, session=db)
    await db.commit()

    log.info(f"User {target_user.email} access revoked by {admin.email}")

    return templates.TemplateResponse(
        "pages/admin/users/row.html",
        {
            "request": request,
            "user": admin,
            "target_user": target_user,
        },
    )


@router.post("/{user_id}/promote", response_class=HTMLResponse)
async def promote_user(
    request: Request,
    user_id: str,
    admin: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
) -> HTMLResponse:
    """Promote user to admin role."""
    target_user = await User.read(id=user_id, session=db, logger=log)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    await target_user.set_role(UserRole.ADMIN, session=db)
    await db.commit()

    log.info(f"User {target_user.email} promoted to admin by {admin.email}")

    return templates.TemplateResponse(
        "pages/admin/users/row.html",
        {
            "request": request,
            "user": admin,
            "target_user": target_user,
        },
    )


@router.post("/{user_id}/demote", response_class=HTMLResponse)
async def demote_user(
    request: Request,
    user_id: str,
    admin: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
) -> HTMLResponse:
    """Demote user from admin role."""
    target_user = await User.read(id=user_id, session=db, logger=log)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    if str(target_user.id) == str(admin.id):
        raise HTTPException(status_code=400, detail="Cannot demote yourself")

    await target_user.set_role(None, session=db)
    await db.commit()

    log.info(f"User {target_user.email} demoted from admin by {admin.email}")

    return templates.TemplateResponse(
        "pages/admin/users/row.html",
        {
            "request": request,
            "user": admin,
            "target_user": target_user,
        },
    )
