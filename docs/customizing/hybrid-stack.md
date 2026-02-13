# Hybrid Stack

This guide covers combining Python (FastAPI) backend with TypeScript (Vite/React) frontend.

## When to Use Hybrid

Best for complex apps needing:
- Python's data/ML capabilities (pandas, numpy, pydantic-ai)
- Modern React frontend with rich interactivity
- Real-time features with type-safe events

## Architecture

```
Browser → Python (FastAPI)
  ├── /api/v0/*   → JSON API endpoints
  ├── /_status/*  → Health checks, metrics (livez, readyz, versionz)
  ├── /_admin/*   → Server-rendered admin pages (Jinja2 + HTMX)
  └── /app/*      → Serves SPA index.html (Vite build)
        └── SPA loads → fetch('/api/v0/...') for data
```

The Python server:
1. Handles all API requests (`/api/v0/*`)
2. Serves health/status endpoints for infrastructure (`/_status/*`)
3. Serves admin pages with server-rendering (`/_admin/*`)
4. Serves the built SPA for user-facing routes (`/app/*`)
5. Manages WebSocket connections for real-time features

### Why Keep Server-Rendered Routes?

Even in a hybrid setup, some pages are better server-rendered:

**`/_status/*` - Health & Monitoring**
- `/livez` - Kubernetes liveness probe
- `/readyz` - Kubernetes readiness probe
- `/versionz` - Build info, git sha, deploy timestamp
- No JS required, instant response, infrastructure-friendly

**`/_admin/*` - Internal Admin Pages**
- CRUD interfaces, data tables, forms
- Simpler than building admin in React
- HTMX for interactivity without SPA complexity
- Can reuse existing Jinja2 templates

## Setup Steps

### 1. Configure Vite Output

In `packages/ts-web/vite.config.ts`:

```typescript
export default defineConfig({
  build: {
    outDir: '../../apps/py-platform/static/app',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/_status': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

### 2. Serve SPA from Python

Add a catch-all route in FastAPI:

```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Mount static assets
app.mount("/app/assets", StaticFiles(directory="static/app/assets"))

# Catch-all for SPA routes
@app.get("/app/{path:path}")
async def spa_catchall(path: str):
    return FileResponse("static/app/index.html")
```

### 4. Status Router

Add health check endpoints for infrastructure:

```python
# src/routes/_status.py
from fastapi import APIRouter

router = APIRouter(prefix="/_status", tags=["status"])

@router.get("/livez")
async def livez():
    return {"status": "ok"}

@router.get("/readyz")
async def readyz(db: AsyncSession = Depends(get_db)):
    # Check database connection
    await db.execute(text("SELECT 1"))
    return {"status": "ok"}

@router.get("/versionz")
async def versionz():
    return {
        "version": os.getenv("APP_VERSION", "dev"),
        "git_sha": os.getenv("GIT_SHA", "unknown"),
    }
```

### 5. Admin Router

Keep Jinja2 for admin pages:

```python
# src/routes/_admin.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/_admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin/dashboard.html", {"request": request})

@router.get("/users", response_class=HTMLResponse)
async def admin_users(request: Request, db: AsyncSession = Depends(get_db)):
    users = await db.execute(select(User))
    return templates.TemplateResponse("admin/users.html", {
        "request": request,
        "users": users.scalars().all(),
    })
```

### 6. API-Only for User-Facing Features

For SPA-consumed endpoints, return JSON (no templates):

```python
# src/routes/api/v0/threads.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v0/threads", tags=["threads"])

@router.get("/{id}")
async def get_thread(id: str) -> ThreadResponse:
    return ThreadResponse(thread=thread, messages=messages)
```

## Shared Types

### Option 1: OpenAPI Generation

FastAPI auto-generates OpenAPI specs. Use a generator to create TypeScript types:

```bash
# Generate TypeScript types from OpenAPI
npx openapi-typescript http://localhost:8000/openapi.json -o src/api/types.ts
```

### Option 2: Manual Type Mirroring

Maintain parallel types in both languages:

```python
# Python (Pydantic)
class ThreadResponse(BaseModel):
    id: str
    title: str
    status: ThreadStatus
    message_count: int
```

```typescript
// TypeScript
interface ThreadResponse {
  id: string;
  title: string;
  status: ThreadStatus;
  messageCount: number;
}
```

## Real-Time Features

### WebSocket Events

Python sends events:

```python
await websocket.send_json({
    "type": "chunk",
    "completion_id": completion.id,
    "data": chunk.text,
})
```

TypeScript receives:

```typescript
import { ThreadStreamEvent } from '@repo/ts-core/events';

socket.onmessage = (event) => {
  const data: ThreadStreamEvent = JSON.parse(event.data);
  handleEvent(data);
};
```

### SSE Alternative

For simpler real-time needs, use Server-Sent Events:

```python
from fastapi.responses import StreamingResponse

@router.get("/api/v0/threads/{id}/stream")
async def stream_thread(id: str):
    async def generate():
        async for chunk in engine.stream():
            yield f"data: {json.dumps(chunk)}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

## Build Pipeline

### Unified Turbo Workspace

The hybrid stack uses a single turbo workspace that orchestrates both Python and TypeScript:

```
app/
├── turbo.json           # Orchestrates all packages
├── package.json         # Root scripts: dev, build, test
├── pyproject.toml       # Python workspace config
├── pnpm-workspace.yaml  # Includes apps/* and packages/*
├── apps/
│   └── py-platform/     # FastAPI app (@app/py-platform)
└── packages/
    ├── py-core/         # Python library (@app/py-core)
    ├── py-database/     # Python database (@app/py-database)
    ├── ts-web/          # Vite SPA (@app/ts-web)
    └── ts-core/         # TypeScript types (@app/ts-core)
```

### Development

Single command runs everything:

```bash
pnpm dev
```

This runs:
- `setup` tasks first (database migrations, etc.)
- Python API server (`py-platform`)
- Python worker and scheduler
- TypeScript dev server (`ts-web`)

Turbo handles the dependency graph - TypeScript packages build before the SPA starts, setup runs before dev servers.

### turbo.json Configuration

```json
{
  "tasks": {
    "dev": {
      "dependsOn": ["^setup"],
      "cache": false,
      "persistent": true
    },
    "dev#@app/ts-web": {
      "cache": false,
      "persistent": true
    },
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", "../py-platform/static/app/**"]
    }
  }
}
```

Key patterns:
- `^setup` ensures database/services ready before dev
- `persistent: true` for long-running dev servers
- Build outputs TypeScript to Python's static directory

### Production Build

Single Dockerfile builds both stacks:

```dockerfile
FROM node:20 AS frontend
WORKDIR /app
COPY . .
RUN pnpm install && pnpm build

FROM python:3.12
WORKDIR /app
COPY --from=frontend /app .
CMD ["uvicorn", "apps.py-platform.src.main:app"]
```

## File Structure

```
app/
├── turbo.json
├── package.json
├── pyproject.toml
├── pnpm-workspace.yaml
├── apps/
│   └── py-platform/              # FastAPI application
│       ├── src/
│       │   ├── routes/
│       │   │   ├── _status.py    # /_status/* health checks
│       │   │   ├── _admin.py     # /_admin/* server-rendered
│       │   │   └── api/
│       │   │       └── v0/       # /api/v0/* JSON endpoints
│       │   └── main.py           # FastAPI app + SPA serving
│       ├── templates/
│       │   └── admin/            # Jinja2 templates for admin
│       └── static/
│           └── app/              # Built SPA (from ts-web)
└── packages/
    ├── py-core/                  # Python shared library
    ├── py-database/              # Database models, migrations
    ├── ts-web/                   # Vite SPA (React)
    │   ├── src/
    │   │   ├── api/              # API client
    │   │   ├── components/       # React components
    │   │   └── App.tsx
    │   └── vite.config.ts        # Outputs to py-platform/static/app
    └── ts-core/                  # Shared TypeScript types
```

### Package Naming Convention

| Prefix | Language | Example |
|--------|----------|---------|
| `py-*` | Python | `@app/py-core`, `@app/py-database` |
| `ts-*` | TypeScript | `@app/ts-web`, `@app/ts-core` |

### Route Prefix Conventions

| Prefix | Purpose | Rendering |
|--------|---------|-----------|
| `/api/v0/*` | User-facing API | JSON |
| `/_status/*` | Health/monitoring | JSON (no auth) |
| `/_admin/*` | Internal admin | Jinja2 + HTMX |
| `/app/*` | User-facing UI | SPA (Vite build) |

The underscore prefix (`_status`, `_admin`) signals internal/infrastructure routes.

## Related Documentation

- [Turbo Monorepo](turbo-monorepo.md) - Build orchestration details
- [TypeScript Packages](typescript-packages.md) - Shared type patterns
- [Python Packages](python-packages.md) - py-core library patterns
