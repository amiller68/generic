# Infrastructure Setup Guide

This guide explains how to deploy infrastructure using Terraform with 1Password for secrets management.

## Overview

The platform uses Terraform to provision:
- **Container Registry** (Docker Hub repositories for your services)
- **Digital Ocean Droplets** (VM servers for each stage)
- **Cloudflare DNS** (Domain records pointing to your servers)
- **SSH Keys** (Auto-generated for server access)
- **Firewall Rules** (HTTP/HTTPS/SSH access)

All managed via a single command: `make iac <stage> <command>`

## Prerequisites

Before proceeding, ensure you've completed:

1. **[1Password Setup](./ONE_PASSWORD.md)** - Vaults configured with cloud credentials
2. **[Terraform Cloud Setup](./TERRAFORM_CLOUD.md)** - Organization and workspaces created

## Infrastructure Stages

The platform supports multiple stages (environments):

```
Stages (in .env.project):
├── container-registry   # Docker Hub repositories (shared across stages)
├── production          # Production servers and DNS
└── staging             # Staging servers and DNS (optional)
```

Each stage is deployed independently via `make iac <stage> <command>`.

## Deployment Workflow

Deploy stages in this order:

1. **Container Registry** - Create Docker repositories first
2. **Production/Staging** - Deploy servers and configure DNS

## Container Registry Setup

The container registry stage creates Docker Hub repositories for your services.

### Step 1: Initialize Terraform

```bash
make iac container-registry init
```

This connects to Terraform Cloud workspace and downloads required providers.

### Step 2: Review Plan

```bash
make iac container-registry plan
```

Expected resources:
- Docker Hub repositories for each service in `SERVICES` (.env.project)
- Example: `yourorg/generic-py`, `yourorg/generic-ts`

### Step 3: Apply Configuration

```bash
make iac container-registry apply
```

Terraform will:
1. Authenticate to Docker Hub using credentials from 1Password
2. Create repositories (public or private based on `USE_PRIVATE_REPOS`)
3. Configure repository descriptions
4. Store state in Terraform Cloud

Expected output:
```
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

repository_urls = {
  "py" = "yourorg/generic-py"
  "ts" = "yourorg/generic-ts"
}
```

### Step 4: Verify Repositories

Check Docker Hub:
```bash
# List repositories
docker search yourorg/generic
```

Or view in [Docker Hub UI](https://hub.docker.com/repositories).

## Production Setup

The production stage deploys a Digital Ocean droplet with Docker pre-installed.

### Step 1: Initialize Terraform

```bash
make iac production init
```

### Step 2: Review Infrastructure Plan

```bash
make iac production plan
```

Expected resources:
- **Droplet**: Ubuntu 22.04 LTS, 1GB RAM, NYC3 region
- **SSH Key**: Auto-generated ED25519 key pair
- **Firewall**: Rules for HTTP (80), HTTPS (443), SSH (22)
- **Cloudflare DNS**: A records for your services
- **Cloud-init**: Docker, Docker Compose, swap file, UFW firewall

### Step 3: Deploy Infrastructure

```bash
make iac production apply
```

This will:
1. Generate SSH key pair
2. Create Digital Ocean droplet
3. Configure firewall rules
4. Install Docker via cloud-init
5. Create DNS records in Cloudflare
6. Save SSH private key locally

Expected output:
```
Apply complete! Resources: 5 added, 0 changed, 0 destroyed.

Outputs:

server_ip = "147.182.XXX.XXX"
ssh_connect_command = "ssh -i iac/stages/production/ssh-keys/generic-production.pem root@147.182.XXX.XXX"
dns_records = {
  "py" = "app.yourdomain.com -> 147.182.XXX.XXX"
  "ts" = "yourdomain.com -> 147.182.XXX.XXX"
}
```

### Step 4: Verify Deployment

Check server is online:
```bash
# Get server IP
make iac production output server_ip

# SSH into server
bin/ssh production

# Verify Docker is installed
docker --version
docker-compose --version
```

Expected: Docker version 24.x and Docker Compose version 2.x.

### Step 5: Verify DNS

Check DNS records are propagating:
```bash
# Get DNS records
make iac production output dns_records

# Check DNS resolution
dig yourdomain.com
dig app.yourdomain.com
```

**Note**: DNS propagation can take a few minutes.

## What Gets Deployed

### Digital Ocean Droplet

**Default Configuration:**
- **Name**: `generic-production` (or `${PROJECT_NAME}-${STAGE}`)
- **Size**: `s-1vcpu-1gb` (1 vCPU, 1GB RAM) - $6/month
- **Region**: NYC3
- **OS**: Ubuntu 22.04 LTS
- **Monitoring**: Enabled

**Cloud-init Setup:**
- Docker Engine and Docker Compose
- 1GB swap file
- UFW firewall (configured but disabled for Kamal)
- System updates
- Monitoring agent

### SSH Key

Auto-generated ED25519 key pair:
- **Private key**: Saved to `iac/stages/${STAGE}/ssh-keys/${PROJECT_NAME}-${STAGE}.pem`
- **Public key**: Added to droplet
- **Permissions**: 600 (read/write for owner only)

**Note**: Private key is **not** committed to git (excluded via `.gitignore`).

### Firewall Rules

**Inbound:**
- SSH (22): Open to all (should restrict - see Security section)
- HTTP (80): Open to all
- HTTPS (443): Open to all

**Outbound:**
- All traffic allowed

### Cloudflare DNS

A records for each service:
- Root domain (`yourdomain.com`) -> Droplet IP (for `ts` service)
- Subdomains (`app.yourdomain.com`) -> Droplet IP (for `py` service)

Based on `SERVICES` configuration in `.env.project`:
```bash
SERVICES="py:app,ts-web:"
# Means: py -> app subdomain, ts-web -> root domain
```

## Infrastructure Outputs

View all outputs:
```bash
make iac production output
```

Common outputs:
```bash
# Server IP address
make iac production output server_ip

# SSH connection command
make iac production output ssh_connect_command

# SSH private key (for scripts)
make iac production output -raw ssh_private_key

# DNS records
make iac production output dns_records
```

## SSH Access

### Using bin/ssh (Recommended)

```bash
# SSH as root
bin/ssh production

# SSH as specific user
bin/ssh production ubuntu
```

The script automatically:
- Loads SSH private key from Terraform outputs
- Connects to correct server IP
- Uses proper SSH options (disables host key checking for ephemeral servers)

### Manual SSH

Get the SSH command from Terraform:
```bash
make iac production output -raw ssh_connect_command | sh
```

Or construct manually:
```bash
ssh -i iac/stages/production/ssh-keys/generic-production.pem root@SERVER_IP
```

## Managing Infrastructure

### Update Droplet Size

Edit `iac/stages/production/variables.tf`:
```hcl
variable "droplet_size" {
  default = "s-2vcpu-2gb"  # Upgrade to 2GB RAM
}
```

Apply changes:
```bash
make iac production plan   # Review changes
make iac production apply  # Apply update
```

**Note**: Resizing may cause brief downtime.

### Update Firewall Rules

Edit `iac/modules/server/firewall.tf`:
```hcl
# Restrict SSH to your IP only
variable "ssh_allowed_ips" {
  default = ["YOUR_IP/32"]
}
```

Apply:
```bash
make iac production apply
```

### Add New Service

1. **Update `.env.project`**:
   ```bash
   SERVICES="py:app,ts-web:,static:static"
   # Added static service
   ```

2. **Update infrastructure**:
   ```bash
   make iac container-registry apply  # Create new repository
   make iac production apply          # Add DNS record
   ```

3. **Create Kamal config**:
   ```bash
   cp config/deploy/py.yml config/deploy/static.yml
   # Edit static.yml for your service
   ```

### Destroy Infrastructure

**CAREFUL**: This deletes all infrastructure for the stage.

```bash
# Destroy production (asks for confirmation)
make iac production destroy

# Destroy container registry (asks for confirmation)
make iac container-registry destroy
```

To destroy without confirmation (CI/CD):
```bash
make iac production destroy -auto-approve
```

### Check Current State

```bash
# List all resources in stage
make iac production state list

# Show detailed state
make iac production show

# Show specific resource
make iac production state show digitalocean_droplet.main
```

## Staging Environment (Optional)

To deploy a staging environment:

### Step 1: Create Stage Directory

```bash
mkdir -p iac/stages/staging
```

### Step 2: Copy Production Config

```bash
# Copy Terraform config from production
cp -r iac/stages/production/* iac/stages/staging/

# Edit staging-specific values if needed
# (Usually the same as production, just separate state)
```

### Step 3: Create Staging Vault

```bash
# In 1Password
op vault create "generic-staging"

# Add staging secrets (same structure as production)
# See ONE_PASSWORD.md for details
```

### Step 4: Create Workspace

```bash
# Creates generic-staging workspace
make tfc up
```

### Step 5: Deploy Staging

```bash
# Initialize
make iac staging init

# Deploy infrastructure
make iac staging plan
make iac staging apply
```

Staging and production are completely separate:
- Different servers
- Different DNS records (uses stage-specific subdomains)
- Different secrets (from `generic-staging` vault)
- Different state (separate TFC workspace)

## Cost Estimation

Running production infrastructure:

**Compute:**
- Droplet (s-1vcpu-1gb): $6/month
- Bandwidth: 1TB included
- Backups (optional): +20% ($1.20/month)

**DNS:**
- Cloudflare: Free

**Other:**
- Terraform Cloud: Free (up to 500 resources)
- Docker Hub: Free (public repos) or $5/month (private repos)

**Total minimum**: $6-15/month

## Security Recommendations

### 1. Restrict SSH Access

**Critical**: Default firewall allows SSH from anywhere. Restrict to your IP:

Edit `iac/modules/server/firewall.tf`:
```hcl
variable "ssh_allowed_ips" {
  default = ["YOUR_IP/32"]  # Replace with your IP
}
```

Get your IP:
```bash
curl ifconfig.me
```

Apply:
```bash
make iac production apply
```

### 2. Enable Backups

Edit `iac/stages/production/main.tf`:
```hcl
module "server" {
  source = "../../modules/server"

  backups = true  # Enable weekly backups (+20% cost)
  # ...
}
```

### 3. Use SSH Key Agent

For better security, use SSH agent instead of storing private key:

```bash
# Add key to agent
ssh-add iac/stages/production/ssh-keys/generic-production.pem

# Connect (no -i flag needed)
ssh root@$(make iac production output -raw server_ip)
```

### 4. Rotate SSH Keys

To rotate SSH keys:

```bash
# Taint the SSH key resource
make iac production taint tls_private_key.ssh_key

# Apply to generate new key
make iac production apply
```

**Warning**: This will regenerate the key and update the droplet. Brief SSH downtime.

### 5. Monitor Access

Check Digital Ocean monitoring dashboard for:
- CPU/memory usage
- Bandwidth consumption
- Droplet status

Or SSH to server:
```bash
bin/ssh production
docker stats  # Container resource usage
```

## Troubleshooting

### "Error: Unable to authenticate"

Check Digital Ocean token:
```bash
# Verify token is accessible
bin/vault read DIGITALOCEAN_TOKEN

# Test authentication
curl -X GET \
  -H "Authorization: Bearer $(bin/vault read DIGITALOCEAN_TOKEN)" \
  "https://api.digitalocean.com/v2/account"
```

Expected: JSON with account info.

### "Error: Error creating droplet"

Common causes:
1. **Insufficient resources**: DO account limit reached
2. **Region unavailable**: Try different region in `variables.tf`
3. **Invalid size**: Check available sizes:
   ```bash
   doctl compute size list  # Requires doctl CLI
   ```

### "Backend initialization required"

Run terraform init:
```bash
make iac production init
```

### DNS Not Resolving

Check:
1. **Cloudflare API token**: `bin/vault read CLOUDFLARE_API_TOKEN`
2. **Zone exists**: Verify `DNS_ROOT_ZONE` in `.env.project` matches Cloudflare zone
3. **Propagation time**: Wait 5-10 minutes, then check again:
   ```bash
   dig yourdomain.com
   ```

### SSH Connection Refused

1. **Check firewall**: Ensure your IP is allowed
2. **Wait for cloud-init**: First boot takes 2-3 minutes for cloud-init
3. **Check droplet status**:
   ```bash
   # Via Terraform
   make iac production show digitalocean_droplet.main

   # Or via DO API
   doctl compute droplet list
   ```

### State Locked

If Terraform state is locked:

1. **Check Terraform Cloud**: Go to workspace -> see who has lock
2. **Wait**: Lock auto-releases when operation completes
3. **Force unlock** (last resort):
   ```bash
   # In TFC UI: Workspace -> Settings -> Force unlock
   ```

### Docker Not Installed

Cloud-init may have failed. SSH to server and check:

```bash
bin/ssh production

# Check cloud-init status
cloud-init status

# View cloud-init logs
less /var/log/cloud-init-output.log

# Manually install Docker if needed
curl -fsSL https://get.docker.com | sh
```

## Advanced Operations

### Import Existing Resources

To bring existing infrastructure under Terraform management:

```bash
# Example: Import existing droplet
make iac production import digitalocean_droplet.main DROPLET_ID
```

### Taint Resources

Force recreation of a resource:

```bash
# Taint droplet (will be destroyed and recreated)
make iac production taint digitalocean_droplet.main

# Apply to recreate
make iac production apply
```

### Targeted Apply

Apply changes to specific resources only:

```bash
# Update only DNS records
make iac production apply -target=module.dns

# Update only droplet
make iac production apply -target=module.server
```

### Terraform Console

Test Terraform expressions interactively:

```bash
make iac production console

# Try:
> var.project_name
> module.server.server_ip
```

## Next Steps

Once infrastructure is deployed:

1. **Verify SSH Access**: `bin/ssh production`
2. **Check Docker**: `ssh root@SERVER_IP docker --version`
3. **Wait for DNS**: DNS records should resolve in ~5 minutes
4. **Deploy Applications**: See [Kamal Deployment Guide](../deployment/KAMAL.md)

All deployment commands will automatically load server IPs and SSH keys from Terraform outputs.
