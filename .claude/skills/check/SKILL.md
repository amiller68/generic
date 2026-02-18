---
description: Run project checks (build, test, lint, format). Use when validating code quality, preparing for merge, or verifying changes pass CI.
allowed-tools:
  - Bash(make:*)
  - Bash(cat:*)
  - Bash(ls:*)
  - Read
  - Glob
  - Grep
---

Run the full success criteria checks to validate code quality.

## This Project

This is a dual-workspace project with Python (`py/`) and TypeScript (`ts/`).

### Quick Commands

```bash
make check           # Run all checks for both projects
make check-py        # Check Python only
make check-ts        # Check TypeScript only
```

### Individual Checks

**Python (in `py/` directory):**
- `make fmt-check` — Black formatting
- `make lint` — Ruff linter
- `make types` — mypy type checking
- `make test` — pytest (requires Postgres + Redis)

**TypeScript (in `ts/` directory):**
- `make fmt-check` — Prettier formatting
- `make lint` — ESLint
- `make types` — TypeScript compiler
- `make test` — Vitest

## Steps

1. Determine which workspace(s) have changes:
   - Check `git status` for modified files
   - If changes in `py/`, run Python checks
   - If changes in `ts/`, run TypeScript checks
   - If both or uncertain, run `make check` from root

2. Run checks for affected workspace(s):
   ```bash
   make check        # All projects
   make check-py     # Python only
   make check-ts     # TypeScript only
   ```

3. If formatting checks fail, auto-fix:
   ```bash
   make fmt          # Format all
   make fmt-py       # Python only (Black)
   make fmt-ts       # TypeScript only (Prettier)
   ```

4. Report a summary of pass/fail status for each check.

5. If any checks fail that cannot be auto-fixed, report what needs manual attention.

## Notes

- Python tests require local services. Run `make setup-py` first if tests fail on database connection.
- This is the gate for all PRs — all checks must pass before merge.
