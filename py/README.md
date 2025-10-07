# muze

## Requirements

- python 3.12
- uv
- hcp (for vault secrets)
- tailwindcss@3
- PostgreSQL (via Docker/Podman for local development)

## 🚀 Quick Start

```bash
# Install dependencies
make install

# Start development server (with 1Password vault integration)
make dev

# Run the project
make run

# Database operations
make db up                                    # Start PostgreSQL container
make db migrate                               # Run migrations (auto-starts DB)
make db prepare "Add user table"              # Create new migration
MANUAL=1 make db prepare "Custom migration"   # Create manual migration (important!)
```

## 📦 Database Management

### Key Database Commands

```bash
# Container management
make db up         # Start PostgreSQL container
make db down       # Stop and remove container/volumes
make db status     # Check container status
make db connect    # Open psql connection
make db endpoint   # Get connection URL

# Migrations - IMPORTANT: Use environment variables for flags!
make db migrate                               # Run migrations (auto-starts local DB if needed)
make db prepare "Description here"            # Auto-generate migration from models
MANUAL=1 make db prepare "Description"        # Create manual/empty migration template
```

### ⚠️ IMPORTANT: Migration Examples with Flags

The **RECOMMENDED** way to pass flags is through environment variables:

```bash
# Manual migration (IMPORTANT: Use MANUAL=1 prefix)
MANUAL=1 make db prepare "Add custom indexes"
MANUAL=true make db prepare "Data migration script"

# Direct script call (always works)
./bin/db.sh prepare --manual "Complex data transformation"
```

### Why Use Environment Variables for Flags?

Due to how Make processes arguments, flags like `--manual` don't pass through correctly with the standard `make db prepare` syntax. Using `MANUAL=1` ensures the flag is properly recognized by the underlying script.

## 🔧 Development Commands

### Code Quality

```bash
# Formatting
make fmt           # Auto-format code with black
make fmt-check     # Check formatting without changes

# Linting
make lint          # Run ruff linter

# Type checking
make types         # Run mypy type checker

# Run all quality checks
make check         # Runs fmt-check, lint, types, and test
```

### Testing

```bash
# Run all tests (auto-starts PostgreSQL if needed)
make test

# Direct test command with options
uv run pytest tests/ -v  # Verbose output
```

## 🎯 Application Commands

```bash
# Development server (with vault integration)
make dev           # Runs with 1Password vault for secrets
# or directly:
./bin/app/dev.sh

# Production-like run
make run           # Standard run without vault
# or directly:
./bin/app/run.sh

# Install/update dependencies
make install       # Uses uv to sync dependencies
```

## 🎨 Styling and Assets

```bash
# Build Tailwind CSS styles
make styles        # Build and minify CSS, copy brand assets

# Watch mode for development
make styles-watch  # Auto-rebuild on style changes
```

## 🧹 Utilities

```bash
# Clean build artifacts
make clean         # Remove __pycache__, .pyc, coverage, etc.

# Show help
make help          # Display all available targets with descriptions
```

## 🔐 Environment Variables

### Database
- `POSTGRES_URL` - PostgreSQL connection string (auto-set by db commands)
- `DATABASE_URL` - Alternative name for POSTGRES_URL

### Migration Flags (IMPORTANT!)
- `MANUAL=1` or `MANUAL=true` - Create manual migration template (prefix to command!)

### Vault Integration
The project uses 1Password for secret management. Secrets are loaded from `.env.vault` when using `make dev`.

## 📋 Example Workflows

### Start fresh development environment
```bash
make clean
make install
make db up
make db migrate
make dev
```

### Create and apply a new migration
```bash
# Auto-generate from model changes
make db prepare "Add user profile fields"

# Or create manual migration (NOTE THE PREFIX!)
MANUAL=1 make db prepare "Custom data migration"

# Apply the migration
make db migrate
```

### Run full test suite
```bash
make check  # Runs fmt-check, lint, types, and test
```

### Development with live reload
```bash
# Terminal 1 - Start database and app
make db up
make dev

# Terminal 2 - Watch styles
make styles-watch
```

## 💡 Pro Tips

1. **⚡ Always use environment variables for flags**: `MANUAL=1 make db prepare "..."`
   - This is the most reliable way to pass flags through Make

2. **🔄 Database auto-starts**: Migration commands will start PostgreSQL automatically if needed
   - No need to run `make db up` before `make db migrate`

3. **🔑 Vault integration**: Use `make dev` for development with 1Password secrets
   - Automatically loads secrets from your vault

4. **🎯 Direct script access**: All scripts in `bin/` can be called directly for more control
   - Example: `./bin/db.sh prepare --manual "My migration"`

## 🐛 Troubleshooting

### Make command shows "Unknown command"
- Make sure you're in the `py/` directory
- Check that the command exists in the Makefile

### Database connection issues
```bash
make db status     # Check if container is running
make db up         # Start container
make db endpoint   # Get connection URL
```

### Migration issues
```bash
# View migration history
uv run alembic history

# Check current revision
uv run alembic current

# Downgrade if needed (direct command)
uv run alembic downgrade -1
```

### Port conflicts
If port 5432 is already in use:
```bash
lsof -i :5432      # Check what's using the port
make db down       # Stop our container
# Then stop the conflicting service
```

### Manual migration not working?
Remember: **Always prefix with MANUAL=1**
```bash
# ✅ Correct
MANUAL=1 make db prepare "My manual migration"

# ❌ Won't work
make db prepare --manual "My manual migration"
```

## 📚 Direct Script Reference

For more control, you can always use the scripts directly:

```bash
# Database management
./bin/db.sh up                              # Start PostgreSQL
./bin/db.sh prepare --manual "Description"  # Manual migration
./bin/db.sh migrate                         # Run migrations

# CI scripts
./bin/ci/fmt.sh                   # Format code
./bin/ci/lint.sh                  # Run linter
./bin/ci/types.sh                 # Type checking
./bin/ci/test.sh                  # Run tests

# Application
./bin/app/dev.sh                  # Development server
./bin/app/run.sh                  # Production-like run
```

## 📖 Full Makefile Command Reference

Run `make help` to see all available commands with descriptions.
