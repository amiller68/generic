"""Tests for database utilities."""

from enum import Enum

from py_core.database.utils import uuid7_str, StringEnum, utcnow


class TestUuid7Str:
    """Tests for uuid7_str function."""

    def test_generates_string(self) -> None:
        """uuid7_str returns a string."""
        result = uuid7_str()
        assert isinstance(result, str)

    def test_generates_valid_uuid_format(self) -> None:
        """uuid7_str returns valid UUID format."""
        result = uuid7_str()
        # UUID format: 8-4-4-4-12 hex chars
        parts = result.split("-")
        assert len(parts) == 5
        assert len(parts[0]) == 8
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4
        assert len(parts[3]) == 4
        assert len(parts[4]) == 12

    def test_generates_unique_values(self) -> None:
        """uuid7_str generates unique values."""
        ids = [uuid7_str() for _ in range(100)]
        assert len(set(ids)) == 100

    def test_time_sortable(self) -> None:
        """uuid7 IDs are time-sortable (later IDs sort after earlier ones)."""
        ids = [uuid7_str() for _ in range(10)]
        sorted_ids = sorted(ids)
        assert ids == sorted_ids


class TestStringEnum:
    """Tests for StringEnum SQLAlchemy type."""

    class TestStatus(str, Enum):
        ACTIVE = "active"
        INACTIVE = "inactive"
        PENDING = "pending"

    def test_process_bind_param_with_enum(self) -> None:
        """StringEnum converts enum to string value."""
        enum_type = StringEnum(self.TestStatus)
        result = enum_type.process_bind_param(self.TestStatus.ACTIVE, None)
        assert result == "active"

    def test_process_bind_param_with_string(self) -> None:
        """StringEnum passes through string values."""
        enum_type = StringEnum(self.TestStatus)
        result = enum_type.process_bind_param("active", None)
        assert result == "active"

    def test_process_bind_param_with_none(self) -> None:
        """StringEnum handles None values."""
        enum_type = StringEnum(self.TestStatus)
        result = enum_type.process_bind_param(None, None)
        assert result is None

    def test_process_result_value_converts_to_enum(self) -> None:
        """StringEnum converts string from DB to enum."""
        enum_type = StringEnum(self.TestStatus)
        result = enum_type.process_result_value("active", None)
        assert result == self.TestStatus.ACTIVE
        assert isinstance(result, self.TestStatus)

    def test_process_result_value_with_none(self) -> None:
        """StringEnum handles None from DB."""
        enum_type = StringEnum(self.TestStatus)
        result = enum_type.process_result_value(None, None)
        assert result is None


class TestUtcnow:
    """Tests for utcnow function."""

    def test_returns_datetime(self) -> None:
        """utcnow returns a datetime."""
        from datetime import datetime

        result = utcnow()
        assert isinstance(result, datetime)

    def test_is_naive(self) -> None:
        """utcnow returns naive datetime for TIMESTAMP WITHOUT TIME ZONE."""
        result = utcnow()
        assert result.tzinfo is None

    def test_is_utc_based(self) -> None:
        """utcnow returns current UTC time (but naive for DB storage)."""
        from datetime import datetime, timezone

        result = utcnow()
        utc_now = datetime.now(timezone.utc).replace(tzinfo=None)
        # Should be within 1 second of UTC now
        assert abs((result - utc_now).total_seconds()) < 1
