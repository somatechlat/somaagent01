# Security Posture Review (Draft)

## Identity & Auth
- JWT cookie parsing with algorithm enforcement; PyJWT required.
- API keys via Redis-backed store; prefixes and revocation supported.
- Policy middleware (OPA) applied globally in gateway; fail-closed configurable.

## Secrets
- No secrets logged: add redaction filter (TODO) for common keys and bearer patterns.
- Secret resolution via `vault_secrets` helper; plan to add reference-by-key in config registry.

## Data Handling
- Uploads guarded by allowed/denied mime lists; antivirus optional with strict mode.
- Sensitive payload scrubbing for audit/details (present in gateway).

## Transport & TLS
- Recommend mTLS at edge (Envoy/Kong); ensure `X-Forwarded-Proto` honored for WS URL building.

## Authorization
- Metrics for policy decisions; add latency histogram to observe OPA/sidecar performance.

## Multi-tenancy
- Tenant extracted from auth metadata; topic headers support `tenant` (future).

## Supply Chain
- Pin critical packages in `pyproject.toml`; run `pip-audit` in CI (TODO).

## Next Steps
1. Implement log redaction filter and unit tests.
2. Add `policy_decision_latency_seconds` histogram and sampling.
3. Add OpenFGA optional enforcement points (documented toggles).
4. Secrets-by-reference support in config registry and integrity checks.
5. CI: add SAST/dep scan + secret scanning on commits.
