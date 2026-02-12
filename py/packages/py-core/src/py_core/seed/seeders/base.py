"""Base classes for seeders."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from py_core.observability import Logger


@dataclass
class SeederContext:
    """Shared context for all seeders."""

    db: AsyncSession
    logger: Logger


@dataclass
class SeederResult:
    """Result of a seeding operation."""

    created: int = 0
    skipped: int = 0  # Already existed (idempotent)
    errors: list[str] = field(default_factory=list)


ConfigT = TypeVar("ConfigT")


class Seeder(ABC, Generic[ConfigT]):
    """Abstract base class for seeders."""

    name: str  # Human-readable name for logging

    @abstractmethod
    async def seed(
        self,
        items: list[ConfigT],
        ctx: SeederContext,
    ) -> SeederResult:
        """
        Seed items to the database.

        Must be idempotent - running multiple times should not duplicate data.
        """
        pass
