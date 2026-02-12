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
  └── /app/*      → Serves SPA index.html (Vite build)
        └── SPA loads → fetch('/api/v0/...') for data
```

The Python server:
1. Handles all API requests
2. Serves the built SPA for frontend routes
3. Manages WebSocket connections for real-time features

## Setup Steps

### 1. Configure Vite Output

In `ts/apps/web/vite.config.ts`:

```typescript
export default defineConfig({
  build: {
    outDir: '../../py/apps/py-app/static/app',
    emptyOutDir: true,
  },
});
```

### 2. Configure API Proxy (Development)

For local development, proxy API requests to Python:

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

### 3. Serve SPA from Python

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

### 4. API-Only Python

Remove Jinja2 templates - return JSON instead:

```python
# Before (server-rendered)
@router.get("/threads/{id}")
async def get_thread(id: str):
    return templates.TemplateResponse("thread.html", {"thread": thread})

# After (API-only)
@router.get("/api/v0/threads/{id}")
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

### Development

Run both servers:

```bash
# Terminal 1: Python
cd py && make dev

# Terminal 2: TypeScript with proxy
cd ts && pnpm dev --filter=web
```

Or use tmux (from root):

```bash
make dev
```

### Production Build

1. Build TypeScript to Python's static directory
2. Build Python Docker image (includes SPA)
3. Deploy single container

```dockerfile
# Dockerfile
FROM node:20 AS frontend
WORKDIR /app/ts
COPY ts/ .
RUN pnpm install && pnpm build --filter=web

FROM python:3.12
WORKDIR /app
COPY --from=frontend /app/py/apps/py-app/static/app ./static/app
COPY py/ .
CMD ["uvicorn", "src.main:app"]
```

## File Structure

```
py/
├── apps/py-app/
│   ├── src/
│   │   ├── api/          # JSON API routes
│   │   └── main.py       # FastAPI app + SPA serving
│   └── static/
│       └── app/          # Built SPA (from Vite)

ts/
├── apps/web/
│   ├── src/
│   │   ├── api/          # API client
│   │   ├── components/   # React components
│   │   └── App.tsx
│   └── vite.config.ts    # Output to py-app/static/app
```

## Related Documentation

- `docs/development/MIXING_LANGUAGES.md` - When to use HTMX vs SPA
- [TypeScript Packages](typescript-packages.md) - Shared type patterns
- [Turbo Monorepo](turbo-monorepo.md) - Build orchestration
