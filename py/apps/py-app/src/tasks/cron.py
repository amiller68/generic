"""
Declarative cron tasks with distributed locking and run tracking.

Usage:
    from src.tasks.cron import cron

    @cron("* * * * *", lock_ttl=120)
    async def my_periodic_task(
        db: AsyncSession = TaskiqDepends(get_db_session),
    ) -> dict:
        return {"result": "done"}
"""

import inspect
from dataclasses import dataclass
from typing import Any, Callable

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import TaskiqDepends

from py_core.database.models.cron_job_run import CronJobRun, CronJobRunStatus
from py_core.database.utils import utcnow
from src.tasks.deps import get_db_session, get_redis

_cron_registry: dict[str, "CronConfig"] = {}


@dataclass
class CronConfig:
    expression: str
    lock_ttl: int
    task_name: str


class TaskLock:
    KEY_PREFIX = "taskiq:lock:"

    def __init__(self, redis: Redis):
        self._redis = redis

    async def acquire(self, name: str, ttl_seconds: int) -> bool:
        key = f"{self.KEY_PREFIX}{name}"
        result = await self._redis.set(key, "1", nx=True, ex=ttl_seconds)
        return result is not None

    async def release(self, name: str) -> None:
        key = f"{self.KEY_PREFIX}{name}"
        await self._redis.delete(key)


async def _record_run_start(db: AsyncSession, job_name: str) -> str:
    run = CronJobRun(
        job_name=job_name,
        status=CronJobRunStatus.RUNNING,
        started_at=utcnow(),
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return str(run.id)


async def _record_run_complete(
    db: AsyncSession,
    run_id: str,
    status: CronJobRunStatus,
    result: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    stmt = select(CronJobRun).where(CronJobRun.id == run_id)
    run = (await db.execute(stmt)).scalar_one_or_none()
    if run:
        run.status = status
        completed_at = utcnow()
        run.completed_at = completed_at
        if run.started_at:
            run.duration_ms = int((completed_at - run.started_at).total_seconds() * 1000)
        run.result = result
        run.error = error
        await db.commit()


def cron(expression: str, lock_ttl: int = 300) -> Callable[..., Any]:
    def decorator(func: Any) -> Any:
        task_name = func.__name__

        _cron_registry[task_name] = CronConfig(
            expression=expression,
            lock_ttl=lock_ttl,
            task_name=task_name,
        )

        async def wrapper(
            *args: Any,
            _cron_redis: Redis = TaskiqDepends(get_redis),
            _cron_db: AsyncSession = TaskiqDepends(get_db_session),
            **kwargs: Any,
        ) -> dict[str, Any]:
            lock = TaskLock(_cron_redis)

            if not await lock.acquire(task_name, lock_ttl):
                run_id = await _record_run_start(_cron_db, task_name)
                await _record_run_complete(_cron_db, run_id, CronJobRunStatus.SKIPPED)
                return {"skipped": True, "reason": "lock_held"}

            run_id = await _record_run_start(_cron_db, task_name)

            try:
                result = await func(*args, **kwargs)
                result_dict = result if isinstance(result, dict) else {"result": result}
                await _record_run_complete(
                    _cron_db, run_id, CronJobRunStatus.COMPLETED, result=result_dict
                )
                return result_dict
            except Exception as e:
                await _record_run_complete(
                    _cron_db, run_id, CronJobRunStatus.FAILED, error=str(e)
                )
                raise
            finally:
                await lock.release(task_name)

        orig_sig = inspect.signature(func)
        wrapper_sig = inspect.signature(wrapper)
        cron_params = {
            k: v for k, v in wrapper_sig.parameters.items() if k.startswith("_cron_")
        }
        combined_params = list(orig_sig.parameters.values()) + list(
            cron_params.values()
        )
        wrapper.__signature__ = orig_sig.replace(parameters=combined_params)  # type: ignore[attr-defined]
        wrapper.__name__ = func.__name__
        wrapper.__qualname__ = func.__qualname__
        wrapper.__module__ = func.__module__

        from src.tasks import broker

        decorated_task = broker.task(schedule=[{"cron": expression}])(wrapper)
        return decorated_task

    return decorator


def get_cron_registry() -> dict[str, CronConfig]:
    return _cron_registry.copy()
