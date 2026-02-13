PROJECTS := py ts

.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Run-all targets (operate on all projects):'
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?##/ && !/^[a-zA-Z_-]+-%:/ { printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ''
	@echo 'Project-specific targets (use with -<project> suffix, e.g., -py, -ts):'
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+-%:.*?##/ { gsub(/-%/, "-<project>", $$1); printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ''
	@echo 'Available projects:'
	@for project in $(PROJECTS); do \
	    echo "  - $$project"; \
	done

# run a make command in the given directory
run-for:
	@if [ -d "./$(PROJECT)" ]; then \
		if [ -f "./$(PROJECT)/Makefile" ]; then \
			cd ./$(PROJECT) && make $(CMD); \
		else \
			echo "Error: Makefile not found in ./$(PROJECT) directory"; \
			exit 1; \
		fi; \
	else \
		echo "Error: Directory ./$(PROJECT) does not exist"; \
		exit 1; \
	fi

.PHONY: check
check: ## Check all projects
	@for project in $(PROJECTS); do \
		$(MAKE) run-for PROJECT=$$project CMD=check; \
	done

.PHONY: check-%
check-%: ## Check the given project
	@$(MAKE) run-for PROJECT=$(@:check-%=%) CMD=check

.PHONY: install
install: ## Install dependencies for all projects
	@for project in $(PROJECTS); do \
		$(MAKE) run-for PROJECT=$$project CMD=install; \
	done

.PHONY: install-%
install-%: ## Install dependencies for the given project
	@$(MAKE) run-for PROJECT=$(@:install-%=%) CMD=install

.PHONY: dev
dev: ## Run all development servers in tmux (use ARGS="--kill" to kill session)
	@./bin/dev $(ARGS)

.PHONY: dev-%
dev-%: ## Run development server for the given project
	@$(MAKE) run-for PROJECT=$(@:dev-%=%) CMD=dev

.PHONY: build
build: ## Build all projects
	@for project in $(PROJECTS); do \
		$(MAKE) run-for PROJECT=$$project CMD=build; \
	done

.PHONY: build-%
build-%: ## Build the given project
	@$(MAKE) run-for PROJECT=$(@:build-%=%) CMD=build

.PHONY: test
test: ## Run tests for all projects
	@for project in $(PROJECTS); do \
		$(MAKE) run-for PROJECT=$$project CMD=test; \
	done

.PHONY: test-%
test-%: ## Run tests for the given project
	@$(MAKE) run-for PROJECT=$(@:test-%=%) CMD=test

.PHONY: test-unit
test-unit: ## Run unit tests (no external dependencies)
	@for project in $(PROJECTS); do \
		$(MAKE) run-for PROJECT=$$project CMD=test-unit; \
	done

.PHONY: test-integration
test-integration: ## Run integration tests (requires local services)
	@for project in $(PROJECTS); do \
		$(MAKE) run-for PROJECT=$$project CMD=test-integration; \
	done

.PHONY: lint
lint: ## Run linters for all projects
	@for project in $(PROJECTS); do \
		$(MAKE) run-for PROJECT=$$project CMD=lint; \
	done

.PHONY: lint-%
lint-%: ## Run linters for the given project
	@$(MAKE) run-for PROJECT=$(@:lint-%=%) CMD=lint

.PHONY: fmt
fmt: ## Format all projects
	@for project in $(PROJECTS); do \
		$(MAKE) run-for PROJECT=$$project CMD=fmt; \
	done

.PHONY: fmt-%
fmt-%: ## Format the given project
	@$(MAKE) run-for PROJECT=$(@:fmt-%=%) CMD=fmt

.PHONY: fmt-check
fmt-check: ## Check formatting for all projects
	@for project in $(PROJECTS); do \
		$(MAKE) run-for PROJECT=$$project CMD=fmt-check; \
	done

.PHONY: fmt-check-%
fmt-check-%: ## Check formatting for the given project
	@$(MAKE) run-for PROJECT=$(@:fmt-check-%=%) CMD=fmt-check

.PHONY: types
types: ## Run type checking for all projects
	@for project in $(PROJECTS); do \
		$(MAKE) run-for PROJECT=$$project CMD=types; \
	done

.PHONY: types-%
types-%: ## Run type checking for the given project
	@$(MAKE) run-for PROJECT=$(@:types-%=%) CMD=types

.PHONY: setup
setup: ## Setup local development (database + redis)
	@for project in $(PROJECTS); do \
		$(MAKE) run-for PROJECT=$$project CMD=setup; \
	done

.PHONY: setup-%
setup-%: ## Setup local development for the given project
	@$(MAKE) run-for PROJECT=$(@:setup-%=%) CMD=setup

.PHONY: wipe
wipe: ## Drop all databases (keeps containers running)
	@for project in $(PROJECTS); do \
		$(MAKE) run-for PROJECT=$$project CMD=wipe; \
	done

.PHONY: wipe-%
wipe-%: ## Drop databases for the given project
	@$(MAKE) run-for PROJECT=$(@:wipe-%=%) CMD=wipe

.PHONY: teardown
teardown: ## Stop and remove all containers and volumes
	@for project in $(PROJECTS); do \
		$(MAKE) run-for PROJECT=$$project CMD=teardown; \
	done

.PHONY: teardown-%
teardown-%: ## Teardown containers for the given project
	@$(MAKE) run-for PROJECT=$(@:teardown-%=%) CMD=teardown

.PHONY: docker-build
docker-build: ## Build Docker images for all projects
	@for project in $(PROJECTS); do \
		$(MAKE) run-for PROJECT=$$project CMD=docker-build; \
	done

.PHONY: docker-build-%
docker-build-%: ## Build Docker image for the given project
	@$(MAKE) run-for PROJECT=$(@:docker-build-%=%) CMD=docker-build

.PHONY: docker-up
docker-up: ## Start docker-compose with vault secrets (rebuilds images)
	@./bin/vault run --stage development -- docker compose up --build

.PHONY: docker-down
docker-down: ## Stop docker-compose
	@docker compose down

.PHONY: docker-clean
docker-clean: ## Remove docker images and volumes
	@docker compose down -v --rmi local

.PHONY: clean
clean: ## Clean all projects
	@for project in $(PROJECTS); do \
		$(MAKE) run-for PROJECT=$$project CMD=clean; \
	done

.PHONY: clean-%
clean-%: ## Clean the given project
	@$(MAKE) run-for PROJECT=$(@:clean-%=%) CMD=clean

.PHONY: ports
ports: ## Show dev server port assignment for current branch
	@./bin/worktree-ports

.PHONY: worktree-create
worktree-create: ## Create a new git worktree - usage: make worktree-create BRANCH=<branch-name>
	@if [ -z "$(BRANCH)" ]; then \
		echo "Error: BRANCH is required. Usage: make worktree-create BRANCH=feature/my-branch"; \
		exit 1; \
	fi
	@./bin/worktree --repo . create $(BRANCH)

.PHONY: worktree-list
worktree-list: ## List all git worktrees
	@./bin/worktree --repo . list

.PHONY: worktree-remove
worktree-remove: ## Remove a git worktree - usage: make worktree-remove BRANCH=<branch-name>
	@if [ -z "$(BRANCH)" ]; then \
		echo "Error: BRANCH is required. Usage: make worktree-remove BRANCH=feature/my-branch"; \
		exit 1; \
	fi
	@./bin/worktree --repo . remove $(BRANCH)

.PHONY: worktree-cleanup
worktree-cleanup: ## Remove all git worktrees
	@./bin/worktree --repo . cleanup

# Terraform Cloud management - pass all arguments after 'tfc' to the script
.PHONY: tfc
tfc: ## Terraform Cloud management - pass all arguments after 'tfc' to the script
	@./bin/tfc $(filter-out $@,$(MAKECMDGOALS))


# Infrastructure management - pass all arguments after 'iac' to the script
.PHONY: iac
iac: ## Infrastructure management - run terraform with vault secrets
	@./bin/iac $(filter-out $@,$(MAKECMDGOALS))

# Deployment management - pass all arguments after 'deploy' to the kamal script
.PHONY: kamal
kamal: ## Deploy services using Kamal - usage: make kamal <service> <stage> <command>
	@./bin/kamal $(filter-out $@,$(MAKECMDGOALS))

# Catch additional arguments to tfc, ghcr, iac, and deploy commands
%:
	@:
