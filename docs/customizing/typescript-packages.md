# TypeScript Packages

This guide describes patterns for shared TypeScript packages, using `ts-core` as the model architecture.

## Package Structure

A well-organized shared package separates concerns into submodules:

```
packages/ts-core/
├── src/
│   ├── index.ts      # Main exports
│   ├── core/         # Domain primitives
│   │   ├── index.ts
│   │   └── types.ts
│   ├── api/          # Request/response contracts
│   │   ├── index.ts
│   │   └── types.ts
│   └── events/       # WebSocket/SSE payloads
│       ├── index.ts
│       └── types.ts
├── package.json
└── tsconfig.json
```

### Core Types

Domain primitives that define your business entities:

```typescript
// core/types.ts
export interface User {
  id: string;
  email: string;
  name: string;
  createdAt: Date;
}

export interface Thread {
  id: string;
  userId: string;
  title: string;
  status: ThreadStatus;
}

export type ThreadStatus = 'active' | 'archived' | 'deleted';
```

### API Types

Request and response contracts for HTTP endpoints:

```typescript
// api/types.ts
import { User, Thread } from '../core';

// Request types
export interface CreateThreadRequest {
  title: string;
  initialMessage?: string;
}

// Response types
export interface ThreadResponse {
  thread: Thread;
  messageCount: number;
}

export interface ListThreadsResponse {
  threads: Thread[];
  total: number;
  hasMore: boolean;
}
```

### Event Types

Payloads for real-time communication (WebSockets, SSE):

```typescript
// events/types.ts
export interface ThreadStreamEvent {
  type: 'chunk' | 'complete' | 'error';
  completionId: string;
  data?: string;
  error?: string;
}

export interface ThreadUpdatedEvent {
  type: 'thread_updated';
  threadId: string;
  changes: Partial<Thread>;
}
```

## Subpath Exports

Enable importing from specific submodules:

```json
// package.json
{
  "name": "@repo/ts-core",
  "exports": {
    ".": {
      "import": "./dist/index.js",
      "types": "./dist/index.d.ts"
    },
    "./core": {
      "import": "./dist/core/index.js",
      "types": "./dist/core/index.d.ts"
    },
    "./api": {
      "import": "./dist/api/index.js",
      "types": "./dist/api/index.d.ts"
    },
    "./events": {
      "import": "./dist/events/index.js",
      "types": "./dist/events/index.d.ts"
    }
  }
}
```

Usage:

```typescript
// Import everything
import { User, CreateThreadRequest, ThreadStreamEvent } from '@repo/ts-core';

// Import specific modules
import { User, Thread } from '@repo/ts-core/core';
import { CreateThreadRequest } from '@repo/ts-core/api';
import { ThreadStreamEvent } from '@repo/ts-core/events';
```

## Building Packages

Use [bunchee](https://github.com/huozhi/bunchee) for zero-config bundling:

```json
{
  "scripts": {
    "build": "bunchee",
    "dev": "bunchee --watch"
  }
}
```

Bunchee automatically:
- Generates ESM and CJS outputs
- Creates TypeScript declarations
- Handles subpath exports

## Using in Apps

Add as workspace dependency:

```json
// apps/web/package.json
{
  "dependencies": {
    "@repo/ts-core": "workspace:*"
  }
}
```

Turbo ensures the package builds before the app.

## Type Safety Across Boundaries

### Frontend to API

```typescript
// Frontend code
import { CreateThreadRequest, ThreadResponse } from '@repo/ts-core/api';

async function createThread(data: CreateThreadRequest): Promise<ThreadResponse> {
  const res = await fetch('/api/threads', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return res.json();
}
```

### WebSocket Events

```typescript
// Frontend event handler
import { ThreadStreamEvent } from '@repo/ts-core/events';

socket.onmessage = (event) => {
  const data: ThreadStreamEvent = JSON.parse(event.data);
  switch (data.type) {
    case 'chunk':
      appendChunk(data.data);
      break;
    case 'complete':
      finishStream();
      break;
  }
};
```

## Existing Packages

The template includes these packages:

| Package | Purpose |
|---------|---------|
| `@repo/http-api` | Express API utilities, request building |
| `@repo/typescript-config` | Shared tsconfig presets |

Add more packages as your domain grows:
- `@repo/ts-core` - Domain types
- `@repo/ui` - Shared React components
- `@repo/utils` - Common utilities
