# Vault server configuration — AAAS test stack.
#
# Same production shape as infra/standalone/vault.hcl:
#   * `file` storage on a named volume, so secrets SURVIVE a container restart.
#     Dev mode keeps them in memory and loses every credential on restart.
#     This stack used to run dev mode with VAULT_DEV_ROOT_TOKEN_ID from the
#     environment — a root token in an env var, readable from `ps`,
#     /proc/*/environ and every core dump. That is gone.
#   * Real seal. Starts sealed, unsealed by vault_unseal.py with a key the
#     deployer holds in ../standalone/secrets/.
#
# TLS is disabled: the listener is container-internal on a compose network.
# Production terminates TLS at the listener.

storage "file" {
  path = "/vault/data"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1
}

# No api_addr / cluster_addr — Vault derives both from the request and the
# listener, and pinning them invites a second bind. See the `entrypoint` note.
disable_mlock = true

ui = true
