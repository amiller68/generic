"""
Process a widget asynchronously.

This demonstrates the library pattern:
- Library function takes callbacks, does NOT publish events directly
- Caller (task layer) provides callbacks that publish events
"""

import asyncio
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from py_core.database.models import Widget, WidgetStatus
from py_core.observability import Logger


class OnProcessingStarted(Protocol):
    """Callback when processing starts."""

    async def __call__(self, widget_id: str, message: str) -> None: ...


class OnProcessingComplete(Protocol):
    """Callback when processing completes."""

    async def __call__(self, widget_id: str, new_status: str, message: str) -> None: ...


class OnProcessingFailed(Protocol):
    """Callback when processing fails."""

    async def __call__(self, widget_id: str, error: str) -> None: ...


@dataclass
class Context:
    """Dependencies for process_widget operation."""

    db: AsyncSession
    logger: Logger


@dataclass
class Params:
    """Parameters for process_widget operation."""

    widget_id: str
    on_started: OnProcessingStarted | None = None
    on_complete: OnProcessingComplete | None = None
    on_failed: OnProcessingFailed | None = None


@dataclass
class Result:
    """Result of process_widget operation."""

    widget_id: str
    name: str
    new_status: str
    success: bool


async def process_widget(params: Params, ctx: Context) -> Result:
    """
    Process a widget asynchronously.

    This demonstrates how library functions:
    - Take callbacks via Params, not publish events directly
    - Call callbacks at appropriate points
    - Let caller (task layer) decide what to do with notifications

    Args:
        params: Widget ID and optional callbacks
        ctx: Database session and logger

    Returns:
        Result with widget info and success status

    Raises:
        ValueError: If widget not found
    """
    widget = await Widget.read(id=params.widget_id, session=ctx.db, logger=ctx.logger)

    if not widget:
        ctx.logger.warn(f"Widget {params.widget_id} not found")
        raise ValueError(f"Widget {params.widget_id} not found")

    ctx.logger.info(f"Processing widget: {widget.name}")

    # Notify caller that processing started
    if params.on_started is not None:
        await params.on_started(params.widget_id, "Processing started...")

    try:
        # Simulate processing work (2-4 seconds)
        # In a real app, this might be:
        # - Calling an external API
        # - Running ML inference
        # - Generating a report
        # - Processing files
        await asyncio.sleep(3)

        # Update status to active after processing
        await widget.set_status(WidgetStatus.ACTIVE, session=ctx.db, logger=ctx.logger)

        ctx.logger.info(f"Widget {widget.name} processed successfully")

        # Notify caller that processing completed
        if params.on_complete is not None:
            await params.on_complete(
                params.widget_id,
                WidgetStatus.ACTIVE.value,
                "Processing complete",
            )

        return Result(
            widget_id=params.widget_id,
            name=str(widget.name),
            new_status=WidgetStatus.ACTIVE.value,
            success=True,
        )

    except Exception as e:
        ctx.logger.error(f"Widget processing failed: {params.widget_id}, error={e}")

        # Notify caller that processing failed
        if params.on_failed is not None:
            await params.on_failed(params.widget_id, str(e))

        raise
