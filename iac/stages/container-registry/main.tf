# Docker Hub provider configuration
# Credentials come from environment variables
provider "dockerhub" {
  username = var.docker_hub_username
  password = var.docker_hub_password
}

# Define repositories to create based on services from environment
locals {
  # Parse services from environment variable
  # Format: "service1:subdomain1,service2:subdomain2"
  services = toset([
    for s in split(",", var.services) :
    split(":", s)[0]
  ])

  project_name = var.project_name
}

# Create repositories based on services
resource "dockerhub_repository" "repos" {
  for_each = local.services

  name        = "${local.project_name}-${each.value}"
  namespace   = var.docker_hub_username
  description = "${var.project_name} ${each.value} service"
  private     = var.use_private_repos
}

# Output repository URLs
output "repositories" {
  value = {
    for key, repo in dockerhub_repository.repos :
    key => "${var.docker_hub_username}/${repo.name}"
  }
  description = "Docker Hub repository URLs"
}

output "registry_url" {
  value       = "docker.io"
  description = "Docker Hub registry URL"
}
