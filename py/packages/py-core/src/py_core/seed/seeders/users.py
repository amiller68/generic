"""User seeder - seeds users by email."""

from py_core.database.models import User

from ..config import UserSeedConfig
from .base import Seeder, SeederContext, SeederResult


class UserSeeder(Seeder[UserSeedConfig]):
    """Seeds users with optional admin role."""

    name = "users"

    async def seed(
        self,
        items: list[UserSeedConfig],
        ctx: SeederContext,
    ) -> SeederResult:
        result = SeederResult()

        for user_config in items:
            try:
                # Check if user exists by email
                existing = await User.read_by_email(
                    user_config.email,
                    ctx.db,
                    ctx.logger,
                )

                if existing:
                    # Track if we made any updates
                    updated = False

                    # Update role if needed (compare enums directly)
                    if existing.role != user_config.role:
                        existing.role = user_config.role
                        updated = True
                        ctx.logger.info(
                            f"Updated user {user_config.email} role to {user_config.role}"
                        )

                    # Update approved status if needed
                    if existing.approved != user_config.approved:
                        existing.approved = user_config.approved
                        updated = True
                        ctx.logger.info(
                            f"Updated user {user_config.email} approved to {user_config.approved}"
                        )

                    if updated:
                        await ctx.db.flush()
                        result.created += 1
                    else:
                        ctx.logger.info(f"User {user_config.email} already exists")
                        result.skipped += 1
                else:
                    # Create new user
                    user = await User.create(user_config.email, ctx.db, ctx.logger)
                    if user_config.role:
                        user.role = user_config.role
                    user.approved = user_config.approved
                    await ctx.db.flush()
                    ctx.logger.info(
                        f"Created user {user_config.email} "
                        f"with role {user_config.role}, approved={user_config.approved}"
                    )
                    result.created += 1

            except Exception as e:
                ctx.logger.error(f"Failed to seed user {user_config.email}: {e}")
                result.errors.append(f"{user_config.email}: {str(e)}")

        return result
