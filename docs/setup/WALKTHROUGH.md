# Complete Setup Walkthrough

This guide walks you through the complete setup process for deploying the generic template from scratch.

## Overview

The generic template is an **extensible Docker-based deployment framework** for different types of applications. It provides:

- **Multiple application stacks** - TypeScript (Vite + Express) and Python (FastAPI)
- **Container-first deployment** - Portable, reproducible builds with Docker
- **Infrastructure as Code** - Terraform for server provisioning
- **Automated secrets management** - 1Password integration
- **Zero-downtime deployments** - Kamal orchestration

This walkthrough will guide you through:
1. Prerequisites and account setup
2. 1Password vault configuration
3. Terraform Cloud setup
4. Infrastructure deployment
5. Application deployment

**Time estimate**: 1-2 hours for first-time setup

## Prerequisites

### Required Accounts

1. **1Password account** with CLI installed (`op`)
   - Individual or Teams account
   - CLI tool: https://1password.com/downloads/command-line/

2. **Terraform Cloud account** (free tier)
   - Sign up at: https://app.terraform.io/

3. **Digital Ocean account** with API token
   - Sign up at: https://www.digitalocean.com/
   - Create API token in Settings → API

4. **Cloudflare account** managing your DNS zone
   - Sign up at: https://www.cloudflare.com/
   - Add your domain to Cloudflare

5. **Docker Hub account** (or GitHub Container Registry)
   - Sign up at: https://hub.docker.com/
   - Create access token in Settings → Security

### Required Tools

Install these tools on your development machine:

```bash
# macOS
brew install --cask 1password-cli
brew install terraform
gem install kamal

# Verify installations
op --version
terraform --version
kamal version
```

### Domain Setup

You need a domain name managed by Cloudflare:

1. Register a domain (NameCheap, Google Domains, etc.)
2. Point nameservers to Cloudflare
3. Verify domain is active in Cloudflare dashboard

## Step 1: Configure Project Settings

### 1.1 Edit `.env.project`

This is the single source of truth for your project configuration:

```bash
# Edit the file
vim .env.project
```

Set these values:

```bash
# Must be globally unique (becomes your TFC org name)
PROJECT_NAME=yourname-generic

# Your Cloudflare domain
DNS_ROOT_ZONE=yourdomain.com

# Services and subdomains (format: service:subdomain)
# Empty subdomain means root domain
SERVICES="py:app,ts-web:"

# 1Password vault for cloud credentials
CLOUD_VAULT=cloud-providers
```

**Important**:
- `PROJECT_NAME` must be globally unique (TFC org name = `${PROJECT_NAME}-org`)
- For `SERVICES`, format is `service:subdomain`
  - `py:app` → deploys Python API to `app.yourdomain.com`
  - `ts-web:` → deploys web app to `yourdomain.com` (root)

### 1.2 Verify Configuration

```bash
# Source the config
source .env.project

# Verify variables are set
echo $PROJECT_NAME
echo $DNS_ROOT_ZONE
echo $SERVICES
```

## Step 2: 1Password Setup

### 2.1 Create Cloud Providers Vault

Create a vault for cloud provider credentials:

```bash
# Create vault
op vault create "cloud-providers"

# Or use existing vault and update .env.project
```

### 2.2 Add Cloud Provider Credentials

Add credentials to the cloud-providers vault:

**Terraform Cloud API Token:**
```bash
op item create \
  --category=login \
  --title=TERRAFORM_CLOUD_API_TOKEN \
  --vault=cloud-providers \
  credential=<your-terraform-cloud-token>
```

Get token from: https://app.terraform.io/app/settings/tokens

**Docker Hub:**
```bash
op item create \
  --category=login \
  --title=DOCKER_HUB_LOGIN \
  --vault=cloud-providers \
  username=<your-docker-username> \
  credential=<your-docker-token>
```

**Digital Ocean:**
```bash
op item create \
  --category=login \
  --title=DO_API_TOKEN \
  --vault=cloud-providers \
  credential=<your-do-token>
```

**Cloudflare:**
```bash
op item create \
  --category=login \
  --title=CLOUDFLARE_DNS_API_TOKEN \
  --vault=cloud-providers \
  credential=<your-cloudflare-token>
```

### 2.3 Create Stage-Specific Vaults

Create vaults for each deployment stage:

```bash
# Production vault
op vault create "<project-name>-production"

# Staging vault (optional)
op vault create "<project-name>-staging"

# Development vault (for local dev)
op vault create "<project-name>-development"
```

### 2.4 Add Application Secrets

Add application-specific secrets to stage vaults:

**Google OAuth (for Python app):**
```bash
op item create \
  --category=login \
  --title=GOOGLE_O_AUTH_CLIENT \
  --vault=<project>-production \
  username=<your-google-client-id> \
  credential=<your-google-client-secret>
```

Get credentials from: https://console.cloud.google.com/apis/credentials

**Other secrets as needed:**
- API keys
- Third-party service tokens
- Application-specific config

### 2.5 Verify 1Password Setup

```bash
# Test reading credentials
bin/vault read DOCKER_HUB_USERNAME
bin/vault read DO_API_TOKEN

# Should print values without errors
```

See [ONE_PASSWORD.md](./ONE_PASSWORD.md) for detailed vault structure.

## Step 3: Terraform Cloud Setup

### 3.1 Create Organization and Workspaces

```bash
# Create TFC org and workspaces
make tfc up
```

This creates:
- TFC organization: `<project-name>-org`
- Workspaces:
  - `container-registry` - Docker Hub repos
  - `production` - Production infrastructure
  - `staging` - Staging infrastructure (optional)

### 3.2 Verify TFC Setup

```bash
# Check status
make tfc status

# Should show:
# ✓ Organization exists
# ✓ Workspaces created
```

See [TERRAFORM_CLOUD.md](./TERRAFORM_CLOUD.md) for details.

## Step 4: Infrastructure Deployment

### 4.1 Deploy Container Registry

First, create Docker Hub repositories:

```bash
# Initialize Terraform
make iac container-registry init

# Review plan
make iac container-registry plan

# Deploy
make iac container-registry apply
```

This creates Docker Hub repos for each service.

### 4.2 Deploy Production Infrastructure

```bash
# Initialize Terraform
make iac production init

# Review plan
make iac production plan

# Deploy infrastructure
make iac production apply
```

This creates:
- Digital Ocean droplet (server)
- SSH keys for access
- Cloudflare DNS records
- Firewall rules

**Note**: First apply may take 5-10 minutes.

### 4.3 Verify Infrastructure

```bash
# Get infrastructure outputs
make iac production output

# Should show:
# server_ip = "xxx.xxx.xxx.xxx"
# ssh_connect_command = "ssh ..."
# dns_records = { ... }

# Test SSH access
bin/ssh production
# Should connect to server
```

See [INFRASTRUCTURE.md](./INFRASTRUCTURE.md) for details.

## Step 5: Application Deployment

### 5.1 Bootstrap Server

**First time only** - setup Kamal infrastructure on server:

```bash
# Bootstrap server (installs Traefik, Docker networks, etc.)
make kamal ARGS="py production setup"
```

### 5.2 Deploy Python API

If using the Python stack:

```bash
# Boot PostgreSQL database
make kamal ARGS="py production accessory boot postgres"

# Deploy Python app
make kamal ARGS="py production deploy"

# Verify
curl https://app.yourdomain.com/health
# Should return: {"status": "ok"}
```

### 5.3 Deploy TypeScript Web App

If using the TypeScript stack:

```bash
# Deploy web app
make kamal ARGS="ts-web production deploy"

# Verify
curl https://yourdomain.com
# Should return HTML
```

### 5.4 Verify Deployments

```bash
# Check running containers
make kamal ARGS="py production ps"

# View logs
make kamal ARGS="py production logs"
make kamal ARGS="ts-web production logs"

# Check SSL certificates
curl -I https://yourdomain.com
# Should show: HTTP/2 200
```

See [KAMAL.md](../deployment/KAMAL.md) for deployment details.

## Step 6: Verification and Testing

### 6.1 Test Services

Visit your deployed services:

- **Web app**: https://yourdomain.com
- **Python API**: https://app.yourdomain.com
- **API health**: https://app.yourdomain.com/health

### 6.2 Monitor Resources

```bash
# SSH to server
bin/ssh production

# Check resource usage
docker stats

# Should show all containers running with reasonable CPU/RAM
```

### 6.3 Test OAuth (if enabled)

For Python app with Google OAuth:

1. Visit: https://app.yourdomain.com/auth/google
2. Should redirect to Google login
3. After auth, redirects back to app

## Common Issues

### "TFC organization already exists"

Someone else is using that project name. Change `PROJECT_NAME` in `.env.project`.

### "DNS records not propagating"

Wait 5-10 minutes for Cloudflare DNS propagation. Check with:
```bash
dig yourdomain.com
```

### "Cannot connect to server via SSH"

Check firewall allows your IP:
```bash
# Get your IP
curl ifconfig.me

# Add to firewall in Digital Ocean dashboard
```

### "Container won't start"

Check logs:
```bash
make kamal ARGS="py production logs"
```

Common issues:
- Missing environment variables in 1Password
- Database not booted (for Python)
- Health check endpoint not responding

### "SSL certificate not issued"

Ensure:
- DNS points to server (check with `dig`)
- Port 80/443 open in firewall
- Valid email in Kamal config

## Next Steps

After successful deployment:

1. **Set up monitoring**
   - Uptime Robot for health checks
   - Sentry for error tracking
   - Log aggregation (if needed)

2. **Configure backups**
   - Database backups (for Python stack)
   - Config backups (1Password handles this)

3. **Set up CI/CD** (optional)
   - GitHub Actions for automated deploys
   - Run tests before deployment

4. **Scale as needed**
   - Upgrade droplet size in Terraform
   - Add more servers for load balancing

5. **Customize your application**
   - Modify Python/TypeScript code
   - Add new features
   - Deploy updates with `make kamal ARGS="<service> production deploy"`

## Development Workflow

For local development:

```bash
# Install dependencies
make install

# Build styles
make styles

# Run all dev servers
make dev
```

See [LOCAL.md](../development/LOCAL.md) for development guide.

## Resources

- [1Password Setup](./ONE_PASSWORD.md)
- [Terraform Cloud Setup](./TERRAFORM_CLOUD.md)
- [Infrastructure Guide](./INFRASTRUCTURE.md)
- [Deployment Guide](../deployment/KAMAL.md)
- [Development Guide](../development/LOCAL.md)
- [DevOps Philosophy](../dev-ops/index.md)

## Support

For issues:
- Check troubleshooting sections in each guide
- Review Kamal logs: `make kamal ARGS="<service> production logs"`
- Check infrastructure: `make iac production output`
- Verify 1Password: `bin/vault read <KEY>`

## Cost Estimate

Running this stack:
- **Digital Ocean Droplet** (s-1vcpu-1gb): $6/month
- **Cloudflare DNS**: Free
- **Terraform Cloud**: Free (up to 500 resources)
- **1Password**: Varies by plan

**Total minimum**: ~$6-15/month
