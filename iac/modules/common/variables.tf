locals {
  # Common tags for all resources
  common_tags = [
    "project:${var.project_name}",
    "env:${var.environment}",
    "managed-by:terraform"
  ]
}

variable "project_name" {
  description = "The name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (staging, production, etc.)"
  type        = string
  validation {
    # supported environments
    # TODO: support more environments
    condition     = contains(["production"], var.environment)
    error_message = "Environment must be one of: production"
  }
}

# DigitalOcean configuration
variable "digitalocean" {
  description = "Configuration for DigitalOcean infrastructure"
  type = object({
    droplet = object({
      region = string
      size   = optional(string, "s-1vcpu-1gb")
    })
  })
}

# Cloudflare configuration
variable "cloudflare" {
  description = "Configuration for Cloudflare DNS"
  type = object({
    ttl          = optional(number, 300)
    proxied      = optional(bool, false)
    dns_root_zone = string
  })
}

variable "subdomains" {
  description = "Comma-separated list of subdomains to create DNS records for (@ for root)"
  type        = string
}