terraform {
  cloud {
    organization = "krondor-generic-org"

    workspaces {
      name = "krondor-generic-container-registry"
    }
  }
}
