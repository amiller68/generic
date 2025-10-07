# Local Development Guide

This guide explains how to set up and use the local development environment for the generic template.

## Overview

The template supports local development with:
- **Multi-project tmux sessions** - All services in one terminal
- **Hot-reload** - Python and TypeScript automatically reload on changes
- **Local databases** - PostgreSQL in Docker containers
- **1Password integration** - Secrets loaded from vaults
- **Branding sync** - Shared CSS and assets across projects

## Quick Start

```bash
# Install all dependencies
make install

# Build styles
make styles

# Run all dev servers in tmux
make dev
```

This starts:
- Python FastAPI on `http://localhost:8000`
- TypeScript Vite web app on `http://localhost:5173`
- TypeScript Express API on `http://localhost:3001`
- PostgreSQL on `localhost:5432` (Python only)

## Prerequisites

### Required Tools

**All Projects:**
- **1Password CLI** (`op`) - For secrets management
- **Make** - Command runner

**Python:**
- **Python 3.12**
- **uv** - Python package manager
- **Docker** - For PostgreSQL container

**TypeScript:**
- **Node.js 20.x**
- **pnpm** - Installed automatically by project

### Install Prerequisites

```bash
# macOS
brew install --cask 1password-cli
brew install python@3.12
brew install --cask docker

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Node.js (via nvm recommended)
nvm install 20
nvm use 20
```

## Development Workflows

### Multi-Project Development (Recommended)

Run all projects simultaneously in a tmux session:

```bash
# Start all dev servers
make dev
```

This creates a tmux session with:
- **Pane 1**: Python development server
- **Pane 2**: TypeScript development servers (web + api)

**Tmux Navigation:**
- `Ctrl-b %` - Split pane vertically
- `Ctrl-b "` - Split pane horizontally
- `Ctrl-b arrow` - Navigate between panes
- `Ctrl-b d` - Detach from session
- `tmux attach -t <session-name>` - Reattach to session

**Stopping:**
```bash
# Kill the tmux session
make dev ARGS="--kill"

# Or from inside tmux
Ctrl-b :kill-session
```

### Single Project Development

Run projects individually:

```bash
# Python only
make dev-py

# TypeScript only
make dev-ts
```

Or use project-specific commands:

```bash
# Python development
cd py/
make dev

# TypeScript development
cd ts/
make dev
```

## TypeScript Development

### Initial Setup

```bash
cd ts/

# Install dependencies
make install

# Setup branding asset symlinks
make styles

# Start development servers
make dev
```

### Development Servers

```bash
# All apps (web + api)
make dev
```

This starts:
- Vite web app on `http://localhost:5173`
- Express API on `http://localhost:3001`

Both with:
- Hot module replacement
- TypeScript compilation
- Auto-restart on changes

### Code Quality

```bash
# Format code
make fmt

# Check formatting
make fmt-check

# Type checking
make types

# Run tests
make test

# Run all checks
make check
```

### Styles and Assets

```bash
# Create asset symlinks
make styles

# Clean symlinks
make clean
```

This creates symlinks in `ts/apps/web/public/` pointing to `branding/assets/`:
- `favicon.ico` → `branding/assets/favicon.ico`
- `icon.svg` → `branding/assets/icon.svg`
- etc.

**Note**: Symlinks are used in development. For Docker builds, assets are copied instead.

### Project Structure

```
ts/
├── apps/
│   ├── web/              # Vite React app
│   │   ├── src/          # Source code
│   │   ├── public/       # Static files (symlinks to branding)
│   │   └── package.json
│   └── api/              # Express API
│       ├── src/          # Source code
│       ├── tests/        # Test files
│       └── package.json
├── packages/
│   ├── typescript-config/ # Shared TypeScript configs
│   └── http-api/          # Shared HTTP API types
├── bin/
│   └── styles.sh          # Branding asset setup
├── package.json           # Root package.json
├── pnpm-workspace.yaml    # pnpm workspace config
└── turbo.json             # Turbo monorepo config
```

### Common Tasks

**Add a new page (web app):**
1. Create component in `apps/web/src/pages/YourPage.tsx`
2. Add route to your router
3. Test: `http://localhost:5173/your-page`

**Add an API endpoint:**
1. Create route in `apps/api/src/routes/`
2. Register in `apps/api/src/index.ts`
3. Test: `curl http://localhost:3001/your-endpoint`

**Add a dependency:**
```bash
# To web app
cd apps/web
pnpm add package-name

# To API
cd apps/api
pnpm add package-name

# To root (dev dependency)
pnpm add -D -w package-name
```

## Python Development

### Initial Setup

```bash
cd py/

# Install dependencies
make install

# Build styles
make styles

# Start local PostgreSQL
make db up

# Run migrations
make db migrate
```

### Development Server

```bash
# With 1Password vault (recommended)
make dev

# Without vault (requires manual env vars)
make run
```

Server runs on `http://localhost:8000` with hot-reload.

### Database Management

**Starting Database:**
```bash
# Start PostgreSQL container
make db up

# Check status
make db status

# View connection URL
make db endpoint
```

**Migrations:**
```bash
# Run all pending migrations
make db migrate

# Create new migration (auto-detect changes)
make db prepare "Add user table"

# Create manual migration
MANUAL=1 make db prepare "Custom data migration"
```

**Database Access:**
```bash
# Connect via psql
make db connect

# Run SQL query
make db connect
> SELECT * FROM users;

# View migration history
uv run alembic history
```

**Stopping Database:**
```bash
# Stop container (keeps data)
docker stop <container-name>

# Remove container and volumes (deletes data)
make db down
```

## Branding and Styles

Shared branding assets are in `branding/`:

```
branding/
├── assets/           # Icons, favicons
│   ├── favicon.ico
│   ├── icon.svg
│   ├── icon.png
│   └── favicon.png
├── styles/           # CSS source files
│   └── global.css  # Tailwind base + custom CSS
└── tailwind.config.js  # Shared Tailwind config
```

### Building Styles

```bash
# From project root
make styles       # Build styles for all projects
make styles-py    # Build Python styles only
make styles-ts    # Build TypeScript styles only

# Or from individual projects
cd py/ && make styles
cd ts/ && make styles
```

**Python**: Copies assets and compiles Tailwind CSS to `py/static/css/main.css`

**TypeScript**: Creates symlinks from `ts/apps/web/public/` to `branding/assets/`

## Environment Variables

### Development Environment

For local development, secrets can be loaded from 1Password or set manually.

**Python** (via `bin/app/dev.sh`):
```bash
# Example environment variables
GOOGLE_O_AUTH_CLIENT_ID
GOOGLE_O_AUTH_CLIENT_SECRET
POSTGRES_URL  # Auto-set by db commands
```

**TypeScript**:
```bash
# Web app can use .env.local or environment variables
VITE_API_URL=http://localhost:3001

# API can use environment variables for config
PORT=3001
```

## Testing

### Python Tests

```bash
cd py/

# Run all tests
make test

# Run specific test file
uv run pytest tests/test_auth.py

# Run with coverage
uv run pytest --cov=src tests/

# Run with verbose output
uv run pytest -v tests/
```

### TypeScript Tests

```bash
cd ts/

# Run all tests
make test

# Run specific test
pnpm test your-test.spec.ts

# Run with watch mode
cd apps/api
pnpm test --watch
```

## Troubleshooting

### "Module not found" (Python)

```bash
cd py/
make install  # Reinstall dependencies
```

### "Command not found: pnpm" (TypeScript)

```bash
cd ts/
make install  # Installs pnpm and dependencies
```

### "Database connection refused" (Python)

```bash
# Check database is running
make db status

# Start database
make db up

# Check connection URL
make db endpoint
```

### "Port already in use"

```bash
# Python (8000)
lsof -i :8000
kill -9 PID

# TypeScript Web (5173)
lsof -i :5173
kill -9 PID

# TypeScript API (3001)
lsof -i :3001
kill -9 PID

# PostgreSQL (5432)
lsof -i :5432
make db down
```

### "Styles not loading"

```bash
# Rebuild styles
make styles

# Python: Check static/css/main.css exists
ls py/static/css/

# TypeScript: Check symlinks exist
ls -la ts/apps/web/public/
```

## Next Steps

After setting up local development:

1. **Make changes** to your application
2. **Test locally** with `make dev`
3. **Run checks** with `make check`
4. **Commit changes** to git
5. **Deploy** to staging/production (see deployment guides)

For deployment workflows, see:
- [Infrastructure Setup](../setup/INFRASTRUCTURE.md)
- [Deployment Guide](../deployment/KAMAL.md)
