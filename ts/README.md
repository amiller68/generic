# TypeScript Projects

This directory contains TypeScript-based projects for the generic template, managed with pnpm workspaces and Turbo.

## Structure

```
ts/
├── apps/
│   ├── web/              # Vite + React application
│   └── api/              # Express API server
├── packages/
│   ├── typescript-config/ # Shared TypeScript configs
│   └── http-api/         # Shared HTTP API types
├── bin/
│   └── styles.sh         # Branding asset setup script
├── package.json          # Root package.json
├── pnpm-workspace.yaml   # pnpm workspace configuration
├── Makefile              # Build and development commands
└── turbo.json           # Turbo configuration
```

## Prerequisites

- Node.js 20.x
- pnpm (installed automatically by project)

## Quick Start

```bash
# Install dependencies
make install

# Setup branding assets (creates symlinks)
make styles

# Start development servers
make dev

# Build for production
make build
```

## Available Commands

All commands are available through the Makefile:

```bash
make help          # Show available commands
make install       # Install dependencies with pnpm
make dev           # Run development servers (sets up styles first)
make build         # Build all projects (sets up styles first)
make test          # Run all tests
make fmt           # Format code with Prettier
make fmt-check     # Check code formatting
make types         # Check TypeScript types
make check         # Run all checks (format, types, tests)
make styles        # Setup branding asset symlinks
make clean         # Clean build artifacts and symlinks
make docker-build  # Build Docker images for all apps
```

## Projects

### Web App (`apps/web/`)

A client-side web application built with:
- **Vite** - Fast build tool and dev server
- **React 19** - UI library
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Shadcn UI** - Component library

#### Development

```bash
# From the ts/ directory
make dev

# The app will be available at http://localhost:5173
```

Vite automatically:
- Compiles Tailwind CSS
- Hot-reloads on file changes
- Type-checks TypeScript

#### Building

```bash
# Build for production
make build

# Or use Vite build command directly
pnpm build
```

The build process:
1. Sets up branding asset symlinks (`make styles`)
2. Runs `vite build` which compiles the app
3. Outputs static files to `apps/web/dist/`

#### Branding Assets

Branding assets (icons, favicons) are symlinked from `branding/assets/`:

```bash
# Create symlinks (run automatically by make dev/build)
make styles

# Symlinks are created in apps/web/public/:
# - favicon.ico -> ../../../../branding/assets/favicon.ico
# - favicon.png -> ../../../../branding/assets/favicon.png
# - icon.png -> ../../../../branding/assets/icon.png
# - icon.svg -> ../../../../branding/assets/icon.svg
```

**Note**: Symlinks are **not** committed to git. Run `make styles` after cloning the repo.

### API Server (`apps/api/`)

An Express-based API server with:
- **Express** - Web framework
- **TypeScript** - Type-safe development
- **Zod** - Runtime type validation
- **tsup** - Fast TypeScript bundler
- **Vitest** - Unit testing framework

#### Development

```bash
# From the ts/ directory
make dev

# The API will be available at http://localhost:3001
```

The development server:
- Watches for file changes
- Automatically rebuilds and restarts
- Serves on port 3001

#### Building

```bash
# Build for production
make build
```

This creates `apps/api/dist/index.cjs` for deployment.

#### Testing

```bash
# Run tests
make test

# Or from apps/api/
cd apps/api
pnpm test
```

## Monorepo Management

This project uses:
- **pnpm workspaces** - Efficient dependency management with shared node_modules
- **Turbo** - Build orchestration, caching, and parallel execution

### Adding Packages

To add a dependency to the web app:

```bash
cd apps/web
pnpm add package-name
```

To add a dependency to the API:

```bash
cd apps/api
pnpm add package-name
```

To add a shared dev dependency at the root:

```bash
pnpm add -D -w package-name
```

## Code Quality

The project enforces code quality through:

- **TypeScript** - Type checking with `make types`
- **Prettier** - Code formatting with `make fmt`
- **Vitest** - Testing with `make test`

Before committing, run:

```bash
make check
```

This runs formatting checks, type checks, and tests.

## Docker Deployment

Both apps have Dockerfiles for containerized deployment:

```bash
# Build Docker images
make docker-build

# Or build individually
make docker-build-web
make docker-build-api
```

The Docker images:
- Use multi-stage builds for optimization
- Copy branding assets during build
- Are ready for deployment with Kamal

## Troubleshooting

**Branding assets not loading**:
```bash
make styles  # Recreate symlinks
```

**TypeScript errors after pulling**:
```bash
make install  # Reinstall dependencies
make types    # Check for type errors
```

**Port conflicts**:
- Web app uses port 5173 (Vite default)
- API uses port 3001

Change ports in respective `package.json` dev scripts if needed.

**Build cache issues**:
```bash
pnpm turbo clean  # Clear Turbo cache
make clean        # Clean build artifacts
make install      # Reinstall dependencies
```
