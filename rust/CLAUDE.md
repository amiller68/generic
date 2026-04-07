# Project Guide

Axum web server with SQLite, HTMX, struct-patch models, and Apalis background tasks.

## Quick Reference

```bash
cargo build                    # Build
cargo test                     # Test
cargo clippy -- -D warnings    # Lint (warnings are errors)
cargo fmt -- --check           # Format check
make dev                       # Creates data/ dir and starts server
cargo run --bin seed           # Seed the database
```

## Project Structure

```
crates/app/src/
├── main.rs           # Entry point: config, tracing, service spawning
├── config.rs         # Environment-based configuration
├── state.rs          # AppState: shared state across services
├── runtime/          # Service trait + ShutdownHandle
├── http/             # HttpServer (Service impl)
│   ├── auth/         # OAuth (Google) + session extractors
│   │   └── google/   # login.rs, callback.rs
│   ├── html/         # HTMX page handlers
│   │   ├── widgets/  # views/ + actions/
│   │   └── admin/    # views/ + actions/
│   ├── sse/          # Server-sent events
│   └── health/       # Liveness, readiness, version
├── database/         # SQLite pool, migrations, models
│   ├── models/       # User, Widget (struct-patch for partial updates)
│   └── types/        # DbUuid
├── tasks/            # TaskProducer + TaskWorker (Service impl)
│   └── widget/       # ProcessWidgetTask
└── events/           # EventBus (broadcast channel for SSE)
```

## Documentation

- `docs/PATTERNS.md` — Coding conventions and architectural patterns
- `docs/SUCCESS_CRITERIA.md` — CI checks and quality gates
- `docs/CONTRIBUTING.md` — Contribution guide

## Key Patterns

- **`runtime::Service`** — implement `run(state, shutdown_rx)`, get `spawn()` for free.
- **Models** — private fields with getters. `struct-patch` generates Patch types for partial updates.
- **Handlers** — one file per handler, each exports `pub async fn handler(...)`. Organized under `views/` and `actions/`.
- **Events** — scoped (`User(Uuid)` or `Broadcast`), two-level serde tagging. SSE filters by scope.
- **Tasks** — `TaskProducer` (client in AppState) + `TaskWorker` (Service impl). Domain-scoped under `tasks/`.

## Constraints

1. All CI checks must pass before merging (build, test, clippy, fmt).
2. Follow existing patterns — match style of existing code.
3. UUIDs throughout — no string IDs.

## Do Not

- Push to main directly — create a PR
- Skip clippy warnings — fix them
- Add debug code (`println!`, `dbg!`) to commits
- Use `#[allow(dead_code)]` — remove unused code instead
- Create documentation files unless explicitly asked
