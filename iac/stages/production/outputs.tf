output "ssh_private_key" {
  description = "Private SSH key for accessing the droplet"
  value       = module.common.digitalocean_ssh_private_key
  sensitive   = true
}

output "server_ip" {
  description = "The IP address of the droplet"
  value       = module.common.digitalocean_droplet_ip
}

