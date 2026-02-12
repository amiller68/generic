---
description: Initialize and customize template for your project
allowed-tools:
  - Read
  - Glob
  - Grep
  - AskUserQuestion
  - EnterPlanMode
---

Initialize and customize this template for your specific project.

## Your Role: Interviewer

You are conducting a friendly interview to understand what the user is building. Your goal is to:

1. **Understand their project** - What are they building? What problem does it solve?
2. **Identify their focus** - Which stack will they primarily work in?
3. **Configure identity** - Project name, domain, branding
4. **Clean up docs** - Remove template-specific documentation they won't need

**Philosophy reminder:** This template is fullstack by design. Don't push users to delete stacks or features. It's easier to ignore unused code than to re-add it later. Focus on configuration, not removal.

## The Interview

Have a conversation. Don't just fire off all questions at once - respond to their answers, ask follow-ups, and make it feel natural.

### Understanding Their Project

Start by asking what they're building. Get a sense of:
- What does the app do?
- Who is it for?
- What's the core functionality?

This context helps you make better suggestions throughout.

### Project Identity

Once you understand the project, gather:

- **Project name**: Used for packages, docker tags, 1Password vaults
  - Must be lowercase, no spaces (e.g., "myapp", "acme-dashboard")
- **Brief description**: One sentence for README and package.json

### Stack Focus

Ask which stack they'll primarily work in:

| Focus | Description |
|-------|-------------|
| **Python-focused** | FastAPI backend + HTMX/Jinja frontend (server-rendered) |
| **TypeScript-focused** | Vite SPA + Express API (React frontend) |
| **Both (Hybrid)** | Python API + Vite frontend |

**Important:** This is about focus, not removal. They keep both stacks either way. This just helps you tailor documentation and suggestions.

### Features Discussion

Rather than a checklist, discuss what they need:

- Do they need real-time updates? (WebSockets/SSE)
- Will there be background processing? (TaskIQ jobs)
- Is this multi-tenant (teams/orgs) or single-user?
- What auth approach? (Google OAuth is pre-configured, but they may want others)

Don't remove features they say "no" to - just note them for context.

## After the Interview

### Enter Plan Mode

Call `EnterPlanMode` with a plan covering:

**1. Project Identity Updates**
- Update `package.json` name fields
- Update `pyproject.toml` name fields
- Update `.env.project` PROJECT_NAME
- Update docker image tags in `config/deploy/*.yml`
- Update README.md title and description

**2. Documentation Cleanup**

Remove template-specific docs they won't need:
- `docs/customizing/` - they're done customizing
- Template README sections about "getting started with the template"
- Any placeholder content

Keep all technical documentation (deployment, patterns, database, etc.)

**3. Getting Deployment Working**

Don't ask about deployment - tell them what they need:

> To deploy, you'll need to:
> 1. **Set up 1Password** - Create a vault matching your project name, add required secrets (see `docs/setup/ONE_PASSWORD.md`)
> 2. **Provision infrastructure** - Run Terraform to create your server and DNS (see `docs/setup/INFRASTRUCTURE.md`)
> 3. **Configure Kamal** - Update `config/deploy/*.yml` with your server IP and domain
> 4. **Deploy** - Run `make kamal ARGS="py production deploy"`
>
> Full walkthrough: `docs/setup/WALKTHROUGH.md`

**4. CLAUDE.md Updates**

Update CLAUDE.md to reflect:
- Their project name and description
- Their primary stack focus
- Remove references to template customization (they're past that)

### Execute After Approval

Once approved:
- Make the file updates
- Run `make check` to verify nothing broke
- Commit with a message like "chore: initialize project as {project-name}"

## Reference Documentation

Point users to these docs:
- `docs/customizing/` - Customization guides (before you delete them)
- `docs/setup/WALKTHROUGH.md` - Full setup guide
- `docs/deployment/KAMAL.md` - Deployment reference
- `py/docs/PYTHON_LIBRARY_PATTERNS.md` - Python patterns
