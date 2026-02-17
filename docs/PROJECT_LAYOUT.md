# Project Layout

Overview of the codebase structure.

## Directory Structure

```
.
├── py/                          # Python workspace (FastAPI)
│   ├── apps/
│   │   └── py-app/              # Main FastAPI application
│   │       ├── src/             # Application source
│   │       │   ├── main.py      # Entry point
│   │       │   ├── routes/      # API route handlers
│   │       │   ├── models/      # SQLAlchemy models
│   │       │   ├── services/    # Business logic
│   │       │   ├── tasks/       # Taskiq background jobs
│   │       │   └── templates/   # Jinja2 templates
│   │       └── tests/           # pytest tests
│   ├── packages/
│   │   └── py-core/             # Shared Python package
│   ├── pyproject.toml           # Workspace configuration
│   ├── Makefile                 # Build/test commands
│   └── Dockerfile               # Production container
│
├── ts/                          # TypeScript workspace (pnpm + Turbo)
│   ├── apps/
│   │   ├── web/                 # Vite + React frontend
│   │   │   ├── src/
│   │   │   │   ├── main.tsx     # React entry point
│   │   │   │   └── components/  # React components
│   │   │   └── vite.config.ts
│   │   └── api/                 # Express API server
│   │       ├── src/
│   │       │   └── index.ts     # Express entry point
│   │       └── vitest.config.ts
│   ├── packages/
│   │   ├── http-api/            # Shared HTTP types
│   │   └── typescript-config/   # Shared TS configs
│   ├── package.json             # Workspace root
│   ├── pnpm-workspace.yaml      # pnpm workspace config
│   ├── turbo.json               # Turbo build config
│   └── Makefile                 # Build/test commands
│
├── bin/                         # Deployment scripts
│   ├── dev                      # Multi-project tmux runner
│   ├── vault                    # 1Password secrets access
│   ├── kamal                    # Deployment orchestration
│   ├── iac                      # Terraform wrapper
│   ├── tfc                      # Terraform Cloud management
│   └── ssh                      # Server SSH access
│
├── config/
│   └── deploy/                  # Kamal service configs
│       ├── py.yml               # Python API deployment
│       ├── ts-web.yml           # TypeScript web deployment
│       └── static.yml           # Static assets deployment
│
├── iac/                         # Infrastructure as Code
│   ├── modules/                 # Reusable Terraform modules
│   │   ├── digitalocean/        # DO droplet, DNS, etc.
│   │   ├── cloudflare/          # DNS records
│   │   └── common/              # Shared resources
│   └── stages/                  # Environment configs
│       ├── production/          # Production infrastructure
│       └── container-registry/  # Docker registry setup
│
├── branding/                    # Shared brand assets
│   └── assets/                  # CSS, icons, fonts
│
├── static/                      # Static file serving
│
├── docs/                        # Documentation
├── issues/                      # File-based issue tracking
│
├── .env.project                 # Project configuration
├── .env.vault                   # 1Password vault paths
├── docker-compose.yml           # Local dev services
├── Makefile                     # Root-level commands
└── CLAUDE.md                    # Project guide
```

## Key Files

- `py/apps/py-app/src/main.py` — FastAPI application entry point
- `ts/apps/web/src/main.tsx` — React application entry point
- `ts/apps/api/src/index.ts` — Express API entry point
- `.env.project` — Project-wide configuration (name, DNS, services)
- `.env.vault` — 1Password secret paths (not committed)
- `Makefile` — Root build orchestration

## Entry Points

| Service | Entry Point | Port |
|---------|-------------|------|
| Python API | `py/apps/py-app/src/main.py` | 8000 |
| TypeScript Web | `ts/apps/web/src/main.tsx` | 5173 |
| TypeScript API | `ts/apps/api/src/index.ts` | 3001 |

## Configuration

- `.env.project` — Project name, DNS zone, service list
- `.env.vault` — 1Password paths for secrets (per environment)
- `config/deploy/*.yml` — Kamal deployment configs
- `iac/stages/*` — Terraform environment configs

## Tests

- `py/apps/py-app/tests/` — Python tests (pytest)
- `ts/apps/*/src/**/*.test.ts` — TypeScript tests (Vitest, co-located)
- `ts/tests/` — TypeScript integration tests

## Build Output

- `py/.venv/` — Python virtual environment
- `ts/node_modules/` — Node.js dependencies
- `ts/apps/*/dist/` — Built TypeScript bundles
- `target/` — Docker build artifacts (not committed)
