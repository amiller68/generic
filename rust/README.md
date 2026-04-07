# Rust App

Axum web server with SQLite, HTMX, and background task processing.

## Quick Start

```bash
cargo build
make dev          # creates data/ dir and starts the server
```

## Architecture

```
crates/app/
├── src/
│   ├── main.rs           # Entry point: config, logging, service spawning
│   ├── config.rs          # Environment-based configuration
│   ├── state.rs           # AppState: shared state across services
│   ├── runtime/           # Service trait + graceful shutdown
│   ├── http/              # Axum HTTP server (Service impl)
│   │   ├── auth/          # OAuth (Google) + session extractors
│   │   │   └── google/    # Login + callback handlers
│   │   ├── html/          # HTMX page handlers
│   │   │   ├── widgets/   # Widget CRUD (views/ + actions/)
│   │   │   └── admin/     # Admin dashboard (views/ + actions/)
│   │   ├── sse/           # Server-sent events
│   │   └── health/        # Health + version endpoints
│   ├── database/          # SQLite pool, migrations, models
│   │   ├── models/        # User, Widget (struct-patch for partial updates)
│   │   └── types/         # DbUuid
│   ├── tasks/             # Apalis background job processing (Service impl)
│   │   └── widget/        # Widget-specific tasks
│   └── events/            # EventBus (broadcast channel for SSE)
├── migrations/            # SQLx migrations (app + apalis)
├── templates/             # Askama HTML templates
└── static/                # CSS, favicon
```

## Key Patterns

- **`runtime::Service`** — implement `run(state, shutdown_rx)`, get `spawn()` for free. Each service owns its shutdown logic.
- **Models** — private fields with getters. `struct-patch` generates `UserPatch`/`WidgetPatch` for partial updates via `model.patch(patch, db)`.
- **Handlers** — one file per handler, each exports `handler`. Organized under `views/` and `actions/` directories.
- **Events** — scoped (`User(Uuid)` or `Broadcast`), two-level serde tagging (`AppEvent::Widget(WidgetEvent)`). SSE filters by scope.

## Commands

```bash
cargo build                    # Build
cargo test                     # Test
cargo clippy -- -D warnings    # Lint
cargo fmt -- --check           # Format check
cargo run --bin seed           # Seed the database
```
