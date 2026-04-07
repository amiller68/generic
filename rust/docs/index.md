# Documentation

Rust web application built with Axum, SQLite, HTMX, and Apalis background tasks.

## Contents

- [PATTERNS.md](PATTERNS.md) — Coding conventions and architectural patterns
- [SUCCESS_CRITERIA.md](SUCCESS_CRITERIA.md) — CI checks and quality gates
- [CONTRIBUTING.md](CONTRIBUTING.md) — Contribution guide

## Key Concepts

- **HATEOAS** — Server-rendered HTML with HTMX for interactivity. No JSON API, no SPA.
- **runtime::Service** — Trait for long-running services (HTTP, task worker) with graceful shutdown.
- **struct-patch** — Partial model updates via generated Patch types.
- **Apalis** — Background job processing with SQLite-backed persistence.
- **EventBus** — Broadcast channel powering SSE for real-time UI updates.
