# Contributing

Guide for both human contributors and AI agents working on this project.

## For All Contributors

### Getting Started

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd generic
   ```

2. Install dependencies:
   ```bash
   make install
   ```

3. Start local services (for Python development):
   ```bash
   make setup-py
   ```

4. Run development servers:
   ```bash
   make dev
   ```

5. Verify everything works:
   ```bash
   make check
   ```

### Making Changes

1. Create a feature branch from `main`
2. Make your changes following the patterns in `docs/PATTERNS.md`
3. Run checks: `make check`
4. Format code: `make fmt`
5. Commit with a clear message describing the change
6. Open a pull request

### Commit Message Format

Use Conventional Commits:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation changes
- `refactor:` — Code refactoring
- `test:` — Adding or updating tests
- `chore:` — Build, CI, or tooling changes

**Scopes (optional):**
- `py` — Python workspace
- `ts` — TypeScript workspace
- `infra` — Infrastructure changes
- `ci` — CI/CD pipeline

**Examples:**
```
feat(py): add user authentication endpoint
fix(ts): resolve routing issue on refresh
docs: update contributing guide
chore(ci): add Docker build caching
```

## For AI Agents

### Context to Gather First

Before making changes, read:
- `CLAUDE.md` — Project overview and quick commands
- `docs/PATTERNS.md` — Coding conventions
- `docs/SUCCESS_CRITERIA.md` — CI checks that must pass
- Related code files to understand existing patterns

### Workflow

1. **Understand** — Read the task and relevant code
2. **Plan** — Break down into small steps
3. **Implement** — Follow existing patterns
4. **Verify** — Run tests and checks
5. **Commit** — Clear, atomic commits

### Constraints

- Do not modify CI/CD configuration without approval
- Do not add new dependencies without discussion
- Do not refactor unrelated code
- Do not skip tests or use `--no-verify`
- Do not modify `.env.project` PROJECT_NAME after initialization
- Do not commit secrets or `.env` files

### Working with Both Workspaces

This project has two separate workspaces:
- `py/` — Python (FastAPI, SQLAlchemy, Taskiq)
- `ts/` — TypeScript (React, Express, Vite)

When making changes:
- Work within the appropriate workspace
- Use the workspace's Makefile commands
- Check if changes affect shared infrastructure

## Code Review

- All PRs require review before merge
- CI must pass before merge
- Use draft PRs for work-in-progress
- Squash commits on merge preferred

## Local Development

### Python Setup

```bash
cd py
make install     # Install dependencies
make setup       # Start Postgres + Redis
make dev         # Run dev server (port 8000)
```

### TypeScript Setup

```bash
cd ts
make install     # Install dependencies
make styles      # Set up branding symlinks
make dev         # Run dev servers (ports 5173, 3001)
```

### Database Migrations (Python)

```bash
cd py
make db-prepare MSG="description"   # Generate migration from model changes
make db-migrate                     # Apply pending migrations
```

For manual migrations or more commands, see `py/docs/DATABASE.md`.
