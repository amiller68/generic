ARGS ?=

PROJECT_ROOT := $(shell cd .. && pwd)
VAULT_CMD := $(PROJECT_ROOT)/bin/vault
DB_SCRIPT := ./bin/db.sh

.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@echo '  dev:        Run the dev server with hot reload (vault secrets)'
	@echo '  check:      Check all Rust code'
	@echo '  install:    Install dependencies'
	@echo '  build:      Build all Rust packages'
	@echo '  test:       Run all tests'
	@echo '  lint:       Run clippy linter'
	@echo '  fmt:        Format code'
	@echo '  fmt-check:  Check code formatting'
	@echo '  db-setup:   Create DB, migrate, and seed for current branch'
	@echo '  db-reset:   Drop, recreate, migrate, and seed'
	@echo '  db-seed:    Seed the database'
	@echo '  db-query:   Run SQL (e.g. make db-query SQL="SELECT * FROM users")'
	@echo '  db-info:    Show current branch database info'
	@echo '  db-clean:   Delete current branch database'
	@echo '  db-nuke:    Delete ALL databases'
	@echo '  db-migrate: Create a new migration (e.g. make db-migrate NAME=add_foo)'
	@echo '  clean:      Clean build artifacts'

.PHONY: dev
DEV_PORT ?= 9000

dev: db-setup ## Run the dev server with hot reload and vault secrets
	@bash -c '\
		export PROJECT_ROOT="$(PROJECT_ROOT)" && \
		source "$(PROJECT_ROOT)/bin/utils" && \
		source "$(PROJECT_ROOT)/bin/config" && \
		echo "Starting on http://localhost:$(DEV_PORT) ..." && \
		source "$(PROJECT_ROOT)/bin/vault" && \
		run_with_vault --stage development -- \
			env SQLITE_DATABASE_URL=sqlite://data/app.db \
			    LISTEN_ADDRESS=127.0.0.1:$(DEV_PORT) \
			    HOST_NAME=http://localhost:$(DEV_PORT) \
			    SERVICE_SECRET=dev-secret-change-in-prod \
			cargo watch -x "run --bin generic-rust-app" \
	'

# -- Database targets (delegate to bin/db.sh) --

.PHONY: db-setup
db-setup: ## Create DB, run migrations, seed
	@$(DB_SCRIPT) setup

.PHONY: db-reset
db-reset: ## Drop DB, recreate, migrate, seed
	@$(DB_SCRIPT) reset

.PHONY: db-seed
db-seed: ## Seed the database
	@$(DB_SCRIPT) seed

.PHONY: db-clean
db-clean: ## Delete current branch's database
	@$(DB_SCRIPT) clean

.PHONY: db-nuke
db-nuke: ## Delete ALL databases
	@$(DB_SCRIPT) nuke

.PHONY: db-info
db-info: ## Show current database info
	@$(DB_SCRIPT) info

.PHONY: db-query
db-query: ## Run SQL query (use SQL="..." argument)
	@$(DB_SCRIPT) query "$(SQL)"

.PHONY: db-migrate
db-migrate: ## Create a new migration file (use NAME=... argument)
	@$(DB_SCRIPT) migrate -n "$(NAME)"

# -- Standard targets --

.PHONY: check
check: ## Check all Rust code
	cargo check --all

.PHONY: install
install: ## Install dependencies
	cargo fetch

.PHONY: build
build: ## Build all Rust packages
	cargo build --all

.PHONY: test
test: ## Run all tests
	cargo test --all

.PHONY: lint
lint: ## Run clippy linter
	cargo clippy --all -- -D warnings

.PHONY: fmt
fmt: ## Format code
	cargo fmt --all

.PHONY: fmt-check
fmt-check: ## Check code formatting
	cargo fmt --all -- --check

.PHONY: types
types: ## Run type checking (alias for check)
	@$(MAKE) check

.PHONY: clean
clean: ## Clean build artifacts
	cargo clean
