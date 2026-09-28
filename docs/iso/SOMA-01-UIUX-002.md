# SOMA-01-UIUX-002 — User Interface — Modal & Overlay Specification

## Document Control

| Field | Value |
|---|---|
| Document Title | User Interface — Modal & Overlay Specification |
| Document Identifier | SOMA-01-UIUX-002 |
| Version | 1.0.0 |
| Date | 2026-09-28 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-28 |
| Related | `SOMA-01-QMS-001.md`, `SOMA-A0-PARITY-001.md`, `SOMA-01-UIUX-001.md`, `SOMA-01-UIUX-003.md`, `docs/design/SOMA-UI-PARITY-002.md` |
| Source of truth | This document for the three modal patterns; `SOMA-UI-IDREG-001.md` for identifiers; `webui/src/components/saas-glass-modal.ts` and `webui/src/views/*` for current behaviour |
| Audience | UI/UX contributors, product engineering, any agent acting on somaAgent01 |
| Scope | Every modal, dialog, drawer, full-screen surface and non-modal overlay in `webui/` |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-09-28 | SomaTech Engineering | Initial issue. Three-pattern modal system (UI-M-01..03), A0 mapping table, per-screen inventory UI-S-01..53, non-modal overlay contracts, honesty notes. |

## Normative References

| ID | Reference | Role |
|---|---|---|
| N-1 | SOMA-01-QMS-001 | Quality management system |
| N-2 | SOMA-01-DOCS-001 | Document control and traceability procedure |
| N-3 | SOMA-A0-PARITY-001 | Feature clone never code clone; Plan Gate; honesty rules |
| N-4 | SOMA-01-UIUX-001 | Screen and feature specification (the master) |
| N-5 | SOMA-UI-IDREG-001.md | Authoritative ID allocation (UI-M-01..03) |
| N-6 | docs/design/SOMA-UI-PARITY-002.md §4.4 | Authority for the 24 → 3 modal reduction (B-4) |
| N-7 | webui/src/components/saas-glass-modal.ts | Live Dialog shell implementation |
| N-8 | SOMA-UI-TEMPLATE-001.md | House ISO template and honesty rules |

---

## 1. Purpose and Scope

### 1.1 Purpose

Agent Zero ships **24 discrete modal patterns** (context, file-browser, file-tree, rename,
full-screen-input, history, image-viewer, markdown, process-step-detail, scheduler×5, and others —
see N-6 §4.4 and the A0 column of §3 below). That count is a maintenance and accessibility
liability: each modal invents its own size, dismiss model, focus behaviour and stacking order.

This document reduces those 24 usages to **exactly three patterns**, allocated in N-5:

| ID | Pattern | Contract (N-5) |
|---|---|---|
| UI-M-01 | Drawer | right-side, 420px, ESC closes, focus trap |
| UI-M-02 | Full-screen | covers viewport, explicit dismiss only |
| UI-M-03 | Dialog | centred, destructive confirm, ESC closes |

The reduction is **normative**, not aspirational. N-6 §4.4 is the authority: "*Exactly three
surface patterns*: Drawer (inspect/edit), Full-screen (focus: file, image, message), Dialog
(destructive/irreversible only)." N-6 §4.4 also instructs: keep `saas-glass-modal.ts` as the single
Dialog implementation; add Drawer + Full-screen as siblings.

### 1.2 Scope

- All modal, dialog, drawer and full-screen surfaces in `webui/src/`.
- Non-modal overlays (toast, impersonation banner, voice overlay) — specified in §5 under their own
  contracts. They are **not** UI-M-* and MUST NOT be given UI-M identifiers.
- Mapping of Agent Zero modal usages onto the three patterns (§3).
- Per-screen inventory for UI-S-01..53 (§4).

### 1.3 Out of Scope

- Right-rail surfaces UI-X-01..08 (specified in N-4; UI-X-08 Desktop remains GATED).
- Screen-level layout, navigation and facet chrome (N-4).
- Backend API shapes (cited only where a modal's data source is named).

---

## 2. The Three Patterns

Every pattern below is specified across the same eleven dimensions: anatomy, size/position,
trigger, contents, primary / secondary / dismiss actions, focus trap behaviour, ESC behaviour,
validation behaviour, stacking rules, mobile behaviour.

### 2.1 UI-M-01 — Drawer

**Role.** Inspect or edit a bounded object without leaving the current screen. The Drawer is the
workhorse for "look at the detail of this row / step / file" flows.

| Dimension | Specification |
|---|---|
| Anatomy | (1) scrim (click-to-dismiss, optional per instance); (2) panel container; (3) header: title, optional subtitle, close button; (4) scrollable body (default slot); (5) footer with `slot="actions"` (optional). |
| Size / position | Fixed to the **right** edge. Width **420px** on viewports ≥ 768px (N-5). Height 100vh. Max body height 100% minus header/footer. Panel is above the scrim; the page behind is inert. |
| Trigger | Explicit user action on a row, chip, timeline step, tree node or list item ("Inspect", "Details", row click). Never auto-opened on route entry. |
| Contents | Read-only detail panes, small edit forms (≤ 6 fields), file trees, process-step arguments/results, rename fields. **Not** for multi-step wizards (use a dedicated route) and not for destructive confirmations (use UI-M-03). |
| Primary action | Optional. Label states the effect ("Save", "Apply", "Rename"). Enabled only when the form is valid and dirty. |
| Secondary action | Optional. Non-destructive alternative ("Cancel edit", "Reset"). |
| Dismiss actions | (a) close button in header; (b) ESC; (c) scrim click when `closeOnBackdrop` is true; (d) programmatic `close()`. Dismiss with unsaved edits MUST prompt (UI-M-03) "Discard changes?" before closing. |
| Focus trap behaviour | On open: move focus into the panel (first focusable, or the panel container). While open: Tab / Shift+Tab cycle **only** among focusables inside the panel. On close: restore focus to the element that opened the drawer. |
| ESC behaviour | Closes the drawer (N-5: "ESC closes"). If an inner UI-M-03 is stacked on top, ESC closes the inner dialog first. |
| Validation behaviour | Inline field errors (`saas-form-field.error`), never a blocking toast. Invalid state disables the primary action and states the reason next to the field. Submit failure renders an inline error banner inside the drawer body with the server message. |
| Stacking rules | At most **one** Drawer open at a time per screen. A Drawer MAY host one UI-M-03 on top (discard-changes, destructive confirm). A Drawer MUST NOT open another Drawer. Opening a Drawer while a Full-screen (UI-M-02) is open is forbidden. |
| Mobile behaviour (< 768px) | Width becomes 100vw (edge-to-edge sheet). Height 100vh. Scrim remains. Close button stays top-right and keeps a ≥ 44×44px hit target. Footer actions become full-width stacked buttons. |

**Implementation note.** No Drawer primitive exists in `webui/src/components/` as of 2026-09-28.
It SHALL be added as a sibling of `saas-glass-modal.ts` (N-6 §4.4, WU-0.3).

### 2.2 UI-M-02 — Full-screen

**Role.** Immersive focus on a single artefact — a long message, an image, a focused composer —
where the surrounding chrome is a distraction.

| Dimension | Specification |
|---|---|
| Anatomy | (1) full-viewport container (`role="dialog"`, `aria-modal="true"`); (2) top bar: title/counter, dismiss control, optional secondary actions (zoom, copy, download); (3) content stage (centred, scrollable or pannable); (4) optional bottom controls. No scrim — the container covers the viewport. |
| Size / position | Covers 100vw × 100vh. `position: fixed; inset: 0`. `z-index` above every Drawer and Dialog. |
| Trigger | Explicit "expand" / "open full" action from a message, attachment thumbnail, or composer focus control. Never auto-opened. |
| Contents | Rendered markdown of one message; an image with zoom/pan; a focused composer input (A0 `full-screen-input`); a single-file preview. **Not** for lists, tables or settings forms. |
| Primary action | Optional and content-specific ("Copy text", "Download", "Send"). |
| Secondary action | Optional ("Zoom in", "Zoom out", "Fit", "Open original"). |
| Dismiss actions | **Explicit dismiss only** (N-5). (a) close button; (b) optional keyboard shortcut (e.g. `q` or `Esc` when the instance sets `closeOnEscape`) — but scrim-click dismiss does not exist because there is no scrim. Programmatic `close()`. |
| Focus trap behaviour | On open: focus the dismiss control or the content stage. While open: focus is trapped in the top bar + stage + bottom controls. On close: restore focus to the invoking element. |
| ESC behaviour | **Instance-defined.** The pattern default is *explicit dismiss only* (N-5), so ESC is inert unless the instance sets `closeOnEscape`. When it is set, ESC behaves as the close button. Image viewers SHOULD enable it; focused composers SHOULD NOT (ESC is used to cancel an in-progress generation first). |
| Validation behaviour | Not applicable for viewers. For the focused composer: inline send-error inside the stage; never a toast that vanishes under the user's hands. |
| Stacking rules | Exactly **one** Full-screen at a time. Full-screen MAY stack one UI-M-03 (e.g. "Discard draft?"). Full-screen MUST NOT stack a Drawer. A Full-screen MUST NOT open over another Full-screen. |
| Mobile behaviour | Already full-viewport. Top bar collapses to icon-only controls. Safe-area insets (`env(safe-area-inset-*)`) are respected on notched devices. Pinch-zoom is enabled on the image stage. |

**Implementation note.** No Full-screen primitive exists in `webui/src/components/` as of
2026-09-28. `saas-glass-modal` size `full` is a large centred card, **not** UI-M-02 (it keeps a
scrim and a dismiss-by-backdrop). Do not relabel it.

### 2.3 UI-M-03 — Dialog

**Role.** Short, decisive confirmations — above all **destructive or irreversible** ones — and
compact single-purpose forms. This is the only pattern that asks "Are you sure?".

| Dimension | Specification |
|---|---|
| Anatomy | (1) scrim (click-to-dismiss configurable); (2) centred card: (3) header: title, optional subtitle, close button; (4) body (default slot) — warning copy, consequence list, or a short form; (5) footer `slot="actions"`: primary + secondary buttons. |
| Size / position | Centred both axes. Widths by `size` (live shell, N-7): `sm` 400px, `md` 560px, `lg` 720px, `xl` 960px, `full` large centred card. Destructive confirms use `sm` or `md`. Max-height 90vh with body scroll. |
| Trigger | (a) a destructive action button ("Delete…", "Suspend…", "Reset…"); (b) a compact create/edit form that needs no route. NEVER used for passive detail viewing (that is UI-M-01). |
| Contents | Destructive confirm copy naming the object and the consequence; ≤ 8-field forms; blocked-reason panels. **Not** for long content (UI-M-02) or row detail (UI-M-01). |
| Primary action | **Required.** Verb-first, consequence-naming label ("Delete memory", "Suspend user", "Reset parameters"). For destructive dialogs the primary button uses the danger style. Label MUST NOT be a bare "OK". |
| Secondary action | **Required** for destructive confirms: "Cancel" (safe path). Optional for non-destructive forms. |
| Dismiss actions | (a) close button; (b) ESC (N-5: "ESC closes"); (c) scrim click when `closeOnBackdrop`; (d) secondary/cancel button; (e) programmatic `close()`. Dismiss = cancel; it MUST NOT commit. |
| Focus trap behaviour | On open: focus the **safe** action (Cancel / secondary) for destructive dialogs, or the first field for forms. While open: Tab cycles only inside the card. On close: restore focus to the invoker. |
| ESC behaviour | Closes the dialog and cancels the operation. ESC is never a synonym for confirm. |
| Validation behaviour | Forms: inline field errors; primary stays disabled while invalid. Destructive confirms: no fields; optional typed confirmation ("type the name to confirm") for irreversible multi-object deletes. Server rejection renders an inline error in the body and keeps the dialog open. |
| Stacking rules | At most **two** UI-M-03 visible (one host Drawer/Full-screen + one Dialog). Dialog-on-Dialog beyond that is forbidden. The topmost dialog owns ESC and focus. |
| Mobile behaviour | Width `calc(100vw - 32px)`, max 400px effective. Actions stack full-width, safe action first in DOM order for destructive confirms. Keyboard-open state: dialog scrolls into view; never clip the primary action behind the on-screen keyboard. |

**Implementation note.** `webui/src/components/saas-glass-modal.ts` (tag `saas-glass-modal`) is the
**live generic Dialog shell** and SHALL remain the single Dialog implementation (N-6 §4.4).
Measured properties (N-7:180-186): `open`, `title`, `subtitle`, `size`, `closeOnBackdrop`,
`closeOnEscape`, `showClose`, `noPadding`. Events (N-7:274, 280): `saas-modal-open`,
`saas-modal-close`. Slots: default (body), `footer`, `actions`.

**Gap against this specification (honesty).** The shell's header comment claims "focus trap"
(N-7:9) but the implementation only handles ESC (N-7:190-192) and body scroll lock (N-7:207-213).
A real focus trap is **missing** and is a compliance item for WU-0.3, not a finished behaviour.

---

## 3. Mapping Table — Agent Zero Modal Usage → Three Patterns

Authority: N-6 §4.4 (B-4). The A0 column is reproduced from the parity doc and expanded with the
disposition Soma will take.

### 3.1 Core reduction (verbatim from N-6 §4.4)

| A0 modal | Soma pattern | Rationale |
|---|---|---|
| `context` | **UI-M-01 Drawer** | Bounded inspector of the assembled context lanes; inspect-only. |
| `process-step-detail` | **UI-M-01 Drawer** | Args/result/duration/error for one tool step; row-level detail (N-6 §3: "B-4 drawer for detail, not a modal"). |
| `file-browser` | **UI-M-01 Drawer** | Bounded browse/select task beside the current screen. |
| `file-tree` | **UI-M-01 Drawer** | Same shape as file-browser; tree navigation inside a 420px panel. |
| `rename` | **UI-M-01 Drawer** | Single-field edit with save/cancel. (Soma today already renames inline in the chat list — `saas-chat.ts:2190-2211`; keep inline where a row exists, Drawer when rename is invoked from a context menu without a row.) |
| `full-screen-input` | **UI-M-02 Full-screen** | Focus composer mode; explicit dismiss. |
| `image-viewer` | **UI-M-02 Full-screen** | Zoom/pan on one artefact; explicit dismiss. |
| `markdown` | **UI-M-02 Full-screen** | Rendered full view of one message (N-6 §3 "B-2 highlight inside"). |
| `scheduler` × 5 | **UI-M-03 Dialog** or **dedicated route** | Five discrete scheduler modals collapse into one Dialog for simple create/toggle, and a dedicated route for the full scheduler editor. Never five modals. |
| any destructive confirm | **UI-M-03 Dialog** | The defining use of Dialog (N-5, N-6 §4.4). |

### 3.2 Expanded dispositions

| A0 modal / surface | Soma pattern | Status today | Note |
|---|---|---|---|
| `history` modal | Not a modal — searchable list in the left rail | DONE (N-6 §3) | Export format picker (md/json) is a UI-M-03 Dialog. |
| `attachments` drag-drop overlay | Not a modal — inline previews | PARTIAL (N-6 §3) | Composer drag-drop overlay is specified in §5.4; per-file preview chips are inline. |
| `process-group` collapsible steps | Not a modal — inline in `saas-tool-timeline.ts` | PARTIAL | Step detail opens UI-M-01 Drawer. |
| plugin `execute` modal (A0 Plugins) | **UI-M-03 Dialog** | MISSING | Capsule Module execute confirmation. |
| plugin `config` modal (A0 Plugins) | **UI-M-01 Drawer** or dedicated route | PARTIAL | Module config is settings-section injection (see UIUX-003 §5); a Drawer is only for a quick toggle/config glance. |
| notification modal (A0 Notifications) | **UI-M-03 Dialog** for actionable alerts | partial toasts | Passive notifications are toasts (§5.1), never Dialogs. |
| delete/reset confirms (A0 various) | **UI-M-03 Dialog** | PARTIAL | Eight live `window.confirm()` call sites must migrate (§4). |

### 3.3 Anti-patterns (forbidden)

1. A fourth pattern. If a surface does not fit Drawer / Full-screen / Dialog, it is a **route** or
   an **inline region** — not a new modal.
2. A modal with no data source (see §6).
3. A destructive confirm implemented as `window.confirm()`.
4. Relabelling `saas-glass-modal` size `full` as UI-M-02.
5. Auto-opening any modal on route entry without a user gesture.

---

## 4. Per-screen Modal Inventory (UI-S-01 … UI-S-53)

Cross-referenced against `webui/src/main.ts` routing and `webui/src/views/*` as measured on
2026-09-28. "Pattern" is the **target** pattern under this specification; "Today" is what the code
actually does.

| Screen | View (from `main.ts`) | Opens a modal today? | Pattern | Contents | Source |
|---|---|---|---|---|---|
| UI-S-01 Soul — persona & system prompt | `saas-capsule-editor` (via workspace) | No | — | (no modal; inline editor) | `webui/src/components/saas-capsule-editor.ts` |
| UI-S-02 Brain — model & IQ | `saas-cognitive-panel.ts` | Yes — `window.confirm` | **UI-M-03** | "Reset all adaptation parameters to defaults? This cannot be undone." | `saas-cognitive-panel.ts:814` |
| UI-S-03 Hands — tools & capabilities | `saas-feature-catalog.ts` | No | — | — | `main.ts:179-180` |
| UI-S-04 Memory — retention & recall | `saas-memory-view.ts` | Yes — `window.confirm` | **UI-M-03** | "Delete this memory?" | `saas-memory-view.ts:785` |
| UI-S-05 Body — resources & limits | NEW | No | — | screen not built | N-5 |
| UI-S-06 Governance — constitution & hooks | NEW | No | — | screen not built | N-5 |
| UI-S-07 Chat workspace | `saas-chat.ts` | Yes — `window.confirm` | **UI-M-03** | `Delete "<title>"?` for a conversation | `saas-chat.ts:2260` |
| UI-S-08 Message detail | `saas-chat.ts` | No (target: UI-M-02) | **UI-M-02** | rendered markdown of one message (A0 `markdown`) | target per §3 |
| UI-S-09 Conversation export | NEW (export is inline download) | No | **UI-M-03** (format picker) | md/json choice before download | `saas-chat.ts:1288-1321`, `1863-1891` |
| UI-S-10 Conversation queue | NEW | No | — | screen not built | N-5 |
| UI-S-11 Capsule list | `saas-workspace.ts` | No | — | — | `main.ts:420-421` |
| UI-S-12 Capsule editor | `saas-workspace.ts` | No | — | — | `main.ts:420-421` |
| UI-S-13 Version rail & diff | NEW | No | **UI-M-01** (target) | version diff inspector | target per N-4 |
| UI-S-14 Instances | NEW | No | — | screen not built | N-5 |
| UI-S-15 Module list | NEW | No | — | screen not built | N-5 |
| UI-S-16 Module detail & config | NEW | No | **UI-M-01** (target) | quick module config glance | target per §3.2 |
| UI-S-17 Capability registry | NEW | No | — | screen not built | N-5 |
| UI-S-18 Capability detail & hook bindings | NEW | No | **UI-M-01** (target) | hook binding inspector | target per N-4 |
| UI-S-19 Tenants | `saas-tenants.ts` | **Yes** — `saas-glass-modal` `size="lg"` | **UI-M-03** (detail form) or **UI-M-01** | Tenant detail: status, plan, agents, users, MRR, created; action "Edit Tenant" | `saas-tenants.ts:379-419` |
| UI-S-20 Tenant wizard | `saas-tenant-wizard.ts` | No | — | wizard is a **route**, not a modal (§3.3.1) | `main.ts:154-155` |
| UI-S-21 Tenant dashboard | `saas-tenant-dashboard.ts` | No | — | — | `main.ts:375-376` |
| UI-S-22 Users | `saas-tenant-users.ts` / `saas-user-detail.ts` | Yes — `window.confirm` | **UI-M-03** | "Are you sure you want to suspend this user?" | `saas-user-detail.ts:404` |
| UI-S-23 Roles & role matrix | `saas-admin-roles-list.ts` | **Yes** — `saas-glass-modal` `size="lg"` | **UI-M-03** (form) | Edit Role Permissions: name, code (disabled), agent-mode toggles, permission matrix (matrix currently unavailable — states its blocking reason) | `saas-admin-roles-list.ts:260-322` |
| UI-S-24 Permissions | `saas-permissions.ts` | No | — | — | `main.ts:160-161` |
| UI-S-25 Billing | `saas-tenant-billing.ts` | No | — | — | `main.ts:316-317` |
| UI-S-26 Subscriptions | `saas-subscriptions.ts` | Yes — `saas-subscription-editor` (own overlay) + `window.confirm` | **UI-M-03** | tier editor form; `Delete this custom tier? Tenants using it will need to be reassigned.` | `saas-subscriptions.ts:308`, `saas-subscription-editor.ts` |
| UI-S-27 Usage analytics | `saas-usage-analytics.ts` | No | — | — | `main.ts:120-121` |
| UI-S-28 Tier builder | `saas-tier-builder.ts` | No | — | — | `main.ts:113-114` |
| UI-S-29 Login | `saas-login.ts` | No | — | — | `main.ts:53-61` |
| UI-S-30 Register | `saas-register.ts` | No | — | — | `main.ts:66-68` |
| UI-S-31 Forgot password | `saas-forgot-password.ts` | No | — | — | `main.ts:73-75` |
| UI-S-32 MFA setup | `saas-mfa-setup.ts` | No | — | — | `main.ts:414-415` |
| UI-S-33 Auth callback | `saas-auth-callback.ts` | No | — | — | `main.ts:81-82` |
| UI-S-34 Personal profile | `saas-personal-profile.ts` | No (toast only) | — | `show-toast` on save success/failure | `saas-personal-profile.ts:338,345` |
| UI-S-35 Platform profile | `saas-platform-profile.ts` | No (toast only) | — | `show-toast` on save | `saas-platform-profile.ts:394-395` |
| UI-S-36 Mode selection | `saas-mode-selection.ts` | No | — | — | `main.ts:323-324` |
| UI-S-37 Platform dashboard | `saas-platform-dashboard.ts` | No | — | — | `main.ts:100-101` |
| UI-S-38 Platform metrics | `platform-metrics-dashboard.ts` | No | — | — | `main.ts:219-220` |
| UI-S-39 Infrastructure dashboard | `saas-infrastructure-dashboard.ts` | No | — | — | `main.ts:212-213` |
| UI-S-40 Rate limits | `saas-rate-limits.ts` | No | — | — | `main.ts:127-128` |
| UI-S-41 Integrations dashboard | `saas-integrations-dashboard.ts` | No (local toast) | — | 4s toast on connection test | `saas-integrations-dashboard.ts:251-253` |
| UI-S-42 Marketplace | `saas-marketplace.ts` | No | — | — | `main.ts:186-187` |
| UI-S-43 Audit dashboard | `saas-audit-dashboard.ts` | No | — | — | `main.ts:303-304` |
| UI-S-44 Audit log | `saas-audit-log.ts` | No | — | — | `main.ts:461-462` |
| UI-S-45 Agent metrics | `saas-agent-metrics.ts` | No | — | — | `main.ts:193-194` |
| UI-S-46 Voice chat | `saas-voice-chat.ts` | No | — | (voice UI is inline; see §5.3) | `main.ts:457-458` |
| UI-S-47 Voice sessions | `saas-voice-sessions.ts` | No | — | — | `main.ts:451-452` |
| UI-S-48 Voice personas | `saas-voice-personas.ts` | **Yes** — `saas-glass-modal` + `window.confirm` | **UI-M-03** | persona create/edit form; `Delete "<name>"?` | `saas-voice-personas.ts:430-507`, `:328` |
| UI-S-49 Multimodal settings | `saas-multimodal-settings.ts` | No (toast event) | — | `show-toast` on save | `saas-multimodal-settings.ts:328` |
| UI-S-50 Settings — Agent | `saas-settings.ts` | No | — | — | `main.ts:425-426` |
| UI-S-51 Settings — Models | `saas-settings-models.ts` | No (local toast) | — | inline `.toast` message | `saas-settings-models.ts:634` |
| UI-S-52 Settings — Channels | `saas-settings-channels.ts` | Yes — `window.confirm` | **UI-M-03** | "Delete this channel?" | `saas-settings-channels.ts:167` |
| UI-S-53 Settings — External & Developer | NEW | No | **UI-M-01** (target) | secret reveal / connection inspect drawer | target per N-4 |

### 4.1 Modal users that are NOT in UI-S-01..53 (register gap — honesty)

These views open a Dialog today but have no `UI-S-*` identifier in N-5. They MUST be allocated
identifiers in N-5 before they are specified in N-4; until then they are catalogued here so nothing
is silently omitted.

| View | Route | Modal today | Contents | Source |
|---|---|---|---|---|
| `saas-admin-models-list.ts` | `/platform/models` | `saas-glass-modal` `size="md"` | "Add Model to Catalog" form: provider, model ID, display name, type, context window, max output tokens | `saas-admin-models-list.ts:225-310` |
| `saas-admin-api-keys.ts` | `/platform/api-keys` | `saas-glass-modal` `size="md"` | "Add API Key": provider, API key (password field, helper "Keys are stored securely in Secret Manager"), active toggle; Cancel / "Safe & Verify" | `saas-admin-api-keys.ts:189-232` |
| `saas-admin-feature-flags.ts` | `/platform/flags` | **import only** | imports `saas-glass-modal.js` (`:15`) but never instantiates it — dead import | `saas-admin-feature-flags.ts:15` |
| `saas-entity-views.ts` / `entity-manager.ts` | `/admin/users`, `/admin/agents`, `/platform/features` | `window.confirm` | generic entity action confirm: `Are you sure you want to <action> this <entity>?` | `entity-manager.ts:397` |

### 4.2 Migration obligations (from `window.confirm` → UI-M-03)

| Site | Copy today | Target |
|---|---|---|
| `saas-chat.ts:2260` | `Delete "<title>"?` | UI-M-03, danger primary "Delete conversation" |
| `saas-memory-view.ts:785` | `Delete this memory?` | UI-M-03, danger primary "Delete memory" |
| `saas-cognitive-panel.ts:814` | `Reset all adaptation parameters to defaults? This cannot be undone.` | UI-M-03, danger primary "Reset parameters" |
| `saas-settings-channels.ts:167` | `Delete this channel?` | UI-M-03, danger primary "Delete channel" |
| `saas-subscriptions.ts:308` | `Delete this custom tier? Tenants using it will need to be reassigned.` | UI-M-03, danger primary "Delete tier" |
| `saas-user-detail.ts:404` | `Are you sure you want to suspend this user?` | UI-M-03, danger primary "Suspend user" |
| `saas-voice-personas.ts:328` | `Delete "<name>"?` | UI-M-03, danger primary "Delete persona" |
| `entity-manager.ts:397` | `Are you sure you want to <action> this <entity>?` | UI-M-03 with verb-first label; non-destructive actions need no Dialog |

### 4.3 Reintroducing the invite flow

N-6 §4.4 records: `saas-user-invite-modal.ts` was deleted 2026-09-27 as dead code (its tag was
instantiated zero times). Verified absent from the tree on 2026-09-28. The invite flow SHALL be
reintroduced from **this** specification — a **UI-M-03 Dialog** with a real `POST` to the users API,
not by restoring the deleted file. Until that API and screen work land, no invite modal exists and
no invite modal is faked.

---

## 5. Overlays That Are NOT Modals

These surfaces are overlays but are **not** UI-M-*. They MUST NOT receive UI-M identifiers and MUST
NOT be built as Dialogs.

### 5.1 Toast

| Field | Value |
|---|---|
| Identifier | not a modal — no UI-M-* |
| Role | Ephemeral confirmation or non-blocking error. Never a decision point. |
| Anatomy | Icon (success `check_circle` / error `error`), one-line message. Optional single action. |
| Position | Top-right of the content area, above page content, below any open modal. |
| Lifetime | ~4000ms auto-dismiss (`saas-integrations-dashboard.ts:253`). Errors that require action are **not** toasts — they are inline banners. |
| Stacking | Max 3 visible; older ones evicted. A toast never covers a modal's actions. |
| Mobile | Full-width, top, respects safe-area inset. |
| Trigger | Completion of a user-initiated background action (save, test connection). Never on page load. |
| Accessibility | `role="status"` (`aria-live="polite"`) for success; `role="alert"` for errors. |

**Current state (honesty).** Two implementations coexist:

1. **Local toasts** — rendered inside the view: `saas-integrations-dashboard.ts:177-253,330-333`
   and `saas-settings-models.ts:215-221,634`.
2. **`show-toast` CustomEvent** — dispatched from `saas-personal-profile.ts:338,345`,
   `saas-platform-profile.ts:394-395`, `saas-multimodal-settings.ts:328` and
   `tenant-settings-controller.ts:147`. **No global listener exists in `webui/src/main.ts`** as of
   2026-09-28. These events are dispatched but unhandled unless an intermediate parent listens.
   This is a real gap, not a design choice; the fix is one `show-toast` listener in the app shell.

### 5.2 Impersonation banner

| Field | Value |
|---|---|
| Identifier | not a modal — no UI-M-* |
| Role | Persistent, non-dismissible-by-accident notice that the operator is acting as another principal. |
| Anatomy | Full-width bar pinned to the top of the app chrome: warning icon, text "You are acting as <name>", and a single action "Exit impersonation". |
| Position | Above the top chrome, below any OS inset. Always visible while the session is impersonated. |
| Dismiss | **Only** via "Exit impersonation" (which ends the impersonation session). There is no close button — the banner is the cost of the state. |
| Content rule | The impersonated display name and tenant MUST come from the session record, never from client-side guesswork. |
| Accessibility | `role="status"`, `aria-live="polite"`. Colour alone is insufficient — the icon and text carry the meaning. |

**Current state (honesty).** **Not implemented.** The only trace in `webui/` is an action entry
`{ id: 'impersonate', label: 'Impersonate', icon: 'person', permission: ':impersonate' }` in
`entity-manager.ts:72`. There is no banner component, no session flag surfaced to the shell, and no
banner CSS. This contract is the specification for when the impersonation capability is built; it
is not a description of working code.

### 5.3 Voice overlay

| Field | Value |
|---|---|
| Identifier | not a modal — no UI-M-* |
| Role | When voice capture is active over another screen: show level, state and a way to stop — without becoming a Dialog. |
| Anatomy | Compact floating strip (or the waveform stage inside Voice chat): `voice-waveform` status, duration, stop control. |
| Position | Bottom-centre floating strip when overlaying other screens; inline stage inside UI-S-46. |
| Lifetime | Bound to the recording session. Ends with the session. |
| Dismiss | Ends the session (stop / end-session). Not dismissible while recording without ending. |
| Accessibility | `aria-live="polite"` for state changes; recording state is not colour-only. |

**Current state (honesty).** `saas-voice-overlay.ts` was **deleted 2026-09-27** as dead code (its
custom-element tag was instantiated zero times — import-graph + tag scan; recorded in N-6 §4.4).
Verified absent from `webui/src/components/` on 2026-09-28. What exists today is inline voice UI:
`voice-waveform.ts` (a `.status-overlay` chip inside the waveform stage, `voice-waveform.ts:57,274`),
`saas-voice-controls.ts` and `saas-voice-transcript.ts` / `voice-transcript.ts`, used by
UI-S-46/47/48. There is **no** cross-screen voice overlay. Do not describe one as live.

### 5.4 Composer drag-drop overlay

| Field | Value |
|---|---|
| Identifier | not a modal — no UI-M-* |
| Role | Highlight the drop target while a file is dragged over the composer. |
| Anatomy | Dashed border + centred hint over the composer box. |
| Lifetime | `dragenter` → `dragleave`/`drop`. |
| Dismiss | Ends with the drag gesture. |
| Current state | N-6 §3 marks attachments as PARTIAL: drag-drop overlay + per-file preview chips + type/size rules are the target; previews are inline, not a modal. |

---

## 6. Honesty Notes

1. **Never fake a modal over nothing.** Every modal SHALL have a real data source — an API response,
   a store value, or a real form model. A modal that shows placeholder rows, invented counts or a
   disabled form with no blocking reason is a compliance failure (N-8 honesty rules; N-3).
2. **Three patterns only.** UI-M-01, UI-M-02, UI-M-03. A fourth surface is a route or an inline
   region. Do not invent "UI-M-04".
3. **`saas-user-invite-modal.ts` and `saas-voice-overlay.ts` are gone.** Deleted 2026-09-27 as dead
   code (zero tag instantiations). Verified absent 2026-09-28. Reintroduce from this spec.
4. **`saas-glass-modal.ts` is the live Dialog shell** (UI-M-03), instantiated in exactly five views
   (§4). Its header comment claims a focus trap it does not implement (`saas-glass-modal.ts:9` vs
   `:190-192`) — do not cite the comment as behaviour.
5. **`size="large"` is not a valid `ModalSize`.** The live type is `'sm' | 'md' | 'lg' | 'xl' | 'full'`
   (`saas-glass-modal.ts:16`). `saas-voice-personas.ts:430` passes `size="large"` and listens for
   `@close` instead of `@saas-modal-close`. Both are defects, not patterns to copy.
6. **`saas-admin-feature-flags.ts` imports the Dialog shell and never uses it** (`:15`). Dead import.
7. **`window.confirm()` is not a Dialog.** Eight call sites (§4.2) are known debt and MUST migrate
   to UI-M-03. Until they do, this document lists them honestly as `window.confirm`, not as UI-M-03.
8. **`saas-subscription-editor.ts` is a bespoke fixed-position overlay** (its own `.modal-overlay`
   CSS, `open`/`editingTier` properties, `close-editor`/`save-tier` events) — not `saas-glass-modal`.
   It SHALL be rebuilt on UI-M-03 or absorbed into a route; do not treat it as a fourth pattern.
9. **Toast events may be orphaned.** `show-toast` is dispatched from four places with no shell
   listener (§5.1). Never claim "a toast appears" for those paths.
10. **Impersonation banner and voice overlay are specifications, not code.** State the blocking
    reason, never "coming soon" (N-8).
11. **Register gaps.** Four modal-opening views have no `UI-S-*` id (§4.1). Do not invent ids;
    allocate them in N-5 first.
12. **No invented metrics.** Counts in this document were measured from the tree on 2026-09-28:
    5 `saas-glass-modal` instantiation sites, 8 `window.confirm()` call sites, 2 deleted modal files
    verified absent, 0 Drawer primitives, 0 Full-screen primitives.

End of Document
