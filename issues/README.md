# Issue Tracking

File-based issue tracking for AI agents and contributors.

This is the default convention for projects using `jig`. If your project uses an external tracker like Linear, Jira, or GitHub Issues, you can replace this workflow with your own — the `/issues` command can be adapted to query external tools (e.g., Linear MCP) instead of scanning local files.

## Directory Structure

```
issues/
├── README.md                   # This file (convention docs)
├── _template.md                # Ticket template
├── cloud-sync.md               # Epic (high-level overview)
├── cloud-sync-01-sdk-setup.md  # Ticket (specific task)
├── cloud-sync-02-oauth.md
└── ...
```

## Issue Types

### Epics

Large features or initiatives broken into multiple tickets.

- **File naming**: `feature-name.md` (descriptive, no number prefix)
- **Purpose**: High-level overview, context, and architecture decisions
- **Contains**: Background, phases, key technical decisions
- **Links to**: Child tickets for each discrete task

### Tickets

Focused, actionable tasks that can be completed in a single session.

- **File naming**: `feature-NN-short-description.md` (e.g., `cloud-sync-02-oauth.md`)
- **Number prefix**: Suggests execution order within a feature
- **Purpose**: Everything needed to implement one specific task
- **Links to**: Parent epic for full context

## Ticket Format

See `_template.md` for the standard ticket format, or use this structure:

```markdown
# [Ticket Title]

**Status:** Planned | In Progress | Complete | Blocked
**Epic:** [epic-name.md](./epic-name.md)
**Dependencies:** ticket-01 (if any)

## Objective

One-sentence description of what this ticket accomplishes.

## Implementation Steps

1. Step-by-step guide
2. With specific file paths
3. And code snippets where helpful

## Files to Modify/Create

- `path/to/file` - Description of changes

## Acceptance Criteria

- [ ] Checkbox criteria
- [ ] That can be verified

## Verification

How to test that this is working.
```

## Status Values

| Status | Meaning |
|--------|---------|
| `Planned` | Ready to be worked on |
| `In Progress` | Currently being implemented |
| `Complete` | Done and verified |
| `Blocked` | Waiting on external dependency |

## Picking Up Work

1. Look in `issues/` for tickets with `Status: Planned`
2. Check the parent epic for broader context
3. Verify dependencies are complete before starting
4. Update status to `In Progress` when starting
5. Update status to `Complete` when done

## Creating New Tickets

1. Copy `_template.md` to a new file with the appropriate name
2. If working on an existing epic, follow its naming pattern
3. For new features, create an epic first if the scope is large

## Dependencies

Tickets can have dependencies in two ways:

1. **Implicit (number order)**: `feature-01` should be done before `feature-02`
2. **Explicit**: Listed in the Dependencies field when non-linear

## Best Practices

- Keep tickets small enough to complete in one session
- Reference specific file paths in implementation steps
- Include code snippets for complex changes
- Always link back to the parent epic
- Update status immediately when starting/finishing work
