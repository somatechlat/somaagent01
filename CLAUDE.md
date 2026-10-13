# somaAgent01 — agent entry rules

| Field | Value |
|---|---|
| Primary standard | `docs/standards/SOMA-STD-TRIAD-001.md` (shared with somabrain + somafractalmemory) |
| Coding law | `docs/standards/SOMA-STD-CODING-001.md` (VIBE) |
| UI/UX law | `docs/standards/SOMA-STD-UIUX-001.md` (webui: skins · I18N · GATED honesty · A0 · acceptance) |
| **Security / Vault law** | `docs/standards/SOMA-LAW-SECURITY-001.md` (no root on disk · orphan tokens 720h · code=truth) |
| Rapid plan | `docs/standards/SOMA-RAPID-DEVELOPMENT-001.md` |
| Status report | `docs/reports/SOMA-RPT-STATUS-001.md` |
| A2A | `docs/plans/a2a/` — claim before large edits; log commits |

## ABSOLUTE LAW — REAL CODE ONLY (operator, 2026-10-09)

**NO SHIMS. NO FAKES. NO MOCKS. NO STUBS. NO PLACEHOLDERS. NO TODO PASSES.**

A shim is a bypass. A mock is a lie. A fake is a defect.
Acceptance = live real services (T-8/VIBE). If a dependency is missing, integrate the **real** library/API or do not ship the feature.

**Code is the ONLY source of truth.** Docs yield to live code. Never print secrets. Never write root to disk. Fail-closed.

## SECURITY / VAULT LAW (operator, 2026-10-13 — after token outage)

1. **NEVER root on disk.** No `vault_root_token` in T0, `/tmp`, repo, compose env, or any file. Root = one-shot process RAM → `auth/token/revoke-self` immediately after mint.
2. **Orphan service tokens only.** Every runtime `auth/token/create` uses `no_parent: True`. Root revoke without orphan kills all children (outage root cause).
3. **No secrets in ENV steady-state.** `VAULT_TOKEN` / `VAULT_UNSEAL_KEY` are one-shot only, stripped before exec. Services read `VAULT_TOKEN_FILE` from their private T0.
4. **T0 custodian:** tmpfs preferred; this deploy uses named volume `standalone_t0_agent` (**ext4**, not tmpfs — documented §2.1a exception). Scoped tokens + unseal key only. Never root. 0700/0600.
5. **TTL is operator config** (`VAULT_TOKEN_TTL_HOURS`; this deploy **720h**). No coded default (Rule 91). Expired token = fail-closed, never widen policy.
6. **Policies least privilege.** `agent-runtime`: read `secret/data/agent/credentials` + `api_keys` only. No write. No `sys/`. Mint path of record: `infra/standalone/vault_scoped_tokens.py`.

Truth document: `docs/reports/SOMA-RPT-SEC-VAULT-001.md`. Law: `SOMA-LAW-SECURITY-001` · `SOMA-STD-BOOTSTRAP-001` §2.1a/§3.4 · `SOMA-STD-SECURITY-001`.

**Always feed these rules to every agent you spawn.**

## SECURITY / VAULT LAW (code = truth · 2026-10-13)

Full text: `docs/standards/SOMA-LAW-SECURITY-001.md`. Minimum every agent knows:

1. **Never write Vault root to disk.** One-shot memory only; `revoke-self` after mint.  
2. **Never print secrets** (logs, docs, chat, commits).  
3. **No secrets in env/git.** `.env` = topology only.  
4. **Service tokens = orphans** (`no_parent`) + TTL **720h** (30d) — so root revoke does not kill them.  
5. **Fail closed** (F-10/F-11) — no backup file, no policy widening.  
6. **Docs must match code** (`vault_scoped_tokens.py`, `vault-policies/*.hcl`, compose).  
7. T0 in this deploy is Docker volume `standalone_t0_agent` (ext4) — service tokens `appuser:appuser` 0600; **never root**.

## Stack lock

Django Ninja · Django ORM · Lit 3.x · Milvus (via SomaBrain) · Temporal for async · Vault secrets · **no React/Alpine/FastAPI/SQLAlchemy/Qdrant**.

## Memory

T-1: only `MemoryGateway` → `SomaBrainAdapter`. Never an SFM client.

## Local project agents (`.mimocode/agent/`)

| Agent | Use for |
|---|---|
| `soma-wiring-engineer` | Memory seam, adapter, Temporal workers, phantom routes, CLEF brain-write lane |
| `soma-ui-engineer` | webui Lit UI, A0 chrome, honest states, CLEF decision UI |
| `soma-cognitive-engineer` | Cognitive API wiring, OPA confidence/CLEF contract |
| `soma-temporal-ops` | Temporal 100% + env contract + CLEF async (Seam D) |
| `soma-adversarial-skeptic` | Every wave critic (parallel with builder) |
| `soma-clef-engineer` | Clef integration: decisions client, real Clef dependency, mod_clef, guardrail choke |
| `triad-iso-docs` | ISO document control |
| `soma-deadcode-remover` | Python/Django dead code, duplicates, shims, compat-facade deletion (grep-proven zero callers) |
| `soma-dedup-engineer` | T-2 one coord authority, name-fork collapse, settings-chain unification, twin-pipeline collapse |
| `soma-e2e-prover` | Live behavioral proof only — codeword round-trip, kill-brain drill, Playwright on real services |
| `soma-vault-authority` | Single credential trust, merge-safe KV v2, read-back assert, `*_FILE` only |
| `soma-infra-health` | Kafka/Temporal/Milvus/OPA/Redis proven Running (not just compose-present) |
| `soma-prod-hardening` | Django security block, pooling, DEBUG decouple, rate limits, bounded schemas, SSRF |

## How to invoke

Say in chat: use `soma-ui-engineer` for X · use `soma-adversarial-skeptic` on this diff · or spawn via the actor/subagent mechanism with that name.

## Done =

Human Playwright session green on real services — not skip-gated, not mocked.
