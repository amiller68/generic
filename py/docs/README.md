# Python Project Documentation

This directory contains documentation for the Python components of the generic template. These docs are designed for both AI agents and human developers.

## Quick Start

1. Run `make install` to ensure dependencies are available
2. Read [PYTHON_LIBRARY_PATTERNS.md](./PYTHON_LIBRARY_PATTERNS.md) for architecture patterns
3. Ensure [SUCCESS_CRITERIA.md](./SUCCESS_CRITERIA.md) are met before creating a PR

---

## Document Index

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [CONTRIBUTING.md](./CONTRIBUTING.md) | How to contribute (agents & humans) | First time contributing |
| [DATABASE.md](./DATABASE.md) | Database operations, migrations, local setup | Working with the database |
| [PACKAGE_SETUP.md](./PACKAGE_SETUP.md) | Package scripts and tooling | Creating or modifying packages |
| [PYTHON_LIBRARY_PATTERNS.md](./PYTHON_LIBRARY_PATTERNS.md) | Python architecture patterns | Writing Python code |
| [TASKS.md](./TASKS.md) | Background jobs and scheduled tasks | Working with TaskIQ |
| [SUCCESS_CRITERIA.md](./SUCCESS_CRITERIA.md) | CI requirements and checks | Before creating a PR |

---

## Document Summaries

### [CONTRIBUTING.md](./CONTRIBUTING.md)
How to contribute to the project:
- **For AI agents**: Constraints, code quality expectations, submission checklist
- **For humans**: Dev setup, code review guidelines, architecture decisions
- Commit conventions and PR process

### [DATABASE.md](./DATABASE.md)
Database operations and local development:
- Local setup with make commands (`make setup`, `make db-migrate`)
- Creating and running Alembic migrations
- Model patterns and best practices
- Storage (MinIO) setup and usage

### [PYTHON_LIBRARY_PATTERNS.md](./PYTHON_LIBRARY_PATTERNS.md)
Architecture patterns for Python code:
- **Models vs Operations**: Database models are data-only; operations are functional
- **Dependency Injection**: Use `Context` dataclasses, never globals
- **Params for Extensibility**: Design params with defaults for backward compatibility
- **Module Organization**: Standard structure with `_context.py`, `create.py`, `read.py`

### [TASKS.md](./TASKS.md)
Background jobs and scheduled tasks:
- TaskIQ broker and worker setup
- `@cron` decorator with distributed locking
- Task dependencies (`TaskiqDepends`)
- Run tracking and observability

### [SUCCESS_CRITERIA.md](./SUCCESS_CRITERIA.md)
What "done" means:
- `make check` must pass (build, format, types, lint)
- Tests must pass
- No dev servers (shared machine)
- Common fixes for CI failures

### [PACKAGE_SETUP.md](./PACKAGE_SETUP.md)
Package development standards:
- Python package scripts, pyproject.toml, Makefile
- Tool standards (Black, Ruff, ty)
- Turbo configuration and task orchestration

---

## Key Constraints

1. **Run `make install` first** - Always at the start of work
2. **No dev servers** - Shared machine with other agents
3. **`make check` must pass** - Before creating any PR
4. **Follow existing patterns** - Match codebase style

---

## External Resources

- [Local Development](../../docs/development/LOCAL.md) - Full development environment
- [Kamal Deployment](../../docs/deployment/KAMAL.md) - Deployment guide
- [Setup Walkthrough](../../docs/setup/WALKTHROUGH.md) - Complete setup guide
