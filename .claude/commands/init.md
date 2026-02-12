---
description: Initialize and customize template for your project
allowed-tools:
  - Read
  - Glob
  - Grep
  - AskUserQuestion
  - EnterPlanMode
---

Initialize and customize this template for your specific project.

This skill guides you through customizing the generic template by:
1. Gathering your project requirements
2. Planning the transformation
3. Executing after your approval

## Phase 1: Requirements Gathering

Ask the user these questions using AskUserQuestion. Collect all answers before proceeding to plan mode.

### Question 1: Project Identity

Ask for:
- **Project name**: Used for package.json, pyproject.toml, docker tags, 1Password vaults
  - Must be lowercase, no spaces (e.g., "myapp", "acme-dashboard")
- **Brief description**: One sentence describing what the app does

### Question 2: Stack Selection

Which stack configuration?

| Option | Description |
|--------|-------------|
| **Python only** | FastAPI backend + HTMX/Jinja frontend (server-rendered) |
| **TypeScript only** | Vite SPA + Express API (React frontend) |
| **Hybrid** | Python API + Vite frontend (most common for complex apps) |

### Question 3: Features

Which features does your app need? (multi-select)

- **Database** (PostgreSQL) - persistent data storage
- **Background jobs** (TaskIQ + Redis) - async task processing
- **Real-time** (WebSockets/SSE) - live updates
- **Multi-tenancy** - tenant isolation patterns
- **Authentication** - Google OAuth (can add more later)

### Question 4: Deployment

What's your deployment target?

| Option | Description |
|--------|-------------|
| **Kamal + Digital Ocean** | Production-ready single-server deployment |
| **Local only** | Development only, remove deployment configs |

## Phase 2: Enter Plan Mode

After gathering all requirements, call `EnterPlanMode` with the collected context.

The plan should cover:

### Structure Transformation

Based on stack selection:

**Python only:**
```
py/ -> app/
Remove: ts/
Update: Makefile, ci.yml, docker-compose.yml
Delete: config/deploy/ts-*.yml
```

**TypeScript only:**
```
ts/ -> app/
Remove: py/
Update: Makefile, ci.yml, docker-compose.yml
Delete: config/deploy/py.yml
```

**Hybrid (Python API + Vite frontend):**
```
py/packages/py-core/ -> app/api/packages/py-core/
py/apps/py-app/ -> app/api/ (remove templates/, API-only)
ts/apps/web/ -> app/web/
Update: API to return JSON, Vite to proxy to API
```

### File Updates Checklist

The plan must address each of these:

1. **Project identity**
   - [ ] Update `package.json` name field (if TypeScript)
   - [ ] Update `pyproject.toml` name field (if Python)
   - [ ] Update `.env.project` PROJECT_NAME
   - [ ] Update docker image tags in deploy configs
   - [ ] Update README.md title and description

2. **Stack consolidation**
   - [ ] Move selected stack to `app/` (or appropriate structure)
   - [ ] Remove unused stack directories
   - [ ] Update root Makefile PROJECTS variable
   - [ ] Update CI workflow to remove unused jobs

3. **Feature configuration**
   - [ ] Keep/remove database setup based on selection
   - [ ] Keep/remove TaskIQ/Redis based on selection
   - [ ] Keep/remove multi-tenancy patterns based on selection
   - [ ] Keep/remove OAuth setup based on selection

4. **Deployment configuration**
   - [ ] Update or remove Kamal configs
   - [ ] Update or remove Terraform configs
   - [ ] Update docker-compose.yml

5. **Documentation updates**
   - [ ] Update CLAUDE.md to reflect new structure
   - [ ] Update README.md with project-specific info
   - [ ] Remove irrelevant docs (e.g., MIXING_LANGUAGES.md if single stack)

### Target Structures

**Python only final structure:**
```
app/
├── apps/py-app/          # FastAPI application
│   ├── src/
│   ├── templates/
│   └── static/
├── packages/py-core/     # Shared library
├── Dockerfile
├── Makefile
└── pyproject.toml
```

**TypeScript only final structure:**
```
app/
├── apps/web/             # Vite SPA
├── apps/api/             # Express API
├── packages/             # Shared packages
├── Dockerfile
├── Makefile
└── package.json
```

**Hybrid final structure:**
```
app/
├── api/                  # Python API (FastAPI, JSON responses)
│   ├── src/
│   └── packages/py-core/
├── web/                  # Vite SPA (React frontend)
│   └── src/
├── Makefile
└── docker-compose.yml
```

## Phase 3: Execute After Approval

Once the user approves the plan, execute the transformation step by step.

Important execution notes:
- Use `git mv` for moves to preserve history
- Update imports/references after moves
- Run `make check` after each major change to catch issues early
- Commit logical chunks (e.g., "restructure to app/", "update configs", "update docs")

## Reference Documentation

Point users to these docs for manual customization or deeper understanding:

- `docs/CUSTOMIZING.md` - Manual customization guide
- `docs/development/MIXING_LANGUAGES.md` - For hybrid setups
- `py/docs/PYTHON_LIBRARY_PATTERNS.md` - Python patterns
- `docs/deployment/KAMAL.md` - Deployment guide
