# Generic Template

A fullstack Python monorepo template with AI chat, background jobs, and real-time streaming.

## Project Structure

```
py/
├── apps/py-app/          # FastAPI application
│   ├── src/              # App source code
│   ├── templates/        # Jinja2 templates
│   └── static/           # Static assets
├── packages/py-core/     # Shared library
│   └── src/py_core/
│       ├── ai_ml/        # AI/ML: chat engine, pydantic-ai
│       ├── database/     # SQLAlchemy models, migrations
│       └── events/       # Event publishing
ts/                       # TypeScript apps (Vite + Express)
config/deploy/            # Kamal deployment configs
docs/                     # Documentation
```

## Key Patterns

### SQLAlchemy 2.0 with StringEnum

All models use `Mapped`/`mapped_column` syntax with `StringEnum` for type-safe enums:

```python
from sqlalchemy.orm import Mapped, mapped_column
from py_core.database.utils import StringEnum

class MyModel(Base):
    status: Mapped[MyStatus] = mapped_column(StringEnum(MyStatus), default=MyStatus.PENDING)
```

**Important**: StringEnum usage depends on ORM vs Core:
```python
# ORM operations - use enum directly (StringEnum handles conversion)
model.status = MyStatus.PENDING
query.filter(Model.status == MyStatus.ACTIVE)

# Core update/insert - use .value (TypeDecorator doesn't auto-bind)
update(Model).where(Model.status == MyStatus.DRAFT.value).values(status=MyStatus.ACTIVE.value)
```

### uuid7 for IDs

All models use uuid7 (time-sortable) for primary keys:
```python
from py_core.database.utils import uuid7_str

class MyModel(Base):
    id: Mapped[str] = mapped_column(primary_key=True, default=uuid7_str)
```

### Background Jobs (TaskIQ)

Tasks use Redis broker with distributed locking for cron jobs:
```python
from src.tasks.cron import cron

@cron("*/5 * * * *", lock_ttl=120)
async def my_periodic_task():
    pass
```

## Deployment

Uses Kamal with 1Password for secrets management.

**Secrets come from 1Password vaults, not kamal env push.**

```bash
# Deploy
make kamal ARGS="py production deploy"

# Logs
make kamal ARGS="py production logs"
```

Key docs:
- `docs/deployment/KAMAL.md` - Deployment guide
- `docs/setup/WALKTHROUGH.md` - Complete setup walkthrough

## Code Quality

```bash
cd py && make check    # Run all checks (fmt, lint, types, test)
cd py && make types    # Type checking with ty
cd py && make lint     # Linting with ruff
cd py && make fmt      # Format with black
```

## Local Development

```bash
make install           # Install all dependencies
make dev               # Run all dev servers in tmux
```

Python runs on `localhost:8000`, TypeScript on `localhost:5173`.

## Agent Documentation

For detailed patterns and conventions, see the documentation:

### Python Patterns (`py/docs/`)
- `py/docs/PYTHON_LIBRARY_PATTERNS.md` - Context DI, Params dataclasses, module organization
- `py/docs/DATABASE.md` - Migrations, models, local setup
- `py/docs/SUCCESS_CRITERIA.md` - CI requirements, "done" definition
- `py/docs/CONTRIBUTING.md` - Contribution guidelines

### Setup & Deployment (`docs/`)
- `docs/setup/WALKTHROUGH.md` - Complete project setup
- `docs/setup/ONE_PASSWORD.md` - 1Password vault configuration
- `docs/setup/INFRASTRUCTURE.md` - Terraform infrastructure
- `docs/deployment/KAMAL.md` - Deployment guide

### Customization (`docs/customizing/`)
- `docs/customizing/README.md` - Overview and philosophy
- `docs/customizing/project-setup.md` - Renaming, domains, .env files
- `docs/customizing/typescript-packages.md` - TypeScript package patterns
- `docs/customizing/hybrid-stack.md` - Python API + TypeScript frontend
- `docs/customizing/multi-tenancy.md` - SaaS tenant isolation

## Issue Tracking

Use `/issues` to work with the local issue catalog in `issues/`.

Issues are markdown files in `issues/open/` and `issues/closed/`. See `issues/README.md` for format and workflow.

## Slash Commands

Available skills:
- `/init` - Initialize and customize template for your project
- `/check` - Run all CI checks (format, lint, types, tests)
- `/draft` - Push branch and create a draft PR
- `/issues` - Manage local issue catalog
- `/docs` - Navigate project documentation

## Customization

New to this template? Run `/init` to interactively customize it for your project, or see `docs/customizing/` for manual customization guides.
