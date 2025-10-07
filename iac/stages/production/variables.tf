# Production environment variables
variable "project_name" {
  description = "The name of the project"
  type        = string
}

variable "services" {
  description = "Services configuration from .env.project (format: service:subdomain,service:subdomain)"
  type        = string
}

variable "dns_root_zone" {
  description = "Root DNS zone for the project"
  type        = string
}

variable "subdomains" {
  description = "Comma-separated list of subdomains to create DNS records for (@ for root)"
  type        = string
}
