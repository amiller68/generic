"""
Complete thread task.

Thin wrapper around ChatEngine for background task execution.
"""

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import TaskiqDepends

from py_core.ai_ml.chat.engine import ChatEngine, EngineConfig, EngineContext
from py_core.events import EventPublisher
from py_core.observability import Logger

from src.agents import get_admin_chat_agent_spec
from src.tasks import broker
from src.tasks.deps import get_db_session, get_event_publisher, get_logger, get_redis


@broker.task
async def complete_thread_task(
    user_id: str,
    completion_id: str,
    db: AsyncSession = TaskiqDepends(get_db_session),
    logger: Logger = TaskiqDepends(get_logger),
    events: EventPublisher = TaskiqDepends(get_event_publisher),
    redis: Redis = TaskiqDepends(get_redis),
) -> dict:
    """
    Complete a thread by running LLM on the message history.

    Args:
        user_id: User to publish events to
        completion_id: Completion record to process

    Events published:
        - ThreadStreamEvent for each chunk
        - ThreadStreamEvent with done=True when complete
        - ThreadCancelledEvent if cancelled by user
        - ThreadFailedEvent on error
    """
    config = EngineConfig(agent_spec=get_admin_chat_agent_spec())
    ctx = EngineContext(
        db=db,
        logger=logger,
        events=events,
        redis=redis,
        user_id=user_id,
        completion_id=completion_id,
    )

    engine = ChatEngine(config=config, ctx=ctx)
    return await engine.run()
