# Turbo Monorepo

The TypeScript stack uses [Turborepo](https://turbo.build/) to orchestrate builds across packages and apps.

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

## Integration with Python

Turbo handles TypeScript builds. Python uses uv workspaces separately.

For hybrid setups where TypeScript builds output to Python's static directory:
- Configure Vite to output to `py/apps/py-app/static/app/`
- Python serves the built SPA
- See [Hybrid Stack](hybrid-stack.md) for details
