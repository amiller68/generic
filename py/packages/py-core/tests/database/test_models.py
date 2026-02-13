"""Tests for database models."""

from py_core.database.models import (
    User,
    UserRole,
    Widget,
    WidgetStatus,
    CronJobRunStatus,
    AsyncToolExecutionStatus,
    AsyncToolExecutionErrorType,
)


class TestUserModel:
    """Tests for User model."""

    def test_user_role_enum_values(self) -> None:
        """UserRole enum has expected values."""
        assert UserRole.ADMIN.value == "admin"

    def test_user_model_conversion(self) -> None:
        """User.model() creates UserModel with correct fields."""
        user = User(
            id="test-id",
            email="test@example.com",
            role=UserRole.ADMIN,
            approved=True,
        )
        model = user.model()

        assert model.id == "test-id"
        assert model.email == "test@example.com"
        assert model.role == UserRole.ADMIN
        assert model.approved is True

    def test_user_model_conversion_no_role(self) -> None:
        """User.model() handles None role."""
        user = User(
            id="test-id",
            email="test@example.com",
            role=None,
            approved=False,
        )
        model = user.model()

        assert model.role is None
        assert model.approved is False


class TestWidgetModel:
    """Tests for Widget model."""

    def test_widget_status_enum_values(self) -> None:
        """WidgetStatus enum has expected values."""
        assert WidgetStatus.DRAFT.value == "draft"
        assert WidgetStatus.ACTIVE.value == "active"
        assert WidgetStatus.ARCHIVED.value == "archived"

    def test_widget_model_conversion(self) -> None:
        """Widget.model() creates WidgetModel with correct fields."""
        widget = Widget(
            id="widget-id",
            name="Test Widget",
            description="A test widget",
            status=WidgetStatus.ACTIVE,
            priority=5,
            owner_id="user-id",
            is_public=True,
        )
        model = widget.model()

        assert model.id == "widget-id"
        assert model.name == "Test Widget"
        assert model.description == "A test widget"
        assert model.status == WidgetStatus.ACTIVE
        assert model.priority == 5
        assert model.owner_id == "user-id"
        assert model.is_public is True


class TestCronJobRunModel:
    """Tests for CronJobRun model."""

    def test_cron_job_run_status_enum_values(self) -> None:
        """CronJobRunStatus enum has expected values."""
        assert CronJobRunStatus.RUNNING.value == "running"
        assert CronJobRunStatus.COMPLETED.value == "completed"
        assert CronJobRunStatus.FAILED.value == "failed"
        assert CronJobRunStatus.SKIPPED.value == "skipped"


class TestAsyncToolExecutionModel:
    """Tests for AsyncToolExecution model."""

    def test_async_tool_execution_status_enum_values(self) -> None:
        """AsyncToolExecutionStatus enum has expected values."""
        assert AsyncToolExecutionStatus.PENDING.value == "pending"
        assert AsyncToolExecutionStatus.COMPLETED.value == "completed"
        assert AsyncToolExecutionStatus.FAILED.value == "failed"

    def test_async_tool_execution_error_type_enum_values(self) -> None:
        """AsyncToolExecutionErrorType enum has expected values."""
        assert AsyncToolExecutionErrorType.TIMEOUT.value == "timeout"
        assert AsyncToolExecutionErrorType.INTERNAL_ERROR.value == "internal_error"
        assert AsyncToolExecutionErrorType.VALIDATION_ERROR.value == "validation_error"
        assert AsyncToolExecutionErrorType.NOT_FOUND.value == "not_found"
