.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

.PHONY: dev
dev: ## Run development server
	@./bin/dev.sh

.PHONY: worker
worker: ## Run TaskIQ worker
	@./bin/worker.sh

.PHONY: scheduler
scheduler: ## Run TaskIQ scheduler
	@./bin/scheduler.sh

.PHONY: styles
styles: ## Build styles
	@./bin/styles.sh

.PHONY: styles-watch
styles-watch: ## Watch and rebuild styles
	@./bin/styles.sh --watch

.PHONY: test
test: ## Run tests
	@uv run pytest || test $$? -eq 5

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
	@find . -type f -name "*.pyc" -delete
