# Contributing Guide

This guide covers how to contribute to the project, whether you're an AI agent or a human developer.

## For AI Agents

### Getting Started

1. **Run `make install`** - Always first, to ensure dependencies are available
2. **Read the relevant docs** - Start with [PYTHON_LIBRARY_PATTERNS.md](./PYTHON_LIBRARY_PATTERNS.md)
3. **Understand the task** - Use planning mode to analyze requirements before coding
4. **Follow existing patterns** - Match the style and structure of existing code

### Key Constraints

- **Work only in your workspace** - Don't access files outside your workspace
- **No dev servers** - Shared machine; trust tests and builds instead
- **All database/storage through py-core** - Never access DB or storage directly from apps
- **`make check` must pass** - Before creating any PR

### Code Quality Expectations

- Follow [PYTHON_LIBRARY_PATTERNS.md](./PYTHON_LIBRARY_PATTERNS.md) for Python code
- Use `Params` and `Context` dataclasses for operations
- Keep functions pure where possible
- Write tests for new functionality
- Update documentation when patterns change

### File Naming Conventions

**TypeScript/React:**
- Use `kebab-case` for all file names, including React components
- Example: `chat-header.tsx`, `message-list.tsx`, `use-server-event.ts`
- Export components with `PascalCase` names: `export { ChatHeader } from './chat-header'`

**Python:**
- Use `snake_case` for all file names (standard Python convention)
- Example: `async_tool_execution.py`, `run_search.py`

### Naming Philosophy

**Prefer pedantic, descriptive names over short ones.** Clarity is more important than brevity.

- Function/file names should fully describe what they do
- Don't abbreviate unless the abbreviation is universally understood
- If a name feels too long, that's usually fine - it helps future readers understand the code

**Examples:**
```python
# Good - pedantic and descriptive
recover_stuck_async_tool_executions_task
create_async_tool_execution
get_thread_with_messages_and_operations

# Bad - too short or ambiguous
recover_ops_task
create_execution
get_thread
```

This applies to files, functions, classes, and variables. When in doubt, be more explicit.

### Refactoring Principles

**No backward compatibility shims.** When refactoring:

- Update all imports in a single pass - don't create re-export shims
- Delete the old code completely after migrating
- If consolidating code to a shared package, update all consumers directly
- The user would rather have a clean refactor (with LLM assistance to update imports) than a codebase littered with deprecated re-exports

This applies to:
- Moving types/classes between packages
- Consolidating duplicated code
- Renaming exports
- Changing import paths

### Before Submitting

1. Run `make check` - All checks must pass
2. Run `make test` - All tests must pass
3. Update docs if needed - See [SUCCESS_CRITERIA.md](./SUCCESS_CRITERIA.md#documentation-requirements)
4. Write descriptive commit messages
5. Create PR with clear summary

---

## For Human Developers

### Development Setup

1. **Clone the repository**
   ```bash
   git clone git@github.com:your-org/generic.git
   cd generic
   ```

2. **Install dependencies**
   ```bash
   make install
   ```

3. **Start local services** (if needed)
   ```bash
   # Services are managed via Docker
   # See docs/development/LOCAL.md for full setup
   ```

4. **Run the dev server**
   ```bash
   make dev
   ```

### Code Review Guidelines

When reviewing PRs (from agents or humans):

**Do check:**
- Does the code solve the stated problem?
- Are there appropriate tests?
- Does it follow existing patterns?
- Is the code readable and maintainable?
- Are there security concerns?

**Don't worry about:**
- Formatting - CI enforces this
- Linting - CI catches this
- Type safety - Type checker verifies this

### Architecture Decisions

Before making significant changes:

1. **Discuss first** - Open an issue or discuss in PR
2. **Document the decision** - Update relevant docs
3. **Follow established patterns** - Or document why you're deviating

Key architectural principles:
- Database and storage operations go through py-core only
- Python operations are functional with explicit dependency injection
- Use `Params` dataclasses for extensible function signatures
- Prefer composition over inheritance

---

## Commit Conventions

Use conventional commit prefixes:

| Prefix | Use For |
|--------|---------|
| `feat:` | New features |
| `fix:` | Bug fixes |
| `refactor:` | Code refactoring (no behavior change) |
| `chore:` | Maintenance tasks, dependency updates |
| `docs:` | Documentation changes |
| `test:` | Test additions or modifications |
| `perf:` | Performance improvements |

Example:
```
feat: add user export functionality

- Implement export endpoint
- Add file serialization
- Write tests for export flow

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## TODO Comments

Use structured TODO comments to track work that needs to be done:

| Format | Meaning |
|--------|---------|
| `TODO (name):` | Future work - do this eventually |
| `TODO (draft):` | Must be resolved before merging |
| `TODO (name, tag):` | Create an issue for this with the specified tag |

**Examples:**

```python
# TODO (username): Optimize this query for large datasets

# TODO (draft): Add error handling for edge cases

# TODO (username, enhancement): Support batch imports
```

**Guidelines:**
- `TODO (draft):` comments **must** be resolved before the PR is merged
- `TODO (name):` comments are acceptable to merge - they track future work
- `TODO (name, tag):` should result in a GitHub issue being created with the appropriate label

---

## Pull Request Process

1. **Create a branch** - Use descriptive names (e.g., `feature/user-export`)
2. **Make changes** - Follow patterns, write tests
3. **Run checks** - `make check && make test`
4. **Push and create PR** - Use the PR template
5. **Wait for CI** - All checks must pass
6. **Address feedback** - Respond to review comments
7. **Merge** - Squash merge to main

---

## Getting Help

- **Documentation issues** - Update the relevant doc and submit a PR
- **Bug reports** - Open a GitHub issue with reproduction steps
- **Feature requests** - Open a GitHub issue with use case description
- **Questions** - Check existing docs first, then open a discussion
