---
description: Manage Python database migrations. Use when modifying SQLAlchemy models, creating migrations, or applying schema changes.
allowed-tools:
  - Bash(make:*)
  - Bash(cd:*)
  - Bash(cat:*)
  - Bash(ls:*)
  - Bash(git diff:*)
  - Bash(git status:*)
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

Manage database schema changes through Alembic migrations for the Python project.

## Quick Reference

```bash
# From py/ directory
make setup              # Start Postgres + Redis, run migrations, seed
make db-migrate         # Apply pending migrations
make db-prepare MSG="description"  # Auto-generate migration from model changes

# Manual migration (for data migrations)
MANUAL=1 make db-prepare MSG="migrate legacy data"
```

## Workflow: Adding or Modifying Models

### 1. Modify the Model

Edit or create models in `py/packages/py-core/src/py_core/database/models/`:

```python
from sqlalchemy.orm import Mapped, mapped_column
from py_core.database.utils import uuid7_str, utcnow, StringEnum

class MyModel(Base):
    __tablename__ = "my_models"

    id: Mapped[str] = mapped_column(primary_key=True, default=uuid7_str)
    name: Mapped[str] = mapped_column()
    status: Mapped[MyStatus] = mapped_column(StringEnum(MyStatus), default=MyStatus.DRAFT)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
```

### 2. Register the Model

If creating a new model, add it to `py/packages/py-core/src/py_core/database/models/__init__.py`:

```python
from .my_model import MyModel
```

### 3. Generate the Migration

```bash
cd py
make db-prepare MSG="add my_models table"
```

This auto-generates a migration by comparing your models to the current database schema.

### 4. Review the Migration

**Always review generated migrations before applying.** Check:

```bash
cat py/packages/py-core/alembic/versions/*_add_my_models_table.py
```

Verify:
- Correct table/column names
- Proper indexes
- Constraints are as expected
- `downgrade()` properly reverses the changes

### 5. Apply the Migration

```bash
cd py
make db-migrate
```

### 6. Test

```bash
cd py
make test
```

## Common Scenarios

### Adding a Column

1. Add the column to the model
2. Generate migration: `make db-prepare MSG="add status column to widgets"`
3. Review and apply

### Renaming a Column

Auto-generation can't detect renames (it sees drop + add). Use manual migration:

```bash
MANUAL=1 make db-prepare MSG="rename widget_name to name"
```

Then edit the migration:

```python
def upgrade():
    op.alter_column('widgets', 'widget_name', new_column_name='name')

def downgrade():
    op.alter_column('widgets', 'name', new_column_name='widget_name')
```

### Data Migration

For data transformations, use manual migration:

```bash
MANUAL=1 make db-prepare MSG="backfill user display names"
```

```python
def upgrade():
    connection = op.get_bind()
    connection.execute(text("""
        UPDATE users SET display_name = email WHERE display_name IS NULL
    """))
```

## Database Commands

| Command | Description |
|---------|-------------|
| `make setup` | Start containers, migrate, and seed |
| `make db-migrate` | Apply pending migrations |
| `make db-prepare MSG="..."` | Generate migration from model changes |
| `MANUAL=1 make db-prepare MSG="..."` | Create empty migration for manual edits |
| `make wipe` | Drop database (keeps container) |
| `make teardown` | Stop and remove all containers |

## Troubleshooting

### Migration fails to generate

1. Ensure database is running: `make setup`
2. Check model is imported in `__init__.py`
3. Verify POSTGRES_URL is set correctly

### Migration applies but tests fail

1. Check for missing indexes or constraints
2. Verify foreign keys reference correct tables
3. Run `make wipe && make setup` to reset and reapply all migrations

### Conflict with existing migration

Never modify already-pushed migrations. Create a new migration to fix issues.

## Best Practices

1. **One logical change per migration** — Don't combine unrelated changes
2. **Always test downgrade** — Run `alembic downgrade -1` then `upgrade` to verify
3. **Review auto-generated migrations** — They may need manual tweaks
4. **Use descriptive messages** — The message becomes the filename
5. **Never hard delete** — Use soft deletes with `archived_at` timestamp

## References

- Full database guide: `py/docs/DATABASE.md`
- Model patterns: `py/docs/PYTHON_LIBRARY_PATTERNS.md`
