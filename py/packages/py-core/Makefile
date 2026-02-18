.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# Get branch-specific database name (derived from git branch)
# For local dev, we use worktree-ports to get branch-specific database
# In CI, POSTGRES_URL is set by the environment or defaults in conftest.py
PROJECT_ROOT := $(shell cd ../../../ && pwd)
WORKTREE_DB_NAME := $(shell PROJECT_ROOT=$(PROJECT_ROOT) && source $(PROJECT_ROOT)/bin/utils && source $(PROJECT_ROOT)/bin/config && source $(PROJECT_ROOT)/bin/worktree-ports && get_worktree_db_name 2>/dev/null || echo "krondor-generic")
TEST_POSTGRES_URL := $(shell ./bin/db.sh endpoint $(WORKTREE_DB_NAME) 2>/dev/null)

# Helper to set POSTGRES_URL only if we got a valid one from endpoint
ifdef TEST_POSTGRES_URL
  POSTGRES_ENV := POSTGRES_URL="$(TEST_POSTGRES_URL)"
else
  POSTGRES_ENV :=
endif

.PHONY: setup
setup: ## Start postgres + redis containers, migrate, and seed
	@./bin/db.sh up
	@./bin/redis.sh up
	@echo "Setting up branch-specific database: $(WORKTREE_DB_NAME)..."
	@./bin/db.sh ensure_database "$(WORKTREE_DB_NAME)"
	@$(POSTGRES_ENV) ./bin/db.sh migrate
	@$(POSTGRES_ENV) ./bin/seed.sh all

.PHONY: seed
seed: ## Seed database with initial data
	@$(POSTGRES_ENV) ./bin/seed.sh all

.PHONY: seed-users
seed-users: ## Seed users only
	@./bin/seed.sh users

.PHONY: seed-dry-run
seed-dry-run: ## Show what would be seeded (dry run)
	@./bin/seed.sh --dry-run

.PHONY: teardown
teardown: ## Stop and remove all containers
	@./bin/db.sh down
	@./bin/redis.sh down

.PHONY: wipe
wipe: ## Drop the branch-specific database (keeps container running)
	@echo "Wiping branch-specific database: $(WORKTREE_DB_NAME)..."
	@./bin/db.sh wipe "$(WORKTREE_DB_NAME)"

.PHONY: test
test: ## Run tests
	@$(POSTGRES_ENV) uv run pytest

.PHONY: lint
lint: ## Run linting
	@uv run ruff check src/ tests/

.PHONY: fmt
fmt: ## Format code
	@uv run black src/ tests/

.PHONY: fmt-check
fmt-check: ## Check formatting
	@uv run black --check src/ tests/

.PHONY: types
types: ## Run type checking with ty
	@uv run ty check src/ tests/

.PHONY: check
check: fmt-check lint types test ## Run all checks

.PHONY: clean
clean: ## Clean build artifacts
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type d -name ".ruff_cache" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete

# Database commands
.PHONY: db-up
db-up: ## Start PostgreSQL container
	@./bin/db.sh up

.PHONY: db-down
db-down: ## Stop and remove PostgreSQL container (deletes data)
	@./bin/db.sh down

.PHONY: db-status
db-status: ## Check PostgreSQL container status
	@./bin/db.sh status

.PHONY: db-endpoint
db-endpoint: ## Print PostgreSQL connection URL
	@./bin/db.sh endpoint

.PHONY: db-connect
db-connect: ## Connect to PostgreSQL with psql
	@./bin/db.sh connect

.PHONY: db-migrate
db-migrate: ## Run pending database migrations
	@$(POSTGRES_ENV) ./bin/db.sh migrate

.PHONY: db-prepare
db-prepare: ## Create new migration (usage: make db-prepare MSG="description")
ifdef MANUAL
	@$(POSTGRES_ENV) ./bin/db.sh prepare --manual "$(MSG)"
else
	@$(POSTGRES_ENV) ./bin/db.sh prepare "$(MSG)"
endif
