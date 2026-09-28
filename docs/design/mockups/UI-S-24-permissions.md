# UI-S-24 — Permissions

Screen UI-S-24 · Facet: Platform · Route: `/saas/permissions`
Source view per `SOMA-UI-IDREG-001.md`: `saas-permissions` (`webui/src/views/saas-permissions.ts`).
Route matches `webui/src/main.ts:160`.

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  Memory  Body  Governance ──────────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Permissions [1]                                   │ SURFACES x8             │
│  Chat    │ ┌────────────────────────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule │ │ SEARCH [2] ‹filter.perms…│  GROUP [3] ‹group ▾│         │  │ [Editor][Debug][Capsule]│
│  Module  │ │ SCOPE [4] ‹scope ▾│                                    │  │ [Brain][Desktop†] †GATED│
│  Platform│ │ ┌────────────────────────────────────────────────────┐ │  │                         │
│  Ops     │ │ │ PERMISSION TABLE [5]                               │ │  │                         │
│  Settings│ │ │ ‹perm.name›  ‹group›  ‹scope›  ‹state›  [⋯]       │ │  │                         │
│          │ │ │ ‹perm.name›  ‹group›  ‹scope›  ‹state›  [⋯]       │ │  │                         │
│          │ │ │ ‹perm.name›  ‹group›  ‹scope›  ‹state›  [⋯]       │ │  │                         │
│          │ │ │ (scroll)                                           │ │  │                         │
│          │ │ └────────────────────────────────────────────────────┘ │  │                         │
│          │ │ [ Grant ] [6]   [ Revoke ] [7]                          │  │                         │
│          │ └────────────────────────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Permissions) | Screen shell. |
| 2 | UI-C-021 | Search | Filters the table live. |
| 3 | UI-C-114 | Group filter select | Permission groups as stored. |
| 4 | UI-C-115 | Scope select | Scope values as stored (tenant / platform / …). |
| 5 | UI-C-116 | Permission table | Rows `‹perm.name›` / `‹group›` / `‹scope›` / `‹state›`. |
| 5 | UI-C-028 | Row action menu (⋯) | Grant / Revoke / Open detail. Revoke opens UI-M-03. |
| 6 | UI-A-059 | Grant permission | Grants the selection to the current role/scope context. |
| 7 | UI-A-060 | Revoke permission | DESTRUCTIVE — always opens UI-M-03. |

## 3. State variants

- **loading** — Table shows 5 skeleton rows. Verbatim label: "Loading permissions…"
- **empty** — `UI-C-023` verbatim: "No permissions match this filter. Clear the filter to see all."
  With no data at all: "No permissions are defined for this scope yet."
- **error** — `UI-C-024` verbatim: "Permissions could not be loaded. Retry, or check that the
  somaAgent01 API is reachable."
- **permission-denied** — Grant/Revoke disabled with inline reason
  "Permission changes require the platform-admin role." Table remains readable; `UI-C-025` verbatim:
  "You do not have permission to change permissions. Ask a platform admin for the platform-admin role."
- **offline** — Table shows last cached page ("Showing the last synced page."); Grant/Revoke
  disabled with reason "Permission changes are unavailable offline."

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| UI-A-060 Revoke permission | UI-M-03 Dialog | "Revoke ‹perm.name› from ‹scope›?" Cancel / Revoke. |
| Row → Open detail | UI-M-01 Drawer (420px) | Full permission record; ESC closes, focus trap. |
| — | UI-M-02 | Not used by this screen. |

## 5. Honesty notes

Permission names, groups and scopes are store placeholders. The table shows stored grants only —
no assumed effective-permission calculations are drawn.

End of Document
