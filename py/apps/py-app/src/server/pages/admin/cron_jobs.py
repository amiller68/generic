"""Admin cron job monitoring pages."""

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from py_core.database.models import User
from py_core.database.models.cron_job_run import CronJobRun, CronJobRunStatus

from src.server.deps import async_db, require_admin_user
from src.server.templates import templates

router = APIRouter()

ITEMS_PER_PAGE = 20


@router.get("", response_class=HTMLResponse)
async def list_cron_jobs(
    request: Request,
    user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(async_db),
    page: int = Query(1, ge=1),
    job_name: str = Query("", description="Filter by job name"),
    status: str = Query("", description="Filter by status"),
) -> HTMLResponse:
    """List all cron job runs with pagination and filtering."""
    offset = (page - 1) * ITEMS_PER_PAGE

    query = select(CronJobRun)
    count_query = select(func.count(CronJobRun.id))

    if job_name:
        query = query.where(CronJobRun.job_name.ilike(f"%{job_name}%"))
        count_query = count_query.where(CronJobRun.job_name.ilike(f"%{job_name}%"))
    if status:
        query = query.where(CronJobRun.status == status)
        count_query = count_query.where(CronJobRun.status == status)

    query = query.order_by(CronJobRun.started_at.desc())
    query = query.offset(offset).limit(ITEMS_PER_PAGE)

    result = await db.execute(query)
    items = list(result.scalars().all())

    count_result = await db.execute(count_query)
    total_count = count_result.scalar() or 0
    total_pages = max(1, (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

    # Get unique job names for filter dropdown
    job_names_query = select(CronJobRun.job_name).distinct()
    job_names_result = await db.execute(job_names_query)
    job_names = [row[0] for row in job_names_result.all()]

    context = {
        "request": request,
        "user": user,
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total_count": total_count,
        "job_name": job_name,
        "status": status,
        "job_names": job_names,
        "statuses": [s.value for s in CronJobRunStatus],
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "pages/admin/cron_jobs/table.html",
            context,
        )

    return templates.TemplateResponse(
        "pages/admin/cron_jobs/index.html",
        context,
    )
