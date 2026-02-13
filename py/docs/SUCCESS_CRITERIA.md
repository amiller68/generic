# Success Criteria

This document defines what "done" means for agent work. All criteria must be met before creating a PR.

## Golden Rule

**You are not allowed to finish in a state where CI is failing.**

---

## Required Checks

Before considering work complete, run from the project root:

```bash
make check       # Runs all checks (build, format, types, lint)
```

This is the primary command. Individual checks can also be run:

```bash
make build       # Build all packages with no errors
make fmt-check   # Formatting check passes
make types       # Type checking passes
make lint        # Linting passes
make test        # Run all tests
```

---

## CI/CD Pipeline

Our GitHub Actions CI (`.github/workflows/ci.yml`) runs automatically on every push and PR.

### Checks That Run

| Check | Python Tool | TypeScript Tool |
|-------|-------------|-----------------|
| Format | Black | Biome |
| Linting | Ruff | Biome |
| Type checking | ty | tsc |
| Tests | pytest | Vitest |
| Build | - | Vite/esbuild |
| Docker | Dockerfile build | - |

**All checks must pass before merging.**

---

## Testing Your Changes

Since dev servers should not run in workspaces (shared machine with other agents), verify changes through:

```bash
make test        # Run all tests
make build       # Check builds succeed
make types       # Run type checking
make fmt-check   # Verify formatting
make lint        # Run linting
```

Or run everything at once:

```bash
make check       # All checks combined
```

---

## Adding Dependencies

If you add dependencies to any package:

```bash
make install     # Install all dependencies (pnpm + uv)
```

**Always run `make install` at the beginning of work** to ensure dependencies are available.

---

## Fixing Common Issues

### Format Issues

```bash
make fmt          # Auto-fix formatting
git add .
git commit -m "chore: fix formatting"
git push
```

### Type Errors

```bash
make types        # See type errors
# Fix errors, then:
git add .
git commit -m "fix: resolve type errors"
git push
```

### Lint Errors

```bash
make lint         # See lint errors
# Fix errors, then commit and push
```

### Test Failures

```bash
make test         # See failing tests
# Fix tests, then commit and push
```

---

## Documentation Requirements

Agents are responsible for keeping documentation up to date. If your changes affect any of the following, update the relevant docs:

**Update `py/docs/` when:**
- Adding new patterns or conventions
- Changing project structure
- Modifying build/test commands
- Adding new packages or dependencies

**Update inline documentation when:**
- Adding new public functions or modules
- Changing function signatures or behavior
- Adding new configuration options

**Documentation locations:**
- `py/docs/` - Python-specific patterns (this folder)
- `docs/` - Cross-project documentation
- `CLAUDE.md` files - Package-specific instructions for agents
- Code comments - Complex logic explanations
- Docstrings - Public API documentation

**If you're unsure whether docs need updating, they probably do.**

---

## Pre-Commit Checklist

- [ ] `make check` passes
- [ ] Tests written for new functionality
- [ ] Documentation updated if patterns/structure changed
- [ ] No debug code left behind (console.log, print statements)
- [ ] No secrets or credentials committed
- [ ] Changes are committed with descriptive messages
- [ ] Branch is pushed to remote
