"""Widget seeder - seeds example widgets."""

from sqlalchemy.future import select

from py_core.database.models import Widget

from ..config import WidgetSeedConfig
from .base import Seeder, SeederContext, SeederResult


class WidgetSeeder(Seeder[WidgetSeedConfig]):
    """Seeds widgets with configurable status and priority."""

    name = "widgets"

    async def seed(
        self,
        items: list[WidgetSeedConfig],
        ctx: SeederContext,
    ) -> SeederResult:
        result = SeederResult()

        for widget_config in items:
            try:
                # Check if widget exists by name
                existing_result = await ctx.db.execute(
                    select(Widget).filter_by(name=widget_config.name)
                )
                existing = existing_result.scalars().first()

                if existing:
                    # Track if we made any updates
                    updated = False

                    # Update description if different
                    if existing.description != widget_config.description:
                        existing.description = widget_config.description
                        updated = True

                    # Update status if different
                    if existing.status != widget_config.status.value:
                        existing.status = widget_config.status.value
                        updated = True

                    # Update priority if different
                    if existing.priority != widget_config.priority:
                        existing.priority = widget_config.priority
                        updated = True

                    # Update is_public if different
                    if existing.is_public != widget_config.is_public:
                        existing.is_public = widget_config.is_public
                        updated = True

                    if updated:
                        await ctx.db.flush()
                        ctx.logger.info(f"Updated widget: {widget_config.name}")
                        result.created += 1
                    else:
                        ctx.logger.info(f"Widget {widget_config.name} already exists")
                        result.skipped += 1
                else:
                    # Create new widget
                    await Widget.create(
                        name=widget_config.name,
                        description=widget_config.description,
                        status=widget_config.status,
                        priority=widget_config.priority,
                        is_public=widget_config.is_public,
                        session=ctx.db,
                        logger=ctx.logger,
                    )
                    ctx.logger.info(
                        f"Created widget: {widget_config.name} "
                        f"(status={widget_config.status.value}, priority={widget_config.priority})"
                    )
                    result.created += 1

            except Exception as e:
                ctx.logger.error(f"Failed to seed widget {widget_config.name}: {e}")
                result.errors.append(f"{widget_config.name}: {str(e)}")

        return result
