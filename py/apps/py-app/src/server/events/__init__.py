"""Server-Sent Events for real-time updates.

This module provides SSE endpoints that HTMX can subscribe to for live updates.
Uses the hx-ext="sse" extension with hx-sse="connect:/path swap:event-name".

Example usage in templates:
    <div hx-ext="sse"
         hx-sse="connect:/_events/widgets swap:widget-updated">
        <!-- Content will be swapped when widget-updated event fires -->
    </div>
"""

from fastapi import APIRouter

from .widgets import router as widgets_router
from .chat import router as chat_router

router = APIRouter()
router.include_router(widgets_router, prefix="/widgets")
router.include_router(chat_router, prefix="/chat")
