# Customizing the Generic Template

This guide explains the template's modular architecture and how to customize it for your project.

**Prefer the guided approach?** Run `/init` to interactively customize the template with Claude's help.

## Architecture Overview

The template is organized as a modular monorepo with independent stacks:

```
.
├── py/                   # Python stack (FastAPI + SQLAlchemy)
│   ├── apps/py-app/      # Main application
│   └── packages/py-core/ # Shared library
├── ts/                   # TypeScript stack (Vite + Express)
│   ├── apps/web/         # Vite SPA
│   └── apps/api/         # Express API
├── config/deploy/        # Kamal deployment configs
├── iac/                  # Terraform infrastructure
└── docs/                 # Documentation
```

Each stack is self-contained and can be used independently or together.

## Stack Selection

### Python Only

Best for: Server-rendered apps, APIs with HTMX frontends, data-heavy applications.

**What you get:**
- FastAPI with async support
- SQLAlchemy 2.0 with PostgreSQL
- Jinja2 templates + HTMX for reactive UI
- TaskIQ for background jobs
- Google OAuth authentication

**To use Python only:**
1. Remove `ts/` directory
2. Rename `py/` to `app/` (optional, for cleaner structure)
3. Update root Makefile: `PROJECTS := app` (or `py`)
4. Remove TypeScript jobs from `.github/workflows/ci.yml`
5. Delete `config/deploy/ts-*.yml`

### TypeScript Only

Best for: SPAs, React applications, Node.js APIs.

**What you get:**
- Vite + React frontend
- Express API server
- pnpm + Turbo monorepo
- Tailwind CSS

**To use TypeScript only:**
1. Remove `py/` directory
2. Rename `ts/` to `app/` (optional)
3. Update root Makefile: `PROJECTS := app` (or `ts`)
4. Remove Python jobs from `.github/workflows/ci.yml`
5. Delete `config/deploy/py.yml`

### Hybrid (Python API + TypeScript Frontend)

Best for: Complex apps needing Python's data/ML capabilities with a React frontend.

**What you get:**
- Python API returning JSON
- React SPA consuming the API
- Shared deployment infrastructure

**To set up hybrid:**
1. Keep `py/packages/py-core/` for shared Python code
2. Modify `py/apps/py-app/` to be API-only (remove templates/)
3. Configure Vite to proxy API requests to Python backend
4. See `docs/development/MIXING_LANGUAGES.md` for details

## Feature Configuration

### Database (PostgreSQL)

The Python stack includes full PostgreSQL support via SQLAlchemy.

**Components:**
- `py/packages/py-core/src/py_core/database/` - Models, migrations, utilities
- `docker-compose.yml` - Local PostgreSQL container
- Alembic for migrations

**To remove database:**
1. Delete `py/packages/py-core/src/py_core/database/`
2. Remove database-related dependencies from `pyproject.toml`
3. Remove PostgreSQL from `docker-compose.yml`
4. Remove `postgres` accessory from Kamal configs

### Background Jobs (TaskIQ + Redis)

Async task processing with distributed locking for cron jobs.

**Components:**
- `py/apps/py-app/src/tasks/` - Task definitions
- Redis broker configuration

**To remove background jobs:**
1. Delete `py/apps/py-app/src/tasks/`
2. Remove TaskIQ dependencies from `pyproject.toml`
3. Remove Redis from `docker-compose.yml` and Kamal configs

### Multi-tenancy

Tenant isolation patterns for SaaS applications.

**Components:**
- Tenant model and middleware
- Row-level security patterns

**To add multi-tenancy:**
- See `docs/development/MULTI_TENANCY.md` (if exists)
- Or implement tenant filtering in database queries

### Authentication (Google OAuth)

OAuth2 authentication with Google.

**Components:**
- `py/apps/py-app/src/auth/` - Auth routes and middleware
- Session management

**To use different auth:**
- The OAuth implementation can be adapted for other providers
- For custom auth, implement your own session/JWT handling
- Remove Google-specific code if not needed

## Deployment Configuration

### Kamal (Recommended)

Single-server Docker deployment with zero-downtime deploys.

**Config files:** `config/deploy/<service>.yml`

**To customize:**
1. Update `.env.project` with your project name and domain
2. Modify deploy configs for your services
3. See `docs/deployment/KAMAL.md`

### Local Only (No Deployment)

For development-only projects.

**To remove deployment:**
1. Delete `config/deploy/`
2. Delete `iac/` (Terraform)
3. Remove deployment sections from Makefile
4. Remove deployment docs

## Common Customization Patterns

### Renaming the Project

1. Update `.env.project`:
   ```bash
   PROJECT_NAME=your-project-name
   ```

2. Update `py/pyproject.toml`:
   ```toml
   [project]
   name = "your-project-name"
   ```

3. Update `ts/package.json` (if using TypeScript):
   ```json
   { "name": "your-project-name" }
   ```

4. Update docker tags in `config/deploy/*.yml`

### Adding a New Python Package

1. Create `py/packages/your-package/`
2. Add `pyproject.toml` with package metadata
3. Add to workspace in root `py/pyproject.toml`
4. Import in apps as needed

### Adding a New TypeScript App

1. Create `ts/apps/your-app/`
2. Add `package.json` and configure build
3. Add to Turbo pipeline in `ts/turbo.json`

### Changing the Domain

1. Update `.env.project`:
   ```bash
   DNS_ROOT_ZONE=yourdomain.com
   ```

2. Update Cloudflare DNS configuration in Terraform
3. Re-run infrastructure deployment

## File Reference

| File | Purpose | Customization Notes |
|------|---------|---------------------|
| `.env.project` | Project-wide config | Update PROJECT_NAME, domain |
| `.env.vault` | 1Password secret paths | Update vault names |
| `Makefile` | Root build commands | Update PROJECTS list |
| `.github/workflows/ci.yml` | CI pipeline | Remove unused stack jobs |
| `docker-compose.yml` | Local services | Add/remove services |
| `config/deploy/*.yml` | Kamal configs | One per deployed service |
| `CLAUDE.md` | Agent instructions | Update for your patterns |

## Getting Help

- **Guided setup:** Run `/init` for interactive customization
- **Documentation:** Run `/docs` to navigate project docs
- **Issues:** Check `issues/` for known issues and TODOs
