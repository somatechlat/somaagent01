storage "file" {
  path = "/vault/file"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1
}

cluster_addr = "http://vault:8201"
api_addr     = "http://vault:8200"

disable_mlock = false

default_lease_ttl = "168h"
max_lease_ttl     = "720h"
ui                = true
