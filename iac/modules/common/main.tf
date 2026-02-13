# DigitalOcean Infrastructure Module

# random prefix for the project
resource "random_string" "project_prefix" {
  length  = 4
  special = false
}

# Project
module "digitalocean_project" {
  source = "../digitalocean/project"

  name = "${var.project_name}-${var.environment}-${random_string.project_prefix.result}-project"
  description = "Project for ${var.project_name} ${var.environment}"
  environment = var.environment
  resources = [module.digitalocean_droplet.urn]
}


# SSH key which will get access to the droplet
module "digitalocean_ssh_key" {
  source = "../digitalocean/ssh_key"

  name = "${var.project_name}-${var.environment}-${random_string.project_prefix.result}-ssh-key"
}

# Droplet
module "digitalocean_droplet" {
  source = "../digitalocean/droplet"

  name = "${var.project_name}-${var.environment}-${random_string.project_prefix.result}-droplet"

  region = var.digitalocean.droplet.region
  size   = var.digitalocean.droplet.size
  tags   = ["${var.project_name}-${var.environment}"]

  # SSH configuration
  ssh_keys        = [module.digitalocean_ssh_key.id]
}

# Cloudflare DNS
module "cloudflare_dns" {
  source = "../cloudflare/dns"

  environment    = var.environment
  dns_root_zone  = var.cloudflare.dns_root_zone
  droplet_ip     = module.digitalocean_droplet.ipv4_address
  domain_slugs   = split(",", var.subdomains)
  ttl            = var.cloudflare.ttl
  proxied        = var.cloudflare.proxied
}