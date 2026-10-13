# SOMA-RPT-UI-CONTROLS-SCORE-001 — Interactive control inventory, honesty / handlers / a11y scorecard

## Document Control

| Field | Value |
|---|---|
| Document Title | WebUI interactive controls inventory and score |
| Document Identifier | SOMA-RPT-UI-CONTROLS-SCORE-001 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | agent-evaluator (docs-only pass) |
| Classification | Internal |
| Scope | `webui/src/views/**` + `webui/src/components/**` (66 Lit files) |
| Sources of truth | `docs/design/SOMA-UI-AGENT-FRONTEND-MASTER-001.md` (control law L4), `docs/design/mockups/UI-S-*.md` + `UI-X-*.md`, `docs/reports/SOMA-RPT-UIUX-AUDIT-001.md`, `docs/reports/SOMA-RPT-UI-PARITY-GAP-001.md` |
| Mode | **DOCS ONLY** — no code changed, no commits |

---

## 0. Scoring law

From `SOMA-UI-AGENT-FRONTEND-MASTER-001.md:4`:

> **Law:** NO MOCKS / FAKES / STUBS / SHIMS. Every control has a real handler or an honest disabled reason.

Operational rubric used in this report:

| Axis | 5 | 3 | 1 |
|---|---|---|---|
| **Honesty** | every non-live control is present-but-disabled with a named blocking reason; no fake meters/counts | mixed: most gates honest, some silent omissions | dead control with no reason, or fabricated state |
| **Handlers** | every enabled control has a real API/WS/route handler; disabled controls never fire | live controls wired; some mockup-listed controls absent rather than gated | `@click` present but empty / console-only / event to nowhere |
| **A11y** | role + name + keyboard + disabled announced | name present, keyboard or role incomplete | div-click with no role/name/keyboard |

**Dead control = FAIL. Honest gate = PASS.** Absent-but-documented-in-mockup as `design` is not a FAIL (mockup itself marks it non-live).

---

## 1. Inventory totals (views + components)

Element census (HTML tags + custom control hosts in template literals):

| Control class | Count | Notes |
|---|---:|---|
| `<button>` | 183 | includes hard-disabled honest gates |
| `<input>` | 87 | text/email/password/checkbox/range/number/file/month/url |
| `<select>` | 35 | native selects (preferred for a11y) |
| `<a href>` | 17 | in-app routes + external ToS/Privacy/MFA URI |
| `<textarea>` | 6 | composer, memory Remember, capsule, voice config/personas |
| `<soma-button>` | 6 | channels lifecycle |
| `<soma-toggle>` | 6 | profile notification prefs (3+3) |
| `<soma-action-menu>` | 2 | entity rows + API keys |
| click-only `<div class="tab">` | 12 | platform-metrics / infra / user-detail / capsule |
| **Total interactive elements** | **354** | |

**Handler scan (empty / console-only methods):** 0 hits. Every private handler referenced by `@click` has a non-empty body. No `addEventListener` to a missing listener. No `href="#"` dead links. No `<a>` without `href` and without `@click`.

**Hard-disabled controls:** 4 sites (all carry a blocking reason — see §3). Conditional `?disabled=` busy/dirty gates: 11 sites (legitimate state gating, not dead).

---

## 2. Per-file scorecard

Legend: **H** = honesty, **D** = handlers, **A** = a11y (1–5). Verdict uses the law: **PASS** / **PARTIAL** / **FAIL**.

### 2.1 Views (`webui/src/views/`)

| File | Ctrl (n) | H | D | A | Verdict | Evidence |
|---|---:|---:|---:|---:|---|---|
| `soma-chat.ts` | 26 | 5 | 5 | 4 | **PASS** | Nav Memory/Settings `:3009-3012`; logout `:3023` aria-label; delete confirm cancel/submit `:2923-2924`; canvas toggle `aria-pressed` `:3541`; model chip LIVE gated (UIUX-AUDIT P4). Topbar subcomponent has `role="group"` (see 2.2). |
| `soma-memory-view.ts` | 15 | 5 | 5 | 4 | **PASS** | Run probe / Remember / Forget / Export / Refresh all bound; WM/LTM `—` + `GATED` `:865-877` (never 0); unavailable bar `:746-750`, `:957-959`. |
| `soma-settings.ts` | 17 | 5 | 4 | 3 | **PARTIAL** | 9 tabs `:654-664` all `@click→_setTab` `:696-702` (real); save gated on `system:configure` `:674-679`. **A11y gap:** tabs are `<button class="tab-item">` without `role="tab"` / `aria-selected`. |
| `soma-settings-models.ts` | 55 | 5 | 5 | 4 | **PASS** | Activate/Edit/Delete/Preset/Save-key/Load-models/Test-connection all real. `:1357` hard-disabled "No models loaded yet" is an honest empty-state control (no handler needed). LIVE chip role-bound (UIUX-AUDIT P3). |
| `soma-settings-channels.ts` | 12 | 5 | 5 | 4 | **PASS** | `soma-button` Create `:284`, lifecycle test/start/stop `:305-311`, delete `:314` → `_createChannel`/`_lifecycle`/`_deleteChannel`. |
| `soma-settings-somabrain.ts` | 8 | 5 | 5 | 4 | **PASS** | Inputs bound to live knobs; status label `'unavailable'` `:477-478` `:496-497` is honest, not a fake meter. |
| `soma-login.ts` | 14 | 5 | 5 | 4 | **PASS** | Email/password `:699-711`; show-password `:715`; remember-me `:725`; submit `:730` (`?disabled=_isLoading`); Google `:674`; SSO modal open/test/save `:684`, `:802`, `:826`; links `/register` `:666`, `/forgot-password` `:709`. |
| `soma-register.ts` | 9 | 5 | 5 | 4 | **PASS** | Submit gated `:256` on `_isLoading \|\| !_termsAccepted` (honest terms gate); ToS/Privacy links `:251-252`. |
| `soma-forgot-password.ts` | 3 | **5** | 5 | 4 | **PASS (honest gate)** | `BLOCKING_REASON` `:165-169` cites the real missing route (`admin/auth/api.py`). Visible reason card `:194-197` `role="status"`; input disabled + `title=` `:202-206`; submit disabled + `title=` `:209-211`; form `@submit` prevented `:199`. **Textbook honest gate.** |
| `soma-mfa-setup.ts` | 10 | 5 | 5 | 4 | **PASS** | Step buttons (intro/scan/verify/retry) all wired `:361-497`; back via `history.back()` `:369`. |
| `soma-auth-callback.ts` | 1 | 5 | 5 | 4 | **PASS** | Retry `:118` → `_retry`. |
| `soma-personal-profile.ts` | 12 | 5 | 5 | 3 | **PARTIAL** | Save `:564` `?disabled=saving`; MFA reconfigure nav `:519`; 3× `soma-toggle` notifications `:538-554`. **A11y:** inherits `soma-toggle` keyboard/role gap (§4.1). Email/tenant inputs correctly `disabled` read-only `:444`, `:461`. |
| `soma-platform-profile.ts` | 8 | 5 | 5 | 3 | **PARTIAL** | Same toggle set `:566-582`; MFA `:497`; save button `:441`. Same a11y inheritance. |
| `soma-user-detail.ts` | 7 | 5 | 5 | 2 | **PARTIAL (a11y)** | Suspend `:493` real; role select `:516`. **FAIL a11y:** 4 tabs are `<div class="tab" @click>` `:460-473` — mouse-only, no `role="tab"`, no keyboard. |
| `soma-admin-api-keys.ts` | 7 | 5 | 5 | 3 | **PARTIAL** | Create modal open `:268`, Generate `:360`, cancel `:353`, copy `:379` all real. `soma-action-menu` `:249` inherits §4.3 gap. |
| `soma-admin-roles-list.ts` | 1 | 5 | 5 | 4 | **PASS** | Link to matrix pane. |
| `soma-role-matrix.ts` | 2 | 5 | 5 | 4 | **PASS** | Revert `:218` `?disabled=!dirty`; Save `:221` real. |
| `soma-entity-views.ts` | 0* | 5 | 5 | 4 | **PASS** | Delegates to `entity-manager` (see 2.2). |
| `soma-audit-dashboard.ts` | 8 | 5 | 5 | 4 | **PASS** | Refresh `:433`, Export CSV `:437`, filters `:466-481`, pagination `:547-552`. |
| `soma-integrations-dashboard.ts` | 7 | 5 | 5 | 4 | **PASS** | Refresh `:381`; Test `:421` `?disabled=testing===provider`; Config `:425`; Save `:453` `?disabled=saving`. Keys write-only (UIUX-AUDIT UI-S-41). |
| `platform-metrics-dashboard.ts` | 6 | 5 | 5 | 2 | **PARTIAL (a11y)** | Refresh `:477` real. **FAIL a11y:** 5 tabs are `<div class="tab" @click>` `:485-497` — mouse-only. |
| `soma-infrastructure-dashboard.ts` | 5 | 5 | 5 | 2 | **PARTIAL (a11y)** | Refresh `:485`; Seed rate limits `:567`. **FAIL a11y:** 3 div tabs `:493-499`. |
| `soma-agent-metrics.ts` | 1 | 4 | 5 | 4 | **PARTIAL** | Month picker `:364` real. Chart area is comment-only `:214` `/* Charts placeholder */` — **no fake series drawn** (honest absence vs UI-S-45, but incomplete surface). |
| `soma-cognitive-panel.ts` | 5 | 5 | 5 | 4 | **PASS** | Sleep cycle `:599`; Reset adaptation `:603`; Connected/Unavailable text `:592` honest. |
| `soma-multimodal-settings.ts` | 16 | 5 | 5 | 4 | **PASS** | Save `:332`; 8 selects + 7 checkboxes bound to live config; ceilings disclosed not invented (UIUX-AUDIT UI-S-49). |
| `soma-voice-chat.ts` | 0* | 5 | 5 | 4 | **PASS** | Controls live in `soma-voice-controls` / `voice-waveform`. |
| `soma-voice-sessions.ts` | 2 | 5 | 5 | 4 | **PASS** | Reload `:240`; row action `:306`. |
| `soma-voice-personas.ts` | 6 | 5 | 5 | 4 | **PASS** | Create `:387`/`:404`; form inputs `:440-472`; confirm `:493-500`. |
| `index.ts` | 0 | — | — | — | n/a | barrel only |

\* zero *direct* control tags; controls live in composed children.

### 2.2 Components (`webui/src/components/`)

| File | Ctrl (n) | H | D | A | Verdict | Evidence |
|---|---:|---:|---:|---:|---|---|
| `entity-manager.ts` | 5 | **5** | 5 | 4 | **PASS (honest gate)** | Blocking reasons `:66-75` (`REASON_NO_PASSWORD_RESET` / `_EDIT_SCREEN` / `_CREATE_SCREEN` / `_AGENT_DETAIL` / `_DUPLICATE_API`) verified against `admin/auth/api.py`, `admin/platform/api/users.py`, `admin/platform/api/tenant_agents.py`. Create btn disabled + inline reason `:512-518`. Actions with `disabledReason` `:105-106`, `:130-132`. `handleAction` refuses disabled `:433-435`. Comment `:444-445` documents removal of a previous dead event-dispatch control. |
| `soma-right-panel.ts` | 7 | **5** | 5 | **5** | **PASS (honest gate + a11y gold)** | SURFACES registry `:56-78`: Browser `blockedReason: 'Bind a browser model on UI-S-02 first'` `:64`; Desktop blocked `:75-76`. Save `SAVE_DISABLED_REASON` `:191-192` + button `:1074-1079` (`disabled`, `title`, `aria-label`). Tab rail `role="tablist"` `:802`; tabs `role="tab"` + `aria-selected` + `aria-disabled` `:821-824`. Desktop action btn disabled + reason `:1175-1180`. Matches MASTER-001 `:278-283` (Browser GATED, Editor Save disabled, Desktop GATED). |
| `soma-action-menu.ts` | 2 | 5 | 5 | 2 | **PARTIAL (a11y)** | Honesty excellent: disabled never fires `:159-163`; reason inline `:184`, `:190-191`. **FAIL a11y:** trigger is `<div @click>` `:176`; items are `<div @click>` `:182-185` — no `role="menu"/"menuitem"`, no keyboard, no `aria-expanded`. |
| `soma-composer.ts` | 6 | 5 | 5 | 4 | **PASS** | Send `:571`/`:603`, textarea `:580`, attach `:557`, mic `:588`/`:621` with honest mic-unavailable copy `:541`, `:476`. |
| `soma-composer-menu.ts` | 4 | 5 | 5 | **5** | **PASS (a11y good)** | `role="menu"` `:142`; `role="menuitem"` on file `:143`, Memory `:148`, Clear `:161`, Export `:165`. |
| `soma-chat-topbar.ts` | 4 | 5 | 5 | **5** | **PASS (a11y gold)** | `role="group" aria-label="Chat controls"` `:286`. Pause/Resume `:287-296`, Nudge `:298-307`, Stop `:309-318`, Reset `:320-328` — each has `@click`, `?disabled` state gate, `title`, `aria-label`. Emits real WS actions (UI-S-07 #7). |
| `soma-capsule-editor.ts` | 7 | 5 | 5 | 2 | **PARTIAL (a11y)** | Tabs `:415-422`, Reload `:440`, Export `:443`, Archive `:447` real. **FAIL a11y:** tabs are buttons without `role="tab"`/`aria-selected`; two further tab uses are also mouse-centric. |
| `soma-agent-header.ts` | 4 | 5 | 5 | 3 | **PARTIAL** | IQ badge `:266`, knobs `:271`/`:299`, capsule `:322` all navigate real surfaces. Icon-only buttons have `title` but not all have `aria-label`. |
| `soma-message.ts` | 3 | 5 | 5 | 4 | **PASS** | Copy actions `:1163`, `:1219` delegated (comment `:929` explains unsafeHTML safety). Attachment fail → `is-unavailable` card `:1135-1141` ("Preview unavailable"/"Not uploaded") — honest, never broken frame. |
| `soma-tool-timeline.ts` | 2 | 5 | 5 | 4 | **PASS** | Approve/Reject `:422`, `:427` → `tool.approval` (UI-S-07 #10). |
| `soma-capsule` / `soma-glass-modal.ts` | 1 | 5 | 5 | 3 | **PARTIAL** | Close `:235` real; icon button may lack accessible name in some instances. |
| `soma-permission-guard.ts` | 2 | 5 | 5 | 4 | **PASS** | Go Back `:209`; Request Access `:210` — real navigation, no fake grant. |
| `soma-skin-gallery.ts` | 5 | 5 | 5 | 4 | **PASS** | Preview `:301`, Apply `:304`, Revert `:329`, Install bundled `:333` all real skin-sdk ops (MASTER-001 §3.4 skins live). |
| `soma-sidebar.ts` | 2 | 5 | 5 | 4 | **PASS** | Collapse `:350` real. |
| `soma-select.ts` | 1 | 5 | 5 | 1 | **FAIL (a11y)** | Header claims "Keyboard navigation" `:9` but trigger is `<div @click>` `:186`; options are `<div @click>` `:203-206`. No `role="listbox"/"option"`, no arrow-key handling, no `aria-expanded`/`aria-activedescendant`. **Claim vs code mismatch.** |
| `soma-toggle.ts` | 1 | 5 | 5 | 1 | **FAIL (a11y)** | Whole control is `<div class="container" @click>` `:93-95` wrapping a styled `<div class="switch">` `:97`. No `role="switch"`, no `tabindex`, no `aria-checked`, no keyboard handler. Header claims "Accessible state" `:9` — **claim vs code mismatch**. Emits `soma-change` correctly `:84-88`. |
| `soma-button.ts` | 1 | 5 | 5 | 4 | **PASS** | Real `<button ?disabled type=…>` `:77-81`. Clicks bubble (composed) so host `@click` works. No built-in reason channel (callers supply text). |
| `soma-form-field.ts` | 1 | 5 | 5 | 2 | **PARTIAL (a11y claim fail)** | Input handler `:102-110` real. Header claims "Accessible label association" `:8` but `<label>` `:115-117` has **no `for`** and `<input>` `:121-128` has **no `id`** — label is not programmatically associated. |
| `settings-form.ts` | 5 | 5 | 5 | 2 | **PARTIAL (a11y)** | Revert `:462-468`, Save `:469-475` with `?disabled=!dirty\|\|saving`; read-only notice when `!canEdit` `:478-483` (honest). **FAIL a11y:** boolean toggle is a clickable `<div class="toggle">` `:515-521`; label `:495` has no `for`. Non-editable fields print "Deployment topology — changes with a deploy" `:499-501`. |
| `soma-status-dot.ts` / `soma-status-badge.ts` / `soma-stat-card.ts` | 0 | 5 | — | 4 | **PASS** | Display-only; status honesty covered by UIUX-AUDIT P5. |
| `soma-data-table.ts` | 1† | 5 | 5 | 3 | **PARTIAL** | Sortable headers `:165` real. Header click-only pattern (no `role="columnheader"` sort state) is a minor a11y gap. |
| `soma-infra-*` (3 files) | 0† | 5 | 5 | 4 | **PASS** | Display cards/lists; no interactive dead ends. |
| `soma-voice-controls.ts` | 2 | 5 | 5 | 4 | **PASS** | Mic start/stop `:270`, `:287`. |
| `soma-voice-session-picker.ts` / `soma-voice-transcript.ts` / `voice-*.ts` | 5 | 5 | 5 | 4 | **PASS** | Clear transcript `voice-transcript.ts:224`; persona Edit/Dup/SetDefault/Delete `voice-persona-card.ts:228-233`; waveform button `voice-waveform.ts:282`; config panel full form `voice-config-panel.ts:247-366` all bound. |
| `soma-user-profile-card.ts` | 0 | 5 | — | 4 | **PASS** | Display. |
| `index.ts` | 0 | — | — | — | n/a | barrel. |

† sort header is a control-like affordance.

---

## 3. Honest gates — PASS inventory (law-satisfying)

These are the controls that *look* interactive but are correctly present-and-disabled with a machine-checkable reason. Per the law, each is **PASS**, not FAIL.

| # | Control | file:line | Blocking reason | Why PASS |
|---|---|---|---|---|
| G1 | Send reset link | `views/soma-forgot-password.ts:209-211` | `BLOCKING_REASON` `:165-169` — no password-reset route in `admin/auth/api.py` | Disabled + `title` + visible `role="status"` card `:194-197`; form submit prevented `:199` |
| G2 | Email (forgot) | `views/soma-forgot-password.ts:202-206` | same | disabled + `title` |
| G3 | Create User/Agent | `components/entity-manager.ts:512-518` | `REASON_NO_CREATE_SCREEN` `:70-71` | `title` + inline `.btn-reason` span |
| G4 | Edit / Reset Password / Duplicate / Agent View | `components/entity-manager.ts:105-106`, `:130-132` | `REASON_NO_EDIT_SCREEN` / `_PASSWORD_RESET` / `_AGENT_DETAIL` / `_DUPLICATE_API` `:66-75` | `disabledReason` printed by action-menu `:190-191`; `handleAction` early-return `:433-435` |
| G5 | Canvas tab Browser | `components/soma-right-panel.ts:64`, `:814-824` | `'Bind a browser model on UI-S-02 first'` | stays on rail, `aria-disabled`, `title` = reason |
| G6 | Canvas tab Desktop | `components/soma-right-panel.ts:75-76`, `:1175-1180` | `'Requires a remote-desktop capability… Not available today.'` | present-but-disabled frame + disabled button with reason |
| G7 | Editor Save | `components/soma-right-panel.ts:191-192`, `:1074-1079` | `SAVE_DISABLED_REASON` — no `PUT`/content route in `admin/filesv2/api.py` | `disabled` + `title` + `aria-label="Save — disabled. …"` |
| G8 | WM / LTM tiles | `views/soma-memory-view.ts:865-877` | `title="No count API — shown as — until one ships. Never 0."` | renders `—` + `GATED`, never fabricated 0 |
| G9 | Disabled action items | `components/soma-action-menu.ts:157-163`, `:184-191` | caller-supplied `disabledReason` | disabled never fires; reason inline |
| G10 | Settings read-only shell | `components/settings-form.ts:478-483` | `You don't have permission to edit these settings` | locks form; non-editable fields print deploy-topology note `:499-501` |
| G11 | "No models loaded yet" | `views/soma-settings-models.ts:1357` | empty-state label | hard-disabled, no fake action |
| G12 | Mic unavailable | `components/soma-composer.ts:541` | `'Voice input unavailable — MediaRecorder/getUserMedia not supported…'` | honest capability gate |

**No dead control found that is silent.** The only hard-disabled controls all carry reasons.

---

## 4. Failures and gaps

### 4.1 FAIL — `soma-toggle` is not a switch (a11y)

- `components/soma-toggle.ts:93-106` — interaction is a clickable `<div class="container">` with a decorative `<div class="switch">`.
- Missing: `role="switch"`, `tabindex="0"`, `aria-checked`, `keydown` (Space/Enter).
- Header `:9` claims "Accessible state" — **not implemented**.
- Blast radius: 6 live toggles on personal/platform profile (`views/soma-personal-profile.ts:538-554`, `views/soma-platform-profile.ts:566-582`).

**Fix:** render `<button role="switch" aria-checked=${checked} …>` (or `<input type="checkbox">` with `role="switch"`), keep `soma-change` payload.

### 4.2 FAIL — `soma-select` claims keyboard nav it does not have (a11y + doc lie)

- `components/soma-select.ts:9` comment: "Keyboard navigation".
- `:186` trigger is `<div @click=${this._toggle}>`; `:203-206` options are `<div @click>`.
- No `role="listbox"`, `role="option"`, `aria-expanded`, `aria-activedescendant`, or arrow-key handling. Search input `:194-199` is the only focusable part when `searchable`.

**Fix:** either implement combobox pattern, or delete the false claim and prefer native `<select>` (already used in 35 places).

### 4.3 FAIL — `soma-action-menu` menu is mouse-only (a11y)

- `components/soma-action-menu.ts:176` trigger `<div @click>`; `:182-185` items `<div @click>`.
- Unlike `soma-composer-menu.ts:142-165` (which correctly uses `role="menu"` / `role="menuitem"`), this menu has **zero** ARIA menu roles and no keyboard support.

**Fix:** mirror composer-menu roles; make trigger a `<button aria-haspopup="menu" aria-expanded>`.

### 4.4 FAIL — `soma-form-field` label association claimed but missing (a11y)

- `components/soma-form-field.ts:8` claims "Accessible label association".
- `:115-117` `<label class="label">` has no `for`; `:121-128` `<input>` has no `id`.
- Same pattern in `components/settings-form.ts:495` (`<label class="field-label">` without `for`).

**Fix:** generate `id` on input and set `for` on label (or wrap input in label).

### 4.5 PARTIAL — click-only tab strips (a11y)

Div-based tabs with `@click` and no `role="tab"` / `aria-selected` / keyboard:

| File | Lines | Tabs |
|---|---|---|
| `views/platform-metrics-dashboard.ts` | `:485-497` | overview / llm / tools / memory / sla |
| `views/soma-infrastructure-dashboard.ts` | `:493-499` | health / ratelimits / degradation |
| `views/soma-user-detail.ts` | `:460-473` | profile / agents / activity / sessions |
| `components/soma-capsule-editor.ts` | `:415-422` | soul / learning |

`views/soma-settings.ts:696-702` uses real `<button>` tabs (better) but still omits `role="tab"`/`aria-selected`.

**Gold standard already in-tree:** `components/soma-right-panel.ts:802`, `:821-824` (`role="tablist"` / `role="tab"` / `aria-selected` / `aria-disabled`). Reuse that pattern.

### 4.6 GAP (not a dead control) — mockup controls not mounted

UI-S-07 control map lists these as bound; they are **absent** from the chat shell (fail-closed absence, not a fake):

| Mockup # | Control | Status in code |
|---|---|---|
| UI-S-07 #15 | Project picker (top bar) | not present in `soma-chat-topbar.ts` / `soma-chat.ts` |
| UI-S-07 #16 | Notifications bell `GET /notifications` | not present; notification *preferences* exist on profile screens (`soma-personal-profile.ts:534-555`) |
| UI-S-07 after #18 | ⌘K command palette | correctly **not shipped** (mockup `:299` marks it unshipped) |
| UI-S-04 #3 | Layer filter `wm\|ltm\|both` | not implemented; mockup marks `design` (`UI-S-04-memory.md:96`) |
| UI-S-04 #11 | Open record drawer UI-M-01 | not implemented; mockup marks `design` (`:104`) |
| UI-S-45 | Agent metrics charts | comment-only `views/soma-agent-metrics.ts:214`; **no fake series** (honest absence) |

Per MASTER-001 `:4` and the fail-closed UI rule, absence of a mockup control is preferred over a dead button. These are **completeness gaps**, not honesty FAILs.

### 4.7 PASS confirmation vs MASTER-001 §3.7 canvas surfaces

| ID | Surface | MASTER-001 `:274-283` | Code | Score |
|---|---|---|---|---|
| UI-X-01 Files | thin list | live list in right-panel | PASS |
| UI-X-02 Tools | LIVE | live tools + WS log | PASS |
| UI-X-03 Browser | GATED honest | `blockedReason` `soma-right-panel.ts:64` | **PASS** |
| UI-X-04 Editor | RO + Save disabled | `SAVE_DISABLED_REASON` `:191-192` | **PASS** |
| UI-X-05 Debug | LIVE | WS frame ring | PASS |
| UI-X-06 Capsule | LIVE | `soma-capsule-editor` | PASS |
| UI-X-07 Brain | LIVE | `soma-cognitive-panel` | PASS |
| UI-X-08 Desktop | GATED honest | `blockedReason` `:75-76` | **PASS** |

---

## 5. Axis scores

| Axis | Score | Basis |
|---|---:|---|
| **Honesty** | **5 / 5** | Zero silent dead controls. 12 documented honest gates (§3). Memory tiles never fake 0 (`soma-memory-view.ts:865-877`). Editor Save / Browser / Desktop / Forgot-password / entity Create carry named blocking reasons. Empty-handler scan: 0. |
| **Handlers** | **4 / 5** | Every enabled control inspected has a real API/WS/route/local-state handler. Conditional disables are busy/dirty gates, not stubs. Deduct 1: UI-S-07 #15/#16 and UI-S-45 charts are mockup-listed but not mounted (absent rather than gated) — completeness gap, not a lie. |
| **A11y** | **3 / 5** | Gold patterns exist (`soma-chat-topbar.ts:286-328`, `soma-right-panel.ts:802-824`, `soma-composer-menu.ts:142-165`, `soma-forgot-password.ts:194`). Failures: `soma-toggle`, `soma-select`, `soma-action-menu`, `soma-form-field` label association, 4 div-tab strips. Two file headers claim accessibility they do not implement (`soma-toggle.ts:9`, `soma-select.ts:9`, `soma-form-field.ts:8`). |

**Weighted verdict (law-first):** Honesty is the project law and it is clean. A11y is the weakest axis and contains two **doc-lies** (claimed keyboard/accessible state) which violate the same no-sham law at the documentation level.

| Aggregate | Score |
|---|---:|
| Mean of H/D/A | **4.0 / 5** |
| Law compliance (dead controls = 0) | **PASS** |
| Ready to ship as-is? | **Yes, with a11y debt listed** |

---

## 6. Priority remediation (docs-only recommendations — do not implement here)

| P | Item | file:line | Impact |
|---|---|---|---|
| P0 | Rebuild `soma-toggle` as `role="switch"` + keyboard | `components/soma-toggle.ts:93-106` | 6 live profile toggles unreachable by keyboard |
| P0 | Fix or retire `soma-select` keyboard claim; prefer native `<select>` | `components/soma-select.ts:9`, `:186-216` | false accessibility claim in source |
| P0 | Associate `soma-form-field` label↔input (`for`/`id`) | `components/soma-form-field.ts:115-128` | all admin API-key fields mislabeled for SR |
| P1 | ARIA menu pattern on `soma-action-menu` (copy `soma-composer-menu`) | `components/soma-action-menu.ts:176-195` | entity/API-key row actions mouse-only |
| P1 | Convert div-tabs to `role="tab"` buttons (copy `soma-right-panel`) | `platform-metrics-dashboard.ts:485-497`, `soma-infrastructure-dashboard.ts:493-499`, `soma-user-detail.ts:460-473`, `soma-capsule-editor.ts:415-422`, `soma-settings.ts:696-702` | 19 tab stops not keyboard/AT-addressable |
| P2 | Either mount UI-S-07 #15/#16 or annotate mockup as `design` like UI-S-04 #3/#11 | mockup `UI-S-07-chat-workspace.md:294-295` | closes mockup↔code ambiguity |
| P2 | Render honest empty chart frame (or GATED chip) for UI-S-45 | `soma-agent-metrics.ts:214` | user sees blank region with only a code comment |
| P3 | Add `aria-label` to remaining icon-only buttons | `soma-agent-header.ts:266-322`, `soma-glass-modal.ts:235` | minor SR naming |

---

## 7. Method / verification

| Check | Method | Result |
|---|---|---|
| Element census | Python tag scan over `views/**/*.ts` + `components/**/*.ts` | 354 interactive elements in 66 files |
| Handler presence | scan `@click` / `@submit` / `@change` / `@input` against tag open | 0 buttons without handler (except hard-disabled honest gates) |
| Empty / console-only handlers | regex over method bodies | 0 hits |
| Dead links | `<a>` without `href` or `@click`; `href="#"` | 0 hits |
| Hard-disabled without reason | `<button … disabled>` without `title`/reason | 0 hits (4 hard-disabled all titled) |
| Honesty markers | `rg -i 'blockedReason|disabledReason|GATED|BLOCKING|unavailable|Not available'` | 12 gate sites (§3) |
| ARIA inventory | `rg 'role=|aria-'` | concentrated in chat (21), right-panel (14), composer (8), message (6); **zero** in `soma-toggle` / `soma-select` / `soma-action-menu` |
| Mockup cross-ref | UI-S-04 §3, UI-S-07 §3, UI-X-04, UI-S-51, MASTER-001 §3.7 | see §4.6–4.7 |

**Not run (out of scope for docs-only):** Playwright, axe-core live audit, tsc. Prior session ran `bun node_modules/typescript/bin/tsc --noEmit` green (`SOMA-RPT-UIUX-AUDIT-001.md:15`).

---

## 8. A2A / next actions

- This pass is **docs-only**. No `webui/` code edited. Implementers must claim `webui/` in `docs/plans/a2a/CLAIMS.md` before applying §6 items.
- Related reports: `SOMA-RPT-UIUX-AUDIT-001.md` (per-screen parity + P1–P6), `SOMA-RPT-UI-PARITY-GAP-001.md` (Agent Zero parity), `docs/design/SOMA-UI-AGENT-FRONTEND-MASTER-001.md` (control law).

---

## 9. Bottom line

**The honesty law holds.** Across 354 interactive elements there is **no dead control without a reason** and **no fabricated count/meter**. Browser / Desktop / Editor Save / Forgot Password / entity Create are textbook present-but-disabled gates with file-and-route-cited blocking reasons.

**The a11y floor does not hold yet**, and two component headers actively claim accessibility they do not implement (`soma-toggle`, `soma-select`, `soma-form-field`). Under the same no-sham law those comments are defects until the code matches.

| Question | Answer |
|---|---|
| Dead controls? | **0 → FAIL count = 0** |
| Honest gates? | **12 → all PASS** |
| Handler integrity? | **PASS** (4/5 only for mockup-listed unmounted controls) |
| A11y floor? | **PARTIAL** (3/5) — 5 concrete defects, §6 |
| Ship? | **Yes**, with §6 P0 a11y items treated as debt tickets, not blockers to honesty sign-off |
