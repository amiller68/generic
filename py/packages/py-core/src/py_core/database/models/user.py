from datetime import datetime
from enum import Enum

from pydantic import BaseModel
from sqlalchemy import Boolean, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Mapped, mapped_column

from py_core.observability.logger import Logger

from ..client import Base, DatabaseException
from ..utils import utcnow, uuid7_str, StringEnum


class UserRole(str, Enum):
    """User role types."""

    ADMIN = "admin"


class UserModel(BaseModel):
    id: str
    email: str
    role: UserRole | None = None
    approved: bool = False


class User(Base):
    __tablename__ = "users"

    # Unique identifier (uuid7 for time-sortable IDs)
    id: Mapped[str] = mapped_column(primary_key=True, default=uuid7_str)

    # email
    email: Mapped[str] = mapped_column(unique=True)

    # role (optional - None means regular user)
    role: Mapped[UserRole | None] = mapped_column(StringEnum(UserRole), nullable=True)

    # approved status (new users start as not approved)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)

    # timestamps
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    def model(self) -> UserModel:
        return UserModel(
            id=str(self.id),
            email=str(self.email),
            role=self.role,
            approved=bool(self.approved),
        )

    @staticmethod
    async def create(
        email: str, session: AsyncSession, logger: Logger | None = None
    ) -> "User":
        try:
            user = User(email=email)
            session.add(user)
            await session.flush()
            return user
        except Exception as e:
            if logger:
                logger.error(e)
            raise DatabaseException.from_sqlalchemy_error(e)

    @staticmethod
    async def read(
        id: str, session: AsyncSession, logger: Logger | None = None
    ) -> "User | None":
        try:
            result = await session.execute(select(User).filter_by(id=id))
            return result.scalars().first()
        except Exception as e:
            if logger:
                logger.error(e)
            raise DatabaseException.from_sqlalchemy_error(e)

    @staticmethod
    async def read_by_email(
        email: str, session: AsyncSession, logger: Logger | None = None
    ) -> "User | None":
        try:
            result = await session.execute(select(User).filter_by(email=email))
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
        search: str | None = None,
        logger: Logger | None = None,
    ) -> list["User"]:
        """List all users with optional email search."""
        try:
            query = select(User)
            if search:
                query = query.filter(User.email.ilike(f"%{search}%"))
            query = query.offset(offset).limit(limit).order_by(User.created_at.desc())
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            if logger:
                logger.error(e)
            raise DatabaseException.from_sqlalchemy_error(e)

    @staticmethod
    async def count_all(
        session: AsyncSession,
        search: str | None = None,
        logger: Logger | None = None,
    ) -> int:
        """Count total users with optional search filter."""
        try:
            query = select(func.count(User.id))
            if search:
                query = query.filter(User.email.ilike(f"%{search}%"))
            result = await session.execute(query)
            return result.scalar() or 0
        except Exception as e:
            if logger:
                logger.error(e)
            raise DatabaseException.from_sqlalchemy_error(e)

    async def set_role(
        self,
        role: UserRole | None,
        session: AsyncSession,
        logger: Logger | None = None,
    ) -> None:
        """Update user role (promote/demote admin)."""
        try:
            self.role = role
            await session.flush()
        except Exception as e:
            if logger:
                logger.error(e)
            raise DatabaseException.from_sqlalchemy_error(e)

    async def set_approved(
        self,
        approved: bool,
        session: AsyncSession,
        logger: Logger | None = None,
    ) -> None:
        """Update user approval status."""
        try:
            self.approved = approved
            await session.flush()
        except Exception as e:
            if logger:
                logger.error(e)
            raise DatabaseException.from_sqlalchemy_error(e)
