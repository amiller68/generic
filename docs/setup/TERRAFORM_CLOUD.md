# Terraform Cloud Setup Guide

This guide explains how to set up Terraform Cloud for managing infrastructure state across multiple stages.

## Overview

The platform uses Terraform Cloud for:
- **Remote state storage** - Shared, versioned infrastructure state
- **Workspace management** - Separate state for each stage (production, staging, container-registry)
- **Local execution** - Plans and applies run on your machine with access to local files and 1Password

Our `bin/tfc` script automates workspace creation and configuration.

## Prerequisites

### 1. Terraform Cloud Account

Create a free account at [app.terraform.io](https://app.terraform.io).

**Important**: Your `PROJECT_NAME` in `.env.project` must be globally unique, as it will be used to create a Terraform Cloud organization named `${PROJECT_NAME}-org`. TFC organization names are unique across all users.

### 2. Create API Token

1. Go to [Terraform Cloud tokens](https://app.terraform.io/app/settings/tokens)
2. Create a new API token
3. Copy the token value

### 3. Add Token to 1Password

Add your TFC token to the `cloud-providers` vault:

```bash
op item create \
  --category=login \
  --title=TERRAFORM_CLOUD_API_TOKEN \
  --vault=cloud-providers \
  credential=YOUR_TFC_TOKEN
```

Verify it's accessible:
```bash
bin/vault read TF_TOKEN
```

### 4. Install Terraform CLI

```bash
# macOS
brew install terraform

# Verify installation
terraform --version
```

## Workspace Structure

The platform creates workspaces based on stages defined in `.env.project`:

```
${PROJECT_NAME}-org/
├── generic-container-registry    # Docker registry resources
├── generic-production            # Production infrastructure
└── generic-staging               # Staging infrastructure (optional)
```

Workspace names follow the pattern: `${PROJECT_NAME}-${STAGE}`.

## Setup Workflow

### Step 1: Create Organization and Workspaces

Use `bin/tfc` to automatically create the organization and all workspaces:

```bash
# Create org and workspaces for all stages
make tfc up
```

This will:
1. Create organization `generic-org` (or `${PROJECT_NAME}-org`)
2. Create workspaces for each stage in `iac/stages/`:
   - `generic-container-registry`
   - `generic-production`
   - Any other stages you've defined
3. Configure each workspace for local execution
4. Generate `terraform.tf` backend configs in `iac/stages/*/`

Expected output:
```
Creating Terraform Cloud Organization
✓ Organization 'generic-org' is ready

Creating Terraform Workspace: generic-container-registry
✓ Workspace 'generic-container-registry' is ready
✓ Backend configuration created at iac/stages/container-registry/terraform.tf

Creating Terraform Workspace: generic-production
✓ Workspace 'generic-production' is ready
✓ Backend configuration created at iac/stages/production/terraform.tf
```

### Step 2: Configure Default Execution Mode

**CRITICAL**: You must manually configure the organization to use local execution mode.

1. Go to [app.terraform.io](https://app.terraform.io)
2. Navigate to your organization (e.g., `generic-org`)
3. Click **Settings** in the left sidebar
4. Select **General** settings
5. Find **Default Execution Mode**
6. Select **Local**
7. Click **Update organization**

**Why local execution?**
- Our Terraform configs read from local Kamal deployment files
- Environment variables are passed from our local environment
- 1Password integration requires local vault access

### Step 3: Verify Setup

Check that workspaces were created:

```bash
make tfc status
```

Expected output:
```
Terraform Cloud Status
✓ Organization 'generic-org' exists

Checking workspaces
  ✓ generic-container-registry exists
  ✓ generic-production exists
```

### Step 4: Initialize Terraform

Initialize each workspace locally:

```bash
# Initialize container registry workspace
make iac container-registry init

# Initialize production workspace
make iac production init
```

This connects your local Terraform to the remote state in Terraform Cloud.

Expected output:
```
Initializing Terraform Cloud...
Terraform Cloud has been successfully initialized!
```

## Workspace Configuration

Each workspace is configured with:

- **Name**: `${PROJECT_NAME}-${STAGE}` (e.g., `generic-production`)
- **Execution mode**: Local (runs on your machine)
- **Auto-apply**: Disabled (manual confirmation required)
- **Description**: "Workspace for {stage} environment"
- **Global remote state**: Enabled (other workspaces can read outputs)

Configuration is stored in `iac/stages/${STAGE}/terraform.tf`:

```hcl
terraform {
  cloud {
    organization = "generic-org"
    workspaces {
      name = "generic-production"
    }
  }
}
```

## Using Terraform Cloud

### Check Workspace Status

View state, runs, and outputs in the Terraform Cloud UI:

1. Go to [app.terraform.io](https://app.terraform.io)
2. Select your organization
3. Click on a workspace (e.g., `generic-production`)
4. View:
   - **States** - Current and historical infrastructure state
   - **Runs** - Plan and apply history
   - **Variables** - Workspace variables (we don't use these)

### Local Operations

All Terraform operations run locally via `bin/iac`:

```bash
# Plan changes (runs locally, reads from remote state)
make iac production plan

# Apply changes (runs locally, writes to remote state)
make iac production apply

# View outputs
make iac production output

# Show current state
make iac production show
```

The state is automatically synced to/from Terraform Cloud.

### State Locking

Terraform Cloud automatically locks state during operations:
- Prevents concurrent modifications
- Shows who has the lock
- Auto-releases after operation completes

If a lock gets stuck:
```bash
# In Terraform Cloud UI, go to workspace -> Settings -> General -> Force unlock
```

### State Versioning

Terraform Cloud keeps a history of all state changes:
- View previous states in the UI
- Rollback if needed
- Compare state versions

## Advanced Configuration

### Per-Workspace Execution Mode

Override execution mode for a specific workspace:

1. Go to workspace in Terraform Cloud
2. Settings -> General -> Execution Mode
3. Select **Local** or **Remote** as needed

### Workspace Variables (Optional)

While we use 1Password for secrets, you can set Terraform variables in the UI:

1. Go to workspace -> Variables
2. Add variable:
   - **Terraform Variables**: Available as `var.name`
   - **Environment Variables**: Available as `env.NAME`

**Note**: Our `bin/iac` script passes all variables via `TF_VAR_*` environment variables, so workspace variables are generally not needed.

### Remote State Sharing

Workspaces can read outputs from other workspaces:

```hcl
# In iac/stages/production/main.tf
data "terraform_remote_state" "registry" {
  backend = "remote"

  config = {
    organization = "generic-org"
    workspaces = {
      name = "generic-container-registry"
    }
  }
}

# Use outputs from container-registry workspace
output "registry_url" {
  value = data.terraform_remote_state.registry.outputs.registry_url
}
```

## Troubleshooting

### "Organization already exists" (HTTP 422)

**If you own the organization**: This is expected when running `make tfc up` multiple times. The script handles this gracefully and continues to create workspaces.

**If someone else owns the organization**: Your `PROJECT_NAME` is not globally unique. Terraform Cloud organization names must be unique across all TFC users. Change `PROJECT_NAME` in `.env.project` to something more unique (e.g., add your username or company name: `mycompany-generic`).

### "Unable to authenticate"

Check:
1. TFC token is in 1Password: `bin/vault read TF_TOKEN`
2. Token has proper permissions (organization management)
3. CLI is authenticated: `eval $(op signin)`

### "Workspace not found"

Ensure:
1. Workspace was created: `make tfc status`
2. Name matches pattern: `${PROJECT_NAME}-${STAGE}`
3. Organization name is correct in `terraform.tf`

### "Backend initialization required"

Run `terraform init` for the workspace:
```bash
make iac production init
```

### "File not found" errors during plan/apply

Ensure execution mode is set to **Local**:
1. Check organization default: Settings -> General -> Default Execution Mode
2. Check workspace override: Workspace -> Settings -> General -> Execution Mode

Remote execution cannot access local files like `config/deploy/*.yml`.

### "Environment variables not working"

For local execution:
1. The execution mode must be **Local** (not Remote)
2. Our `bin/iac` script passes variables via `TF_VAR_*` prefix
3. Check variables are exported: `env | grep TF_VAR`

Example:
```bash
# bin/iac sets these before running terraform
export TF_VAR_project_name="${PROJECT_NAME}"
export TF_VAR_dns_root_zone="${DNS_ROOT_ZONE}"
```

## Docker Hub Authentication Issue

**Known Issue**: The Terraform Docker Hub provider requires your actual Docker Hub **password**, not an access token.

### Current Setup (Temporary)

In 1Password `cloud-providers` vault:
- **DOCKER_HUB_LOGIN**:
  - Username field: Your Docker Hub username
  - Credential field: Your actual Docker Hub **password** (not access token)

### Why This Is Not Ideal

1. **Security**: Passwords have full account access vs. scoped tokens
2. **Rotation**: Changing passwords affects all integrations
3. **Audit**: No per-token tracking of usage

### Planned Improvements

We're investigating:
1. **Different Terraform provider** that supports access tokens
2. **Direct API calls** for registry management
3. **GitHub Container Registry** (better token support)

## Managing Stages

### Adding a New Stage

To add a staging environment:

1. **Create infrastructure directory**:
   ```bash
   mkdir -p iac/stages/staging
   ```

2. **Create Terraform configuration**:
   ```bash
   # Copy from production as template
   cp -r iac/stages/production/* iac/stages/staging/
   ```

3. **Create workspace**:
   ```bash
   make tfc up  # Automatically detects new stage
   ```

4. **Initialize**:
   ```bash
   make iac staging init
   ```

5. **Create stage vault in 1Password**:
   ```bash
   op vault create "generic-staging"
   ```

6. **Deploy**:
   ```bash
   make iac staging apply
   ```

### Removing a Stage

To remove a stage (e.g., staging):

1. **Destroy infrastructure**:
   ```bash
   make iac staging destroy
   ```

2. **Remove directory**:
   ```bash
   rm -rf iac/stages/staging
   ```

3. **Delete workspace in TFC UI**:
   - Go to workspace -> Settings -> Destruction and Deletion
   - Delete workspace

## Next Steps

Once Terraform Cloud is configured:

1. **[Deploy Container Registry](./INFRASTRUCTURE.md#container-registry-setup)** - `make iac container-registry apply`
2. **[Deploy Production Infrastructure](./INFRASTRUCTURE.md#production-setup)** - `make iac production apply`
3. **[Deploy Applications](../deployment/KAMAL.md)** - `make kamal ARGS="..."`

All subsequent infrastructure operations will use Terraform Cloud for state management.
