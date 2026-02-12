# Project Setup

This guide covers the essential configuration files for customizing your project's identity and settings.

## Renaming the Project

### 1. Update `.env.project`

The project-wide configuration file:

```bash
PROJECT_NAME=your-project-name
DNS_ROOT_ZONE=yourdomain.com
```

This affects:
- Docker image tags
- 1Password vault names
- Database names
- Subdomain patterns

### 2. Update Python Package Name

In `py/pyproject.toml`:

```toml
[project]
name = "your-project-name"
```

Also update individual packages if needed:
- `py/apps/py-app/pyproject.toml`
- `py/packages/py-core/pyproject.toml`

### 3. Update TypeScript Package Name

In `ts/package.json`:

```json
{ "name": "your-project-name" }
```

### 4. Update Docker Tags

In `config/deploy/*.yml`, update image references:

```yaml
image: your-dockerhub-username/your-project-name
```

## Environment Variables

### `.env.project`

Project configuration (committed to git):

```bash
PROJECT_NAME=generic
DNS_ROOT_ZONE=example.com
```

### `.env.vault`

1Password vault references (committed):

```bash
OP_VAULT_NAME=your-project-name
```

### `.env` (local)

Local development overrides (not committed):

```bash
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

## Domain Configuration

### Changing Domains

1. Update `.env.project`:
   ```bash
   DNS_ROOT_ZONE=yourdomain.com
   ```

2. Update Terraform configuration in `iac/` for Cloudflare DNS

3. Re-run infrastructure deployment:
   ```bash
   cd iac && terraform apply
   ```

### Subdomain Patterns

The template uses subdomains for environments:

| Environment | Pattern |
|-------------|---------|
| Production | `app.yourdomain.com` |
| Staging | `staging.yourdomain.com` |
| Preview | `preview.yourdomain.com` |

## File Reference

| File | Purpose |
|------|---------|
| `.env.project` | Project-wide config (committed) |
| `.env.vault` | 1Password vault paths (committed) |
| `.env` | Local overrides (not committed) |
| `Makefile` | Root build commands |
| `docker-compose.yml` | Local development services |
| `CLAUDE.md` | Agent instructions |
