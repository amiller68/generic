.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

.PHONY: dev
dev: styles ## Run development server (builds styles first)
	@./bin/app/dev.sh

.PHONY: install
install: ## Install dependencies
	@uv sync

.PHONY: build
build: ## Build the project
	echo "no build for py"

.PHONY: test
test: ## Run tests
	@./bin/ci/test.sh

.PHONY: lint
lint: ## Run linter (ruff)
	@./bin/ci/lint.sh

.PHONY: fmt
fmt: ## Format code (black)
	@./bin/ci/fmt.sh

.PHONY: fmt-check
fmt-check: ## Check code formatting
	@./bin/ci/fmt.sh --check

.PHONY: types
types: ## Check types (mypy/pyright)
	@./bin/ci/types.sh

# Database management - pass all arguments after 'db' to the postgres script
.PHONY: db
db: ## Database management - pass all arguments after 'db' to the postgres script
	@./bin/db.sh $(filter-out $@,$(MAKECMDGOALS))

# Catch additional arguments to db command
%:
	@:

.PHONY: check
check: fmt-check lint types test ## Run all checks

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
	@find . -type f -name ".venv" -delete
	@echo "Cleaning built styles and assets..."
	@rm -rf static/css/
	@rm -f static/*.ico static/*.png static/*.svg
	@rm -rf .venv
	@echo "✓ Clean complete"

.PHONY: styles
styles: ## Build styles with Tailwind CSS and copy assets (USE_SYMLINKS=1 for symlinks)
	@./bin/styles.sh

.PHONY: styles-watch
styles-watch: ## Watch and rebuild styles on changes
	@./bin/styles.sh --watch
