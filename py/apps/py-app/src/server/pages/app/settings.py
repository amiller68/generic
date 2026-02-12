from fastapi import Request
from src.server.handlers.page import PageResponse

# Create page response helper
page = PageResponse(
    template="pages/app/settings.html",
    layout="layouts/app.html",
)


async def handler(request: Request):
    """Settings page handler

    User settings and preferences

    Args:
        request: The incoming request

    Returns:
        HTMLResponse with full layout or just content for HTMX
    """
    return page.render(request, {})
