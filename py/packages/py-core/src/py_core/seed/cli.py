"""CLI entry point for database seeding."""

import argparse
import asyncio
import os
import sys

from py_core.database import AsyncDatabase
from py_core.observability import Logger

from .config import SeedConfig
from .runner import seed_database, SeedTarget


async def main(target: SeedTarget, dry_run: bool = False) -> int:
    """Run database seeding."""
    logger = Logger()

    # Load configuration
    config = SeedConfig.load()

    if dry_run:
        logger.info("Dry run - showing what would be seeded:")
        logger.info(f"  Users: {len(config.users)}")
        for u in config.users:
            logger.info(f"    - {u.email} (role: {u.role})")
        logger.info(f"  Widgets: {len(config.widgets)}")
        for w in config.widgets:
            logger.info(f"    - {w.name} (status: {w.status.value})")
        return 0

    # Initialize database
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        logger.error("POSTGRES_URL environment variable is required")
        return 1

    # Normalize URL for asyncpg
    if not postgres_url.startswith("postgresql+asyncpg://"):
        postgres_url = postgres_url.replace("postgresql://", "postgresql+asyncpg://")
        postgres_url = postgres_url.replace("postgres://", "postgresql+asyncpg://")

    database = AsyncDatabase(postgres_url)
    await database.initialize()

    # Run seeding
    async with database.session() as session:
        result = await seed_database(
            config=config,
            db=session,
            logger=logger,
            target=target,
        )
        await session.commit()

    # Report results
    logger.info("=" * 40)
    logger.info(f"Total created: {result.total_created}")
    logger.info(f"Total skipped: {result.total_skipped}")

    if result.total_errors > 0:
        logger.error(f"Total errors: {result.total_errors}")
        for err in result.users.errors:
            logger.error(f"  - User: {err}")
        for err in result.widgets.errors:
            logger.error(f"  - Widget: {err}")
        return 1

    return 0


def cli() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Seed the database")
    parser.add_argument(
        "--target",
        choices=["all", "users", "widgets"],
        default="all",
        help="What to seed",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be seeded without making changes",
    )

    args = parser.parse_args()

    exit_code = asyncio.run(main(args.target, args.dry_run))
    sys.exit(exit_code)


if __name__ == "__main__":
    cli()
