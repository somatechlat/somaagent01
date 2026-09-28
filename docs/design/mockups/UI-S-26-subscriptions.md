# UI-S-26 — Subscriptions

Screen UI-S-26 · Facet: Platform · Route: `/saas/subscriptions`
Source view per `SOMA-UI-IDREG-001.md`: `saas-subscriptions` (`webui/src/views/saas-subscriptions.ts`).
Route matches `webui/src/main.ts:205`.

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  Memory  Body  Governance ──────────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Subscriptions [1]                                  │ SURFACES x8             │
│  Chat    │ ┌────────────────────────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule │ │ FILTER [2] ‹status ▾│   SEARCH [3] ‹filter.subs…│       │  │ [Editor][Debug][Capsule]│
│  Module  │ │ ┌────────────────────────────────────────────────────┐ │  │ [Brain][Desktop†] †GATED│
│  Platform│ │ │ SUBSCRIPTION TABLE [4]                             │ │  │                         │
│  Ops     │ │ │ ‹tenant.name› ‹plan.name› ‹status› ‹ts› ‹seats› [⋯]│ │  │                         │
│  Settings│ │ │ ‹tenant.name› ‹plan.name› ‹status› ‹ts› ‹seats› [⋯]│ │  │                         │
│          │ │ │ ‹tenant.name› ‹plan.name› ‹status› ‹ts› ‹seats› [⋯]│ │  │                         │
│          │ │ │ (scroll)                                           │ │  │                         │
│          │ │ └────────────────────────────────────────────────────┘ │  │                         │
│          │ │ SEATS for selection [5]  ‹seats›                        │  │                         │
│          │ │ [ Save seats ] [6]     [ Cancel subscription ] [7]      │  │                         │
│          │ └────────────────────────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Subscriptions) | Screen shell. |
| 2 | UI-C-069 | Status filter select | Subscription states as stored. |
| 3 | UI-C-021 | Search | Filters the table live. |
| 4 | UI-C-022 | Subscription table | Rows `‹tenant.name›` / `‹plan.name›` / `‹status›` / `‹ts›` / `‹seats›`. |
| 4 | UI-C-028 | Row action menu (⋯) | Open / Change seats / Cancel. Cancel opens UI-M-03. |
| 5 | UI-C-072 | Seats field | Reused priority/seats numeric field; validated against the plan as stored. |
| 6 | UI-A-063 | Save seats | Writes the seat count for the selection. |
| 7 | UI-A-062 | Cancel subscription | DESTRUCTIVE — always opens UI-M-03. |

## 3. State variants

- **loading** — Table shows 5 skeleton rows. Verbatim label: "Loading subscriptions…"
- **empty** — `UI-C-023` verbatim: "No subscriptions yet. Create a tenant with a plan to get started."
  Empty under a filter verbatim: "No subscriptions match this filter. Clear the filter to see all."
- **error** — `UI-C-024` verbatim: "Subscriptions could not be loaded. Retry, or check that the
  billing service is reachable." Save failure verbatim: "Seat change was not saved. Your value is still here."
- **permission-denied** — Seats/Cancel disabled with inline reason
  "Subscription changes require the tenant-admin role." `UI-C-025` verbatim:
  "You do not have permission to manage subscriptions. Ask a platform admin for the tenant-admin role."
- **offline** — Table shows last cached page ("Showing the last synced page."); write actions
  disabled with reason "Subscription actions are unavailable offline."

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| UI-A-062 Cancel subscription | UI-M-03 Dialog | "Cancel the subscription for ‹tenant.name›? Access continues until ‹ts›." Cancel / Cancel subscription. |
| Row → Open | UI-M-01 Drawer (420px) | Subscription record detail; ESC closes, focus trap. |
| — | UI-M-02 | Not used by this screen. |

## 5. Honesty notes

Tenant names, plan names, statuses, seat counts and dates are store placeholders. No pricing is
printed on this screen.

End of Document
