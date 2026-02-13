# Mixing Languages: Python + TypeScript

This project supports both Python (FastAPI) and TypeScript (Next.js/Vite) as separate project roots. This guide covers when to use each and how to combine them.

## When to Use HTMX/HATEOAS (Python)

Server-rendered HTML with HTMX is the default for most pages:

- **Admin pages** - CRUD interfaces, data tables, forms
- **Home/landing pages** - Marketing, public content
- **Login/auth screens** - OAuth flows, session management
- **Settings pages** - User preferences, account management
- **Content-heavy pages** - Blog posts, documentation, help

The Python stack (`py/`) uses FastAPI + Jinja2 + HTMX + Tailwind CSS. Pages are server-rendered with progressive enhancement via HTMX for interactivity.

## When to Reach for a Vite SPA (TypeScript)

Some UIs genuinely need client-side state management:

- **Complex stateful UIs** - Multi-step wizards, form builders
- **Drag-and-drop** - Kanban boards, file upload, reordering
- **Real-time visualization** - Charts, graphs, live dashboards
- **WebSocket-driven features** - Chat, collaborative editing
- **Rich text editors** - WYSIWYG, code editors

## Architecture: Embedding a SPA in Python

When you need a TypeScript SPA for specific routes:

1. **Vite builds to `py-app/static/app/`** - The TypeScript app compiles to static assets
2. **Python serves the SPA** - A catch-all route at `/app/*` serves the SPA's `index.html`
3. **SPA calls Python API endpoints** - The TypeScript app uses `fetch()` to call `/api/v0/*`

```
Browser → Python (FastAPI)
  ├── /           → Server-rendered HTML (Jinja2 + HTMX)
  ├── /login      → Server-rendered HTML
  ├── /api/v0/*   → JSON API endpoints
  └── /app/*      → Serves SPA index.html (Vite build)
        └── SPA loads → fetch('/api/v0/...') for data
```

## Build Tools

The repo provides native tooling for cross-language development:

- **pnpm + Turbo** manages TypeScript packages and dependency graph traversal
- **uv workspaces** manages Python packages
- **Makefile** at root orchestrates both with `make dev`, `make build`, etc.
- **Dockerfile** handles multi-stage builds (TypeScript assets first, then Python)
