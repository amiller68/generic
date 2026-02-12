"""
Chat engine module.

Provides centralized thread lifecycle management:
- ThreadManager: In-memory thread state with append_message
- ChatEngine: Executes completions with streaming and cancellation
"""

from .runner import ChatEngine, EngineConfig, EngineContext, get_cancel_key
from .thread_manager import ThreadManager, serialize_message_history

__all__ = [
    # Thread
    "ThreadManager",
    "serialize_message_history",
    # Engine
    "ChatEngine",
    "EngineConfig",
    "EngineContext",
    "get_cancel_key",
]
