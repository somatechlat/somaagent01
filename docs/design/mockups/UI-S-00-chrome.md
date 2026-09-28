# UI-S-00 — Global Chrome

Global application shell. Not routable on its own: every screen UI-S-01…UI-S-53 renders its
workspace region inside this frame. Route: n/a (shell). IDs follow `SOMA-UI-IDREG-001.md`.

## 1. ASCII wireframe — full desktop shell (width ≥ 1280px)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ TOP BAR                                                                                     [1][2][3][4] │
│ ┌──────────────┐  ‹capsule.name›   [v‹semver›] [‹lifecycle›]        IQ ──────●───  AUTO ──●─────  BUDGET │
│ │ ( capsule ▾ )│  [1]              [2]        [3]                     [5]      [6]           [7]  ──●──   │
│ └──────────────┘                                                                                         │
│ derived (READ-ONLY) [8]: temperature ‹› · max_tokens ‹› · rlm_iterations ‹› · recall_limit ‹› ·          │
│                          model_tier ‹› · brain_query_enabled ‹› · require_hitl ‹› · tool_approval ‹› ·    │
│                          egress_allowed ‹› · token_limit ‹› · cost_tier ‹› · thinking_budget ‹›           │
│                                                                     [ ⌘K  command palette ] [9]          │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ FACET TABS x6 [10]:   ( Soul )  ( Brain )  ( Hands )  ( Memory )  ( Body )  ( Governance )                │
│                       [11]       [12]       [13]       [14]        [15]      [16]                          │
├──────────────────┬───────────────────────────────────────────────────────────────────────┬───────────────┤
│ LEFT NAV RAIL    │ WORKSPACE [26]                                              [35][36]  │ SURFACE RAIL  │
│ [17]             │                                                             [37][38]  │ x8 [27]       │
│                  │ ┌───────────────────────────────────────────────────────────────────┐ │               │
│ ◈ Chat      [18] │ │                                                                   │ │ [Files  ] [28]│
│ ◈ Capsules  [19] │ │                                                                   │ │ [Tools  ] [29]│
│ ◈ Modules   [20] │ │              one screen's content lives here                     │ │ [Browser] [30]│
│ ─────────────    │ │              (UI-S-01 … UI-S-53 workspace region)                │ │ [Editor ] [31]│
│ ◈ Tenants   [21] │ │                                                                   │ │ [Debug  ] [32]│
│ ◈ Users     [22] │ │                                                                   │ │ [Capsule] [33]│
│ ◈ Billing   [23] │ │                                                                   │ │ [Brain  ] [34]│
│ ─────────────    │ │                                                                   │ │ [Desktop] [35]│
│ ◈ Ops       [24] │ └───────────────────────────────────────────────────────────────────┘ │   GATED †     │
│ ◈ Settings  [25] │                                                                       │ † "Requires a │
│                  │                                                                       │  remote-desk- │
│                  │                                                                       │  top capability│
│                  │                                                                       │  in somaAgent01│
│                  │                                                                       │  Not available│
│                  │                                                                       │  today."      │
├──────────────────┴───────────────────────────────────────────────────────────────────────┴───────────────┤
│ INSTANCE STRIP [36]:  ‹instance.id› ‹instance.status›   ‹instance.id› ‹instance.status›   [+ instance]   │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ NEURO METERS x4 [37]:   DA  [░░░░░░░░] ‹value›   5-HT [░░░░░░░░] ‹value›   NE  [░░░░░░░░] ‹value›       │
│                        ACh [░░░░░░░░] ‹value›    last_synced_at: ‹ timestamp ›  [sync now] [38]          │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

† UI-X-08 Desktop is GATED. Its tab renders disabled with the blocking reason inline
("Requires a remote-desktop capability in somaAgent01. Not available today."). Never a fake surface.

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-001 | Capsule switcher (dropdown) | Selects the active capsule; writes `‹capsule.id›` to the shell store. |
| 1 | UI-C-002 | Capsule name label | Read-only text bound to `‹capsule.name›`. Not editable here. |
| 2 | UI-C-003 | Version chip | Read-only; shows `‹capsule.version›`. Click opens UI-S-13 version rail via UI-M-01. |
| 3 | UI-C-004 | Lifecycle chip | Read-only; shows `‹capsule.lifecycle›` (e.g. draft / active / retired as stored). |
| 5 | UI-C-005 | Persona knob — IQ | Range input; persona core, NOT an AgentIQ derived field. |
| 6 | UI-C-006 | Persona knob — AUTO | Range input; autonomy level. |
| 7 | UI-C-007 | Persona knob — BUDGET | Range input; spend/effort budget. |
| 8 | UI-C-008 | AgentIQ derived readout block | READ-ONLY, greyed, non-interactive. Never inputs. |
| 9 | UI-C-009 | Command palette affordance | Opens palette (UI-M-02). Also bound to ⌘K / Ctrl-K. |
| 10 | UI-C-010 | Facet tab strip | Holds the six cognitive facets; selects UI-S-01…UI-S-06. |
| 11-16 | UI-C-010 | Facet tabs: Soul / Brain / Hands / Memory / Body / Governance | One tab per facet screen. |
| 17 | UI-C-011 | Left navigation rail | Jump list to non-facet screens (Chat, Capsule, Module, Platform, Ops, Voice, Settings). |
| 18-25 | UI-C-011 | Nav entries | Highlight the active route; entries disabled per role carry `disabled-reason` inline. |
| 26 | UI-C-012 | Workspace region | The only region a screen owns. Everything else is chrome. |
| 27 | UI-C-013 | Right surface rail | Container for UI-X-01…UI-X-08. |
| 28-35 | UI-C-014 | Surface tabs (x8) | Files, Tools, Browser, Editor, Debug, Capsule, Brain, Desktop. Desktop is GATED. |
| 36 | UI-C-015 | Instance strip | Live instance chips for `‹instance.id›` / `‹instance.status›`. |
| 37 | UI-C-016…019 | Neuro meters (DA / 5-HT / NE / ACh) | Readouts of `‹live value›`. No fabricated numbers. |
| 38 | UI-C-020 | `last_synced_at` stamp + sync action | Timestamp placeholder `‹ timestamp ›`; sync action is UI-A-007. |

Shared pattern controls reused across screens (defined here so IDs never collide):

| UI-C-* | control | notes |
|---|---|---|
| UI-C-021 | Search / filter field | List screens. |
| UI-C-022 | Data table / list | List screens. |
| UI-C-023 | Empty-state block | Renders the screen's verbatim empty copy. |
| UI-C-024 | Error banner | Renders the screen's verbatim error copy. |
| UI-C-025 | Permission gate notice | Renders the screen's verbatim permission-denied copy. |
| UI-C-026 | Offline banner | Global when the shell is offline; screens may also show it. |
| UI-C-027 | Loading skeleton | Replaces the region that is still loading. |
| UI-C-028 | Row action menu (⋯) | Per-row overflow; destructive items open UI-M-03. |

## 3. State variants (chrome level)

- **loading** — Top bar and facet tabs render immediately. Workspace shows `UI-C-027` skeleton
  for whichever screen is mounting. Neuro meters show empty bars with `last_synced_at: never`
  until the first sync payload arrives.
- **empty** — Capsule switcher with no capsules shows verbatim:
  "No capsules yet. Create a capsule to start." Workspace of the current route still renders
  its own empty state. Instance strip shows verbatim: "No running instances."
- **error** — A single `UI-C-024` banner under the facet tabs: verbatim:
  "Shell data could not be loaded. Retry, or check that the somaAgent01 API is reachable."
  Neuro meters hold their last painted value and stamp `last_synced_at` unchanged.
- **permission-denied** — Chrome still frames the app (identity is known). The workspace region
  is replaced by `UI-C-025`: verbatim: "You do not have permission to open this screen.
  Ask a platform admin for the required role." Facet tabs the role cannot open render disabled
  with the blocking reason inline.
- **offline** — `UI-C-026` banner, sticky above the instance strip: verbatim:
  "You are offline. Edits are held locally and will not save until the connection returns."
  Persona knobs and all inputs go read-only. UI-X-08 stays GATED regardless of connectivity.

## 4. Modal overlays opened from the chrome

| Trigger | Modal | Contents |
|---|---|---|
| UI-C-003 version chip | UI-M-01 Drawer (420px) | Version list preview; full rail is UI-S-13. |
| UI-C-009 / ⌘K command palette | UI-M-02 Full-screen | Command input, route list, capsule list, action list (UI-A-005). Explicit dismiss only. |
| UI-C-001 "new capsule" entry | UI-M-03 Dialog | Name + confirm; delegates to UI-A-031. |
| UI-C-014 surface tab (non-gated) | no modal | Expands the surface in the rail. |
| UI-C-014 Desktop (UI-X-08) | no modal | Disabled; blocking reason inline, no overlay. |

## 5. Honesty notes

- The three persona knobs (IQ / AUTO / BUDGET) are the only persona inputs in the chrome.
  The twelve AgentIQ fields in `UI-C-008` are READ-ONLY readouts and are never drawn as inputs.
- Neuro meter values, instance ids/statuses, capsule name/version/lifecycle and
  `last_synced_at` are placeholders (`‹ live value ›`, `<capsule.name>`, `‹ timestamp ›`).
  No fabricated numbers anywhere in this file.
- UI-X-08 Desktop is GATED with the exact reason from `SOMA-UI-IDREG-001.md`:
  "Requires a remote-desktop capability in somaAgent01. Not available today."
- No secret material is ever drawn in the chrome.

## 6. Trace

Chrome controls are referenced by every UI-S-01…UI-S-53 mockup. Facets map to UI-S-01…UI-S-06;
surfaces map to UI-X-01…UI-X-08. Control IDs UI-C-001…UI-C-028 and the shared action/UI-F IDs
below are reserved by this file and are safe to re-reference from screen mockups.

Shared actions: UI-A-001 Save · UI-A-002 Cancel/Close · UI-A-003 Retry · UI-A-004 Refresh ·
UI-A-005 Open command palette · UI-A-006 Switch capsule · UI-A-007 Sync now · UI-A-008 Revert.

Shared features: UI-F-001 Persona knobs · UI-F-002 Neuro meters · UI-F-003 Surface rail ·
UI-F-004 Command palette · UI-F-005 Facet navigation.

End of Document
