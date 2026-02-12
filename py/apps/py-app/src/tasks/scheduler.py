"""
TaskIQ scheduler for periodic tasks.

Run with:
    taskiq scheduler src.tasks.scheduler:scheduler
"""

from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource

from src.tasks import broker

scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)
