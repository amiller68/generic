"""init

Revision ID: 20260212_init
Revises:
Create Date: 2026-02-12

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260212_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types for native PostgreSQL enums
    message_role = postgresql.ENUM("user", "assistant", name="message_role", create_type=False)
    message_role.create(op.get_bind(), checkfirst=True)

    completion_status = postgresql.ENUM(
        "pending", "processing", "completed", "cancelled", "failed",
        name="completion_status", create_type=False
    )
    completion_status.create(op.get_bind(), checkfirst=True)

    completion_error_type = postgresql.ENUM(
        "api", "overloaded", "internal", "timeout",
        name="completion_error_type", create_type=False
    )
    completion_error_type.create(op.get_bind(), checkfirst=True)

    # Users table (base table - no dependencies)
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("approved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # Cron job runs table (no dependencies)
    op.create_table(
        "cron_job_runs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("job_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cron_job_runs_job_name", "cron_job_runs", ["job_name"])

    # Widgets table (depends on users)
    op.create_table(
        "widgets",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("owner_id", sa.String(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
    )
    op.create_index("ix_widgets_owner_id", "widgets", ["owner_id"])
    op.create_index("ix_widgets_status", "widgets", ["status"])

    # Threads table (depends on users)
    op.create_table(
        "threads",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_threads_user_id", "threads", ["user_id"])

    # Completions table (depends on threads, users)
    op.create_table(
        "completions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("thread_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending", "processing", "completed", "cancelled", "failed",
                name="completion_status", create_type=False
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("message_history", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("response", sa.Text(), nullable=True),
        sa.Column(
            "error_type",
            postgresql.ENUM(
                "api", "overloaded", "internal", "timeout",
                name="completion_error_type", create_type=False
            ),
            nullable=True,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_details", postgresql.JSONB(), nullable=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["thread_id"], ["threads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_completions_thread_id", "completions", ["thread_id"])
    op.create_index("ix_completions_user_id", "completions", ["user_id"])

    # Messages table (depends on threads, completions)
    op.create_table(
        "messages",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("thread_id", sa.String(), nullable=False),
        sa.Column("completion_id", sa.String(), nullable=True),
        sa.Column(
            "role",
            postgresql.ENUM("user", "assistant", name="message_role", create_type=False),
            nullable=False,
        ),
        sa.Column("parts", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["thread_id"], ["threads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["completion_id"], ["completions.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_messages_thread_id", "messages", ["thread_id"])
    op.create_index("ix_messages_completion_id", "messages", ["completion_id"])

    # Async tool executions table (depends on threads, completions)
    op.create_table(
        "async_tool_executions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("thread_id", sa.String(), nullable=False),
        sa.Column("completion_id", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), nullable=True),
        sa.Column("ref_type", sa.String(), nullable=True),
        sa.Column("ref_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("error_type", sa.String(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["thread_id"], ["threads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["completion_id"], ["completions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_async_tool_executions_thread_id", "async_tool_executions", ["thread_id"])
    op.create_index("ix_async_tool_executions_completion_id", "async_tool_executions", ["completion_id"])
    op.create_index("ix_async_tool_executions_ref_type", "async_tool_executions", ["ref_type"])
    op.create_index("ix_async_tool_executions_ref_id", "async_tool_executions", ["ref_id"])


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_index("ix_async_tool_executions_ref_id", "async_tool_executions")
    op.drop_index("ix_async_tool_executions_ref_type", "async_tool_executions")
    op.drop_index("ix_async_tool_executions_completion_id", "async_tool_executions")
    op.drop_index("ix_async_tool_executions_thread_id", "async_tool_executions")
    op.drop_table("async_tool_executions")

    op.drop_index("ix_messages_completion_id", "messages")
    op.drop_index("ix_messages_thread_id", "messages")
    op.drop_table("messages")

    op.drop_index("ix_completions_user_id", "completions")
    op.drop_index("ix_completions_thread_id", "completions")
    op.drop_table("completions")

    op.drop_index("ix_threads_user_id", "threads")
    op.drop_table("threads")

    op.drop_index("ix_widgets_status", "widgets")
    op.drop_index("ix_widgets_owner_id", "widgets")
    op.drop_table("widgets")

    op.drop_index("ix_cron_job_runs_job_name", "cron_job_runs")
    op.drop_table("cron_job_runs")

    op.drop_table("users")

    # Drop enum types
    postgresql.ENUM(name="completion_error_type").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="completion_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="message_role").drop(op.get_bind(), checkfirst=True)
