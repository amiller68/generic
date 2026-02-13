# Python Library Patterns

This document describes the architectural patterns and conventions for Python libraries in this project. Follow these patterns when adding new functionality or modifying existing code in any Python package.

**Applies to:**
- `py/packages/py-core` - Core domain operations and database persistence
- `py/apps/py-app` - FastAPI application layer
- Any new Python packages

## Overview

Our Python architecture follows a **functional-first design** with clear separation between data models and business operations. Key components include:

- **Database persistence** - SQLAlchemy ORM models (data containers only)
- **Domain operations** - Functional async operations with explicit dependencies
- **Infrastructure services** - Events, tasks, storage, observability

## Core Principles

1. **Database models are data containers only** - no business logic
2. **Library operations are pure functions** - explicit inputs/outputs, no hidden state
3. **Dependencies are injected via Context** - never accessed globally
4. **Composition over inheritance** - operations call other operations

---

## Database Models vs Library Operations

### Database Models

**Location:** `py_core/database/models/`

Database models are SQLAlchemy ORM classes that define table structure. They contain:
- Column definitions with type hints
- Constraints and indexes
- **No business logic**

```python
# Example: database/models/entity.py
class Entity(Base):
    """Database entity. No methods, just columns."""

    __tablename__ = "entities"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), nullable=False, index=True
    )
    status: Mapped[EntityStatus] = mapped_column(
        PgEnum(EntityStatus), default=EntityStatus.PENDING
    )
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    __table_args__ = (
        CheckConstraint("id ~ '^ent_[A-Za-z0-9]+$'", name="ck_entities_id_format"),
    )
```

**Key patterns:**
- Use `Mapped[T]` and `mapped_column()` for type-safe columns
- Use `PgEnum` for enum columns (see CLAUDE.md for usage)
- Define constraints in `__table_args__`
- Use uuid7 for IDs (see `py_core.database.utils.uuid7_str`)

### Library Operations

**Location:** Domain-specific modules like `entity/`, `feature/`, `library/`, `search/`

Library operations are **async functions** that implement business logic. They follow this signature:

```python
async def operation_name(params: Params, ctx: Context) -> Result
```

```python
# Example: entity/create.py
async def create_entity(entity: Entity, ctx: Context) -> Entity:
    """
    Persist an Entity to the database.

    This is idempotent - creating the same entity twice is safe.
    """
    entity_id = entity.id

    # Insert entity (idempotent - ignore conflicts)
    stmt = (
        insert(DbEntity)
        .values(id=entity_id, user_id=entity.user_id, data=entity.data)
        .on_conflict_do_nothing(index_elements=["id"])
    )
    await ctx.db.execute(stmt)
    await ctx.db.flush()
    ctx.logger.debug(f"Created entity {entity_id}")

    return entity
```

**Key patterns:**
- Functions are **stateless** - all state passed via parameters
- Functions are **idempotent** where possible (use `on_conflict_do_nothing`)
- Access dependencies only through `ctx` parameter
- Return the same type or a defined `Result` dataclass

---

## Dependency Injection with Context

Every operation receives dependencies via a `Context` dataclass. Dependencies are **never accessed globally**.

### Defining Context

Each module defines its own `_context.py`:

```python
# Example: entity/_context.py
from dataclasses import dataclass
from py_core.observability import Logger
from sqlalchemy.ext.asyncio import AsyncSession

@dataclass
class Context:
    db: AsyncSession
    logger: Logger
```

### Standard Dependencies

| Dependency | Type | Purpose |
|------------|------|---------|
| `db` | `AsyncSession` | Database operations |
| `logger` | `Logger` | Structured logging |
| `storage` | `Storage` | File storage (S3/MinIO) |

### Using Context in Operations

```python
async def search_library(params: Params, ctx: Context) -> list[SearchResult]:
    # Access database through context
    result = await ctx.db.execute(query)

    # Access logger through context
    ctx.logger.debug(f"Search returned {len(results)} items")

    return results
```

### Nested Context for Sub-Operations

When an operation calls another operation, create a new context:

```python
# In library/import_file.py
async def import_to_library(params: Params, ctx: Context) -> Result:
    # Create contexts for sub-operations
    feature_ctx = FeatureContext(db=ctx.db, logger=ctx.logger)
    entity_ctx = EntityContext(db=ctx.db, logger=ctx.logger)

    # Call sub-operations with their contexts
    for feature in features:
        await create_feature(feature, feature_ctx)
    await create_entity(entity, entity_ctx)
```

---

## Designing Params for Extensibility

The `Params` dataclass pattern is critical for building extensible library methods. Params should be designed so new functionality can be added without breaking existing callers.

### Why Use Params Instead of Direct Arguments

**Don't do this:**
```python
# Fragile - adding parameters breaks all callers
async def search_library(
    user_id: str,
    query: str | None,
    status: str | None,
    min_score: int,
    ctx: Context,
) -> list[SearchResult]:
    ...
```

**Do this instead:**
```python
# Extensible - new fields with defaults don't break callers
@dataclass
class Params:
    user_id: str                        # Required: always first
    query: str | None = None            # Optional with sensible default
    status: str | None = None           # Optional filter
    min_score: int = 60                 # Optional with sensible default
    include_archived: bool = False      # Easy to add later

async def search_library(params: Params, ctx: Context) -> list[SearchResult]:
    ...
```

### Params Design Rules

1. **Required fields first, optional fields with defaults after**
   ```python
   @dataclass
   class Params:
       user_id: str                     # Required - no default
       target_id: str                   # Required - no default
       target_type: str = "default"     # Optional - has default
       max_depth: int = 5               # Optional - has default
       options: list[str] | None = None # Optional - None means "use defaults"
   ```

2. **Use `None` to mean "use system defaults"**
   ```python
   @dataclass
   class Params:
       options: list[str] | None = None  # None = use DEFAULT_OPTIONS constant
       settings: dict | None = None      # None = auto-infer
   ```

   Then in the operation:
   ```python
   options = params.options or DEFAULT_OPTIONS
   settings = params.settings or infer_settings()
   ```

3. **Boolean flags default to the safe/common case**
   ```python
   @dataclass
   class Params:
       include_archived: bool = False  # Default: don't include archived
       validate_inputs: bool = True    # Default: do validate
       dry_run: bool = False           # Default: actually execute
   ```

### Adding New Features Without Breaking Callers

When you need to add new functionality:

```python
# BEFORE: existing Params
@dataclass
class Params:
    user_id: str
    query: str | None = None
    min_score: int = 60

# AFTER: add new optional fields with defaults
@dataclass
class Params:
    user_id: str
    query: str | None = None
    min_score: int = 60
    # NEW: added without breaking existing callers
    include_archived: bool = False
    limit: int | None = None  # None = no limit
```

Existing callers continue to work:
```python
# Old code still works
params = Params(user_id="user123", query="search")

# New code can use new features
params = Params(user_id="user123", query="search", include_archived=True, limit=50)
```

### Params vs Direct Arguments: When to Use Each

**Use Params dataclass when:**
- Operation has 3+ parameters
- Operation is likely to gain new parameters over time
- Operation is called from multiple places (API, tasks, tests)
- You want explicit documentation of all options

**Use direct arguments when:**
- Operation has 1-2 simple parameters that won't change
- Operation is internal/private (prefixed with `_`)
- The domain type already encapsulates the input (e.g., `create_entity(entity, ctx)`)

```python
# Direct args OK - simple, stable interface
async def read_entity(entity_id: str, ctx: Context) -> Entity | None:
    ...

# Direct args OK - domain type is the input
async def create_feature(feature: Feature, ctx: Context) -> Feature:
    ...

# Params needed - complex, likely to evolve
async def search_library(params: Params, ctx: Context) -> list[SearchResult]:
    ...
```

### Result Dataclasses

Similarly, use explicit `Result` dataclasses for complex return values:

```python
@dataclass
class Result:
    """Result of import_to_library operation."""
    entity_id: str      # Primary result
    related_id: str     # Related entity ID
    name: str           # Metadata for confirmation
    # Easy to add more fields later without breaking callers
```

This allows adding new return fields without changing the function signature.

---

## Purely Functional Operations

Operations should be **pure functions** where possible:

### Do

- Pass all inputs explicitly via `params` or direct arguments
- Pass all dependencies via `ctx`
- Return explicit outputs (dataclass or domain type)
- Use helper functions prefixed with `_` for internal transformations

### Don't

- Access global state or singletons
- Store state in class instances
- Use implicit configuration
- Mutate input parameters

### Helper Functions

Pure helper functions are prefixed with `_` and kept in the same file:

```python
# Example: library/search.py

# Public async operation
async def search_library(params: Params, ctx: Context) -> list[SearchResult]:
    for item, entity in rows:
        status = _normalize_status(entity.status)
        ...

# Private sync helper (pure transformation)
def _normalize_status(status) -> str:
    """Convert DB status enum to lowercase string."""
    status_str = status.value if hasattr(status, "value") else str(status)
    return status_str.lower()

# Private async helper (still receives db explicitly)
async def _get_entity_features(
    db: AsyncSession, entity_id: str
) -> list[tuple[str, str | None, str]]:
    """Get features for an entity as (id, label, type) tuples."""
    query = select(Feature.id, Feature.label, Feature.type)...
    result = await db.execute(query)
    return [(row[0], row[1], row[2]) for row in result.all()]
```

---

## Module Organization

Each entity module follows this structure:

```
module_name/
├── __init__.py      # Public API re-exports
├── _context.py      # Context dataclass for DI
├── types.py         # Business types
├── create.py        # Persistence operation
├── read.py          # Retrieval operation
└── [other_ops].py   # Additional operations as needed
```

### Public API via `__init__.py`

```python
# Example: entity/__init__.py
from ._context import Context
from .types import Entity, EntityType
from .create import create_entity
from .read import read_entity

__all__ = [
    "Context",
    "Entity",
    "EntityType",
    "create_entity",
    "read_entity",
]
```

### Usage

```python
# Import the module
from py_core import entity

# Use operations via module
ctx = entity.Context(db=session, logger=logger)
await entity.create_entity(my_entity, ctx)
```

---

## Quick Reference

| Pattern | Location | Example |
|---------|----------|---------|
| Database model | `database/models/` | `class Entity(Base)` |
| Context definition | `module/_context.py` | `@dataclass class Context` |
| Create operation | `module/create.py` | `async def create_X(x, ctx)` |
| Read operation | `module/read.py` | `async def read_X(id, ctx)` |
| Params dataclass | Same file as operation | `@dataclass class Params` |
| Result dataclass | Same file as operation | `@dataclass class Result` |
| Private helper | Same file, `_` prefix | `def _normalize_X()` |

### Operation Signature Pattern

```python
async def operation_name(
    params: Params,    # or direct args for simple ops
    ctx: Context,
) -> Result:          # or domain type
    """
    One-line description.

    Longer explanation if needed.
    """
    # Implementation
    return result
```

### Checklist for New Operations

- [ ] Define `Context` in `_context.py` (or reuse existing)
- [ ] Define `Params` dataclass if operation has 3+ inputs or may evolve
- [ ] Put required fields first, optional fields with defaults after
- [ ] Use `None` for optional params that have system defaults
- [ ] Define `Result` dataclass if returning structured data
- [ ] Use `async def` for all database operations
- [ ] Access dependencies only via `ctx`
- [ ] Make operations idempotent where possible
- [ ] Add to `__all__` in `__init__.py`

### Params Design Checklist

- [ ] Required params have no defaults
- [ ] Optional params have sensible defaults
- [ ] Boolean flags default to the safe/common behavior
- [ ] `None` means "use system default" (not "disabled")
- [ ] Related params are grouped with comments
- [ ] Docstring explains each field's purpose
