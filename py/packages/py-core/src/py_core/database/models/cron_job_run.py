from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..client import Base
from ..utils import utcnow, uuid7_str, StringEnum


class CronJobRunStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class CronJobRun(Base):
    __tablename__ = "cron_job_runs"

    id: Mapped[str] = mapped_column(primary_key=True, default=uuid7_str)
    job_name: Mapped[str] = mapped_column(index=True)
    status: Mapped[CronJobRunStatus] = mapped_column(
        StringEnum(CronJobRunStatus), default=CronJobRunStatus.RUNNING
    )
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
