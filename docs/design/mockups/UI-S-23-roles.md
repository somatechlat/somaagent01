# UI-S-23 — Roles & role matrix

Screen UI-S-23 · Facet: Platform · Route: `/platform/roles`
Source view per `SOMA-UI-IDREG-001.md`: `saas-admin-roles-list` (`webui/src/views/saas-admin-roles-list.ts`).
Route matches `webui/src/main.ts:140`. Note: a separate role-matrix view (`saas-role-matrix`) is
routed at `/platform/role-matrix` (`main.ts:147`) and is not listed as its own screen in
`SOMA-UI-IDREG-001.md`; this mockup shows the matrix as a secondary pane of the same screen.

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  Memory  Body  Governance ──────────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Roles [1]                                        │ SURFACES x8             │
│  Chat    │ ┌──────────────┐ ┌──────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule │ │ ROLE LIST [2]│ │ ROLE MATRIX [3]                      │  │ [Editor][Debug][Capsule]│
│  Module  │ │  ‹role.name› │ │  perms        ‹role.a› ‹role.b› ‹role.c›│ │ [Brain][Desktop†] †GATED│
│  Platform│ │ › ‹role.name› │ │  ─────────    ────── ────── ──────  │  │                         │
│  Ops     │ │  ‹role.name› │ │  ‹perm.name›    [x]     [ ]     [x] │  │                         │
│  Settings│ │  ‹role.name› │ │  ‹perm.name›    [x]     [x]     [ ] │  │  [4] cell toggles       │
│          │ │ [+ New role] │ │  ‹perm.name›    [ ]     [ ]     [ ] │  │                         │
│          │ │              │ │  ‹perm.name›    [x]     [ ]     [ ] │  │                         │
│          │ │              │ │  (scroll)                            │  │                         │
│          │ │              │ │ [ Save matrix ] [5]  [ Delete role ] [6]│                         │
│          │ └──────────────┘ └──────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Roles) | Screen shell. |
| 2 | UI-C-111 | Role list | Rows `‹role.name›`; selection drives the matrix columns. |
| 2 | UI-A-056 | Create role | Adds a role via UI-M-03 dialog (name + confirm). |
| 3 | UI-C-112 | Role matrix grid | Permissions × roles; cells are UI-C-113. |
| 4 | UI-C-113 | Permission cell toggle | Enables/disables one permission for one role. |
| 5 | UI-A-057 | Save matrix | Writes all cell edits. (ID note: UI-A-057 is Save here; delete is UI-A-058.) |
| 6 | UI-A-058 | Delete role | DESTRUCTIVE — always opens UI-M-03. |

## 3. State variants

- **loading** — Role list and matrix skeleton. Verbatim label: "Loading roles…"
- **empty** — Role list verbatim: "No roles defined. Create a role to start a matrix."
  Matrix with no selection verbatim: "Select a role to see its permissions."
- **error** — `UI-C-024` verbatim: "Roles could not be loaded. Retry, or check that the
  somaAgent01 API is reachable." Save failure verbatim: "Matrix was not saved. Your changes are still here."
- **permission-denied** — Cell toggles locked; Create/Delete/Save disabled with inline reason
  "Role administration requires the platform-admin role." `UI-C-025` verbatim:
  "You do not have permission to manage roles. Ask a platform admin for the platform-admin role."
- **offline** — Matrix remains visible read-only; write actions disabled with reason
  "Role changes are unavailable offline."

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| UI-A-056 Create role | UI-M-03 Dialog | Role name field + Create / Cancel. |
| UI-A-058 Delete role | UI-M-03 Dialog | "Delete ‹role.name›? Users with only this role lose access." Cancel / Delete. |
| — | UI-M-01 / UI-M-02 | Not used by this screen. |

## 5. Honesty notes

Role and permission names are store placeholders. Cell states show only what the role store
holds — no assumed defaults are painted as real grants.

End of Document
