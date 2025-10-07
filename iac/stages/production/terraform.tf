terraform {
  cloud {
    organization = "krondor-generic-org"

    workspaces {
      name = "krondor-generic-production"
    }
  }
}
