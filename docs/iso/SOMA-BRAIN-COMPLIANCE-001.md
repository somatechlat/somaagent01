# SOMA-BRAIN-COMPLIANCE-001 — SomaBrain No-Fakes / No-Bypasses Audit

## Document Control

| Field | Value |
|-------|-------|
| Document Identifier | SOMA-BRAIN-COMPLIANCE-001 |
| Version | 1.0.0 |
| Date | 2026-09-27 |
| Status | Findings open — remediation in progress |
| Related | `SOMA-A0-PARITY-001.md`, `SOMA-TRIAD-ARCH-001.md`, `SOMA-STD-CODING-001.md` |
| Scope | `somabrain/` production code + tests |

## Rules enforced

| Rule | Source |
|------|--------|
| No mocks, no stubs, no fakes, no bypasses | VIBE / user 2026-09-27 |
| Fail-closed at every boundary | T-5 |
| One coordinate authority | T-2 |
| One write lane | T-1 |
| Tests prove behaviour against real services | T-8 |
| No silent `"default"` tenant | R-05 |

---

## Verdict

**NOT COMPLIANT.** Production code and tests still contain fail-opens, duplicate coord authority, a direct-backend bypass, and mocked suites. Kafka startup correctly refuses localhost fallback (good). Wire path `remember → MemoryClient → SFM` is real. Several `return []` sites treat outage as empty success (F-10 class defect).

| Area | Status |
|------|--------|
| Live memory write/read/delete to SFM | REAL (HTTP client + outbox) |
| Coordinate authority | **FAIL** — `_stable_coord` still 2+ copies in-repo |
| Tenant fail-closed | **FAIL** — multiple `or "default"` |
| Recall outage honesty | **PARTIAL** — agent adapters fixed; brain `recall_ops` still `return []` |
| Forget | REAL (implemented this session) |
| Mocked tests | **FAIL** — 3 files still mock |
| Direct backend bypass | **FAIL** — `direct_backend.py` still present |
| Feature flags / quota / OPA | Mostly real |
| Docs examples showing mocks | Noise (ONBOARDING.md / CONTRIBUTING.md) |

---

## Findings (production)

### BF-01 · HIGH · Duplicate `_stable_coord` (T-2)

| Copy | Location |
|------|----------|
| 1 | `somabrain/memory/client/serialization.py:9` |
| 2 | `somabrain/memory/normalization.py:13` |
| 3 | Preimage wrappers: `memory/client/write.py:31`, `memory/client/core.py:43`, `memory/utils.py:83` |

**Action:** import from shared `soma-memory-contract` (M4). Until then, `normalization._stable_coord` must re-export the serialization definition only.

### BF-02 · HIGH · Silent `"default"` tenant (T-5 / R-05)

| Location | Snippet |
|----------|---------|
| `memory/transport.py:322-323` | `namespace or "default"`, `tenant or "default"` |
| `memory/client/core.py:31` | `namespace or "default"` |
| `db/outbox.py:301,325` | `tenant_id or "default"` |
| `services/tiered_memory_registry.py:68` | `tenant or "default"` |
| `workers/quota_manager.py:51,83` | `tenant_id or "default"` |
| `services/learner_*.py`, `outbox_sync/clean/replay` | same pattern |
| `services/retrieval_pipeline.py:44` | `namespace or "default"` |

**Action:** raise / reject when tenant or namespace unresolved on **request paths**. Label-only default for metrics is acceptable **only** if tagged `unspecified` not a real tenant.

### BF-03 · HIGH · Recall treats outage as empty (F-10)

`memory/recall_ops.py` — many `return []` on error/empty including transport failure paths (`:29,99,106,117,125,193,257,400,415`).
`memory/hybrid.py:218,276,322,375`, `memory/client/read.py:87,98,109`, `memory/utils.py:96+`.

**Action:** empty result is OK for “no hits”. Transport/HTTP failure must raise `MemoryServiceError` / `MemoryRecallUnavailable`, never `[]`.

### BF-04 · HIGH · `direct_backend` write bypass (T-1)

`somabrain/memory/direct_backend.py` + `memory/backends.py` factory — in-process SFM bypasses HTTP tenant/coord contract.

**Action:** delete or feature-flag **off** by default with explicit AAAS justification (OD-1 default: delete).

### BF-05 · MED · Fail-open security leftovers

| Location | Issue |
|----------|-------|
| `aaas/webhooks.py:58` | `return True  # Allow in development` |
| `core/security/vault_client.py:74` | test env Vault bypass |
| `aaas/granular.py:483` | AAAS_ADMIN bypass comment path |
| `bootstrap/runtime_init.py:202` | pytest disable enforcement |

**Action:** development bypasses must be compile-time/settings-gated and off in STANDALONE/production profile.

### BF-06 · MED · Metrics no-op fallback

`metrics/memory_metrics.py:268` — “no-op metric when Prometheus registry has conflicts”.

**Action:** fail-closed or structured degrade; no silent no-op.

### BF-07 · LOW · Settings comments implying Redis pattern bypass

`brain_settings/models.py:172` — incomplete Redis pattern delete. Behaviour may be OK; comment admits production gap.

---

## Findings (tests) — T-8

| File | Issue | Action |
|------|-------|--------|
| `tests/unit/test_aaas_mode.py` | `MagicMock`, `@patch(MemoryClient)`, monkeypatch | Rewrite vs live or pure config |
| `tests/unit/test_memory_service.py` | `_FakeNamespaceClient`, `_FakeBackend` | Live integration or delete |
| `tests/oak/test_thread.py` | monkeypatch | Acceptable if pure; else live |
| `tests/integration/test_seam_contract.py` | states it replaces fakes | Keep if live |

`scripts/ci/forbid_stubs.sh` exists — wire into CI.

---

## Positive findings (compliant)

- `services/orchestrator_service.py:78` and `workers/wm_updates_cache.py:51` **refuse localhost Kafka fallback**
- `lifecycle/startup.py:339-343` warns/rejects localhost memory endpoint in Docker
- `memory/transport.py` loop-aware async client (F-09 fixed)
- `POST /memory/forget` implemented (this session)
- Outbox durable path present (`db/outbox.py`, `remember.py`)
- Circuit breaker on `MemoryService`
- `hmac.compare_digest` token checks

---

## Remediation order (SomaBrain)

| # | Item | Exit |
|---|------|------|
| 1 | BF-02 request-path tenant/namespace fail-closed | no `or "default"` on request path |
| 2 | BF-03 recall raises on transport failure | kill `return []` on error |
| 3 | BF-04 remove/gate `direct_backend` | no hot-path bypass |
| 4 | BF-01 collapse `_stable_coord` | 1 definition |
| 5 | BF-05/06 security/metrics fail-closed | no dev bypass in prod |
| 6 | BF-T tests de-mock | CI forbid_stubs green |

---

## Live stack note (2026-09-27)

Agent, Brain (:30101), SFM (:10101) healthy. Agent memory env wired (`SOMABRAIN_URL`, `SOMAFRACTALMEMORY_URL`, tokens). One write lane on **agent** side is brain-only (done). **Brain internal** compliance is this document.
