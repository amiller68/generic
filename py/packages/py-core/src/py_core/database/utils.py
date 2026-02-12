from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy import TypeDecorator
from sqlalchemy.dialects.postgresql import VARCHAR
from uuid_utils import uuid7


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def uuid7_str() -> str:
    """Generate a time-sortable UUID7 string."""
    return str(uuid7())


class StringEnum(TypeDecorator):
    """
    SQLAlchemy type for storing Python enums as PostgreSQL strings.

    Maps enum values to their string representation in the database,
    allowing direct enum usage in queries without .value:

        model.status = MyStatus.PENDING  # Correct
        query.filter(Model.status == MyStatus.ACTIVE)  # Correct

    Usage:
        class MyModel(Base):
            status: Mapped[MyStatus] = mapped_column(
                PgEnum(MyStatus), default=MyStatus.PENDING
            )
    """

    impl = VARCHAR
    cache_ok = True

    def __init__(self, enum_class: type[Enum], *args: Any, **kwargs: Any) -> None:
        self.enum_class = enum_class
        super().__init__(*args, **kwargs)

    def process_bind_param(self, value: Enum | str | None, dialect: Any) -> str | None:
        """Convert enum to string for database storage."""
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            return value.value
        return value

    def process_result_value(self, value: str | None, dialect: Any) -> Enum | None:
        """Convert string from database to enum."""
        if value is None:
            return None
        return self.enum_class(value)
