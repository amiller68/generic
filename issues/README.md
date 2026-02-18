# Issue Tracking

File-based issue tracking for AI agents and contributors.

## Directory Structure

```
issues/
├── README.md             # This file
├── _templates/           # Issue templates
│   ├── standalone.md     # Single-ticket feature/bug/chore
│   ├── epic-index.md     # Epic overview
│   └── ticket.md         # Ticket within an epic
├── epics/                # Multi-ticket features
│   └── feature-name/
│       ├── index.md      # Epic overview
│       └── 0-task.md     # Tickets (0-indexed)
├── features/             # Single-ticket features
├── bugs/                 # Bug fixes
└── chores/               # Maintenance tasks
```

## Issue Types

### Standalone Issues

Single-ticket work items in `features/`, `bugs/`, or `chores/`:

```bash
cp issues/_templates/standalone.md issues/features/my-feature.md
cp issues/_templates/standalone.md issues/bugs/fix-crash.md
cp issues/_templates/standalone.md issues/chores/update-deps.md
```

### Epics

Large features broken into multiple tickets:

```bash
mkdir issues/epics/cloud-sync
cp issues/_templates/epic-index.md issues/epics/cloud-sync/index.md
cp issues/_templates/ticket.md issues/epics/cloud-sync/0-sdk-setup.md
cp issues/_templates/ticket.md issues/epics/cloud-sync/1-oauth.md
```

- **index.md**: Overview, architecture decisions, ticket table
- **0-task.md, 1-task.md, ...**: Individual tickets (0-indexed for order)

## Status Values

| Status | Indicator | Meaning |
|--------|-----------|---------|
| `Planned` | `[ ]` | Ready to be worked on |
| `In Progress` | `[~]` | Currently being implemented |
| `Complete` | `[x]` | Done and verified |
| `Blocked` | `[!]` | Waiting on external dependency |

## Picking Up Work

1. Look for issues with `Status: Planned`
2. Check dependencies are complete
3. Update status to `In Progress` when starting
4. Update status to `Complete` when done

## Creating Issues

### Quick create

```bash
# Feature
cp issues/_templates/standalone.md issues/features/add-export.md

# Bug
cp issues/_templates/standalone.md issues/bugs/fix-playback.md

# Epic
mkdir issues/epics/multi-vault
cp issues/_templates/epic-index.md issues/epics/multi-vault/index.md
cp issues/_templates/ticket.md issues/epics/multi-vault/0-data-model.md
```

### Fill in the template

- **Objective**: One sentence describing the goal
- **Implementation Steps**: Specific guidance with file paths
- **Acceptance Criteria**: Checkboxes for verification

## Best Practices

- Keep tickets small enough to complete in one session
- Reference specific file paths in implementation steps
- Include code snippets for complex changes
- Update status immediately when starting/finishing work
- For epics, update the ticket table in `index.md`

## External Trackers

This convention is for file-based tracking. For Linear, Jira, or GitHub Issues, use their respective tools (MCP servers, `gh issue`, etc.) instead of scanning local files.
