# Python Packages

This guide covers the py-core shared library pattern and how to organize Python code in the monorepo.

## Package Structure

```
py/
├── apps/
│   └── py-app/           # FastAPI application
│       ├── src/          # App source code
│       ├── templates/    # Jinja2 templates
│       └── static/       # Static assets
├── packages/
│   └── py-core/          # Shared library
│       └── src/py_core/
│           ├── ai_ml/    # AI/ML: chat engine, pydantic-ai
│           ├── database/ # SQLAlchemy models, migrations
│           └── events/   # Event publishing
└── pyproject.toml        # Workspace configuration
```

## py-core Library

The `py-core` package contains shared code used by applications:

### Database Module

```
py_core/database/
├── __init__.py
├── base.py           # SQLAlchemy Base, session management
├── utils.py          # uuid7, StringEnum, common utilities
├── migrations/       # Alembic migrations
└── models/           # ORM models
    ├── __init__.py
    ├── user.py
    └── thread.py
```

### AI/ML Module

```
py_core/ai_ml/
├── __init__.py
├── engine.py         # Chat completion engine
├── providers.py      # LLM provider abstractions
└── types.py          # Pydantic models for AI operations
```

### Events Module

```
py_core/events/
├── __init__.py
├── publisher.py      # Redis-based event publishing
└── types.py          # Event payload types
```

## Key Patterns

### SQLAlchemy 2.0 with StringEnum

All models use `Mapped`/`mapped_column` syntax with `StringEnum` for type-safe enums:

```python
from sqlalchemy.orm import Mapped, mapped_column
from py_core.database.utils import StringEnum

class MyModel(Base):
    status: Mapped[MyStatus] = mapped_column(
        StringEnum(MyStatus),
        default=MyStatus.PENDING
    )
```

**Important**: Use enums directly - no `.value` needed:

```python
# Correct
model.status = MyStatus.PENDING
query.filter(Model.status == MyStatus.ACTIVE)

# Wrong
model.status = MyStatus.PENDING.value  # NO
```

### uuid7 for IDs

All models use uuid7 (time-sortable) for primary keys:

```python
from py_core.database.utils import uuid7_str

class MyModel(Base):
    id: Mapped[str] = mapped_column(primary_key=True, default=uuid7_str)
```

### Context-Based Dependency Injection

Operations receive dependencies via Context dataclasses:

```python
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

@dataclass
class Context:
    db: AsyncSession
    logger: Logger

async def create_entity(params: Params, ctx: Context) -> Entity:
    # Access dependencies through ctx
    await ctx.db.execute(stmt)
    ctx.logger.debug("Created entity")
```

See `py/docs/PYTHON_LIBRARY_PATTERNS.md` for comprehensive patterns.

## Using in Apps

Import from py-core in application code:

```python
from py_core.database import Base, get_session
from py_core.database.models import User, Thread
from py_core.ai_ml import ChatEngine
from py_core.events import EventPublisher
```

## Adding a New Package

1. Create the package directory:
   ```
   py/packages/your-package/
   ├── src/your_package/
   │   └── __init__.py
   └── pyproject.toml
   ```

2. Configure `pyproject.toml`:
   ```toml
   [project]
   name = "your-package"
   version = "0.1.0"

   [build-system]
   requires = ["hatchling"]
   build-backend = "hatchling.build"
   ```

3. Add to workspace in root `py/pyproject.toml`:
   ```toml
   [tool.uv.workspace]
   members = ["apps/*", "packages/*"]
   ```

4. Add as dependency to apps:
   ```toml
   [project]
   dependencies = ["your-package"]
   ```

## Database Migrations

Migrations live in `py/packages/py-core/src/py_core/database/migrations/`.

```bash
# Generate a migration
cd py && make migration MSG="add new table"

# Apply migrations
cd py && make migrate

# Rollback
cd py && make migrate-down
```

## Testing

Tests live alongside the code or in dedicated test directories:

```bash
cd py && make test          # Run all tests
cd py && make test-cov      # With coverage
```

## Related Documentation

- `py/docs/PYTHON_LIBRARY_PATTERNS.md` - Context DI, Params dataclasses, module organization
- `py/docs/DATABASE.md` - Migrations, models, local setup
- `py/docs/SUCCESS_CRITERIA.md` - CI requirements, "done" definition
