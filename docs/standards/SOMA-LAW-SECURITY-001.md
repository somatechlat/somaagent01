# SOMA-LAW-SECURITY-001 — Security & Vault reality (CODE = TRUTH)

## Document Control

| Field | Value |
|---|---|
| Document Title | Security & Vault operating law (matches live code) |
| Document Identifier | SOMA-LAW-SECURITY-001 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 · ISO 27001 controls (A.5–A.8) |
| Next Review | 2027-01-13 |
| Source of truth | `infra/standalone/vault_scoped_tokens.py` · `vault-policies/*.hcl` · `vault_unseal.py` · `services/common/vault_secrets.py` · `docker-compose.yml` |
| Related | `SOMA-STD-BOOTSTRAP-001` · `SOMA-STD-SECURITY-001` · `SOMA-RPT-SEC-VAULT-001` · `CLAUDE.md` |
| Audience | **Every Soma agent** — spawn with this law |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | SomaTech Engineering | After 2026-10-13 outage: orphan tokens, 720h lease, no root on disk. Code is truth. |

---

## 1. Absolute rules (agents MUST follow)

| ID | Rule |
|---|---|
| SEC-LAW-01 | **Never write Vault root to disk** (any filesystem). One-shot process memory only. |
| SEC-LAW-02 | **Never print secrets** (tokens, keys, passwords) in logs, docs, chat, commits. |
| SEC-LAW-03 | **Never put secrets in env files or git.** `.env` = non-secret topology only. |
| SEC-LAW-04 | **Service tokens MUST be orphans** (`no_parent: true`) so root `revoke-self` does not revoke them. |
| SEC-LAW-05 | **Mint then revoke root immediately.** Ceremony: generate-root → install policy → issue orphans → revoke-self. |
| SEC-LAW-06 | **Fail closed.** Missing token/secret → stop with named error (F-10/F-11). No backup file, no widen policy, no `omit the secret and start`. |
| SEC-LAW-07 | **Least privilege policies only.** agent-runtime: `read` on `secret/data/agent/credentials` + `api_keys` (+ metadata). No write. No `sys/`. |
| SEC-LAW-08 | **Code is the only source of truth.** If docs disagree with `vault_*.py` / compose / policies — fix docs to match code. |
| SEC-LAW-09 | Soma law: NO SHIMS/FAKES/MOCKS/STUBS. T-1 MemoryGateway only. |
| SEC-LAW-10 | UI law: `SOMA-STD-UIUX-001` · skins · I18N · GATED honesty · no emojis. |

## 2. Live Vault facts (verified 2026-10-13)

| Fact | Value |
|---|---|
| Service token type | `hvs.*` lease **720h (30d)** · orphan (`no_parent`) |
| Paths | `VAULT_TOKEN_FILE=/run/t0/agent_runtime_token` · brain: `brain_runtime_token` |
| Custodian (this deploy) | Docker volume `standalone_t0_agent` → `/run/t0` (**ext4**, not tmpfs) |
| File mode | `0600` `appuser:appuser` (docker cp as root then `chown`) |
| Root | **Never** in `/run/t0`. generate-root + `auth/token/revoke-self` after mint. |
| Policies | `agent-runtime.hcl` · `brain-runtime.hcl` (read-only KV v2) |
| TTL config | `VAULT_TOKEN_TTL_HOURS=720` in `infra/standalone/.env` |

### 2.1 T0 tmpfs vs volume (doc correction)

| Source | Claim |
|---|---|
| older `SOMA-STD-BOOTSTRAP-001` prose | T0 = RAM tmpfs only |
| live `vault_scoped_tokens.py` / `vault_unseal.py` | Allow **tmpfs OR dedicated named-volume mount** (BOOTSTRAP-001 **§2.1a**). Refuse root writes. Refuse overlay/root-fs. |
| `docker-compose.yml` | `t0_agent:/run/t0` **named volume** so unseal key survives recreate |

**Truth for this deploy:** Docker volume **`standalone_t0_agent` (ext4)** at `/run/t0` is intentional for unseal continuity (§2.1a). Mint writes **scoped** tokens directly into that custodian (`_t0_custodian_allows`). Never root. Never chmod 0777. Do not weaken policy. Full narrative: `docs/reports/SOMA-RPT-SEC-VAULT-001.md`.

## 3. Correct ceremony (operators / bots)

```
MINT PATH OF RECORD: infra/standalone/vault_scoped_tokens.py (orphan + revoke-self).
Do NOT pair bootstrap_exec.py mint_scoped with root revoke until it sets no_parent.

1. vault operator generate-root -generate-otp
2. generate-root -init -otp=…  → nonce
3. unseal key from T0 (custodian) | generate-root -nonce=…
4. generate-root -decode -otp=… → root (memory only)
5. export VAULT_TOKEN=<root>   # THIS one-shot process env only
6. T0_DIR=/run/t0 VAULT_ADDR=… VAULT_TOKEN_TTL_HOURS=720 \
     python3 vault_scoped_tokens.py
   # installs policies
   # auth/token/create {policies:[…], ttl:720h, no_parent:true, no_default_policy:true}
   # writes agent_runtime_token + brain_runtime_token to T0 (0600, consumer UID)
   # refuses vault_root_token (R-SEC-01)
   # auth/token/revoke-self on root  (orphans survive)
7. verify: test ! -f /run/t0/vault_root_token
8. restart somaagent_standalone; POST /api/v2/auth/login must be 200
```

## 4. Incident that defined this (2026-10-13)

| Step | What happened |
|---|---|
| Cause | 24h service lease expired → F-11 pepper/key unreadable → login 503 |
| Error | Root written to `/run/t0` (R-SEC-01) — **removed** |
| Error | `revoke-self` without `no_parent` killed service tokens |
| Fix | Orphan tokens + 720h + chown 0600 + document code=truth |

## 5. Agent checklist (every PR)

- [ ] No secret in git / logs / docs  
- [ ] No root token material on disk  
- [ ] Fail-closed errors named  
- [ ] Docs match code  
- [ ] Soma law + UI law held  

**End of SOMA-LAW-SECURITY-001.**
