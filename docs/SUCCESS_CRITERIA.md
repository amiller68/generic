# Success Criteria

Checks that must pass before code can be merged. This is the CI gate.

## Quick Check

Run all checks for both projects:
```bash
make check
```

Or check a specific project:
```bash
make check-py    # Python only
make check-ts    # TypeScript only
```

## Individual Checks

### Python

#### Format Check
```bash
cd py && make fmt-check
```
Uses Black formatter. Fix with `make fmt`.

#### Lint
```bash
cd py && make lint
```
Uses Ruff linter.

#### Type Check
```bash
cd py && make types
```
Uses mypy for type checking.

#### Tests
```bash
cd py && make test
```
Uses pytest. Requires Postgres and Redis running (`make setup`).

#### Build
```bash
cd py && make build
```
Validates the Docker build.

### TypeScript

#### Format Check
```bash
cd ts && make fmt-check
```
Uses Prettier. Fix with `make fmt`.

#### Lint
```bash
cd ts && make lint
```
Runs ESLint across the monorepo.

#### Type Check
```bash
cd ts && make types
```
Uses TypeScript compiler for type checking.

#### Tests
```bash
cd ts && make test
```
Uses Vitest.

#### Build
```bash
cd ts && make build
```
Builds all apps and packages via Turbo.

### Docker Build

```bash
make docker-build
```
Verifies Docker images can be built for all services.

## Fixing Common Issues

### Formatting Failures

Run the formatter and commit:
```bash
make fmt        # Format all projects
# or
make fmt-py     # Python only
make fmt-ts     # TypeScript only
```

### Lint Warnings

Most lint issues can be auto-fixed:
```bash
cd py && ruff check --fix .
cd ts && pnpm lint --fix
```

### Type Errors

- Python: Check import paths and add type annotations
- TypeScript: Ensure types are exported and imported correctly

### Test Failures

Python tests require local services:
```bash
make setup-py    # Start Postgres + Redis
make test-py     # Run tests
```

TypeScript tests are self-contained:
```bash
make test-ts
```

## CI Pipeline

The GitHub Actions CI runs all checks on PR and push to main:

1. **Python:** fmt-check, lint, types, test, build
2. **TypeScript:** fmt-check, lint, types, test, build
3. **Docker:** Build check for all images

All jobs must pass for the `ci-success` gate to open.
