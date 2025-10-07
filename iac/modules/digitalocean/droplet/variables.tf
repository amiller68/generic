variable "name" {
  description = "The name of the droplet"
  type        = string
}

variable "region" {
  description = "The region where the droplet will be created"
  type        = string
  default     = "nyc3"
}

variable "size" {
  description = "The size of the droplet"
  type        = string
  default     = "s-1vcpu-1gb"
}

variable "image" {
  description = "The droplet image ID or slug"
  type        = string
  default     = "ubuntu-24-04-x64"
}

variable "ssh_keys" {
  description = "A list of SSH key IDs or fingerprints to enable"
  type        = list(string)
  default     = []
}

variable "vpc_uuid" {
  description = "The ID of the VPC where the droplet will be located"
  type        = string
  default     = null
}

variable "tags" {
  description = "A list of tags to apply to the droplet"
  type        = list(string)
  default     = []
}

variable "monitoring" {
  description = "Whether to enable monitoring for the droplet"
  type        = bool
  default     = true
}

variable "backups" {
  description = "Whether to enable backups for the droplet"
  type        = bool
  default     = false
}

variable "ipv6" {
  description = "Whether to enable IPv6 for the droplet"
  type        = bool
  default     = false
}

variable "resize_disk" {
  description = "Whether to enable resize disk for the droplet"
  type        = bool
  default     = true
}

variable "droplet_agent" {
  description = "Whether to enable the DigitalOcean agent for monitoring"
  type        = bool
  default     = true
}

variable "graceful_shutdown" {
  description = "Whether to enable graceful shutdown for the droplet"
  type        = bool
  default     = false
}

variable "ssh_allowed_ips" {
  description = "List of allowed IP addresses for SSH access"
  type        = list(string)
  default     = ["0.0.0.0/0", "::/0"]
}

variable "additional_ports" {
  description = "Additional ports to open in the firewall"
  type        = list(string)
  default     = []
}

