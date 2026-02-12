# Multi-Tenancy Patterns

This guide describes how to implement multi-tenancy for SaaS applications.

## Overview

Multi-tenancy allows multiple isolated "tenants" (organizations, teams, workspaces) to share the same infrastructure while keeping their data separate. This is implemented via a `tenant_id` field - each resource belongs to a tenant, and users access resources through their tenant membership.

## Key Concepts

### Tenant Isolation Model

```
User -> Tenant -> Resource -> Data
```

- Users belong to one or more tenants
- Resources (threads, projects, etc.) are scoped to a tenant
- Authorization checks verify tenant membership, not direct ownership

### Single-Tenant Model (simpler)

```
User -> Resource -> Data
```

- Resources are directly owned by users
- Authorization checks verify user ownership
- Simpler, but doesn't support teams/organizations

## Implementation Patterns

### 1. Database Models

**Tenant Model:**

```python
class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid7_str)
    name: Mapped[str] = mapped_column(String, nullable=False)
    owner_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))

    members: Mapped[list["TenantMember"]] = relationship(...)
    threads: Mapped[list["Thread"]] = relationship(...)

class TenantMember(Base):
    __tablename__ = "tenant_members"

    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String)  # "owner", "editor", "viewer"
```

**Resource with tenant_id:**

```python
class Thread(Base):
    __tablename__ = "threads"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid7_str)

    # Tenant scope (for authorization)
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

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="threads")
```

**Key Points:**
- `tenant_id` is NOT NULL - every resource must belong to a tenant
- `user_id` is nullable - tracks creator but not used for authorization
- Foreign key cascade ensures resources are deleted when tenant is deleted

### 2. Context with Tenant

Pass tenant ID through the execution context:

```python
@dataclass
class Context:
    db: AsyncSession
    logger: Logger
    events: EventPublisher
    user_id: str      # Who triggered the action (for events/audit)
    tenant_id: str    # Tenant scope (for authorization)
```

### 3. Tenant-Scoped Operations

All operations filter by tenant:

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
        select(Thread).where(
            Thread.id == thread_id,
            Thread.tenant_id == tenant_id,  # Tenant authorization
        )
    )
    thread = result.scalar_one_or_none()
    if not thread:
        raise ThreadNotFound(f"Thread {thread_id} not found in tenant")
    return cls(thread)
```

### 4. API Layer Authorization

Authorization happens at the API layer:

```python
@router.get("/tenants/{tenant_id}/threads/{thread_id}")
async def get_thread(
    tenant_id: str,
    thread_id: str,
    ctx: ActingContext = Depends(require_tenant_access),
):
    # ctx.tenant_id verified by dependency
    return await load_thread(thread_id, ctx.tenant_id, ctx.db)
```

The `require_tenant_access` dependency:
1. Extracts user from JWT/session
2. Extracts tenant_id from route
3. Verifies user has permission on the tenant
4. Returns `ActingContext` with both `user_id` and `tenant_id`

## Migration Path

To add multi-tenancy to a single-tenant implementation:

### Step 1: Add Tenant Model

Create the tenant and membership tables.

### Step 2: Add tenant_id to Resources

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

Replace `user_id` authorization with `tenant_id`:

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

# After
@router.get("/tenants/{tenant_id}/threads/{thread_id}")
```

## Event Publishing

Events are still published to user channels (for real-time UI updates), but actions are authorized via tenant:

```python
# User receives events on their personal channel
await ctx.events.publish(
    ctx.user_id,
    ThreadStreamEvent(completion_id=ctx.completion_id, chunk=chunk),
)
```

For multi-user collaboration, also publish to tenant channels:

```python
# All tenant members receive updates
await ctx.events.publish_to_tenant(
    ctx.tenant_id,
    ThreadUpdatedEvent(thread_id=thread_id),
)
```

## Summary

| Aspect | Single-Tenant | Multi-Tenant |
|--------|---------------|--------------|
| Resource ownership | `user_id` | `tenant_id` |
| Authorization check | User owns resource | User has tenant access |
| Route structure | `/threads/{id}` | `/tenants/{tenant_id}/threads/{id}` |
| Context fields | `user_id` | `user_id` + `tenant_id` |
| Event channels | Per-user | Per-user + per-tenant |

**Key insight:** Tenant ID flows through every operation - from API auth to database queries to background tasks. This ensures complete isolation.
