from fastapi import Request
from src.server.handlers.page import PageResponse

# Create page response helper - login uses minimal layout (no header)
page = PageResponse(
    template="pages/app/login.html",
    layout="layouts/minimal.html",
)


async def handler(request: Request):
    """Login page handler

    Simple login page with SSO options

    Args:
        request: The incoming request

    Returns:
        HTMLResponse with full layout or just content for HTMX
    """
    return page.render(request, {})
