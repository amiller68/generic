---
description: Run success criteria checks (format, lint, types, tests)
allowed-tools:
  - Bash(make:*)
---

Run the full success criteria checks to validate code quality before merging.

## Steps

1. Run `make check` to execute all checks (format, lint, types, tests)

2. If formatting check fails:
   - Run `make fmt` to auto-fix formatting issues
   - Re-run `make check` to verify fixes

3. Report a summary of pass/fail status for each check:
   - Format check
   - Lint check
   - Type check
   - Tests

4. If any checks fail that cannot be auto-fixed, report what needs manual attention.

This is the gate for all PRs - all checks must pass before merge.
