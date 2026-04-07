# Success Criteria

All checks must pass before merging:

```bash
cargo build                    # Compiles without errors
cargo test                     # All tests pass
cargo clippy -- -D warnings    # No clippy warnings
cargo fmt -- --check           # Code is formatted
```

## Standards

- No `println!`, `dbg!`, or `#[allow(dead_code)]` in committed code.
- No `.unwrap()` in production code paths — use proper error handling.
- Models use private fields with getters.
- Every handler file exports `pub async fn handler(...)`.
- Templates declared in the same file as the handler that uses them.
- UUIDs throughout — no string IDs.
