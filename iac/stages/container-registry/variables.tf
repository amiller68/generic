variable "docker_hub_username" {
  description = "Docker Hub username or organization name"
  type        = string
  sensitive   = false
}

variable "docker_hub_password" {
  description = "Docker Hub personal access token"
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "Project name for repository naming"
  type        = string
}

variable "services" {
  description = "Services configuration from .env.project (format: service:subdomain,service:subdomain)"
  type        = string
}

variable "use_private_repos" {
  description = "Whether to create private repositories"
  type        = bool
  default     = false
}
