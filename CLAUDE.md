# somaAgent01 — agent entry rules

| Field | Value |
|---|---|
| Primary standard | `docs/standards/SOMA-STD-TRIAD-001.md` (shared with somabrain + somafractalmemory) |
| Coding law | `docs/standards/SOMA-STD-CODING-001.md` (VIBE) |
| Rapid plan | `docs/standards/SOMA-RAPID-DEVELOPMENT-001.md` |
| Status report | `docs/reports/SOMA-RPT-STATUS-001.md` |
| A2A | `docs/plans/a2a/` — claim before large edits; log commits |

## Stack lock

Django Ninja · Django ORM · Lit 3.x · Milvus (via SomaBrain) · Temporal for async · Vault secrets · **no React/Alpine/FastAPI/SQLAlchemy/Qdrant**.

## Memory

T-1: only `MemoryGateway` → `SomaBrainAdapter`. Never an SFM client.

## Local project agents (`.mimocode/agent/`)

| Agent | Use for |
|---|---|
| `soma-wiring-engineer` | Memory seam, adapter, Temporal workers, phantom routes |
| `soma-ui-engineer` | webui Lit UI, A0 chrome, honest states |
| `soma-cognitive-engineer` | Cognitive API wiring in chat orchestrator |
| `soma-temporal-ops` | Temporal 100% + env contract |
| `soma-adversarial-skeptic` | Every wave critic (parallel with builder) |
| `triad-iso-docs` | ISO document control |

## How to invoke

Say in chat: use `soma-ui-engineer` for X · use `soma-adversarial-skeptic` on this diff · or spawn via the actor/subagent mechanism with that name.

## Done =

Human Playwright session green on real services — not skip-gated, not mocked.
