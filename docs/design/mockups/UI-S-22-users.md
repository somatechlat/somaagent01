# UI-S-22 — Users

Screen UI-S-22 · Facet: Platform · Route: `/admin/users`
Source view per `SOMA-UI-IDREG-001.md`: `saas-users-view` (`webui/src/views/saas-entity-views.ts`,
custom element `saas-users-view`).
Route matches `webui/src/main.ts:249`. Note: `main.ts:362` contains a second `/admin/users`
handler mounting `saas-tenant-users`, but it is unreachable — the earlier match returns first.

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  Memory  Body  Governance ──────────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Users [1]                                        │ SURFACES x8             │
│  Chat    │ ┌────────────────────────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule │ │ SEARCH [2] ‹filter.users…│   ROLE [3] ‹role ▾│         │  │ [Editor][Debug][Capsule]│
│  Module  │ │ [ + Invite user ] [4]                                  │  │ [Brain][Desktop†] †GATED│
│  Platform│ │ ┌────────────────────────────────────────────────────┐ │  │                         │
│  Ops     │ │ │ USER TABLE [5]                                     │ │  │                         │
│  Settings│ │ │ ‹user.name›  ‹user.email›  ‹role›  ‹status›   [⋯] │ │  │                         │
│          │ │ │ ‹user.name›  ‹user.email›  ‹role›  ‹status›   [⋯] │ │  │                         │
│          │ │ │ ‹user.name›  ‹user.email›  ‹role›  ‹status›   [⋯] │ │  │                         │
│          │ │ │ (scroll)                                           │ │  │                         │
│          │ │ └────────────────────────────────────────────────────┘ │  │                         │
│          │ │ ASSIGN ROLE for selection [6]  ‹role ▾│                 │  │                         │
│          │ └────────────────────────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Users) | Screen shell. |
| 2 | UI-C-021 | Search | Filters the table live. |
| 3 | UI-C-108 | Role filter select | Roles as stored (see UI-S-23). |
| 4 | UI-A-054 | Invite user | Opens UI-M-01 drawer with the invite form. |
| 5 | UI-C-109 | User table | Rows `‹user.name›` / `‹user.email›` / `‹role›` / `‹status›`. |
| 5 | UI-C-028 | Row action menu (⋯) | Open / Resend invite / Deactivate. Deactivate opens UI-M-03. |
| 6 | UI-C-110 | Role assign select | Applies to the current selection. |
| — | UI-A-055 | Deactivate user | DESTRUCTIVE — always opens UI-M-03. |

## 3. State variants

- **loading** — Table shows 5 skeleton rows. Verbatim label: "Loading users…"
- **empty** — `UI-C-023` verbatim: "No users yet. Invite someone to get started."
  Empty under a filter verbatim: "No users match this filter. Clear the filter to see all."
- **error** — `UI-C-024` verbatim: "Users could not be loaded. Retry, or check that the
  somaAgent01 API is reachable." Invite failure verbatim: "Invite was not sent. Your details are still here."
- **permission-denied** — Invite/Deactivate/Assign disabled with inline reason
  "User administration requires the tenant-admin role." `UI-C-025` verbatim:
  "You do not have permission to manage users. Ask a platform admin for the tenant-admin role."
- **offline** — Table shows last cached page ("Showing the last synced page."); write actions
  disabled with reason "User actions are unavailable offline."

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| UI-A-054 Invite user | UI-M-01 Drawer (420px) | Email + role fields, Send invite / Cancel. ESC closes, focus trap. |
| UI-A-055 Deactivate user | UI-M-03 Dialog | "Deactivate ‹user.name›? They will lose access immediately." Cancel / Deactivate. |
| Row → Open | — | Navigates to the user detail route; no modal. |
| — | UI-M-02 | Not used by this screen. |

## 5. Honesty notes

User names, emails, roles and statuses are store placeholders. No user counts are invented.

End of Document
