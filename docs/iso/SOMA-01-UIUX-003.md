# SOMA-01-UIUX-003 — User Interface — Component & Module Catalogue

## Document Control

| Field | Value |
|---|---|
| Document Title | User Interface — Component & Module Catalogue |
| Document Identifier | SOMA-01-UIUX-003 |
| Version | 1.0.0 |
| Date | 2026-09-28 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-28 |
| Related | `SOMA-01-QMS-001.md`, `SOMA-A0-PARITY-001.md`, `SOMA-01-UIUX-001.md`, `SOMA-01-UIUX-002.md`, `SOMA-01-UIUX-005.md` |
| Source of truth | This document for the component/module inventory; `webui/src/components/`, `webui/src/stores/`, `webui/src/services/`, `webui/src/controllers/`, `admin/modules/`, `services/capsule_export.py`, `admin/core/agentiq/` as cited per row |
| Audience | UI/UX contributors, product engineering, any agent acting on somaAgent01 |
| Scope | Every file in `webui/src/components/` (56 measured 2026-09-28), 6 stores, 5 services, 8 controllers, the Capsule Module injection contract, Capsule facets, and the AgentIQ derivation |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-09-28 | SomaTech Engineering | Initial issue. 56-file component catalogue, 6 stores, 5 services, 8 controllers, Capsule Module contract, six facets, AgentIQ 3→12 derivation, honesty notes. |

## Normative References

| ID | Reference | Role |
|---|---|---|
| N-1 | SOMA-01-QMS-001 | Quality management system |
| N-2 | SOMA-01-DOCS-001 | Document control and traceability procedure |
| N-3 | SOMA-A0-PARITY-001 | Feature clone never code clone; Plan Gate; honesty rules |
| N-4 | SOMA-01-UIUX-001 | Screen and feature specification (the master) |
| N-5 | SOMA-UI-IDREG-001.md | Authoritative ID allocation |
| N-6 | SOMA-UI-TEMPLATE-001.md | House ISO template and honesty rules |
| N-7 | admin/modules/manifest.py | Capsule Module `module.yaml` contract |
| N-8 | admin/modules/hooks.py | KNOWN_HOOKS / RESERVED_HOOKS registry |
| N-9 | services/capsule_export.py | Six-facet Capsule export model |
| N-10 | admin/core/agentiq/settings.py, admin/core/agentiq/derivation.py, admin/core/agentiq/tables.py | AgentIQ 3 knobs → 12 derived settings |
| N-11 | admin/core/helpers/capsule_settings.py | Settings categories and resolution |
| N-12 | SOMA-01-UIUX-005 | Settings→screen placement; derived-settings rule |

---

## 1. Purpose and Scope

### 1.1 Purpose

This document is the **measured inventory** of the Soma web UI's shared parts: components, stores,
services, controllers, the Capsule Module injection contract, Capsule facets and AgentIQ. It exists
so that:

1. every reusable part has one catalogue row naming its tag, role, consumers and public surface;
2. the Capsule Module injection contract is written down once, including which hooks are live and
   which are reserved;
3. the six Capsule facets and their settings-category bindings are traceable;
4. the AgentIQ 3-knob → 12-derived-settings rule is stated as a derivation table, with derived
   values marked READ-ONLY (N-6 honesty rules; N-12 §8).

Counts in this document were **measured**, not assumed (see §8.1). Where the instructions that
prompted this document disagreed with the tree, the tree wins and the disagreement is recorded in §8.

### 1.2 Scope

- `webui/src/components/` — 56 files as of 2026-09-28.
- `webui/src/stores/` — 6 files. `webui/src/services/` — 5 files. `webui/src/controllers/` — 8 files.
- `admin/modules/` — manifest and hook contract; the three built-in Capsule Modules.
- `services/capsule_export.py` — six facets.
- `admin/core/agentiq/` — 3 knobs → 12 derived settings.

### 1.3 Out of Scope

- Per-screen control/action/feature ID allocation (UI-C-*/UI-A-*/UI-F-* belong to N-4).
- Modal pattern behaviour (N-02 = `SOMA-01-UIUX-002.md`).
- Backend business logic beyond the contracts named here.

---

## 2. Shared Component Catalogue (`webui/src/components/`)

**Measured 2026-09-28:** 56 files; **54** declare a tag via `@customElement(...)`; **1** declares a
tag via `customElements.define` (`settings-form.ts:709-710`); **1** is a barrel with no tag
(`index.ts`). So: 56 files, **55 registered custom-element tags**, 0 unregistered classes.

Legend — **props** are Lit `@property` declarations; **events** are `CustomEvent` names dispatched
by the component; **used by** lists measured consumers under `webui/src/`.

### 2.1 Core primitives

| # | File | Tag | Role | Used by | Public properties | Events |
|---|---|---|---|---|---|---|
| 1 | `saas-button.ts` | `saas-button` | Button primitive | `saas-settings-channels.ts`, `index.ts` | `variant`, `disabled`, `type` | — |
| 2 | `saas-select.ts` | `saas-select` | Select/dropdown primitive | `saas-admin-api-keys.ts`, `saas-admin-models-list.ts`, `index.ts` | `label`, `value`, `options`, `searchable`, `placeholder` | `saas-change` |
| 3 | `saas-toggle.ts` | `saas-toggle` | Toggle switch | `saas-admin-api-keys.ts`, `saas-admin-feature-flags.ts`, `saas-admin-models-list.ts`, `saas-admin-roles-list.ts`, `saas-personal-profile.ts`, `saas-platform-profile.ts`, `saas-settings-models.ts`, `saas-tenant-security-settings.ts` | `checked`, `disabled`, `label`, `description` | `saas-change` |
| 4 | `saas-form-field.ts` | `saas-form-field` | Labelled input with error/helper | `saas-admin-api-keys.ts`, `saas-admin-models-list.ts`, `saas-admin-roles-list.ts` | `label`, `type`, `placeholder`, `value`, `required`, `error`, `helper`, `disabled` | `saas-input` |
| 5 | `saas-data-table.ts` | `saas-data-table` | Sortable/clickable data table | `entity-manager.ts`, `saas-admin-api-keys.ts`, `saas-admin-feature-flags.ts`, `saas-admin-models-list.ts`, `saas-admin-roles-list.ts`, `saas-voice-sessions.ts` | `columns`, `data`, `clickable`, `rowKey`, `emptyMessage` | `saas-row-click`, `saas-sort` |
| 6 | `saas-status-badge.ts` | `saas-status-badge` | Status pill | `saas-admin-api-keys.ts`, `saas-admin-feature-flags.ts`, `saas-admin-models-list.ts`, `saas-admin-roles-list.ts`, `saas-settings-channels.ts`, `saas-settings-models.ts`, `saas-tenants.ts`, `saas-voice-sessions.ts` | `variant`, `size`, `showDot`, `label` | — |
| 7 | `saas-stat-card.ts` | `saas-stat-card` | Metric card | `saas-voice-sessions.ts` | `title`, `value`, `unit`, `subtitle`, `status`, `trend`, `trendValue`, `showStripe` | `saas-card-click` |
| 8 | `saas-action-menu.ts` | `saas-action-menu` | Row action menu | `entity-manager.ts`, `saas-admin-api-keys.ts`, `saas-admin-feature-flags.ts`, `saas-admin-models-list.ts`, `saas-admin-roles-list.ts` | `actions` | `saas-action` |
| 9 | `saas-permission-guard.ts` | `saas-permission-guard` | Renders children only with permission | `saas-marketplace.ts`, `saas-tenant-api-keys.ts`, `saas-tenant-security-settings.ts`, `saas-user-detail.ts` | `permission`, `permissions`, `fallback` | `request-access` |
| 10 | `saas-glass-modal.ts` | `saas-glass-modal` | **UI-M-03 Dialog shell** (see UIUX-002 §2.3) | `saas-admin-api-keys.ts`, `saas-admin-feature-flags.ts` (import only), `saas-admin-models-list.ts`, `saas-admin-roles-list.ts`, `saas-tenants.ts`, `saas-voice-personas.ts` | `open`, `title`, `subtitle`, `size`, `closeOnBackdrop`, `closeOnEscape`, `showClose`, `noPadding` | `saas-modal-open`, `saas-modal-close` |
| 11 | `entity-manager.ts` | `entity-manager` | Generic CRUD entity grid | `saas-entity-views.ts` | `entity`, `apiBase`, `columns`, `permissions` | `entity-action`, `saas-navigate` |
| 12 | `settings-form.ts` | `settings-form` (via `customElements.define`, `:709-710`) | JSON-Schema-driven settings form | `main.ts:236` (`/platform/settings/*`) | `entity`, `schemaUrl`, `valuesUrl`, `permissions` | — |
| 13 | `index.ts` | *(no tag)* | Barrel re-exports | — | re-exports 24 components + types | — |

### 2.2 Shell / navigation

| # | File | Tag | Role | Used by | Public properties | Events |
|---|---|---|---|---|---|---|
| 14 | `saas-sidebar.ts` | `saas-sidebar` | App sidebar | 19 views incl. `saas-workspace.ts`, `saas-agent-metrics.ts`, `saas-usage-analytics.ts`, `saas-voice-personas.ts` | `sections`, `activeRoute`, `collapsed`, `userName`, `userRole`, `logoText` | `saas-navigate`, `saas-sidebar-toggle` |
| 15 | `saas-sidebar-workspace.ts` | `saas-sidebar-workspace` | Workspace left rail | `saas-workspace.ts` | — | `saas-navigate` |
| 16 | `saas-right-panel.ts` | `saas-right-panel` | Workspace right rail (UI-X-*) | `saas-workspace.ts` | — | — |
| 17 | `saas-agent-header.ts` | `saas-agent-header` | Agent identity / knob strip chrome | `saas-workspace.ts` | — | — |
| 18 | `saas-welcome-dashboard.ts` | `saas-welcome-dashboard` | Empty-state workspace landing | `saas-chat-workspace.ts` | — | `new-conversation`, `saas-navigate` |
| 19 | `saas-user-profile-card.ts` | `saas-user-profile-card` | User identity card | `saas-platform-profile.ts`, `saas-user-detail.ts` | `user`, `showActions` | — |

### 2.3 Chat

| # | File | Tag | Role | Used by | Public properties | Events |
|---|---|---|---|---|---|---|
| 20 | `saas-chat-workspace.ts` | `saas-chat-workspace` | Chat workspace layout | `saas-workspace.ts` | — | — |
| 21 | `saas-chat-topbar.ts` | `saas-chat-topbar` | Chat title/model/control bar | `saas-chat.ts` | `title`, `modelLabel`, `busy`, `paused`, `canNudge`, `connectionStatus`, `nudgeTitle` | `saas-chat-control` |
| 22 | `saas-composer.ts` | `saas-composer` | Message composer | `saas-chat-workspace.ts`, `saas-chat.ts` | `busy`, `placeholder` | (types `ComposerSendDetail`) |
| 23 | `saas-composer-menu.ts` | `saas-composer-menu` | Composer overflow menu | `saas-composer.ts` | — | `clear-chat`, `export-chat`, `saas-navigate` |
| 24 | `saas-message.ts` | `saas-message` | Chat message bubble | `saas-chat-workspace.ts`, `saas-chat.ts` | `messageRole`, `text`, `timestamp`, `tools`, `streaming`, `stopped`, `confidence`, `error`, `attachments` | — |
| 25 | `saas-tool-timeline.ts` | `saas-tool-timeline` | Tool-call step timeline | `saas-chat-workspace.ts`, `saas-chat.ts`, `saas-message.ts` | `steps` (type `ToolCallStep[]`) | `tool-approval` |
| 26 | `saas-capsule-editor.ts` | `saas-capsule-editor` | Capsule persona/prompt editor (UI-S-01) | `saas-right-panel.ts` | — | — |
| 27 | `saas-brain-panel.ts` | `saas-brain-panel` | Brain facet panel (UI-S-02) | `saas-right-panel.ts` | — | — |

### 2.4 Platform / billing / tenant

| # | File | Tag | Role | Used by | Public properties | Events |
|---|---|---|---|---|---|---|
| 28 | `saas-platform-stats-grid.ts` | `saas-platform-stats-grid` | Platform KPI grid | `saas-platform-dashboard.ts` | `metrics` | — |
| 29 | `saas-platform-tenants-table.ts` | `saas-platform-tenants-table` | Platform tenants table | `saas-platform-dashboard.ts` | `tenants` | — |
| 30 | `saas-platform-activity-feed.ts` | `saas-platform-activity-feed` | Activity feed | `saas-platform-dashboard.ts` | `events` | — |
| 31 | `saas-platform-alerts-panel.ts` | `saas-platform-alerts-panel` | Alerts panel | `saas-platform-dashboard.ts` | `activeAlerts`, `alerts` | — |
| 32 | `saas-billing-metrics-cards.ts` | `saas-billing-metrics-cards` | Billing KPI cards | `saas-billing.ts` | `metrics` | — |
| 33 | `saas-billing-invoices-table.ts` | `saas-billing-invoices-table` | Platform invoices table | `saas-billing.ts` | `invoices` | — |
| 34 | `saas-billing-revenue-chart.ts` | `saas-billing-revenue-chart` | Tier revenue chart | `saas-billing.ts` | `tierRevenue` | — |
| 35 | `saas-tenant-billing-summary.ts` | `saas-tenant-billing-summary` | Tenant plan/usage summary | `saas-tenant-billing.ts` | `currentPlan`, `usage` | — |
| 36 | `saas-tenant-billing-plans.ts` | `saas-tenant-billing-plans` | Tenant plan cards | `saas-tenant-billing.ts` | `plans`, `upgrading` | — |
| 37 | `saas-tenant-billing-invoices.ts` | `saas-tenant-billing-invoices` | Tenant invoices | `saas-tenant-billing.ts` | `invoices` | — |
| 38 | `saas-tenant-general-settings.ts` | `saas-tenant-general-settings` | Tenant general settings form | `saas-tenant-settings.ts` | `settings` | — |
| 39 | `saas-tenant-security-settings.ts` | `saas-tenant-security-settings` | Tenant security settings | `saas-tenant-settings.ts` | `settings`, `activeTab` | — |
| 40 | `saas-tenant-api-keys.ts` | `saas-tenant-api-keys` | Tenant API key list | `saas-tenant-settings.ts` | — | — |
| 41 | `saas-tenant-wizard-form.ts` | `saas-tenant-wizard-form` | Wizard identity/plan form | `saas-tenant-wizard.ts` | `formData`, `slugStatus` | — |
| 42 | `saas-tenant-wizard-steps.ts` | `saas-tenant-wizard-steps` | Wizard step indicator | `saas-tenant-wizard.ts` | `currentStep`, `steps` | — |
| 43 | `saas-tenant-wizard-tier-select.ts` | `saas-tenant-wizard-tier-select` | Wizard tier picker | `saas-tenant-wizard.ts` | `tiers`, `selectedTierId`, `billingEmail` | — |
| 44 | `saas-subscription-tier-cards.ts` | `saas-subscription-tier-cards` | Tier cards | `saas-subscriptions.ts` | `tiers` | `delete-tier`, `edit-tier` |
| 45 | `saas-subscription-editor.ts` | `saas-subscription-editor` | Tier editor overlay (bespoke modal — see UIUX-002 §6.8) | `saas-subscriptions.ts` | `open`, `editingTier` | `close-editor`, `save-tier` |
| 46 | `saas-subscription-feature-matrix.ts` | `saas-subscription-feature-matrix` | Tier × feature matrix | `saas-subscriptions.ts` | `tiers` | — |

### 2.5 Infrastructure

| # | File | Tag | Role | Used by | Public properties | Events |
|---|---|---|---|---|---|---|
| 47 | `saas-infra-status-card.ts` | `saas-infra-status-card` | Service health card | `saas-infrastructure-dashboard.ts` | `service`, `component` | — |
| 48 | `saas-infra-metrics-chart.ts` | `saas-infra-metrics-chart` | Infra metrics chart | `saas-infrastructure-dashboard.ts` | `metrics` | — |
| 49 | `saas-infra-alert-list.ts` | `saas-infra-alert-list` | Infra recommendations/alerts | `saas-infrastructure-dashboard.ts` | `recommendations`, `mitigationActions`, `history` | — |

### 2.6 Voice

| # | File | Tag | Role | Used by | Public properties | Events |
|---|---|---|---|---|---|---|
| 50 | `saas-voice-controls.ts` | `saas-voice-controls` | Session/recording controls | `saas-voice-chat.ts` | `sessionStatus`, `selectedPersona`, `duration`, `turnCount`, `isLoading`, `isRecording`, `error` | `start-session`, `end-session`, `recording-start`, `recording-stop` |
| 51 | `saas-voice-session-picker.ts` | `saas-voice-session-picker` | Persona picker | `saas-voice-chat.ts` | `personas`, `selectedPersona`, `loading` | `persona-selected` |
| 52 | `saas-voice-transcript.ts` | `saas-voice-transcript` | Session transcript | `saas-voice-chat.ts` | `emptyMessage` | — |
| 53 | `voice-transcript.ts` | `voice-transcript` | Live transcript list | `saas-voice-chat.ts`, `saas-voice-transcript.ts` | `messages`, `autoScroll`, `emptyMessage` | `clear-transcript` |
| 54 | `voice-waveform.ts` | `voice-waveform` | Mic level / waveform stage | `saas-voice-controls.ts` | `status`, `showControls` | `mic-error`, `recording-start`, `recording-stop` |
| 55 | `voice-config-panel.ts` | `voice-config-panel` | Persona voice/LLM config | `saas-voice-personas.ts` | `config`, `llmOptions`, `voiceOptions` | `config-change`, `voice-preview` |
| 56 | `voice-persona-card.ts` | `voice-persona-card` | Persona card | `saas-voice-personas.ts` | `persona`, `editable` | `persona-edit`, `persona-delete`, `persona-duplicate`, `persona-set-default` |

### 2.7 Deleted components (verified absent 2026-09-28)

| File | Tag | Disposition |
|---|---|---|
| `saas-user-invite-modal.ts` | — | **DELETED 2026-09-27** as dead code (tag instantiated zero times). Reintroduce the invite flow from `SOMA-01-UIUX-002` §4.3, not from the deleted file. |
| `saas-voice-overlay.ts` | — | **DELETED 2026-09-27** as dead code (same evidence). Current voice UI is inline (§2.6); see UIUX-002 §5.3. |

---

## 3. Stores and Services

### 3.1 Stores (`webui/src/stores/` — 6 files)

Each store is a plain reactive class with a Lit `createContext` handle and a listener set. No store
talks to the network directly.

| # | File | Class | State owned | Consumed by |
|---|---|---|---|---|
| 1 | `activity-store.ts` | `ActivityStore` | Sidebar activity feed events (`ActivityEvent[]`) | `saas-sidebar-workspace.ts` |
| 2 | `agent-store.ts` | `AgentStore` | Active agent, `AgentProfile[]`, `ModelPreset[]` | `saas-agent-header.ts` |
| 3 | `brain-store.ts` | `BrainStore` | SomaBrain cognitive state: `NeuromodulatorState`, adaptation (0-100), memoryUsage (vector count) | `saas-brain-panel.ts` |
| 4 | `composer-store.ts` | `ComposerStore` | Composer draft/attachments state | `saas-composer.ts`, `saas-composer-menu.ts` |
| 5 | `iq-store.ts` | `IQStore` | The 3 knobs (`IQKnobs`: intelligence 1-10, autonomy 1-10, budget $/turn) + client-side `DerivedSettings` mirror | `saas-agent-header.ts` |
| 6 | `workspace-store.ts` | `WorkspaceStore` | Layout state for Agent Workspace | `saas-right-panel.ts`, `saas-agent-header.ts`, `saas-workspace.ts` |

### 3.2 Services (`webui/src/services/` — 5 files)

| # | File | Role | Owned state / contract | Consumed by |
|---|---|---|---|---|
| 1 | `api-client.ts` | SaaS Admin HTTP client | `ApiClientConfig`, `ApiResponse<T>`, `ApiError`; auth via **httpOnly cookie** — no Authorization header, no localStorage token | `agent-store.ts`, `entity-manager.ts`, `saas-chat-workspace.ts`, `saas-composer.ts`, `saas-permission-guard.ts`, all 8 controllers |
| 2 | `websocket-client.ts` | Realtime channel | Exponential backoff reconnect, 20s heartbeat, event subscription; auth via `Sec-WebSocket-Protocol` subprotocol (P3-04), cookie fallback; **never** a token in the query string | `saas-chat.ts` |
| 3 | `google-auth-service.ts` | Google OAuth 2.0 | `GoogleConfig`, `GoogleUserInfo`; real Google endpoints, state validation | `saas-login.ts`, `saas-auth-callback.ts` |
| 4 | `keycloak-service.ts` | Keycloak OIDC | `KeycloakConfig`, `KeycloakToken`; token + refresh handling | `saas-login.ts`, `saas-auth-callback.ts` |
| 5 | `theme-boot.ts` | Theme boot | `UiTheme = 'light' \| 'dark'`; `getTheme()`, `applyTheme()`; light by default, dark only via explicit toggle, persisted in localStorage | `main.ts`, `saas-sidebar-workspace.ts` |

---

## 4. Controllers (`webui/src/controllers/` — 8 files)

Controllers own data loading and mutations. They hold no UI markup ("Minimal logic, no UI concerns",
`subscriptions-controller.ts`). Each is consumed by the views/components named.

| # | File | Owns | Consumed by |
|---|---|---|---|
| 1 | `billing-controller.ts` | Platform billing metrics, invoices, tier revenue | `saas-billing.ts`, `saas-tenant-billing.ts`, billing chart/table/card components |
| 2 | `infra-dashboard-controller.ts` | `ServiceHealth`, `InfrastructureHealth`, `RateLimitPolicy`, polling | `saas-infrastructure-dashboard.ts`, `saas-infra-*` |
| 3 | `platform-dashboard-controller.ts` | `PlatformMetrics`, `RecentEvent`, user session state | `saas-platform-dashboard.ts`, `saas-platform-*` |
| 4 | `subscriptions-controller.ts` | `SubscriptionTier[]` load + save mutations | `saas-subscriptions.ts`, `saas-subscription-*` |
| 5 | `tenant-billing-controller.ts` | Tenant invoices, usage stats, tier limits, upgrade mutation | `saas-tenant-billing.ts`, `saas-tenant-billing-*` |
| 6 | `tenant-settings-controller.ts` | `TenantSettings` load/mutate/save; dispatches `show-toast` | `saas-tenant-settings.ts`, `saas-tenant-general-settings.ts`, `saas-tenant-security-settings.ts` |
| 7 | `tenant-wizard-controller.ts` | Wizard state, validation, submission (`TenantFormData` over 3 steps) | `saas-tenant-wizard.ts`, `saas-tenant-wizard-*` |
| 8 | `voice-chat-controller.ts` | WebSocket voice session, audio recording, `VoicePersona` list | `saas-voice-chat.ts`, `saas-voice-controls.ts`, `saas-voice-session-picker.ts` |

---

## 5. Capsule Module Injection Contract

Source: `admin/modules/manifest.py` (loader convention A0 `plugin.yaml` → Soma `module.yaml`) and
`admin/modules/hooks.py`. A Capsule Module lives at `admin/modules/<name>/` (built-in) or the
future install path `usr/modules/<name>/`.

### 5.1 Directory shape

```
admin/modules/<name>/
  module.yaml          # required manifest (the module's contract)
  module.config.json   # optional default runtime config (JSON)
  services/            # optional helpers (importable Python package)
  hooks.py             # optional: registers orchestrator hooks on import
  api.py               # optional: Ninja router mounted at /api/v2/modules/<name>/
  prompts/             # optional: prompt fragments merged into Capsule system_prompt
```

### 5.2 Contract fields (`module.yaml`)

| Field | Required | Type | Meaning |
|---|---|---|---|
| `name` | yes | str | Unique module id (stable). Example `mod_whatsapp`. |
| `title` | yes | str | Human label. Example "WhatsApp Channel". |
| `version` | yes | str | semver string. |
| `description` | no | str | Free text. |
| `settings_sections` | no | list | UI sections the module injects into. Accepted values (`manifest.py` `VALID_SETTINGS_SECTIONS`): `agent`, `external`, `developer`, `mcp`, `backup`, `file-browser`, `skills`. Unknown values raise `ManifestError`. |
| `permissions` | no | list | Declared capability permissions (e.g. `network`, `vault:read`). |
| `always_enabled` | no | bool | If true, the module cannot be disabled via API. Default `false`. |
| `feature_flag` | no | str | Optional FeatureRegistry key that must be enabled before this module can be enabled. Example `bridge_whatsapp`. |
| `config_schema` | no | object | Optional JSON schema for `module.config.json`. |

**Where state lives (honesty).** Toggle state and runtime config are stored on the `Module` database
row (`enabled`, `config`) — not in the filesystem — so enable/disable is real state that survives
restarts. Capsule-level overrides live in `Capsule.persona_config.modules.<name>`
(`manifest.py` module docstring).

### 5.3 KNOWN_HOOKS (8) — live

Only these are registerable today (`hooks.py:33-42`). Registration against any other name raises
`UnknownHookError` (`hooks.py:98-99`). Handler contract: `fn(ctx: dict) -> Any`; a failure in one
handler never breaks the agent loop.

| # | Hook | When it fires |
|---|---|---|
| 1 | `message_loop_start` | before LLM — load channel context |
| 2 | `system_prompt` | prompt build — inject channel/persona |
| 3 | `response_stream` | tokens — TG draft edit / WA typing |
| 4 | `tool_execute_after` | tool done — forward result |
| 5 | `process_chain_end` | turn end — send reply to channel |
| 6 | `monologue_end` | session end — typing cleanup |
| 7 | `job_loop` | worker tick — poll WA/TG/IMAP |
| 8 | `handle_exception` | error — notify channel on failure |

### 5.4 RESERVED_HOOKS (23) — reserved, not yet registerable

Full Annex D.3 list for discoverability (`hooks.py:46-70`). Only KNOWN_HOOKS are registerable; these
names are reported by the API as reserved. **UI rule (binding):** every RESERVED_HOOKS row in any
module/capability UI SHALL render as **"reserved — not yet registerable"**, never as a working
toggle, switch or binder. A reserved hook with an enabled toggle is a compliance failure (N-6).

`agent_init`, `banners`, `before_main_llm_call`, `error_format`, `hist_add_before`,
`hist_add_tool_result`, `message_loop_end`, `message_loop_prompts_before`,
`message_loop_prompts_after`, `message_loop_result`, `monologue_start`, `reasoning_stream`,
`reasoning_stream_chunk`, `reasoning_stream_end`, `response_stream_chunk`, `response_stream_end`,
`startup_migration`, `tool_execute_before`, `user_message_ui`, `util_model_call_before`,
`webui_ws_connect`, `webui_ws_disconnect`, `webui_ws_event`.

### 5.5 The three real Capsule Modules (verified 2026-09-28)

Exactly three module directories exist under `admin/modules/`. All three are channel bridges; all
three declare `settings_sections: [agent, external]`, `permissions: [network, vault:read]`,
`always_enabled: false`.

| Module | Title | `feature_flag` | Manifest |
|---|---|---|---|
| `mod_whatsapp` | WhatsApp Channel — Channel, QR pairing, group/DM context | `bridge_whatsapp` | `admin/modules/mod_whatsapp/module.yaml` |
| `mod_telegram` | Telegram Channel — bot token, webhook/poll, draft typing | `bridge_telegram` | `admin/modules/mod_telegram/module.yaml` |
| `mod_email` | Email Channel — IMAP poll, SMTP send, thread context | `bridge_email` | `admin/modules/mod_email/module.yaml` |

No other Capsule Module directories exist. Do not catalogue `mod_*` names that are not on disk.

---

## 6. Capsule Facets

Source: `services/capsule_export.py` (`CapsuleExport`, `:116-121`, with per-facet dataclasses
`:51-97`). Six facets. Memory is exported as a **pointer, not a payload** (`:79-80`).

| Facet | Export class | What it holds | Binds to settings categories (N-11) | Screen (N-5) |
|---|---|---|---|---|
| **Soul** | `CapsuleSoulExport` | `system_prompt`, `personality_traits`, `neuromodulator_baseline` | `PERSONALITY`, `AGENT` | UI-S-01 |
| **Brain** | `CapsuleBrainExport` | `chat_model`, `image_model`, `voice_model`, `browser_model`, `iq_knobs` | `LLM`, AgentIQ knobs | UI-S-02 |
| **Hands** | `CapsuleHandsExport` | `tool_registry`, `tool_policy` (capabilities live here) | `AGENT`, tool policy | UI-S-03 |
| **Memory** | `CapsuleMemoryPointerExport` | pointer only: `tenant`, `namespace`, `recall_limit`, `similarity_threshold` | `MEMORY` | UI-S-04 |
| **Body** | `CapsuleBodyExport` | `resource_limits` **only** — "capabilities are in hands" (`:90`) | `INFRA`, resource limits | UI-S-05 |
| **Governance** | `CapsuleGovernanceExport` | `constitution_ref`, `registry_signature`, `certified_at` | `GOVERNANCE`, `SECURITY` | UI-S-06 |

Facet-adjacent state also exported on `CapsuleExport`: `neuromodulator_state`, `spec_version`, `id`,
`name`, `version`, `tenant`, `status`, `parent_id`, timestamps.

**Settings-category spine (N-11).** `admin/core/helpers/capsule_settings.py` defines ten categories:
`INFRA`, `SECURITY`, `MEMORY`, `LLM`, `AGENT`, `PERSONALITY`, `UI`, `GOVERNANCE`, `OBSERVABILITY`,
`INTEGRATION`. Resolution order is Capsule persona config → AgentSetting overrides → Django/env →
Vault (N-11 header). Module-injected settings land in the `settings_sections` named by the module
(§5.2), which map onto the Settings screens UI-S-50/51/52/53.

---

## 7. AgentIQ — 3 Knobs → 12 Derived Settings

Sources: `admin/core/agentiq/settings.py` (`DerivedSettings`, `:46-72`),
`admin/core/agentiq/derivation.py` (`derive_all_settings`, `:27-89`),
`admin/core/agentiq/tables.py` (lookup tables). There is no top-level `agentiq/` package; the
implementation lives at `admin/core/agentiq/` (`__init__.py`, `settings.py`, `derivation.py`,
`tables.py`, `unified_gate.py`).

### 7.1 The 3 knobs (editable)

Stored in `capsule.body.persona.knobs`; fallbacks resolved via `resolve_setting`
(`derivation.py:48-65`).

| Knob | Range | Default | Settings key fallback |
|---|---|---|---|
| `intelligence_level` | 1–10 | 5 | `AGENTIQ_INTELLIGENCE_LEVEL` |
| `autonomy_level` | 1–10 | 5 | `AGENTIQ_AUTONOMY_LEVEL` |
| `resource_budget` | $/turn | 0.10 | `AGENTIQ_RESOURCE_BUDGET` |

### 7.2 The 12 derived settings — **READ-ONLY readouts, never editors**

Binding rule (N-6 honesty rules; N-12 §8 / REQ-UIXS-003): the twelve fields below SHALL be rendered
as read-only derived readouts beside the three knobs on UI-S-02 and in the workspace knob strip.
They SHALL NOT be independently editable. Writing a derived field directly is a bug, not a feature.
`DerivedSettings` is a **frozen** Pydantic model (`settings.py:74`), which enforces this in code.

| Knob (editable) | Derived readouts (read-only) | Type / bounds | Source |
|---|---|---|---|
| `intelligence_level` | `temperature` | float, 0.0–1.0 | `settings.py:57`, `tables.py` INTELLIGENCE_TABLE |
| | `max_tokens` | int, 256–16384 | `settings.py:58` |
| | `rlm_iterations` | int, 1–10 | `settings.py:59` |
| | `recall_limit` | int, 1–100 | `settings.py:60` |
| | `model_tier` | `budget \| standard \| premium \| flagship` | `settings.py:61` |
| | `brain_query_enabled` | bool | `settings.py:62` |
| `autonomy_level` | `require_hitl` | bool | `settings.py:65` |
| | `tool_approval` | `all \| dangerous \| none` | `settings.py:66` |
| | `egress_allowed` | `none \| whitelist \| expanded \| unrestricted` | `settings.py:67` |
| `resource_budget` | `token_limit` | int, 1000–200000 | `settings.py:70` |
| | `cost_tier` | `budget \| standard \| premium \| flagship` | `settings.py:71` |
| | `thinking_budget` | int, 0–8192 | `settings.py:72` |

### 7.3 Derivation tables (`tables.py`)

**INTELLIGENCE** (`tables.py:56-89`) — ranges 1-3 / 4-6 / 7-8 / 9-10:

| Level | temperature | max_tokens | rlm_iterations | recall_limit | model_tier | brain_query_enabled |
|---|---|---|---|---|---|---|
| 1–3 | 0.3 | 512 | 1 | 5 | budget | false |
| 4–6 | 0.7 | 2048 | 2 | 15 | standard | true |
| 7–8 | 0.8 | 4096 | 3 | 25 | premium | true |
| 9–10 | 0.9 | 8192 | 5 | 50 | flagship | true |

**AUTONOMY** (`tables.py:94-115`):

| Level | require_hitl | tool_approval | egress_allowed |
|---|---|---|---|
| 1–3 | true | all | none |
| 4–6 | false (dangerous only) | dangerous | whitelist |
| 7–8 | false | none | expanded |
| 9–10 | false | none | unrestricted |

**RESOURCE** (`tables.py:120-141`) — budget $/turn:

| Budget | token_limit | cost_tier | thinking_budget |
|---|---|---|---|
| 0.01–0.10 | 1 000 | budget | 256 |
| 0.10–0.50 | 10 000 | standard | 1 024 |
| 0.50–2.00 | 50 000 | premium | 2 048 |
| 2.00+ | 100 000 | flagship | 4 096 |

### 7.4 UI rule

- The 3 knobs are sliders/editors (L2, agent-owner).
- The 12 derived values are `derived-ro` readouts (N-12 §7 control type). No editor, no reset-to-
  default, no direct write path in the UI. The client-side mirror in `iq-store.ts` is display state
  and MUST NOT be presented as an authority over the server derivation.

---

## 8. Honesty Notes

### 8.1 Measurement provenance

Counts were measured from the working tree on 2026-09-28 and are reproducible:

| Claim | Measurement |
|---|---|
| 56 component files | `ls webui/src/components/*.ts \| wc -l` |
| 54 `@customElement` tags + 1 `customElements.define` (`settings-form`) + 1 barrel (`index.ts`) | `grep -n "@customElement" webui/src/components/*.ts`; `settings-form.ts:709-710` |
| 6 stores / 5 services / 8 controllers | `ls` of each directory |
| 8 KNOWN_HOOKS / 23 RESERVED_HOOKS | `admin/modules/hooks.py:33-42`, `:46-70` |
| 3 Capsule Modules | `ls admin/modules/mod_*` |
| 6 facets | `services/capsule_export.py:116-121` |
| 12 derived settings | `admin/core/agentiq/settings.py:56-72`; `derivation.py:73-89` |

### 8.2 What the code disagreed with, or what must not be overstated

1. **`saas-user-invite-modal.ts` and `saas-voice-overlay.ts` do not exist.** Both were deleted
   2026-09-27 as dead code (zero tag instantiations). Verified absent 2026-09-28. Do not catalogue
   them as live components; reintroduce flows from `SOMA-01-UIUX-002` §4.3 / §5.3.
2. **`saas-glass-modal.ts` is the live Dialog shell**, instantiated in five views. Its header
   comment claims a focus trap the code does not implement (`saas-glass-modal.ts:9` vs `:190-192`).
   Never cite the comment as behaviour.
3. **`saas-admin-feature-flags.ts` imports `saas-glass-modal.js` and never instantiates it** (`:15`).
   Dead import — it is not a sixth Dialog user.
4. **Two transcript components share one concern.** `voice-transcript.ts` (tag `voice-transcript`)
   and `saas-voice-transcript.ts` (tag `saas-voice-transcript`) both exist; `saas-voice-transcript`
   wraps the other. Not a duplicate to delete without checking both consumers.
5. **`settings-form.ts` does not use the `@customElement` decorator**; it registers with
   `customElements.define('settings-form', …)` (`settings-form.ts:709-710`). A `grep` for
   `@customElement` alone undercounts tags by one.
6. **No `agentiq/` top-level package.** The prompt named `agentiq/settings.py` as a possibility; the
   real path is `admin/core/agentiq/`.
7. **RESERVED_HOOKS must never render as working toggles.** 23 reserved names are discoverability
   entries only (`hooks.py:44-45`). UI copy is exactly "reserved — not yet registerable".
8. **Memory is a pointer.** `CapsuleMemoryPointerExport` holds `tenant`, `namespace`,
   `recall_limit`, `similarity_threshold` — never a memory payload. Do not specify a facet screen
   that pretends to export memories from the Capsule.
9. **Body does not hold capabilities.** `CapsuleBodyExport` is `resource_limits` only;
   capabilities are in Hands (`capsule_export.py:90`). Do not invent a Body capabilities table.
10. **Derived AgentIQ settings are read-only.** Twelve readouts, three editors (N-6 honesty rules;
    N-12 REQ-UIXS-003). Never specify an editor for `temperature`, `max_tokens`, `rlm_iterations`,
    `recall_limit`, `model_tier`, `brain_query_enabled`, `require_hitl`, `tool_approval`,
    `egress_allowed`, `token_limit`, `cost_tier`, `thinking_budget`.
11. **Module state is in the database, not the filesystem.** `Module.enabled` / `Module.config` are
    ORM state; `module.yaml` is the contract, not the runtime toggle.
12. **No invented counts.** Every number in this document traces to a measurement or a cited
    `file:line`. Where a screen or component does not exist, this document says so.

End of Document
