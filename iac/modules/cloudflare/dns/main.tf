# Data source to look up the zone ID from the domain name
data "cloudflare_zone" "main" {
  name = var.dns_root_zone
}

# A record for root domain
resource "cloudflare_record" "root" {
  count = var.create_root_record ? 1 : 0

  zone_id = data.cloudflare_zone.main.id
  name    = "@"
  content = var.droplet_ip
  type    = "A"
  ttl     = var.ttl
  proxied = var.proxied
}

# A records for each domain slug
resource "cloudflare_record" "subdomains" {
  for_each = toset(var.domain_slugs)

  zone_id = data.cloudflare_zone.main.id
  # if our env is production, we won't prepend the env to the domain slug
  #  This is to avoid having to create a new DNS record for each environment
  name = var.environment == "production" ? each.value : "${var.environment}.${each.value}"
  content = var.droplet_ip
  type    = "A"
  ttl     = var.ttl
  proxied = var.proxied
}