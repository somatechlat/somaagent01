# agent-runtime — the policy the somaAgent01 runtime holds.
#
# Least privilege: it may READ the credentials it actually consumes and
# nothing else. It cannot write, cannot list other mounts, and cannot reach
# the root-only sys/ endpoints. A compromised agent process can therefore
# read its own configuration but cannot rewrite the trust boundary.
#
# Issued as a TTL-bound token by vault_scoped_tokens.py. The root token is
# never held by a running service — see vault_unsecl.py for why a root token
# in an environment variable is readable from ps, /proc/*/environ and every
# core dump.

# Credentials this service resolves through UnifiedSecretManager.get_credential.
path "secret/data/agent/credentials" {
  capabilities = ["read"]
}

# Provider API keys (Vault secret/agent/api_keys/{provider}_api_key).
path "secret/data/agent/api_keys" {
  capabilities = ["read"]
}

path "secret/data/agent/api_keys/*" {
  capabilities = ["read"]
}

# Metadata lookups only. No list of other mounts, no delete, no write.
path "secret/metadata/agent/credentials" {
  capabilities = ["read"]
}

path "secret/metadata/agent/api_keys/*" {
  capabilities = ["read"]
}

# Token self-management: renew its own lease, never mint others.
path "auth/token/renew-self" {
  capabilities = ["update"]
}

path "auth/token/lookup-self" {
  capabilities = ["read"]
}

# Explicitly nothing else. No sys/, no other mounts, no write anywhere.
