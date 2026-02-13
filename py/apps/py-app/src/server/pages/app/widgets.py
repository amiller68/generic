"""User widget management pages.

This allows logged-in users to manage their own widgets.
Unlike the admin panel, users can only see and modify widgets they own.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from py_core.database.models import User, Widget, WidgetStatus
from py_core.events import (
    EventPublisher,
    WidgetCreatedEvent,
    WidgetDeletedEvent,
    WidgetUpdatedEvent,
)
from py_core.observability import Logger

from src.server.deps import async_db, logger, redis, require_logged_in_user
from src.tasks.jobs.process_widget import process_widget_task
from src.server.templates import templates

router = APIRouter()

WIDGETS_PER_PAGE = 10
APP_LAYOUT = "layouts/app.html"


def render_page(request: Request, template: str, context: dict) -> HTMLResponse:
    """Render a page with HTMX-aware layout handling.

    For HTMX requests: return just the content template
    For full page requests: wrap content in layout
    """
    context["request"] = request

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(template, context)

    # Full page - render content then wrap in layout
    content_template = templates.get_template(template)
    content_html = content_template.render(context)
    context["content"] = content_html
    return templates.TemplateResponse(APP_LAYOUT, context)


@router.get("", response_class=HTMLResponse)
async def list_widgets(
    request: Request,
    user: User = Depends(require_logged_in_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
    page: int = Query(1, ge=1),
    search: str = Query("", description="Search by name"),
    status: str = Query("", description="Filter by status"),
) -> HTMLResponse:
    """List user's widgets with pagination and filters."""
    offset = (page - 1) * WIDGETS_PER_PAGE

    # Parse status filter
    status_filter = None
    if status and status in [s.value for s in WidgetStatus]:
        status_filter = WidgetStatus(status)

    widgets = await Widget.list_all(
        session=db,
        offset=offset,
        limit=WIDGETS_PER_PAGE,
        owner_id=str(user.id),  # Only user's widgets
        search=search if search else None,
        status=status_filter,
    )
    total_count = await Widget.count_all(
        session=db,
        owner_id=str(user.id),
        search=search if search else None,
        status=status_filter,
    )
    total_pages = max(1, (total_count + WIDGETS_PER_PAGE - 1) // WIDGETS_PER_PAGE)

    context = {
        "user": user,
        "widgets": widgets,
        "page": page,
        "total_pages": total_pages,
        "total_count": total_count,
        "search": search,
        "status": status,
        "statuses": [s.value for s in WidgetStatus],
    }

    # For table-only refresh (filter/pagination)
    if (
        request.headers.get("HX-Request")
        and request.headers.get("HX-Target") == "widgets-table"
    ):
        context["request"] = request
        return templates.TemplateResponse("pages/app/widgets/table.html", context)

    return render_page(request, "pages/app/widgets/index.html", context)


@router.get("/new", response_class=HTMLResponse)
async def new_widget_form(
    request: Request,
    user: User = Depends(require_logged_in_user),
) -> HTMLResponse:
    """Show form to create a new widget."""
    return render_page(
        request,
        "pages/app/widgets/form.html",
        {
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
    priority: int = Form(0),
    is_public: bool = Form(False),
    user: User = Depends(require_logged_in_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
    redis_client: Redis = Depends(redis),
) -> HTMLResponse:
    """Create a new widget owned by the current user."""
    widget = await Widget.create(
        name=name,
        description=description if description else None,
        status=WidgetStatus.DRAFT,  # Users always start with draft
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

    # Redirect to widget detail page
    return render_page(
        request,
        "pages/app/widgets/detail.html",
        {
            "user": user,
            "widget": widget,
            "statuses": [s.value for s in WidgetStatus],
            "is_owner": True,
        },
    )


@router.get("/{widget_id}", response_class=HTMLResponse)
async def view_widget(
    request: Request,
    widget_id: str,
    user: User = Depends(require_logged_in_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
) -> HTMLResponse:
    """View a single widget."""
    widget = await Widget.read(id=widget_id, session=db, logger=log)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    # Users can only view their own widgets or public widgets
    if widget.owner_id != str(user.id) and not widget.is_public:
        raise HTTPException(status_code=403, detail="Access denied")

    return render_page(
        request,
        "pages/app/widgets/detail.html",
        {
            "user": user,
            "widget": widget,
            "statuses": [s.value for s in WidgetStatus],
            "is_owner": widget.owner_id == str(user.id),
        },
    )


@router.get("/{widget_id}/edit", response_class=HTMLResponse)
async def edit_widget_form(
    request: Request,
    widget_id: str,
    user: User = Depends(require_logged_in_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
) -> HTMLResponse:
    """Show form to edit a widget."""
    widget = await Widget.read(id=widget_id, session=db, logger=log)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    # Users can only edit their own widgets
    if widget.owner_id != str(user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    return render_page(
        request,
        "pages/app/widgets/form.html",
        {
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
    priority: int = Form(0),
    is_public: bool = Form(False),
    user: User = Depends(require_logged_in_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
    redis_client: Redis = Depends(redis),
) -> HTMLResponse:
    """Update a widget."""
    widget = await Widget.read(id=widget_id, session=db, logger=log)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    # Users can only edit their own widgets
    if widget.owner_id != str(user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    await widget.update(
        name=name,
        description=description if description else None,
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

    # Return to detail page
    return render_page(
        request,
        "pages/app/widgets/detail.html",
        {
            "user": user,
            "widget": widget,
            "statuses": [s.value for s in WidgetStatus],
            "is_owner": True,
        },
    )


@router.post("/{widget_id}/activate", response_class=HTMLResponse)
async def activate_widget(
    request: Request,
    widget_id: str,
    user: User = Depends(require_logged_in_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
    redis_client: Redis = Depends(redis),
) -> HTMLResponse:
    """Activate a widget (set status to active)."""
    widget = await Widget.read(id=widget_id, session=db, logger=log)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    if widget.owner_id != str(user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    await widget.set_status(WidgetStatus.ACTIVE, session=db, logger=log)
    await db.commit()

    log.info(f"Widget '{widget.name}' activated by {user.email}")

    # Publish typed event for real-time updates
    publisher = EventPublisher(redis_client)
    await publisher.publish(str(user.id), WidgetUpdatedEvent(widget_id=widget_id))

    # Return appropriate template based on HTMX target
    hx_target = request.headers.get("HX-Target", "")
    if hx_target == "main-content":
        return templates.TemplateResponse(
            "pages/app/widgets/detail.html",
            {
                "request": request,
                "user": user,
                "widget": widget,
                "statuses": [s.value for s in WidgetStatus],
                "is_owner": True,
            },
        )
    else:
        return templates.TemplateResponse(
            "pages/app/widgets/row.html",
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
    user: User = Depends(require_logged_in_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
    redis_client: Redis = Depends(redis),
) -> HTMLResponse:
    """Archive a widget."""
    widget = await Widget.read(id=widget_id, session=db, logger=log)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    if widget.owner_id != str(user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    await widget.set_status(WidgetStatus.ARCHIVED, session=db, logger=log)
    await db.commit()

    log.info(f"Widget '{widget.name}' archived by {user.email}")

    # Publish typed event for real-time updates
    publisher = EventPublisher(redis_client)
    await publisher.publish(str(user.id), WidgetUpdatedEvent(widget_id=widget_id))

    # Return appropriate template based on HTMX target
    hx_target = request.headers.get("HX-Target", "")
    if hx_target == "main-content":
        return templates.TemplateResponse(
            "pages/app/widgets/detail.html",
            {
                "request": request,
                "user": user,
                "widget": widget,
                "statuses": [s.value for s in WidgetStatus],
                "is_owner": True,
            },
        )
    else:
        return templates.TemplateResponse(
            "pages/app/widgets/row.html",
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
    user: User = Depends(require_logged_in_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
) -> HTMLResponse:
    """Queue widget for background processing."""
    widget = await Widget.read(id=widget_id, session=db, logger=log)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    if widget.owner_id != str(user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    # Dispatch background task with user_id for events
    await process_widget_task.kiq(widget_id=widget_id, user_id=str(user.id))

    log.info(f"Widget '{widget.name}' queued for processing by {user.email}")

    # Return appropriate template based on HTMX target
    hx_target = request.headers.get("HX-Target", "")
    if hx_target == "main-content":
        # Called from detail page - return detail with processing state
        return templates.TemplateResponse(
            "pages/app/widgets/detail.html",
            {
                "request": request,
                "user": user,
                "widget": widget,
                "statuses": [s.value for s in WidgetStatus],
                "is_owner": True,
                "processing": True,
            },
        )
    else:
        # Called from table - return row with processing state
        return templates.TemplateResponse(
            "pages/app/widgets/row.html",
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
    user: User = Depends(require_logged_in_user),
    db: AsyncSession = Depends(async_db),
    log: Logger = Depends(logger),
    redis_client: Redis = Depends(redis),
) -> HTMLResponse:
    """Delete a widget."""
    widget = await Widget.read(id=widget_id, session=db, logger=log)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")

    if widget.owner_id != str(user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    widget_name = widget.name
    await widget.delete(session=db, logger=log)
    await db.commit()

    log.info(f"Widget '{widget_name}' deleted by {user.email}")

    # Publish typed event for real-time updates
    publisher = EventPublisher(redis_client)
    await publisher.publish(str(user.id), WidgetDeletedEvent(widget_id=widget_id))

    # Return empty response - htmx will remove the row
    return HTMLResponse(content="", status_code=200)
