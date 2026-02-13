---
description: Navigate project documentation
allowed-tools:
  - Read
  - Glob
---

Navigate and explore project documentation.

## Documentation Structure

### Root Docs (`docs/`)

Cross-project documentation that applies to the entire repository:

| Path | Purpose |
|------|---------|
| `docs/development/LOCAL.md` | Local development setup and workflow |
| `docs/setup/WALKTHROUGH.md` | Complete setup walkthrough for new projects |
| `docs/setup/ONE_PASSWORD.md` | 1Password vault configuration |
| `docs/setup/TERRAFORM_CLOUD.md` | Terraform Cloud setup |
| `docs/setup/INFRASTRUCTURE.md` | Server provisioning with Terraform |
| `docs/deployment/KAMAL.md` | Kamal deployment guide |
| `docs/dev-ops/index.md` | DevOps philosophy and approach |

### Python Docs (`py/docs/`)

Python-specific patterns and conventions:

| Path | Purpose |
|------|---------|
| `py/docs/README.md` | Index of Python documentation |
| `py/docs/PYTHON_LIBRARY_PATTERNS.md` | SQLAlchemy patterns, Context DI, Params dataclasses |
| `py/docs/DATABASE.md` | Migrations, local setup, model patterns |
| `py/docs/SUCCESS_CRITERIA.md` | CI requirements, "done" definition |
| `py/docs/PACKAGE_SETUP.md` | Package scripts and tooling |
| `py/docs/CONTRIBUTING.md` | How to contribute |

### CLAUDE.md Files

Package-specific instructions for agents:

| Path | Purpose |
|------|---------|
| `CLAUDE.md` | Root project overview and key patterns |
| `py/apps/py-app/CLAUDE.md` | Python app specific patterns (if exists) |
| `ts/CLAUDE.md` | TypeScript specific patterns (if exists) |

## Quick Access

### Getting Started
- **New to the project?** Read `CLAUDE.md` first, then `docs/development/LOCAL.md`
- **Setting up deployment?** Start with `docs/setup/WALKTHROUGH.md`

### Common Tasks
- **Writing Python code?** Read `py/docs/PYTHON_LIBRARY_PATTERNS.md`
- **Working with database?** Read `py/docs/DATABASE.md`
- **Before creating a PR?** Check `py/docs/SUCCESS_CRITERIA.md`
- **Deploying changes?** Read `docs/deployment/KAMAL.md`

### Secrets & Infrastructure
- **Setting up secrets?** Read `docs/setup/ONE_PASSWORD.md`
- **Provisioning servers?** Read `docs/setup/INFRASTRUCTURE.md`
- **Terraform state?** Read `docs/setup/TERRAFORM_CLOUD.md`

## Usage

When the user asks for documentation help:

1. Identify what they're trying to do
2. Point them to the relevant doc(s)
3. Optionally read and summarize key sections

Examples:
- "How do I set up local dev?" -> `docs/development/LOCAL.md`
- "How do database migrations work?" -> `py/docs/DATABASE.md`
- "What checks need to pass for PR?" -> `py/docs/SUCCESS_CRITERIA.md`
- "How do I deploy?" -> `docs/deployment/KAMAL.md`
