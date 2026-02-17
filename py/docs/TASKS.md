# Background Tasks

This guide covers TaskIQ background jobs and scheduled tasks.

## Overview

- **Task Queue**: TaskIQ with Redis broker
- **Scheduling**: Cron-based with distributed locking
- **Run Tracking**: Database records for observability
- **Location**: `py/apps/py-app/src/tasks/`

---

## Quick Reference

```bash
# Run the worker (processes background tasks)
taskiq worker src.tasks:broker

# Run the scheduler (triggers cron tasks)
taskiq scheduler src.tasks.scheduler:scheduler

# In development, both run via `make dev`
```

---

## Architecture

```
src/tasks/
├── __init__.py      # Broker configuration
├── scheduler.py     # Scheduler configuration
├── cron.py          # @cron decorator with distributed locking
├── deps.py          # TaskiqDepends helpers (db, logger, redis)
└── jobs/            # Task implementations
    ├── __init__.py
    ├── cleanup_expired_data.py
    └── ...
```

---

## Creating Tasks

### Simple One-Off Task

Use `@broker.task` for tasks triggered programmatically:

```python
from src.tasks import broker
from src.tasks.deps import get_db_session, get_logger
from sqlalchemy.ext.asyncio import AsyncSession
from py_core.observability import Logger
from taskiq import TaskiqDepends

@broker.task
async def process_upload(
    upload_id: str,
    db: AsyncSession = TaskiqDepends(get_db_session),
    logger: Logger = TaskiqDepends(get_logger),
) -> dict:
    """Process an uploaded file."""
    logger.info(f"Processing upload: {upload_id}")
    # ... do work ...
    return {"processed": upload_id}
```

**Calling from application code:**

```python
# Fire and forget
await process_upload.kiq(upload_id="abc123")

# Wait for result
task = await process_upload.kiq(upload_id="abc123")
result = await task.wait_result()
```

### Scheduled Cron Task

Use `@cron` for periodic tasks with distributed locking:

```python
from src.tasks.cron import cron
from src.tasks.deps import get_db_session, get_logger
from sqlalchemy.ext.asyncio import AsyncSession
from py_core.observability import Logger
from taskiq import TaskiqDepends

@cron("*/5 * * * *", lock_ttl=120)
async def cleanup_expired_data(
    db: AsyncSession = TaskiqDepends(get_db_session),
    logger: Logger = TaskiqDepends(get_logger),
) -> dict:
    """Clean up expired records every 5 minutes."""
    # ... cleanup logic ...
    return {"deleted_count": 42}
```

**Cron expression format:** `minute hour day month weekday`

| Expression | Meaning |
|------------|---------|
| `* * * * *` | Every minute |
| `*/5 * * * *` | Every 5 minutes |
| `0 * * * *` | Every hour |
| `0 0 * * *` | Daily at midnight |
| `0 0 * * 0` | Weekly on Sunday |

---

## The @cron Decorator

The `@cron` decorator provides:

1. **Distributed locking** — Only one instance runs at a time (across workers)
2. **Run tracking** — Every run is recorded in `cron_job_runs` table
3. **Automatic cleanup** — Lock released even on failure

```python
@cron("*/5 * * * *", lock_ttl=120)
async def my_periodic_task(...) -> dict:
    ...
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `expression` | `str` | Cron schedule expression |
| `lock_ttl` | `int` | Lock timeout in seconds (default: 300) |

**Lock TTL Guidelines:**
- Set to 2-3x your expected task duration
- If task takes 30s, use `lock_ttl=90`
- If task might take 2 minutes, use `lock_ttl=300`

### Run Tracking

Every cron job run is recorded in the `cron_job_runs` table:

| Column | Description |
|--------|-------------|
| `job_name` | Task function name |
| `status` | RUNNING, COMPLETED, FAILED, SKIPPED |
| `started_at` | When the run started |
| `completed_at` | When the run finished |
| `duration_ms` | Run duration in milliseconds |
| `result` | JSON result (on success) |
| `error` | Error message (on failure) |

**Skipped runs:** When a task can't acquire the lock (another instance is running), it records a SKIPPED status and returns immediately.

---

## Task Dependencies

Use `TaskiqDepends` to inject dependencies into tasks:

```python
from taskiq import TaskiqDepends
from src.tasks.deps import (
    get_db_session,      # AsyncSession
    get_logger,          # Logger
    get_redis,           # Redis client
    get_event_publisher, # EventPublisher for real-time events
    get_session_factory, # For multiple concurrent sessions
)

@broker.task
async def my_task(
    param: str,
    db: AsyncSession = TaskiqDepends(get_db_session),
    logger: Logger = TaskiqDepends(get_logger),
    events: EventPublisher = TaskiqDepends(get_event_publisher),
) -> dict:
    logger.info(f"Processing: {param}")
    await events.publish(user_id, SomeEvent(...))
    return {"result": param}
```

### Available Dependencies

| Dependency | Type | Use Case |
|------------|------|----------|
| `get_db_session` | `AsyncSession` | Database operations |
| `get_logger` | `Logger` | Structured logging |
| `get_redis` | `Redis` | Direct Redis access |
| `get_event_publisher` | `EventPublisher` | Real-time events to clients |
| `get_session_factory` | `Callable` | Multiple concurrent sessions |

### Session Factory for Parallel Operations

When you need multiple concurrent database sessions (e.g., parallel tool calls):

```python
from src.tasks.deps import get_session_factory

@broker.task
async def parallel_task(
    session_factory = TaskiqDepends(get_session_factory),
) -> dict:
    async with session_factory() as session1, session_factory() as session2:
        # Run concurrent operations
        result1, result2 = await asyncio.gather(
            operation1(session1),
            operation2(session2),
        )
    return {"results": [result1, result2]}
```

---

## Running Workers

### Development

`make dev` starts all services including workers and scheduler.

### Production (Docker Compose)

```yaml
# docker-compose.yml
services:
  worker:
    command: taskiq worker src.tasks:broker --workers 2
    depends_on:
      - redis
      - postgres

  scheduler:
    command: taskiq scheduler src.tasks.scheduler:scheduler
    depends_on:
      - redis
```

### Production (Kamal)

Workers and scheduler are configured in `config/deploy/py.yml` as accessories.

---

## Best Practices

### Task Design

1. **Make tasks idempotent** — Safe to retry on failure
2. **Keep tasks focused** — One task, one responsibility
3. **Use appropriate lock TTL** — 2-3x expected duration
4. **Return structured results** — Always return a dict for observability

### Error Handling

```python
@broker.task
async def risky_task(
    item_id: str,
    logger: Logger = TaskiqDepends(get_logger),
) -> dict:
    try:
        result = await do_work(item_id)
        return {"success": True, "result": result}
    except SpecificError as e:
        logger.warning(f"Expected error for {item_id}: {e}")
        return {"success": False, "error": str(e)}
    # Let unexpected errors propagate for retry/alerting
```

### Logging

Always log task start/end for observability:

```python
@cron("0 * * * *", lock_ttl=300)
async def hourly_sync(
    logger: Logger = TaskiqDepends(get_logger),
) -> dict:
    logger.info("Starting hourly sync")
    count = await do_sync()
    logger.info(f"Completed hourly sync: {count} items")
    return {"synced": count}
```

---

## Troubleshooting

### Task Not Running

1. **Check worker is running:** `taskiq worker src.tasks:broker`
2. **Check scheduler is running:** `taskiq scheduler src.tasks.scheduler:scheduler`
3. **Check Redis connection:** Tasks queue through Redis

### Cron Task Skipped

If a cron task shows SKIPPED status, another instance is holding the lock:
- Check if a previous run is stuck
- Verify lock TTL is appropriate
- Check for multiple scheduler instances

### Task Fails Silently

Ensure task is registered by importing in `src/tasks/jobs/__init__.py`:

```python
# src/tasks/jobs/__init__.py
from .my_new_task import my_new_task  # Must import to register
```
