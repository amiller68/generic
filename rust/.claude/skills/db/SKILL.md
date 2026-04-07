---
description: Manage Rust app's SQLite database — migrations, seeding, queries, and schema changes. Use when modifying database models, creating migrations, or debugging data issues.
argument-hint: [setup | reset | migrate | seed | query | info]
allowed-tools:
  - Bash(make db-*)
  - Bash(./rust/bin/db.sh:*)
  - Bash(sqlite3:*)
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# Database (Rust / SQLite)

Manage SQLite database for the Rust Axum application. Each git branch gets its own isolated database file.

## Quick Reference

```bash
# From rust/ directory
make db-setup                    # Create DB, migrate, seed (runs on make dev)
make db-reset                    # Drop, recreate, migrate, seed
make db-seed                     # Re-run seed data
make db-info                     # Show current branch's DB path and tables
make db-query SQL="SELECT ..."   # Run SQL against current branch's DB
make db-migrate NAME=add_foo     # Create a new migration file
make db-clean                    # Delete current branch's database
make db-nuke                     # Delete ALL databases

# Or use the script directly
./bin/db.sh setup
./bin/db.sh query "SELECT * FROM users"
./bin/db.sh query "SELECT * FROM widgets" -t   # Tab-separated output
./bin/db.sh info
```

## How It Works

- Database files live in `rust/data/` (gitignored)
- Migrations are in `rust/crates/app/migrations/` as plain `.up.sql` files
- Migrations run automatically on app startup via `sqlx::migrate!`
- Seed data is in `rust/crates/app/seed/` as YAML files
- Seeding is idempotent — safe to run repeatedly
- `make dev` runs `db-setup` before starting the server

## Workflows

### Inspecting Data

```bash
# List tables
make db-query SQL=".tables"

# Show schema for a table
make db-query SQL=".schema users"

# Sample rows
make db-query SQL="SELECT * FROM users"
make db-query SQL="SELECT * FROM widgets WHERE status = 'active'"

# Count
make db-query SQL="SELECT COUNT(*) FROM widgets"
```

### Adding a Table

1. Create a migration file:
   ```bash
   make db-migrate NAME=create_orders
   ```

2. Edit the generated file in `crates/app/migrations/`:
   ```sql
   CREATE TABLE orders (
       id TEXT PRIMARY KEY NOT NULL,
       user_id TEXT NOT NULL REFERENCES users(id),
       total INTEGER NOT NULL DEFAULT 0,
       status TEXT NOT NULL DEFAULT 'pending',
       created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
       updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
   );

   CREATE INDEX idx_orders_user_id ON orders (user_id);
   CREATE INDEX idx_orders_status ON orders (status);
   ```

3. Add the Rust model in `crates/app/src/database/models/`

4. Restart the dev server — migrations apply automatically on connect

### Modifying a Table

SQLite has limited `ALTER TABLE` support. For simple column additions:

```sql
ALTER TABLE widgets ADD COLUMN priority INTEGER NOT NULL DEFAULT 0;
```

For renames or complex changes, create a new table, copy data, drop old, rename:

```sql
CREATE TABLE widgets_new (...);
INSERT INTO widgets_new SELECT ... FROM widgets;
DROP TABLE widgets;
ALTER TABLE widgets_new RENAME TO widgets;
```

### Adding Seed Data

Edit `crates/app/seed/users.yaml` or `crates/app/seed/widgets.yaml`:

```yaml
users:
  - email: "al@krondor.org"
    name: "Al"
    is_admin: true
  - email: "new@example.com"
    name: "New User"
    is_admin: false
```

Then run `make db-seed`.

### Resetting Everything

```bash
make db-reset
```

This deletes the DB file, recreates it, runs all migrations, and seeds.

## Schema Conventions

Every table should include:
- `id TEXT PRIMARY KEY NOT NULL` — UUID v4, generated in Rust
- `created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))`
- `updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))`
- Appropriate indexes on foreign keys and filtered columns
- Use `TEXT` for strings, `INTEGER` for booleans (0/1), `REAL` for floats

## File Layout

```
rust/
├── bin/db.sh                        # Database management script
├── data/                            # Database files (gitignored)
│   └── *.db                         # One per branch
└── crates/app/
    ├── migrations/                  # SQL migration files
    │   ├── 20260404000000_create_widgets.up.sql
    │   └── 20260404000001_create_users.up.sql
    ├── seed/                        # YAML seed data
    │   ├── users.yaml
    │   └── widgets.yaml
    └── src/database/
        ├── mod.rs                   # Database wrapper
        ├── sqlite.rs                # Connection + migration runner
        ├── seed.rs                  # Seed logic
        └── models/                  # Rust model structs + queries
            ├── user.rs
            └── widget.rs
```

## Hard Rules

- **Never modify pushed migrations** — create a new one to fix issues
- **One logical change per migration** — keep them small and focused
- **Name migrations clearly** — `create_orders`, not `fix` or `update`
- **Always add indexes** on foreign keys and commonly filtered columns
- **Seed data is idempotent** — existing records are updated, not duplicated
