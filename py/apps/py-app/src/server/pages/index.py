from fastapi import Request
from src.server.handlers.page import PageResponse

# Create page response helper - home page uses different layout
page = PageResponse(
    template="pages/index.html",
    layout="layouts/home.html",  # Using home layout for landing page
)


async def handler(request: Request):
    """Landing page handler

    Simple landing page with no authentication required

    Args:
        request: The incoming request

    Returns:
        HTMLResponse with full layout or just content for HTMX
    """
    return page.render(request, {})
