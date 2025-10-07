output "digitalocean_ssh_private_key" {
  description = "The generated private SSH key (sensitive)"
  value       = module.digitalocean_ssh_key.private_key_openssh
  sensitive   = true
}

output "digitalocean_ssh_public_key" {
  description = "The public SSH key"
  value       = module.digitalocean_ssh_key.public_key_openssh
}

output "digitalocean_droplet_ip" {
  description = "The IP address of the droplet"
  value       = module.digitalocean_droplet.ipv4_address
}