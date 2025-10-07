# Provider configuration for production environment
terraform {
  required_version = ">= 1.0"

  required_providers {
    dockerhub = {
      source  = "artificialinc/dockerhub"
      version = "~> 0.0.15"
    }
  }
}
