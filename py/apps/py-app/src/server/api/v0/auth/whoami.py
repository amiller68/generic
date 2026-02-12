from fastapi import Request, Depends

from py_core.database.models import User
from py_core.observability import Logger
from src.server.deps import require_logged_in_user, logger
from src.server.handlers.component import ComponentResponseHandler

# Handler instance - only returns components, never full pages
responder = ComponentResponseHandler(
    component_template_path="components/user.html",
)


async def handler(
    request: Request,
    user: User = Depends(require_logged_in_user),
    logger: Logger = Depends(logger),
):
    """Get current user information

    Requires authenticated user via session cookie
    Returns JSON or HTML based on request headers

    Args:
        request: The incoming request
        user: Current authenticated user (auto-injected via deps)
        logger: Request span for logging

    Returns:
        HTMLResponse or JSONResponse via DualResponseHandler
    """
    logger.info(f"whoami request from user: {user.email}")

    return await responder.respond(request, user.model())
