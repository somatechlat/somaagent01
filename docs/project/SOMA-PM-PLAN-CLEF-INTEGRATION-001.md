# SOMA-PM-PLAN-CLEF-INTEGRATION-001 — Cloudflare Clef integration plan (SA01)

## Document Control

| Field | Value |
|---|---|
| Document Title | Cloudflare Clef integration plan (SA01) |
| Document Identifier | SOMA-PM-PLAN-CLEF-INTEGRATION-001 |
| Version | 1.0.0 |
| Date | 2026-10-12 |
| Status | Draft |
| Author | soma-clef-engineer |
| Approver | operator |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 §8.3 Design and development |
| Next Review | 2027-01-12 |
| Related | `SOMA-ARCH-CLEF-001` (architecture — sole design authority), `SOMA-ARCH-INVARIANTS-001`, `SOMA-STD-CODING-001`, `SOMA-STD-TRIAD-001`, `SOMA-PM-PLAN-JEV-INTEGRATION-001` (obsolete), `SOMA-ARCH-JEV-002` (obsolete) |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-12 | soma-clef-engineer | Initial plan. Derived from `SOMA-ARCH-CLEF-001` §F as-built inventory and §H phased rollout. Closes the dangling reference at `SOMA-ARCH-CLEF-001:17`. |

---

## 1. Purpose

Executable implementation plan for Cloudflare **Clef / Clef-flash** as the SA01 System One decision layer. Architecture is frozen in `SOMA-ARCH-CLEF-001`. This document assigns work, exit criteria, evidence, and owners per wave.

OpenJev is removed. Do not implement from any JEV doc.

## 2. Scope

- In: decision client/contract, tool-choke guardrail, brain decision-facts, OPA evidence inputs, feature flags, settings chain, tests, later waves (router / triage / calibration).
- Out: chat LLM language, memory storage (SomaBrain owns all data), authz (UnifiedGate), Temporal orchestration, any second decision model, any silent fallback.

## 3. Product laws (non-negotiable)

| Law | Enforcement |
|---|---|
| Fail-closed only. No silent fallback, no rule-based "looks safe" stub, no cached decision. | `clef_client.py` refuses unconfigured; `guardrail.py` tighten-only; OPA denies when `p_safe` null |
| `noul` is P(true), never confidence | `contracts.py` + `policy/confidence.rego` |
| Sole client. A second call site is a review failure. | `DecisionClient` / `ClefClient` only |
| Decision-facts must be written to the brain before tier-3 auto-run | `decision_client.py` mandatory `MemoryGateway.remember` |
| No shims / fakes / mocks / stubs / TODO passes | ABSOLUTE LAW |

## 4. Wave plan

### W-C0 — REMOVAL (OpenJev purge)

| Item | Owner | Exit criteria | Status |
|---|---|---|---|
| Delete `openjev` pin, `mod_jev`, JEV tests/scripts, `JEV_*` settings | soma-deadcode-remover | `rg -i 'openjev\|mod_jev\|JEV_'` clean outside historical docs | **DONE** (LEDGER 2026-10-09T19:10Z) |
| Rename flags `jev_*` → `clef_decide` / `clef_guardrail` | soma-clef-engineer | flags live in `features.py` | **DONE** |
| Rename brain namespace `jev.decisions.*` → `clef.decisions.*` | soma-clef-engineer | `contracts.decision_fact_namespace()` | **DONE** |
| Agent profile `soma-jev-engineer` → `soma-clef-engineer` | triad-iso-docs | profile + `CLAUDE.md` updated | **DONE** |
| Retire JEV docs (Obsolete banners) | triad-iso-docs | banners present; hard-delete after claim release | **DONE** (banners) · delete pending |
| Rename rego `jev_required` → `decision_guard_required` | soma-clef-engineer | cosmetic; semantics unchanged | **TRACKED** (non-blocking) |

### W-C1 — CLIENT + CONTRACT

| Item | Path | Exit criteria | Status |
|---|---|---|---|
| Contracts | `services/common/decisions/contracts.py` | `ClefAnswer`, `ClefResponse`, `DecisionSignals`, `DecisionFact`, `map_answers_to_signals`, `outcome_from_signals`, `should_flag` | **LIVE** |
| Clef client | `services/common/decisions/clef_client.py` | `ClefClient.decide()` POST `{model, state, questions}` to `CLEF_AI_RUN_PATH`; fail-closed on missing token/settings | **LIVE** |
| Decision client | `services/common/decisions/decision_client.py` | sole caller of `ClefClient`; mandatory brain write via `MemoryGateway.remember`; `clef_flag_enabled("clef_decide")` | **LIVE** |
| Settings | `config/settings.py` + `settings_model.py` + `capsule_settings.py` | `CLEF_BACKEND`, `CLEF_API_BASE`, `CLEF_ACCOUNT_ID`, `CLEF_MODEL_ID`, `CLEF_TIMEOUT_MS`, `CLEF_MAX_STATE_CHARS` | **LIVE** |
| Module shell | `admin/modules/mod_clef/module.yaml` | `feature_flag: clef_decide`, `permissions: [network, vault:read]` | **LIVE** |
| Contract tests | `tests/unit/test_clef_contracts.py` | schema freeze; shape change fails build | **LIVE** |
| Vault token | `secret/agent/api_keys/cloudflare_api_key` | `get_credential` / `get_secret_manager` | **OPEN — operator I-1** |

### W-C2 — GUARDRAIL CHOKE (first ship)

| Item | Path | Exit criteria | Status |
|---|---|---|---|
| Guardrail | `services/common/decisions/guardrail.py` | `choke_tool_call()` tighten-only; tier sets TIER1/2/3; `opa_input_from_signals()` | **LIVE** |
| Choke wiring | `admin/core/tool_calling.py` `decide_and_authorize_tool()` | calls `choke_tool_call`; fail-closed on exception | **LIVE** |
| OPA | `policy/confidence.rego` | consumes `p_safe`/`risk`/`confidence`/`decision_guard`; deny when `p_safe` null | **LIVE** |
| Feature flags | `services/common/features.py` | `clef_decide`, `clef_guardrail` (depends on `clef_decide`) | **LIVE** |
| Guardrail tests | `tests/unit/test_clef_guardrail.py` | flag-off and Clef-down both fail closed; tier-3 stays approval-gated | **LIVE** |
| Operator demo on real tools | human Playwright / e2e | tier-3 denied without decision; auto_execute only with brain-written fact | **PENDING operator I-1…I-3** |

**First ship = W-C0 + W-C1 + W-C2.** Code is live in tree. Runtime enablement blocked on I-1 (Cloudflare token in Vault).

### W-C3 — Decision surfaces (NOT STARTED)

| Item | Exit criteria |
|---|---|
| D-5 urgency `score` | urgency badge in UI |
| D-6 escalation `noul` | escalation path uses `should_flag` |
| D-3 tool `choice` rank | ranked tool list |
| D-4 model-router tie-break | evidence per mode |

### W-C4 — Exposure + vision (NOT STARTED)

| Item | Exit criteria |
|---|---|
| `clef_decide` tool exposure | tool gated; deferred on purpose until golden set exists |
| Vision path (I-4) | vision golden cases |
| Per-tenant backend override | residency tenants isolated |

### W-C5 — Calibration (NOT STARTED)

| Item | Exit criteria |
|---|---|
| Temporal calibration workflow | calibration report |
| flash-vs-clef benchmark | model split justified by data |
| Threshold retune | thresholds justified by data |

### W-C6 — Optional fine-tune (NOT STARTED, opt-in only)

| Item | Exit criteria |
|---|---|
| Cloudflare RL on SA01 decision traces | fine-tuned model behind `CLEF_MODEL_ID` |

## 5. Operator gates (block runtime, not code)

| # | Gate | Blocks | Default |
|---|---|---|---|
| **I-1** | Cloudflare account + scoped API token in Vault at `secret/agent/api_keys/cloudflare_api_key`; accept tool-state egress in `workers_ai` mode | first live call | cannot ship `workers_ai`; must choose `hf`+GPU or hold |
| **I-2** | Primary backend: Workers AI or HF weights | W-C1 runtime | Workers AI primary; HF residency alternate |
| **I-3** | Model split: flash on choke, full Clef async — or pin one | W-C1 runtime | split as recommended |
| **I-5** | Tenancy: shared account vs per-tenant override | W-C2 | shared + override hook |
| **I-6** | Residency tenants forbidding third-party egress | W-C2 | assume none until stated |
| **I-7** | Workers AI budget ceiling + alert owner | W-C2 | alert-only |
| **I-8** | A2A: supersede `soma-jev-engineer` claims → `soma-clef-engineer` | W-C0 close | supersede |
| **I-9** | RL fine-tune partnership | W-C6 | out of scope for now |

## 6. Evidence required before any wave ships

1. `pytest tests/unit/test_clef_contracts.py tests/unit/test_clef_guardrail.py` green.
2. Fail-closed drill: unset `CLEF_*` / kill token ⇒ tier-3 **denied**, tier-2 **approval_required** (never allow).
3. Brain-write drill: decision-fact recallable under `clef.decisions.{category}`; lost fact ⇒ tier-3 blocked.
4. `rg -n 'TODO|FIXME|placeholder|shim|stub|mock|fake' services/common/decisions/ admin/core/tool_calling.py` clean.
5. No literal model id or token in source (`CLEF_MODEL_ID` via `require_setting` only).
6. Human Playwright session green on real services (Done definition).

## 7. Related documents

| Doc | Role |
|---|---|
| `SOMA-ARCH-CLEF-001` | Sole architecture authority (as-built + design) |
| `SOMA-ARCH-JEV-001/002`, `SOMA-PM-JEV-PIN-001`, `SOMA-PM-PLAN-JEV-INTEGRATION-001` | Obsolete historical record — do not implement |
| `SOMA-STD-TRIAD-001` / `SOMA-STD-CODING-001` | Governing law |
| `docs/plans/a2a/LEDGER.md` | Execution history |

---

*End of document — SOMA-PM-PLAN-CLEF-INTEGRATION-001 v1.0.0*
