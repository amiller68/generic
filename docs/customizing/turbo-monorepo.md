# Turbo Monorepo

[Turborepo](https://turbo.build/) orchestrates builds and dev servers across both Python and TypeScript packages.

## How Turbo Works

Turbo manages the dependency graph between packages, ensuring:
- Packages build before apps that depend on them
- Parallel execution where possible
- Intelligent caching of build outputs

### Configuration

Root config at `ts/turbo.json`:

```json
{
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", "build/**"]
    },
    "dev": {
      "dependsOn": ["^build", "build"],
      "cache": false,
      "persistent": true
    }
  }
}
```

Key concepts:
- `^build` means "build dependencies first"
- `outputs` define what gets cached
- `persistent: true` for long-running dev servers

## Package Structure

```
ts/
├── apps/
│   ├── web/          # Vite SPA (depends on packages)
│   └── api/          # Express API (depends on packages)
├── packages/
│   ├── http-api/     # HTTP client utilities
│   └── typescript-config/  # Shared tsconfig
├── turbo.json        # Build orchestration
└── package.json      # Root scripts
```

## Running Commands

All commands run from `ts/`:

```bash
# Build all packages and apps
pnpm build

# Run dev servers (builds packages first)
pnpm dev

# Run tests
pnpm test

# Type check everything
pnpm check-types

# Format code
pnpm fmt
```

### Filtered Commands

Run commands for specific packages:

```bash
# Build only the web app
pnpm turbo run build --filter=web

# Dev server for api only
pnpm turbo run dev --filter=api

# Build a package and its dependents
pnpm turbo run build --filter=@repo/http-api...
```

## Adding a New Package

1. Create the package directory:
   ```
   ts/packages/your-package/
   ├── src/
   │   └── index.ts
   ├── package.json
   └── tsconfig.json
   ```

2. Configure `package.json`:
   ```json
   {
     "name": "@repo/your-package",
     "main": "./dist/index.js",
     "scripts": {
       "build": "bunchee src/index.ts",
       "dev": "bunchee src/index.ts --watch"
     }
   }
   ```

3. Add to apps that need it:
   ```json
   {
     "dependencies": {
       "@repo/your-package": "workspace:*"
     }
   }
   ```

4. Turbo automatically detects the new package - no config changes needed.

## Adding a New App

1. Create the app directory in `ts/apps/`

2. Add a `package.json` with build scripts

3. Optionally add a `turbo.json` for app-specific config:
   ```json
   {
     "extends": ["//"],
     "tasks": {
       "build": {
         "outputs": ["dist/**"]
       }
     }
   }
   ```

## Build Caching

Turbo caches build outputs based on:
- Source file hashes
- Dependencies
- Environment variables (configurable)

Cache is stored in `.turbo/` (gitignored).

### Cache Invalidation

```bash
# Clear local cache
pnpm clean

# Force rebuild without cache
pnpm turbo run build --force
```

## Running Multiple Services

Turbo's killer feature: run all your services with one command in one terminal.

```bash
pnpm dev
```

This starts everything in parallel:
- Python API server
- Python background worker
- Python scheduler
- TypeScript dev server
- Any other persistent tasks

No tmux, no multiple terminal tabs, no process managers. Just one command.

### How It Works

In `turbo.json`, tasks marked `persistent: true` run as long-lived processes:

```json
{
  "tasks": {
    "dev": {
      "dependsOn": ["^setup"],
      "cache": false,
      "persistent": true
    }
  }
}
```

Each package defines its own `dev` script:

```json
// apps/py-app/package.json
{
  "scripts": {
    "dev": "uv run uvicorn src.main:app --reload"
  }
}

// apps/ts-app/package.json
{
  "scripts": {
    "dev": "vite"
  }
}
```

Turbo runs them all, handles dependencies (`^setup` runs first), and shows unified output.

### Running Specific Services

```bash
# Just the API
pnpm turbo run dev --filter=py-app

# Just the frontend
pnpm turbo run dev --filter=ts-app

# API + worker
pnpm turbo run dev --filter=py-app --filter=py-worker
```

### Why Not tmux?

| | Turbo | tmux |
|---|-------|------|
| Setup | `pnpm dev` | Scripts, keybindings, configs |
| Learning curve | None | Moderate |
| Dependency ordering | Automatic | Manual |
| Output | Unified, labeled | Split panes |
| Stopping | Ctrl+C | Kill each pane |

Turbo is the right tool for dev servers. Save tmux for SSH sessions.
