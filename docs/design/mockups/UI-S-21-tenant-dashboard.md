# UI-S-21 — Tenant dashboard

Screen UI-S-21 · Facet: Platform · Route: `/admin/dashboard`
Source view per `SOMA-UI-IDREG-001.md`: `saas-tenant-dashboard` (`webui/src/views/saas-tenant-dashboard.ts`).
Route matches `webui/src/main.ts:356`.

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  Memory  Body  Governance ──────────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Tenant dashboard [1]                               │ SURFACES x8             │
│  Chat    │ ┌────────────────────────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule │ │ ‹tenant.name›  ·  ‹plan.name›  ·  ‹status›              │  │ [Editor][Debug][Capsule]│
│  Module  │ │ KPI TILES [2]                                            │  │ [Brain][Desktop†] †GATED│
│  Platform│ │ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────┐│  │                         │
│  Ops     │ │ │ users      │ │ capsules   │ │ messages   │ │ spend  ││  │                         │
│  Settings│ │ │ ‹ live ›   │ │ ‹ live ›   │ │ ‹ live ›   │ │ ‹ live ›││  │                         │
│          │ │ └────────────┘ └────────────┘ └────────────┘ └────────┘│  │                         │
│          │ │ ACTIVITY [3]                  QUICK ACTIONS [4]         │  │                         │
│          │ │  ‹ts› ‹activity.text›          [ Invite user ]         │  │                         │
│          │ │  ‹ts› ‹activity.text›          [ New capsule ]         │  │                         │
│          │ │  ‹ts› ‹activity.text›          [ View billing ]        │  │                         │
│          │ │  (scroll)                      [ View usage ]          │  │                         │
│          │ └────────────────────────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Tenant dashboard) | Screen shell. |
| 2 | UI-C-105 | KPI tile grid | Each tile is a READ-ONLY `‹ live value ›` from the analytics store. Never invented numbers. |
| 3 | UI-C-106 | Activity feed | Rows `‹ts›` + `‹activity.text›` from the audit/activity store. |
| 4 | UI-C-107 | Quick actions | Links to UI-S-22, UI-S-11, UI-S-25, UI-S-27. |
| — | UI-A-053 | Open quick action | Navigation only; the destination screens own their actions. |

## 3. State variants

- **loading** — Tiles show skeleton blocks; feed shows 4 skeleton rows. Verbatim label: "Loading dashboard…"
- **empty** — Tiles show `—` with helper (verbatim): "No data yet for this tenant."
  Feed verbatim: "No activity recorded yet."
- **error** — `UI-C-024` verbatim: "Dashboard data could not be loaded. Retry, or check that the
  somaAgent01 API is reachable."
- **permission-denied** — `UI-C-025` verbatim:
  "You do not have permission to view this tenant dashboard. Ask a platform admin for the member role."
  Chrome still frames the app.
- **offline** — Tiles keep last painted values with note "Showing the last synced values."
  Quick actions that navigate to write screens are disabled with reason "Unavailable offline."

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| KPI tile drill-down | — | Navigates to the owning screen (UI-S-22 / UI-S-25 / UI-S-27); no modal. |
| — | UI-M-01 / UI-M-02 / UI-M-03 | Not used by this screen. |

## 5. Honesty notes

Every KPI tile is a placeholder (`‹ live value ›`). No counts, percentages or spend figures are
fabricated anywhere on this screen.

End of Document
