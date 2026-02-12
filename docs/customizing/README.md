# Customizing the Template

This guide explains how to customize the generic template for your project.

**Quick start:** Run `/init` for interactive customization with Claude's guidance.

## Philosophy

This template is **fullstack by design**. Before removing features, consider:

1. **Keep what you don't need** - It's easier to ignore a feature than add it back later
2. **Features are integrated** - Database, jobs, auth work together out of the box
3. **Mix and match** - The py/ and ts/ stacks exist to combine, not to choose one

### Why not remove unused code?

- Removing code means losing tested integrations
- Future you might need that feature
- The "unused" code costs nothing if you don't call it
- It serves as documentation of patterns

### When to customize

**Focus on:**
- Project identity (name, domain, branding)
- Business logic (your actual app code)
- Extensions (multi-tenancy, new packages)

**Don't focus on:**
- Deleting stacks you "won't use"
- Removing features "to keep it simple"

## Customization Guides

| Guide | Description |
|-------|-------------|
| [Project Setup](project-setup.md) | Renaming, configuring .env.project, domains |
| [Turbo Monorepo](turbo-monorepo.md) | How turbo orchestrates TypeScript builds |
| [TypeScript Packages](typescript-packages.md) | ts-core pattern with subpath exports |
| [Python Packages](python-packages.md) | py-core library patterns |
| [Hybrid Stack](hybrid-stack.md) | Python API + TypeScript frontend |
| [Multi-Tenancy](multi-tenancy.md) | Tenant isolation for SaaS apps |

## Architecture Overview

The template is organized as a modular monorepo:

```
.
├── py/                   # Python stack (FastAPI + SQLAlchemy)
│   ├── apps/py-app/      # Main application
│   └── packages/py-core/ # Shared library
├── ts/                   # TypeScript stack (Vite + Express)
│   ├── apps/web/         # Vite SPA
│   ├── apps/api/         # Express API
│   └── packages/         # Shared packages
├── config/deploy/        # Kamal deployment configs
├── iac/                  # Terraform infrastructure
└── docs/                 # Documentation
```

Each stack is self-contained and can be used independently or together.

## Getting Help

- **Guided setup:** Run `/init` for interactive customization
- **Documentation:** Run `/docs` to navigate project docs
- **Issues:** Check `issues/` for known issues and TODOs
