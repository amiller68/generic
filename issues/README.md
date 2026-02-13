# Local Issue Catalog

A lightweight, markdown-based issue tracking system for managing project work items locally.

## Overview

This directory contains project issues tracked as markdown files:

```
issues/
├── README.md           # This file
├── open/               # Issues that need work
│   └── 001-example.md  # Example issue
└── closed/             # Completed issues
```

## Why Local Issues?

- **Version controlled** - Issues are part of the codebase
- **Offline access** - No dependency on external services
- **Agent-friendly** - Claude Code can read/write issues directly
- **Simple** - Just markdown files, no complex tooling

## Issue Format

Each issue is a markdown file with YAML frontmatter:

```markdown
---
id: 001
title: Short descriptive title
status: open
priority: medium
created: 2025-01-15
---

## Description

Detailed description of what needs to be done.

## Tasks

- [ ] First task to complete
- [ ] Second task to complete
- [ ] Third task to complete

## Related Files

- `path/to/relevant/file.py`
- `another/file.ts`

## Notes

Any additional context or notes.
```

### Frontmatter Fields

| Field | Required | Values | Description |
|-------|----------|--------|-------------|
| `id` | Yes | Number | Unique identifier (e.g., 001, 002) |
| `title` | Yes | String | Short, descriptive title |
| `status` | Yes | `open`, `closed` | Current status |
| `priority` | Yes | `low`, `medium`, `high`, `critical` | Issue priority |
| `created` | Yes | YYYY-MM-DD | Creation date |
| `closed` | No | YYYY-MM-DD | Completion date (closed issues only) |

### File Naming

Files are named: `{id}-{slug}.md`

Examples:
- `001-setup-local-dev.md`
- `002-fix-auth-redirect.md`
- `003-add-export-feature.md`

## Workflow

### Creating an Issue

1. Determine the next available ID (check `open/` and `closed/`)
2. Create a new file in `issues/open/`
3. Fill in the frontmatter and content
4. Commit the file

```bash
# Example: Create issue 004
touch issues/open/004-my-new-issue.md
# Edit the file with proper format
git add issues/open/004-my-new-issue.md
git commit -m "docs: add issue 004 - my new issue"
```

### Working on an Issue

1. Read the issue to understand requirements
2. Complete the tasks listed
3. Check off tasks as you go (update the markdown)
4. Close the issue when done

### Closing an Issue

1. Update the frontmatter:
   - Change `status: open` to `status: closed`
   - Add `closed: YYYY-MM-DD`
2. Move the file from `open/` to `closed/`
3. Commit the change

```bash
# Update the file first, then:
mv issues/open/001-example.md issues/closed/
git add issues/
git commit -m "docs: close issue 001 - example issue"
```

## Using with Claude Code

The `/issues` skill provides commands for working with issues:

```
/issues              # List open issues
/issues create       # Create a new issue
/issues view 001     # View issue details
/issues close 001    # Close an issue
```

## Best Practices

1. **One issue per task** - Keep issues focused and well-scoped
2. **Clear titles** - Use action-oriented titles (e.g., "Add user export feature")
3. **Detailed descriptions** - Include context, requirements, and acceptance criteria
4. **Task checklists** - Break work into concrete, checkable tasks
5. **Link related files** - Help future readers understand the codebase impact
6. **Close promptly** - Move issues to `closed/` when complete

## Integration with PRs

When creating a PR that addresses an issue:

1. Reference the issue in your PR description: "Closes issue #001"
2. Close the issue when the PR is merged
3. The closed issue serves as documentation of what was done

## Migrating from External Trackers

If moving issues from GitHub/Linear/Jira:

1. Create a new markdown file for each issue
2. Copy relevant details into the format above
3. Link to the original issue in the Notes section
4. Mark external issue as "moved to local catalog"
