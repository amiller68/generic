---
description: Work with the local issue catalog
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Bash(mkdir:*)
  - Bash(mv:*)
---

Work with the local issue catalog in `issues/`.

## Overview

This project uses a local markdown-based issue tracking system. Issues are markdown files stored in:
- `issues/open/` - Open issues that need work
- `issues/closed/` - Resolved issues

## Commands

### List Open Issues

List all open issues with their IDs and titles:

```bash
# Read issues/open/ directory and summarize each issue
```

### View Issue Details

Read a specific issue file to see full details:
- Description
- Tasks checklist
- Related files
- Priority

### Create New Issue

Create a new issue file in `issues/open/` with the standard format:

```markdown
---
id: NNN
title: Issue title here
status: open
priority: medium
created: YYYY-MM-DD
---

## Description

Describe the issue here.

## Tasks

- [ ] Task 1
- [ ] Task 2

## Related Files

- `path/to/file.py`
```

Use the next available ID number (check existing issues first).

### Update Issue

Edit an existing issue to:
- Update task checklist
- Add notes
- Change priority

### Close Issue

Move a completed issue from `issues/open/` to `issues/closed/`:
1. Update the status in frontmatter to `closed`
2. Add `closed: YYYY-MM-DD` to frontmatter
3. Move file: `mv issues/open/NNN-*.md issues/closed/`

## Issue Format

All issues use this frontmatter format:

```yaml
---
id: 001
title: Short descriptive title
status: open | closed
priority: low | medium | high | critical
created: YYYY-MM-DD
closed: YYYY-MM-DD  # Only for closed issues
---
```

## Workflow

1. Check `issues/open/` for available work
2. Pick an issue to work on
3. Complete the tasks listed in the issue
4. Close the issue when done

See `issues/README.md` for full documentation.
