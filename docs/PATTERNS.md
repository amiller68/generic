# Coding Patterns

Coding patterns and conventions for both Python and TypeScript workspaces.

**Detailed Python patterns:** See `py/docs/PYTHON_LIBRARY_PATTERNS.md` for comprehensive coverage of Context DI, Params dataclasses, module organization, SQLAlchemy patterns (StringEnum, uuid7), and background tasks.

## Error Handling

### Python (FastAPI)

- Use FastAPI's `HTTPException` for API errors
- Return structured error responses: `{"detail": "message"}`
- Use `try/except` with specific exception types
- Log errors with appropriate levels before raising

### TypeScript (Express)

- Use Zod for request validation
- Return structured error responses: `{error: "message"}`
- Use middleware for common error handling
- Throw specific error types, catch at route level

## Module Organization

### Python

```
apps/py-app/
├── src/
│   ├── main.py          # FastAPI app entry point
│   ├── routes/          # API route handlers
│   ├── models/          # SQLAlchemy models
│   ├── services/        # Business logic
│   └── tasks/           # Taskiq background jobs
```

- One router per domain area
- Models define database schema
- Services contain business logic (not in routes)
- Tasks for async/background work

### TypeScript

```
apps/web/
├── src/
│   ├── main.tsx         # React entry point
│   ├── components/      # React components
│   ├── hooks/           # Custom React hooks
│   └── lib/             # Utilities

apps/api/
├── src/
│   ├── index.ts         # Express entry point
│   ├── routes/          # API route handlers
│   └── lib/             # Shared utilities
```

- Feature-based component organization
- Barrel exports via `index.ts` files
- Shared types in `packages/http-api`

## Naming Conventions

### Python

- `snake_case` for functions, variables, modules
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants
- Prefix private methods with `_`

### TypeScript

- `camelCase` for functions, variables
- `PascalCase` for components, types, interfaces
- `UPPER_SNAKE_CASE` for constants
- Suffix types with descriptive names (e.g., `UserResponse`, `CreateUserInput`)

### Files

- Python: `snake_case.py`
- TypeScript: `kebab-case.ts` or `PascalCase.tsx` for components

## Output Conventions

### Logging

- Python: Use `logging` module with appropriate levels
- TypeScript: Use `console.log/warn/error` for dev, structured logging in production

### API Responses

- Success: Return data directly or `{data: ...}`
- Error: Return `{error: "message"}` or `{detail: "message"}`
- Use appropriate HTTP status codes

## Testing Patterns

### Python (pytest)

```
tests/
├── conftest.py          # Shared fixtures
├── test_routes.py       # API endpoint tests
└── test_services.py     # Business logic tests
```

- Use `pytest-asyncio` for async tests
- Fixtures for database setup/teardown
- Test file naming: `test_*.py`
- Test function naming: `test_<what>_<expected>`

### TypeScript (Vitest)

```
src/
├── components/
│   ├── Button.tsx
│   └── Button.test.tsx  # Co-located tests
tests/
└── integration/         # Integration tests
```

- Co-locate unit tests with source files
- Use `.test.ts` or `.test.tsx` suffix
- Mock external dependencies with `vi.mock()`

## Common Idioms

### Database (Python/SQLAlchemy)

- Use Alembic for migrations: `make db migrate`
- Auto-generate migrations from model changes
- Always review generated migrations before applying

### API Validation (TypeScript/Zod)

```typescript
const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1),
});

app.post("/users", (req, res) => {
  const result = CreateUserSchema.safeParse(req.body);
  if (!result.success) {
    return res.status(400).json({ error: result.error });
  }
  // ...
});
```

### Background Jobs (Python/Taskiq)

- Define tasks in `tasks/` directory
- Use Redis broker for job queue
- Scheduler for cron-style recurring tasks
