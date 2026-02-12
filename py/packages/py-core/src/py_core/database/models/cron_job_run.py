import uuid
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP

from ..client import Base
from ..utils import utcnow


class CronJobRunStatus(PyEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class CronJobRun(Base):
    __tablename__ = "cron_job_runs"

    id = Column(
        String, primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )
    job_name = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default=CronJobRunStatus.RUNNING.value)
    started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    result = Column(JSONB, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=utcnow)
