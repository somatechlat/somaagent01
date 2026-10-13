# somaAgent01 — agent entry rules

| Field | Value |
|---|---|
| Primary standard | `docs/standards/SOMA-STD-TRIAD-001.md` (shared with somabrain + somafractalmemory) |
| Coding law | `docs/standards/SOMA-STD-CODING-001.md` (VIBE) |
| UI/UX law | `docs/standards/SOMA-STD-UIUX-001.md` (webui: skins · I18N · GATED honesty · A0 · acceptance) |
| Rapid plan | `docs/standards/SOMA-RAPID-DEVELOPMENT-001.md` |
| Status report | `docs/reports/SOMA-RPT-STATUS-001.md` |
| A2A | `docs/plans/a2a/` — claim before large edits; log commits |

## ABSOLUTE LAW — REAL CODE ONLY (operator, 2026-10-09)

**NO SHIMS. NO FAKES. NO MOCKS. NO STUBS. NO PLACEHOLDERS. NO TODO PASSES.**

A shim is a bypass. A mock is a lie. A fake is a defect.
Acceptance = live real services (T-8/VIBE). If a dependency is missing, integrate the **real** library/API or do not ship the feature.

**Always feed these rules to every agent you spawn.**

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
