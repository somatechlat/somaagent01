# SOMA-01-UIUX-001 — User Interface — Screen & Feature Specification

## Document Control

| Field | Value |
|---|---|
| Document Title | User Interface — Screen & Feature Specification |
| Document Identifier | SOMA-01-UIUX-001 |
| Version | 1.0.0 |
| Date | 2026-09-28 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-28 |
| Related | `SOMA-01-QMS-001.md`, `SOMA-A0-PARITY-001.md`, `docs/design/SOMA-UI-PARITY-002.md`, `SOMA-UI-IDREG-001.md`, `SOMA-UI-TEMPLATE-001.md`, `SOMA-01-UIUX-005.md` |
| Source of truth | This document for every screen and surface; `SOMA-UI-IDREG-001.md` for identifier allocation; `webui/src/main.ts` for route ground truth; code paths cited per row |
| Audience | UI/UX contributors, product engineering, QA, any agent acting on somaAgent01 |
| Scope | Every routable screen (UI-S-00 … UI-S-53) and every right-rail surface (UI-X-01 … UI-X-08) in the somaAgent01 web UI |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-09-28 | SomaTech Engineering | Initial issue. Master screen and feature specification: capsule-first IA, normative requirements REQ-UIX-001…026, screen register of 53 screens and 8 surfaces, full per-screen blocks UI-S-01…53, surface specifications UI-X-01…08 (UI-X-08 GATED), global chrome UI-S-00, honesty notes with file:line defect evidence. |

## Normative References

| ID | Reference | Role |
|---|---|---|
| N-1 | SOMA-01-QMS-001 | Quality management system |
| N-2 | SOMA-01-DOCS-001 | Document control and traceability procedure |
| N-3 | SOMA-A0-PARITY-001 | Feature clone never code clone; Plan Gate; honesty rules |
| N-4 | `SOMA-UI-IDREG-001.md` | Authoritative ID allocation — identifiers used here exactly |
| N-5 | `SOMA-UI-TEMPLATE-001.md` | House ISO template, honesty rules, per-screen block shape |
| N-6 | `docs/design/SOMA-UI-PARITY-002.md` §3 | Capsule-first information architecture (authoritative) |
| N-7 | `services/capsule_export.py` | Six capsule facet export definitions (Soul/Brain/Hands/Memory/Body/Governance) |
| N-8 | `admin/core/models/core.py` | `Capsule` / `CapsuleInstance` / `Capability` domain models |
| N-9 | `admin/modules/hooks.py` | `KNOWN_HOOKS` (8) and `RESERVED_HOOKS` (23) |
| N-10 | `webui/src/main.ts` | SPA router — route ground truth |
| N-11 | ISO 9001:2015 clause 7.5 | Control of documented information |

---

## 1. Purpose and Scope

### 1.1 Purpose

This is the **master document of the UI/UX suite**. It specifies every screen and every surface of
the somaAgent01 web user interface: what each one is for, what regions it has, which controls and
actions it exposes, which states it renders, which features it carries, and how it traces to code.
Every mockup, parity matrix and acceptance-test document in the suite is subordinate to this file.

### 1.2 Capsule-first information architecture

The IA is **capsule-first**. Screens organise by Capsule facet — **Soul / Brain / Hands / Memory /
Body / Governance** — with **Chat as a facet peer**. Around that core sit Capsule lifecycle,
Modules, Platform, Auth, Ops, Voice and Settings.

The authority for this IA is `docs/design/SOMA-UI-PARITY-002.md` §3 ("CAPSULE-FIRST INFORMATION
ARCHITECTURE (authoritative)"). That section states that source of truth is our own model
(`admin/core/models/core.py:109` `Capsule`, `:423` `CapsuleInstance`, `:445` `Capability`,
`admin/modules/hooks.py`, `services/capsule_export.py`), not the Agent Zero screen list. The six
facets are named in code by the six export dataclasses in `services/capsule_export.py`
(`CapsuleSoulExport` :51, `CapsuleBrainExport` :60, `CapsuleHandsExport` :71,
`CapsuleMemoryPointerExport` :79, `CapsuleBodyExport` :89, `CapsuleGovernanceExport` :96).

Facet-to-model binding (all fields measured in `admin/core/models/core.py`):

| Facet | Code fields | Screen |
|---|---|---|
| Soul | `system_prompt` :184, `personality_traits` :185, `neuromodulator_baseline` :189, `learning_config` :191 | UI-S-01 |
| Brain | `chat_model` :201, `image_model` :210, `voice_model` :220, `browser_model` :230 (FK → `LLMModelConfig`) | UI-S-02 |
| Hands | `capabilities` M2M :243, `tool_policy` :267 | UI-S-03 |
| Memory | `memory_pointer` :279 (`tenant`, `namespace`, `recall_limit`, `similarity_threshold`) | UI-S-04 |
| Body | `resource_limits` :317 | UI-S-05 |
| Governance | `constitution` FK :166, `constitution_ref` :173, `registry_signature` :176, `certified_at` :179 | UI-S-06 |

Cross-cutting, not facets: lifecycle `status` (`draft → active → archived`, `core.py:121-129`),
version lineage (`parent`/`children`, `core.py:157-163`), persona knobs
(`persona_config.knobs`, `core.py:254-265`), neuromodulator state (`core.py:292-302`), and runtime
instances (`CapsuleInstance`, `core.py:423-437`). Chat is a **peer of the facets**
(`SOMA-UI-PARITY-002.md` §3.3): the capsule being spoken through is always named in the chrome.

### 1.3 Scope boundary

In scope: UI-S-00 global chrome; UI-S-01 … UI-S-53 routable screens; UI-X-01 … UI-X-08 right-rail
surfaces; the identifier scheme and per-screen block shape; normative requirements REQ-UIX-*;
tracked honesty findings for known defects.

Out of scope: visual design tokens (owned by the mockup documents), modal contracts (UI-M-01 …
UI-M-03 are owned by `SOMA-01-UIUX-002`), acceptance-test identifiers (UIX-AT-* are owned by
`SOMA-01-UIUX-004`), and any production-code change. **This document does not change code.**
Defects are recorded as findings, not fixed here.

---

## 2. Conventions

### 2.1 Identifier scheme

Identifiers are allocated in `SOMA-UI-IDREG-001.md` and MUST be used exactly as
allocated. Ranges are exclusive per owner document and MUST NOT collide.

| Kind | Range | Meaning | Owner |
|---|---|---|---|
| `UI-S-*` | 00–53 | Routable screen (00 = global chrome) | this document |
| `UI-X-*` | 01–08 | Right-rail surface | this document |
| `UI-M-*` | 01–03 | Modal pattern (Drawer / Full-screen / Dialog) | `SOMA-01-UIUX-002` |
| `UI-C-*` | 001–120 | Control (one table row per control) | this document |
| `UI-A-*` | 001–120 | Action (one table row per action) | this document |
| `UI-F-*` | 001–080 | Feature (one bullet per feature) | this document |
| `REQ-UIX-*` | 001–060 | Normative requirement | this document |
| `UIX-AT-*` | 01–40 | Acceptance test | `SOMA-01-UIUX-004` |

Allocation in this issue (no collisions): `UI-C-001` … `UI-C-119`, `UI-A-001` … `UI-A-120`,
`UI-F-001` … `UI-F-070`, `REQ-UIX-001` … `REQ-UIX-026`. Remaining headroom is reserved for
revision; identifiers are never reused or renumbered.

### 2.2 Per-screen block shape

Every screen block uses the exact shape from `SOMA-UI-TEMPLATE-001.md`:

```
### UI-S-<nn> — <Screen name>
| Field | Value |   (Screen Identifier, Route, Facet, Primary actor, Stores, APIs, Related)
**Purpose.** one sentence
**Regions.** left rail / workspace / right rail
**Controls.** table: UI-C-* | control | type | default | validation | disabled-when | disabled-reason
**Actions.**  table: UI-A-* | action | trigger | effect | confirmation | undo
**States.** loading | empty | error | permission-denied | offline — verbatim copy
**Features.** UI-F-* list
**Trace.** components | API | UIX-AT-*
**Honesty notes.** what must NOT be faked here
```

### 2.3 Honesty vocabulary

- A disabled control states its **blocking reason**. The string "coming soon" is forbidden as a
  specification value.
- Every control row carries `disabled-when` and `disabled-reason`. `disabled-when: never` with
  `disabled-reason: —` is the encoding for an always-enabled control.
- Secrets render as a masked placeholder plus "rotate in Vault" — never a value.
- Derived AgentIQ settings (`temperature`, `max_tokens`, `rlm_iterations`, `recall_limit`,
  `model_tier`, `brain_query_enabled`, `require_hitl`, `tool_approval`, `egress_allowed`,
  `token_limit`, `cost_tier`, `thinking_budget`) are **READ-ONLY** readouts beside the three
  persona knobs. They are never editable. Names confirmed in
  `webui/src/stores/iq-store.ts:15-28` (`DerivedSettings`).
- Code claims cite `file:line`. Measured counts are stated as measured, not rounded.
- `UIX-AT-*` in a Trace row points to the acceptance-test owner document (`SOMA-01-UIUX-004`);
  this document does not allocate UIX-AT identifiers.

### 2.4 Route notation

Route values are the specification target from `SOMA-UI-IDREG-001.md`. `NEW` means the screen is
specified but has no router branch today. Where the current router disagrees with the register,
the per-screen Honesty notes give the measured `webui/src/main.ts` line and the disagreement is
restated in §8. Nothing is silently renumbered or silently re-routed.

---

## 3. Normative requirements

Requirements use SHALL / SHALL NOT. Priority: P1 = blocking for UI/UX suite acceptance,
P2 = required before general availability, P3 = required before the next major revision.

| ID | Requirement | Priority | Source | Verification |
|---|---|---|---|---|
| REQ-UIX-001 | The information architecture SHALL organise screens by Capsule facet (Soul / Brain / Hands / Memory / Body / Governance) with Chat as a facet peer, plus Capsule lifecycle, Modules, Platform, Auth, Ops, Voice and Settings. | P1 | `docs/design/SOMA-UI-PARITY-002.md` §3; N-6 | Screen register §4 facet column reviewed against §3.1 |
| REQ-UIX-002 | Every screen, surface, control, action, feature and requirement SHALL use the identifier allocated in `SOMA-UI-IDREG-001.md` exactly. Identifiers SHALL NOT be renumbered or reused. | P1 | N-4 | ID audit of this document against `SOMA-UI-IDREG-001.md` |
| REQ-UIX-003 | Every screen block SHALL use the per-screen block shape of `SOMA-UI-TEMPLATE-001.md` with all eight fields present. | P1 | N-5 | `scripts/check_docs.py` plus shape review of §5–§7 |
| REQ-UIX-004 | Specifications SHALL NOT use the banned placeholder phrase defined in §2.3 as a value. A disabled control SHALL state its blocking reason inline. | P1 | N-3; N-5 | Grep of screen and surface specifications for the banned placeholder phrase (the single rule-text definition in §2.3 is exempt) |
| REQ-UIX-005 | Every control row SHALL carry `disabled-when` and `disabled-reason`. A disabled control with no reason is a compliance failure. | P1 | N-5 | Controls tables in §5–§7 |
| REQ-UIX-006 | Secrets SHALL be shown as a masked placeholder plus the instruction "rotate in Vault". A secret value SHALL NOT appear in any screen specification. | P1 | N-5 | UI-S-35, UI-S-53 controls; suite grep |
| REQ-UIX-007 | Surface UI-X-08 (desktop) SHALL be marked GATED with blocking reason exactly "Requires a remote-desktop capability in somaAgent01. Not available today." Its controls SHALL render present-but-disabled with that reason printed inline. | P1 | N-5; `SOMA-UI-IDREG-001.md` UI-X-08 | §6 UI-X-08 block |
| REQ-UIX-008 | The twelve derived AgentIQ settings SHALL render as READ-ONLY readouts beside the three persona knobs and SHALL NOT be editable on any screen. | P1 | N-5; `webui/src/stores/iq-store.ts:15-28` | UI-S-00 UI-F-002; UI-S-02 |
| REQ-UIX-009 | Hook names in `RESERVED_HOOKS` SHALL render as "reserved — not yet registerable". Only `KNOWN_HOOKS` (8) MAY render as registerable toggles. | P1 | `admin/modules/hooks.py:33-42`, `:46-70`; N-9 | UI-S-18 controls and honesty notes |
| REQ-UIX-010 | Neuromodulator meters (dopamine, serotonin, norepinephrine, acetylcholine) SHALL be read-only and SHALL display `last_synced_at`. No meter value SHALL render without a real sync timestamp. | P1 | `admin/core/models/core.py:292-302`; N-8 | UI-S-00 UI-C-010…013 |
| REQ-UIX-011 | Capsule lifecycle transitions (`draft → active → archived`) SHALL be explicit actions. No screen SHALL change lifecycle implicitly as a side effect of a save. | P1 | `admin/core/models/core.py:121-129` | UI-S-00 UI-A-002; UI-S-11 |
| REQ-UIX-012 | Editing a Capsule SHALL spawn a new version (`parent` lineage). In-place mutation of an active Capsule SHALL NOT be offered. | P1 | `admin/core/models/core.py:157-163`; N-6 §3.1 | UI-S-12 UI-A-029 |
| REQ-UIX-013 | The version chip in global chrome SHALL show the `Capsule.version` string of the selected Capsule and SHALL update on capsule switch. | P2 | `admin/core/models/core.py:133` | UI-S-00 UI-C-002 |
| REQ-UIX-014 | Every claim about current code SHALL cite `file:line`. Counts SHALL be measured, not assumed. | P1 | N-3 | §8 findings; Trace rows |
| REQ-UIX-015 | A screen whose route is not matched by `webui/src/main.ts` SHALL be marked `NEW` in the register and SHALL NOT be described as reachable. | P1 | N-10 | §4 route column; §8 finding H-05 |
| REQ-UIX-016 | Logout SHALL terminate the server session and clear the session cookie that `checkAuth()` reads. Client-side-only logout is a security defect and SHALL be tracked as a finding until fixed. | P1 | `webui/src/main.ts:342-347`, `:36-43` | §8 finding H-04 |
| REQ-UIX-017 | Unreachable route branches in the router SHALL be tracked as findings with `file:line` evidence and SHALL NOT be presented as live screens. | P1 | N-10 | §8 findings H-01…H-03 |
| REQ-UIX-018 | A placeholder redirect SHALL be reported as a placeholder redirect, with the redirect target named. | P2 | `webui/src/main.ts:438-443` | §8 finding H-06 |
| REQ-UIX-019 | Overlays SHALL use only the three modal patterns UI-M-01 (Drawer), UI-M-02 (Full-screen), UI-M-03 (Dialog). A fourth pattern SHALL NOT be introduced. | P2 | N-4; N-6 §4.4 | `SOMA-01-UIUX-002` |
| REQ-UIX-020 | A surface that is not available SHALL render present-but-disabled with its blocking reason. It SHALL NOT be omitted from the surface rail. | P1 | N-5 | §6; UI-S-00 UI-C-014 |
| REQ-UIX-021 | The three persona knobs (`intelligence_level`, `autonomy_level`, `resource_budget`) SHALL be the only editable AgentIQ inputs in global chrome. | P1 | `admin/core/models/core.py:258-260`; N-6 §3.1 | UI-S-00 UI-C-004…006 |
| REQ-UIX-022 | Global chrome SHALL expose facet tabs for the six facets and SHALL treat Chat as a peer of those tabs, not as a child. | P1 | N-6 §3.3 | UI-S-00 UI-C-008 |
| REQ-UIX-023 | The instance strip SHALL render real `CapsuleInstance` state (`session_id`, `status`, `started_at`, `completed_at`) and SHALL NOT synthesise instance rows. | P1 | `admin/core/models/core.py:423-437` | UI-S-00 UI-C-009; UI-S-14 |
| REQ-UIX-024 | The `permission-denied` state SHALL name the missing permission or role. A generic "forbidden" without a named capability SHALL NOT be used. | P2 | N-3 | States rows in §5 |
| REQ-UIX-025 | The `offline` state SHALL label data as stale and SHALL NOT fabricate or extrapolate values. | P1 | N-3 | States rows in §5 |
| REQ-UIX-026 | Module hook bindings SHALL be shown against `KNOWN_HOOKS` only; a reserved hook name SHALL NOT be offered as a working toggle. | P1 | `admin/modules/hooks.py:98-99` (`UnknownHookError`) | UI-S-18; UI-S-16 |

---

## 4. Screen register

Index of all 53 screens and 8 surfaces. Route is the specification target from
`SOMA-UI-IDREG-001.md`; `NEW` = specified, not routed today. Full blocks are in §5; surfaces in §6;
chrome in §7.

### 4.1 Screens UI-S-01 … UI-S-53

| ID | Screen | Facet | Route (spec) | Source view |
|---|---|---|---|---|
| UI-S-01 | Soul — persona & system prompt | Soul | NEW | saas-capsule-editor |
| UI-S-02 | Brain — model & IQ | Brain | /cognitive | saas-cognitive-panel |
| UI-S-03 | Hands — tools & capabilities | Hands | /tools | saas-feature-catalog |
| UI-S-04 | Memory — retention & recall | Memory | /memory | saas-memory-view |
| UI-S-05 | Body — resources & limits | Body | NEW | NEW |
| UI-S-06 | Governance — constitution & hooks | Governance | NEW | NEW |
| UI-S-07 | Chat workspace | Chat | /chat | saas-chat |
| UI-S-08 | Message detail | Chat | /chat/:id | saas-chat |
| UI-S-09 | Conversation export | Chat | NEW | NEW |
| UI-S-10 | Conversation queue | Chat | NEW | NEW |
| UI-S-11 | Capsule list | Capsule | /workspace | saas-workspace |
| UI-S-12 | Capsule editor | Capsule | /workspace/:id | saas-workspace |
| UI-S-13 | Version rail & diff | Capsule | NEW | NEW |
| UI-S-14 | Instances | Capsule | NEW | NEW |
| UI-S-15 | Module list | Module | NEW | NEW |
| UI-S-16 | Module detail & config | Module | NEW | NEW |
| UI-S-17 | Capability registry | Module | NEW | NEW |
| UI-S-18 | Capability detail & hook bindings | Module | NEW | NEW |
| UI-S-19 | Tenants | Platform | /saas/tenants | saas-tenants |
| UI-S-20 | Tenant wizard | Platform | /saas/tenants/new | saas-tenant-wizard |
| UI-S-21 | Tenant dashboard | Platform | /admin/dashboard | saas-tenant-dashboard |
| UI-S-22 | Users | Platform | /admin/users | saas-users-view |
| UI-S-23 | Roles & role matrix | Platform | /platform/roles | saas-admin-roles-list |
| UI-S-24 | Permissions | Platform | /saas/permissions | saas-permissions |
| UI-S-25 | Billing | Platform | /admin/billing | saas-tenant-billing |
| UI-S-26 | Subscriptions | Platform | /saas/subscriptions | saas-subscriptions |
| UI-S-27 | Usage analytics | Platform | /platform/usage | saas-usage-analytics |
| UI-S-28 | Tier builder | Platform | /platform/tiers | saas-tier-builder |
| UI-S-29 | Login | Auth | /login | saas-login |
| UI-S-30 | Register | Auth | /register | saas-register |
| UI-S-31 | Forgot password | Auth | /forgot-password | saas-forgot-password |
| UI-S-32 | MFA setup | Auth | /mfa/setup | saas-mfa-setup |
| UI-S-33 | Auth callback | Auth | /auth/callback | saas-auth-callback |
| UI-S-34 | Personal profile | Auth | /profile | saas-personal-profile |
| UI-S-35 | Platform profile | Auth | /admin/profile | saas-platform-profile |
| UI-S-36 | Mode selection | Auth | /mode-select | saas-mode-selection |
| UI-S-37 | Platform dashboard | Ops | /saas/dashboard | saas-platform-dashboard |
| UI-S-38 | Platform metrics | Ops | /platform/metrics | platform-metrics-dashboard |
| UI-S-39 | Infrastructure dashboard | Ops | /platform/infrastructure | saas-infrastructure-dashboard |
| UI-S-40 | Rate limits | Ops | /platform/infrastructure/redis/ratelimits | saas-rate-limits |
| UI-S-41 | Integrations dashboard | Ops | /platform/integrations | saas-integrations-dashboard |
| UI-S-42 | Marketplace | Ops | /platform/marketplace | saas-marketplace |
| UI-S-43 | Audit dashboard | Ops | /platform/audit | saas-audit-dashboard |
| UI-S-44 | Audit log | Ops | /audit | saas-audit-log |
| UI-S-45 | Agent metrics | Ops | /admin/metrics | saas-agent-metrics |
| UI-S-46 | Voice chat | Voice | /voice/chat | saas-voice-chat |
| UI-S-47 | Voice sessions | Voice | /voice/sessions | saas-voice-sessions |
| UI-S-48 | Voice personas | Voice | /voice/personas | saas-voice-personas |
| UI-S-49 | Multimodal settings | Voice | /settings/multimodal | saas-multimodal-settings |
| UI-S-50 | Settings — Agent | Settings | /settings | saas-settings |
| UI-S-51 | Settings — Models | Settings | /settings/models | saas-settings-models |
| UI-S-52 | Settings — Channels | Settings | /settings/channels | saas-settings-channels |
| UI-S-53 | Settings — External & Developer | Settings | NEW | NEW |

### 4.2 Surfaces UI-X-01 … UI-X-08

| ID | Surface | Facet | State | Blocking reason when gated |
|---|---|---|---|---|
| UI-X-01 | Files | Capsule | specified | — |
| UI-X-02 | Tools | Hands | specified | — |
| UI-X-03 | Browser | Brain | specified | — |
| UI-X-04 | Editor | Soul | specified | — |
| UI-X-05 | Debug | Governance | specified | — |
| UI-X-06 | Capsule | Capsule | specified | — |
| UI-X-07 | Brain | Brain | specified | — |
| UI-X-08 | Desktop | Body | GATED | Requires a remote-desktop capability in somaAgent01. Not available today. |

### 4.3 Register counts (measured)

| Item | Count | Evidence |
|---|---|---|
| Routable screens specified | 53 | `SOMA-UI-IDREG-001.md` UI-S-01…53 |
| Surfaces specified | 8 | `SOMA-UI-IDREG-001.md` UI-X-01…08 |
| Screens with an existing route branch | 45 | `webui/src/main.ts` (see per-screen Trace) |
| Screens marked `NEW` | 8 | UI-S-01, 05, 06, 09, 10, 13, 14, 15, 16, 17, 18, 53 — see §8 H-05 for the route reality of UI-S-12 |
| `webui/src/views/*.ts` files | 55 | measured 2026-09-28, including `index.ts` |
| `webui/src/components/*.ts` files | 56 | measured 2026-09-28, including `index.ts` |
| `webui/src/stores/*.ts` | 6 | `activity-store`, `agent-store`, `brain-store`, `composer-store`, `iq-store`, `workspace-store` |
| `webui/src/services/*.ts` | 5 | `api-client`, `google-auth-service`, `keycloak-service`, `theme-boot`, `websocket-client` |
| `webui/src/controllers/*.ts` | 8 | billing, infra-dashboard, platform-dashboard, subscriptions, tenant-billing, tenant-settings, tenant-wizard, voice-chat |

Note on "Screens marked NEW": 12 screens carry `NEW` as their route. UI-S-12 carries the register
route `/workspace/:id` but that path is **not** matched by the current router — see §8 H-05.

---

## 5. Per-screen specification (UI-S-01 … UI-S-53)

Block shape per `SOMA-UI-TEMPLATE-001.md` §"Per-screen block shape". Facet values are the closed set
from that template. Global chrome (UI-S-00) surrounds every block and is specified in §7.

### UI-S-01 — Soul — persona & system prompt

| Field | Value |
|---|---|
| Screen Identifier | UI-S-01 |
| Route | NEW |
| Facet | Soul |
| Primary actor | Capsule author |
| Stores | `agent-store` (`webui/src/stores/agent-store.ts`) |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`); per-endpoint shapes not asserted in this document |
| Related | UI-M-01, UI-C-015, UI-C-016, UI-C-017, UI-A-007, UI-A-008, UI-F-006 |

**Purpose.** Write the Capsule's instruction set and cognitive identity: system prompt, Big-5
personality traits, neuromodulator baseline and learning hyperparameters.

**Regions.** left rail = capsule switcher context; workspace = prompt editor + trait panel +
learning config; right rail = prompt provenance stack (UI-X-04 Editor).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-015 | system_prompt | multiline editor | `""` (`core.py:184`) | non-empty for `active` status | capsule status is `active` | Active capsules are immutable; edit spawns a child version (REQ-UIX-012) |
| UI-C-016 | personality_traits (Big-5) | 5 sliders, 0.0–1.0 | `{}` (`core.py:185`) | each trait within 0.0–1.0 | capsule status is `active` | Active capsules are immutable; edit spawns a child version (REQ-UIX-012) |
| UI-C-017 | learning_config (GMD η/λ/α + reward thresholds) | JSON form | `{}` (`core.py:191`) | numeric η/λ/α; thresholds numeric | capsule status is `active` | Active capsules are immutable; edit spawns a child version (REQ-UIX-012) |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-007 | Save soul fields | Save button | persist to Capsule draft fields | none | discard-draft (UI-M-03 only when dirty) |
| UI-A-008 | Reset soul to parent version | Reset button | copy `parent` values into the draft | UI-M-03 destructive confirm | none — re-enter values |

**States.** loading — "Loading soul…"; empty — "No system prompt yet. Write the instruction set."; error — "Could not load the soul. Retry."; permission-denied — "You need `capsule:write` to edit the soul."; offline — "Offline — edits are not saved. Values shown may be stale."

**Features.** UI-F-006.

**Trace.** `webui/src/components/saas-capsule-editor.ts`, `admin/core/models/core.py:184-194`, `services/capsule_export.py:51-57`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Do not fabricate trait descriptions that imply measured psychology — the Big-5 values are author-set floats (`core.py:185-187`). Do not show a save success without the API round-trip. `neuromodulator_baseline` is a *baseline*; live state belongs to UI-S-00 meters (§7), never here.

---

### UI-S-02 — Brain — model & IQ

| Field | Value |
|---|---|
| Screen Identifier | UI-S-02 |
| Route | /cognitive |
| Facet | Brain |
| Primary actor | Capsule author |
| Stores | `iq-store` (`webui/src/stores/iq-store.ts`), `brain-store` |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-018, UI-C-019, UI-A-009, UI-A-010, UI-F-007, UI-X-07 |

**Purpose.** Bind the four model roles from configured models only and read the IQ knobs and
their twelve derived AgentIQ settings.

**Regions.** left rail = capsule context; workspace = four model-role binders + IQ knob panel;
right rail = Brain surface (UI-X-07) live readouts.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-018 | model-role binder (chat / image / voice / browser) | 4 FK pickers → `LLMModelConfig` | `null` chat permitted in draft (`core.py:204`) | value must be a configured model | no configured model of that role exists | No configured model available for this role |
| UI-C-019 | iq_knobs + derived readouts | 3 knobs (editable) + 12 readouts (read-only) | intelligence 7, autonomy 5, budget 0.05 (`iq-store.ts:35-39`) | knobs 1–10, budget 0.01–1.00 | never (knobs); derived are never editable | Derived AgentIQ settings are computed, not authored (REQ-UIX-008) |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-009 | Bind model role | picker change | set `chat_model` / `image_model` / `voice_model` / `browser_model` FK | none | re-bind previous model |
| UI-A-010 | Verify model binding | Verify button | request model availability check | none | none — read-only probe |

**States.** loading — "Loading model bindings…"; empty — "No models configured. Bind a model to talk."; error — "Model binding could not be saved."; permission-denied — "You need `capsule:write` to change model roles."; offline — "Offline — model list may be stale."

**Features.** UI-F-007.

**Trace.** `webui/src/views/saas-cognitive-panel.ts`, `webui/src/stores/iq-store.ts:9-28`, `admin/core/models/core.py:201-237`, `services/capsule_export.py:60-69`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** The twelve derived settings are NEVER editable (N-5). Do not invent model metrics. Knob names in the store (`intelligence`, `autonomy`, `budget`, `iq-store.ts:9-13`) differ from the model keys (`intelligence_level`, `autonomy_level`, `resource_budget`, `core.py:259`) — the UI labels follow the model keys; the disagreement is tracked in §8 H-07.

---

### UI-S-03 — Hands — tools & capabilities

| Field | Value |
|---|---|
| Screen Identifier | UI-S-03 |
| Route | /tools |
| Facet | Hands |
| Primary actor | Capsule author |
| Stores | `agent-store` |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-020, UI-C-021, UI-A-011, UI-A-012, UI-F-008, UI-X-02 |

**Purpose.** Attach and detach capabilities and place each tool into one of three policy buckets.

**Regions.** left rail = capsule context; workspace = capability catalogue + policy buckets;
right rail = Tools surface (UI-X-02).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-020 | capability list (`capabilities` M2M) | checkbox list grouped by `category` | enabled capabilities only (`core.py:365`) | capability must exist and `is_enabled` | capability `is_enabled` is false (`core.py:476`) | Capability is disabled in the registry |
| UI-C-021 | tool_policy buckets | 3-bucket drag list | `auto_execute` / `approval_required` / `denied` (`core.py:267-277`) | every attached tool in exactly one bucket | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-011 | Attach / detach capability | checkbox | add or remove M2M link | none | re-check to restore |
| UI-A-012 | Move tool between policy buckets | drag or menu | rewrite `tool_policy` lists | none | move back |

**States.** loading — "Loading capabilities…"; empty — "No capabilities registered."; error — "Capability list could not be loaded."; permission-denied — "You need `capsule:write` to change tools."; offline — "Offline — policy changes are not saved."

**Features.** UI-F-008.

**Trace.** `webui/src/views/saas-feature-catalog.ts` (routed at `webui/src/main.ts:432`), `admin/core/models/core.py:243-248`, `:267-277`, `:445-489`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** `/tools` currently renders `saas-feature-catalog` (`webui/src/main.ts:432-435`), which is the platform feature catalogue, not a capsule-scoped Hands editor. The Hands editor is specified here; the current route is a partial stand-in and is tracked in §8 H-08. Never show a tool as auto-executable when it sits in `denied`.

---

### UI-S-04 — Memory — retention & recall

| Field | Value |
|---|---|
| Screen Identifier | UI-S-04 |
| Route | /memory |
| Facet | Memory |
| Primary actor | Capsule author |
| Stores | `agent-store` |
| APIs | REST `/api/v2/memory/` (measured in `webui/src/`); `/api/v2/memory/forget` |
| Related | UI-C-022, UI-C-023, UI-A-013, UI-A-014, UI-F-009 |

**Purpose.** Point the Capsule at a memory namespace and preview live recall against real hits only.

**Regions.** left rail = capsule context; workspace = memory_pointer form + recall preview;
right rail = Files surface (UI-X-01) for namespace context.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-022 | memory_pointer form | text + number fields | `tenant`, `namespace`, `recall_limit`, `similarity_threshold` (`core.py:279-290`) | namespace non-empty; recall_limit ≥ 1; threshold 0.0–1.0 | capsule status is `active` | Active capsules are immutable; edit spawns a child version (REQ-UIX-012) |
| UI-C-023 | recall preview | result list | empty | query must be sent to a real backend | never (preview is read-only) | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-013 | Set memory pointer | Save button | write `memory_pointer` | none | re-edit fields |
| UI-A-014 | Run recall preview | Preview button | fetch real hits only | none | none — read-only |

**States.** loading — "Searching memory…"; empty — "No memories matched this query."; error — "Recall failed. The memory service did not answer."; permission-denied — "You need `memory:read` to preview recall."; offline — "Offline — recall requires a live memory service."

**Features.** UI-F-009.

**Trace.** `webui/src/views/saas-memory-view.ts` (routed at `webui/src/main.ts:402-412`), `admin/core/models/core.py:279-290`, `services/capsule_export.py:79-87`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** The recall preview MUST show only real hits. Synthetic or illustrative memories are forbidden (N-3). Empty is a valid honest result and MUST NOT be filled with sample rows. `memory_config` is disabled in the model (`core.py:308-315`) — do not offer a MemoryConfig picker.

---

### UI-S-05 — Body — resources & limits

| Field | Value |
|---|---|
| Screen Identifier | UI-S-05 |
| Route | NEW |
| Facet | Body |
| Primary actor | Capsule author / operator |
| Stores | `agent-store` |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-024, UI-C-025, UI-A-015, UI-A-016, UI-F-010 |

**Purpose.** Set resource ceilings for the Capsule and observe instance consumption when running.

**Regions.** left rail = capsule context; workspace = resource_limits form + consumption readout;
right rail = Debug surface (UI-X-05).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-024 | resource_limits form | numeric fields (wall clock, concurrency) | `{}` (`core.py:317`) | positive integers | capsule status is `active` | Active capsules are immutable; edit spawns a child version (REQ-UIX-012) |
| UI-C-025 | instance consumption readout | read-only table | empty | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-015 | Save resource limits | Save button | write `resource_limits` | none | re-edit fields |
| UI-A-016 | Inspect consumption | row select | open Drawer (UI-M-01) with instance detail | none | close drawer |

**States.** loading — "Loading resource limits…"; empty — "No resource limits set."; error — "Limits could not be saved."; permission-denied — "You need `capsule:write` to set limits."; offline — "Offline — consumption figures may be stale."

**Features.** UI-F-010.

**Trace.** no dedicated view today; model fields at `admin/core/models/core.py:317`, export at `services/capsule_export.py:89-94`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Consumption figures MUST come from real `CapsuleInstance` records (`core.py:423-437`). Do not interpolate or estimate. `CapsuleBodyExport` holds resource limits only — capabilities belong to Hands (`services/capsule_export.py:90`).

---

### UI-S-06 — Governance — constitution & hooks

| Field | Value |
|---|---|
| Screen Identifier | UI-S-06 |
| Route | NEW |
| Facet | Governance |
| Primary actor | Governance officer |
| Stores | `agent-store` |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-026, UI-C-027, UI-A-017, UI-A-018, UI-F-011, UI-F-067, UI-X-05 |

**Purpose.** Bind a Constitution to the Capsule and show cryptographic certification state.

**Regions.** left rail = capsule context; workspace = constitution binder + certification panel;
right rail = Debug surface (UI-X-05) for hook bindings.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-026 | constitution binder | FK picker → `Constitution` | `null` (`core.py:166-172`) | constitution must exist | capsule status is `active` | Active capsules are immutable; edit spawns a child version (REQ-UIX-012) |
| UI-C-027 | certification panel | read-only signature block | `registry_signature` empty (`core.py:176-181`) | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-017 | Bind constitution | picker change | set `constitution` FK and `constitution_ref` | none | unbind (destructive — UI-M-03) |
| UI-A-018 | Certify capsule | Certify button | request Ed25519 `registry_signature` and `certified_at` | UI-M-03 destructive confirm | none — re-certification required |

**States.** loading — "Loading governance state…"; empty — "No constitution bound."; error — "Certification request failed."; permission-denied — "You need `governance:certify` to certify a capsule."; offline — "Offline — certification requires the registry authority."

**Features.** UI-F-011, UI-F-067.

**Trace.** no dedicated view today; `admin/core/models/core.py:166-181`, `:410-416`, `services/capsule_export.py:96-103`, `:559-571`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Signature and checksum values are shown as hex digests actually returned by the authority — never a placeholder that looks like a signature. OPA policies and SpiceDB relations are read from `persona_config.governance` (`core.py:410-416`); do not invent policy documents. Reserved hooks belong to UI-S-18, not here.

---

### UI-S-07 — Chat workspace

| Field | Value |
|---|---|
| Screen Identifier | UI-S-07 |
| Route | /chat |
| Facet | Chat |
| Primary actor | End user |
| Stores | `composer-store`, `activity-store` |
| APIs | WebSocket `/ws/v2/chat/` and `/ws/v2/chat/:id` (measured in `webui/src/`); REST `/api/v2/chat/conversations/{id}/messages` |
| Related | UI-C-028, UI-C-029, UI-C-030, UI-A-019, UI-A-020, UI-F-012, UI-X-01, UI-X-02 |

**Purpose.** The hero surface: hold a conversation through the selected Capsule, with composer,
message stream and capsule context always visible.

**Regions.** left rail = navigation; workspace = chat topbar + message list + composer; right rail =
surfaces (UI-X-01…08).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-028 | composer | textarea + mic + attachments | empty | non-empty before send | no capsule selected | Select a capsule to chat |
| UI-C-029 | message list | scroll list | empty | never | never | — |
| UI-C-030 | chat topbar | capsule identity + session controls | current capsule | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-019 | Send message | Enter / Send | emit on `/ws/v2/chat/:id` | none | delete message (visible tombstone) |
| UI-A-020 | Branch conversation | message action menu | create branch from a message | none | switch branch |

**States.** loading — "Connecting to the conversation…"; empty — "No messages yet. Start the conversation."; error — "The conversation socket closed. Reconnect."; permission-denied — "You need `chat:write` to send messages."; offline — "Offline — messages will not send until the connection returns."

**Features.** UI-F-012.

**Trace.** `webui/src/views/saas-chat.ts`, `webui/src/components/saas-chat-workspace.ts`, `saas-composer.ts`, `saas-message.ts`, `webui/src/stores/composer-store.ts`; routed at `webui/src/main.ts:390-394`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Home `/` also renders `saas-chat` (`webui/src/main.ts:93-97`). Do not show typing indicators or delivery ticks that are not backed by a socket event. Do not fabricate assistant text while a request is in flight — show a streaming placeholder labelled as in-flight.

---

### UI-S-08 — Message detail

| Field | Value |
|---|---|
| Screen Identifier | UI-S-08 |
| Route | /chat/:id |
| Facet | Chat |
| Primary actor | End user / auditor |
| Stores | `activity-store` |
| APIs | REST `/api/v2/chat/conversations/{id}/messages`; WebSocket `/ws/v2/chat/:id` |
| Related | UI-C-031, UI-C-032, UI-A-021, UI-A-022, UI-F-013 |

**Purpose.** Inspect a single message: payload, metadata and its position in the branch tree.

**Regions.** left rail = navigation; workspace = message payload viewer + meta panel; right rail =
Debug surface (UI-X-05) for raw frames.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-031 | message payload viewer | rendered + raw tabs | selected message | never | never | — |
| UI-C-032 | message meta panel | definition list | selected message meta | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-021 | Copy message | Copy button | copy raw text to clipboard | none | none — clipboard |
| UI-A-022 | Jump to branch point | meta link | navigate to parent message | none | back navigation |

**States.** loading — "Loading message…"; empty — "No message selected."; error — "Message could not be loaded."; permission-denied — "You need `chat:read` to view this message."; offline — "Offline — showing cached message, which may be stale."

**Features.** UI-F-013.

**Trace.** `webui/src/views/saas-chat.ts` (same element as UI-S-07; `path.startsWith('/chat/')` at `webui/src/main.ts:390`), `webui/src/components/saas-message.ts`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** `/chat/:id` shares `saas-chat` with UI-S-07 — there is no separate detail element today. Do not claim a dedicated detail route that the router does not have.

---

### UI-S-09 — Conversation export

| Field | Value |
|---|---|
| Screen Identifier | UI-S-09 |
| Route | NEW |
| Facet | Chat |
| Primary actor | End user / auditor |
| Stores | `activity-store` |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-033, UI-C-034, UI-A-023, UI-A-024, UI-F-014 |

**Purpose.** Export a conversation to a file the user can keep.

**Regions.** left rail = navigation; workspace = export scope + format form; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-033 | export scope selector | radio: this message / branch / whole conversation | whole conversation | at least one scope | no messages in scope | Nothing to export in this scope |
| UI-C-034 | export format selector | select: JSON / Markdown | JSON | format supported by the exporter | format not implemented by the exporter | Format not supported by the exporter today |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-023 | Start export | Export button | request export job | none | cancel job while pending |
| UI-A-024 | Download export | Download button | save file to the client | none | none — file written |

**States.** loading — "Preparing export…"; empty — "No messages to export."; error — "Export failed."; permission-denied — "You need `chat:export` to export conversations."; offline — "Offline — export requires the server."

**Features.** UI-F-014.

**Trace.** no dedicated view today; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Do not offer a format the exporter cannot produce — a format option with no backend is a fake control (REQ-UIX-004). Do not claim end-to-end encryption or retention guarantees that the code does not implement.

---

### UI-S-10 — Conversation queue

| Field | Value |
|---|---|
| Screen Identifier | UI-S-10 |
| Route | NEW |
| Facet | Chat |
| Primary actor | End user |
| Stores | `composer-store` |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-035, UI-C-036, UI-A-025, UI-A-026, UI-F-015 |

**Purpose.** Queue messages while a turn is in flight and manage what will be sent next.

**Regions.** left rail = navigation; workspace = queue list + queue controls; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-035 | queue list | ordered list | empty | never | never | — |
| UI-C-036 | queue controls | pause / resume / clear | resumed | never | no queued items | No queued items to control |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-025 | Enqueue message | composer while busy | append to queue | none | dequeue |
| UI-A-026 | Cancel queued message | row action | remove from queue | none | re-enqueue by retyping |

**States.** loading — "Loading queue…"; empty — "Queue is empty."; error — "Queue state unavailable."; permission-denied — "You need `chat:write` to queue messages."; offline — "Offline — queued messages will not send."

**Features.** UI-F-015.

**Trace.** no dedicated view today; `webui/src/stores/composer-store.ts`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Queue depth MUST reflect real client state. Do not simulate queued items. Pausing the queue is client-side only — say so.

---

### UI-S-11 — Capsule list

| Field | Value |
|---|---|
| Screen Identifier | UI-S-11 |
| Route | /workspace |
| Facet | Capsule |
| Primary actor | Capsule author / operator |
| Stores | `workspace-store` (`webui/src/stores/workspace-store.ts`) |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-037, UI-A-027, UI-A-028, UI-F-016 |

**Purpose.** List the tenant's Capsules and open one for editing.

**Regions.** left rail = navigation; workspace = capsule table; right rail = Capsule surface (UI-X-06).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-037 | capsule table | sortable table | all capsules in tenant | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-027 | Create capsule | New button | create draft Capsule | none | archive the new draft |
| UI-A-028 | Open capsule | row click | navigate to capsule editor (UI-S-12) | none | back navigation |

**States.** loading — "Loading capsules…"; empty — "No capsules yet. Create your first capsule."; error — "Capsule list could not be loaded."; permission-denied — "You need `capsule:read` to list capsules."; offline — "Offline — list may be stale."

**Features.** UI-F-016.

**Trace.** `webui/src/views/saas-workspace.ts`, `webui/src/stores/workspace-store.ts`, routed at `webui/src/main.ts:396-400`; model at `admin/core/models/core.py:109`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** The current `saas-workspace` element is a three-panel layout (sidebar / chat / right panel) driven by `workspace-store` — it is not a capsule table today. This block specifies the target. Do not describe the current view as a capsule list.

---

### UI-S-12 — Capsule editor

| Field | Value |
|---|---|
| Screen Identifier | UI-S-12 |
| Route | /workspace/:id |
| Facet | Capsule |
| Primary actor | Capsule author |
| Stores | `workspace-store`, `agent-store` |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-038, UI-C-039, UI-A-029, UI-A-030, UI-F-017, UI-S-01…06 |

**Purpose.** Edit one Capsule across its six facets; every edit spawns a child version.

**Regions.** left rail = capsule list context; workspace = capsule identity form + facet workspace;
right rail = Capsule surface (UI-X-06).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-038 | capsule identity form | name / version / description | current Capsule | name non-empty; version semver | capsule status is `active` | Active capsules are immutable; edit spawns a child version (REQ-UIX-012) |
| UI-C-039 | facet workspace host | tab host for UI-S-01…06 | first facet | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-029 | Spawn child version | Save on an active capsule | create child Capsule via `parent` lineage | none | archive the child |
| UI-A-030 | Save draft | Save button | persist draft fields | none | discard-draft |

**States.** loading — "Loading capsule…"; empty — "Capsule not found."; error — "Capsule could not be loaded."; permission-denied — "You need `capsule:write` to edit this capsule."; offline — "Offline — edits are not saved."

**Features.** UI-F-017.

**Trace.** `webui/src/views/saas-workspace.ts`, `webui/src/components/saas-capsule-editor.ts`; model lineage at `admin/core/models/core.py:157-163`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** **Route disagreement:** `SOMA-UI-IDREG-001.md` gives `/workspace/:id`, but `webui/src/main.ts:396` matches only exact `/workspace`. A URL `/workspace/<uuid>` is not matched by any branch and falls through to the default `saas-chat` at `webui/src/main.ts:466-468`. Tracked in §8 H-05. Do not describe `/workspace/:id` as reachable today.

---

### UI-S-13 — Version rail & diff

| Field | Value |
|---|---|
| Screen Identifier | UI-S-13 |
| Route | NEW |
| Facet | Capsule |
| Primary actor | Capsule author / auditor |
| Stores | `workspace-store` |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-040, UI-C-041, UI-A-031, UI-A-032, UI-F-018 |

**Purpose.** Show Capsule version lineage and a diff of a version against its parent.

**Regions.** left rail = version rail; workspace = diff viewer; right rail = Capsule surface (UI-X-06).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-040 | version rail | vertical list of `parent`/`children` | latest version | never | never | — |
| UI-C-041 | diff viewer | side-by-side field diff | selected vs parent | never | version has no parent | This version has no parent to diff against |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-031 | Select version | rail click | load that version into the diff | none | select another |
| UI-A-032 | Restore version | Restore button | spawn a new version with restored fields | UI-M-03 destructive confirm | archive the restored child |

**States.** loading — "Loading history…"; empty — "Only one version so far."; error — "History could not be loaded."; permission-denied — "You need `capsule:read` to view history."; offline — "Offline — history may be stale."

**Features.** UI-F-018.

**Trace.** no dedicated view today; lineage at `admin/core/models/core.py:157-163`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Restore spawns a new version — it never rewrites history (REQ-UIX-012). Do not show a diff between versions the backend did not return.

---

### UI-S-14 — Instances

| Field | Value |
|---|---|
| Screen Identifier | UI-S-14 |
| Route | NEW |
| Facet | Capsule |
| Primary actor | Operator |
| Stores | `activity-store` |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-042, UI-A-033, UI-A-034, UI-F-019 |

**Purpose.** List running and historical Capsule instances and control their lifecycle.

**Regions.** left rail = navigation; workspace = instance table; right rail = Debug surface (UI-X-05).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-042 | instance table | table of `CapsuleInstance` rows | running first | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-033 | Start instance | Start button | create `CapsuleInstance` | none | stop instance |
| UI-A-034 | Stop instance | Stop button | set status and `completed_at` | UI-M-03 destructive confirm | none — start a new instance |

**States.** loading — "Loading instances…"; empty — "No instances running."; error — "Instance list could not be loaded."; permission-denied — "You need `instance:control` to start or stop instances."; offline — "Offline — instance state may be stale."

**Features.** UI-F-019.

**Trace.** no dedicated view today; model at `admin/core/models/core.py:423-437` (`id`, `capsule`, `session_id`, `state`, `status`, `started_at`, `completed_at`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Every row MUST map to a real `CapsuleInstance`. Synthetic instance rows are forbidden (REQ-UIX-023). Never show an instance as running when `completed_at` is set.

---

### UI-S-15 — Module list

| Field | Value |
|---|---|
| Screen Identifier | UI-S-15 |
| Route | NEW |
| Facet | Module |
| Primary actor | Operator |
| Stores | `agent-store` |
| APIs | REST `/api/v2/modules` and `/api/v2/modules/` (measured in `webui/src/`) |
| Related | UI-C-043, UI-A-035, UI-A-036, UI-F-020 |

**Purpose.** List Capsule Modules and their enablement state.

**Regions.** left rail = navigation; workspace = module table; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-043 | module table | table with status badges | all modules | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-035 | Enable module | toggle | enable module (subject to `feature_flag`) | none | toggle off |
| UI-A-036 | Disable module | toggle | disable module and unregister its hooks | UI-M-03 confirm when hooks are registered | toggle on |

**States.** loading — "Loading modules…"; empty — "No modules installed."; error — "Module list could not be loaded."; permission-denied — "You need `module:manage` to change modules."; offline — "Offline — module state may be stale."

**Features.** UI-F-020.

**Trace.** no dedicated view today; `admin/modules/` (`manifest.py`, `registry.py`, `hooks.py`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** A module gated by `feature_flag` MUST show *why* it cannot be enabled — never a dead toggle (N-6 §3.2). `always_enabled` modules render a locked toggle with a reason.

---

### UI-S-16 — Module detail & config

| Field | Value |
|---|---|
| Screen Identifier | UI-S-16 |
| Route | NEW |
| Facet | Module |
| Primary actor | Operator |
| Stores | `agent-store` |
| APIs | REST `/api/v2/modules/` (measured in `webui/src/`) |
| Related | UI-C-044, UI-C-045, UI-A-037, UI-A-038, UI-F-021 |

**Purpose.** Configure one module and see what it contributes to the facets.

**Regions.** left rail = module list; workspace = config form + contribution panel; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-044 | module config form | form generated from `config_schema` | module defaults | schema validation | module `always_enabled` and config is locked | Module is always enabled; this field is locked |
| UI-C-045 | module contribution panel | read-only list | module manifest | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-037 | Save module config | Save button | write `module.config.json` values | none | re-edit fields |
| UI-A-038 | Toggle module | toggle | enable or disable the module | UI-M-03 when disabling with live hooks | toggle back |

**States.** loading — "Loading module…"; empty — "Module not found."; error — "Config could not be saved."; permission-denied — "You need `module:manage` to configure modules."; offline — "Offline — config is not saved."

**Features.** UI-F-021.

**Trace.** `admin/modules/manifest.py` (`module.yaml`: `settings_sections`, `permissions`, `always_enabled`, `feature_flag`, `config_schema`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** A module never owns a top-level page — contributions land in named settings sections and facet slots (N-6 §3.2). Do not render a module-provided micro design system; modules contribute through typed slots only.

---

### UI-S-17 — Capability registry

| Field | Value |
|---|---|
| Screen Identifier | UI-S-17 |
| Route | NEW |
| Facet | Module |
| Primary actor | Operator |
| Stores | `agent-store` |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-046, UI-A-039, UI-A-040, UI-F-022 |

**Purpose.** Register and manage Capabilities (tools / MCP servers) available to capsules.

**Regions.** left rail = navigation; workspace = capability table; right rail = Tools surface (UI-X-02).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-046 | capability table | table grouped by `category` | all capabilities | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-039 | Create capability | New button | create `Capability` row | none | disable capability |
| UI-A-040 | Disable capability | toggle | set `is_enabled` false (`core.py:476`) | none | toggle on |

**States.** loading — "Loading capabilities…"; empty — "No capabilities registered."; error — "Capability registry could not be loaded."; permission-denied — "You need `capability:manage` to change the registry."; offline — "Offline — registry may be stale."

**Features.** UI-F-022.

**Trace.** model at `admin/core/models/core.py:445-489` (`name`, `description`, `category`, `schema`, `config`, `policy`, `implementation`, `is_enabled`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** A capability with `is_enabled` false MUST NOT appear as attachable on UI-S-03 (REQ-UIX-026 analogue). Do not invent tool schemas.

---

### UI-S-18 — Capability detail & hook bindings

| Field | Value |
|---|---|
| Screen Identifier | UI-S-18 |
| Route | NEW |
| Facet | Module |
| Primary actor | Operator / module author |
| Stores | `agent-store` |
| APIs | REST `/api/v2/modules/` (measured in `webui/src/`) |
| Related | UI-C-047, UI-C-048, UI-A-041, UI-A-042, UI-F-023, UI-F-068 |

**Purpose.** Edit a Capability and show its module hook bindings against the real hook registry.

**Regions.** left rail = capability list; workspace = capability detail form + hook binding list;
right rail = Debug surface (UI-X-05).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-047 | capability detail form | form for `policy` / `implementation` / `config` | current values (`core.py:452-475`) | numeric `timeout_seconds`, `max_retries` | capability `is_enabled` is false | Capability is disabled in the registry |
| UI-C-048 | hook binding list | list of 8 `KNOWN_HOOKS` + 23 `RESERVED_HOOKS` | current registrations | handler must be callable | hook name is in `RESERVED_HOOKS` | reserved — not yet registerable |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-041 | Save capability | Save button | write `policy` / `implementation` / `config` | none | re-edit fields |
| UI-A-042 | Register hook binding | Add binding on a KNOWN_HOOK | `register_hook(hook, handler, module=…)` | none | unregister binding |

**States.** loading — "Loading capability…"; empty — "No hook bindings yet."; error — "Capability could not be saved."; permission-denied — "You need `capability:manage` to change bindings."; offline — "Offline — bindings are not saved."

**Features.** UI-F-023, UI-F-068.

**Trace.** `admin/modules/hooks.py:33-42` (`KNOWN_HOOKS`, 8 names), `:46-70` (`RESERVED_HOOKS`, 23 names), `:90-105` (`register_hook` raises `UnknownHookError` for unknown names at `:98-99`); model at `admin/core/models/core.py:445-489`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** **This is the honesty-critical screen for hooks.** The 8 `KNOWN_HOOKS` (`message_loop_start`, `system_prompt`, `response_stream`, `tool_execute_after`, `process_chain_end`, `monologue_end`, `job_loop`, `handle_exception`) are registerable. The 23 `RESERVED_HOOKS` MUST render as "reserved — not yet registerable" and MUST NOT be working toggles (REQ-UIX-009). `register_hook` raises `UnknownHookError` for anything outside `KNOWN_HOOKS` — a UI toggle that calls it for a reserved name will fail at the call site.

---

### UI-S-19 — Tenants

| Field | Value |
|---|---|
| Screen Identifier | UI-S-19 |
| Route | /saas/tenants |
| Facet | Platform |
| Primary actor | Platform admin |
| Stores | `activity-store` |
| APIs | REST `/api/v2/saas/tenants` (measured in `webui/src/`) |
| Related | UI-C-049, UI-A-043, UI-A-044, UI-F-024 |

**Purpose.** List tenants and open one for administration.

**Regions.** left rail = navigation; workspace = tenant table; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-049 | tenant table | sortable table | all tenants | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-043 | Create tenant | New button | navigate to UI-S-20 | none | none — wizard cancel |
| UI-A-044 | Open tenant | row click | navigate to UI-S-21 | none | back navigation |

**States.** loading — "Loading tenants…"; empty — "No tenants yet."; error — "Tenant list could not be loaded."; permission-denied — "You need `tenant:read` to list tenants."; offline — "Offline — list may be stale."

**Features.** UI-F-024.

**Trace.** `webui/src/views/saas-tenants.ts`, routed at `webui/src/main.ts:199-203` (aliases `/platform/tenants`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Do not show tenant counts or MRR that the API did not return.

---

### UI-S-20 — Tenant wizard

| Field | Value |
|---|---|
| Screen Identifier | UI-S-20 |
| Route | /saas/tenants/new |
| Facet | Platform |
| Primary actor | Platform admin |
| Stores | `activity-store` |
| APIs | REST `/api/v2/saas/tenants`, `/api/v2/saas/tenants/check-slug` (measured in `webui/src/`) |
| Related | UI-C-050, UI-C-051, UI-A-045, UI-A-046, UI-F-025 |

**Purpose.** Create a tenant through a stepped wizard.

**Regions.** left rail = none; workspace = wizard steps + form; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-050 | wizard steps | step indicator | step 1 | never | never | — |
| UI-C-051 | wizard form | form per step | empty | slug availability via `check-slug` | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-045 | Next step | Next button | advance wizard when step validates | none | Previous step |
| UI-A-046 | Submit tenant | Create button | POST tenant | UI-M-03 confirm | none — archive the tenant |

**States.** loading — "Checking availability…"; empty — "Enter a name to begin."; error — "Tenant could not be created."; permission-denied — "You need `tenant:create` to create tenants."; offline — "Offline — creation requires the server."

**Features.** UI-F-025.

**Trace.** `webui/src/views/saas-tenant-wizard.ts`, `webui/src/components/saas-tenant-wizard-*.ts`, `webui/src/controllers/tenant-wizard-controller.ts`, routed at `webui/src/main.ts:154-158` (alias `/platform/tenants/new`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Slug availability MUST come from the live `check-slug` endpoint. Do not claim a slug is free without asking.

---

### UI-S-21 — Tenant dashboard

| Field | Value |
|---|---|
| Screen Identifier | UI-S-21 |
| Route | /admin/dashboard |
| Facet | Platform |
| Primary actor | Tenant admin |
| Stores | `activity-store` |
| APIs | REST `/api/v2/aaas/dashboard/` (measured in `webui/src/`) |
| Related | UI-C-052, UI-A-047, UI-A-048, UI-F-026 |

**Purpose.** Show one tenant's operational dashboard.

**Regions.** left rail = navigation; workspace = stats grid; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-052 | tenant stats grid | stat cards | live snapshot | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-047 | Refresh dashboard | Refresh button | re-fetch snapshot | none | none — read-only |
| UI-A-048 | Drill into metric | card click | navigate to the owning screen | none | back navigation |

**States.** loading — "Loading dashboard…"; empty — "No activity yet for this tenant."; error — "Dashboard could not be loaded."; permission-denied — "You need `tenant:read` to view this dashboard."; offline — "Offline — figures may be stale."

**Features.** UI-F-026.

**Trace.** `webui/src/views/saas-tenant-dashboard.ts`, routed at `webui/src/main.ts:356-360`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Every figure MUST come from the API response. Do not compute derived "health scores" the backend does not provide.

---

### UI-S-22 — Users

| Field | Value |
|---|---|
| Screen Identifier | UI-S-22 |
| Route | /admin/users |
| Facet | Platform |
| Primary actor | Tenant admin |
| Stores | `activity-store` |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-053, UI-A-049, UI-A-050, UI-F-027 |

**Purpose.** List the tenant's users and open one for management.

**Regions.** left rail = navigation; workspace = user table; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-053 | user table | sortable table | all users in tenant | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-049 | Invite user | Invite button | send invitation | none | revoke invitation |
| UI-A-050 | Open user | row click | navigate to user detail | none | back navigation |

**States.** loading — "Loading users…"; empty — "No users in this tenant."; error — "User list could not be loaded."; permission-denied — "You need `user:read` to list users."; offline — "Offline — list may be stale."

**Features.** UI-F-027.

**Trace.** live branch `webui/src/main.ts:249-253` renders `saas-users-view` from `saas-entity-views.js`; **dead branch** `webui/src/main.ts:362-366` would render `saas-tenant-users` — see §8 H-02; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** The router currently serves `saas-users-view` for `/admin/users`. The second branch is unreachable and MUST NOT be described as live (REQ-UIX-017). Do not show email addresses in list view without masking on shared screens.

---

### UI-S-23 — Roles & role matrix

| Field | Value |
|---|---|
| Screen Identifier | UI-S-23 |
| Route | /platform/roles |
| Facet | Platform |
| Primary actor | Platform admin |
| Stores | `activity-store` |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-054, UI-C-055, UI-A-051, UI-A-052, UI-F-028 |

**Purpose.** Define roles and edit the role-to-permission matrix.

**Regions.** left rail = navigation; workspace = role list + matrix; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-054 | role list | list with member counts | all roles | never | never | — |
| UI-C-055 | role matrix | checkbox matrix | selected role | never | role is a system role | System roles are not editable |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-051 | Save role matrix | Save button | write role-permission links | none | re-edit matrix |
| UI-A-052 | Create role | New button | create role | none | delete role |

**States.** loading — "Loading roles…"; empty — "No roles defined."; error — "Roles could not be loaded."; permission-denied — "You need `role:manage` to edit roles."; offline — "Offline — changes are not saved."

**Features.** UI-F-028.

**Trace.** `webui/src/views/saas-admin-roles-list.ts` at `webui/src/main.ts:140-144`; also `saas-role-matrix.ts` at `/platform/role-matrix` (`webui/src/main.ts:147-151`), which has **no** UI-S identifier in `SOMA-UI-IDREG-001.md` — see §8 H-09; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** System roles render their matrix read-only with the reason "System roles are not editable". Do not imply a permission is granted when the matrix API rejected the write.

---

### UI-S-24 — Permissions

| Field | Value |
|---|---|
| Screen Identifier | UI-S-24 |
| Route | /saas/permissions |
| Facet | Platform |
| Primary actor | Platform admin |
| Stores | `activity-store` |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-056, UI-C-057, UI-A-053, UI-A-054, UI-F-029 |

**Purpose.** Inspect the permission catalogue and who holds each permission.

**Regions.** left rail = navigation; workspace = permission table + holder panel; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-056 | permission table | grouped table | all permissions | never | never | — |
| UI-C-057 | holder panel | read-only list | selected permission | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-053 | Grant permission | Grant button | attach permission to a role | none | revoke |
| UI-A-054 | Revoke permission | Revoke button | detach permission | UI-M-03 destructive confirm | re-grant |

**States.** loading — "Loading permissions…"; empty — "No permissions defined."; error — "Permissions could not be loaded."; permission-denied — "You need `permission:manage` to change grants."; offline — "Offline — changes are not saved."

**Features.** UI-F-029.

**Trace.** `webui/src/views/saas-permissions.ts`, routed at `webui/src/main.ts:160-164` (alias `/platform/permissions`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Holder lists MUST come from the API. Do not infer holders from role names.

---

### UI-S-25 — Billing

| Field | Value |
|---|---|
| Screen Identifier | UI-S-25 |
| Route | /admin/billing |
| Facet | Platform |
| Primary actor | Tenant admin |
| Stores | `activity-store` |
| APIs | REST `/api/v2/saas/billing/usage` (measured in `webui/src/`) |
| Related | UI-C-058, UI-C-059, UI-A-055, UI-A-056, UI-F-030 |

**Purpose.** Show the tenant's billing summary, invoices and usage.

**Regions.** left rail = navigation; workspace = billing summary + invoices; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-058 | billing summary | metric cards | current period | never | never | — |
| UI-C-059 | invoices table | table | latest first | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-055 | Download invoice | row action | download invoice file | none | none — file written |
| UI-A-056 | Change plan | Change plan button | navigate to UI-S-26 | none | back navigation |

**States.** loading — "Loading billing…"; empty — "No invoices yet."; error — "Billing data could not be loaded."; permission-denied — "You need `billing:read` to view billing."; offline — "Offline — figures may be stale."

**Features.** UI-F-030.

**Trace.** `webui/src/views/saas-tenant-billing.ts`, `webui/src/components/saas-tenant-billing-*.ts`, `webui/src/controllers/tenant-billing-controller.ts`, routed at `webui/src/main.ts:316-320` (alias `/tenant/billing`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Payment card details are never rendered. If a secret or token appears in billing config, show a masked placeholder plus "rotate in Vault" (REQ-UIX-006).

---

### UI-S-26 — Subscriptions

| Field | Value |
|---|---|
| Screen Identifier | UI-S-26 |
| Route | /saas/subscriptions |
| Facet | Platform |
| Primary actor | Platform admin |
| Stores | `activity-store` |
| APIs | REST `/api/v2/saas/tiers` (measured in `webui/src/`) |
| Related | UI-C-060, UI-C-061, UI-A-057, UI-A-058, UI-F-031 |

**Purpose.** Manage subscription plans and their feature matrices.

**Regions.** left rail = navigation; workspace = tier cards + feature matrix; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-060 | subscription tier cards | card list | current tiers | never | never | — |
| UI-C-061 | subscription feature matrix | matrix editor | selected tier | never | tier is published | Published tiers are not editable |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-057 | Edit tier | Edit button | open tier editor | none | discard changes |
| UI-A-058 | Publish tier | Publish button | make tier purchasable | UI-M-03 destructive confirm | none — unpublish requires support |

**States.** loading — "Loading subscriptions…"; empty — "No subscription tiers defined."; error — "Tiers could not be loaded."; permission-denied — "You need `tier:manage` to edit tiers."; offline — "Offline — changes are not saved."

**Features.** UI-F-031.

**Trace.** `webui/src/views/saas-subscriptions.ts`, `webui/src/components/saas-subscription-*.ts`, `webui/src/controllers/subscriptions-controller.ts`, routed at `webui/src/main.ts:205-209`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Feature availability per tier MUST match the API. Do not grey out a feature with a vague reason — state the blocking condition.

---

### UI-S-27 — Usage analytics

| Field | Value |
|---|---|
| Screen Identifier | UI-S-27 |
| Route | /platform/usage |
| Facet | Platform |
| Primary actor | Platform admin |
| Stores | `activity-store` |
| APIs | REST `/api/v2/saas/billing/usage` (measured in `webui/src/`) |
| Related | UI-C-062, UI-C-063, UI-A-059, UI-A-060, UI-F-032 |

**Purpose.** Show platform usage analytics across tenants and time.

**Regions.** left rail = navigation; workspace = usage charts + filters; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-062 | usage charts | time-series charts | last 30 days | date range valid | never | — |
| UI-C-063 | filter bar | date range + tenant select | all tenants | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-059 | Apply filters | Apply button | re-query usage | none | reset filters |
| UI-A-060 | Export usage | Export button | download CSV/JSON | none | none — file written |

**States.** loading — "Loading usage…"; empty — "No usage in the selected range."; error — "Usage could not be loaded."; permission-denied — "You need `usage:read` to view analytics."; offline — "Offline — charts may be stale."

**Features.** UI-F-032.

**Trace.** `webui/src/views/saas-usage-analytics.ts`, routed at `webui/src/main.ts:120-124` (alias `/saas/usage`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Chart series MUST be API-returned samples. Do not smooth or interpolate gaps into apparent data.

---

### UI-S-28 — Tier builder

| Field | Value |
|---|---|
| Screen Identifier | UI-S-28 |
| Route | /platform/tiers |
| Facet | Platform |
| Primary actor | Platform admin |
| Stores | `activity-store` |
| APIs | REST `/api/v2/saas/tiers` (measured in `webui/src/`) |
| Related | UI-C-064, UI-C-065, UI-A-061, UI-A-062, UI-F-033 |

**Purpose.** Build and price subscription tiers.

**Regions.** left rail = navigation; workspace = tier editor + pricing form; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-064 | tier editor | form | draft tier | name and price required | tier is published | Published tiers are not editable |
| UI-C-065 | pricing form | currency + interval fields | monthly | amount ≥ 0 | tier is published | Published tiers are not editable |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-061 | Save tier | Save button | write tier definition | none | discard changes |
| UI-A-062 | Publish tier | Publish button | make tier purchasable | UI-M-03 destructive confirm | none — unpublish requires support |

**States.** loading — "Loading tiers…"; empty — "No tiers defined. Create one."; error — "Tier could not be saved."; permission-denied — "You need `tier:manage` to build tiers."; offline — "Offline — changes are not saved."

**Features.** UI-F-033.

**Trace.** `webui/src/views/saas-tier-builder.ts`, routed at `webui/src/main.ts:113-117` (alias `/saas/tiers`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Do not display a currency symbol the API does not return. Prices are server-authoritative.

---

### UI-S-29 — Login

| Field | Value |
|---|---|
| Screen Identifier | UI-S-29 |
| Route | /login |
| Facet | Auth |
| Primary actor | Any user |
| Stores | `localStorage` keys `saas_auth_token`, `saas_user` (client-side only) |
| APIs | REST `/api/v2/auth/login`, `/api/v2/auth/me` (measured in `webui/src/`) |
| Related | UI-C-066, UI-C-067, UI-A-063, UI-A-064, UI-F-034, UI-F-069 |

**Purpose.** Authenticate a user and start a server session.

**Regions.** left rail = none; workspace = login form; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-066 | credentials form | username + password | empty | non-empty; password never echoed | request in flight | Signing in… |
| UI-C-067 | SSO button | OAuth button | hidden unless configured | never | SSO not configured | No SSO provider is configured |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-063 | Sign in | Submit button | POST `/api/v2/auth/login`, set session cookie | none | sign out |
| UI-A-064 | Sign in with SSO | SSO button | start OAuth flow | none | cancel at provider |

**States.** loading — "Signing in…"; empty — "Enter your credentials."; error — "Sign-in failed. Check your credentials."; permission-denied — "Your account is locked. Contact your administrator."; offline — "Offline — sign-in requires the server."

**Features.** UI-F-034, UI-F-069.

**Trace.** `webui/src/views/saas-login.ts`, `webui/src/services/google-auth-service.ts`, `keycloak-service.ts`, routed at `webui/src/main.ts:53-64`; auth check at `webui/src/main.ts:36-43`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Session truth is the httpOnly cookie read by `checkAuth()` with `credentials: 'include'` (`webui/src/main.ts:38`), **not** `localStorage`. Any UI that treats `localStorage.saas_auth_token` as proof of a session is wrong — see §8 H-04. Never show a "signed in" state before `/api/v2/auth/me` returns ok.

---

### UI-S-30 — Register

| Field | Value |
|---|---|
| Screen Identifier | UI-S-30 |
| Route | /register |
| Facet | Auth |
| Primary actor | New user |
| Stores | none |
| APIs | REST `/api/v2/auth/register` (measured in `webui/src/`) |
| Related | UI-C-068, UI-C-069, UI-A-065, UI-A-066, UI-F-035 |

**Purpose.** Create a user account.

**Regions.** left rail = none; workspace = registration form; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-068 | registration form | email + password + confirm | empty | email valid; passwords match | request in flight | Creating account… |
| UI-C-069 | terms checkbox | checkbox | unchecked | must be checked | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-065 | Create account | Submit button | POST `/api/v2/auth/register` | none | delete account (separate flow) |
| UI-A-066 | Resend verification | Link | re-send verification email | none | none — email is idempotent |

**States.** loading — "Creating account…"; empty — "Fill in the form to register."; error — "Registration failed."; permission-denied — "Registration is closed on this deployment."; offline — "Offline — registration requires the server."

**Features.** UI-F-035.

**Trace.** `webui/src/views/saas-register.ts`, routed at `webui/src/main.ts:66-71`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Do not claim email verification is complete until the API says so. Password strength hints must be factual, not decorative.

---

### UI-S-31 — Forgot password

| Field | Value |
|---|---|
| Screen Identifier | UI-S-31 |
| Route | /forgot-password |
| Facet | Auth |
| Primary actor | Any user |
| Stores | none |
| APIs | REST `/api/v2/auth/password/reset-request` (measured in `webui/src/`) |
| Related | UI-C-070, UI-C-071, UI-A-067, UI-A-068, UI-F-036 |

**Purpose.** Request a password-reset link.

**Regions.** left rail = none; workspace = reset-request form; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-070 | email field | email input | empty | email valid | request in flight | Sending… |
| UI-C-071 | submit button | button | enabled | never | request in flight | Sending… |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-067 | Request reset | Submit button | POST reset-request | none | none — email sent |
| UI-A-068 | Back to login | Link | navigate to UI-S-29 | none | back navigation |

**States.** loading — "Sending…"; empty — "Enter your email address."; error — "Request failed."; permission-denied — "Reset is disabled on this deployment."; offline — "Offline — reset requires the server."

**Features.** UI-F-036.

**Trace.** `webui/src/views/saas-forgot-password.ts`, routed at `webui/src/main.ts:73-78`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** The confirmation message MUST NOT reveal whether the email exists — use the same copy either way: "If that address is registered, a reset link is on its way."

---

### UI-S-32 — MFA setup

| Field | Value |
|---|---|
| Screen Identifier | UI-S-32 |
| Route | /mfa/setup |
| Facet | Auth |
| Primary actor | Any user |
| Stores | none |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-072, UI-C-073, UI-A-069, UI-A-070, UI-F-037 |

**Purpose.** Enrol a second factor for the account.

**Regions.** left rail = none; workspace = MFA enrolment panel; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-072 | authenticator QR | QR image + secret (masked) | fresh enrolment | never | MFA already enrolled | MFA is already enrolled; unenrol first |
| UI-C-073 | verification code | 6-digit input | empty | 6 digits | request in flight | Verifying… |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-069 | Verify code | Submit button | confirm enrolment | none | unenrol (destructive — UI-M-03) |
| UI-A-070 | Generate recovery codes | Button | issue one-time recovery codes | none | regenerate (invalidates previous) |

**States.** loading — "Loading enrolment…"; empty — "Scan the QR code to begin."; error — "Code not accepted. Try again."; permission-denied — "You need to sign in first."; offline — "Offline — MFA setup requires the server."

**Features.** UI-F-037.

**Trace.** `webui/src/views/saas-mfa-setup.ts`, routed at `webui/src/main.ts:375-379` (alias `/settings/mfa`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** The shared secret is displayed once as a masked placeholder plus "rotate in Vault" for storage; recovery codes are shown once and never re-fetchable (REQ-UIX-006). Never render a QR code for a secret the server did not issue.

---

### UI-S-33 — Auth callback

| Field | Value |
|---|---|
| Screen Identifier | UI-S-33 |
| Route | /auth/callback |
| Facet | Auth |
| Primary actor | System |
| Stores | none |
| APIs | REST `/api/v2/auth/google/callback` (measured in `webui/src/`) |
| Related | UI-C-074, UI-A-071, UI-A-072, UI-F-038 |

**Purpose.** Complete the OAuth redirect and land the user in the app.

**Regions.** left rail = none; workspace = callback status; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-074 | callback status panel | status + retry | processing | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-071 | Continue | automatic | navigate to `/chat` on success | none | none — navigation |
| UI-A-072 | Retry | Retry button | re-attempt token exchange | none | none — idempotent retry |

**States.** loading — "Completing sign-in…"; empty — "Waiting for the provider…"; error — "Sign-in could not be completed."; permission-denied — "Your account is not permitted on this deployment."; offline — "Offline — sign-in requires the server."

**Features.** UI-F-038.

**Trace.** `webui/src/views/saas-auth-callback.ts`, routed at `webui/src/main.ts:81-86`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Do not auto-redirect on a partial token. Show the failure copy verbatim when the exchange fails.

---

### UI-S-34 — Personal profile

| Field | Value |
|---|---|
| Screen Identifier | UI-S-34 |
| Route | /profile |
| Facet | Auth |
| Primary actor | Any user |
| Stores | none |
| APIs | REST `/api/v2/auth/me` (measured in `webui/src/`) |
| Related | UI-C-075, UI-C-076, UI-A-073, UI-A-074, UI-F-039 |

**Purpose.** Let a user view and edit their own profile.

**Regions.** left rail = navigation; workspace = profile form; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-075 | profile form | name + email + locale | current user | email valid | never | — |
| UI-C-076 | password change | current + new + confirm | empty | new password policy | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |  |
|---|---|---|---|---|---|---|
| UI-A-073 | Save profile | Save button | PATCH profile | none | re-edit fields |  |
| UI-A-074 | Change password | Submit button | POST password change | UI-M-03 confirm | none — re-enter |  |

**States.** loading — "Loading profile…"; empty — "Profile not found."; error — "Profile could not be saved."; permission-denied — "You need to sign in first."; offline — "Offline — changes are not saved."

**Features.** UI-F-039.

**Trace.** `webui/src/views/saas-personal-profile.ts`, `webui/src/components/saas-user-profile-card.ts`, routed at `webui/src/main.ts:284-288`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Never echo a password. The email field shows the address the API returned, not a locally cached guess.

---

### UI-S-35 — Platform profile

| Field | Value |
|---|---|
| Screen Identifier | UI-S-35 |
| Route | /admin/profile |
| Facet | Auth |
| Primary actor | Platform admin |
| Stores | none |
| APIs | REST `/api/v2/auth/me` (measured in `webui/src/`) |
| Related | UI-C-077, UI-C-078, UI-A-075, UI-A-076, UI-F-040 |

**Purpose.** Edit the platform administrator's own profile and API credentials.

**Regions.** left rail = navigation; workspace = profile form + credential panel; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-077 | profile form | name + email | current admin | email valid | never | — |
| UI-C-078 | API key panel | masked key + regenerate | masked placeholder | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-075 | Save profile | Save button | PATCH profile | none | re-edit fields |
| UI-A-076 | Regenerate API key | Regenerate button | issue new key | UI-M-03 destructive confirm | none — old key revoked |

**States.** loading — "Loading profile…"; empty — "Profile not found."; error — "Profile could not be saved."; permission-denied — "You need `platform:admin` to view this profile."; offline — "Offline — changes are not saved."

**Features.** UI-F-040.

**Trace.** `webui/src/views/saas-platform-profile.ts`, routed at `webui/src/main.ts:270-274` (alias `/platform/profile` at `:263-267`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** **Secrets rule:** the API key renders as a masked placeholder plus "rotate in Vault" — never a value (REQ-UIX-006). After regeneration the new key is shown once and then masked.

---

### UI-S-36 — Mode selection

| Field | Value |
|---|---|
| Screen Identifier | UI-S-36 |
| Route | /mode-select |
| Facet | Auth |
| Primary actor | Any user |
| Stores | none |
| APIs | REST `/api/v2/auth/me` (measured in `webui/src/`) |
| Related | UI-C-079, UI-C-080, UI-A-077, UI-A-078, UI-F-041 |

**Purpose.** Choose which surface of the product to enter.

**Regions.** left rail = none; workspace = mode cards; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-079 | mode cards | selectable cards | none | exactly one selected | mode not permitted for this account | This mode is not enabled for your account |
| UI-C-080 | remember-choice checkbox | checkbox | unchecked | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-077 | Enter mode | Enter button | navigate to the chosen home | none | return to UI-S-36 |
| UI-A-078 | Skip | Skip button | navigate to default home `/chat` | none | back navigation |

**States.** loading — "Loading modes…"; empty — "No modes available for your account."; error — "Modes could not be loaded."; permission-denied — "No mode is enabled for your account."; offline — "Offline — showing cached modes."

**Features.** UI-F-041.

**Trace.** `webui/src/views/saas-mode-selection.ts`, routed at `webui/src/main.ts:323-327`; **duplicate dead branch** at `webui/src/main.ts:349-353` — see §8 H-10; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** A mode card that the account cannot enter is present-but-disabled with the reason "This mode is not enabled for your account" — never a silent hide.

---

### UI-S-37 — Platform dashboard

| Field | Value |
|---|---|
| Screen Identifier | UI-S-37 |
| Route | /saas/dashboard |
| Facet | Ops |
| Primary actor | Platform admin |
| Stores | `activity-store` |
| APIs | REST `/api/v2/aaas/admin` (measured in `webui/src/`) |
| Related | UI-C-081, UI-A-079, UI-A-080, UI-F-042 |

**Purpose.** Show platform-wide operational health and activity.

**Regions.** left rail = navigation; workspace = stats grid + activity feed + alerts; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-081 | platform stats grid | stat cards + feed + alerts | live snapshot | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-079 | Refresh snapshot | Refresh button | re-fetch snapshot | none | none — read-only |
| UI-A-080 | Acknowledge alert | alert action | mark alert acknowledged | none | un-acknowledge |

**States.** loading — "Loading platform dashboard…"; empty — "No platform activity yet."; error — "Dashboard could not be loaded."; permission-denied — "You need `platform:read` to view this dashboard."; offline — "Offline — figures may be stale."

**Features.** UI-F-042.

**Trace.** `webui/src/views/saas-platform-dashboard.ts`, `webui/src/components/saas-platform-*.ts`, `webui/src/controllers/platform-dashboard-controller.ts`, routed at `webui/src/main.ts:100-104` (aliases `/saas`, `/platform`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Home `/` is Chat, never this dashboard (`webui/src/main.ts:93-97`). Do not show alert counts the API did not return.

---

### UI-S-38 — Platform metrics

| Field | Value |
|---|---|
| Screen Identifier | UI-S-38 |
| Route | /platform/metrics |
| Facet | Ops |
| Primary actor | Platform admin / SRE |
| Stores | `activity-store` |
| APIs | REST `/api/v2/core/observability/snapshot`, `/api/v2/core/observability/sla` (measured in `webui/src/`) |
| Related | UI-C-082, UI-C-083, UI-A-081, UI-A-082, UI-F-043 |

**Purpose.** Show platform metrics and SLA adherence.

**Regions.** left rail = navigation; workspace = metrics charts + SLA panel; right rail = Debug surface (UI-X-05).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-082 | metrics charts | time-series charts | last hour | date range valid | never | — |
| UI-C-083 | SLA panel | read-only panel | current window | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-081 | Change window | window selector | re-query metrics | none | reset window |
| UI-A-082 | Export metrics | Export button | download metrics file | none | none — file written |

**States.** loading — "Loading metrics…"; empty — "No metrics in this window."; error — "Metrics could not be loaded."; permission-denied — "You need `observability:read` to view metrics."; offline — "Offline — charts may be stale."

**Features.** UI-F-043.

**Trace.** `webui/src/views/platform-metrics-dashboard.ts`, routed at `webui/src/main.ts:219-223` (alias `/saas/metrics`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** SLA percentages MUST come from the `/sla` endpoint. Do not derive SLA client-side.

---

### UI-S-39 — Infrastructure dashboard

| Field | Value |
|---|---|
| Screen Identifier | UI-S-39 |
| Route | /platform/infrastructure |
| Facet | Ops |
| Primary actor | Platform admin / SRE |
| Stores | `activity-store` |
| APIs | REST `/api/v2/core/infrastructure/ratelimits`, `/api/v2/observability` (measured in `webui/src/`) |
| Related | UI-C-084, UI-C-085, UI-A-083, UI-A-084, UI-F-044 |

**Purpose.** Show infrastructure status cards, alert lists and metrics.

**Regions.** left rail = navigation; workspace = status cards + alert list + charts; right rail = Debug surface (UI-X-05).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-084 | infra status cards | status cards | live | never | never | — |
| UI-C-085 | alert list | alert rows | unresolved first | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-083 | Refresh status | Refresh button | re-fetch status | none | none — read-only |
| UI-A-084 | Open rate limits | link | navigate to UI-S-40 | none | back navigation |

**States.** loading — "Loading infrastructure…"; empty — "No infrastructure alerts."; error — "Infrastructure status could not be loaded."; permission-denied — "You need `infra:read` to view infrastructure."; offline — "Offline — status may be stale."

**Features.** UI-F-044.

**Trace.** `webui/src/views/saas-infrastructure-dashboard.ts`, `webui/src/components/saas-infra-*.ts`, `webui/src/controllers/infra-dashboard-controller.ts`, routed at `webui/src/main.ts:212-216` (alias `/saas/infrastructure`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** A status card with no backend sample renders "No data" — never an invented green tick.

---

### UI-S-40 — Rate limits

| Field | Value |
|---|---|
| Screen Identifier | UI-S-40 |
| Route | /platform/infrastructure/redis/ratelimits |
| Facet | Ops |
| Primary actor | Platform admin / SRE |
| Stores | `activity-store` |
| APIs | REST `/api/v2/core/infrastructure/ratelimits` (measured in `webui/src/`) |
| Related | UI-C-086, UI-C-087, UI-A-085, UI-A-086, UI-F-045 |

**Purpose.** Inspect and adjust Redis-backed rate limits.

**Regions.** left rail = navigation; workspace = rate-limit table + editor; right rail = Debug surface (UI-X-05).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-086 | rate-limit table | editable table | current limits | numeric limits | limit is system-managed | This limit is system-managed and cannot be edited |
| UI-C-087 | reset-window selector | select | current window | valid window | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-085 | Save limit | row save | write limit | none | revert row |
| UI-A-086 | Reset counters | Reset button | clear counters for the window | UI-M-03 destructive confirm | none — counters restart |

**States.** loading — "Loading rate limits…"; empty — "No rate limits configured."; error — "Limits could not be loaded."; permission-denied — "You need `infra:manage` to change limits."; offline — "Offline — changes are not saved."

**Features.** UI-F-045.

**Trace.** `webui/src/views/saas-rate-limits.ts`, routed at `webui/src/main.ts:127-131` (alias `/platform/ratelimits`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Counters MUST come from Redis via the API. Do not estimate remaining quota client-side.

---

### UI-S-41 — Integrations dashboard

| Field | Value |
|---|---|
| Screen Identifier | UI-S-41 |
| Route | /platform/integrations |
| Facet | Ops |
| Primary actor | Platform admin |
| Stores | `activity-store` |
| APIs | REST `/api/v2/saas/integrations` (measured in `webui/src/`) |
| Related | UI-C-088, UI-C-089, UI-A-087, UI-A-088, UI-F-046 |

**Purpose.** Show configured integrations and their connection state.

**Regions.** left rail = navigation; workspace = integration cards; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-088 | integration cards | card grid | all integrations | never | never | — |
| UI-C-089 | connection state badge | status badge | live | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-087 | Configure integration | Configure button | open config Drawer (UI-M-01) | none | close drawer |
| UI-A-088 | Test connection | Test button | ping the integration | none | none — read-only probe |

**States.** loading — "Loading integrations…"; empty — "No integrations configured."; error — "Integrations could not be loaded."; permission-denied — "You need `integration:manage` to configure integrations."; offline — "Offline — connection state may be stale."

**Features.** UI-F-046.

**Trace.** `webui/src/views/saas-integrations-dashboard.ts`, routed at `webui/src/main.ts:134-138` (alias `/saas/settings/integrations`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Connection badges reflect the last probe the API returned — never a hardcoded "connected". Credentials render as a masked placeholder plus "rotate in Vault".

---

### UI-S-42 — Marketplace

| Field | Value |
|---|---|
| Screen Identifier | UI-S-42 |
| Route | /platform/marketplace |
| Facet | Ops |
| Primary actor | Platform admin |
| Stores | `activity-store` |
| APIs | REST `/api/v2/platform/marketplace/templates` (measured in `webui/src/`) |
| Related | UI-C-090, UI-C-091, UI-A-089, UI-A-090, UI-F-047 |

**Purpose.** Browse and install agent marketplace templates.

**Regions.** left rail = navigation; workspace = template grid + detail; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-090 | template grid | card grid | all templates | never | never | — |
| UI-C-091 | search + category filter | text + select | all | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-089 | Install template | Install button | create Capsule from template | UI-M-03 confirm | archive the created Capsule |
| UI-A-090 | Preview template | Preview button | open Drawer (UI-M-01) with manifest | none | close drawer |

**States.** loading — "Loading marketplace…"; empty — "No templates match this filter."; error — "Marketplace could not be loaded."; permission-denied — "You need `marketplace:install` to install templates."; offline — "Offline — marketplace requires the server."

**Features.** UI-F-047.

**Trace.** `webui/src/views/saas-marketplace.ts`, routed at `webui/src/main.ts:186-190`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Install counts and ratings MUST come from the API. Never invent popularity figures.

---

### UI-S-43 — Audit dashboard

| Field | Value |
|---|---|
| Screen Identifier | UI-S-43 |
| Route | /platform/audit |
| Facet | Ops |
| Primary actor | Auditor / platform admin |
| Stores | `activity-store` |
| APIs | REST `/api/v2/aaas/audit` (measured in `webui/src/`) |
| Related | UI-C-092, UI-A-091, UI-A-092, UI-F-048 |

**Purpose.** Summarise audit activity and link into the audit log.

**Regions.** left rail = navigation; workspace = audit summary charts; right rail = Debug surface (UI-X-05).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-092 | audit summary charts | charts + counters | last 7 days | date range valid | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-091 | Open audit log | link | navigate to UI-S-44 | none | back navigation |
| UI-A-092 | Export audit | Export button | download audit export | none | none — file written |

**States.** loading — "Loading audit summary…"; empty — "No audit events in this range."; error — "Audit summary could not be loaded."; permission-denied — "You need `audit:read` to view audit data."; offline — "Offline — summary may be stale."

**Features.** UI-F-048.

**Trace.** live branch `webui/src/main.ts:303-307` renders `saas-audit-dashboard`; **dead branch** `webui/src/main.ts:382-386` also matches `/platform/audit` and would render `saas-audit-log` — see §8 H-03; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Audit counters MUST come from the API. Never present an audit summary as complete when the query window is partial.

---

### UI-S-44 — Audit log

| Field | Value |
|---|---|
| Screen Identifier | UI-S-44 |
| Route | /audit |
| Facet | Ops |
| Primary actor | Auditor / platform admin |
| Stores | `activity-store` |
| APIs | REST `/api/v2/aaas/audit`, `/api/v2/aaas/audit/export` (measured in `webui/src/`) |
| Related | UI-C-093, UI-A-093, UI-A-094, UI-F-049 |

**Purpose.** List, filter and export individual audit events.

**Regions.** left rail = navigation; workspace = audit table + filters; right rail = Debug surface (UI-X-05).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-093 | audit table | paged table | newest first | filter valid | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-093 | Filter events | Apply button | re-query events | none | clear filters |
| UI-A-094 | Export log | Export button | download export via `/api/v2/aaas/audit/export` | none | none — file written |

**States.** loading — "Loading audit events…"; empty — "No events match this filter."; error — "Audit log could not be loaded."; permission-denied — "You need `audit:read` to view the audit log."; offline — "Offline — log may be stale."

**Features.** UI-F-049.

**Trace.** `webui/src/views/saas-audit-log.ts`, routed at `webui/src/main.ts:382-386` for `/audit` and `/admin/audit` (the `/platform/audit` alternative in that condition is unreachable — §8 H-03); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Audit rows are immutable evidence. Do not round, reformat or summarise away actor identity, timestamps or action names.

---

### UI-S-45 — Agent metrics

| Field | Value |
|---|---|
| Screen Identifier | UI-S-45 |
| Route | /admin/metrics |
| Facet | Ops |
| Primary actor | Tenant admin |
| Stores | `activity-store` |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-094, UI-C-095, UI-A-095, UI-A-096, UI-F-050 |

**Purpose.** Show per-agent metrics for the tenant.

**Regions.** left rail = navigation; workspace = agent metric charts; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-094 | agent metric charts | time-series charts | last 24 hours | date range valid | never | — |
| UI-C-095 | agent selector | select | all agents | never | no agents in tenant | No agents in this tenant |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-095 | Change window | window selector | re-query metrics | none | reset window |
| UI-A-096 | Open agent | link | navigate to the agent's capsule | none | back navigation |

**States.** loading — "Loading agent metrics…"; empty — "No agents to measure."; error — "Metrics could not be loaded."; permission-denied — "You need `metrics:read` to view agent metrics."; offline — "Offline — charts may be stale."

**Features.** UI-F-050.

**Trace.** `webui/src/views/saas-agent-metrics.ts`, routed at `webui/src/main.ts:193-197` (alias `/tenant/metrics`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Per-agent figures MUST come from the API. Do not aggregate client-side into totals the backend did not publish.

---

### UI-S-46 — Voice chat

| Field | Value |
|---|---|
| Screen Identifier | UI-S-46 |
| Route | /voice/chat |
| Facet | Voice |
| Primary actor | End user |
| Stores | `composer-store` |
| APIs | REST `/api/v2/voice/transcribe` (measured in `webui/src/`); WebSocket `/ws/v2/chat/` |
| Related | UI-C-096, UI-C-097, UI-A-097, UI-A-098, UI-F-051 |

**Purpose.** Hold a voice conversation with a visible mic/TTS state machine.

**Regions.** left rail = navigation; workspace = voice controls + transcript; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|
| UI-C-096 | voice controls | mic + speak buttons | idle | never | microphone permission denied | Microphone permission is denied |
| UI-C-097 | live transcript | scrolling transcript | empty | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-097 | Start recording | Mic button | begin capture + transcribe | none | stop recording |
| UI-A-098 | Speak reply | Speak button | play TTS for the latest reply | none | stop playback |

**States.** loading — "Connecting…"; empty — "Press the mic to start speaking."; error — "Voice session failed."; permission-denied — "Microphone permission is denied. Enable it in the browser."; offline — "Offline — voice requires the server."

**Features.** UI-F-051.

**Trace.** `webui/src/views/saas-voice-chat.ts`, `webui/src/components/saas-voice-*.ts`, `voice-*.ts`, `webui/src/controllers/voice-chat-controller.ts`, routed at `webui/src/main.ts:458-462` (aliases `/platform/voice/chat`, `/voice`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** The mic/TTS state machine MUST be legible: permission, recording, transcribing, error are distinct visible states (N-6 B-7). Never show a transcript line the transcriber did not return.

---

### UI-S-47 — Voice sessions

| Field | Value |
|---|---|
| Screen Identifier | UI-S-47 |
| Route | /voice/sessions |
| Facet | Voice |
| Primary actor | End user / auditor |
| Stores | `activity-store` |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-098, UI-C-099, UI-A-099, UI-A-100, UI-F-052 |

**Purpose.** List past voice sessions and reopen their transcripts.

**Regions.** left rail = navigation; workspace = session list + transcript; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-098 | session list | table | newest first | never | never | — |
| UI-C-099 | session transcript | read-only transcript | selected session | never | no session selected | Select a session to view its transcript |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-099 | Open session | row click | load transcript | none | select another |
| UI-A-100 | Delete session | row action | delete session record | UI-M-03 destructive confirm | none — deletion is permanent |

**States.** loading — "Loading sessions…"; empty — "No voice sessions yet."; error — "Sessions could not be loaded."; permission-denied — "You need `voice:read` to view sessions."; offline — "Offline — list may be stale."

**Features.** UI-F-052.

**Trace.** `webui/src/views/saas-voice-sessions.ts`, `webui/src/components/saas-voice-session-picker.ts`, routed at `webui/src/main.ts:452-456` (alias `/platform/voice/sessions`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Transcripts are evidence of what was said — do not paraphrase or auto-summarise in place of the transcript.

---

### UI-S-48 — Voice personas

| Field | Value |
|---|---|
| Screen Identifier | UI-S-48 |
| Route | /voice/personas |
| Facet | Voice |
| Primary actor | Capsule author |
| Stores | `agent-store` |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-100, UI-C-101, UI-A-101, UI-A-102, UI-F-053 |

**Purpose.** Configure voice personas (TTS voices and speaking style).

**Regions.** left rail = navigation; workspace = persona cards + config panel; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-100 | persona cards | card grid | available voices | never | never | — |
| UI-C-101 | persona config form | rate + pitch + style fields | persona defaults | numeric ranges | no `voice_model` bound | Bind a voice model on UI-S-02 first |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-101 | Save persona | Save button | write persona config | none | re-edit fields |
| UI-A-102 | Preview voice | Play button | synthesise a sample | none | stop playback |

**States.** loading — "Loading personas…"; empty — "No voice personas available."; error — "Persona could not be saved."; permission-denied — "You need `capsule:write` to change voice personas."; offline — "Offline — preview requires the server."

**Features.** UI-F-053.

**Trace.** `webui/src/views/saas-voice-personas.ts`, `webui/src/components/voice-persona-card.ts`, `voice-config-panel.ts`, routed at `webui/src/main.ts:446-450` (alias `/platform/voice/personas`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Voice selection MUST be limited to voices the configured `voice_model` actually offers. Never list a voice the provider does not have.

---

### UI-S-49 — Multimodal settings

| Field | Value |
|---|---|
| Screen Identifier | UI-S-49 |
| Route | /settings/multimodal |
| Facet | Voice |
| Primary actor | Agent owner |
| Stores | `agent-store` |
| APIs | REST `/api/v2/agents/{id}/multimodal-config` (measured in `webui/src/`) |
| Related | UI-C-102, UI-C-103, UI-A-103, UI-A-104, UI-F-054 |

**Purpose.** Configure multimodal processing (vision, voice, transcription) for an agent.

**Regions.** left rail = navigation; workspace = multimodal config form; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|
| UI-C-102 | multimodal config form | toggles + model selects | current config | model must be configured | corresponding model role is unbound | Bind this model role on UI-S-02 first |
| UI-C-103 | job status list | read-only job rows | recent jobs | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-103 | Save multimodal config | Save button | PATCH multimodal-config | none | re-edit fields |
| UI-A-104 | Retry job | row action | re-queue a failed job | none | cancel retry |

**States.** loading — "Loading multimodal settings…"; empty — "No multimodal features configured."; error — "Settings could not be saved."; permission-denied — "You need `agent:write` to change multimodal settings."; offline — "Offline — changes are not saved."

**Features.** UI-F-054.

**Trace.** `webui/src/views/saas-multimodal-settings.ts`, `saas-multimodal-jobs.ts`, routed at `webui/src/main.ts:226-230` (alias `/agent/multimodal`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Job statuses come from real `MultimodalOutcome` records. Do not show a success state for a job the backend has not completed.

---

### UI-S-50 — Settings — Agent

| Field | Value |
|---|---|
| Screen Identifier | UI-S-50 |
| Route | /settings |
| Facet | Settings |
| Primary actor | Agent owner |
| Stores | `agent-store` |
| APIs | REST `/api/v2/settings/` (measured in `webui/src/`) |
| Related | UI-C-104, UI-C-105, UI-A-105, UI-A-106, UI-F-055 |

**Purpose.** Edit agent-scope settings in one place.

**Regions.** left rail = settings scope tabs; workspace = settings form; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-104 | settings form | scoped key/value form | resolved settings | per-key validation | key is env-owned or Vault-owned | This setting is owned by environment or Vault and is read-only here |
| UI-C-105 | settings search | search box | empty | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-105 | Save settings | Save button | write settings | none | revert to resolved values |
| UI-A-106 | Reset to defaults | Reset button | clear overrides | UI-M-03 destructive confirm | none — re-enter values |

**States.** loading — "Loading settings…"; empty — "No settings in this scope."; error — "Settings could not be saved."; permission-denied — "You need `settings:write` to change settings."; offline — "Offline — changes are not saved."

**Features.** UI-F-055.

**Trace.** `webui/src/views/saas-settings.ts`, `webui/src/components/settings-form.ts`, routed at `webui/src/main.ts:426-430`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Settings scopes follow `SOMA-SETTINGS-MODEL-001.md` (see `SOMA-01-UIUX-005.md`). Secrets render as a masked placeholder plus "rotate in Vault" — never a value (REQ-UIX-006). A read-only key states *why* it is read-only.

---

### UI-S-51 — Settings — Models

| Field | Value |
|---|---|
| Screen Identifier | UI-S-51 |
| Route | /settings/models |
| Facet | Settings |
| Primary actor | Agent owner |
| Stores | `agent-store` |
| APIs | REST `/api/v2/llm` (measured in `webui/src/`) |
| Related | UI-C-106, UI-C-107, UI-A-107, UI-A-108, UI-F-056 |

**Purpose.** Configure the model catalogue the four Brain roles bind against.

**Regions.** left rail = settings scope tabs; workspace = model catalogue table; right rail = Brain surface (UI-X-07).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-106 | model catalogue table | table of `LLMModelConfig` rows | all configured models | never | never | — |
| UI-C-107 | model edit form | endpoint + credential fields | selected model | endpoint URL valid | model is in use by a capsule role | This model is bound to a capsule role and cannot be deleted |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-107 | Save model | Save button | write model config | none | re-edit fields |
| UI-A-108 | Test model | Test button | probe the model endpoint | none | none — read-only probe |

**States.** loading — "Loading models…"; empty — "No models configured."; error — "Model config could not be saved."; permission-denied — "You need `settings:write` to change models."; offline — "Offline — changes are not saved."

**Features.** UI-F-056.

**Trace.** `webui/src/views/saas-settings-models.ts`, `saas-admin-models-list.ts`, routed at `webui/src/main.ts:414-418` (alias `/agent/models`; platform catalogue at `/platform/models` `:106-110`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** API keys for model endpoints render as a masked placeholder plus "rotate in Vault" (REQ-UIX-006). Never print a provider key into the model table.

---

### UI-S-52 — Settings — Channels

| Field | Value |
|---|---|
| Screen Identifier | UI-S-52 |
| Route | /settings/channels |
| Facet | Settings |
| Primary actor | Agent owner |
| Stores | `agent-store` |
| APIs | REST `/api/v2/bridges/channels` and `/api/v2/bridges/channels/` (measured in `webui/src/`) |
| Related | UI-C-108, UI-C-109, UI-A-109, UI-A-110, UI-F-057 |

**Purpose.** Configure channel bridges (WhatsApp, Telegram, Email) as module contributions.

**Regions.** left rail = settings scope tabs; workspace = channel cards + config; right rail = none.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|
| UI-C-108 | channel cards | card grid | installed bridge modules | never | bridge module not installed | Install the bridge module first |
| UI-C-109 | channel config form | token + webhook fields | empty | token format | module is `always_enabled` and locked | Module is always enabled; this field is locked |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-109 | Connect channel | Connect button | register webhook / poller | none | disconnect |
| UI-A-110 | Disconnect channel | Disconnect button | remove channel registration | UI-M-03 destructive confirm | reconnect |

**States.** loading — "Loading channels…"; empty — "No channels configured."; error — "Channel could not be connected."; permission-denied — "You need `channel:manage` to change channels."; offline — "Offline — changes are not saved."

**Features.** UI-F-057.

**Trace.** `webui/src/views/saas-settings-channels.ts`, routed at `webui/src/main.ts:420-424` (alias `/agent/channels`); bridge modules `admin/bridges/services/telegram_bridge.py`, `whatsapp_bridge.py`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Channel tokens render as a masked placeholder plus "rotate in Vault" (REQ-UIX-006). QR/connected state MUST come from the real bridge API — never a static "connected" badge.

---

### UI-S-53 — Settings — External & Developer

| Field | Value |
|---|---|
| Screen Identifier | UI-S-53 |
| Route | NEW |
| Facet | Settings |
| Primary actor | Agent owner / developer |
| Stores | `agent-store` |
| APIs | REST `/api/v2/secrets`, `/api/v2/settings/` (measured in `webui/src/`) |
| Related | UI-C-110, UI-C-111, UI-A-111, UI-A-112, UI-F-058 |

**Purpose.** Host external-service and developer settings, including secret references and debug toggles.

**Regions.** left rail = settings scope tabs; workspace = external + developer forms; right rail = Debug surface (UI-X-05).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-110 | external settings form | endpoint + credential-reference fields | resolved values | URL valid | secret value is Vault-owned | Secret is stored in Vault — rotate it there |
| UI-C-111 | developer toggles | debug + verbose toggles | off | never | user is not a developer role | Developer toggles require the `developer` role |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-111 | Save external settings | Save button | write external settings | none | re-edit fields |
| UI-A-112 | Rotate secret reference | Rotate button | invalidate and re-issue secret reference | UI-M-03 destructive confirm | none — old secret revoked |

**States.** loading — "Loading settings…"; empty — "No external settings configured."; error — "Settings could not be saved."; permission-denied — "You need `settings:write` and the `developer` role."; offline — "Offline — changes are not saved."

**Features.** UI-F-058.

**Trace.** no dedicated view today; `/api/v2/secrets` measured in `webui/src/`; see also `webui/src/views/saas-admin-api-keys.ts`, `saas-admin-feature-flags.ts` (routed, but without UI-S identifiers — §8 H-09); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** **Secrets rule (REQ-UIX-006):** every secret renders as a masked placeholder plus "rotate in Vault". Never a value, never a truncated value that leaks a prefix. The "rotate" action invalidates the old secret — say so in the confirmation copy.

---

## 6. Surfaces (UI-X-01 … UI-X-08)

The right rail hosts eight surfaces. All eight render on the rail at all times. A surface that is
not available is **present-but-disabled** with its blocking reason printed inline (REQ-UIX-020).
Surfaces never own a route; they are chrome-adjacent panels opened from UI-S-00 UI-C-014. Surface
blocks use the house per-screen block shape; `Route` is `—` because a surface is not routable.

### UI-X-01 — Files

| Field | Value |
|---|---|
| Screen Identifier | UI-X-01 |
| Route | — (surface; not routable) |
| Facet | Capsule |
| Primary actor | Any authenticated user |
| Stores | `workspace-store` |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-112, UI-A-113, UI-F-059, UI-M-01 |

**Purpose.** Browse and reference files in the capsule's working set.

**Regions.** left rail = navigation; workspace = current screen; right rail = this surface (file tree).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-112 | file tree | tree view | workspace root | never | filesystem access is disabled on this deployment | Filesystem access is not enabled on this deployment |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-113 | Open file | node click | load into Editor surface (UI-X-04) | none | close tab |

**States.** loading — "Loading files…"; empty — "No files in the working set."; error — "Files could not be listed."; permission-denied — "You need `files:read` to browse files."; offline — "Offline — listing may be stale."

**Features.** UI-F-059.

**Trace.** `webui/src/components/saas-right-panel.ts`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** File names and sizes come from a real listing. Never fabricate sample files to fill an empty tree.

---

### UI-X-02 — Tools

| Field | Value |
|---|---|
| Screen Identifier | UI-X-02 |
| Route | — (surface; not routable) |
| Facet | Hands |
| Primary actor | Any authenticated user |
| Stores | `agent-store` |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-113, UI-A-114, UI-F-060, UI-M-01 |

**Purpose.** Show the tools the current Capsule can call and their policy bucket.

**Regions.** left rail = navigation; workspace = current screen; right rail = this surface (tool list).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-113 | tool list | list with policy badges | enabled capabilities | never | no capsule selected | Select a capsule to see its tools |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-114 | Inspect tool | row click | open Drawer (UI-M-01) with tool schema | none | close drawer |

**States.** loading — "Loading tools…"; empty — "No tools attached to this capsule."; error — "Tools could not be loaded."; permission-denied — "You need `capability:read` to view tools."; offline — "Offline — tool list may be stale."

**Features.** UI-F-060.

**Trace.** `webui/src/components/saas-right-panel.ts`, `saas-tool-timeline.ts`; policy from `admin/core/models/core.py:267-277`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Policy badges reflect `tool_policy` exactly. A tool in `denied` never shows as callable.

---

### UI-X-03 — Browser

| Field | Value |
|---|---|
| Screen Identifier | UI-X-03 |
| Route | — (surface; not routable) |
| Facet | Brain |
| Primary actor | Any authenticated user |
| Stores | `brain-store` |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-114, UI-A-115, UI-F-061 |

**Purpose.** Show the agent's browsing context.

**Regions.** left rail = navigation; workspace = current screen; right rail = this surface (viewport + URL bar).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-114 | browser viewport | viewport + URL bar | last visited URL | never | no `browser_model` bound | Bind a browser model on UI-S-02 first |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-115 | Navigate | URL bar / link | load URL in viewport | none | back navigation |

**States.** loading — "Loading page…"; empty — "No browsing context yet."; error — "Page could not be loaded."; permission-denied — "Browsing is not permitted for this capsule."; offline — "Offline — browsing requires the network."

**Features.** UI-F-061.

**Trace.** `webui/src/components/saas-right-panel.ts`; `browser_model` FK at `admin/core/models/core.py:230-237`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** The viewport shows only pages the agent actually loaded. Do not show a homepage that was never fetched.

---

### UI-X-04 — Editor

| Field | Value |
|---|---|
| Screen Identifier | UI-X-04 |
| Route | — (surface; not routable) |
| Facet | Soul |
| Primary actor | Any authenticated user |
| Stores | `workspace-store` |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-115, UI-A-116, UI-F-062 |

**Purpose.** Edit a file or prompt fragment with syntax highlighting.

**Regions.** left rail = navigation; workspace = current screen; right rail = this surface (code editor).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-115 | code editor | editor with language chip | selected buffer | never | file is read-only on disk | This file is read-only |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-116 | Save buffer | Save button | write buffer to disk | none | revert buffer |

**States.** loading — "Opening file…"; empty — "No file open."; error — "File could not be saved."; permission-denied — "You need `files:write` to edit files."; offline — "Offline — save requires the server."

**Features.** UI-F-062.

**Trace.** `webui/src/components/saas-right-panel.ts`; code-block hook noted in `SOMA-UI-PARITY-002.md` B-2 (`utils/markdown.ts` `onCodeBlock`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Syntax highlighting is specified here; do not claim a highlighter exists in the current bundle without evidence.

---

### UI-X-05 — Debug

| Field | Value |
|---|---|
| Screen Identifier | UI-X-05 |
| Route | — (surface; not routable) |
| Facet | Governance |
| Primary actor | Developer / auditor |
| Stores | `activity-store` |
| APIs | WebSocket `/ws/v2/` (`webui/src/main.ts:490`) |
| Related | UI-C-116, UI-A-117, UI-F-063 |

**Purpose.** First-class debug surface: filterable event stream, request inspector, WS frame log.

**Regions.** left rail = navigation; workspace = current screen; right rail = this surface (event stream).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-116 | event stream filter | text + level filter | all events | never | user lacks `debug:read` | Debug visibility requires the `debug:read` permission |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-117 | Clear stream | Clear button | clear local buffer | none | none — buffer is local |

**States.** loading — "Attaching to event stream…"; empty — "No events yet."; error — "Event stream disconnected."; permission-denied — "Debug visibility requires the `debug:read` permission."; offline — "Offline — live stream is paused."

**Features.** UI-F-063.

**Trace.** `webui/src/components/saas-right-panel.ts`, `webui/src/services/websocket-client.ts`; WS endpoints `/ws/v2/` (`webui/src/main.ts:490`); UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** The stream shows real frames only. Do not inject example events to demonstrate filtering.

---

### UI-X-06 — Capsule

| Field | Value |
|---|---|
| Screen Identifier | UI-X-06 |
| Route | — (surface; not routable) |
| Facet | Capsule |
| Primary actor | Any authenticated user |
| Stores | `workspace-store`, `agent-store` |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-117, UI-A-118, UI-F-064 |

**Purpose.** Show the selected Capsule's identity, version, lifecycle and certification at a glance.

**Regions.** left rail = navigation; workspace = current screen; right rail = this surface (capsule summary).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-117 | capsule summary panel | read-only summary | selected capsule | never | no capsule selected | Select a capsule to see its summary |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-118 | Open capsule editor | Edit button | navigate to UI-S-12 | none | back navigation |

**States.** loading — "Loading capsule…"; empty — "No capsule selected."; error — "Capsule could not be loaded."; permission-denied — "You need `capsule:read` to view this capsule."; offline — "Offline — summary may be stale."

**Features.** UI-F-064.

**Trace.** `webui/src/components/saas-right-panel.ts`; model summary from `admin/core/models/core.py:109-336`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Certification state mirrors `is_certified` (`core.py:339-341`): true only when `registry_signature` is present **and** status is `active`.

---

### UI-X-07 — Brain

| Field | Value |
|---|---|
| Screen Identifier | UI-X-07 |
| Route | — (surface; not routable) |
| Facet | Brain |
| Primary actor | Any authenticated user |
| Stores | `brain-store` |
| APIs | REST `/api/v2/` prefix (`webui/src/main.ts:489`) |
| Related | UI-C-118, UI-A-119, UI-F-065 |

**Purpose.** Show live Brain state: neuromodulators, adaptation, memory usage, cognitive load.

**Regions.** left rail = navigation; workspace = current screen; right rail = this surface (brain state panel).

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-118 | brain state panel | read-only meters | disconnected | never | never | — |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-119 | Refresh brain state | Refresh button | re-fetch SomaBrain state | none | none — read-only |

**States.** loading — "Connecting to SomaBrain…"; empty — "No brain state available."; error — "SomaBrain did not answer."; permission-denied — "You need `brain:read` to view brain state."; offline — "Offline — brain state is stale."

**Features.** UI-F-065.

**Trace.** `webui/src/components/saas-brain-panel.ts`, `webui/src/stores/brain-store.ts`; model state at `admin/core/models/core.py:292-302`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** Meter values require a real sync. `brain-store.ts:7-11` types the fourth neuromodulator as `noradrenaline` while `core.py:297` calls it `norepinephrine`, and the store has no `last_synced_at` field although the model carries one (`core.py:299`) — tracked in §8 H-08 and H-11. Until the store carries `last_synced_at`, this panel MUST NOT claim a value is live.

---

### UI-X-08 — Desktop — GATED

| Field | Value |
|---|---|
| Screen Identifier | UI-X-08 |
| Route | — (surface; not routable) |
| Facet | Body |
| Primary actor | Operator (when available) |
| Stores | — (no backend today) |
| APIs | — (no backend today) |
| Related | UI-C-119, UI-A-120, UI-F-066, UI-F-070 |

**Purpose.** Would show a remote-desktop view of the agent's host. **Not available today — GATED.**

**Regions.** left rail = navigation; workspace = current screen; right rail = this surface, rendered as a disabled frame carrying its blocking reason.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-119 | desktop viewport | viewport (present-but-disabled) | none | n/a | always | Requires a remote-desktop capability in somaAgent01. Not available today. |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-120 | Open desktop session | button (present-but-disabled) | none | n/a | n/a |

**States.** The surface renders its disabled frame with the blocking reason printed inline. There is
no loading, empty or live state, because there is no backend. The copy is exactly:
"Requires a remote-desktop capability in somaAgent01. Not available today."

**Features.** UI-F-066, UI-F-070.

**Trace.** surface rail at UI-S-00 UI-C-014; no remote-desktop capability exists in the codebase;
UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.** **This surface is GATED.** Every control on it renders **present-but-disabled**
with the blocking reason printed inline (REQ-UIX-007, REQ-UIX-020). The banned placeholder phrase
defined in §2.3 is forbidden here and everywhere else (REQ-UIX-004). The surface stays on the rail —
it is never omitted, never hidden, never shown as a working desktop.

---

## 7. Global chrome — UI-S-00

The frame every screen sits inside. Specified per `SOMA-UI-IDREG-001.md` "Chrome — UI-S-00" and
`SOMA-UI-PARITY-002.md` §3.3.

| Field | Value |
|---|---|
| Screen Identifier | UI-S-00 |
| Route | — (chrome; present on every authenticated route) |
| Facet | — (cross-cutting) |
| Primary actor | Any authenticated user |
| Stores | `iq-store`, `brain-store`, `workspace-store`, `agent-store` |
| APIs | REST `/api/v2/auth/me` (`webui/src/main.ts:38`); WebSocket `/ws/v2/` (`:490`) |
| Related | UI-C-001…014, UI-A-001…006, UI-F-001…005, UI-M-01…03 |

**Purpose.** Keep the capsule, its lifecycle, its persona knobs, its facets, its instances, its
neurochemistry and its surfaces visible on every screen.

**Regions.** top bar = capsule switcher + version chip + lifecycle chip + persona knobs x3 + command
palette; left rail = navigation; workspace = facet tabs x6; right rail = instance strip + neuro
meters x4 + surface rail x8.

**Controls.**

| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |
|---|---|---|---|---|---|---|
| UI-C-001 | capsule switcher | select + prev/next | last selected capsule | never | no capsules in tenant | No capsules in this tenant |
| UI-C-002 | version chip | read-only chip | `Capsule.version` (`core.py:133`) | never | never | — |
| UI-C-003 | lifecycle chip | status chip + transition menu | `Capsule.status` (`core.py:147-153`) | transitions only `draft→active`, `active→archived` | status is `archived` | Archived capsules cannot transition |
| UI-C-004 | persona knob — `intelligence_level` | slider 1–10 | 7 (`iq-store.ts:35`) | integer 1–10 | capsule status is `active` | Active capsules are immutable; edit spawns a child version (REQ-UIX-012) |
| UI-C-005 | persona knob — `autonomy_level` | slider 1–10 | 5 (`iq-store.ts:36`) | integer 1–10 | capsule status is `active` | Active capsules are immutable; edit spawns a child version (REQ-UIX-012) |
| UI-C-006 | persona knob — `resource_budget` | slider 0.01–1.00 | 0.05 (`iq-store.ts:37`) | 0.01–1.00 | capsule status is `active` | Active capsules are immutable; edit spawns a child version (REQ-UIX-012) |
| UI-C-007 | command palette | overlay (Cmd-K / Ctrl-K) | closed | never | never | — |
| UI-C-008 | facet tabs x6 | tablist: Soul · Brain · Hands · Memory · Body · Governance | first facet | never | never | — |
| UI-C-009 | instance strip | horizontal chip list | running instances | never | never | — |
| UI-C-010 | neuro meter — dopamine | read-only gauge + `last_synced_at` | no value until synced | never | never | — |
| UI-C-011 | neuro meter — serotonin | read-only gauge + `last_synced_at` | no value until synced | never | never | — |
| UI-C-012 | neuro meter — norepinephrine | read-only gauge + `last_synced_at` | no value until synced | never | never | — |
| UI-C-013 | neuro meter — acetylcholine | read-only gauge + `last_synced_at` | no value until synced | never | never | — |
| UI-C-014 | surface rail x8 | icon rail: Files · Tools · Browser · Editor · Debug · Capsule · Brain · Desktop | first available surface | never | surface is gated | see per-surface blocking reason (UI-X-08: "Requires a remote-desktop capability in somaAgent01. Not available today.") |

**Actions.**

| UI-A-* | action | trigger | effect | confirmation | undo |
|---|---|---|---|---|---|
| UI-A-001 | Switch capsule | switcher change | rebind all capsule-scoped chrome | none | switch back |
| UI-A-002 | Transition lifecycle | lifecycle menu | write `Capsule.status` | UI-M-03 destructive confirm | reverse transition while permitted |
| UI-A-003 | Adjust persona knob | slider release | write `persona_config.knobs` | none | slider restore |
| UI-A-004 | Invoke command palette | Cmd-K / Ctrl-K / button | open palette overlay (UI-M-02) | none | ESC closes |
| UI-A-005 | Select facet tab | tab click | show one facet (Chat is a peer, not a child) | none | select another tab |
| UI-A-006 | Select chrome context item | chip / rail click | open instance strip item or surface panel | none | close panel |

**States.** loading — "Loading workspace…"; empty — "No capsules in this tenant. Create one to begin."; error — "Workspace chrome could not be loaded."; permission-denied — "You need `capsule:read` to use the workspace."; offline — "Offline — chrome shows the last known capsule state, which may be stale."

**Features.** UI-F-001, UI-F-002, UI-F-003, UI-F-004, UI-F-005.

**Trace.** IA diagram `docs/design/SOMA-UI-PARITY-002.md` §3.3; knobs at `admin/core/models/core.py:254-265`; derived settings at `webui/src/stores/iq-store.ts:15-28`; neuro state at `admin/core/models/core.py:292-302`; instances at `:423-437`; UIX-AT-* → `SOMA-01-UIUX-004`.

**Honesty notes.**

- The four neuro meters are **read-only** and each shows `last_synced_at` (REQ-UIX-010). No meter
  renders a value without a real sync timestamp.
- The twelve derived AgentIQ settings render as **read-only** readouts beside the three knobs
  (REQ-UIX-008). They are never editable (N-5).
- The three knobs are the only editable AgentIQ inputs (REQ-UIX-021).
- UI-X-08 stays on the rail as a disabled entry with its blocking reason inline — never removed,
  never with the banned placeholder phrase of §2.3.
- Lifecycle transitions are explicit (REQ-UIX-011). Saving a facet field never silently promotes a
  draft to active.

---

## 8. Honesty notes — tracked findings

Cross-reference of known defects. **This document does not change production code.** Each finding
is evidence-backed with `file:line` and is tracked here so no screen spec claims the defect away.

### 8.1 Router defects (webui/src/main.ts, 492 lines, measured 2026-09-28)

| ID | Finding | Evidence | Severity |
|---|---|---|---|
| H-01 | **Unreachable route branch — `/platform/features`.** The live branch renders `saas-feature-catalog`; a later branch for the same path renders `saas-features-view` and can never run. | live: `webui/src/main.ts:179-183`; dead: `webui/src/main.ts:296-300` | P2 functional dead code |
| H-02 | **Unreachable route branch — `/admin/users`.** The live branch renders `saas-users-view`; a later branch renders `saas-tenant-users` and can never run. | live: `webui/src/main.ts:249-253`; dead: `webui/src/main.ts:362-366` | P2 functional dead code |
| H-03 | **Unreachable route branch — `/admin/agents` and `/platform/audit`.** `/admin/agents` live-renders `saas-agents-view`, while `webui/src/main.ts:368-372` would render `saas-tenant-agents` and can never run. `/platform/audit` live-renders `saas-audit-dashboard`, while the `/audit \| /admin/audit \| /platform/audit` condition at `webui/src/main.ts:382-386` can never match `/platform/audit` (already returned) — only `/audit` and `/admin/audit` reach `saas-audit-log`. | `/admin/agents` live: `:290-294`, dead: `:368-372`; `/platform/audit` live: `:303-307`, dead arm: `:382-386` | P2 functional dead code |
| H-04 | **`/logout` is client-side only — security relevant.** It removes `localStorage` keys `saas_auth_token` and `saas_user` and redirects to `/login`. It does **not** call a server logout endpoint and does **not** clear the session cookie that `checkAuth()` reads via `credentials: 'include'`. The session therefore survives "logout" on the same browser until the cookie expires. | `webui/src/main.ts:342-347` (client-only logout); `webui/src/main.ts:36-43` (`checkAuth()` reads `/api/v2/auth/me` with `credentials: 'include'`) | **P1 security** |
| H-05 | **UI-S-12 route disagreement.** `SOMA-UI-IDREG-001.md` specifies `/workspace/:id` for the Capsule editor, but the router matches only exact `/workspace`. A URL `/workspace/<uuid>` matches no branch and falls through to the default `saas-chat`. | `SOMA-UI-IDREG-001.md` UI-S-12 row; `webui/src/main.ts:396-400` (exact `/workspace` only); default fallthrough `webui/src/main.ts:466-468` | P1 specification/route mismatch |
| H-06 | **`/themes` is a placeholder redirect.** The branch redirects to `/settings` with the comment "Themes view might not exist yet". It is not a screen and must not be specified as one. | `webui/src/main.ts:438-443` | P3 placeholder |
| H-10 | **Duplicate `/mode-select` branch.** A second identical branch exists and is unreachable. | live: `webui/src/main.ts:323-327`; dead: `webui/src/main.ts:349-353` | P3 dead code |

### 8.2 State and naming defects

| ID | Finding | Evidence | Severity |
|---|---|---|---|
| H-07 | **Persona knob key disagreement.** The client store types knobs as `intelligence`, `autonomy`, `budget`; the model stores them as `intelligence_level`, `autonomy_level`, `resource_budget`. UI labels follow the model keys (REQ-UIX-021). | `webui/src/stores/iq-store.ts:9-13` vs `admin/core/models/core.py:258-260` | P3 naming |
| H-08 | **Neuromodulator key disagreement.** `brain-store.ts` types the fourth neuromodulator as `noradrenaline`; the model field is `norepinephrine`. Also: `/tools` currently renders the platform feature catalogue rather than a capsule-scoped Hands editor. | `webui/src/stores/brain-store.ts:7-11` vs `admin/core/models/core.py:292-302`; `webui/src/main.ts:432-435` | P2 mapping |
| H-09 | **Unregistered routed views.** The following views are routed in `webui/src/main.ts` but have no `UI-S-*` identifier in `SOMA-UI-IDREG-001.md`: `saas-admin-api-keys` (`:172-176`), `saas-admin-feature-flags` (`:166-170`), `saas-admin-models-list` (`:106-110`), `saas-role-matrix` (`:147-151`), `saas-user-detail` (`:256-260`), `saas-tenant-settings` (`:277-281`), `saas-billing` (`:309-313`), `saas-onboarding` (`:336-340`), `settings-form` for `/platform/settings/*` (`:233-240`), `saas-tenants-view` for `/platform/tenants-new` (`:243-247`). They are real surfaces awaiting identifiers — do not invent IDs (REQ-UIX-002). | `webui/src/main.ts` lines cited; `SOMA-UI-IDREG-001.md` screen table | P3 coverage |
| H-11 | **`brain-store` has no `last_synced_at`.** The model carries `last_synced_at` in `neuromodulator_state`, but the client store type omits it, so the UI cannot honestly show a sync timestamp today. Chrome meters (UI-C-010…013) MUST NOT claim live values until the store carries this field (REQ-UIX-010). | `webui/src/stores/brain-store.ts:7-11` (no timestamp field) vs `admin/core/models/core.py:292-302` (`last_synced_at` at `:299`) | P1 honesty |

### 8.3 Router measurement (as measured, for REQ-UIX-014)

| Measure | Value |
|---|---|
| `path === '...'` literal comparisons | 87 occurrences, 81 distinct strings |
| `path.startsWith('...')` prefixes | 5 (`/platform/settings/`, `/admin/settings/`, `/onboarding`, `/invite/`, `/chat/`) |
| `path.match(...)` regex branches | 1 (`/^\/admin\/users\/[^/]+$/` at `webui/src/main.ts:256`) |
| Duplicate `path ===` literals (later occurrence unreachable) | `/platform/features`, `/admin/users`, `/admin/agents`, `/platform/audit`, `/mode-select`, `/select-mode` |
| `createElement(...)` calls | 59 calls, 53 distinct custom elements |
| Distinct elements reachable only via dead branches | 4 (`saas-agents-view`, `saas-features-view`, `saas-tenant-users`, `saas-tenant-agents`) |
| Views / components / stores / services / controllers | 55 / 56 / 6 / 5 / 8 files |

Note: an earlier expectation of "51 distinct route paths → 50 element targets" does not match the
measured router. The measured figures above are reported as measured; the discrepancy is recorded
rather than reconciled by renumbering (REQ-UIX-002, REQ-UIX-014).

### 8.4 Suite-wide honesty rules restated

1. The banned placeholder phrase defined in §2.3 never appears as a specification value (REQ-UIX-004).
2. Every disabled control carries `disabled-when` and `disabled-reason` (REQ-UIX-005).
3. UI-X-08 is GATED with the exact reason "Requires a remote-desktop capability in somaAgent01.
   Not available today.", and its controls render present-but-disabled with that reason inline
   (REQ-UIX-007).
4. Derived AgentIQ settings are read-only (REQ-UIX-008).
5. `RESERVED_HOOKS` render as "reserved — not yet registerable" (REQ-UIX-009).
6. Neuro meters are read-only with `last_synced_at` shown (REQ-UIX-010).
7. Secrets are masked placeholders plus "rotate in Vault" (REQ-UIX-006).
8. H-04 (client-side-only `/logout`) is security-relevant and is stated prominently here and on
   UI-S-29 so no screen spec claims a server-side logout that does not exist.

---

End of Document
