"""Admin widget management pages."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from py_core.database.models import User, Widget, WidgetStatus
from py_core.observability import Logger

from src.server.deps import async_db, logger, redis, require_admin_user
from src.tasks.jobs.process_widget import process_widget_task
from py_core.events import (
    EventPublisher,
    WidgetCreatedEvent,
    WidgetDeletedEvent,
    WidgetUpdatedEvent,
)
from redis.asyncio import Redis

router = APIRouter()
templates = Jinja2Templates(directory="templates")

WIDGETS_PER_PAGE = 20


@router.get("", response_class=HTMLResponse)
async def list_widgets(
    request: Request,
    user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
    page: int = Query(1, ge=1),
    search: str = Query("", description="Search by name"),
    status: str = Query("", description="Filter by status"),
) -> HTMLResponse:
    """List all widgets with pagination, search, and status filter."""
    offset = (page - 1) * WIDGETS_PER_PAGE

    # Parse status filter
    status_filter = None
    if status and status in [s.value for s in WidgetStatus]:
        status_filter = WidgetStatus(status)

    widgets = await Widget.list_all(
        session=db,
        offset=offset,
        limit=WIDGETS_PER_PAGE,
        search=search if search else None,
        status=status_filter,
    )
    total_count = await Widget.count_all(
        session=db,
        search=search if search else None,
        status=status_filter,
    )
    total_pages = max(1, (total_count + WIDGETS_PER_PAGE - 1) // WIDGETS_PER_PAGE)

    context = {
        "request": request,
        "user": user,
        "widgets": widgets,
        "page": page,
        "total_pages": total_pages,
        "total_count": total_count,
        "search": search,
        "status": status,
        "statuses": [s.value for s in WidgetStatus],
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "pages/admin/widgets/table.html",
            context,
        )

    return templates.TemplateResponse(
        "pages/admin/widgets/index.html",
        context,
    )


@router.get("/new", response_class=HTMLResponse)
async def new_widget_form(
    request: Request,
    user: User = Depends(require_admin_user),
) -> HTMLResponse:
    """Show form to create a new widget."""
    return templates.TemplateResponse(
        "pages/admin/widgets/form.html",
        {
            "request": request,
            "user": user,
            "widget": None,
            "statuses": [s.value for s in WidgetStatus],
        },
    )


@router.post("/new", response_class=HTMLResponse)
async def create_widget(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    status: str = Form("draft"),
    priority: int = Form(0),
    is_public: bool = Form(False),
    user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
    redis_client: Redis = Depends(redis),
) -> HTMLResponse:
    """Create a new widget."""
    widget = await Widget.create(
        name=name,
        description=description if description else None,
        status=WidgetStatus(status),
        priority=priority,
        is_public=is_public,
        owner_id=str(user.id),
        session=db,
        logger=log,
    )
    await db.commit()

    log.info(f"Widget '{name}' created by {user.email}")

    # Publish typed event for real-time updates
    publisher = EventPublisher(redis_client)
    await publisher.publish(str(user.id), WidgetCreatedEvent(widget_id=str(widget.id)))

    # Return the new row for htmx to insert
    return templates.TemplateResponse(
        "pages/admin/widgets/row.html",
        {
            "request": request,
            "user": user,
            "widget": widget,
        },
        headers={"HX-Trigger": "widgetCreated"},
    )


@router.get("/{widget_id}/edit", response_class=HTMLResponse)
async def edit_widget_form(
    request: Request,
    widget_id: str,
    user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
) -> HTMLResponse:
    """Show form to edit a widget."""
    widget = await Widget.read(id=widget_id, session=db, logger=log)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    return templates.TemplateResponse(
        "pages/admin/widgets/form.html",
        {
            "request": request,
            "user": user,
            "widget": widget,
            "statuses": [s.value for s in WidgetStatus],
        },
    )


@router.post("/{widget_id}/edit", response_class=HTMLResponse)
async def update_widget(
    request: Request,
    widget_id: str,
    name: str = Form(...),
    description: str = Form(""),
    status: str = Form("draft"),
    priority: int = Form(0),
    is_public: bool = Form(False),
    user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
    redis_client: Redis = Depends(redis),
) -> HTMLResponse:
    """Update a widget."""
    widget = await Widget.read(id=widget_id, session=db, logger=log)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    await widget.update(
        name=name,
        description=description if description else None,
        status=WidgetStatus(status),
        priority=priority,
        is_public=is_public,
        session=db,
        logger=log,
    )
    await db.commit()

    log.info(f"Widget '{name}' updated by {user.email}")

    # Publish typed event for real-time updates
    publisher = EventPublisher(redis_client)
    await publisher.publish(str(user.id), WidgetUpdatedEvent(widget_id=widget_id))

    return templates.TemplateResponse(
        "pages/admin/widgets/row.html",
        {
            "request": request,
            "user": user,
            "widget": widget,
        },
    )


@router.post("/{widget_id}/activate", response_class=HTMLResponse)
async def activate_widget(
    request: Request,
    widget_id: str,
    user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
) -> HTMLResponse:
    """Activate a widget (set status to active)."""
    widget = await Widget.read(id=widget_id, session=db, logger=log)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    await widget.set_status(WidgetStatus.ACTIVE, session=db, logger=log)
    await db.commit()

    log.info(f"Widget '{widget.name}' activated by {user.email}")

    return templates.TemplateResponse(
        "pages/admin/widgets/row.html",
        {
            "request": request,
            "user": user,
            "widget": widget,
        },
    )


@router.post("/{widget_id}/archive", response_class=HTMLResponse)
async def archive_widget_handler(
    request: Request,
    widget_id: str,
    user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
) -> HTMLResponse:
    """Archive a widget."""
    widget = await Widget.read(id=widget_id, session=db, logger=log)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    await widget.set_status(WidgetStatus.ARCHIVED, session=db, logger=log)
    await db.commit()

    log.info(f"Widget '{widget.name}' archived by {user.email}")

    return templates.TemplateResponse(
        "pages/admin/widgets/row.html",
        {
            "request": request,
            "user": user,
            "widget": widget,
        },
    )


@router.post("/{widget_id}/process", response_class=HTMLResponse)
async def process_widget_handler(
    request: Request,
    widget_id: str,
    user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
) -> HTMLResponse:
    """Queue widget for background processing."""
    widget = await Widget.read(id=widget_id, session=db, logger=log)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    # Dispatch background task with user_id for events
    await process_widget_task.kiq(widget_id=widget_id, user_id=str(user.id))

    log.info(f"Widget '{widget.name}' queued for processing by {user.email}")

    # Return updated row (status won't change immediately, but shows feedback)
    return templates.TemplateResponse(
        "pages/admin/widgets/row.html",
        {
            "request": request,
            "user": user,
            "widget": widget,
            "processing": True,
        },
    )


@router.delete("/{widget_id}", response_class=HTMLResponse)
async def delete_widget(
    request: Request,
    widget_id: str,
    user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
    redis_client: Redis = Depends(redis),
) -> HTMLResponse:
    """Delete a widget."""
    widget = await Widget.read(id=widget_id, session=db, logger=log)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    widget_name = widget.name
    await widget.delete(session=db, logger=log)
    await db.commit()

    log.info(f"Widget '{widget_name}' deleted by {user.email}")

    # Publish typed event for real-time updates
    publisher = EventPublisher(redis_client)
    await publisher.publish(str(user.id), WidgetDeletedEvent(widget_id=widget_id))

    # Return empty response - htmx will remove the row
    return HTMLResponse(content="", status_code=200)
