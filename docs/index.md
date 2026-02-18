# Documentation Index

Central hub for project documentation. AI agents should read this first.

## Quick Start

```bash
# Install dependencies
make install

# Start local services (Postgres + Redis)
make setup-py

# Run all development servers
make dev

# Run all checks
make check
```

**Development URLs:**
- Python API: http://localhost:8000
- TypeScript Web: http://localhost:5173
- TypeScript API: http://localhost:3001

## Documentation

| Document | Purpose |
|----------|---------|
| [PATTERNS.md](./PATTERNS.md) | Coding conventions and patterns |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | How to contribute (agents + humans) |
| [SUCCESS_CRITERIA.md](./SUCCESS_CRITERIA.md) | CI checks that must pass |
| [PROJECT_LAYOUT.md](./PROJECT_LAYOUT.md) | Codebase structure overview |

## For AI Agents

You are an autonomous coding agent working on a focused task.

### Workflow

1. **Understand** — Read the task description and relevant docs
2. **Explore** — Search the codebase to understand context
3. **Plan** — Break down work into small steps
4. **Implement** — Follow existing patterns in `PATTERNS.md`
5. **Verify** — Run checks from `SUCCESS_CRITERIA.md`
6. **Commit** — Clear, atomic commits

### Project-Specific Guidelines

- **Two workspaces:** Python (`py/`) and TypeScript (`ts/`) are separate monorepos
- **Check both if needed:** Changes may affect either or both projects
- **Use Makefiles:** Both projects have Makefiles — use `make` commands, not raw tools
- **Format before commit:** Run `make fmt` in the affected project
- **Tests required:** Add tests for new functionality

### Key Commands

```bash
# In py/ directory
make fmt-check    # Black formatting check
make lint         # Ruff linter
make types        # mypy type checking
make test         # pytest

# In ts/ directory
make fmt-check    # Prettier formatting check
make types        # TypeScript type check
make test         # Vitest
```

### When Complete

Your work will be reviewed and merged by the parent session.
Ensure all checks pass before finishing.
