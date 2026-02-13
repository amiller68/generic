# 1Password Setup Guide

This guide explains how to set up 1Password for secrets management in the deployment framework.

## Overview

The platform uses 1Password as the single source of truth for all secrets:
- **Cloud provider credentials** (Digital Ocean, Cloudflare, Terraform Cloud, Docker Hub)
- **Stage-specific app secrets** (OAuth clients, API keys, database passwords)
- **No secrets in git** - everything loaded from vaults at runtime

All scripts (`bin/vault`, `bin/iac`, `bin/kamal`) automatically inject secrets from 1Password using the paths defined in `.env.vault`.

## Prerequisites

### 1. 1Password Account

You need a 1Password account with:
- Personal account (or team/business account)
- Ability to create vaults
- 1Password CLI access

### 2. Install 1Password CLI

```bash
# macOS (Homebrew)
brew install --cask 1password-cli

# Verify installation
op --version
```

### 3. Authenticate CLI

```bash
# Sign in to your 1Password account
op signin

# Or if already signed in
eval $(op signin)
```

## Vault Structure

The platform requires two types of vaults:

### 1. Cloud Providers Vault (`cloud-providers`)

Contains credentials shared across all projects and stages:

```
cloud-providers/
├── TERRAFORM_CLOUD_API_TOKEN
├── DO_API_TOKEN
├── CLOUDFLARE_DNS_API_TOKEN
├── DOCKER_HUB_LOGIN
└── DOCKER_HUB_TOKEN
```

### 2. Stage Vaults (`${PROJECT_NAME}-${STAGE}`)

One vault per stage, containing app-specific secrets:

```
generic-production/
├── GOOGLE_O_AUTH_CLIENT
└── ... (other app secrets)

generic-staging/
├── GOOGLE_O_AUTH_CLIENT
└── ... (other app secrets)
```

The vault name follows the pattern: `${PROJECT_NAME}-${STAGE}` (e.g., `generic-production`, `generic-staging`).

## Setting Up Vaults

### Step 1: Create Cloud Providers Vault

This vault is shared across all your projects that use the same cloud providers.

1. Open 1Password app
2. Create a new vault named `cloud-providers`
3. Set appropriate permissions (you need read/write access)

Or via CLI:
```bash
# Note: Vault creation via CLI requires appropriate account permissions
op vault create "cloud-providers"
```

### Step 2: Add Cloud Provider Credentials

Add each cloud provider credential to the `cloud-providers` vault:

#### Terraform Cloud API Token

1. Go to [Terraform Cloud tokens](https://app.terraform.io/app/settings/tokens)
2. Create a new API token
3. Add to 1Password:

```bash
op item create \
  --category=login \
  --title=TERRAFORM_CLOUD_API_TOKEN \
  --vault=cloud-providers \
  credential=YOUR_TF_CLOUD_TOKEN
```

#### Digital Ocean API Token

1. Go to [Digital Ocean API](https://cloud.digitalocean.com/account/api/tokens)
2. Generate new personal access token with read/write scope
3. Add to 1Password:

```bash
op item create \
  --category=login \
  --title=DO_API_TOKEN \
  --vault=cloud-providers \
  credential=YOUR_DO_TOKEN
```

#### Cloudflare API Token

1. Go to [Cloudflare API Tokens](https://dash.cloudflare.com/profile/api-tokens)
2. Create token with `Zone:DNS:Edit` permissions for your domain
3. Add to 1Password:

```bash
op item create \
  --category=login \
  --title=CLOUDFLARE_DNS_API_TOKEN \
  --vault=cloud-providers \
  credential=YOUR_CF_TOKEN
```

#### Docker Hub Credentials

1. Go to [Docker Hub](https://hub.docker.com/)
2. Get your username and password
3. Create an access token (Settings > Security > Access Tokens)
4. Add login credentials:

```bash
op item create \
  --category=login \
  --title=DOCKER_HUB_LOGIN \
  --vault=cloud-providers \
  username=YOUR_DOCKER_USERNAME \
  credential=YOUR_DOCKER_PASSWORD
```

5. Add access token:

```bash
op item create \
  --category=login \
  --title=DOCKER_HUB_TOKEN \
  --vault=cloud-providers \
  credential=YOUR_DOCKER_ACCESS_TOKEN
```

**Note**: Currently the Terraform Docker Hub provider requires your actual password, not just an access token. See [TERRAFORM_CLOUD.md](./TERRAFORM_CLOUD.md) for details.

### Step 3: Create Stage Vaults

Create a vault for each stage (production, staging, etc.):

```bash
# Production vault
op vault create "generic-production"

# Staging vault (if you have a staging environment)
op vault create "generic-staging"
```

Replace `generic` with your `PROJECT_NAME` from `.env.project`.

### Step 4: Add Stage-Specific Secrets

For each stage vault, add the required app secrets:

#### Google OAuth Client (for Python app)

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create OAuth 2.0 Client ID
3. Add authorized redirect URIs:
   - `https://app.yourdomain.com/auth/google/callback` (production)
   - `http://localhost:8000/auth/google/callback` (development)
4. Add to 1Password:

```bash
op item create \
  --category=login \
  --title=GOOGLE_O_AUTH_CLIENT \
  --vault=generic-production \
  username=YOUR_CLIENT_ID \
  credential=YOUR_CLIENT_SECRET
```

## Verifying Setup

### Check Vault Access

```bash
# List all vaults
op vault list

# List items in cloud-providers vault
op item list --vault=cloud-providers

# List items in production vault
op item list --vault=generic-production
```

### Test Secret Reading

Using the `bin/vault` script:

```bash
# Test reading cloud provider credentials
bin/vault read DOCKER_HUB_USERNAME
bin/vault read CLOUDFLARE_API_TOKEN

# Test reading stage-specific secrets (requires STAGE env var)
STAGE=production bin/vault read GOOGLE_O_AUTH_CLIENT_ID
```

Expected output: The actual secret value (not an error).

### Verify `.env.vault` Paths

All secret paths in `.env.vault` should match your 1Password structure:

```bash
# Cloud provider secrets (from cloud-providers vault)
TF_TOKEN=op://cloud-providers/TERRAFORM_CLOUD_API_TOKEN/credential
DOCKER_HUB_USERNAME=op://cloud-providers/DOCKER_HUB_LOGIN/username

# Stage-specific secrets (from ${PROJECT_NAME}-${STAGE} vault)
GOOGLE_O_AUTH_CLIENT_ID=op://${VAULT_SLUG}/GOOGLE_O_AUTH_CLIENT/username
```

Where `${VAULT_SLUG}` = `${PROJECT_NAME}-${STAGE}`.

## CI/CD Setup (Optional)

For automated deployments in GitHub Actions or other CI systems:

### 1. Create Service Account

1. Go to [1Password Integrations](https://my.1password.com/integrations/active)
2. Create a new service account
3. Grant access to required vaults:
   - `cloud-providers` (read-only)
   - `generic-production` (read-only)
   - Any other stage vaults
4. Copy the service account token (starts with `ops_`)

### 2. Add to CI/CD Secrets

For GitHub Actions:

1. Go to repository Settings > Secrets > Actions
2. Add secret:
   - Name: `OP_SERVICE_ACCOUNT_TOKEN`
   - Value: Your service account token

### 3. Use in Workflows

The service account token allows CI/CD to read secrets:

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy:
    runs-on: ubuntu-latest
    env:
      OP_SERVICE_ACCOUNT_TOKEN: ${{ secrets.OP_SERVICE_ACCOUNT_TOKEN }}
    steps:
      - uses: actions/checkout@v3

      # Install 1Password CLI
      - name: Install 1Password CLI
        run: |
          curl -sSfLo op.zip https://cache.agilebits.com/dist/1P/op2/pkg/v2.20.0/op_linux_amd64_v2.20.0.zip
          unzip op.zip && sudo mv op /usr/local/bin/

      # Secrets automatically loaded by bin/iac and bin/kamal
      - name: Deploy infrastructure
        run: make iac production apply
```

## Security Best Practices

### 1. Principle of Least Privilege

- **Personal development**: Use your personal 1Password account with full access
- **CI/CD**: Use service accounts with read-only access to specific vaults
- **Team members**: Grant vault access on a per-project basis

### 2. Separate Staging and Production

Always use separate vaults for different stages:
- Different OAuth clients
- Different API keys
- Different database passwords

This prevents staging activities from affecting production.

### 3. Rotate Secrets Regularly

Update secrets periodically:
1. Generate new API token/key in the provider
2. Update 1Password item
3. Redeploy services (they'll pick up new secrets)
4. Revoke old token/key

### 4. Never Commit Secrets

The `.env.vault` file contains **paths** to secrets, not actual secrets:

```bash
# Safe to commit (paths only)
DOCKER_HUB_USERNAME=op://cloud-providers/DOCKER_HUB_LOGIN/username

# NEVER commit (actual secret)
DOCKER_HUB_USERNAME=myusername
```

## Troubleshooting

### "Item not found in vault"

Check:
1. Vault name matches exactly (case-sensitive)
2. Item title matches exactly
3. You have access to the vault
4. CLI is authenticated: `op signin`

List items to verify:
```bash
op item list --vault=cloud-providers
```

### "Unable to authenticate"

Re-authenticate the CLI:
```bash
op signin
# Or
eval $(op signin)
```

### "Permission denied"

Ensure:
1. You have read access to the vault
2. Service account (if CI/CD) has been granted vault access
3. Vault exists: `op vault list`

### Environment Variable Not Set

The `bin/vault` script requires certain env vars:

```bash
# For cloud provider credentials
bin/vault read DOCKER_HUB_USERNAME  # Works (no STAGE needed)

# For stage-specific secrets
STAGE=production bin/vault read GOOGLE_O_AUTH_CLIENT_ID  # Needs STAGE
```

Or set in `.env.project`:
```bash
export CLOUD_VAULT=cloud-providers  # Required
export PROJECT_NAME=generic         # Required for stage vaults
```

## Adding New Secrets

When adding a new secret to your application:

1. **Update `.env.vault`** with the 1Password path:
   ```bash
   # Add to .env.vault
   NEW_API_KEY=op://${VAULT_SLUG}/NEW_API_KEY/credential
   ```

2. **Add secret to 1Password**:
   ```bash
   op item create \
     --category=login \
     --title=NEW_API_KEY \
     --vault=generic-production \
     credential=YOUR_API_KEY_VALUE
   ```

3. **Export in deployment script** (if needed by Terraform/Kamal):
   ```bash
   # Add to bin/iac or bin/kamal if Terraform/Kamal needs it
   export TF_VAR_new_api_key=$(read_from_vault NEW_API_KEY)
   ```

4. **Use in your app**:
   ```python
   # Python app reads from environment
   import os
   api_key = os.getenv("NEW_API_KEY")
   ```

The `run_with_vault` function in deployment scripts automatically loads all secrets from `.env.vault` into the environment.

## Next Steps

Once 1Password is configured:

1. **[Terraform Cloud Setup](./TERRAFORM_CLOUD.md)** - Create TFC org and workspaces
2. **[Infrastructure Setup](./INFRASTRUCTURE.md)** - Deploy servers with `make iac`
3. **[Kamal Deployment](../deployment/KAMAL.md)** - Deploy your apps

All subsequent steps will automatically load secrets from 1Password.
