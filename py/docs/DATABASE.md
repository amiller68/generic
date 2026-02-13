# Database Guide

This guide covers database operations, migrations, and local development setup. All database operations are managed through py-core.

## Overview

- **Database**: PostgreSQL 17
- **ORM**: SQLAlchemy (async)
- **Migrations**: Alembic
- **Location**: `py/packages/py-core/`

**All database operations must go through py-core.** Applications should import from py-core rather than accessing the database directly.

---

## Quick Reference

```bash
# From py/packages/py-core/

# Local development setup
make setup              # Start all services (db + minio + redis) and run migrations

# Database container management
make db-up              # Start PostgreSQL container
make db-down            # Stop and remove container (deletes data)
make db-status          # Check container status
make db-endpoint        # Print connection URL

# Database operations
make wipe               # Drop branch-specific database (keeps container running)

# Migrations
make db-migrate         # Run pending migrations
make db-prepare MSG="description"  # Create new migration (auto-generate)
```

---

## Local Development Setup

### Starting Services

For local development, py-core provides make commands to manage Docker containers:

```bash
# From py/packages/py-core/

# Start everything at once
make setup

# Or start individually
make db-up          # PostgreSQL on port 5433
make minio-up       # MinIO on port 9000
make redis-up       # Redis on port 6379
```

### Connection Details

| Service | Port | URL |
|---------|------|-----|
| PostgreSQL | 5433 | `postgresql://postgres:postgres@localhost:5433/generic` |
| MinIO | 9000 | `http://localhost:9000` |
| Redis | 6379 | `redis://localhost:6379` |

**Note:** PostgreSQL uses port 5433 (not 5432) to avoid conflicts with other local PostgreSQL instances.

### Managing Services

```bash
# From py/packages/py-core/

# Reset database (keeps container running, re-run setup after)
make wipe               # Drop branch-specific database
make setup              # Recreate database and run migrations

# Stop and remove containers (deletes all data)
make db-down
make minio-down
make redis-down

# Clean build artifacts only (does NOT touch containers)
make clean
```

---

## Database Migrations

### Running Migrations

Apply pending migrations to your database:

```bash
# From py/packages/py-core/
make db-migrate
```

This will:
1. Start the database if not running
2. Wait for the database to be ready
3. Run `alembic upgrade head`

### Creating New Migrations

When you modify database models, create a migration:

```bash
# From py/packages/py-core/

# Auto-generate from model changes (recommended)
make db-prepare MSG="add user preferences table"

# For manual migrations (data migrations, complex changes)
MANUAL=1 make db-prepare MSG="migrate legacy data"
```

**Auto-generate** compares your SQLAlchemy models to the current database schema and generates the appropriate `upgrade()` and `downgrade()` functions.

**Manual migrations** create an empty migration file for you to fill in - use this for data migrations or complex schema changes that can't be auto-detected.

### Migration Files

Migrations live in `py/packages/py-core/alembic/versions/`:

```
alembic/
├── env.py                              # Alembic configuration
├── script.py.mako                      # Migration template
└── versions/
    ├── 20251215_initial_schema.py      # First migration
    └── 20251216_add_user_role.py       # Adds role column
```

### Migration Best Practices

1. **One logical change per migration** - Don't combine unrelated changes
2. **Always test downgrade** - Make sure `downgrade()` works
3. **Use descriptive names** - The message becomes the filename
4. **Review auto-generated migrations** - They may need manual tweaks
5. **Don't modify existing migrations** - Once pushed, create a new one instead

### Soft Deletes (Never Hard Delete)

**Never delete records.** Use soft deletes with an `archived_at` timestamp instead:

```python
class MyModel(Base):
    # ... other columns ...
    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)
```

- Set `archived_at = utcnow()` instead of deleting
- Filter queries with `WHERE archived_at IS NULL` to exclude archived records
- This preserves data integrity, audit trails, and allows recovery

### Example Migration

```python
"""add user preferences table

Revision ID: abc123
Revises: def456
Create Date: 2025-01-15 10:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'abc123'
down_revision = 'def456'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('theme', sa.String(), nullable=False, default='light'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_preferences_user_id', 'user_preferences', ['user_id'])

def downgrade() -> None:
    op.drop_index('ix_user_preferences_user_id')
    op.drop_table('user_preferences')
```

---

## Creating Database Models

### Where Models Live

All models are in `py/packages/py-core/src/py_core/database/models/`.

### Model Patterns

Follow these patterns when creating models:

```python
# Example: database/models/user_preference.py
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from py_core.database.client import Base
from py_core.database.utils import utcnow, uuid7_str, PgEnum


class UserPreference(Base):
    """User preferences. No business logic, just columns."""

    __tablename__ = "user_preferences"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid7_str)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    theme: Mapped[str] = mapped_column(String, nullable=False, default="light")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    __table_args__ = (
        CheckConstraint("theme IN ('light', 'dark')", name="ck_user_preferences_theme"),
    )
```

### ID Strategies

- **Content-addressed (immutable)**: `prefix_<blake2b_hash>` (e.g., `con_`, `seq_`, `ftr_`)
- **User-mutable**: UUID7 via `uuid7_str` (e.g., user preferences, settings)

### After Creating a Model

1. Add the model file to `database/models/`
2. Import it in `database/models/__init__.py`
3. Generate a migration: `make db-prepare MSG="add user preferences"`
4. Review the generated migration
5. Apply it: `make db-migrate`
6. Create domain operations in py-core (see [PYTHON_LIBRARY_PATTERNS.md](./PYTHON_LIBRARY_PATTERNS.md))

---

## Storage Operations

Storage (S3/MinIO) is also managed through py-core:

### Local Development

```bash
# From py/packages/py-core/
make minio-up           # Start MinIO
make minio-status       # Check status
make minio-endpoint     # Print S3 endpoint
make minio-console      # Open web console
```

### Using Storage in Code

```python
from py_core.storage import Storage

@dataclass
class Context:
    db: AsyncSession
    logger: Logger
    storage: Storage  # Add storage dependency

async def upload_file(data: bytes, key: str, ctx: Context) -> str:
    await ctx.storage.put(key, data)
    return key
```

---

## Cleanup Commands

There are three levels of cleanup, from least to most destructive:

| Command | What it does | Containers | Data |
|---------|-------------|------------|------|
| `make clean` | Remove build artifacts (__pycache__, .venv, etc.) | Unchanged | Unchanged |
| `make wipe` | Drop branch-specific database | Running | Database dropped |
| `make teardown` | Remove all containers and volumes | All removed | All data deleted |

### Typical workflows

**Reset your database (keep container running):**
```bash
make wipe    # Drop database
make setup   # Recreate and migrate
```

**Full reset (remove containers):**
```bash
make teardown   # Remove all containers and volumes
make setup      # Recreate everything
```

**Clean up before committing:**
```bash
make clean   # Remove build artifacts only
```

### Multi-branch development

When working with git worktrees, each branch gets its own database (e.g., `generic_my_feature`). The `wipe` command respects this and only drops the database for your current branch.

---

## Troubleshooting

### Database Won't Start

```bash
# Check if port 5433 is in use
lsof -i :5433

# Check container status
make db-status

# View container logs
docker logs generic-postgres
```

### Migration Fails

```bash
# Check current migration state
cd py/packages/py-core
uv run alembic current
uv run alembic history

# If stuck, you may need to manually fix the alembic_version table
```

### Connection Issues on macOS

1. Check Docker Desktop is running
2. Verify port forwarding is enabled in Docker settings
3. Try restarting Docker Desktop
4. Check firewall settings

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_URL` | (local container) | PostgreSQL connection string |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO S3 endpoint |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection string |

For production, these are set via the vault configuration. See `bin/vault` for details.
