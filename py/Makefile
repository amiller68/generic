.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

.PHONY: install
install: ## Install all workspace dependencies
	@uv sync --all-packages
	@pnpm install

.PHONY: dev
dev: ## Run dev server + worker + scheduler with turbo
	@pnpm dev

.PHONY: dev-server
dev-server: ## Run only the web server (no worker/scheduler)
	@$(MAKE) -C apps/py-app dev

.PHONY: build
build: ## Build the project
	@echo "no build for py"

.PHONY: test
test: ## Run tests across workspace
	@$(MAKE) -C packages/py-core test
	@$(MAKE) -C apps/py-app test

.PHONY: test-unit
test-unit: ## Run unit tests (no external dependencies)
	@$(MAKE) -C packages/py-core test
	@$(MAKE) -C apps/py-app test

.PHONY: lint
lint: ## Run linting across workspace
	@$(MAKE) -C packages/py-core lint
	@$(MAKE) -C apps/py-app lint

.PHONY: fmt
fmt: ## Format code across workspace
	@$(MAKE) -C packages/py-core fmt
	@$(MAKE) -C apps/py-app fmt

.PHONY: fmt-check
fmt-check: ## Check formatting across workspace
	@$(MAKE) -C packages/py-core fmt-check
	@$(MAKE) -C apps/py-app fmt-check

.PHONY: types
types: ## Check types across workspace
	@$(MAKE) -C packages/py-core types
	@$(MAKE) -C apps/py-app types

.PHONY: check
check: fmt-check lint types test ## Run all checks

.PHONY: setup
setup: ## Start local development services (postgres + redis)
	@$(MAKE) -C packages/py-core setup

.PHONY: teardown
teardown: ## Stop and remove all containers
	@$(MAKE) -C packages/py-core teardown

.PHONY: wipe
wipe: ## Drop the database (keeps container running)
	@$(MAKE) -C packages/py-core wipe

.PHONY: styles
styles: ## Build styles
	@$(MAKE) -C apps/py-app styles

.PHONY: styles-watch
styles-watch: ## Watch and rebuild styles
	@$(MAKE) -C apps/py-app styles-watch

.PHONY: clean
clean: ## Clean build artifacts
	@echo "Cleaning Python build artifacts..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@find . -type d -name ".ruff_cache" -exec rm -rf {} +
	@find . -type d -name "htmlcov" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name ".coverage" -delete
	@rm -rf .venv
	@echo "✓ Clean complete"

# Database commands (delegated to py-core)
.PHONY: db
db: ## Database commands (usage: make db <command>)
	@$(MAKE) -C packages/py-core db-$(filter-out $@,$(MAKECMDGOALS))

.PHONY: db-migrate
db-migrate: ## Run pending database migrations
	@$(MAKE) -C packages/py-core db-migrate

.PHONY: db-prepare
db-prepare: ## Create new migration (usage: make db-prepare MSG="description")
	@$(MAKE) -C packages/py-core db-prepare MSG="$(MSG)" MANUAL="$(MANUAL)"

# Catch additional arguments
%:
	@:
