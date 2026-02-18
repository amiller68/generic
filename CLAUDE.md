# Project Guide

Extensible Docker-based deployment framework for TypeScript and Python applications.

## Quick Reference

```bash
make install             # Install dependencies for all projects
make dev                 # Start all dev servers in tmux
make check               # Run all checks (format, lint, types, tests)
make build               # Build all projects
make test                # Run tests for all projects
make fmt                 # Format all projects
```

**Project-specific:**
```bash
make check-py            # Check Python project only
make check-ts            # Check TypeScript project only
make dev-py              # Run Python dev server
make dev-ts              # Run TypeScript dev servers
make setup-py            # Start Postgres + Redis for Python
```

**Deployment:**
```bash
make kamal <service> <stage> deploy   # Deploy a service
make iac <stage> plan                 # Plan infrastructure changes
make iac <stage> apply                # Apply infrastructure
```

## Project Structure

```
py/                      # Python FastAPI application
├── apps/py-app/         # Main web app with SSR
└── packages/py-core/    # Shared Python package

ts/                      # TypeScript monorepo (pnpm + Turbo)
├── apps/web/            # Vite + React frontend
├── apps/api/            # Express API server
└── packages/            # Shared configs and types

bin/                     # Deployment and infrastructure scripts
config/deploy/           # Kamal service configs
iac/                     # Terraform infrastructure
```

For detailed structure, see `docs/PROJECT_LAYOUT.md`.

## Documentation

- `docs/index.md` — Documentation hub and agent instructions
- `docs/PATTERNS.md` — Coding conventions
- `docs/SUCCESS_CRITERIA.md` — CI checks
- `docs/CONTRIBUTING.md` — Contribution guide
- `docs/PROJECT_LAYOUT.md` — Codebase structure

## Issues

Track work items in `issues/`. See `issues/README.md` for the convention.

## Constraints

- Python 3.12+ with uv package manager
- Node.js 20.x with pnpm 9.x
- TypeScript strict mode enabled
- All code must pass CI checks before merge
- Use Conventional Commits format
- Secrets managed via 1Password vault (never committed)

## Do Not

- Do not commit `.env` files or secrets
- Do not skip CI checks with `--no-verify`
- Do not push directly to main
- Do not add dependencies without team discussion
- Do not modify infrastructure without review
- Do not change PROJECT_NAME in `.env.project` after initialization
