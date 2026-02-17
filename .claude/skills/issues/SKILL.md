---
description: Discover and manage file-based work items. Use to explore tasks before spawning workers or to track project progress.
allowed-tools:
  - Bash(ls:*)
  - Bash(cat:*)
  - Bash(find:*)
  - Bash(grep:*)
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

Discover and manage work items for the project.

Run this command to explore what needs to be done before spawning workers with `/jig`.

## Actions

### List issues

Scan `issues/*.md` and extract from each file:
- Filename
- Title (first `# ` heading)
- Status (from `**Status:**` field)
- Epic (from `**Epic:**` field, for tickets)

Group tickets under their parent epic. Show status with indicators:
- `[ ]` Planned
- `[~]` In Progress
- `[x]` Complete
- `[!]` Blocked

Highlight which tickets are ready to work on (status: Planned, no blockers).

### Show issue

Read a specific issue file and display its full contents.

### Create epic

Create a new epic file using the convention from `issues/README.md`.

### Create ticket

Create a new ticket file linked to an epic, using `issues/_template.md`.

### Update status

Change a ticket's status field (Planned → In Progress → Complete).

## Convention

See `issues/README.md` for the full issue tracking convention.

## External Trackers

This uses file-based issue tracking by default. For external trackers like Linear, Jira, or GitHub Issues, use their respective MCP tools or CLI (`gh issue`) instead and skip the file scanning.
