from fastapi import FastAPI, Request, APIRouter
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.exceptions import HTTPException
from starlette import status
from contextlib import asynccontextmanager
from pathlib import Path
import asyncio
from sse_starlette.sse import EventSourceResponse
from starlette.background import BackgroundTask
from watchfiles import awatch

from fastapi.staticfiles import StaticFiles
from src.state import AppState
from .pages import router as pages_router
from .api import router as api_router
from .auth import router as auth_router
from .health import router as health_router


def create_app(app_state: AppState) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await app_state.startup()
        yield
        await app_state.shutdown()

    app = FastAPI(lifespan=lifespan)

    # Store app_state on the app instance
    app.state.app_state = app_state

    async def state_middleware(request: Request, call_next):
        # Set individual attributes on request.state
        request.state.app_state = app.state.app_state
        return await call_next(request)

    async def logger_middleware(request: Request, call_next):
        request.state.logger = app.state.app_state.logger.with_request(request)
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            request.state.logger.error(str(e))
            raise

    async def db_middleware(request: Request, call_next):
        async with app.state.app_state.database.session() as session:
            request.state.db = session
            try:
                response = await call_next(request)
                return response
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    # Exception handler using the correct decorator syntax
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        print(
            f"Exception handler called: {exc.status_code} - {request.url.path}"
        )  # Debug
        # Redirect unauthorized users to login for protected pages
        if exc.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]:
            # Don't redirect if already on login page
            if not request.url.path.startswith("/app/login"):
                return RedirectResponse(
                    url="/app/login", status_code=status.HTTP_302_FOUND
                )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    # Add middleware
    app.middleware("http")(state_middleware)
    app.middleware("http")(logger_middleware)
    app.middleware("http")(db_middleware)

    # Hot reloading implementation
    if app_state.config.dev_mode:
        dev_router = APIRouter()

        @dev_router.get("/dev/hot-reload")
        async def hot_reload():
            """
            Endpoint for server-sent events that notify the client when files change.
            The client should connect to this endpoint and reload when events are received.
            """

            async def event_generator():
                # Watch templates, src, and static directories
                watch_dirs = [Path("templates"), Path("src"), Path("static")]
                try:
                    # Create a watcher for multiple directories
                    watcher = awatch(*watch_dirs)
                    print(
                        "✓ Hot reload watcher started for templates, src, and static directories"
                    )

                    # Send initial event to confirm connection
                    yield {"event": "connected", "data": "Hot reload connected"}

                    # Monitor for file changes
                    async for changes in watcher:
                        if changes:
                            # Log what changed
                            for change_type, path in changes:
                                print(f"Hot reload: {change_type} {path}")

                            # Send reload event to client
                            yield {"event": "reload", "data": "reload"}
                except asyncio.CancelledError:
                    print("Hot reload event generator cancelled")
                    raise
                finally:
                    print("Hot reload event generator cleanup")

            return EventSourceResponse(
                event_generator(),
                background=BackgroundTask(
                    lambda: print("Hot reload connection closed")
                ),
            )

        # Include the hot reload router
        app.include_router(dev_router)

    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Include the HTML router
    app.include_router(pages_router)
    app.include_router(api_router, prefix="/api")
    app.include_router(auth_router, prefix="/auth")
    app.include_router(health_router, prefix="/_status")

    # TODO: should use the status router instead
    # NOTE (amiller68): for kamal connectivity check out of the box
    @app.get("/up")
    async def up():
        return {"status": "ok"}

    return app


# This instance is used by uvicorn
app = None
