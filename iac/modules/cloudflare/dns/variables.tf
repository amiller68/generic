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

variable "dns_root_zone" {
  description = "Root DNS zone for the project"
  type        = string
}

variable "droplet_ip" {
  description = "The IPv4 address of the droplet"
  type        = string
}

variable "domain_slugs" {
  description = "List of domain slugs to create as subdomains"
  type        = list(string)
  default     = []
  
  # check that no domain slugs conflict with our environment names
  validation {
    condition     = alltrue([
      for slug in var.domain_slugs :
      slug != var.environment
    ])
    error_message = "Domain slugs must not conflict with environment names"
  }
}

variable "ttl" {
  description = "TTL for DNS records"
  type        = number
  default     = 300
}

variable "proxied" {
  description = "Whether the records should be proxied through Cloudflare"
  type        = bool
  default     = false
}

variable "create_root_record" {
  description = "Whether to create a DNS record for the root domain"
  type        = bool
  default     = false
}