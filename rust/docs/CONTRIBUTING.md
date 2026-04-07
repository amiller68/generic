# Contributing

## Setup

```bash
cargo build
make dev          # Creates data/ directory, starts the server
```

## Development Workflow

1. Create a branch off `main`.
2. Make changes following patterns in [PATTERNS.md](PATTERNS.md).
3. Run all checks: `cargo build && cargo test && cargo clippy -- -D warnings && cargo fmt -- --check`.
4. Create a PR — do not push directly to main.

## Adding a New Handler

1. Create a file under the appropriate `views/` or `actions/` directory.
2. Export `pub async fn handler(...)`.
3. Declare the Askama template struct in the same file (if it renders HTML).
4. Wire the route in the parent `mod.rs`.

## Adding a New Model

1. Create the file in `database/models/`.
2. Define three types: full model, `ListItem`, and derive `Patch` via struct-patch.
3. Use private fields with public getters.
4. Implement `find_by_*`, `list()`, `create()`, `patch()`, `delete()` as needed.

## Adding a New Background Task

1. Create a domain directory under `tasks/` (e.g., `tasks/widget/`).
2. Define the task struct with `Serialize`/`Deserialize`.
3. Implement the `Task` trait: set `WORKER_NAME`, implement `register()` (creates storage + worker), and `push()` (enqueues via storage).
4. Add one line to `TaskWorker::run()`: `let monitor = MyTask::register(monitor, db.clone(), events.clone());`
5. Call `state.tasks.push(MyTask { ... }).await` from handlers.
