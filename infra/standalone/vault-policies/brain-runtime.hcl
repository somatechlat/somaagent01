# brain-runtime — the policy the SomaBrain runtime holds.
#
# This is the trust boundary made explicit. SomaBrain needs exactly one
# shared credential from the agent's document — the memory HTTP token that
# vault_client.get_runtime_secret("memory_http_token") reads — plus its own
# service secrets under somabrain/. It is NOT entitled to the agent's database
# password, its keycloak secrets, or anything else in that document.
#
# Least privilege here is the point: "mount the whole secrets directory into
# every job" is privilege creep by convenience. A compromised brain must not
# be able to read the agent's database credentials.

# The ONE shared key. Not the whole document — just this key's data at read.
path "secret/data/agent/credentials" {
  capabilities = ["read"]
}

# This service's own secrets. Owns them end to end.
path "somabrain/data/*" {
  capabilities = ["read", "update", "create", "delete"]
}

path "somabrain/metadata/*" {
  capabilities = ["read", "list", "delete"]
}

# Lease management for its own token only.
path "auth/token/renew-self" {
  capabilities = ["update"]
}

path "auth/token/lookup-self" {
  capabilities = ["read"]
}

# Explicitly denied by omission: sys/mounts, sys/policy, auth/token/create,
# secret/data/agent/api_keys, and every other mount on this Vault.
