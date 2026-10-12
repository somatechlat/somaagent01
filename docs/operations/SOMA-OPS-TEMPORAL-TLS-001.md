# SOMA-OPS-TEMPORAL-TLS-001 — Temporal client TLS / API key (production)

| Field | Value |
|---|---|
| Standard | SOMA-OPS-TEMPORAL-TLS-001 |
| Status | ACTIVE |
| Scope | `somaAgent01` Temporal worker + any `temporalio.client.Client.connect` |

## Rule

In production, every `Client.connect` to Temporal MUST use **TLS and an API key
(or mTLS)**. Plaintext is a development-only posture.

The one worker construction site is:

- `services/conversation_worker/temporal_worker.py` — `Client.connect(temporal_host)`
  (the `main()` entrypoint). `services/delegation_gateway/temporal_worker.py` is a
  thin re-export and does **not** construct a Worker (WAVE 5 single-worker fold).

## Required connect shape (prod)

```python
# Target: operator-supplied SA01_TEMPORAL_HOST (namespace.tmprl:7233 or in-cluster).
# API key / client cert: Vault secret, never os.environ at the call site.
client = await Client.connect(
    temporal_host,
    tls=True,                       # or tls=TLSConfig(client_cert=..., client_private_key=...)
    api_key=vault_secret,           # Temporal Cloud API key OR mTLS identity
)
```

## Why

Workflow payloads carry memory text, tenant ids, and tool events. An
unauthenticated or plaintext cluster is an open read/write channel on the
memory and delegation plane (T-6 zero-loss depends on the workflow history
being trustworthy).

## Checklist

- [ ] `SA01_TEMPORAL_HOST` is the operator deployment parameter (no default scheduler).
- [ ] TLS enabled on the Temporal frontend in every non-loopback deployment.
- [ ] API key or client certificate comes from Vault (`secret/agent/credentials/...`).
- [ ] Local loopback plaintext is allowed only when the operator configured that host.
