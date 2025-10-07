# Generic Fullstack

An extensible Docker-based deployment framework for rapidly building and deploying different types of applications with TypeScript and Python.

**[Live Demo](https://generic.krondor.org)**

## Philosophy

This framework is built on the principle that shipping quickly shouldn't mean sacrificing control. It provides:

- **Type-safe, ergonomic patterns** for both frontend and backend
- **Rapid iteration** with hot-reload dev environments
- **Own your deployment** - no vendor lock-in, deploy to any VM
- **Container-first** - portable, reproducible builds
- **Single source of truth** - all config in `.env.project` and `.env.vault`
- **Extensible architecture** - start with templates, adapt to your needs

**Note**: These templates are designed for rapid prototyping and small-to-medium projects. Not audited for enterprise security, not infinitely scalable (no lambdas, no Kubernetes). Perfect for weekend projects, MVPs, and proof-of-concepts that you can grow into production apps.

For deployment philosophy and architecture details, see [docs/dev-ops/index.md](./docs/dev-ops/index.md)

## What's Included

### TypeScript Stack (`ts/`)

**pnpm + Turbo monorepo with Vite and Express**

- Vite + React web application with Tailwind CSS
- Express API server with type-safe handlers
- Shared TypeScript configs and types
- Development hot-reload and production builds

See [ts/README.md](./ts/README.md) for details.

### Python Stack (`py/`)
**FastAPI + SQLAlchemy + HATEOAS**

- FastAPI server with server-side rendering
- SQLAlchemy ORM with Alembic migrations
- PostgreSQL database (local + production)
- Google OAuth authentication
- htmx + Tailwind CSS for responsive UI

See [py/README.md](./py/README.md) for details.

### Deployment Framework
**Terraform + Kamal + 1Password + Digital Ocean**

- Infrastructure as Code with Terraform
- Container orchestration with Kamal
- Secrets management with 1Password
- DNS with Cloudflare
- Automated SSL via Let's Encrypt

## Quick Start

### Prerequisites

1. **1Password account** with CLI installed (`op`)
2. **Terraform Cloud account** (free tier)
3. **Digital Ocean account** with API token
4. **Cloudflare account** managing your DNS zone
5. **Docker Hub account** (or GitHub Container Registry)

### Setup Workflow

Follow these guides in order:

1. **[Complete Walkthrough](./docs/setup/WALKTHROUGH.md)** - Step-by-step setup guide
2. **[1Password Setup](./docs/setup/ONE_PASSWORD.md)** - Configure vaults and secrets
3. **[Terraform Cloud Setup](./docs/setup/TERRAFORM_CLOUD.md)** - Create org and workspaces
4. **[Infrastructure Setup](./docs/setup/INFRASTRUCTURE.md)** - Deploy container registry and servers
5. **[Kamal Deployment](./docs/deployment/KAMAL.md)** - Deploy your applications

### Development

```bash
# Install dependencies for all projects
make install

# Run all dev servers in tmux
make dev

# Run specific project
make dev-py   # Python API only
make dev-ts   # TypeScript apps only

# Build styles
make styles

# Run checks (format, types, tests)
make check
```

See [docs/development/LOCAL.md](./docs/development/LOCAL.md) for detailed development workflows.

## Project Structure

```
.
├── bin/                    # Deployment and infrastructure scripts
│   ├── tfc               # Terraform Cloud management
│   ├── iac               # Infrastructure as Code (Terraform wrapper)
│   ├── kamal             # Deployment with Kamal
│   ├── vault             # 1Password secrets access
│   ├── ssh               # SSH into servers
│   └── dev               # Multi-project tmux dev environment
├── config/
│   └── deploy/           # Kamal deployment configs per service
├── iac/
│   ├── modules/          # Reusable Terraform modules
│   └── stages/           # Stage-specific configs (production, staging)
├── py/                   # Python FastAPI application
├── ts/                   # TypeScript monorepo (Vite, Express)
├── branding/             # Shared brand assets (CSS, icons, fonts)
├── docs/                 # Detailed documentation
│   ├── setup/          # Setup guides
│   ├── deployment/     # Deployment guides
│   └── development/    # Development guides
├── .env.project          # Project configuration
└── .env.vault            # Vault paths for secrets
```

## Configuration

### `.env.project` - Project Settings

Single source of truth for project-wide configuration:

```bash
PROJECT_NAME=generic                  # Must be globally unique (used for TFC org)
DNS_ROOT_ZONE=yourdomain.com         # Your Cloudflare domain
SERVICES="py:app,ts-web:"            # Services and subdomains
CLOUD_VAULT=cloud-providers          # 1Password vault for cloud credentials
```

**Important**: `PROJECT_NAME` must be globally unique as it becomes your Terraform Cloud organization name (`${PROJECT_NAME}-org`).

All infrastructure, deployment, and app configs derive from this file.

### `.env.vault` - Secrets Paths

Defines paths to secrets in 1Password:

```bash
# Cloud provider credentials
TF_TOKEN=op://cloud-providers/TERRAFORM_CLOUD_API_TOKEN/credential
DOCKER_HUB_USERNAME=op://cloud-providers/DOCKER_HUB_LOGIN/username
CLOUDFLARE_API_TOKEN=op://cloud-providers/CLOUDFLARE_DNS_API_TOKEN/credential
DIGITALOCEAN_TOKEN=op://cloud-providers/DO_API_TOKEN/credential

# Stage-specific app secrets
GOOGLE_O_AUTH_CLIENT_ID=op://${VAULT_SLUG}/GOOGLE_O_AUTH_CLIENT/username
```

Where `${VAULT_SLUG}` = `${PROJECT_NAME}-${STAGE}` (e.g., `generic-production`).

See [docs/setup/ONE_PASSWORD.md](./docs/setup/ONE_PASSWORD.md) for vault structure.

## Common Commands

### Infrastructure Management

```bash
# Terraform Cloud setup
make tfc up              # Create org and workspaces
make tfc status          # Check TFC status

# Infrastructure deployment
make iac <stage> <command>

# Examples:
make iac container-registry init    # Setup container registry
make iac container-registry apply   # Deploy registry
make iac production init            # Initialize production
make iac production plan            # Review infrastructure changes
make iac production apply           # Deploy production infrastructure
make iac production output          # Show outputs (IPs, keys, etc)
```

### Application Deployment

```bash
# Deploy with Kamal
make kamal ARGS="<service> <stage> <command>"

# Examples:
make kamal ARGS="py production deploy"         # Deploy Python API to production
make kamal ARGS="ts-web production deploy"     # Deploy web app to production
make kamal ARGS="py production logs"           # View Python API logs
make kamal ARGS="py production app exec"       # Execute command in container
```

### SSH Access

```bash
# SSH into production server
bin/ssh production

# SSH as specific user
bin/ssh production ubuntu
```

### Development

```bash
# Multi-project development
make dev                 # All projects in tmux
make dev ARGS="--kill"   # Kill tmux session

# Single project development
make dev-py             # Python only
make dev-ts             # TypeScript only

# Build and checks
make build              # Build all projects
make check              # Run all checks (format, types, tests)
make styles             # Build styles for all projects
```

## Architecture

### Local Development
```
Developer Machine
├── tmux session (make dev)
│   ├── Python FastAPI (port 8000)
│   ├── TypeScript Vite web (port 5173)
│   ├── TypeScript Express API (port 3001)
│   └── Local PostgreSQL (Docker, port 5432)
└── 1Password vault integration
```

### Production Deployment
```
Internet → Cloudflare DNS → Digital Ocean Droplet
                            └── Kamal Proxy (Traefik)
                                ├── Web app (yourdomain.com)
                                ├── Python API (app.yourdomain.com)
                                └── PostgreSQL (internal only)
```

## Deployment Workflow

1. **Configure** `.env.project` with your project name and domain
2. **Setup 1Password** vaults with cloud credentials
3. **Create TFC workspaces**: `make tfc up`
4. **Deploy container registry**: `make iac container-registry apply`
5. **Deploy infrastructure**: `make iac production apply`
6. **Bootstrap server**: `make kamal ARGS="py production setup"` (first time only)
7. **Boot accessories**: `make kamal ARGS="py production accessory boot postgres"` (if service has them)
8. **Deploy services**: `make kamal ARGS="py production deploy"`

Each step is automated and uses secrets from 1Password. No manual credential management.

## Documentation

### Setup Guides
- [Complete Walkthrough](./docs/setup/WALKTHROUGH.md) - Step-by-step setup guide
- [1Password Setup](./docs/setup/ONE_PASSWORD.md) - Configure vaults and secrets
- [Terraform Cloud Setup](./docs/setup/TERRAFORM_CLOUD.md) - Create org and workspaces
- [Infrastructure Setup](./docs/setup/INFRASTRUCTURE.md) - Deploy servers and DNS

### Deployment Guides
- [Kamal Deployment](./docs/deployment/KAMAL.md) - Deploy and manage services

### Development Guides
- [Local Development](./docs/development/LOCAL.md) - Dev environment setup
- [TypeScript Projects](./ts/README.md) - Vite app, Express API, and monorepo
- [Python Application](./py/README.md) - FastAPI, database, migrations

### Operations
- [DevOps Philosophy](./docs/dev-ops/index.md) - Architecture and design decisions

## Troubleshooting

**"Unable to authenticate"**
- Check 1Password credentials: `bin/vault read DOCKER_HUB_USERNAME`
- Verify vault names match `.env.project` and `.env.vault`

**"No infrastructure deployed"**
- Run `make iac production apply` first
- Check Terraform Cloud workspaces: `make tfc status`

**"Container won't start"**
- Check logs: `make kamal ARGS="<service> production logs"`
- Verify environment variables in 1Password vault

**"SSH connection refused"**
- Check firewall allows your IP
- Get SSH command: `make iac production output ssh_connect_command`

See individual docs for more troubleshooting.

## Extending the Framework

This framework is designed to be extensible:

### Adding New Application Stacks

The TypeScript and Python templates demonstrate two different patterns. You can:
- Add new language stacks (Rust, Go, etc.)
- Mix and match components
- Customize deployment configs

### Planned Extensions

**Rust Stack** (Planned):
- Axum + htmx web app
- OIDC authorization
- SQLX database integration
- Companion CLI tool

**Python Enhancements**:
- Redis + background jobs using Arq
- LLM patterns with Tensor Zero

**TypeScript Enhancements**:
- Auth patterns (OAuth, crypto keys)
- SQL integration for backend state

## Cost Estimate

Running this stack costs approximately:
- **Digital Ocean Droplet** (s-1vcpu-1gb): $6/month
- **Cloudflare DNS**: Free
- **Terraform Cloud**: Free (up to 500 resources)
- **1Password**: Varies by plan

**Total minimum**: ~$6-15/month depending on your 1Password plan.

## Contributing

This framework is under active development. Expect frequent changes and improvements. Check back for updates or contribute your own!

## License

Use at your own risk. Not audited, not infinitely scalable, not finished. Perfect for learning and rapid prototyping.
