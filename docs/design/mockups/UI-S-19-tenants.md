# UI-S-19 — Tenants

Screen UI-S-19 · Facet: Platform · Route: `/saas/tenants`
Source view per `SOMA-UI-IDREG-001.md`: `saas-tenants` (`webui/src/views/saas-tenants.ts`).
Route matches `webui/src/main.ts:199`.

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  Memory  Body  Governance ──────────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Tenants [1]                                      │ SURFACES x8             │
│  Chat    │ ┌────────────────────────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule │ │ SEARCH [2] ‹filter.tenants…│  STATUS [3] ‹status ▾│    │  │ [Editor][Debug][Capsule]│
│  Module  │ │ [ + New tenant ] [4]                                   │  │ [Brain][Desktop†] †GATED│
│  Platform│ │ ┌────────────────────────────────────────────────────┐ │  │                         │
│  Ops     │ │ │ TENANT TABLE [5]                                   │ │  │                         │
│  Settings│ │ │ ‹tenant.name›  ‹tenant.id›  ‹status›  ‹plan›  [⋯] │ │  │                         │
│          │ │ │ ‹tenant.name›  ‹tenant.id›  ‹status›  ‹plan›  [⋯] │ │  │                         │
│          │ │ │ ‹tenant.name›  ‹tenant.id›  ‹status›  ‹plan›  [⋯] │ │  │                         │
│          │ │ │ (scroll)                                           │ │  │                         │
│          │ │ └────────────────────────────────────────────────────┘ │  │                         │
│          │ │ total: ‹ live value › tenants · page ‹page› of ‹pages› │  │                         │
│          │ └────────────────────────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Tenants) | Screen shell. |
| 2 | UI-C-021 | Search | Filters the table live. |
| 3 | UI-C-069 | Status filter select | Tenant states as stored. |
| 4 | UI-A-049 | Create tenant | Navigates to UI-S-20 wizard. |
| 5 | UI-C-100 | Tenant table | Rows `‹tenant.name›` / `‹tenant.id›` / `‹status›` / `‹plan›`. |
| 5 | UI-C-028 | Row action menu (⋯) | Open / Suspend / Settings. Suspend opens UI-M-03. |
| — | UI-A-050 | Suspend tenant | DESTRUCTIVE — always opens UI-M-03. |

## 3. State variants

- **loading** — Table shows 5 skeleton rows. Verbatim label: "Loading tenants…"
- **empty** — `UI-C-023` verbatim: "No tenants yet. Create the first tenant to get started."
  Empty under a filter verbatim: "No tenants match this filter. Clear the filter to see all."
- **error** — `UI-C-024` verbatim: "Tenants could not be loaded. Retry, or check that the
  somaAgent01 API is reachable."
- **permission-denied** — Create/Suspend disabled with inline reason
  "Tenant administration requires the platform-admin role." `UI-C-025` verbatim:
  "You do not have permission to manage tenants. Ask a platform admin for the platform-admin role."
- **offline** — Table shows last cached page ("Showing the last synced page."); Create/Suspend
  disabled with reason "Tenant actions are unavailable offline."

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| UI-A-050 Suspend tenant | UI-M-03 Dialog | "Suspend ‹tenant.name›? Users will lose access until it is resumed." Cancel / Suspend. |
| Row → Open | — | Navigates to UI-S-21; no modal. |
| Row → Settings | UI-M-01 Drawer (420px) | Tenant settings summary; ESC closes, focus trap. |
| — | UI-M-02 | Not used by this screen. |

## 5. Honesty notes

Tenant names, ids, statuses and plans are store placeholders (`‹tenant.name›` style). Totals and
page counts are `‹ live value ›` — never fabricated numbers.

End of Document
