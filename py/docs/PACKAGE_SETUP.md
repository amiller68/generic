# Package Setup Standards

This document outlines the standardized setup for packages and apps in this monorepo. All packages should follow these conventions for consistent CI/CD workflows.

## Package Types

### Python Packages (`py/packages/py-*`)

**Required `package.json` structure:**
```json
{
  "name": "@generic/py-package-name",
  "engines": {
    "node": "20.x"
  },
  "packageManager": "pnpm@9.15.9",
  "private": true,
  "scripts": {
    "build": "echo 'No build needed for Python package'",
    "fmt": "uv run black src tests --line-length 88",
    "fmt:check": "pnpm fmt --check",
    "lint": "uv run ruff check src tests",
    "lint:fix": "pnpm run lint --fix",
    "test": "uv run pytest",
    "types": "uv run ty check src",
    "check": "pnpm run fmt:check && pnpm run lint && pnpm types",
    "clean": "make clean"
  }
}
```

**Notes:**
- Always include `engines` and `packageManager` fields for consistency
- `fmt:check` and `lint:fix` use shorthand to avoid duplicating commands
- For packages without tests, omit `tests` from `fmt` and `lint` commands
- Additional scripts like `setup`, `db`, or `minio` may be added for local dev infrastructure

**Required `pyproject.toml` structure:**
```toml
[project]
name = "py-package-name"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    # Runtime dependencies
]

[dependency-groups]
dev = [
    "pytest>=8.3.5",
    "pytest-asyncio>=0.25.3",
    "ty",
    "ruff",
    "black"
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/package_name"]
```

**For workspace dependencies:**
```toml
[project]
dependencies = [
    "py-other-package"
]

[tool.uv.sources]
py-other-package = { workspace = true }
```

**Required `Makefile`:**
```makefile
.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

.PHONY: clean
clean: ## Clean build artifacts
	@echo "Cleaning Python build artifacts..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@find . -type d -name ".ruff_cache" -exec rm -rf {} +
	@find . -type d -name "htmlcov" -exec rm -rf {} +
	@find . -type d -name ".coverage" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name ".coverage" -delete
	@find . -type d -name ".turbo" -exec rm -rf {} +
	@find . -type d -name ".venv" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete"
```

---

## Tools and Standards

### Python
- **Formatter:** Black (line length: 88)
- **Linter:** Ruff
- **Type Checker:** ty
- **Test Framework:** pytest
- **Package Manager:** uv

### TypeScript
- **Linter/Formatter:** Biome (`@biomejs/biome`)
- **Type Checker:** TypeScript (`tsc`)
- **Build Tool:** TypeScript compiler or Vite (for bundles)

---

## Turbo Configuration

The root `turbo.json` defines task orchestration. Key conventions:

```json
{
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", "build/**", "src/py_*/_bundle/**"]
    },
    "check": {
      "dependsOn": ["^check"]
    },
    "fmt": {
      "dependsOn": ["^fmt"]
    },
    "lint": {
      "dependsOn": ["^lint"]
    },
    "types": {
      "dependsOn": ["^types"]
    }
  }
}
```

- Tasks with `dependsOn: ["^task"]` run dependencies first
- Output directories should be declared for caching
- All packages should implement the standard task names

---

## Common Patterns

### Script Naming
- Use `:check` suffix for non-mutating validation commands (e.g., `fmt:check`, `lint:check`)
- Use `:fix` suffix for commands that modify code (e.g., `lint:fix`)
- Main commands without suffixes typically modify code (e.g., `fmt`, `lint`)
- Use `check` as the comprehensive CI command that runs all non-mutating validations

### Dependencies
- Always specify minimum versions with `>=`
- Use `peerDependencies` for framework packages (e.g., React)
- Keep dev tooling versions consistent across packages

### Clean Scripts
- **Python packages**: Use `make clean` from package.json
  - Makefiles handle comprehensive cleanup of Python artifacts
  - Cleans: `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.coverage`, `htmlcov`, `.turbo`, `.venv`, `*.pyc`
  - Uses `find` commands for thorough cleanup across subdirectories
- **TypeScript packages**: Use direct `rm` commands in package.json
  - Remove build artifacts: `dist/`, `build/`, `.turbo/`
  - Remove dependency directories: `node_modules/`

---

## Orchestration: Make, pnpm, and Turbo

This monorepo uses **Make + pnpm + Turbo** for task orchestration:

### Layer 1: Developer Commands (Make)

**Preferred entry points for developers:**
```bash
make install     # Install dependencies (pnpm + uv)
make dev         # Start all dev servers
make build       # Build all packages
make test        # Run all tests
make check       # Run all checks (format, lint, types)
make fmt         # Auto-fix formatting
make lint        # Run linters
make types       # Run type checking
make clean       # Clean build artifacts
```

The root Makefile provides the primary interface for all commands.

### Layer 2: Turbo (Orchestration)

Turbo orchestrates task execution:
- **Dependency graphs**: Runs tasks in correct order
- **Parallelization**: Runs independent tasks concurrently
- **Caching**: Skips unchanged tasks
- **Filtering**: Target specific packages

### Layer 3: Package Scripts

**All packages** (TypeScript and Python) use `package.json` scripts:

```json
{
  "scripts": {
    // TypeScript
    "build": "tsc",
    "dev": "tsc --watch",

    // Python
    "fmt": "uv run black src tests --line-length 88",
    "test": "uv run pytest"
  }
}
```

### Why No postinstall Hooks?

**Never use postinstall hooks for `uv sync`** - it breaks Docker's pruned monorepo builds.

```json
// DON'T DO THIS
{
  "scripts": {
    "postinstall": "uv sync"
  }
}
```

Instead, run explicitly when needed:
```bash
make install    # Preferred - handles pnpm + uv
```

---

## Quick Reference

**Standard CI Command:**
```bash
make check      # Runs formatting check, linting, and type checking
```

**Fix All Issues:**
```bash
make fmt        # Auto-fix formatting
```

**Run Tests:**
```bash
make test       # Run all tests
```

**Clean Package:**
```bash
make clean      # Clean build artifacts
```
