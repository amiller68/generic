# Multi-Tenancy Patterns

This document describes how to implement multi-tenancy in the chat system.

## Overview

Multi-tenancy allows multiple isolated "tenants" (organizations, teams, workspaces) to share the same infrastructure while keeping their data separate. This is implemented via a `tenant_id` field - each thread belongs to a tenant, and users access threads through their tenant membership.

## Key Concepts

### Tenant Isolation Model

```
User -> Tenant -> Thread -> Messages/Completions
```

- Users belong to one or more tenants
- Threads are scoped to a tenant, not directly to a user
- Authorization checks verify tenant membership, not direct ownership

### Single-Tenant Model (simpler)

```
User -> Thread -> Messages/Completions
```

- Threads are directly owned by users
- Authorization checks verify user ownership

## Implementation Patterns

### 1. Database Models

**Thread Model with tenant_id:**

```python
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Thread(Base):
    __tablename__ = "threads"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid7()))

    # Tenant scope
    tenant_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # User who created (for audit, not authorization)
    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="threads")
    messages: Mapped[list["Message"]] = relationship(...)
    completions: Mapped[list["Completion"]] = relationship(...)
```

**Key Points:**
- `tenant_id` is NOT NULL - every thread must belong to a tenant
- `user_id` is nullable - tracks creator but not used for authorization
- Foreign key cascade ensures threads are deleted when tenant is deleted

### 2. Engine Context

Pass tenant ID through the entire execution context:

```python
@dataclass
class EngineContext:
    """Runtime dependencies for the engine."""

    db: AsyncSession
    logger: Logger
    events: EventPublisher
    redis: Redis
    user_id: str        # Who triggered the action (for events)
    tenant_id: str      # Tenant scope (for authorization)
    completion_id: str
```

### 3. ThreadManager

All thread operations are scoped by tenant:

```python
@classmethod
async def load(
    cls,
    db: AsyncSession,
    thread_id: str,
    tenant_id: str,  # Tenant scope, NOT user_id
) -> "ThreadManager":
    """Load a thread scoped to a tenant."""
    result = await db.execute(
        select(ThreadModel).where(
            ThreadModel.id == thread_id,
            ThreadModel.tenant_id == tenant_id,  # Tenant authorization
        )
    )
    thread = result.scalar_one_or_none()
    if not thread:
        raise ThreadNotFound(f"Thread {thread_id} not found in tenant")
    # ...

@classmethod
async def create(
    cls,
    db: AsyncSession,
    user_id: str,
    tenant_id: str,  # Required tenant scope
    parts: list[ContentPart],
) -> tuple["ThreadManager", Completion]:
    """Create a thread within a tenant."""
    thread = ThreadModel(
        user_id=user_id,      # Creator (audit)
        tenant_id=tenant_id,  # Tenant (authorization)
    )
    # ...
```

### 4. Cancel Flow

Cancel uses tenant scope, not user scope:

```python
@dataclass
class CancelParams:
    thread_id: str
    tenant_id: str     # Tenant scope
    ttl_seconds: int = 60

async def request_cancel(params: CancelParams, ctx: Context) -> CancelResult:
    # Query scoped to tenant
    result = await ctx.db.execute(
        select(Thread, Completion)
        .outerjoin(
            Completion,
            (Completion.thread_id == Thread.id)
            & Completion.status.in_([CompletionStatus.PENDING, CompletionStatus.PROCESSING]),
        )
        .where(
            Thread.id == params.thread_id,
            Thread.tenant_id == params.tenant_id,  # Tenant authorization
        )
    )
    # ...
```

### 5. API Layer Authorization

Authorization happens at the API layer before calling operations:

```python
async def handler(
    thread_id: str,
    acting_ctx: ActingContext = Depends(require_tenant_access),
    db: AsyncSession = Depends(db_session),
    redis_client: Redis = Depends(redis),
) -> CancelResponse:
    params = CancelParams(
        thread_id=thread_id,
        tenant_id=acting_ctx.tenant_id,  # From auth context
    )
    # ...
```

The `require_tenant_access` dependency:
1. Extracts user from JWT/session
2. Extracts tenant_id from route (e.g., `/tenants/{tenant_id}/threads/{thread_id}`)
3. Verifies user has permission on the tenant
4. Returns `ActingContext` with both `user_id` and `tenant_id`

## Migration Path

To add multi-tenancy to a single-tenant implementation:

### Step 1: Add Tenant Model

```python
class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    owner_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))

    # Relationships
    members: Mapped[list["TenantMember"]] = relationship(...)
    threads: Mapped[list["Thread"]] = relationship(...)

class TenantMember(Base):
    __tablename__ = "tenant_members"

    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String)  # "owner", "editor", "viewer"
```

### Step 2: Add tenant_id to Thread

```sql
-- Migration
ALTER TABLE threads ADD COLUMN tenant_id VARCHAR REFERENCES tenants(id);

-- For existing data, create a "personal" tenant per user
INSERT INTO tenants (id, name, owner_id)
SELECT gen_random_uuid(), 'Personal', user_id
FROM (SELECT DISTINCT user_id FROM threads) t;

-- Update threads to point to personal tenants
UPDATE threads t
SET tenant_id = (SELECT id FROM tenants WHERE owner_id = t.user_id LIMIT 1);

-- Make non-nullable
ALTER TABLE threads ALTER COLUMN tenant_id SET NOT NULL;
```

### Step 3: Update Operations

Replace all `user_id` authorization with `tenant_id`:

```python
# Before (single-tenant)
ThreadManager.load(db, thread_id, user_id)

# After (multi-tenant)
ThreadManager.load(db, thread_id, tenant_id)
```

### Step 4: Update API Routes

Change routes from user-scoped to tenant-scoped:

```python
# Before
@router.get("/threads/{thread_id}")
async def get_thread(thread_id: str, user: User = Depends(require_user)):
    ...

# After
@router.get("/tenants/{tenant_id}/threads/{thread_id}")
async def get_thread(
    tenant_id: str,
    thread_id: str,
    ctx: ActingContext = Depends(require_tenant_access),
):
    ...
```

## Event Publishing

Events are still published to user channels (for real-time UI updates), but the action is authorized via tenant:

```python
# User receives events on their personal channel
await self.ctx.events.publish(
    self.ctx.user_id,  # Publish to user who triggered
    ThreadStreamEvent(completion_id=self.ctx.completion_id, chunk=chunk),
)
```

For multi-user collaboration, you might also publish to a tenant channel:

```python
# All tenant members receive updates
await self.ctx.events.publish_to_tenant(
    self.ctx.tenant_id,
    ThreadUpdatedEvent(thread_id=thread_id),
)
```

## Summary

| Aspect | Single-Tenant | Multi-Tenant |
|--------|---------------|--------------|
| Thread ownership | `user_id` | `tenant_id` |
| Authorization check | User owns thread | User has tenant access |
| Route structure | `/threads/{id}` | `/tenants/{tenant_id}/threads/{id}` |
| Context fields | `user_id` | `user_id` + `tenant_id` |
| Event channels | Per-user | Per-user + per-tenant |

The key insight: **tenant ID flows through every operation** - from API auth to database queries to background tasks. This ensures complete isolation.
