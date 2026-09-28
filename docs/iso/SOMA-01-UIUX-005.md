# SOMA-01-UIUX-005 — User Interface — Settings Parity Matrix

## Document Control

| Field | Value |
|---|---|
| Document Title | User Interface — Settings Parity Matrix |
| Document Identifier | SOMA-01-UIUX-005 |
| Version | 1.0.0 |
| Date | 2026-09-27 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-27 |
| Related | `SOMA-SETTINGS-MODEL-001.md`, `SOMA-01-DOCS-001.md`, `docs/project/SOMA-UIUX-PARITY-PLAN-002.md`, `SOMA-A0-PARITY-001.md` |
| Source of truth | This document for settings→screen placement; `SOMA-SETTINGS-MODEL-001.md` §9 for the settings inventory; code paths cited per row |
| Audience | UI/UX contributors, product engineering, any agent acting on somaAgent01 |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-09-27 | SomaTech Engineering | Initial issue. Settings→Screen placement matrix for all C1–C10 inventory rows, coverage RTM, gaps register, derived-settings rule, drift→UI disposition, secrets rule, honesty notes. |

## Normative References

| ID | Reference | Role |
|---|---|---|
| N-1 | `SOMA-SETTINGS-MODEL-001.md` | Settings inventory (§9), ownership layers (§4), resolution order (§5), drift register (§10) |
| N-2 | `SOMA-01-DOCS-001.md` | Document control, identifier scheme (`UI-S-<NN>`), RTM house format |
| N-3 | `docs/project/SOMA-UIUX-PARITY-PLAN-002.md` §3 | Capsule-first information architecture — six facets, rail, settings scopes |
| N-4 | `services/capsule_export.py` | Facet export definitions (Soul/Brain/Hands/Memory/Body/Governance) |
| N-5 | `admin/core/helpers/capsule_settings.py` | `CATEGORY_*`, `KEY_CATEGORY`, `resolve_setting`, `save_capsule_setting` |
| N-6 | `admin/core/agentiq/settings.py`, `admin/core/agentiq/derivation.py` | 3 knobs → 12 derived settings |
| N-7 | `SOMA-A0-PARITY-001.md` | Error-honesty rules; disabled-with-reason |
| N-8 | ISO 9001:2015 clause 7.5 | Control of documented information |

---

## 1. Purpose and Scope

### 1.1 Purpose

This document proves that **every Soma setting has a home in the Agent Soma UI/UX**. For each of the
inventory rows in `SOMA-SETTINGS-MODEL-001.md` §9 it names:

1. the **screen** (`UI-S-<nn>`) the setting lives on,
2. the **facet** (Soul / Brain / Hands / Memory / Body / Governance / Chat / Module / Capability / Instance / Constitution / Settings / Platform),
3. the **settings scope** (Agent / External / Developer / Backup / Platform / Module-injected),
4. the **control type** that renders it,
5. the **edit authority** (L1 Django / L2 Agent / L3 Env / L4 Vault) and therefore whether the control is editable, read-only, or gated,
6. a **disabled-reason** whenever the control is not user-editable.

The string "coming soon" SHALL NOT appear as a specification value (N-2 REQ-DOCS-015). Where a screen
does not exist yet the row is marked `NEW` and the screen is proposed in §4.

### 1.2 Scope

All 316 settings inventory rows of `SOMA-SETTINGS-MODEL-001.md` §9.1–§9.10 (test-only keys §9.11 are
out of scope and are not product settings). Screens in `webui/src/views/saas-settings*.ts`,
`webui/src/views/saas-multimodal-settings.ts`, `webui/src/components/settings-form.ts` and the
capsule-first screens named in N-3 §3.

### 1.3 Out of Scope

- Concrete production values (deployment configuration).
- API request/response schemas that are not persisted settings.
- Secret values (N-1 §8; see §10 of this document).
- Implementation of the screens — this is a design/specification document only.

---

## 2. Normative Requirements

Requirements use **SHALL** / **SHALL NOT** per N-1 §3 convention.

| ID | Requirement | Priority | Source | Verification |
|---|---|---|---|---|
| REQ-UIXS-001 | Every settings inventory row SHALL have exactly one primary screen (`UI-S-<nn>`) in §5. A row without a screen SHALL be listed in §7 Gaps with a proposed home. | Must | N-1 §9 | Inspection of §5 |
| REQ-UIXS-002 | A control whose owning layer is L3 Env or L4 Vault SHALL be rendered read-only or secret-masked with a stated disabled-reason. The value SHALL NOT be editable in the UI. | Must | N-1 §4, §8 | Inspection of §5 |
| REQ-UIXS-003 | The 12 AgentIQ derived settings SHALL be shown as read-only derived readouts next to their 3 knobs and SHALL NOT be independently editable. | Must | N-1 §7.2, N-6 | Inspection of §8 |
| REQ-UIXS-004 | Vault-owned values SHALL render as a masked placeholder plus a "rotate in Vault" affordance. The value SHALL NEVER be rendered. | Must | N-1 R-OWN-03 | Inspection of §10 |
| REQ-UIXS-005 | A disabled control SHALL state its blocking reason. Placeholder copy such as "coming soon" SHALL NOT appear as a specification value. | Must | N-2 REQ-DOCS-015 | Inspection |
| REQ-UIXS-006 | The settings UI SHALL NOT display demo fallback data when an API call fails, and SHALL NOT report a save as successful when no persistence occurred. | Must | N-7 | Analysis (§11) + test |
| REQ-UIXS-007 | Each of D-01…D-15 SHALL be dispositioned in §9 as visible (diagnostic surface), hidden (platform constant), or a settings-authority gap. | Must | N-1 §10 | Inspection of §9 |
| REQ-UIXS-008 | Coverage counts in §6 SHALL be re-derived from the §5 matrix. Counts copied without derivation SHALL NOT be presented as verified. | Must | N-2 REQ-DOCS-011 | Inspection of §6 |

---

## 3. Method — How Rows and Counts Are Derived

### 3.1 Row unit

One matrix row = one **inventory table row** of `SOMA-SETTINGS-MODEL-001.md` §9. Where §9 groups a
field family into one row (for example `util_model_* (provider, name, api_base, ctx_length, ctx_input, kwargs, rl_*)`
at `SOMA-SETTINGS-MODEL-001.md:479`), this matrix keeps that family as one row, matching the source
inventory's own convention (`SOMA-SETTINGS-MODEL-001.md:715-716`). Field families therefore count as
**one** requirement in §6, not as their individual field count.

### 3.2 Mechanical row count

Rows were counted by parsing every `### 9.x` table in `SOMA-SETTINGS-MODEL-001.md` and excluding the
header and separator rows. The §9 tables contain **316 data rows**:

| Category | §9 data rows (this matrix) | §12 Summary Counts (source) | Delta |
|---|---|---|---|
| C1 INFRA | 67 | 66 | +1 |
| C2 SECURITY | 38 | 37 | +1 |
| C3 MEMORY | 44 | 43 | +1 |
| C4 LLM | 42 | 41 | +1 |
| C5 AGENT | 30 | 29 | +1 |
| C6 PERSONALITY | 18 | 17 | +1 |
| C7 UI | 6 | 5 | +1 |
| C8 GOVERNANCE | 15 | 14 | +1 |
| C9 OBSERVABILITY | 12 | 11 | +1 |
| C10 INTEGRATION | 44 | 43 | +1 |
| **TOTAL** | **316** | **306** | **+10** |

The source §12 (`SOMA-SETTINGS-MODEL-001.md:719-731`) reports 306 — a uniform −1 per category against
the §9 tables as written. This document counts the tables as written (316) because §9 is the inventory;
the discrepancy is recorded as disagreement X-01 in §12. Neither number is rounded or estimated.

### 3.3 Coverage column definitions

| Column | Definition |
|---|---|
| Count | Matrix rows in that category (§5) |
| Implemented | Rows whose control exists in shipped `webui/` code and is wired to a real API read or write (impl = `yes`) |
| Tested | Rows covered by an automated test that names the key or its resolver |
| Coverage | Implemented ÷ Count, one decimal place |

Rows mapped to a `NEW` screen (impl = `new`) or to an existing read-only surface without an editor
(impl = `ro`) are **placed** (they have a home) but are **not Implemented**. Placement is what this
document proves; implementation status is what §6 measures.

---

## 4. Screen Register (`UI-S-<nn>`)

`SOMA-UIUX-PARITY-PLAN-002.md` has **no Appendix A.3** — the file ends at §9
(`docs/project/SOMA-UIUX-PARITY-PLAN-002.md:459-465`) and its screen map is prose in §4, not a numbered
register. The register below is therefore **proposed by this document** and SHALL be folded into
PARITY-PLAN as Appendix A.3. Disagreement X-02 records the missing appendix.

Screens are organised by the CAPSULE-FIRST IA of N-3 §3.3: rail = Capsules · Chat · Modules ·
Capabilities · Instances · Constitutions · Settings; workspace = the six facet tabs of N-3 §3.1.

### 4.1 Capsule facet screens (N-3 §3.1, N-4)

| Screen ID | Name | Status | Component / predecessor |
|---|---|---|---|
| UI-S-01 | Capsule workspace — Soul facet | NEW | `predecessor: webui/src/views/saas-agent-capsule.ts` |
| UI-S-02 | Capsule workspace — Brain facet | NEW | `models half exists: webui/src/views/saas-settings-models.ts` |
| UI-S-03 | Capsule workspace — Hands facet | NEW | `predecessor: webui/src/views/saas-agent-tools.ts` |
| UI-S-04 | Capsule workspace — Memory facet | NEW | `predecessor: webui/src/views/saas-memory-view.ts` |
| UI-S-05 | Capsule workspace — Body facet | NEW | `no predecessor` |
| UI-S-06 | Capsule workspace — Governance facet | NEW | `no predecessor` |

### 4.2 Peer rail screens

| Screen ID | Name | Status | Component / predecessor |
|---|---|---|---|
| UI-S-07 | Chat | EXISTS | `webui/src/views/saas-chat.ts` |
| UI-S-08 | Modules (rail) | NEW | `predecessor: webui/src/views/saas-settings-channels.ts module list` |
| UI-S-09 | Capabilities (rail) | EXISTS-partial | `webui/src/views/saas-agent-tools.ts, saas-feature-catalog.ts` |
| UI-S-10 | Instances (rail) | NEW | `no predecessor` |
| UI-S-11 | Constitutions (rail) | NEW | `no predecessor` |

### 4.3 Settings scopes

N-3 B-3 (`docs/project/SOMA-UIUX-PARITY-PLAN-002.md:213`) defines the four user-facing scopes as
**Agent / External / Connectivity / System**, matching the shipped tabs
(`webui/src/views/saas-settings.ts:22` `type SettingsTab = 'agent' | 'external' | 'connectivity' | 'system'`).
The module manifest vocabulary is a **different list** — `VALID_SETTINGS_SECTIONS = {agent, external, developer, mcp, backup, file-browser, skills}`
(`admin/modules/manifest.py:49-51`). Both are real; they are reconciled below. The scope column of §5
uses the vocabulary requested for this matrix and maps it to both.

| Scope (§5 column) | Shipped tab (`saas-settings.ts:22`) | Manifest `settings_sections` (`manifest.py:49-51`) | Screen IDs |
|---|---|---|---|
| Agent | `agent` | `agent`, `skills` | UI-S-12, UI-S-01…05 |
| External | `external`, `connectivity` | `external`, `mcp` | UI-S-13, UI-S-14, UI-S-16, UI-S-17 |
| Developer | `system` + Debug surface (N-3 B-8) | `developer`, `file-browser` | UI-S-15, UI-S-31 |
| Backup | `system` → Backup & Restore section | `backup` | UI-S-15, UI-S-30 |
| Platform | (no A0 counterpart — operator/platform) | — | UI-S-22…29, UI-S-32 |
| Module-injected | rows injected into a named scope | any valid section | UI-S-08, UI-S-17 |

| Screen ID | Name | Status | Component / route |
|---|---|---|---|
| UI-S-12 | Settings — Agent scope | EXISTS | `webui/src/views/saas-settings.ts:_renderAgentTab` |
| UI-S-13 | Settings — External scope | EXISTS | `webui/src/views/saas-settings.ts:_renderExternalTab` |
| UI-S-14 | Settings — Connectivity scope | EXISTS | `webui/src/views/saas-settings.ts:_renderConnectivityTab` |
| UI-S-15 | Settings — System scope | EXISTS | `webui/src/views/saas-settings.ts:_renderSystemTab` |
| UI-S-16 | Models settings (providers/slots/presets/catalog) | EXISTS | `webui/src/views/saas-settings-models.ts` |
| UI-S-17 | Channels settings (bridges) | EXISTS | `webui/src/views/saas-settings-channels.ts` |
| UI-S-18 | Multimodal settings | EXISTS | `webui/src/views/saas-multimodal-settings.ts` |
| UI-S-19 | Voice personas | EXISTS | `webui/src/views/saas-voice-personas.ts` |
| UI-S-20 | Admin API keys | EXISTS | `webui/src/views/saas-admin-api-keys.ts` |
| UI-S-21 | Admin feature flags | EXISTS | `webui/src/views/saas-admin-feature-flags.ts` |
| UI-S-22 | Tenant settings | EXISTS | `webui/src/views/saas-tenant-settings.ts` |
| UI-S-23 | Rate limits | EXISTS | `webui/src/views/saas-rate-limits.ts` |
| UI-S-24 | Permissions / roles | EXISTS | `webui/src/views/saas-permissions.ts, saas-role-matrix.ts` |
| UI-S-25 | Billing / usage | EXISTS | `webui/src/views/saas-billing.ts, saas-usage-analytics.ts` |
| UI-S-26 | Audit | EXISTS | `webui/src/views/saas-audit-log.ts` |
| UI-S-27 | Platform Topology (read-only diagnostics) | NEW | `no predecessor` |
| UI-S-28 | Platform Observability | EXISTS-partial | `webui/src/views/platform-metrics-dashboard.ts, saas-infrastructure-dashboard.ts` |
| UI-S-29 | Secrets — Vault pointers | NEW | `partial: webui/src/views/saas-admin-api-keys.ts, saas-settings-models.ts key status` |
| UI-S-30 | Backup & Restore | EXISTS-partial | `webui/src/views/saas-settings.ts:791-809 export only` |
| UI-S-31 | Developer / Debug surface | NEW | `PARITY-PLAN B-8; no predecessor` |
| UI-S-32 | Service settings forms (schema entities) | EXISTS | `webui/src/components/settings-form.ts, route /platform/settings/<entity> (main.ts:233-239)` |

### 4.4 Control-type legend

| Control | Rendering |
|---|---|
| text / textarea / path text / URL text / csv text / port | free entry with type validation |
| number / slider | numeric entry or bounded slider |
| select / multi-select | enumerated choice(s) from a closed set |
| toggle | boolean switch |
| secret-masked | masked placeholder + "rotate in Vault" affordance — value never rendered |
| read-only text / read-only meter | diagnostic display; no editor |
| derived readout | computed display next to its source knob; no editor |
| JSON editor / key-value editor / list editor | structured editor with schema validation |
| reference picker | FK / registry picker restricted to real configured objects |
| immutable viewer | render-only constitutional text with checksum + signature |

### 4.5 Edit-authority legend

| Token | Owner layer | Control state |
|---|---|---|
| `L2` | L2 Agent (Capsule / AgentSetting / UISetting / Constitution) | editable by the agent owner |
| `L1-gated` | L1 Django | editable only by platform operator role; otherwise read-only with reason |
| `L3-ro` | L3 Env | read-only — "L3 topology — operator-set in env, shown for diagnosis only" |
| `L4-secret` | L4 Vault | secret-masked — value never rendered; rotate in Vault |
| `derived-ro` | derived from L2 knobs | read-only readout |
| `binding` | Constitution | immutable once signed, or bind-only |
| `meter-ro` | platform metric | read-only meter |

---

## 5. Settings → Screen Placement Matrix

Every row of `SOMA-SETTINGS-MODEL-001.md` §9 appears exactly once. Key text is the §9 key/name.
Dispositions use the legends of §4.4–§4.5. `Impl` is the implementation state used by §6:
`yes` = live editor wired to a real API; `ro` = live read-only surface; `new` = mapped to a `NEW` screen.

### 5.1 C1 — INFRA (67 rows)

| # | Setting key (§9) | Screen | Facet | Scope | Control | Edit | Disabled-reason / note | Impl |
|---|---|---|---|---|---|---|---|---|
| 1 | `SA01_DEPLOYMENT_MODE` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 2 | `SA01_DEPLOYMENT_TARGET` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 3 | `SA01_ENVIRONMENT` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 4 | `SA01_ALLOWED_HOSTS / ALLOWED_HOSTS` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 5 | `SA01_DB_DSN` | UI-S-29 | Platform | Platform | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault; host portion also shown on UI-S-27 | new |
| 6 | `SA01_DB_CONN_MAX_AGE` | UI-S-32 | Platform | Platform | number | L1-gated | L1 Django tunable — operator role required (settings-form postgresql.pool) | ro |
| 7 | `SA01_DB_CONNECT_TIMEOUT` | UI-S-32 | Platform | Platform | number | L1-gated | L1 Django tunable — operator role required (settings-form postgresql.timeout) | ro |
| 8 | `POSTGRES_HOST` | UI-S-32 | Platform | Platform | text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only; fields exist in settings-form postgresql but MUST be read-only (R-ENV-02) | ro |
| 9 | `POSTGRES_PORT` | UI-S-32 | Platform | Platform | port | L3-ro | L3 topology — operator-set in env, shown for diagnosis only; fields exist in settings-form postgresql but MUST be read-only (R-ENV-02) | ro |
| 10 | `POSTGRES_DB` | UI-S-32 | Platform | Platform | text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only; fields exist in settings-form postgresql but MUST be read-only (R-ENV-02) | ro |
| 11 | `POSTGRES_USER` | UI-S-32 | Platform | Platform | text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only; fields exist in settings-form postgresql but MUST be read-only (R-ENV-02) | ro |
| 12 | `SA01_REDIS_URL / REDIS_URL` | UI-S-32 | Platform | Platform | URL text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | ro |
| 13 | `REDIS_HOST` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 14 | `REDIS_PORT` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 15 | `REDIS_DB` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 16 | `SA01_TEMPORAL_HOST` | UI-S-32 | Platform | Platform | text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | ro |
| 17 | `SA01_TEMPORAL_NAMESPACE` | UI-S-32 | Platform | Platform | text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | ro |
| 18 | `SA01_TEMPORAL_CONVERSATION_QUEUE` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 19 | `SA01_TEMPORAL_A2A_QUEUE` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 20 | `KAFKA_BOOTSTRAP_SERVERS / SA01_KAFKA_BOOTSTRAP_SERVERS` | UI-S-32 | Platform | Platform | text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | ro |
| 21 | `KAFKA_SECURITY_PROTOCOL` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 22 | `KAFKA_SASL_MECHANISM` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 23 | `KAFKA_SASL_USERNAME` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 24 | `KAFKA_SASL_PASSWORD` | UI-S-29 | Platform | Platform | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault | new |
| 25 | `PUBLISH_KAFKA_TIMEOUT_SECONDS` | UI-S-27 | Platform | Platform | number | L1-gated | L1 tunable — operator-set in deployment; shown for diagnosis only | new |
| 26 | `CONVERSATION_INBOUND` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 27 | `CONVERSATION_OUTBOUND` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 28 | `CONVERSATION_GROUP` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 29 | `DELEGATION_TOPIC` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 30 | `DELEGATION_GROUP` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 31 | `A2A_TOPIC` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 32 | `A2A_OUT_TOPIC` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 33 | `TOOL_REQUESTS_TOPIC` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 34 | `TOOL_RESULTS_TOPIC` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 35 | `TOOL_EXECUTOR_TOPICS` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 36 | `TOOL_EXECUTOR_GROUP` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 37 | `TASK_FEEDBACK_TOPIC` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 38 | `MEMORY_REPLICATOR_GROUP` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 39 | `MILVUS_HOST` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 40 | `MILVUS_PORT` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 41 | `SOMA_MILVUS_HOST` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 42 | `SOMA_MILVUS_PORT` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 43 | `SPICEDB_HOST` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 44 | `SPICEDB_PORT` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 45 | `SPICEDB_INSECURE` | UI-S-27 | Platform | Platform | toggle | L1-gated | L1 posture flag — operator-set; UI SHALL show value and effective TLS state, editor gated | new |
| 46 | `HTTP_CONNECT_TIMEOUT_S` | UI-S-27 | Platform | Platform | number | L1-gated | L1 resilience tunable — operator role required; default values come from Django settings (config/settings.py:95-109) | new |
| 47 | `HTTP_READ_TIMEOUT_S` | UI-S-27 | Platform | Platform | number | L1-gated | L1 resilience tunable — operator role required; default values come from Django settings (config/settings.py:95-109) | new |
| 48 | `HTTP_SLOW_READ_TIMEOUT_S` | UI-S-27 | Platform | Platform | number | L1-gated | L1 resilience tunable — operator role required; default values come from Django settings (config/settings.py:95-109) | new |
| 49 | `CB_FAILURE_THRESHOLD` | UI-S-27 | Platform | Platform | number | L1-gated | L1 resilience tunable — operator role required; default values come from Django settings (config/settings.py:95-109) | new |
| 50 | `CB_RESET_TIMEOUT_S` | UI-S-27 | Platform | Platform | number | L1-gated | L1 resilience tunable — operator role required; default values come from Django settings (config/settings.py:95-109) | new |
| 51 | `SOMABRAIN_URL / SA01_SOMA_BASE_URL` | UI-S-32 | Platform | Platform | URL text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | ro |
| 52 | `SOMAFRACTALMEMORY_URL` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 53 | `SOMA_MEMORY_URL` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 54 | `SA01_OPA_URL` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 55 | `SA01_POLICY_URL` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 56 | `POLICY_BASE_URL` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 57 | `SA01_GATEWAY_BASE` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 58 | `SA01_WORKER_GATEWAY_BASE` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 59 | `ROUTER_URL` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 60 | `SA01_POLICY_DATA_PATH` | UI-S-27 | Platform | Platform | path text | L3-ro | L3 file path — operator-set; shown for diagnosis only | new |
| 61 | `SA01_POLICY_CACHE_TTL` | UI-S-27 | Platform | Platform | number | L1-gated | L1 tunable — operator role required | new |
| 62 | `POLICY_REQUEUE_PREFIX` | UI-S-27 | Platform | Platform | read-only text | L1-gated | internal Redis requeue key prefix — not user-tunable; diagnostic only | new |
| 63 | `POLICY_REQUEUE_PREFIX_EXTRA` | UI-S-27 | Platform | Platform | read-only text | L1-gated | internal Redis requeue key prefix — not user-tunable; diagnostic only | new |
| 64 | `TENANT_CONFIG_PATH` | UI-S-27 | Platform | Platform | path text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 65 | `TENANT_CONFIG_PATH_EXTRA` | UI-S-27 | Platform | Platform | path text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 66 | `SA01_REDIS_URL (requeue store)` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only; alias of the same topology key | new |
| 67 | `SOMA_AAAS_MODE` | UI-S-27 | Platform | Platform | select | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |

### 5.2 C2 — SECURITY (38 rows)

| # | Setting key (§9) | Screen | Facet | Scope | Control | Edit | Disabled-reason / note | Impl |
|---|---|---|---|---|---|---|---|---|
| 1 | `SECRET_KEY` | UI-S-29 | Platform | Platform | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault | new |
| 2 | `VAULT_ADDR` | UI-S-29 | Platform | Platform | read-only text | L3-ro | Vault bootstrap topology (R-ENV-02) — operator-set; shown for diagnosis only | new |
| 3 | `VAULT_TOKEN_FILE` | UI-S-29 | Platform | Platform | read-only text | L3-ro | Vault bootstrap topology (R-ENV-02) — operator-set; shown for diagnosis only | new |
| 4 | `VAULT_MOUNT` | UI-S-29 | Platform | Platform | read-only text | L3-ro | Vault bootstrap topology (R-ENV-02) — operator-set; shown for diagnosis only | new |
| 5 | `VAULT_PATH_PREFIX` | UI-S-29 | Platform | Platform | read-only text | L3-ro | Vault bootstrap topology (R-ENV-02) — operator-set; shown for diagnosis only | new |
| 6 | `VAULT_NAMESPACE` | UI-S-29 | Platform | Platform | read-only text | L3-ro | Vault bootstrap topology (R-ENV-02) — operator-set; shown for diagnosis only | new |
| 7 | `VAULT_CA_CERT` | UI-S-29 | Platform | Platform | read-only text | L3-ro | Vault bootstrap topology (R-ENV-02) — operator-set; shown for diagnosis only | new |
| 8 | `VAULT_TOKEN` | UI-S-29 | Platform | Platform | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault (bootstrap token) | new |
| 9 | `VAULT_SKIP_VERIFY` | UI-S-29 | Platform | Platform | toggle | L1-gated | dev-only posture flag (services/common/vault_secrets.py) — gated to platform operator; production MUST render locked with reason | new |
| 10 | `SOMABRAIN_MEMORY_HTTP_TOKEN` | UI-S-29 | Platform | Platform | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault | new |
| 11 | `SOMA_API_TOKEN` | UI-S-29 | Platform | Platform | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault | new |
| 12 | `SA01_SOMABRAIN_API_KEY` | UI-S-29 | Platform | Platform | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault | new |
| 13 | `KEYCLOAK_CLIENT_SECRET / SA01_KEYCLOAK_CLIENT_SECRET` | UI-S-29 | Platform | Platform | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault | new |
| 14 | `SA01_JWT_SECRET` | UI-S-29 | Platform | Platform | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault | new |
| 15 | `GOOGLE_CLIENT_SECRET` | UI-S-29 | Platform | Platform | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault | new |
| 16 | `SA01_LLM_API_KEY` | UI-S-29 | Platform | Platform | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault | new |
| 17 | `SA01_LAGO_API_KEY` | UI-S-29 | Platform | Platform | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault | new |
| 18 | `SA01_GATEWAY_INTERNAL_TOKEN` | UI-S-29 | Platform | Platform | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault | new |
| 19 | `SPICEDB_TOKEN` | UI-S-29 | Platform | Platform | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault | new |
| 20 | `SOMA_REGISTRY_PRIVATE_KEY` | UI-S-29 | Platform | Platform | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault | new |
| 21 | `SOMABRAIN_VAULT_TOKEN` | UI-S-29 | Platform | Platform | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault | new |
| 22 | `SOMA_VAULT_TOKEN` | UI-S-29 | Platform | Platform | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault | new |
| 23 | `WA_CLOUD_API_TOKEN` | UI-S-29 | Platform | Platform | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault | new |
| 24 | `WA_CLOUD_APP_SECRET` | UI-S-29 | Platform | Platform | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault | new |
| 25 | `WA_CLOUD_WEBHOOK_VERIFY_TOKEN` | UI-S-29 | Platform | Platform | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault | new |
| 26 | `SA01_KEYCLOAK_PUBLIC_KEY` | UI-S-13 | Platform | External | read-only text | L3-ro | public key material — not secret; shown read-only for fingerprint comparison | new |
| 27 | `SA01_AUTH_REQUIRED` | UI-S-22 | Platform | Platform | toggle | L1-gated | L1 auth posture — operator role required | new |
| 28 | `SA01_AUTHZ_FAIL_OPEN` | UI-S-22 | Platform | Platform | toggle | L1-gated | fail-closed default (config/settings_registry.py:217) — editor gated; UI MUST show the fail-closed baseline | new |
| 29 | `AUTH_MAX_ATTEMPTS` | UI-S-22 | Platform | Platform | number | L1-gated | L1 lockout tunable — operator role required | new |
| 30 | `AUTH_LOCKOUT_DURATION` | UI-S-22 | Platform | Platform | number | L1-gated | L1 lockout tunable — operator role required | new |
| 31 | `AUTH_ATTEMPT_WINDOW` | UI-S-22 | Platform | Platform | number | L1-gated | L1 lockout tunable — operator role required | new |
| 32 | `SA01_JWT_ISSUER_STRICT` | UI-S-22 | Platform | Platform | toggle | L1-gated | L1 JWT posture — operator role required | new |
| 33 | `SA01_HSTS_SECONDS` | UI-S-22 | Platform | Platform | number | L1-gated | L1 transport security tunable — operator role required | new |
| 34 | `auth_login / auth_password / root_password` | UI-S-13 | Settings | External | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault; AgentSetting.is_secret pointer slot only (capsule_settings.py:200-215) | new |
| 35 | `api_keys` | UI-S-16 | Brain | External | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault; UI shows has_api_key status only (saas-settings-models.ts:27,683) | yes |
| 36 | `mcp_server_token` | UI-S-13 | Settings | External | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault | new |
| 37 | `secrets` | UI-S-13 | Settings | External | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault | new |
| 38 | `rfc_password` | UI-S-13 | Settings | External | secret-masked | L4-secret | L4 Vault-owned secret — value never rendered; rotate in Vault | new |

### 5.3 C3 — MEMORY (44 rows)

| # | Setting key (§9) | Screen | Facet | Scope | Control | Edit | Disabled-reason / note | Impl |
|---|---|---|---|---|---|---|---|---|
| 1 | `MEM_EMBED_DIM` | UI-S-27 | Memory | Platform | read-only meter | L1-gated | seam invariant MEM_EMBED_DIM == SOMA_VECTOR_DIM == SOMABRAIN_EMBED_DIM (ARCHITECTURE-INVARIANTS §2) — platform constant; UI shows the three values and their agreement | new |
| 2 | `SOMA_VECTOR_DIM` | UI-S-27 | Memory | Platform | read-only meter | L1-gated | mirror of MEM_EMBED_DIM — same seam invariant; never edited independently | new |
| 3 | `SOMABRAIN_EMBED_DIM` | UI-S-27 | Memory | Platform | read-only meter | L1-gated | mirror of MEM_EMBED_DIM (env key alias EMBED_DIM, see D-15) — never edited independently | new |
| 4 | `MEM_HTTP_TIMEOUT` | UI-S-27 | Memory | Platform | number | L1-gated | L1 memory transport timeout — operator role required; KEY_CATEGORY maps these to INFRA (see disagreement X-04) | new |
| 5 | `MEM_WRITE_TIMEOUT_S` | UI-S-27 | Memory | Platform | number | L1-gated | L1 memory transport timeout — operator role required; KEY_CATEGORY maps these to INFRA (see disagreement X-04) | new |
| 6 | `MEM_RECALL_TIMEOUT_S` | UI-S-27 | Memory | Platform | number | L1-gated | L1 memory transport timeout — operator role required; KEY_CATEGORY maps these to INFRA (see disagreement X-04) | new |
| 7 | `MEM_HISTORY_TIMEOUT_S` | UI-S-27 | Memory | Platform | number | L1-gated | L1 memory transport timeout — operator role required; KEY_CATEGORY maps these to INFRA (see disagreement X-04) | new |
| 8 | `MEM_RECALL_TOP_K` | UI-S-04 | Memory | Agent | number | L2 | Capsule-overridable via resolve_setting — agent owner edits; Django default is infrastructure baseline | new |
| 9 | `MEM_PROXIMITY_TOP_K` | UI-S-04 | Memory | Agent | number | L2 | Capsule-overridable via resolve_setting — agent owner edits; Django default is infrastructure baseline | new |
| 10 | `MEM_HISTORY_LIMIT` | UI-S-04 | Memory | Agent | number | L2 | Capsule-overridable via resolve_setting — agent owner edits; Django default is infrastructure baseline | new |
| 11 | `MEM_CHAT_NAMESPACE` | UI-S-04 | Memory | Agent | text | L2 | Capsule-overridable via resolve_setting — agent owner edits; Django default is infrastructure baseline | new |
| 12 | `MEM_DEFAULT_KIND` | UI-S-04 | Memory | Agent | text | L2 | Capsule-overridable via resolve_setting — agent owner edits; Django default is infrastructure baseline | new |
| 13 | `MEM_DEFAULT_SALIENCE` | UI-S-04 | Memory | Agent | slider | L2 | Capsule-overridable via resolve_setting — agent owner edits; Django default is infrastructure baseline | new |
| 14 | `MEM_DEFAULT_SOURCE` | UI-S-04 | Memory | Agent | text | L2 | Capsule-overridable via resolve_setting — agent owner edits; Django default is infrastructure baseline | new |
| 15 | `MEMORY_WAL_TOPIC` | UI-S-27 | Memory | Platform | read-only text | L1-gated | degraded-mode topic — L1 platform constant; shown for diagnosis only | new |
| 16 | `MEMORY_DEGRADED_TOPIC` | UI-S-27 | Memory | Platform | read-only text | L1-gated | degraded-mode topic — L1 platform constant; shown for diagnosis only | new |
| 17 | `SFM_NAMESPACE` | UI-S-04 | Memory | Agent | text | L2 | addressing namespace (L3 env may inject) — Capsule.memory_pointer / persona_config.memory is the agent authority | new |
| 18 | `SOMABRAIN_NAMESPACE` | UI-S-04 | Memory | Agent | text | L2 | addressing namespace (L3 env may inject) — Capsule.memory_pointer / persona_config.memory is the agent authority | new |
| 19 | `SA01_MEMORY_NAMESPACE` | UI-S-27 | Memory | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 20 | `SOMA_MEMORY_NAMESPACE` | UI-S-27 | Memory | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 21 | `SOMA_NAMESPACE` | UI-S-27 | Memory | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 22 | `SA01_NAMESPACE` | UI-S-27 | Memory | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 23 | `SA01_TENANT_ID` | UI-S-27 | Memory | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 24 | `memory_recall_enabled` | UI-S-04 | Memory | Agent | toggle | L2 | SettingsModel field (admin/core/helpers/settings_model.py) — agent owner; savable via save_capsule_setting | new |
| 25 | `memory_recall_delayed` | UI-S-04 | Memory | Agent | toggle | L2 | SettingsModel field (admin/core/helpers/settings_model.py) — agent owner; savable via save_capsule_setting | new |
| 26 | `memory_recall_query_prep` | UI-S-04 | Memory | Agent | toggle | L2 | SettingsModel field (admin/core/helpers/settings_model.py) — agent owner; savable via save_capsule_setting | new |
| 27 | `memory_recall_post_filter` | UI-S-04 | Memory | Agent | toggle | L2 | SettingsModel field (admin/core/helpers/settings_model.py) — agent owner; savable via save_capsule_setting | new |
| 28 | `memory_memorize_enabled` | UI-S-04 | Memory | Agent | toggle | L2 | SettingsModel field (admin/core/helpers/settings_model.py) — agent owner; savable via save_capsule_setting | new |
| 29 | `memory_memorize_consolidation` | UI-S-04 | Memory | Agent | toggle | L2 | SettingsModel field (admin/core/helpers/settings_model.py) — agent owner; savable via save_capsule_setting | new |
| 30 | `memory_recall_interval` | UI-S-04 | Memory | Agent | number | L2 | SettingsModel field — agent owner; savable via save_capsule_setting | new |
| 31 | `memory_recall_history_len` | UI-S-04 | Memory | Agent | number | L2 | SettingsModel field — agent owner; savable via save_capsule_setting | new |
| 32 | `memory_recall_memories_max_search` | UI-S-04 | Memory | Agent | number | L2 | SettingsModel field — agent owner; savable via save_capsule_setting | new |
| 33 | `memory_recall_solutions_max_search` | UI-S-04 | Memory | Agent | number | L2 | SettingsModel field — agent owner; savable via save_capsule_setting | new |
| 34 | `memory_recall_memories_max_result` | UI-S-04 | Memory | Agent | number | L2 | SettingsModel field — agent owner; savable via save_capsule_setting | new |
| 35 | `memory_recall_solutions_max_result` | UI-S-04 | Memory | Agent | number | L2 | SettingsModel field — agent owner; savable via save_capsule_setting | new |
| 36 | `memory_recall_similarity_threshold` | UI-S-04 | Memory | Agent | slider | L2 | SettingsModel field — agent owner; savable via save_capsule_setting | new |
| 37 | `memory_memorize_replace_threshold` | UI-S-04 | Memory | Agent | slider | L2 | SettingsModel field — agent owner; savable via save_capsule_setting | new |
| 38 | `Capsule.memory_pointer.{tenant,namespace,recall_limit,similarity_threshold}` | UI-S-04 | Memory | Agent | reference picker + number + slider | L2 | Capsule field (core.py:284-295) — agent owner; live recall preview against real hits only (PARITY-PLAN §3.1) | new |
| 39 | `Capsule.persona_config.memory.{recall_limit,similarity_threshold}` | UI-S-04 | Memory | Agent | number + slider | L2 | Capsule persona bucket (core.py:261,407) — agent owner; wins over AgentSetting in resolve_setting | new |
| 40 | `SA01_CACHE_WM_LIMIT` | UI-S-27 | Memory | Platform | number | L1-gated | L1 working-memory cache limit — operator role required | new |
| 41 | `SOMABRAIN_DEFAULT_TENANT` | UI-S-27 | Memory | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 42 | `SOMABRAIN_HRR_DIM` | UI-S-27 | Memory | Platform | read-only meter | L1-gated | SomaBrain-internal vector dimension — platform constant; shown for diagnosis only (settings-form somabrain schema has no field; see gap G-02) | new |
| 43 | `SOMABRAIN_QUANTUM_DIM` | UI-S-27 | Memory | Platform | read-only meter | L1-gated | SomaBrain-internal vector dimension — platform constant; shown for diagnosis only (settings-form somabrain schema has no field; see gap G-02) | new |
| 44 | `SOMABRAIN_HRR_DTYPE` | UI-S-27 | Memory | Platform | read-only text | L1-gated | SomaBrain-internal dtype — platform constant; diagnostic only | new |

### 5.4 C4 — LLM (42 rows)

| # | Setting key (§9) | Screen | Facet | Scope | Control | Edit | Disabled-reason / note | Impl |
|---|---|---|---|---|---|---|---|---|
| 1 | `DEFAULT_CHAT_MODEL_PROVIDER` | UI-S-16 | Brain | Agent | reference picker | L2 | tenant-default slot binding (admin/llm/api.py) — agent owner may override per Capsule; Django default is baseline | ro |
| 2 | `DEFAULT_CHAT_MODEL_NAME` | UI-S-16 | Brain | Agent | reference picker | L2 | tenant-default slot binding (admin/llm/api.py) — agent owner may override per Capsule; Django default is baseline | ro |
| 3 | `DEFAULT_UTIL_MODEL_PROVIDER` | UI-S-16 | Brain | Agent | reference picker | L2 | tenant-default slot binding (admin/llm/api.py) — agent owner may override per Capsule; Django default is baseline | ro |
| 4 | `DEFAULT_UTIL_MODEL_NAME` | UI-S-16 | Brain | Agent | reference picker | L2 | tenant-default slot binding (admin/llm/api.py) — agent owner may override per Capsule; Django default is baseline | ro |
| 5 | `DEFAULT_EMBED_MODEL_PROVIDER` | UI-S-16 | Brain | Agent | reference picker | L2 | tenant-default slot binding (admin/llm/api.py) — agent owner may override per Capsule; Django default is baseline | ro |
| 6 | `DEFAULT_EMBED_MODEL_NAME` | UI-S-16 | Brain | Agent | reference picker | L2 | tenant-default slot binding (admin/llm/api.py) — agent owner may override per Capsule; Django default is baseline | ro |
| 7 | `DEFAULT_VOICE_MODEL` | UI-S-02 | Brain | Agent | reference picker | L2 | voice model slot — agent owner; Capsule.voice_model FK is the body authority (core.py:225) | new |
| 8 | `AAAS_DEFAULT_CHAT_MODEL` | UI-S-16 | Brain | Platform | read-only text | L1-gated | AAAS platform default — operator baseline; shown read-only on Models for diagnosis | ro |
| 9 | `LLM_CONNECT_TIMEOUT_S` | UI-S-27 | Brain | Platform | number | L1-gated | LLM transport tunable — operator role required; KEY_CATEGORY agrees these are LLM (capsule_settings.py:75-80) | new |
| 10 | `LLM_READ_TIMEOUT_S` | UI-S-27 | Brain | Platform | number | L1-gated | LLM transport tunable — operator role required; KEY_CATEGORY agrees these are LLM (capsule_settings.py:75-80) | new |
| 11 | `LLM_MAX_RETRIES` | UI-S-27 | Brain | Platform | number | L1-gated | LLM transport tunable — operator role required; KEY_CATEGORY agrees these are LLM (capsule_settings.py:75-80) | new |
| 12 | `LLM_RETRY_BASE_DELAY_S` | UI-S-27 | Brain | Platform | number | L1-gated | LLM transport tunable — operator role required; KEY_CATEGORY agrees these are LLM (capsule_settings.py:75-80) | new |
| 13 | `LLM_RETRY_BACKOFF_CAP_S` | UI-S-27 | Brain | Platform | number | L1-gated | LLM transport tunable — operator role required; KEY_CATEGORY agrees these are LLM (capsule_settings.py:75-80) | new |
| 14 | `LLM_RETRY_AFTER_CAP_S` | UI-S-27 | Brain | Platform | number | L1-gated | LLM transport tunable — operator role required; KEY_CATEGORY agrees these are LLM (capsule_settings.py:75-80) | new |
| 15 | `LLM_HTTP_TIMEOUT` | UI-S-27 | Brain | Platform | number | L1-gated | LLM transport tunable — operator role required; KEY_CATEGORY agrees these are LLM (capsule_settings.py:75-80) | new |
| 16 | `SA01_LLM_API_URL` | UI-S-27 | Brain | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 17 | `SA01_LLM_BASE_URL` | UI-S-27 | Brain | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 18 | `SA01_LLM_MODEL` | UI-S-16 | Brain | Agent | reference picker | L2 | env mirror of the chat slot — superseded by chat_model_id when set | ro |
| 19 | `SA01_VISION_MODEL` | UI-S-02 | Brain | Agent | reference picker | L2 | vision model name — agent owner; bind via Capsule.image_model FK | new |
| 20 | `SA01_GEMINI_COMPAT_ENABLED` | UI-S-31 | Brain | Developer | toggle | L1-gated | LLM compatibility shim (services/common/llm_compatibility.py) — operator/developer scope; toggle shows effective shim state | new |
| 21 | `SA01_JSON_CLEANING_ENABLED` | UI-S-31 | Brain | Developer | toggle | L1-gated | LLM compatibility shim — operator/developer scope | new |
| 22 | `chat_model_provider / chat_model_name / chat_model_api_base` | UI-S-16 | Brain | Agent | text | L2 | SettingsModel chat binding (settings_model.py:37-43) — agent owner; provider rows save base_url and default model name (saas-settings-models.ts:699-717) | yes |
| 23 | `chat_model_kwargs` | UI-S-02 | Brain | Agent | JSON editor | L2 | per-call kwargs (e.g. temperature) — agent owner; MUST surface the AgentIQ derived temperature as a read-only overlay (see §8) | new |
| 24 | `chat_model_ctx_length` | UI-S-02 | Brain | Agent | number | L2 | SettingsModel field — agent owner | new |
| 25 | `chat_model_ctx_history` | UI-S-02 | Brain | Agent | slider | L2 | history share of context (0.0-1.0) — agent owner | new |
| 26 | `chat_model_vision` | UI-S-02 | Brain | Agent | toggle | L2 | SettingsModel field — agent owner | new |
| 27 | `chat_model_rl_requests / rl_input / rl_output` | UI-S-02 | Brain | Agent | number | L2 | rate-limit triple — agent owner; one row per §9 field-family convention | new |
| 28 | `util_model_* (provider, name, api_base, ctx_length, ctx_input, kwargs, rl_*)` | UI-S-16 | Brain | Agent | text + number + JSON editor | L2 | utility model binding family — agent owner; one inventory row per §9 convention | ro |
| 29 | `embed_model_* (provider, name, api_base, kwargs, rl_*)` | UI-S-16 | Brain | Agent | text + number + JSON editor | L2 | embedding model binding family — agent owner | ro |
| 30 | `browser_model_* (provider, name, api_base, vision, rl_*, kwargs, http_headers)` | UI-S-02 | Brain | Agent | text + number + JSON editor | L2 | browser model binding family — agent owner; Capsule.browser_model FK is the body authority | new |
| 31 | `chat_model_id` | UI-S-16 | Brain | Agent | reference picker | L2 | LLMModelConfig FK for chat slot (admin/llm/api.py:529) — slots tab binds real configured models only | yes |
| 32 | `utility_model_id` | UI-S-16 | Brain | Agent | reference picker | L2 | LLMModelConfig id for utility slot (admin/llm/api.py:519,565) | yes |
| 33 | `embedding_model_id` | UI-S-16 | Brain | Agent | reference picker | L2 | LLMModelConfig id for embedding slot (admin/llm/api.py:520,573) | yes |
| 34 | `llm_provider_configs` | UI-S-16 | Brain | External | key-value editor | L2 | per-provider enable/base_url/model_name/label — providers tab (saas-settings-models.ts:665-727) | yes |
| 35 | `model_presets` | UI-S-16 | Brain | Agent | list editor | L2 | named slot bundles — presets tab (saas-settings-models.ts:_savePreset) | yes |
| 36 | `LLMModelConfig.{name,display_name,model_type,provider,api_base}` | UI-S-16 | Brain | Agent | text | L2 | model registry identity — model catalog tab create/patch (saas-settings-models.ts:541,567) | yes |
| 37 | `LLMModelConfig.{capabilities,priority,cost_tier,domains}` | UI-S-16 | Brain | Agent | multi-select + number | L2 | capability-based routing fields (admin/llm/models.py:45-64) — catalog tab | yes |
| 38 | `LLMModelConfig.{ctx_length,limit_requests,limit_input,limit_output}` | UI-S-16 | Brain | Agent | number | L2 | model limits (admin/llm/models.py:67-70) — catalog tab | yes |
| 39 | `LLMModelConfig.{vision,kwargs,is_active}` | UI-S-16 | Brain | Agent | toggle + JSON editor | L2 | model config flags — catalog tab is_active toggle (saas-settings-models.ts:567) | yes |
| 40 | `USE_LLM` | UI-S-12 | Brain | Agent | toggle | L2 | master LLM switch (settings_model.py:165) — agent owner | new |
| 41 | `litellm_global_kwargs` | UI-S-31 | Brain | Developer | JSON editor | L2 | LiteLLM global kwargs — developer scope; agent owner may set, operator may pin | new |
| 42 | `SA01_CHAT_* / SA01_UTIL_* / SA01_EMBED_* / SA01_BROWSER_*` | UI-S-27 | Brain | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only; env mirrors of model-binding fields (settings_defaults.py:161-244) | new |

### 5.5 C5 — AGENT (30 rows)

| # | Setting key (§9) | Screen | Facet | Scope | Control | Edit | Disabled-reason / note | Impl |
|---|---|---|---|---|---|---|---|---|
| 1 | `Capsule.persona_config.knobs.intelligence_level` | UI-S-02 | Brain | Agent | slider | L2 | control knob 1-10 (core.py:259) — workspace chrome control panel (PARITY-PLAN §3.1); drives 6 derived settings | new |
| 2 | `Capsule.persona_config.knobs.autonomy_level` | UI-S-02 | Brain | Agent | slider | L2 | control knob 1-10 (core.py:259) — drives 3 derived settings | new |
| 3 | `Capsule.persona_config.knobs.resource_budget` | UI-S-02 | Brain | Agent | slider | L2 | control knob $/turn (core.py:259) — drives 3 derived settings | new |
| 4 | `Derived: temperature, max_tokens, rlm_iterations, recall_limit, model_tier, brain_query_enabled` | UI-S-02 | Brain | Agent | derived readout | derived-ro | derived from AgentIQ knob — do not set directly (intelligence_level); see §8 | new |
| 5 | `Derived: require_hitl, tool_approval, egress_allowed` | UI-S-02 | Brain | Agent | derived readout | derived-ro | derived from AgentIQ knob — do not set directly (autonomy_level); see §8 | new |
| 6 | `Derived: token_limit, cost_tier, thinking_budget` | UI-S-02 | Brain | Agent | derived readout | derived-ro | derived from AgentIQ knob — do not set directly (resource_budget); see §8 | new |
| 7 | `Capsule.tool_policy.auto_execute` | UI-S-03 | Hands | Agent | multi-select | L2 | tool policy bucket (core.py:272-282) — drag tools across three buckets (PARITY-PLAN §3.1) | new |
| 8 | `Capsule.tool_policy.approval_required` | UI-S-03 | Hands | Agent | multi-select | L2 | tool policy bucket — agent owner | new |
| 9 | `Capsule.tool_policy.denied` | UI-S-03 | Hands | Agent | multi-select | L2 | tool policy bucket — agent owner | new |
| 10 | `Capsule.capabilities` | UI-S-03 | Hands | Agent | reference picker | L2 | M2M → Capability (core.py:248-253) — attach/detach by category | new |
| 11 | `TOOL_REWARD_SUCCESS` | UI-S-27 | Hands | Platform | slider | L1-gated | SomaBrain FeedbackRequest.utility reward — platform tunable; Capsule-overridable per §9.5, editor gated to operator | new |
| 12 | `TOOL_REWARD_FAILURE` | UI-S-27 | Hands | Platform | slider | L1-gated | tool failure reward — platform tunable | new |
| 13 | `SOMABRAIN_CONTEXT_CONFIDENCE_DEFAULT` | UI-S-27 | Hands | Platform | slider | L1-gated | default context confidence — platform tunable | new |
| 14 | `agent_profile` | UI-S-12 | Agent | Agent | text | L2 | SettingsModel field (settings_model.py:126-138) — agent owner, advanced collapse (PARITY-PLAN B-3) | new |
| 15 | `agent_memory_subdir` | UI-S-12 | Agent | Agent | text | L2 | SettingsModel field (settings_model.py:126-138) — agent owner, advanced collapse (PARITY-PLAN B-3) | new |
| 16 | `agent_knowledge_subdir` | UI-S-12 | Agent | Agent | text | L2 | SettingsModel field (settings_model.py:126-138) — agent owner, advanced collapse (PARITY-PLAN B-3) | new |
| 17 | `shell_interface` | UI-S-12 | Agent | Agent | select | L2 | SettingsModel field (settings_model.py:126-138) — agent owner, advanced collapse (PARITY-PLAN B-3) | new |
| 18 | `SA01_TOOL_TIMEOUT_SECONDS` | UI-S-03 | Hands | Agent | number | L2 | tool execution timeout (services/tool_executor/execution_engine.py) — Capsule-overridable; L1 default is baseline | new |
| 19 | `TOOL_EXECUTOR_CIRCUIT_* (SA01_TOOL_TIMEOUT_SECONDS circuit knobs)` | UI-S-27 | Hands | Platform | number | L1-gated | tool circuit-breaker knobs — platform constant; diagnostic only | new |
| 20 | `TOOL_EXECUTOR_MAX_CONCURRENT` | UI-S-27 | Hands | Platform | number | L1-gated | platform concurrency limit — operator role required | new |
| 21 | `TOOL_FETCH_TIMEOUT` | UI-S-27 | Hands | Platform | number | L1-gated | tool fetch timeout — operator role required | new |
| 22 | `TOOL_WORK_DIR` | UI-S-27 | Hands | Platform | path text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 23 | `SA01_MULTIMODAL_POLL_INTERVAL` | UI-S-18 | Hands | Platform | number | L1-gated | multimodal poll interval — operator role required | new |
| 24 | `mcp_servers` | UI-S-13 | Agent | Agent | JSON editor | L2 | MCP server registry (settings_model.py:154) — agent owner; add-server affordance on UI-S-13 MUST write this | new |
| 25 | `mcp_client_init_timeout` | UI-S-13 | Agent | Agent | number | L2 | SettingsModel field — agent owner | new |
| 26 | `mcp_client_tool_timeout` | UI-S-13 | Agent | Agent | number | L2 | SettingsModel field — agent owner | new |
| 27 | `mcp_server_enabled` | UI-S-13 | Agent | Agent | toggle | L2 | expose MCP server (settings_model.py:157) — agent owner; the UI-S-13 'MCP Client' toggle is a different concept and MUST be relabelled (gap G-06) | new |
| 28 | `a2a_server_enabled` | UI-S-13 | Agent | Agent | toggle | L2 | expose A2A server (settings_model.py:159) — agent owner | new |
| 29 | `variables` | UI-S-12 | Agent | Agent | JSON editor | L2 | agent variables blob (settings_model.py:162) — agent owner | new |
| 30 | `SA01_ENABLE_MULTIMODAL_CAPABILITIES` | UI-S-18 | Hands | Platform | toggle | L1-gated | multimodal capability gate (admin/core/.../process_message.py) — operator role required | new |

### 5.6 C6 — PERSONALITY (18 rows)

| # | Setting key (§9) | Screen | Facet | Scope | Control | Edit | Disabled-reason / note | Impl |
|---|---|---|---|---|---|---|---|---|
| 1 | `system_prompt` | UI-S-01 | Soul | Agent | textarea | L2 | Capsule field (core.py:189) — agent owner; module prompt fragments merge here with provenance (PARITY-PLAN §3.2) | yes |
| 2 | `personality_traits` | UI-S-01 | Soul | Agent | slider (Big-Five) + JSON editor | L2 | Capsule field (core.py:190-191) — Big-Five 0.0-1.0 with live description; JSON editor is the advanced view | yes |
| 3 | `neuromodulator_baseline` | UI-S-01 | Soul | Agent | slider (4 axes) | L2 | Capsule field (core.py:193-194) — baseline chemical state | new |
| 4 | `neuromodulator_state` | UI-S-01 | Soul | Agent | read-only meter | derived-ro | last-synced state from SomaBrain (core.py:297-307) — sync timestamp shown; honesty: no value without a real sync | new |
| 5 | `learning_config` | UI-S-01 | Soul | Agent | number + slider (GMD) | L2 | GMD eta/lambda/alpha + reward thresholds (core.py:196-198) — first-class, not a hidden JSON blob | new |
| 6 | `Capsule.persona_config.prompts.injection_prompts` | UI-S-01 | Soul | Agent | list editor | L2 | persona prompt bucket (core.py:260) — agent owner; ordered with module provenance | new |
| 7 | `Capsule.persona_config.prompts.tool_prompts` | UI-S-01 | Soul | Agent | key-value editor | L2 | persona tool prompts (core.py:260) — agent owner | new |
| 8 | `speech_provider` | UI-S-19 | Soul | Agent | select | L2 | SettingsModel speech field (settings_model.py:146-150) — agent owner; voice personas screen is the home | new |
| 9 | `speech_realtime_model` | UI-S-19 | Soul | Agent | text | L2 | SettingsModel speech field (settings_model.py:146-150) — agent owner; voice personas screen is the home | new |
| 10 | `speech_realtime_voice` | UI-S-19 | Soul | Agent | select | L2 | SettingsModel speech field (settings_model.py:146-150) — agent owner; voice personas screen is the home | new |
| 11 | `speech_realtime_enabled` | UI-S-19 | Soul | Agent | toggle | L2 | SettingsModel field — agent owner | new |
| 12 | `speech_realtime_endpoint` | UI-S-27 | Soul | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only; D-09 records a hardcoded OpenAI URL schema default that MUST be removed | new |
| 13 | `stt_model_size` | UI-S-19 | Soul | Agent | select | L2 | SettingsModel STT field (settings_model.py:141-145) — agent owner | new |
| 14 | `stt_language` | UI-S-19 | Soul | Agent | select | L2 | SettingsModel STT field (settings_model.py:141-145) — agent owner | new |
| 15 | `stt_silence_threshold` | UI-S-19 | Soul | Agent | slider | L2 | SettingsModel STT timing field — agent owner; B-7 state machine surfaces effective values | new |
| 16 | `stt_silence_duration` | UI-S-19 | Soul | Agent | number | L2 | SettingsModel STT timing field — agent owner; B-7 state machine surfaces effective values | new |
| 17 | `stt_waiting_timeout` | UI-S-19 | Soul | Agent | number | L2 | SettingsModel STT timing field — agent owner; B-7 state machine surfaces effective values | new |
| 18 | `tts_kokoro` | UI-S-19 | Soul | Agent | toggle | L2 | Kokoro TTS toggle (settings_model.py:151) — agent owner | new |

### 5.7 C7 — UI (6 rows)

| # | Setting key (§9) | Screen | Facet | Scope | Control | Edit | Disabled-reason / note | Impl |
|---|---|---|---|---|---|---|---|---|
| 1 | `UISetting key space (tenant, user_id, key, value)` | UI-S-12 | Settings | Agent | key-value editor | L2 | free-form UI preferences (core.py:500-515) — per-tenant / per-user; theme and locale SHALL be named keys (D-11) | new |
| 2 | `diagram_theme` | UI-S-18 | Settings | Agent | select | L2 | Mermaid theme enum (saas-multimodal-settings.ts:27,436-437) — persisted via PUT /agents/<id>/multimodal-config | yes |
| 3 | `LANGUAGE_CODE` | UI-S-12 | Settings | Agent | select | L2 | operator-configurable locale (D-12) — UISetting-backed; Django LANGUAGE_CODE is the platform fallback | new |
| 4 | `TIME_ZONE` | UI-S-12 | Settings | Agent | select | L2 | presentation preference — UISetting-backed | new |
| 5 | `USE_I18N` | UI-S-15 | Settings | Platform | toggle | L1-gated | platform i18n switch (services/gateway/settings.py:172) — operator role required | new |
| 6 | `LOG_FORMAT` | UI-S-31 | Settings | Developer | select | L1-gated | log presentation (json\|console) — cross-listed in C9; one control, one authority | new |

### 5.8 C8 — GOVERNANCE (15 rows)

| # | Setting key (§9) | Screen | Facet | Scope | Control | Edit | Disabled-reason / note | Impl |
|---|---|---|---|---|---|---|---|---|
| 1 | `AAAS_DEFAULT_TENANT_ID` | UI-S-22 | Governance | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 2 | `AAAS_DEFAULT_MAX_AGENTS` | UI-S-22 | Governance | Platform | number | L1-gated | tier default quota (services/gateway/settings.py:201-204) — operator role required; tiers UI (UI-S-23/25) reads these as baselines | new |
| 3 | `AAAS_DEFAULT_MAX_USERS` | UI-S-22 | Governance | Platform | number | L1-gated | tier default quota (services/gateway/settings.py:201-204) — operator role required; tiers UI (UI-S-23/25) reads these as baselines | new |
| 4 | `AAAS_DEFAULT_MAX_TOKENS_MONTHLY` | UI-S-22 | Governance | Platform | number | L1-gated | tier default quota (services/gateway/settings.py:201-204) — operator role required; tiers UI (UI-S-23/25) reads these as baselines | new |
| 5 | `AAAS_DEFAULT_STORAGE_GB` | UI-S-22 | Governance | Platform | number | L1-gated | tier default quota (services/gateway/settings.py:201-204) — operator role required; tiers UI (UI-S-23/25) reads these as baselines | new |
| 6 | `SA01_DEFAULT_TOKEN_BUDGET` | UI-S-22 | Governance | Agent | number | L2 | default per-turn token budget — Capsule-overridable per §9.8 | new |
| 7 | `SA01_FEATURE_PROFILE` | UI-S-21 | Governance | Platform | read-only text | L1-gated | feature profile name — platform constant; flags UI shows the effective profile | new |
| 8 | `ENDPOINT_PERMISSIONS` | UI-S-24 | Governance | Platform | JSON editor | L1-gated | endpoint permission map (services/gateway/settings.py:234) — empty = DENY; operator role required | new |
| 9 | `Constitution.content` | UI-S-11 | Governance | Constitution | immutable viewer | binding | immutable once signed (Constitution.content_hash + Ed25519 signature) (core.py:79-90) | new |
| 10 | `Constitution.rules (tenant API)` | UI-S-11 | Governance | Constitution | list editor (pre-sign) | binding | tenant rules surface (admin/gateway/api/gateway.py:200-232) — editable only before signing | new |
| 11 | `Capsule.constitution_ref` | UI-S-06 | Governance | Agent | reference picker + read-only checksum | binding | cross-system ref {checksum,url} (core.py:178-180) — binding, not overridable away | new |
| 12 | `Capsule.resource_limits` | UI-S-05 | Body | Agent | number + JSON editor | L2 | max wall clock, concurrency (core.py:322) — Body facet | new |
| 13 | `Capsule.persona_config.governance.opa_policies` | UI-S-06 | Governance | Agent | JSON editor | L2 | OPA policy bindings (core.py:415-417) — agent owner within constitutional limits | new |
| 14 | `Capsule.persona_config.governance.spicedb_relations` | UI-S-06 | Governance | Agent | JSON editor | L2 | SpiceDB relation bindings (core.py:418) — agent owner within constitutional limits | new |
| 15 | `Budget metrics (tokens, images, tool_calls, …)` | UI-S-25 | Governance | Platform | read-only meter | meter-ro | budget gate metrics (admin/core/budget/gate.py, registry.py) — exhaustion returns HTTP 402; never editable | new |

### 5.9 C9 — OBSERVABILITY (12 rows)

| # | Setting key (§9) | Screen | Facet | Scope | Control | Edit | Disabled-reason / note | Impl |
|---|---|---|---|---|---|---|---|---|
| 1 | `LOG_LEVEL` | UI-S-31 | Settings | Developer | select | L1-gated | root log level — operator/developer role required | new |
| 2 | `LOG_FORMAT` | UI-S-31 | Settings | Developer | select | L1-gated | json\|console — cross-listed in C7; one control (see X-07) | new |
| 3 | `SA01_BRIDGE_LOG_LEVEL` | UI-S-31 | Settings | Developer | select | L1-gated | bridge-worker log level — operator/developer role required | new |
| 4 | `SA01_OTLP_ENDPOINT / OTLP_ENDPOINT` | UI-S-28 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | ro |
| 5 | `SA01_PROMETHEUS_URL` | UI-S-28 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | ro |
| 6 | `CONVERSATION_METRICS_HOST / CONVERSATION_METRICS_PORT` | UI-S-28 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only; bind addresses for per-worker metrics endpoints | ro |
| 7 | `DELEGATION_METRICS_HOST / DELEGATION_METRICS_PORT` | UI-S-28 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only; bind addresses for per-worker metrics endpoints | ro |
| 8 | `METRICS_HOST / METRICS_PORT` | UI-S-28 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only; bind addresses for per-worker metrics endpoints | ro |
| 9 | `TOOL_EXECUTOR_METRICS_HOST / TOOL_EXECUTOR_METRICS_PORT` | UI-S-28 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only; bind addresses for per-worker metrics endpoints | ro |
| 10 | `REPLICATOR_METRICS_HOST / REPLICATOR_METRICS_PORT` | UI-S-28 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only; bind addresses for per-worker metrics endpoints | ro |
| 11 | `SOMA_LOG_LEVEL` | UI-S-31 | Settings | Developer | select | L1-gated | SFM log level — operator/developer role required | new |
| 12 | `SOMA_LOG_JSON` | UI-S-31 | Settings | Developer | toggle | L1-gated | SFM JSON logging — operator/developer role required | new |

### 5.10 C10 — INTEGRATION (44 rows)

| # | Setting key (§9) | Screen | Facet | Scope | Control | Edit | Disabled-reason / note | Impl |
|---|---|---|---|---|---|---|---|---|
| 1 | `SA01_WHISPER_URL` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 2 | `SA01_WHISPER_API_URL` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 3 | `SA01_KOKORO_URL` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 4 | `SA01_KOKORO_TTS_URL` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 5 | `SA01_VOICEVOX_URL` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 6 | `SA01_MERMAID_CLI_URL` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 7 | `SA01_IMAGE_GEN_URL` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 8 | `SA01_DIAGRAM_URL` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 9 | `SA01_LAGO_API_URL` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 10 | `KEYCLOAK_URL / SA01_KEYCLOAK_URL` | UI-S-32 | Platform | Platform | URL text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only; settings-form keycloak.url is the field (settings-form.ts:114) | ro |
| 11 | `KEYCLOAK_REALM / SA01_KEYCLOAK_REALM` | UI-S-32 | Platform | Platform | text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | ro |
| 12 | `KEYCLOAK_CLIENT_ID / SA01_KEYCLOAK_CLIENT_ID` | UI-S-32 | Platform | Platform | text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | ro |
| 13 | `SA01_JWT_JWKS_URL` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 14 | `SA01_JWT_ALGORITHMS` | UI-S-22 | Platform | Platform | csv text | L1-gated | accepted JWT algorithms — operator role required | new |
| 15 | `SA01_JWT_LEEWAY` | UI-S-22 | Platform | Platform | number | L1-gated | JWT clock leeway (s) — operator role required | new |
| 16 | `JWT_ALGORITHM / JWT_AUDIENCE / JWT_ISSUER` | UI-S-22 | Platform | Platform | derived readout | derived-ro | derived JWT parameters (services/gateway/settings.py:334-336) — read-only; algorithm is a platform constant (D-12) | new |
| 17 | `GOOGLE_CLIENT_ID` | UI-S-13 | Platform | External | text | L3-ro | OAuth client topology — operator-set; shown read-only on External | new |
| 18 | `GOOGLE_REDIRECT_URI` | UI-S-13 | Platform | External | text | L3-ro | OAuth client topology — operator-set; shown read-only on External | new |
| 19 | `GOOGLE_JAVASCRIPT_ORIGIN` | UI-S-13 | Platform | External | text | L3-ro | OAuth client topology — operator-set; shown read-only on External | new |
| 20 | `WA_BRIDGE_MODE` | UI-S-17 | Module | Module-injected | select | L2 | WhatsApp bridge mode — set at channel create (saas-settings-channels.ts:215-223,127) | yes |
| 21 | `WA_BRIDGE_BASE_URL` | UI-S-27 | Module | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 22 | `WA_BRIDGE_PORT` | UI-S-27 | Module | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 23 | `WA_BRIDGE_SESSION_DIR` | UI-S-27 | Module | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 24 | `WA_BRIDGE_MEDIA_DIR` | UI-S-27 | Module | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 25 | `WA_BRIDGE_SIDECAR_CMD` | UI-S-27 | Module | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 26 | `WA_BRIDGE_SIDECAR_DIR` | UI-S-27 | Module | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 27 | `WA_CLOUD_PHONE_NUMBER_ID` | UI-S-17 | Module | Module-injected | text | L2 | channel row field — create channel form | new |
| 28 | `TG_API_BASE` | UI-S-27 | Module | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 29 | `TG_BRIDGE_MODE` | UI-S-17 | Module | Module-injected | select | L2 | Telegram bridge mode — set at channel create (saas-settings-channels.ts:215-223) | yes |
| 30 | `TG_WEBHOOK_URL` | UI-S-17 | Module | Module-injected | URL text | L2 | channel webhook URL — shown on channel row; write-only where it embeds a secret path | new |
| 31 | `SA01_BRIDGE_POLL_INTERVAL` | UI-S-27 | Module | Platform | number | L1-gated | bridge worker tunable — operator role required; diagnostic default from code | new |
| 32 | `SA01_BRIDGE_CHANNEL_REFRESH` | UI-S-27 | Module | Platform | number | L1-gated | bridge worker tunable — operator role required; diagnostic default from code | new |
| 33 | `SA01_BRIDGE_MAX_SEND_ATTEMPTS` | UI-S-27 | Module | Platform | number | L1-gated | bridge worker tunable — operator role required; diagnostic default from code | new |
| 34 | `SA01_BRIDGE_BACKOFF_BASE` | UI-S-27 | Module | Platform | number | L1-gated | bridge worker tunable — operator role required; diagnostic default from code | new |
| 35 | `SA01_BRIDGE_BACKOFF_CAP` | UI-S-27 | Module | Platform | number | L1-gated | bridge worker tunable — operator role required; diagnostic default from code | new |
| 36 | `CANVAS_SERVICE_URL` | UI-S-27 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 37 | `CANVAS_SERVICE_TIMEOUT` | UI-S-27 | Platform | Platform | number | L1-gated | canvas service timeout — operator role required | new |
| 38 | `rfc_auto_docker` | UI-S-14 | Module | Agent | toggle | L2 | RFC/tunnel binding (settings_model.py:131-135) — agent owner; tunnel section of Connectivity scope | new |
| 39 | `rfc_url` | UI-S-14 | Module | Agent | text | L2 | RFC/tunnel binding (settings_model.py:131-135) — agent owner; tunnel section of Connectivity scope | new |
| 40 | `rfc_port_http` | UI-S-14 | Module | Agent | number | L2 | RFC/tunnel binding (settings_model.py:131-135) — agent owner; tunnel section of Connectivity scope | new |
| 41 | `rfc_port_ssh` | UI-S-14 | Module | Agent | number | L2 | RFC/tunnel binding (settings_model.py:131-135) — agent owner; tunnel section of Connectivity scope | new |
| 42 | `SOMABRAIN_VAULT_ADDR / SOMABRAIN_VAULT_MOUNT_POINT / SOMABRAIN_VAULT_KV_MOUNT / SOMABRAIN_VAULT_BYPASS` | UI-S-29 | Platform | Platform | read-only text | L3-ro | SomaBrain Vault client topology — operator-set; bypass flag MUST render locked outside dev | new |
| 43 | `SOMA_VAULT_ADDR` | UI-S-29 | Platform | Platform | read-only text | L3-ro | L3 topology — operator-set in env, shown for diagnosis only | new |
| 44 | `AV_SCAN_ENABLED` | UI-S-13 | Module | Platform | toggle | L1-gated | antivirus/content scan capability (admin/gateway/api/gateway.py:245) — operator role required | new |

---

## 6. Coverage Summary (House RTM)

Counts re-derived from §5. `Implemented` = impl `yes` only. `Tested` = rows whose key or resolver is
named by an automated test (measured by searching `tests/` for the key, `resolve_setting`,
`derive_all_settings`, `MEM_EMBED_DIM`; see §3.3).

| Requirement Category | Count | Implemented | Tested | Coverage |
|---|---|---|---|---|
| C1 INFRA | 67 | 0 | 0 | 0.0% |
| C2 SECURITY | 38 | 1 | 0 | 2.6% |
| C3 MEMORY | 44 | 0 | 1 | 0.0% |
| C4 LLM | 42 | 10 | 0 | 23.8% |
| C5 AGENT | 30 | 0 | 0 | 0.0% |
| C6 PERSONALITY | 18 | 2 | 0 | 11.1% |
| C7 UI | 6 | 1 | 0 | 16.7% |
| C8 GOVERNANCE | 15 | 0 | 0 | 0.0% |
| C9 OBSERVABILITY | 12 | 0 | 0 | 0.0% |
| C10 INTEGRATION | 44 | 2 | 0 | 4.5% |
| **TOTAL** | **316** | **16** | **1** | **5.1%** |

Interpretation: **placement is complete** (316/316 rows have a screen in §5); **implementation is not**
(16/316 rows have a live wired editor today, 31 more have a live read-only surface,
269 are mapped to `NEW` screens).
The two numbers answer different questions and SHALL NOT be conflated.

---

## 7. Gaps

### 7.1 Settings with no UI home

Every one of the 316 §9 rows is placed in §5. **No inventory row is silently dropped.** The following
rows have only a *weak* home and are listed explicitly so the weakness is visible:

| Gap ID | Setting (§9) | Why the home is weak | Proposed home |
|---|---|---|---|
| G-01 | `SOMABRAIN_HRR_DIM`, `SOMABRAIN_HRR_DTYPE`, `SOMABRAIN_QUANTUM_DIM` (C3) | The shipped `settings-form` somabrain schema (`webui/src/components/settings-form.ts:120-129`) has no field for these; they are SomaBrain-internal. | Keep on UI-S-27 Platform Topology as read-only meters; add an `Advanced` collapse on UI-S-32 `somabrain` entity only if SomaBrain exposes them over its API. Until then the reason is "SomaBrain-internal vector dimension — platform constant; shown for diagnosis only". |
| G-02 | `POLICY_REQUEUE_PREFIX`, `POLICY_REQUEUE_PREFIX_EXTRA` (C1) | Internal Redis requeue key prefixes — no operator action is meaningful. | UI-S-27 read-only text, diagnostic only; **hidden** disposition. Not user-tunable. |
| G-03 | `LOG_FORMAT` (C7 and C9) | The same key is inventoried in two categories (`SOMA-SETTINGS-MODEL-001.md:562` and `:593`). | One control on UI-S-31 (Developer scope). Category annotation C7=presentation, C9=logging. See X-07. |
| G-04 | `Derived: …` three rows (C5) | These rows are not settable values at all. | Read-only derived readouts on UI-S-02 next to the 3 knobs (§8). Never editors. |
| G-05 | `Budget metrics (tokens, images, tool_calls, …)` (C8) | A metric family, not a settings key; exhaustion is a gate outcome (HTTP 402), not a configured value. | UI-S-25 read-only meters. Never editable. |

### 7.2 UI panels with no setting behind them (reverse gaps)

Every panel in `webui/src/views/saas-settings.ts` (and its siblings) was checked against the settings
model. Panels or controls with **no setting behind them** are gaps in the opposite direction and are
listed with evidence:

| Gap ID | Panel / control | Evidence | Finding | Required action |
|---|---|---|---|---|
| G-06 | External → API Keys rows "OpenAI" / "Anthropic" / "Serper" | `webui/src/views/saas-settings.ts:629-646` — literals `sk-****...****aBcD`, `sk-ant-****...****xYz` rendered as `api-key-value` | **Demo fallback data hardcoded in the component.** No API call populates these rows. Violates REQ-UIXS-006. | Replace with real provider list from `/llm/providers` + `/secrets/providers` (the pattern already used in `saas-settings-models.ts:319-330`). Never render a fabricated key fragment. |
| G-07 | External → API Keys → "Add API Key" button | `webui/src/views/saas-settings.ts:648-651` — `<button class="add-btn">` with no `@click` | Control with no handler (N-3 §9: "no control is clickable without a working handler"). | Remove or wire to the models-screen key flow (`saas-settings-models.ts:_saveKey`). |
| G-08 | External → MCP Configuration → "Add MCP Server" button | `webui/src/views/saas-settings.ts:674-677` — no `@click` | Control with no handler. | Wire to `mcp_servers` (C5 row 24) write path, or remove. |
| G-09 | External → MCP Configuration → "MCP Client" toggle | `webui/src/views/saas-settings.ts:662-672` toggles local `featureFlags.mcpEnabled`; `_saveSettings` posts it to `/settings/agent/` | The entity `agent` is **not** in `DEFAULT_SETTINGS` (`admin/core/api/settings_v2.py:48-94`) and `update_settings` rejects unknown entities (`settings_v2.py:162-165`). The save **cannot persist**. | Rebind to `mcp_server_enabled` / `mcp_servers` via `save_agent_setting`, or delete the control. |
| G-10 | Agent → Memory / SomaBrain → "SomaBrain URL" | `webui/src/views/saas-settings.ts:604` — `value="http://localhost:9696" readonly` | **Hardcoded placeholder URL**, not the live `SOMABRAIN_URL`. Violates REQ-UIXS-006 and R-ENV-03's no-localhost-fallback rule. | Read `SOMABRAIN_URL` from the topology API; render as L3 read-only. |
| G-11 | Agent → Memory / SomaBrain → "Collection" | `webui/src/views/saas-settings.ts:607-609` — free text `value="default"`, no load/save | No setting key backs "Collection". The nearest concepts are `MEM_CHAT_NAMESPACE` / `Capsule.memory_pointer.namespace`. | Replace with the Memory facet namespace field (`Capsule.memory_pointer`, UI-S-04). |
| G-12 | Connectivity → Voice → STT/TTS Provider selects | `webui/src/views/saas-settings.ts:706-719` — `<select>` with options, no binding to state or API | Free-floating selects. | Bind to `speech_provider` / `stt_model_size` / `tts_kokoro` (C6 rows 8, 13, 18). |
| G-13 | Connectivity → Proxy / Network → HTTP Proxy, HTTPS Proxy | `webui/src/views/saas-settings.ts:732-738` — text inputs, no state, no save | **No setting key exists** for HTTP/HTTPS proxy anywhere in `SOMA-SETTINGS-MODEL-001.md` §9. | Either add the keys to §9 (as C1 INFRA, L3) and wire them, or remove the panel. Currently a dead panel. |
| G-14 | System → Feature Flags → Memory / Tools / Voice toggles | `webui/src/views/saas-settings.ts:754-788` toggles `this._featureFlags.{memoryEnabled,toolsEnabled,voiceEnabled}` (defaults at `:488`) and saves to `/settings/agent/` | Same dead save as G-09. The real feature-flag surface is `admin/core/api/feature_flags.py` and `saas-admin-feature-flags.ts` (UI-S-21). | Remove these toggles or rebind to `is_feature_enabled` / FeatureRegistry keys (tested in `tests/unit/test_features_system.py`). |
| G-15 | System → Backup & Restore → "Import Config" button | `webui/src/views/saas-settings.ts:804-807` — no `@click` | Control with no handler. Export (`:800-803`) downloads only the *local* `chatModel/utilityModel/featureFlags` state (`:871-884`), not capsule export. | Wire Import to `services/capsule_import.py`; relabel Export as "Export local draft" or rebind to `services/capsule_export.py`. |
| G-16 | System → Danger Zone → "Reset All Settings" button | `webui/src/views/saas-settings.ts:819-822` — no `@click` | Destructive control with no handler and no confirm dialog (N-3 B-4 allows Dialog only for destructive/irreversible). | Implement behind a Dialog with typed confirmation, backed by a real reset API, or remove. |
| G-17 | Save Changes button on `saas-settings.ts` | `webui/src/views/saas-settings.ts:854-868` — `apiClient.put('/settings/agent/', …)`; on error only `console.error` | Endpoint rejects entity `agent` (G-09). **User sees no error**; `_isDirty` stays true but the header gives no failure signal. Silent failure in the UI even though the code path throws. | Surface the error in the form (the pattern in `saas-settings-models.ts:_flash`) and route to a real persistence path. |

### 7.3 Settings-authority gaps

| Gap ID | Finding | Evidence | Required action |
|---|---|---|---|
| G-18 | `settings_v2.DEFAULT_SETTINGS` invents a **second settings entity space** (`postgresql`, `redis`, `kafka`, `temporal`, `keycloak`, `somabrain`, `voice`) with its own `ServiceConfig` persistence, separate from `AgentSetting` / `UISetting` / `resolve_setting`. | `admin/core/api/settings_v2.py:48-94`, `:97-122`, `:155-178` | Reconcile with N-1 §5 resolution order or explicitly scope `ServiceConfig` as a deployment-entity store and document the split (R-OWN-05: no second resolution path). |
| G-19 | `settings_v2.DEFAULT_SETTINGS` contains `os.getenv(..., "localhost:9092")`-style fallbacks for topology keys. | `admin/core/api/settings_v2.py:50-93` | Fallbacks violate R-ENV-03 (fail-closed, no localhost fallback). Replace with `get_required_env` semantics or mark as schema fallbacks per N-1 §10. |


---

## 8. Derived-Settings Rule (AgentIQ — 3 knobs → 12 readouts)

**REQ-UIXS-003 restated normatively.** The 12 fields of `DerivedSettings`
(`admin/core/agentiq/settings.py:56-72`) SHALL be rendered as **read-only derived readouts** positioned
directly beside the three knobs on the Capsule Brain facet (UI-S-02) and in the workspace chrome
knob strip (N-3 §3.1, `docs/project/SOMA-UIUX-PARITY-PLAN-002.md:115`). They SHALL NOT be
independently editable. Writing a derived field directly is a bug, not a feature (N-1 R-CAP-02).

| Knob (editable, L2) | Range | Derived readouts (read-only) | Source |
|---|---|---|---|
| `intelligence_level` | 1–10 | `temperature`, `max_tokens`, `rlm_iterations`, `recall_limit`, `model_tier`, `brain_query_enabled` | `agentiq/settings.py:56-62` |
| `autonomy_level` | 1–10 | `require_hitl`, `tool_approval`, `egress_allowed` | `agentiq/settings.py:64-69` |
| `resource_budget` | $/turn | `token_limit`, `cost_tier`, `thinking_budget` | `agentiq/settings.py:70-72` |

Rendering rules:

1. Each readout is a `derived readout` control (§4.4) showing the **effective value computed now** by
   `derive_all_settings` (`admin/core/agentiq/derivation.py:27-89`), plus its unit and the knob that owns it.
2. A readout is never a form field. It has no save affordance and no dirty state.
3. When a knob changes, the readouts update from the same derivation call — the UI SHALL NOT
   re-implement the lookup tables (`admin/core/agentiq/tables.py`).
4. Enumerated readouts (`model_tier`, `tool_approval`, `egress_allowed`, `cost_tier`) render their
   enum value as text, not as a select (`agentiq/settings.py:20-43` defines the closed sets).
5. `DerivedSettings` is frozen (`model_config = {"frozen": True}`, `agentiq/settings.py:74`). The UI
   mirrors that immutability: readouts are display-only.

Default-value note: `derivation.py:54,59,64` falls back to `resolve_setting("AGENTIQ_INTELLIGENCE_LEVEL" /
"AGENTIQ_AUTONOMY_LEVEL" / "AGENTIQ_RESOURCE_BUDGET", default=5|5|0.10)`. Those three resolver keys are
**not present in `SOMA-SETTINGS-MODEL-001.md` §9** — disagreement X-05. Until they are inventoried,
the UI shows the knob value from `Capsule.persona_config.knobs` only and SHALL NOT surface the
resolver keys as separate editors.

---

## 9. Drift Items (D-01…D-15) → UI Disposition

Each drift item of `SOMA-SETTINGS-MODEL-001.md` §10 is dispositioned as **visible** (diagnostic
surface), **hidden** (platform constant), or **authority-gap** (settings-authority work, UI blocked
until reconciled).

| ID | §10 location / literal | UI disposition | Surface | Rationale |
|---|---|---|---|---|
| D-01 | `somabrain/memory/milvus_client.py:158` embed-dim fallback `128` | **visible** | UI-S-27 read-only meter: three-value seam agreement panel (`MEM_EMBED_DIM` / `SOMA_VECTOR_DIM` / `SOMABRAIN_EMBED_DIM`) | Operators must see seam disagreement. NOTE: `somabrain/` is not present in this checkout (see X-06) — literal unverified here. |
| D-02 | `somabrain/memory/consolidation.py:194` fallback `256` | **visible** | same seam panel as D-01 | Second inconsistent fallback for the same dimension. |
| D-03 | `somafractalmemory/admin/core/services.py:127` fallback `256` | **visible** | same seam panel as D-01 | Third inconsistent fallback. |
| D-04 | `HRR_DIM` fallback `512` vs `SOMABRAIN_HRR_DIM` default `8192` | **visible** | UI-S-27 `SOMABRAIN_HRR_DIM` meter (§5 C3 row 42) | Two names for one dimension; UI shows the resolved name only, with a note that `HRR_DIM` is a deprecated alias. |
| D-05 | `memory_contract.py:43` `DEFAULT_MEM_EMBED_DIM = 768` | **hidden** | none | Acceptable last-resort for non-Django scripts (N-1 §10). Keep equal to the seam dim. Not a user-facing setting. |
| D-06 | `degraded_memory_queue.py:25` `DEGRADED_TOPIC` module constant | **hidden** | none | **Code already reads `get_memory_setting("MEMORY_DEGRADED_TOPIC", "")`** (`services/common/degraded_memory_queue.py:33`). The duplicate module constant of §10 is no longer how the topic is resolved — drift appears closed in code and open in the document (X-08). |
| D-07 | `settings_defaults.py:100-111` resolution `ENV > DB > default` | **authority-gap** | none until reconciled | **Code no longer matches the drift entry** (X-03). Current `_env_or_db` docstring and body implement `AgentSetting > Django > (env only for topology keys) > default` (`admin/core/helpers/settings_defaults.py:100-127`). §10 D-07 is stale; §5 resolution order is closer to code than the drift register claims. |
| D-08 | `settings_model.py` schema fallbacks | **visible** | UI-S-12 Advanced collapse shows "effective value" + "source" badge (Capsule / AgentSetting / Django / schema fallback) per `resolve_setting` (`capsule_settings.py:138-175`) | Users must see when a value is a schema fallback rather than an authority value. |
| D-09 | `settings_model.py:150` hardcoded `https://api.openai.com/v1/realtime/sessions` | **visible** | UI-S-27 read-only text for `speech_realtime_endpoint` (§5 C6 row 12) with reason "L3 topology — operator-set in env" | Violates R-ENV-01; UI must not present the literal as the value. |
| D-10 | `agentiq/derivation.py:49-51` knob defaults `5`, `5`, `0.10` | **visible** | UI-S-02 knob strip shows "unset — using derivation default" until the knob is persisted on Capsule | Defaults live in code; UI must not claim a Capsule value exists when it does not. Line numbers in §10 are stale (now `:54,59,64` — X-09). |
| D-11 | No named `theme` / `locale` UISetting keys in Python | **visible** | UI-S-12 key-value editor over `UISetting` (§5 C7 row 1) | Register explicit key names when first used (N-1 §9.7 note). Until then the editor shows the free-form key space honestly. |
| D-12 | `JWT_ALGORITHM = "RS256"`, `LANGUAGE_CODE = "en-us"` literals | **visible** / **hidden** | `JWT_ALGORITHM` → UI-S-22 derived readout (hidden platform constant); `LANGUAGE_CODE` → UI-S-12 select (§5 C7 row 3) | Algorithm stays a platform constant; language becomes operator-configurable. |
| D-13 | `KEY_CATEGORY` maps `LLM_*` timeouts/retries to `INFRA` | **authority-gap** | none until taxonomy is aligned | **The drift entry does not match the code** (X-04): `capsule_settings.py:75-80` maps `LLM_*` to `CATEGORY_LLM`. The real mismatch is `MEM_HTTP_TIMEOUT` / `MEM_WRITE_TIMEOUT_S` / `MEM_RECALL_TIMEOUT_S` / `MEM_HISTORY_TIMEOUT_S` → `CATEGORY_INFRA` (`capsule_settings.py:49-52`) while §9.3 lists them under C3 MEMORY. |
| D-14 | dev `CHANNEL_LAYERS` = `InMemoryChannelLayer` vs gateway `RedisChannelLayer` | **visible** | UI-S-27 topology panel shows the effective channel-layer transport per deployment mode | Two Django settings modules disagree; UI shows which one is loaded, not a user choice. |
| D-15 | SomaBrain env key `EMBED_DIM` not `SOMABRAIN_EMBED_DIM` | **visible** | UI-S-27 seam panel labels the alias explicitly | Naming mismatch across repos for one dimension; converge names in code, show both until then. |

---

## 10. Secrets Rule (Normative)

| ID | Rule |
|---|---|
| R-SEC-UI-01 | Vault-owned values (C2, and any `AgentSetting.is_secret=True` row) **SHALL** render as a masked placeholder (for example `sk-…••••`) plus a **"rotate in Vault"** affordance. The value **SHALL NOT** be rendered, echoed, exported, or logged. (`SOMA-SETTINGS-MODEL-001.md` R-OWN-03, `capsule_settings.py:200-215`) |
| R-SEC-UI-02 | The "rotate in Vault" affordance **SHALL** link to the Vault path for the secret and **SHALL NOT** accept a new secret value in the Soma UI. Secret material enters the system only through Vault. |
| R-SEC-UI-03 | A secret-masked control **SHALL** show *presence* only (configured / not configured), never a key fragment that could be compared against a leaked key. The `has_api_key` boolean of `saas-settings-models.ts:27` is the reference implementation. The fabricated fragments `sk-****...****aBcD` at `saas-settings.ts:631` are non-compliant (gap G-06). |
| R-SEC-UI-04 | Secret rows **SHALL** be marked `L4-secret` in §5 and carry the disabled-reason "L4 Vault-owned secret — value never rendered; rotate in Vault". |
| R-SEC-UI-05 | Write-only entry fields (for example the channel bot token, `saas-settings-channels.ts:248-255`) **SHALL** be write-only on create and then re-render as R-SEC-UI-01 masked presence. |

C2 rows so marked in §5: `SECRET_KEY`, `VAULT_TOKEN`, `KAFKA_SASL_PASSWORD`, all service tokens and
client secrets, WhatsApp secrets, and the agent-level `auth_login` / `auth_password` / `root_password` /
`api_keys` / `mcp_server_token` / `secrets` / `rfc_password` family (`SOMA-SETTINGS-MODEL-001.md:360-397`).

---

## 11. Honesty Notes — What the Settings UI Shall Not Fake

These are prohibitions, each backed by a known offender found in the current code.

| ID | Prohibition | Known offender (evidence) | Correct behaviour |
|---|---|---|---|
| H-01 | The settings UI **SHALL NOT** render demo fallback data when an API is unavailable or has not been called. | `saas-settings.ts:629-646` renders literal `sk-****...****aBcD` / `sk-ant-****...****xYz` and a "Serper (Search)" row as if they were configured providers (G-06). | Render an empty state or an explicit error: "Provider list unavailable — /llm/providers did not respond". Never invent a key fragment. |
| H-02 | The settings UI **SHALL NOT** hardcode a topology value that a live setting owns. | `saas-settings.ts:604` `value="http://localhost:9696" readonly` for SomaBrain URL (G-10). | Bind to `SOMABRAIN_URL`; if unset, show "not configured" with the fail-closed reason. |
| H-03 | The settings UI **SHALL NOT** report a save as successful when no persistence occurred, and **SHALL NOT** swallow the failure into the console only. | `saas-settings.ts:854-868` `PUT /settings/agent/` — the entity `agent` is rejected by `admin/core/api/settings_v2.py:162-165`; the catch block only `console.error`s (G-09, G-17). | Show a visible error state on the form (pattern: `saas-settings-models.ts:253,369-391` `_flash`). A silent catch is not an honest save. |
| H-04 | The settings UI **SHALL NOT** ship a control with no handler. | "Add API Key" (`saas-settings.ts:648`), "Add MCP Server" (`:674`), "Import Config" (`:804`), "Reset All Settings" (`:819`) (G-07, G-08, G-15, G-16). | Every control is wired or rendered disabled with a reason (N-3 §9). |
| H-05 | The settings UI **SHALL NOT** present a panel that edits nothing. | Proxy / Network (`saas-settings.ts:724-740`) — inputs with no state and no setting key (G-13). | Remove, or add the keys to the inventory and wire them. |
| H-06 | Derived values **SHALL NOT** be edited, and a knob default **SHALL NOT** be presented as a stored Capsule value. | `derivation.py:54,59,64` code defaults `5/5/0.10` (D-10). | Knob shows "unset — using derivation default" until persisted (§8). |
| H-07 | A disabled control **SHALL** state its blocking reason; placeholder copy **SHALL NOT** stand in for one. | N-3 §4.2 records `coming soon` on four rail surfaces today (`saas-right-panel.ts` per `docs/project/SOMA-UIUX-PARITY-PLAN-002.md:279-284`). | Disabled-with-reason, as `saas-chat-topbar.ts:28` does for Nudge (cited in N-3 §4.1.1 as the reference implementation). |
| H-08 | Counts and statuses **SHALL NOT** be fabricated. | §6 of this document re-derives from §5 rather than copying `SOMA-SETTINGS-MODEL-001.md:731` (REQ-UIXS-008). | Every number cites its derivation. |

---

## 12. Disagreements with SOMA-SETTINGS-MODEL-001 and with the Code

Measured differences between the inventory document, the code, and the task brief. None of these
was silently reconciled.

| ID | Disagreement | Evidence | Effect on this document |
|---|---|---|---|
| X-01 | §12 Summary Counts report **306** rows; the §9 tables contain **316** data rows (uniform −1 per category). | `SOMA-SETTINGS-MODEL-001.md:719-731` vs mechanical parse of §9.1–§9.10 (this document §3.2). | §5 and §6 use 316 (the tables as written). Both numbers are shown in §3.2. |
| X-02 | The task brief cites `SOMA-UIUX-PARITY-PLAN-002.md` **Appendix A.3** for the screen list. That appendix does not exist. | `docs/project/SOMA-UIUX-PARITY-PLAN-002.md` ends at §9 (`:459-465`); no `Appendix` heading in the file. | §4 proposes the `UI-S-<nn>` register and SHALL be folded into PARITY-PLAN as Appendix A.3. |
| X-03 | Drift D-07 claims `_env_or_db` resolves `ENV > DB > default`. The code resolves `AgentSetting > Django > (env only for topology keys) > default`. | `SOMA-SETTINGS-MODEL-001.md:680` vs `admin/core/helpers/settings_defaults.py:100-127`. | D-07 is dispositioned in §9 as an authority gap with a note that the drift entry is stale. |
| X-04 | Drift D-13 claims `KEY_CATEGORY` maps `LLM_*` timeouts to `INFRA`. The code maps `LLM_*` to `CATEGORY_LLM`. The real mismatch is `MEM_*` timeouts → `INFRA` in code vs MEMORY in §9.3. | `SOMA-SETTINGS-MODEL-001.md:686` vs `admin/core/helpers/capsule_settings.py:49-52,75-80`. | §9 D-13 disposition corrects the target of the drift. |
| X-05 | `derivation.py` resolves `AGENTIQ_INTELLIGENCE_LEVEL` / `AGENTIQ_AUTONOMY_LEVEL` / `AGENTIQ_RESOURCE_BUDGET`; these keys are absent from §9. | `admin/core/agentiq/derivation.py:54,59,64` vs `SOMA-SETTINGS-MODEL-001.md` §9 (no such rows). | §8 forbids exposing them as editors until inventoried. |
| X-06 | §9 and §10 cite `somabrain/` and `somafractalmemory/` paths. Those directories are **not present** in this checkout (`somaAgent01`). | `ls` of repository root shows no `somabrain/` or `somafractalmemory/`; only `admin/somabrain` (client). | Drift items D-01…D-04, D-15 are dispositioned on the document's authority; their literals are marked unverified in this checkout. |
| X-07 | `LOG_FORMAT` is inventoried twice (C7 and C9). | `SOMA-SETTINGS-MODEL-001.md:562` and `:593`. | §5 lists it once per category as written (so both appear, 2 rows); §7 G-03 names the single control home. Coverage counts therefore include the cross-listing. |
| X-08 | Drift D-06 lists a duplicate `DEGRADED_TOPIC` module constant; code resolves the topic via `get_memory_setting("MEMORY_DEGRADED_TOPIC")`. | `SOMA-SETTINGS-MODEL-001.md:678` vs `services/common/degraded_memory_queue.py:33`. | D-06 dispositioned hidden/closed-in-code. |
| X-09 | Drift D-10 cites `derivation.py:49-51` for the knob defaults; they are at `:54,59,64` (and now routed through `resolve_setting`). | `admin/core/agentiq/derivation.py:48-65`. | §9 D-10 note records the stale line numbers. |
| X-10 | The task brief names settings scopes "Agent / External / Developer / Backup". The parity plan and shipped code use "Agent / External / Connectivity / System". The module manifest uses a third list (`agent, external, developer, mcp, backup, file-browser, skills`). | Brief vs `docs/project/SOMA-UIUX-PARITY-PLAN-002.md:213` and `webui/src/views/saas-settings.ts:22` vs `admin/modules/manifest.py:49-51`. | §4.3 reconciles all three; §5 scope column uses the brief's vocabulary with an explicit mapping. |

---

## 13. Maintenance

- Any new settings key **SHALL** be added to `SOMA-SETTINGS-MODEL-001.md` §9 and to §5 of this document together, with screen, facet, scope, control, edit authority and disabled-reason.
- Any new screen **SHALL** be registered in §4 with an `UI-S-<nn>` identifier and its component path.
- The §6 RTM **SHALL** be regenerated from §5 whenever §5 changes (REQ-UIXS-008).
- This document **SHALL** be reviewed on `Next Review` or when the settings resolution order or the IA in N-3 §3 changes.

---

End of Document
