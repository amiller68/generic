"""Seed runner - orchestrates seeders."""

from dataclasses import dataclass, field
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from py_core.observability import Logger

from .config import SeedConfig
from .seeders.base import SeederContext, SeederResult
from .seeders.users import UserSeeder
from .seeders.widgets import WidgetSeeder


@dataclass
class SeedResult:
    """Combined result from all seeders."""

    users: SeederResult = field(default_factory=SeederResult)
    widgets: SeederResult = field(default_factory=SeederResult)

    @property
    def total_created(self) -> int:
        return self.users.created + self.widgets.created

    @property
    def total_skipped(self) -> int:
        return self.users.skipped + self.widgets.skipped

    @property
    def total_errors(self) -> int:
        return len(self.users.errors) + len(self.widgets.errors)

    @property
    def success(self) -> bool:
        return self.total_errors == 0


SeedTarget = Literal["all", "users", "widgets"]


async def seed_database(
    config: SeedConfig,
    db: AsyncSession,
    logger: Logger,
    target: SeedTarget = "all",
) -> SeedResult:
    """
    Seed the database with configured data.

    Args:
        config: Seed configuration
        db: Database session
        logger: Logger instance
        target: What to seed - "all", "users", or "widgets"

    Returns:
        SeedResult with counts and any errors
    """
    ctx = SeederContext(db=db, logger=logger)

    users_result = SeederResult()
    widgets_result = SeederResult()

    # Seed users first (widgets may reference users)
    if target in ("all", "users") and config.users:
        logger.info(f"Seeding {len(config.users)} users...")
        user_seeder = UserSeeder()
        users_result = await user_seeder.seed(config.users, ctx)
        logger.info(
            f"Users: {users_result.created} created, "
            f"{users_result.skipped} skipped, "
            f"{len(users_result.errors)} errors"
        )

    # Seed widgets
    if target in ("all", "widgets") and config.widgets:
        logger.info(f"Seeding {len(config.widgets)} widgets...")
        widget_seeder = WidgetSeeder()
        widgets_result = await widget_seeder.seed(config.widgets, ctx)
        logger.info(
            f"Widgets: {widgets_result.created} created, "
            f"{widgets_result.skipped} skipped, "
            f"{len(widgets_result.errors)} errors"
        )

    return SeedResult(users=users_result, widgets=widgets_result)
