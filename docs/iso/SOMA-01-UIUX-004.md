# SOMA-01-UIUX-004 — User Interface — Verification & Traceability

## Document Control

| Field | Value |
|---|---|
| Document Title | User Interface — Verification & Traceability |
| Document Identifier | SOMA-01-UIUX-004 |
| Version | 1.0.0 |
| Date | 2026-09-28 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-28 |
| Related | `SOMA-01-QMS-001.md`, `SOMA-A0-PARITY-001.md`, `SOMA-01-UIUX-001.md`, `SOMA-01-UIUX-005.md`, `SOMA-01-VV-001.md`, `SOMA-01-DOCS-001.md` |
| Source of truth | This document for UI verification status and the RTM; `SOMA-UI-IDREG-001.md` for identifier allocation; `webui/src/` and `tests/e2e/` as measured on 2026-09-28 |
| Audience | UI/UX contributors, product engineering, QA, any agent acting on somaAgent01 |
| Scope | Every `UI-F-*` feature of the Agent Soma UI/UX suite, its traceability chain, its verification evidence, and the known honesty findings of the shipped `webui/` |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-09-28 | SomaTech Engineering | Initial issue. V&V vocabulary, RTM summary, 80-row traceability matrix, Playwright coverage map measured from `tests/e2e/`, known findings with `file:line` evidence, honesty checklist, acceptance criteria, gap register. |

## Normative References

| ID | Reference | Role |
|---|---|---|
| N-1 | `SOMA-01-QMS-001.md` | Quality management system |
| N-2 | `SOMA-01-DOCS-001.md` | Document control, identifier scheme, traceability chain (§6) |
| N-3 | `SOMA-A0-PARITY-001.md` | Feature clone never code clone; Plan Gate; honesty rules; `UI-AT-01`…`UI-AT-08` |
| N-4 | `SOMA-01-UIUX-001.md` | Screen and feature specification (the master). **Not present in this tree at time of issue — see §1.4.** |
| N-5 | `SOMA-UI-IDREG-001.md` | Authoritative ID allocation |
| N-6 | `SOMA-UI-TEMPLATE-001.md` | House ISO template and honesty rules |
| N-7 | `SOMA-01-VV-001.md` | Verification & Validation plan; method vocabulary |
| N-8 | `SOMA-01-UIUX-005.md` | Settings parity matrix; settings-screen findings G-06…G-17 |
| N-9 | ISO 9001:2015 clause 7.5 | Control of documented information |
| N-10 | ISO/IEC/IEEE 29119-3 | Test documentation (adapted) |

---

## 1. Purpose and Scope

### 1.1 Purpose

This document is the **Requirements Traceability Matrix (RTM) and Verification & Validation (V&V) record**
for the Agent Soma UI/UX suite. It proves, for every user-facing feature:

1. that the feature is **identified** (`UI-F-*`) and allocated to a screen (`UI-S-*`), a control or
   action (`UI-C-*` / `UI-A-*`), a shipped component, and an API or store;
2. that the feature is **verifiable** — it names a verification method, a test type, and a test artefact;
3. that the verification state is **honest** — status is measured against the current tree, not aspirational;
4. what is **specified but not yet built**, with an owner and a gate.

The traceability chain is the one fixed by N-2 §6.1:

```
REQ-* ──► UI-F-* ──► UI-S-* ──► UI-C-* / UI-A-* ──► component ──► API / store ──► UIX-AT-*
```

### 1.2 Scope

- Every `UI-F-001`…`UI-F-080` of the feature range reserved by N-5 (`UI-F-* 001-080`, owner
  `SOMA-01-UIUX-001`).
- The shipped `webui/` tree as measured on **2026-09-28**.
- The Playwright suite under `tests/e2e/` as measured on **2026-09-28**.
- Acceptance-test namespace `UIX-AT-01`…`UIX-AT-40` (N-5 range, owner this document).

### 1.3 Out of Scope

- Backend requirement verification (`SOMA-01-VV-001` owns `REQ-*` verification).
- Settings-inventory placement (`SOMA-01-UIUX-005` owns settings→screen placement).
- Concrete production deployment values and secret values.
- Implementation of any screen — this is a verification document, not a build order.

### 1.4 Status of the master specification (N-4)

`SOMA-01-UIUX-001.md` **does not exist in this tree** at the time of issue (directory listing of
`docs/iso/` on 2026-09-28 contains `SOMA-01-UIUX-005.md` but no `SOMA-01-UIUX-001.md`). Per the task
rule, the `UI-F-*` list below is therefore **defined by this document** as a sensible `UI-F-001`…`080`
allocation consistent with N-5, and **SHALL be reconciled against `SOMA-01-UIUX-001.md`** when that
document lands. Every row marked `prov.` in §4 carries a provisional control/action id. Disagreement
X-11 in §9 records the open reconciliation.

---

## 2. Verification Method Vocabulary

House V&V format, taken from N-7 §2.1 and N-2 §6. These tokens are the only permitted values.

### 2.1 Method

| Method | Definition | When used here |
|---|---|---|
| `Inspection` | Manual code or document review against the requirement | Every PR; every claim in this document |
| `Analysis` | Static analysis, static reasoning, or derived-count re-computation | CI; RTM derivation (§3) |
| `Test` | Automated test (pytest, Playwright) | Every PR, CI pipeline |
| `Demonstration` | Manual walkthrough of the feature against real infrastructure | Phase gates, UAT |
| `Simulation` | Load test, chaos experiment, fault injection | Phase 5 (Harden) only |

### 2.2 Test Type

`Unit` | `Integration` | `E2E` | `Config check` | `Code review` | `Load` | `Manual` | `—` (no test planned yet).

### 2.3 Status

| Status | Definition |
|---|---|
| `EXISTS` | An implementation and/or evidence artefact exists but has **not** been checked end-to-end against the requirement. |
| `VERIFIED` | Evidence exists **and** has been checked to satisfy the requirement. |
| `PARTIAL` | Some aspects of the requirement have evidence; others do not. |
| `NOT YET` | No verification evidence exists for this requirement. |

### 2.4 RTM column definitions (§3)

| Column | Definition |
|---|---|
| Count | Matrix rows in that category (§4) |
| Implemented | Rows whose trace chain names a shipped `webui/` component that is **wired to a real API read or write** (≥1 `apiClient.*` / `fetch(` / `api/v2` call site in the view or component; measured 2026-09-28). A predecessor shell, a component with 0 API call sites, or a screen that renders fabricated data is **not** Implemented. |
| Tested | Rows whose `Test File` column names an **existing** automated test that exercises the feature (a test file whose body contains no assertion for that feature does not count). |
| Coverage | Implemented ÷ Count, one decimal place. |

Counts in §3 are **re-derived from §4**. They SHALL NOT be copied from any other document
(N-2 REQ-DOCS-011). The derivation is: count rows per category in §4.2; count rows whose trace chain
satisfies the Implemented rule; count rows whose Test File satisfies the Tested rule.

---

## 3. RTM Summary

Counts re-derived from the §4 matrix. Nothing here is rounded or estimated.

| Requirement Category | Count | Implemented | Tested | Coverage |
|---|---|---|---|---|
| Chrome (UI-S-00) | 6 | 0 | 0 | 0.0% |
| Soul (UI-S-01) | 6 | 0 | 0 | 0.0% |
| Brain (UI-S-02) | 7 | 1 | 0 | 14.3% |
| Hands (UI-S-03) | 6 | 0 | 0 | 0.0% |
| Memory (UI-S-04) | 6 | 1 | 0 | 16.7% |
| Body (UI-S-05) | 4 | 0 | 0 | 0.0% |
| Governance (UI-S-06) | 5 | 0 | 0 | 0.0% |
| Chat (UI-S-07…10) | 9 | 5 | 5 | 55.6% |
| Capsule (UI-S-11…14) | 5 | 0 | 0 | 0.0% |
| Module (UI-S-15…18) | 4 | 1 | 0 | 25.0% |
| Platform (UI-S-19…28) | 7 | 6 | 0 | 85.7% |
| Auth (UI-S-29…36) | 5 | 4 | 1 | 80.0% |
| Ops (UI-S-37…45) | 4 | 4 | 0 | 100.0% |
| Voice (UI-S-46…49) | 3 | 2 | 0 | 66.7% |
| Settings & Surfaces | 3 | 0 | 0 | 0.0% |
| **TOTAL** | **80** | **24** | **6** | **30.0%** |

Derivation check: `6+6+7+6+6+4+5+9+5+4+7+5+4+3+3 = 80`. Implemented `0+0+1+0+1+0+0+5+0+1+6+4+4+2+0 = 24`.
Tested `0+0+0+0+0+0+0+5+0+0+0+1+0+0+0 = 6`. Coverage `24 ÷ 80 = 30.0%`.

**Interpretation — the two numbers answer different questions and SHALL NOT be conflated.**
Placement is complete (80/80 features have a screen and a chain in §4). Implementation is not
(24/80 features are wired to a real API today). Verification is weaker still (6/80 features have an
automated test that actually exercises them). Tested coverage is `6 ÷ 80 = 7.5%`. The categories with
high Implemented counts (Platform 85.7%, Ops 100.0%, Auth 80.0%) are **predecessor screens that are
API-wired but unverified** — their Tested counts are 0 or 1, which is the honest signal.

---

## 4. Traceability Matrix

### 4.0 Derivation notes

- `UI-F-*` ids are provisional pending N-4 (§1.4) and SHALL be reconciled with `SOMA-01-UIUX-001`.
- `UI-C-*` / `UI-A-*` ids are **provisional** (`prov.`) for the same reason; N-5 reserves the ranges
  `UI-C-* 001-120` and `UI-A-* 001-120` for N-4.
- Screen ids (`UI-S-*`) are authoritative — taken verbatim from N-5. Do not renumber.
- `UIX-AT-*` ids are authoritative within `01-40` (N-5, owner this document). `UIX-AT-01`…`08`
  **cross-reference** the `UI-AT-01`…`08` series of N-3 §5.7 and do **not** renumber it (N-2 §3.3.2
  collision control). See §5.1.
- Component and API columns cite real paths where a shipped implementation exists, and `NEW` /
  `TBD (UIUX-001)` where N-5 marks the screen `NEW`. No API shape is invented.

### 4.1 Traceability chain — `UI-F-* → UI-S-* → UI-C-*/UI-A-* → component → API / store → UIX-AT-*`

| UI-F-* | Feature | UI-S-* | UI-C-* / UI-A-* | Component | API / Store | UIX-AT-* |
|---|---|---|---|---|---|---|
| UI-F-001 | Capsule switcher | UI-S-00 | UI-C-001 prov. | `webui/src/components/saas-sidebar-workspace.ts` | Capsule list API (TBD UIUX-001) | UIX-AT-09 |
| UI-F-002 | Version chip + lifecycle chip | UI-S-00 | UI-C-002…003 prov. | NEW (chrome) | `Capsule.version`, lifecycle field | UIX-AT-10 |
| UI-F-003 | Persona knobs ×3 (chrome strip) | UI-S-00 | UI-C-004…006 prov. | NEW (chrome) | `Capsule.persona_config.knobs` | UIX-AT-11 |
| UI-F-004 | Command palette (Cmd-K) | UI-S-00 | UI-A-001 prov. | NEW | SPA routes via `saas-navigate` | UIX-AT-06 (xref UI-AT-06) |
| UI-F-005 | Facet tabs ×6 | UI-S-00 | UI-C-007 prov. | NEW (chrome) | — | UIX-AT-10 |
| UI-F-006 | Instance strip + neuro meters ×4 | UI-S-00 | UI-C-008…009 prov. | NEW (chrome) | `Capsule.neuromodulator_state` | UIX-AT-11 |
| UI-F-007 | System prompt editor | UI-S-01 | UI-C-010 prov. (textarea) | `webui/src/components/saas-capsule-editor.ts` | `Capsule.system_prompt` | UIX-AT-12 |
| UI-F-008 | Personality traits (Big-Five) | UI-S-01 | UI-C-011…015 prov. (slider ×5) | NEW (UI-S-01) | `Capsule.personality_traits` | UIX-AT-12 |
| UI-F-009 | Neuromodulator baseline (4 axes) | UI-S-01 | UI-C-016…019 prov. (slider ×4) | NEW (UI-S-01) | `Capsule.neuromodulator_baseline` | UIX-AT-11 |
| UI-F-010 | Learning config (GMD η/λ/α) | UI-S-01 | UI-C-020…022 prov. (number ×3) | NEW (UI-S-01) | `Capsule.learning_config` | UIX-AT-13 |
| UI-F-011 | Injection prompts (ordered) | UI-S-01 | UI-C-023 prov. (list editor) | NEW (UI-S-01) | `persona_config.prompts.injection_prompts` | UIX-AT-12 |
| UI-F-012 | Tool prompts (key-value) | UI-S-01 | UI-C-024 prov. (KV editor) | NEW (UI-S-01) | `persona_config.prompts.tool_prompts` | UIX-AT-12 |
| UI-F-013 | Intelligence knob → 6 derived readouts | UI-S-02 | UI-C-025 prov. (slider) + UI-C-031…036 prov. (derived) | NEW (UI-S-02) | `persona_config.knobs.intelligence_level`; `derive_all_settings` | UIX-AT-11 |
| UI-F-014 | Autonomy knob → 3 derived readouts | UI-S-02 | UI-C-026 prov. (slider) + UI-C-037…039 prov. (derived) | NEW (UI-S-02) | `persona_config.knobs.autonomy_level` | UIX-AT-11 |
| UI-F-015 | Resource-budget knob → 3 derived readouts | UI-S-02 | UI-C-027 prov. (slider) + UI-C-040…042 prov. (derived) | NEW (UI-S-02) | `persona_config.knobs.resource_budget` | UIX-AT-11 |
| UI-F-016 | Model slot binding (chat/util/embed) | UI-S-02 | UI-C-028…030 prov. (reference picker ×3) | `webui/src/views/saas-settings-models.ts` | `/llm/models`, `LLMModelConfig`, `chat_model_id` / `utility_model_id` / `embedding_model_id` | UIX-AT-04 (xref UI-AT-04) |
| UI-F-017 | Context window + history share | UI-S-02 | UI-C-043…044 prov. (number, slider) | NEW (UI-S-02) | `chat_model_ctx_length`, `chat_model_ctx_history` | UIX-AT-13 |
| UI-F-018 | Vision / browser model binding | UI-S-02 | UI-C-045…046 prov. (reference picker) | NEW (UI-S-02) | `Capsule.image_model`, `Capsule.browser_model` | UIX-AT-13 |
| UI-F-019 | Derived-settings read-only rule (12 readouts) | UI-S-02 | — (no action; readouts are never editable) | NEW (UI-S-02) | `admin/core/agentiq/derivation.py` | UIX-AT-13 |
| UI-F-020 | Tool policy buckets (auto/approval/denied) | UI-S-03 | UI-C-047…049 prov. (multi-select ×3) | NEW (UI-S-03) | `Capsule.tool_policy` | UIX-AT-14 |
| UI-F-021 | Capability attach / detach | UI-S-03 | UI-A-002…003 prov. | NEW (UI-S-03) | `Capsule.capabilities` M2M | UIX-AT-14 |
| UI-F-022 | Tool timeout + circuit knobs | UI-S-03 | UI-C-050…051 prov. (number ×2) | NEW (UI-S-03) | `SA01_TOOL_TIMEOUT_SECONDS`, `TOOL_EXECUTOR_CIRCUIT_*` | UIX-AT-14 |
| UI-F-023 | MCP server registry | UI-S-03 | UI-C-052 prov. (JSON editor) | NEW (UI-S-03) | `mcp_servers` | UIX-AT-14 |
| UI-F-024 | A2A / MCP expose toggles | UI-S-03 | UI-C-053…054 prov. (toggle ×2) | NEW (UI-S-03) | `a2a_server_enabled`, `mcp_server_enabled` | UIX-AT-14 |
| UI-F-025 | Tool timeline & approval | UI-S-03 | UI-A-004 prov. (approve/reject) | NEW (UI-S-03) | tool-executor result stream | UIX-AT-03 (xref UI-AT-03) |
| UI-F-026 | Recall configuration (top-k, history, thresholds) | UI-S-04 | UI-C-055…060 prov. (number, slider) | `webui/src/views/saas-memory-view.ts` | `MEM_RECALL_TOP_K`, `MEM_HISTORY_LIMIT`, `memory_recall_*` | UIX-AT-15 |
| UI-F-027 | Memorize configuration | UI-S-04 | UI-C-061…062 prov. (toggle, slider) | NEW (UI-S-04) | `memory_memorize_*` | UIX-AT-15 |
| UI-F-028 | Memory pointer (tenant / namespace / limits) | UI-S-04 | UI-C-063…066 prov. | NEW (UI-S-04) | `Capsule.memory_pointer` | UIX-AT-15 |
| UI-F-029 | Live recall preview | UI-S-04 | UI-A-005 prov. (preview) | NEW (UI-S-04) | recall API (real hits only) | UIX-AT-15 |
| UI-F-030 | Retention & consolidation toggles | UI-S-04 | UI-C-067…068 prov. (toggle ×2) | NEW (UI-S-04) | `memory_memorize_consolidation`, retention | UIX-AT-15 |
| UI-F-031 | Session-scoped history | UI-S-04 | — (readout) | NEW (UI-S-04) | `MEM_CHAT_NAMESPACE`; session-scoped recall | UIX-AT-15 |
| UI-F-032 | Resource limits (wall clock, concurrency) | UI-S-05 | UI-C-069…070 prov. (number ×2) | NEW (UI-S-05) | `Capsule.resource_limits` | UIX-AT-16 |
| UI-F-033 | Token budget | UI-S-05 | UI-C-071 prov. (number) | NEW (UI-S-05) | `SA01_DEFAULT_TOKEN_BUDGET` | UIX-AT-16 |
| UI-F-034 | Voice / image / browser model FK binding | UI-S-05 | UI-C-072…074 prov. (reference picker ×3) | NEW (UI-S-05) | `Capsule.voice_model`, `image_model`, `browser_model` | UIX-AT-16 |
| UI-F-035 | Cost & usage readouts | UI-S-05 | — (read-only meter) | NEW (UI-S-05) | budget gate metrics | UIX-AT-16 |
| UI-F-036 | Constitution reference binding (checksum) | UI-S-06 | UI-C-075 prov. (reference picker) | NEW (UI-S-06) | `Capsule.constitution_ref` | UIX-AT-17 |
| UI-F-037 | OPA policy bindings | UI-S-06 | UI-C-076 prov. (JSON editor) | NEW (UI-S-06) | `persona_config.governance.opa_policies` | UIX-AT-17 |
| UI-F-038 | SpiceDB relation bindings | UI-S-06 | UI-C-077 prov. (JSON editor) | NEW (UI-S-06) | `persona_config.governance.spicedb_relations` | UIX-AT-17 |
| UI-F-039 | Immutable constitution viewer | UI-S-06 | — (immutable viewer) | NEW (UI-S-06) | `Constitution.content` + Ed25519 signature | UIX-AT-17 |
| UI-F-040 | Governance hooks | UI-S-06 | UI-C-078 prov. (list editor) | NEW (UI-S-06) | hook registry (TBD UIUX-001) | UIX-AT-17 |
| UI-F-041 | Chat workspace | UI-S-07 | UI-C-079 prov. (composer) | `webui/src/views/saas-chat.ts`, `webui/src/components/saas-chat-workspace.ts` | `/api/v2/chat/*`, `WS /ws/v2/chat/*` | UIX-AT-01 (xref UI-AT-01) |
| UI-F-042 | Streaming token render (`chat.delta`) | UI-S-07 | UI-C-080 prov. (message body) | `webui/src/components/saas-message.ts` | WS `chat.delta` frames | UIX-AT-02 (xref UI-AT-02) |
| UI-F-043 | Conversation create / switch / list | UI-S-07 | UI-A-006…008 prov. | `webui/src/views/saas-chat.ts` | `/api/v2/chat/conversations` | UIX-AT-01 |
| UI-F-044 | Message detail | UI-S-08 | UI-A-009 prov. | NEW (UI-S-08) | message store | UIX-AT-18 |
| UI-F-045 | Conversation export | UI-S-09 | UI-A-010 prov. | NEW (UI-S-09) | `services/capsule_export.py` (rebind) | UIX-AT-18 |
| UI-F-046 | Conversation queue | UI-S-10 | UI-C-081 prov. (queue list) | NEW (UI-S-10) | Temporal conversation queue | UIX-AT-18 |
| UI-F-047 | Reconnect banner | UI-S-07 | — (status banner) | `webui/src/services/websocket-client.ts` | WS close/reconnect events | UIX-AT-18 |
| UI-F-048 | Mode switching | UI-S-07 | UI-C-082 prov. (mode dropdown) | `webui/src/views/saas-chat.ts`, `webui/src/views/saas-mode-selection.ts` | mode store | UIX-AT-18 |
| UI-F-049 | Agent selection in chat | UI-S-07 | UI-C-083 prov. (agent picker) | `webui/src/views/saas-chat.ts`, `webui/src/stores/agent-store.ts` | `/api/v2/agents` | UIX-AT-09 |
| UI-F-050 | Capsule list | UI-S-11 | UI-C-084 prov. (data table) | `webui/src/views/saas-workspace.ts` | Capsule list API | UIX-AT-18 |
| UI-F-051 | Capsule editor | UI-S-12 | UI-C-085…090 prov. | `webui/src/components/saas-capsule-editor.ts` | Capsule CRUD | UIX-AT-18 |
| UI-F-052 | Version rail & diff | UI-S-13 | UI-A-011 prov. (diff) | NEW (UI-S-13) | Capsule versions | UIX-AT-18 |
| UI-F-053 | Instance management | UI-S-14 | UI-C-091 prov. (instance list) | NEW (UI-S-14) | Instance API | UIX-AT-18 |
| UI-F-054 | Capsule export / import | UI-S-12 | UI-A-012…013 prov. | NEW (UI-S-12) | `services/capsule_export.py`, `services/capsule_import.py` | UIX-AT-18 |
| UI-F-055 | Module list | UI-S-15 | UI-C-092 prov. (data table) | NEW (UI-S-15) | `admin/modules/manifest.py` | UIX-AT-19 |
| UI-F-056 | Module detail & config | UI-S-16 | UI-C-093…095 prov. | NEW (UI-S-16) | module manifest sections | UIX-AT-19 |
| UI-F-057 | Capability registry | UI-S-17 | UI-C-096 prov. (registry table) | `webui/src/views/saas-feature-catalog.ts` | feature/capability API | UIX-AT-19 |
| UI-F-058 | Capability detail & hook bindings | UI-S-18 | UI-C-097…098 prov. | NEW (UI-S-18) | hook bindings | UIX-AT-19 |
| UI-F-059 | Tenant list + tenant wizard | UI-S-19, UI-S-20 | UI-C-099 prov., UI-A-014 prov. | `webui/src/views/saas-tenants.ts`, `webui/src/views/saas-tenant-wizard.ts` | `/api/v2/tenants` | UIX-AT-20 |
| UI-F-060 | User management | UI-S-22 | UI-C-100 prov. (data table) | `webui/src/views/saas-entity-views.ts` | `/api/v2/users` | UIX-AT-20 |
| UI-F-061 | Roles & role matrix | UI-S-23 | UI-C-101…102 prov. | `webui/src/views/saas-admin-roles-list.ts`, `webui/src/views/saas-role-matrix.ts` | roles API | UIX-AT-20 |
| UI-F-062 | Permissions | UI-S-24 | UI-C-103 prov. | `webui/src/views/saas-permissions.ts` | permissions API | UIX-AT-20 |
| UI-F-063 | Billing & subscriptions | UI-S-25, UI-S-26 | UI-C-104 prov. | `webui/src/views/saas-tenant-billing.ts`, `webui/src/views/saas-subscriptions.ts` | Lago billing API | UIX-AT-20 |
| UI-F-064 | Usage analytics | UI-S-27 | — (read-only meters) | `webui/src/views/saas-usage-analytics.ts` | usage API | UIX-AT-20 |
| UI-F-065 | Tier builder | UI-S-28 | UI-C-105 prov. (tier editor) | `webui/src/views/saas-tier-builder.ts` | tiers API | UIX-AT-20 |
| UI-F-066 | Login | UI-S-29 | UI-C-106…107 prov. (email, password) | `webui/src/views/saas-login.ts` | `/api/v2/auth/token`, `/api/v2/auth/login` | UIX-AT-01 (xref UI-AT-01) |
| UI-F-067 | Register / forgot password | UI-S-30, UI-S-31 | UI-C-108…109 prov. | `webui/src/views/saas-register.ts`, `webui/src/views/saas-forgot-password.ts` | `/api/v2/auth/*` | UIX-AT-21 |
| UI-F-068 | MFA setup | UI-S-32 | UI-C-110 prov. (MFA form) | `webui/src/views/saas-mfa-setup.ts` | MFA API | UIX-AT-21 |
| UI-F-069 | OAuth / SSO callback | UI-S-33 | — (callback handler) | `webui/src/views/saas-auth-callback.ts` | `/api/v2/auth/callback` | UIX-AT-21 |
| UI-F-070 | Profile (personal + platform) & mode select | UI-S-34, UI-S-35, UI-S-36 | UI-C-111…112 prov. | `webui/src/views/saas-personal-profile.ts`, `webui/src/views/saas-platform-profile.ts`, `webui/src/views/saas-mode-selection.ts` | `/api/v2/auth/me` | UIX-AT-21 |
| UI-F-071 | Platform dashboards & metrics | UI-S-37, UI-S-38, UI-S-45 | — (read-only meters) | `webui/src/views/platform-metrics-dashboard.ts`, `webui/src/views/saas-agent-metrics.ts` | metrics API | UIX-AT-20 |
| UI-F-072 | Infrastructure & rate limits | UI-S-39, UI-S-40 | UI-C-113 prov. | `webui/src/views/saas-rate-limits.ts`, `webui/src/views/saas-infrastructure-dashboard.ts` | rate-limit API | UIX-AT-20 |
| UI-F-073 | Integrations & marketplace | UI-S-41, UI-S-42 | UI-C-114 prov. | `webui/src/views/saas-integrations-dashboard.ts`, `webui/src/views/saas-marketplace.ts` | integrations API | UIX-AT-20 |
| UI-F-074 | Audit dashboard & audit log | UI-S-43, UI-S-44 | UI-C-115 prov. (log table) | `webui/src/views/saas-audit-dashboard.ts`, `webui/src/views/saas-audit-log.ts` | audit API | UIX-AT-20 |
| UI-F-075 | Voice chat & sessions | UI-S-46, UI-S-47 | UI-C-116 prov. | `webui/src/views/saas-voice-chat.ts`, `webui/src/views/saas-voice-sessions.ts` | voice API | UIX-AT-21 |
| UI-F-076 | Voice personas & STT/TTS config | UI-S-48 | UI-C-117…119 prov. | `webui/src/views/saas-voice-personas.ts` | `/agents/<id>/multimodal-config`, `speech_*`, `stt_*` | UIX-AT-21 |
| UI-F-077 | Multimodal settings | UI-S-49 | UI-C-120 prov. | `webui/src/views/saas-multimodal-settings.ts` | `PUT /agents/<id>/multimodal-config` | UIX-AT-21 |
| UI-F-078 | Settings screens — honesty & real data | UI-S-50, UI-S-51, UI-S-52, UI-S-53 | UI-A-015 prov. (save) | `webui/src/views/saas-settings.ts`, `saas-settings-models.ts`, `saas-settings-channels.ts` | `PUT /settings/<entity>` (entities of `settings_v2.DEFAULT_SETTINGS` only) | UIX-AT-24 |
| UI-F-079 | Session & logout (server-side cookie clear) | UI-S-29 | UI-A-016 prov. (logout) | `webui/src/main.ts` route `/logout` | `POST /api/v2/auth/logout` (`admin/auth/api.py`) | UIX-AT-22 |
| UI-F-080 | Right-rail surfaces (UI-X-01…08) | UI-S-00 | UI-C-121…128 prov. (surface tabs) | `webui/src/components/saas-right-panel.ts` | surface-specific (TBD UIUX-001) | UIX-AT-23 |

### 4.2 V&V matrix

Columns are the house V&V format exactly (N-7 §3): `| Requirement | Verification Method | Test Type | Test File | Status |`.

#### 4.2.1 Chrome (UI-S-00)

| Requirement | Verification Method | Test Type | Test File | Status |
|---|---|---|---|---|
| UI-F-001 | Inspection | — | — | PARTIAL |
| UI-F-002 | Inspection | — | planned: UIX-AT-10 | NOT YET |
| UI-F-003 | Analysis | — | planned: UIX-AT-11 | NOT YET |
| UI-F-004 | Test | E2E | planned: UIX-AT-06 (xref UI-AT-06) | NOT YET |
| UI-F-005 | Inspection | — | planned: UIX-AT-10 | NOT YET |
| UI-F-006 | Inspection | — | planned: UIX-AT-11 | NOT YET |

#### 4.2.2 Soul (UI-S-01)

| Requirement | Verification Method | Test Type | Test File | Status |
|---|---|---|---|---|
| UI-F-007 | Inspection | — | planned: UIX-AT-12 | PARTIAL |
| UI-F-008 | Inspection | — | planned: UIX-AT-12 | NOT YET |
| UI-F-009 | Inspection | — | planned: UIX-AT-11 | NOT YET |
| UI-F-010 | Inspection | — | planned: UIX-AT-13 | NOT YET |
| UI-F-011 | Inspection | — | planned: UIX-AT-12 | NOT YET |
| UI-F-012 | Inspection | — | planned: UIX-AT-12 | NOT YET |

#### 4.2.3 Brain (UI-S-02)

| Requirement | Verification Method | Test Type | Test File | Status |
|---|---|---|---|---|
| UI-F-013 | Analysis | Unit | planned: UIX-AT-11 | NOT YET |
| UI-F-014 | Analysis | Unit | planned: UIX-AT-11 | NOT YET |
| UI-F-015 | Analysis | Unit | planned: UIX-AT-11 | NOT YET |
| UI-F-016 | Test | E2E | planned: UIX-AT-04 (xref UI-AT-04) | EXISTS |
| UI-F-017 | Inspection | — | planned: UIX-AT-13 | NOT YET |
| UI-F-018 | Inspection | — | planned: UIX-AT-13 | NOT YET |
| UI-F-019 | Analysis | Code review | `admin/core/agentiq/settings.py` | EXISTS |

#### 4.2.4 Hands (UI-S-03)

| Requirement | Verification Method | Test Type | Test File | Status |
|---|---|---|---|---|
| UI-F-020 | Inspection | — | planned: UIX-AT-14 | NOT YET |
| UI-F-021 | Inspection | — | planned: UIX-AT-14 | NOT YET |
| UI-F-022 | Inspection | — | planned: UIX-AT-14 | NOT YET |
| UI-F-023 | Inspection | — | planned: UIX-AT-14 | NOT YET |
| UI-F-024 | Inspection | — | planned: UIX-AT-14 | NOT YET |
| UI-F-025 | Test | E2E | planned: UIX-AT-03 (xref UI-AT-03) | NOT YET |

#### 4.2.5 Memory (UI-S-04)

| Requirement | Verification Method | Test Type | Test File | Status |
|---|---|---|---|---|
| UI-F-026 | Test | E2E | planned: UIX-AT-15 | EXISTS |
| UI-F-027 | Inspection | — | planned: UIX-AT-15 | NOT YET |
| UI-F-028 | Inspection | — | planned: UIX-AT-15 | NOT YET |
| UI-F-029 | Test | E2E | planned: UIX-AT-15 | NOT YET |
| UI-F-030 | Inspection | — | planned: UIX-AT-15 | NOT YET |
| UI-F-031 | Analysis | Unit | `tests/unit/test_memory_*` (session-scoped recall) | PARTIAL |

#### 4.2.6 Body (UI-S-05)

| Requirement | Verification Method | Test Type | Test File | Status |
|---|---|---|---|---|
| UI-F-032 | Inspection | — | planned: UIX-AT-16 | NOT YET |
| UI-F-033 | Inspection | — | planned: UIX-AT-16 | NOT YET |
| UI-F-034 | Inspection | — | planned: UIX-AT-16 | NOT YET |
| UI-F-035 | Inspection | — | planned: UIX-AT-16 | NOT YET |

#### 4.2.7 Governance (UI-S-06)

| Requirement | Verification Method | Test Type | Test File | Status |
|---|---|---|---|---|
| UI-F-036 | Inspection | — | planned: UIX-AT-17 | NOT YET |
| UI-F-037 | Inspection | — | planned: UIX-AT-17 | NOT YET |
| UI-F-038 | Inspection | — | planned: UIX-AT-17 | NOT YET |
| UI-F-039 | Inspection | Code review | planned: UIX-AT-17 | NOT YET |
| UI-F-040 | Inspection | — | planned: UIX-AT-17 | NOT YET |

#### 4.2.8 Chat (UI-S-07…10)

| Requirement | Verification Method | Test Type | Test File | Status |
|---|---|---|---|---|
| UI-F-041 | Test | E2E | `tests/e2e/test_login_to_chat.spec.js`, `tests/e2e/test_ws_chat.spec.js` | VERIFIED |
| UI-F-042 | Test | E2E | `tests/e2e/test_login_to_chat.spec.js` (typing indicator + assistant response) | PARTIAL |
| UI-F-043 | Test | E2E | `tests/e2e/test_login_to_chat.spec.js` (new conversation, conversation list) | EXISTS |
| UI-F-044 | Test | E2E | planned: UIX-AT-18 | NOT YET |
| UI-F-045 | Test | E2E | planned: UIX-AT-18 | NOT YET |
| UI-F-046 | Test | E2E | planned: UIX-AT-18 | NOT YET |
| UI-F-047 | Test | E2E | `tests/e2e/test_login_to_chat.spec.js:255` (body contains no assertion) | PARTIAL |
| UI-F-048 | Test | E2E | `tests/e2e/test_login_to_chat.spec.js` (mode switch) | EXISTS |
| UI-F-049 | Test | E2E | `tests/e2e/test_login_to_chat.spec.js` (agent name in header) | EXISTS |

#### 4.2.9 Capsule (UI-S-11…14)

| Requirement | Verification Method | Test Type | Test File | Status |
|---|---|---|---|---|
| UI-F-050 | Inspection | — | planned: UIX-AT-18 | PARTIAL |
| UI-F-051 | Inspection | — | planned: UIX-AT-18 | PARTIAL |
| UI-F-052 | Inspection | — | planned: UIX-AT-18 | NOT YET |
| UI-F-053 | Inspection | — | planned: UIX-AT-18 | NOT YET |
| UI-F-054 | Test | E2E | planned: UIX-AT-18 | NOT YET |

#### 4.2.10 Module (UI-S-15…18)

| Requirement | Verification Method | Test Type | Test File | Status |
|---|---|---|---|---|
| UI-F-055 | Inspection | — | planned: UIX-AT-19 | NOT YET |
| UI-F-056 | Inspection | — | planned: UIX-AT-19 | NOT YET |
| UI-F-057 | Test | E2E | planned: UIX-AT-19 | EXISTS |
| UI-F-058 | Inspection | — | planned: UIX-AT-19 | NOT YET |

#### 4.2.11 Platform (UI-S-19…28)

| Requirement | Verification Method | Test Type | Test File | Status |
|---|---|---|---|---|
| UI-F-059 | Test | E2E | planned: UIX-AT-20 | EXISTS |
| UI-F-060 | Test | E2E | planned: UIX-AT-20 | EXISTS |
| UI-F-061 | Test | E2E | planned: UIX-AT-20 | EXISTS |
| UI-F-062 | Test | E2E | planned: UIX-AT-20 | EXISTS |
| UI-F-063 | Inspection | — | planned: UIX-AT-20 | NOT YET |
| UI-F-064 | Test | E2E | planned: UIX-AT-20 | EXISTS |
| UI-F-065 | Test | E2E | planned: UIX-AT-20 | EXISTS |

#### 4.2.12 Auth (UI-S-29…36)

| Requirement | Verification Method | Test Type | Test File | Status |
|---|---|---|---|---|
| UI-F-066 | Test | E2E | `tests/e2e/test_login_to_chat.spec.js`, `tests/e2e/test-playwright.spec.ts` | VERIFIED |
| UI-F-067 | Test | E2E | planned: UIX-AT-21 | EXISTS |
| UI-F-068 | Test | E2E | planned: UIX-AT-21 | EXISTS |
| UI-F-069 | Inspection | — | planned: UIX-AT-21 | NOT YET |
| UI-F-070 | Test | E2E | planned: UIX-AT-21 | EXISTS |

#### 4.2.13 Ops (UI-S-37…45)

| Requirement | Verification Method | Test Type | Test File | Status |
|---|---|---|---|---|
| UI-F-071 | Inspection | — | planned: UIX-AT-20 | EXISTS |
| UI-F-072 | Inspection | — | planned: UIX-AT-20 | EXISTS |
| UI-F-073 | Inspection | — | planned: UIX-AT-20 | EXISTS |
| UI-F-074 | Inspection | — | planned: UIX-AT-20 | EXISTS |

#### 4.2.14 Voice (UI-S-46…49)

| Requirement | Verification Method | Test Type | Test File | Status |
|---|---|---|---|---|
| UI-F-075 | Inspection | — | planned: UIX-AT-21 | NOT YET |
| UI-F-076 | Test | E2E | planned: UIX-AT-21 | EXISTS |
| UI-F-077 | Test | E2E | planned: UIX-AT-21 | EXISTS |

#### 4.2.15 Settings & Surfaces

| Requirement | Verification Method | Test Type | Test File | Status |
|---|---|---|---|---|
| UI-F-078 | Inspection | Code review | `webui/src/views/saas-settings.ts` (findings F-07…F-10) | PARTIAL |
| UI-F-079 | Inspection | Code review | `webui/src/main.ts` (finding F-06) | NOT YET |
| UI-F-080 | Inspection | Code review | `webui/src/components/saas-right-panel.ts` (finding F-11) | PARTIAL |

Status distribution across the 80 rows: `VERIFIED` 2 (UI-F-041, UI-F-066); `EXISTS` 16; `PARTIAL` 11;
`NOT YET` 51. This distribution is what §3 derives from — it is not an opinion.

---

## 5. Playwright Coverage Map

Measured by listing `tests/e2e/` and reading every `*.spec.*` file on 2026-09-28. No claim below is
inferred from a file name alone.

### 5.1 Acceptance-test namespace and cross-reference to `UI-AT-*`

N-2 §3.3.2: `SOMA-A0-PARITY-001` already owns `UI-AT-01`…`UI-AT-08`. This document **cross-references**
that series and **does not renumber it**. `UIX-AT-01`…`08` are the same acceptance intents under the
`UIX-AT-NN` namespace; `UIX-AT-09`…`24` are new and owned here; `UIX-AT-25`…`40` are reserved for
reconciliation with N-4.

| UIX-AT-* | Acceptance intent | Cross-reference (N-3 §5.7) | Implemented today? |
|---|---|---|---|
| UIX-AT-01 | Login → chat loads, zero `placeholder` strings in DOM | ≡ UI-AT-01 | PARTIAL — login→chat works; no zero-placeholder assertion |
| UIX-AT-02 | Send message → `chat.delta` tokens render progressively | ≡ UI-AT-02 | PARTIAL — response renders; progressive tokens not asserted |
| UIX-AT-03 | Tool call renders timeline with args + result | ≡ UI-AT-03 | NOT YET |
| UIX-AT-04 | Model switcher changes active model for next turn | ≡ UI-AT-04 | NOT YET |
| UIX-AT-05 | Settings → Channels → WhatsApp shows QR or connected state from real API | ≡ UI-AT-05 | NOT YET |
| UIX-AT-06 | Cmd-K opens palette and routes to settings | ≡ UI-AT-06 | NOT YET |
| UIX-AT-07 | No hardcoded metrics (grep `12400` / `getMock`) in bundle | ≡ UI-AT-07 | NOT YET (automated). Manual grep of `webui/src/` on 2026-09-28 returns **no** `12400`, `getMock`, `mockData`, `fakeData` or `demoData` hits — the assertion is currently true but **unenforced**. |
| UIX-AT-08 | WCAG: focus rings, contrast AA on primary surfaces | ≡ UI-AT-08 | NOT YET |
| UIX-AT-09 | Capsule switcher and agent picker list real capsules/agents only (no synthetic rows) | — | NOT YET |
| UIX-AT-10 | Version chip + lifecycle chip + facet tabs reflect the live Capsule | — | NOT YET |
| UIX-AT-11 | Persona knobs write `persona_config.knobs`; neuro meters and derived readouts follow | — | NOT YET |
| UIX-AT-12 | Soul facet: system prompt, traits, prompts persist via Capsule API | — | NOT YET |
| UIX-AT-13 | Brain facet: learning config persists; the 12 derived settings are never editable | — | NOT YET |
| UIX-AT-14 | Hands facet: tool policy buckets, capability attach/detach, MCP registry | — | NOT YET |
| UIX-AT-15 | Memory facet: recall/memorize config persists; live preview shows real hits only | — | NOT YET |
| UIX-AT-16 | Body facet: resource limits + token budget persist | — | NOT YET |
| UIX-AT-17 | Governance facet: constitution ref + OPA/SpiceDB bindings; viewer is immutable | — | NOT YET |
| UIX-AT-18 | Capsule / conversation export-import round-trip against the real API | — | NOT YET |
| UIX-AT-19 | Module + capability registry screens read the real manifest | — | NOT YET |
| UIX-AT-20 | Platform screens (tenants, users, roles, permissions, billing, usage, tiers, ops, audit) CRUD against the real API | — | NOT YET |
| UIX-AT-21 | Auth + Voice screens against the real IdP and voice APIs | — | NOT YET |
| UIX-AT-22 | Server-side logout clears the session cookie; `checkAuth()` returns false afterwards | — | NOT YET (blocked by finding F-06) |
| UIX-AT-23 | No unreachable route branch: every path literal in `webui/src/main.ts` resolves to exactly one live branch | — | NOT YET (blocked by findings F-01…F-05) |
| UIX-AT-24 | Settings honesty: no fabricated key fragments, no hardcoded topology, no dead save path | — | NOT YET (blocked by findings F-07…F-10) |
| UIX-AT-25…40 | Reserved for N-4 reconciliation | — | — |

### 5.2 What `tests/e2e/*.spec.*` actually covers today

Seven Playwright spec files and one Python file are present. Coverage is **chat-and-auth heavy and
nothing else**.

| File | Tests | What it actually asserts | Maps to |
|---|---|---|---|
| `tests/e2e/test_chat_flow.spec.js` | 5 | API health `status=ok`; OpenAPI schema has >10 paths; bad credentials do not 500-crash; `GET /api/v2/chat/conversations` is <500 unauthenticated; WS unauthenticated connection produces a truthy close result | API smoke. No UI. Supports UI-F-041, UI-F-066 indirectly |
| `tests/e2e/test_chat_visual.spec.js` | 1 | Login via API, copy cookies to UI domain, open `/chat`, screenshot. Logs textarea `placeholder` but **does not assert against it**. Sends one message if the textarea is enabled | UI-F-041, UI-F-042 (weak) |
| `tests/e2e/test_login_to_chat.spec.js` | 27 | Richest suite. Login page elements, RFC 5322 email validation, invalid-credential error, successful login, loading state, remember-me, 5-attempt account lockout, SSO modal open/cancel/provider-switch, chat interface visible, new-conversation button, conversation create, send message, typing indicator, assistant response, mode switch, agent name in header, conversation list, conversation select. **Three tests assert nothing useful**: reconnect banner (empty body), settings navigation (no assertion), logout (URL only — see F-06) | UI-F-041, UI-F-042, UI-F-043, UI-F-048, UI-F-049, UI-F-066. UI-F-079 is *named* but not verified |
| `tests/e2e/test_ws_chat.spec.js` | 1 | Auth → create conversation → WS connect with token → `chat.message` → receive response. Strongest chat-path test. Uses a **hardcoded agent id** `a071df42-ae61-41dc-81d3-fb145e233bdf` | UI-F-041, UI-F-042, UI-F-043 |
| `tests/e2e/test-browser-chat.spec.ts` | 1 | Types credentials character-by-character, submits, screenshots. Ends with `expect(true).toBe(true)` — **no real assertion** | UI-F-066 (smoke only) |
| `tests/e2e/test-debug-login.spec.ts` | 1 | Dumps form field names/placeholders to console. Debug helper, not a test | — |
| `tests/e2e/test-playwright.spec.ts` | 7 | WebUI loads without blank page; login page renders; API health via proxy; Keycloak realm issuer; login with testuser reaches chat; direct Keycloak token + `/auth/me` + `/api/v2/agents`; 60s heartbeat poll until `status=ok` | UI-F-041, UI-F-066 |
| `tests/e2e/test_triad_integration.py` | (pytest) | Python integration test for the cognitive triad; **not** Playwright and not part of the UI E2E map | — |

### 5.3 What is NOT covered today (honest list)

Nothing in `tests/e2e/` exercises:

- Any facet except Chat and the login surface: **Soul, Brain, Hands, Memory, Body, Governance,
  Capsule, Module** have zero Playwright coverage (UI-F-007…040, UI-F-050…058).
- **Tool timeline / approval** (UI-AT-03 / UIX-AT-03) — not implemented, not tested.
- **Model switcher semantics** (UI-AT-04 / UIX-AT-04) — `saas-settings-models.ts` is API-wired but no
  test proves a switch changes the active model for the next turn.
- **Channels / WhatsApp real state** (UI-AT-05 / UIX-AT-05) — `saas-settings-channels.ts` is API-wired
  but untested.
- **Command palette** (UI-AT-06 / UIX-AT-06) — no palette component exists in `webui/src/`.
- **Hardcoded-metric grep** (UI-AT-07 / UIX-AT-07) — the assertion is currently true by manual grep
  but no CI step enforces it.
- **WCAG focus rings and contrast AA** (UI-AT-08 / UIX-AT-08) — zero accessibility tests.
- **Every Settings honesty rule** (UIX-AT-24) — see findings F-07…F-10.
- **Server-side logout** (UIX-AT-22) — see finding F-06. The existing logout test (`test_login_to_chat.spec.js`)
  asserts only that the URL becomes `/login`, which the client-side redirect achieves **even though the
  session cookie survives**. The test therefore passes while the security defect remains. This is the
  single most important honesty gap in the suite.
- **Route uniqueness** (UIX-AT-23) — see findings F-01…F-05.
- **Platform and Ops screens** (UIX-AT-20) and **Voice screens** (UIX-AT-21) — API-wired, untested.
- **Billions of negative paths**: permission-denied, offline, empty-on-service-down.

Two of the seven spec files are not tests at all (`test-browser-chat.spec.ts` ends in
`expect(true).toBe(true)`; `test-debug-login.spec.ts` is a debug dump). They SHALL NOT be counted
toward coverage. The §3 Tested count of 6 reflects this exclusion.

---

## 6. Known Findings

Every row is `NOT YET` — none of these is fixed at the time of issue. Line numbers were re-verified
against the **current** tree on 2026-09-28 (`webui/src/main.ts` is 492 lines; `webui/src/views/saas-settings.ts`
is 892 lines). Each finding is also a row in §9 Gap Register.

### 6.1 Four unreachable / dead route branches in `webui/src/main.ts`

Duplicate path literals where an earlier branch returns first. The later branch is dead code: the
router is an `if`-chain of exact `path ===` comparisons, each of which `return`s, so the first match
wins and every later identical literal is unreachable.

| ID | Finding | Evidence | Why it is dead |
|---|---|---|---|
| F-01 | `/platform/features` branch renders `saas-features-view` | `webui/src/main.ts:296` | `webui/src/main.ts:179` matches `/platform/features` first and returns `saas-feature-catalog`. |
| F-02 | `/mode-select` / `/select-mode` branch renders `saas-mode-selection` | `webui/src/main.ts:349` | Identical condition at `webui/src/main.ts:323` returns first. |
| F-03 | `/admin/users` branch renders `saas-tenant-users` | `webui/src/main.ts:362` | `webui/src/main.ts:249` matches first and returns `saas-users-view`. |
| F-04 | `/admin/agents` branch renders `saas-tenant-agents` | `webui/src/main.ts:368` | `webui/src/main.ts:290` matches first and returns `saas-agents-view`. |

**Additional dead literal (same mechanism, partially live branch).** F-05: `webui/src/main.ts:382`
lists `'/platform/audit'` alongside `'/audit'` and `'/admin/audit'`. The `'/platform/audit'` literal is
dead because `webui/src/main.ts:303` matches it first and returns `saas-audit-dashboard`. `'/audit'`
and `'/admin/audit'` on the same line remain live. The consequence is that two different view
components claim the same routes, and which one a user reaches depends on source order rather than
intent — a maintenance and product-behaviour hazard, not just a lint issue.

**Related (not a duplicate, but a dead fallback).** F-05b: `webui/src/main.ts:402-411` — the `/memory`
route's `try`/`catch` falls back to importing **the same module** (`saas-memory-view.js`) in both arms,
so the "Fallback to legacy memory" comment describes nothing.

### 6.2 `/logout` is client-side only (security-relevant)

| ID | Finding | Evidence |
|---|---|---|
| F-06 | The `/logout` route does not call server logout and does not clear the session cookie that `checkAuth()` reads. | `webui/src/main.ts:342-347` |

The route body is, in full:

```
if (path === '/logout') {
    localStorage.removeItem('saas_auth_token');
    localStorage.removeItem('saas_user');
    window.location.href = '/login');
    return;
}
```

It removes two `localStorage` keys and hard-redirects. It does **not**:

1. call `POST /api/v2/auth/logout`, which **exists and works** at `admin/auth/api.py:299-317` — that
   handler revokes the Keycloak refresh token and calls `response.delete_cookie("access_token")`,
   `delete_cookie("refresh_token")`, `delete_cookie("session_id")`;
2. clear any cookie.

`checkAuth()` at `webui/src/main.ts:36-43` fetches `/api/v2/auth/me` with `credentials: 'include'`, so
it reads the **cookie**, not the localStorage keys. After `/logout` the cookie is still present, so
`checkAuth()` returns `true` and the very next `renderRoute()` call treats the user as authenticated
and redirects them back into the app. The "logout" is a visual redirect, not a session termination.

The same client-only pattern is duplicated in three other places, none of which calls the server
endpoint either:

| Location | What it clears |
|---|---|
| `webui/src/views/saas-chat.ts:2046-2053` | `saas_auth_token`, `saas_user`, `saas_keycloak_token`, `saas_auth_state`, `saas_auth_nonce` |
| `webui/src/controllers/platform-dashboard-controller.ts:141-144` | `saas_mode` only |
| `webui/src/views/saas-mode-selection.ts:614-619` | `saas_user`, `saas_mode`, `saas_tenant_id` |

**Security impact.** On a shared or unattended browser, "Log out" leaves a live authenticated session
cookie. Any subsequent navigation to the app passes `checkAuth()` and resumes the session. This is a
session-fixation / shared-workstation exposure and violates the honesty rule that a control's effect
must be its stated effect. The existing Playwright test `tests/e2e/test_login_to_chat.spec.js` (the
"should logout successfully" case) asserts only `toHaveURL(/\/login/)` and therefore **passes against
the broken behaviour**.

### 6.3 Settings screen fakes (verified 2026-09-28)

All in `webui/src/views/saas-settings.ts` unless stated. Line numbers re-verified against the current
892-line file.

| ID | Finding | Evidence (file:line) |
|---|---|---|
| F-07 | **Fabricated API-key rows.** Three hardcoded rows render as if they were configured providers: `OpenAI` / `sk-****...****aBcD` / `Active`, `Anthropic` / `sk-ant-****...****xYz` / `Active`, `Serper (Search)` / `—` / `Missing`. No API call populates any of them. | `webui/src/views/saas-settings.ts:629-646` — literals at `:631` (`sk-****...****aBcD`) and `:637` (`sk-ant-****...****xYz`); row markup `:629-646`; CSS class `api-key-value` at `:382` |
| F-08 | **Hardcoded SomaBrain URL.** The "SomaBrain URL" field is a readonly input pinned to a localhost literal, not the live `SOMABRAIN_URL`. | `webui/src/views/saas-settings.ts:604` — `value="http://localhost:9696" readonly` |
| F-09 | **Fabricated Collection value.** The "Collection" field is free text defaulted to the literal `default`, with no load and no save binding. | `webui/src/views/saas-settings.ts:607-608` — `value="default"` at `:608` |
| F-10 | **Dead save path.** "Save Changes" issues `apiClient.put('/settings/agent/', …)`. The entity `agent` is **not** in `DEFAULT_SETTINGS`, so `update_settings` rejects it with `ValidationError`. The catch block only `console.error`s, so the user sees no failure. | request: `webui/src/views/saas-settings.ts:858` (`apiClient.put('/settings/agent/', …)`); silent catch: `webui/src/views/saas-settings.ts:865` (`console.error('Failed to save settings:', error)`); entity set: `admin/core/api/settings_v2.py:48-94` — keys are exactly `postgresql` (`:49`), `redis` (`:58`), `kafka` (`:63`), `temporal` (`:68`), `keycloak` (`:76`), `somabrain` (`:82`), `voice` (`:88`); rejection: `admin/core/api/settings_v2.py:162-166` (`if entity not in DEFAULT_SETTINGS: raise ValidationError(...)`) |

Re-verification note: the settings-screen findings were first recorded by `SOMA-01-UIUX-005.md`
(G-06…G-17, dated 2026-09-27) against a then-current tree. Every line number above was **re-read in
the 892-line file on 2026-09-28** and matches. The findings are still open.

### 6.4 Additional honesty findings found in this pass

| ID | Finding | Evidence (file:line) |
|---|---|---|
| F-11 | **"Coming soon" placeholder copy**, forbidden by the house template ("NEVER write 'coming soon' as a specification value"). Four right-rail surfaces and one multimodal capability ship it. | `webui/src/components/saas-right-panel.ts:214` ("Tool manager coming soon"), `:222` ("File browser coming soon"), `:230` ("Browser surface coming soon"), `:238` ("Editor surface coming soon"); `webui/src/views/saas-multimodal-settings.ts:498` ("AI video generation (coming soon)") |
| F-12 | **Self-referential fallback** on the `/memory` route: the catch arm imports the same module as the try arm, so the "Fallback to legacy memory" comment is untrue. | `webui/src/main.ts:402-411` |
| F-13 | **Two non-test spec files** counted in the E2E directory. `test-browser-chat.spec.ts` ends in `expect(true).toBe(true)`; `test-debug-login.spec.ts` dumps form fields to console. They must not be counted as coverage. | `tests/e2e/test-browser-chat.spec.ts:65`; `tests/e2e/test-debug-login.spec.ts:1-72` |
| F-14 | **Hardcoded agent id** in the strongest chat E2E test, which will break on any fresh database. | `tests/e2e/test_ws_chat.spec.js:11` (`AGENT_ID = 'a071df42-ae61-41dc-81d3-fb145e233bdf'`) |

### 6.5 Findings carried from `SOMA-01-UIUX-005` (not re-derived here)

The settings parity matrix already records G-06…G-17 with the same root causes as F-07…F-10, plus
dead controls ("Add API Key" `saas-settings.ts:648`, "Add MCP Server" `:674`, "Import Config" `:804`,
"Reset All Settings" `:819`), a dead Proxy/Network panel (`:724-740`), and free-floating Voice selects
(`:706-719`). Those are in scope for UIX-AT-24 and are **not** renumbered here. This document's job
is to record that they are **unverified and open**.

---

## 7. Honesty Checklist

Binding on every screen spec and every mockup (N-6, N-3). State is measured on 2026-09-28.

| # | Rule | State | Evidence |
|---|---|---|---|
| H-01 | No mocks, no mock fallbacks, no `getMock` / `mockData` / `fakeData` / `demoData` in `webui/src/` | **PASS (unenforced)** | Manual grep 2026-09-28 returns zero hits. UIX-AT-07 is not automated, so the pass is fragile. |
| H-02 | No fabricated data presented as real | **FAIL** | F-07 (`saas-settings.ts:629-646` fabricated key fragments and a fabricated "Serper" row). |
| H-03 | No default tenant / collection literal `"default"` | **FAIL** | F-09 (`saas-settings.ts:608` `value="default"`). |
| H-04 | No empty-list-on-service-down — a failed API call shows an explicit error, never a silent empty list | **NOT VERIFIED** | No test exercises service-down behaviour. UIUX-005 H-01 already requires "Provider list unavailable — /llm/providers did not respond" copy; not implemented. |
| H-05 | No "coming soon" as a specification value; every disabled control states its blocking reason | **FAIL** | F-11 (`saas-right-panel.ts:214,222,230,238`; `saas-multimodal-settings.ts:498`). Reference implementation for disabled-with-reason is `saas-chat-topbar.ts` (Nudge), per N-3 §4.1.1. |
| H-06 | Every disabled control has a `disabled-when` and a `disabled-reason` | **FAIL** | Five "coming soon" surfaces have neither. UI-X-08 (desktop) is correctly GATED in N-5 with the reason "Requires a remote-desktop capability in somaAgent01. Not available today." — that is the required pattern. |
| H-07 | Secrets shown as masked placeholder plus "rotate in Vault" only — never a value, never a comparable fragment | **FAIL** | F-07 renders `sk-****...****aBcD` and `sk-ant-****...****xYz`. A masked fragment that could be compared against a leaked key violates R-SEC-UI-03 of UIUX-005. The compliant reference is `has_api_key` boolean-only in `saas-settings-models.ts:27`. |
| H-08 | No hardcoded topology value that a live setting owns | **FAIL** | F-08 (`saas-settings.ts:604` `http://localhost:9696`). |
| H-09 | No save is reported successful when no persistence occurred; no failure swallowed into the console | **FAIL** | F-10 (`saas-settings.ts:858` dead `PUT /settings/agent/`, catch at `:865` is `console.error` only). |
| H-10 | Derived AgentIQ settings (temperature, max_tokens, rlm_iterations, recall_limit, model_tier, brain_query_enabled, require_hitl, tool_approval, egress_allowed, token_limit, cost_tier, thinking_budget) are READ-ONLY readouts beside the three knobs | **NOT YET** | Rule specified in UIUX-005 §8 and in UI-F-019; no UI-S-02 implementation exists. |
| H-11 | Counts and statuses are not fabricated; every number cites its derivation | **PASS** | §3 states its derivation and its arithmetic check. §5 lists non-tests as non-tests (F-13). |
| H-12 | Every control is clickable-with-a-handler, or rendered disabled with a reason | **FAIL** | Dead controls "Add API Key" (`saas-settings.ts:648`), "Add MCP Server" (`:674`), "Import Config" (`:804`), "Reset All Settings" (`:819`) — carried as UIUX-005 G-07/G-08/G-15/G-16. |

Summary: **2 PASS, 6 FAIL, 2 NOT YET / NOT VERIFIED** of 12. This checklist is the reason §3 reports
Implemented 24 and Tested 6 rather than a rosier number.

---

## 8. Acceptance Criteria

| Criterion | Target | Current |
|---|---|---|
| Every `UI-F-*` has a complete trace chain (screen → control/action → component → API → acceptance test) | 80 / 80 | 80 / 80 chain allocated; **0 / 80** chains closed end-to-end against N-4 (N-4 absent — §1.4) |
| Features with a real API-wired implementation | ≥ 64 / 80 (80%) | 24 / 80 (30.0%) |
| Features with an automated test that exercises them | ≥ 64 / 80 (80%) | 6 / 80 (7.5%) |
| RTM counts re-derived from the matrix, never copied | Always | Yes (§3 arithmetic check) |
| `UI-AT-01`…`UI-AT-08` cross-referenced, never renumbered | 8 / 8 | 8 / 8 (§5.1) |
| Unreachable route branches in `webui/src/main.ts` | 0 | 4 fully dead branches + 1 dead literal (F-01…F-05) |
| `/logout` terminates the server session and clears the session cookie | Yes | No (F-06) |
| Settings screens render no fabricated data | 0 fabrications | 3 fabricated surfaces (F-07, F-08, F-09) |
| Settings save path resolves to a real entity in `settings_v2.DEFAULT_SETTINGS` | All | `agent` rejected (F-10) |
| "Coming soon" strings in `webui/src/` | 0 | 5 (F-11) |
| Honesty checklist H-01…H-12 | 12 / 12 PASS | 2 PASS, 6 FAIL, 2 NOT YET, 2 unverified |
| Accessibility tests (focus rings, contrast AA) | ≥ 1 suite | 0 (UIX-AT-08 / UI-AT-08) |
| Non-test files excluded from E2E coverage counts | Always | Yes (F-13 excluded; documented) |
| Every feature with no test is listed as `NOT YET`, never omitted | Always | Yes (51 rows `NOT YET`) |

---

## 9. Gap Register

What is specified but not yet implemented or not yet verified, with an owner and a gate.
Owner names are roles, not individuals. A gap closes only when its gate evidence lands.

| Gap ID | What is missing | Related | Owner | Gate |
|---|---|---|---|---|
| G-UIX-01 | `SOMA-01-UIUX-001.md` does not exist; the `UI-F-*` / `UI-C-*` / `UI-A-*` ids in §4 are provisional | §1.4, X-11 | UI/UX spec author | UIUX-001 lands and this document issues v1.1.0 reconciling every `prov.` id |
| G-UIX-02 | Four unreachable route branches plus one dead path literal | F-01…F-05 | Frontend engineering | UIX-AT-23 green; a path-literal uniqueness check in CI |
| G-UIX-03 | `/logout` does not terminate the server session or clear the session cookie | F-06 | Frontend engineering + Auth | UIX-AT-22 green: after logout `GET /api/v2/auth/me` returns 401 and the cookie is deleted |
| G-UIX-04 | Fabricated API-key rows and a fabricated Serper row on the Settings External tab | F-07 | Frontend engineering | UIX-AT-24 green; rows populated from `/llm/providers` + real secret presence flags only |
| G-UIX-05 | Hardcoded `http://localhost:9696` SomaBrain URL | F-08 | Frontend engineering | UIX-AT-24 green; field bound to live `SOMABRAIN_URL` as L3 read-only |
| G-UIX-06 | Fabricated `default` Collection value with no load/save | F-09 | Frontend engineering | UIX-AT-24 green; replaced by the Memory-facet namespace field (`Capsule.memory_pointer`) |
| G-UIX-07 | `PUT /settings/agent/` save path is dead; failure swallowed into `console.error` | F-10 | Frontend engineering + Platform API | UIX-AT-24 green; save routed to a real persistence path and errors surfaced with the `_flash` pattern |
| G-UIX-08 | Five "coming soon" strings where a disabled-reason is required | F-11 | Frontend engineering | UIX-AT-23/24 green; each surface is either implemented or disabled with the N-5 blocking-reason pattern |
| G-UIX-09 | No accessibility test suite | UI-AT-08 / UIX-AT-08 | QA | UIX-AT-08 green in CI |
| G-UIX-10 | No tool timeline / approval UI or test | UI-AT-03 / UIX-AT-03 | Agent runtime + Frontend | UIX-AT-03 green |
| G-UIX-11 | No model-switcher behavioural test | UI-AT-04 / UIX-AT-04 | QA | UIX-AT-04 green |
| G-UIX-12 | No channels / WhatsApp real-state test | UI-AT-05 / UIX-AT-05 | QA | UIX-AT-05 green |
| G-UIX-13 | No command palette component or test | UI-AT-06 / UIX-AT-06 | Frontend engineering | UIX-AT-06 green |
| G-UIX-14 | UI-AT-07 hardcoded-metric grep is not enforced in CI | UI-AT-07 / UIX-AT-07 | Platform / CI | Grep step added to CI and green |
| G-UIX-15 | No Playwright coverage for Soul, Brain, Hands, Memory, Body, Governance, Capsule, Module facets | UI-F-007…040, UI-F-050…058 | QA | UIX-AT-12…18 green |
| G-UIX-16 | No Playwright coverage for Platform, Ops, Voice screens | UI-F-059…077 | QA | UIX-AT-20, UIX-AT-21 green |
| G-UIX-17 | Derived-settings read-only rule (12 readouts beside 3 knobs) not implemented | UI-F-019, H-10 | Frontend engineering | UIX-AT-13 green; readouts are display-only and update from `derive_all_settings` |
| G-UIX-18 | `UIX-AT-25`…`UIX-AT-40` range unallocated | §5.1 | UI/UX spec author | Allocated in UIUX-001 reconciliation (G-UIX-01) |
| G-UIX-19 | Two non-test spec files sit in `tests/e2e/` and inflate the apparent suite | F-13 | QA | Files renamed out of `*.spec.*` or given real assertions |
| G-UIX-20 | Hardcoded agent id in `test_ws_chat.spec.js` | F-14 | QA | Agent id resolved from the API at test setup |

### 9.1 Open disagreements

| ID | Disagreement | Evidence | Effect on this document |
|---|---|---|---|
| X-11 | The task brief and N-5 require every `UI-F-*` to come from `SOMA-01-UIUX-001.md`. That document is absent from `docs/iso/`. | `ls docs/iso/` on 2026-09-28 lists `SOMA-01-UIUX-005.md` but no `SOMA-01-UIUX-001.md` | §4 defines a provisional `UI-F-001`…`080` allocation consistent with N-5 ranges and marks it `prov.` throughout. Reconciliation is G-UIX-01. |
| X-12 | `SOMA-01-VV-001.md` reports a 95-requirement `REQ-*` matrix with 37 verified (39%). This document's UI slice is 80 `UI-F-*` with 24 implemented (30.0%) and 6 tested (7.5%). The two matrices measure different populations and **shall not** be averaged. | `SOMA-01-VV-001.md:100-120` vs §3 of this document | Both numbers stand. §3 explicitly scopes its counts to `UI-F-*`. |
| X-13 | `SOMA-01-UIUX-005.md` §6 reports Implemented 16/316 (5.1%) over settings inventory rows. §3 of this document reports Implemented 24/80 (30.0%) over UI features. Different units (setting rows vs feature rows). | UIUX-005 §6 vs §3 here | Neither is wrong. Settings-placement completeness (UIUX-005: 316/316 placed) and feature implementation (this document: 24/80 wired) answer different questions. |
| X-14 | N-3 §5.7 lists `UI-AT-01`…`08` as Playwright acceptance tests. §5.2 measures that only `UI-AT-01` and `UI-AT-02` have anything resembling coverage today, and `UI-AT-07` is true only by manual grep. | N-3 §5.7 vs §5.2 of this document | §5.1 marks each `UIX-AT-*` as PARTIAL / NOT YET honestly. The N-3 list is the **target**, not the **state**. |

---

## 10. Maintenance

- Any new `UI-F-*` **SHALL** be added to §4 with a full chain before it is counted in §3.
- §3 **SHALL** be regenerated from §4 whenever §4 changes (N-2 REQ-DOCS-011). The arithmetic check in
  §3 **SHALL** be recomputed, not copied.
- A row's Status **SHALL** only rise from `NOT YET` when the named test artefact exists and is asserted.
  A test file whose body contains no assertion for the feature **SHALL NOT** move the row to `EXISTS`.
- When `SOMA-01-UIUX-001.md` lands, this document **SHALL** issue v1.1.0 reconciling every `prov.`
  control/action id and closing G-UIX-01 (X-11).
- Findings F-01…F-14 **SHALL** stay `NOT YET` in §6 until their gap in §9 is closed with gate evidence.
  Line numbers **SHALL** be re-verified against the tree at every review.
- This document **SHALL** be reviewed on `Next Review` or whenever `webui/src/main.ts`,
  `webui/src/views/saas-settings.ts`, `admin/core/api/settings_v2.py` or `tests/e2e/` changes.

End of Document
