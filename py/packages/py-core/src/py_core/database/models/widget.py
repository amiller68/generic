"""Widget model - example entity for CRUD operations."""

import uuid
from enum import Enum

from pydantic import BaseModel
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from py_core.observability.logger import Logger

from ..client import Base, DatabaseException
from ..utils import utcnow


class WidgetStatus(str, Enum):
    """Widget status types."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class WidgetModel(BaseModel):
    """Pydantic model for Widget serialization."""

    id: str
    name: str
    description: str | None = None
    status: WidgetStatus = WidgetStatus.DRAFT
    priority: int = 0
    owner_id: str | None = None
    is_public: bool = False


class Widget(Base):
    """Example entity with full CRUD operations."""

    __tablename__ = "widgets"

    # Unique identifier
    id = Column(
        String, primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Basic fields
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default=WidgetStatus.DRAFT.value)
    priority = Column(Integer, nullable=False, default=0)

    # Ownership (optional FK to users)
    owner_id = Column(String, ForeignKey("users.id"), nullable=True)

    # Visibility
    is_public = Column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), default=utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=utcnow, onupdate=utcnow)

    def model(self) -> WidgetModel:
        """Convert to Pydantic model."""
        return WidgetModel(
            id=str(self.id),
            name=str(self.name),
            description=str(self.description) if self.description else None,
            status=WidgetStatus(self.status),
            priority=int(str(self.priority)) if self.priority else 0,
            owner_id=str(self.owner_id) if self.owner_id else None,
            is_public=bool(self.is_public),
        )

    # ==================== CREATE ====================

    @staticmethod
    async def create(
        name: str,
        session: AsyncSession,
        description: str | None = None,
        status: WidgetStatus = WidgetStatus.DRAFT,
        priority: int = 0,
        owner_id: str | None = None,
        is_public: bool = False,
        logger: Logger | None = None,
    ) -> "Widget":
        """Create a new widget."""
        try:
            widget = Widget(
                name=name,
                description=description,
                status=status.value,
                priority=priority,
                owner_id=owner_id,
                is_public=is_public,
            )
            session.add(widget)
            await session.flush()
            return widget
        except Exception as e:
            if logger:
                logger.error(e)
            raise DatabaseException.from_sqlalchemy_error(e)

    # ==================== READ ====================

    @staticmethod
    async def read(
        id: str, session: AsyncSession, logger: Logger | None = None
    ) -> "Widget | None":
        """Read a widget by ID."""
        try:
            result = await session.execute(select(Widget).filter_by(id=id))
            return result.scalars().first()
        except Exception as e:
            if logger:
                logger.error(e)
            raise DatabaseException.from_sqlalchemy_error(e)

    @staticmethod
    async def list_all(
        session: AsyncSession,
        offset: int = 0,
        limit: int = 50,
        status: WidgetStatus | None = None,
        owner_id: str | None = None,
        search: str | None = None,
        logger: Logger | None = None,
    ) -> list["Widget"]:
        """List widgets with optional filters."""
        try:
            query = select(Widget)
            if status:
                query = query.filter(Widget.status == status.value)
            if owner_id:
                query = query.filter(Widget.owner_id == owner_id)
            if search:
                query = query.filter(Widget.name.ilike(f"%{search}%"))
            query = query.offset(offset).limit(limit).order_by(Widget.created_at.desc())
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            if logger:
                logger.error(e)
            raise DatabaseException.from_sqlalchemy_error(e)

    @staticmethod
    async def list_by_owner(
        owner_id: str,
        session: AsyncSession,
        offset: int = 0,
        limit: int = 50,
        logger: Logger | None = None,
    ) -> list["Widget"]:
        """List widgets owned by a specific user."""
        try:
            query = (
                select(Widget)
                .filter_by(owner_id=owner_id)
                .offset(offset)
                .limit(limit)
                .order_by(Widget.created_at.desc())
            )
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            if logger:
                logger.error(e)
            raise DatabaseException.from_sqlalchemy_error(e)

    @staticmethod
    async def count_all(
        session: AsyncSession,
        status: WidgetStatus | None = None,
        owner_id: str | None = None,
        search: str | None = None,
        logger: Logger | None = None,
    ) -> int:
        """Count widgets with optional filters."""
        try:
            query = select(func.count(Widget.id))
            if status:
                query = query.filter(Widget.status == status.value)
            if owner_id:
                query = query.filter(Widget.owner_id == owner_id)
            if search:
                query = query.filter(Widget.name.ilike(f"%{search}%"))
            result = await session.execute(query)
            return result.scalar() or 0
        except Exception as e:
            if logger:
                logger.error(e)
            raise DatabaseException.from_sqlalchemy_error(e)

    # ==================== UPDATE ====================

    async def update(
        self,
        session: AsyncSession,
        name: str | None = None,
        description: str | None = None,
        status: WidgetStatus | None = None,
        priority: int | None = None,
        is_public: bool | None = None,
        logger: Logger | None = None,
    ) -> None:
        """Update widget fields."""
        try:
            if name is not None:
                self.name = name
            if description is not None:
                self.description = description
            if status is not None:
                self.status = status.value
            if priority is not None:
                self.priority = priority
            if is_public is not None:
                self.is_public = is_public
            await session.flush()
        except Exception as e:
            if logger:
                logger.error(e)
            raise DatabaseException.from_sqlalchemy_error(e)

    async def set_status(
        self,
        status: WidgetStatus,
        session: AsyncSession,
        logger: Logger | None = None,
    ) -> None:
        """Update widget status."""
        try:
            self.status = status.value
            await session.flush()
        except Exception as e:
            if logger:
                logger.error(e)
            raise DatabaseException.from_sqlalchemy_error(e)

    async def set_owner(
        self,
        owner_id: str | None,
        session: AsyncSession,
        logger: Logger | None = None,
    ) -> None:
        """Assign or remove widget owner."""
        try:
            self.owner_id = owner_id
            await session.flush()
        except Exception as e:
            if logger:
                logger.error(e)
            raise DatabaseException.from_sqlalchemy_error(e)

    # ==================== DELETE ====================

    async def delete(
        self,
        session: AsyncSession,
        logger: Logger | None = None,
    ) -> None:
        """Delete the widget."""
        try:
            await session.delete(self)
            await session.flush()
        except Exception as e:
            if logger:
                logger.error(e)
            raise DatabaseException.from_sqlalchemy_error(e)

    @staticmethod
    async def delete_by_id(
        id: str,
        session: AsyncSession,
        logger: Logger | None = None,
    ) -> bool:
        """Delete a widget by ID. Returns True if deleted, False if not found."""
        try:
            widget = await Widget.read(id=id, session=session, logger=logger)
            if widget:
                await session.delete(widget)
                await session.flush()
                return True
            return False
        except Exception as e:
            if logger:
                logger.error(e)
            raise DatabaseException.from_sqlalchemy_error(e)
