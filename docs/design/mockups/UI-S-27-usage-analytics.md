# UI-S-27 — Usage analytics

Screen UI-S-27 · Facet: Platform · Route: `/platform/usage`
Source view per `SOMA-UI-IDREG-001.md`: `saas-usage-analytics` (`webui/src/views/saas-usage-analytics.ts`).
Route matches `webui/src/main.ts:121`.

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  Memory  Body  Governance ──────────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Usage analytics [1]                                │ SURFACES x8             │
│  Chat    │ ┌────────────────────────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule │ │ DATE RANGE [2] [ ‹from› ] … [ ‹to› ]   METRIC [3] ‹metric ▾│ │ [Editor][Debug][Capsule]│
│  Module  │ │ [ Apply ] [4]   [ Export CSV ] [5]                       │  │ [Brain][Desktop†] †GATED│
│  Platform│ │ CHART [6]                                                 │  │                         │
│  Ops     │ │ ┌────────────────────────────────────────────────────┐ │  │                         │
│  Settings│ │ │        ‹ live value › over ‹date range›             │ │  │                         │
│          │ │ │        (line chart — no fabricated series)          │ │  │                         │
│          │ │ │        ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·       │ │  │                         │
│          │ │ └────────────────────────────────────────────────────┘ │  │                         │
│          │ │ BREAKDOWN TABLE [7]                                    │  │                         │
│          │ │  ‹dimension›  ‹ live value ›  ‹ live value ›           │  │                         │
│          │ │  ‹dimension›  ‹ live value ›  ‹ live value ›           │  │                         │
│          │ └────────────────────────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Usage analytics) | Screen shell. |
| 2 | UI-C-120 | Date range fields | From/to bound to the analytics store query. (Shared numeric/date field id.) |
| 3 | UI-C-083 | Metric select | Metrics the analytics store actually exposes. (Shared select id.) |
| 4 | UI-A-065 | Apply date range | Re-runs the query; refreshes chart and table. |
| 5 | UI-A-064 | Export usage CSV | Produces a file for the current range and metric. |
| 6 | UI-C-099 | Usage chart | READ-ONLY visualisation of `‹ live value ›` series. No fabricated points. |
| 7 | UI-C-022 | Breakdown table | Rows `‹dimension›` + `‹ live value ›` columns. |

## 3. State variants

- **loading** — Chart shows a skeleton grid; table shows 5 skeleton rows. Verbatim label: "Loading usage…"
- **empty** — Chart area `UI-C-023` verbatim: "No usage recorded for this date range."
  Table verbatim: "No breakdown rows for this date range."
- **error** — `UI-C-024` verbatim: "Usage could not be loaded. Retry, or check that the
  analytics service is reachable." Export failure verbatim: "CSV export failed. Try again."
- **permission-denied** — Export disabled; `UI-C-025` verbatim:
  "You do not have permission to view usage analytics. Ask a platform admin for the tenant-admin role."
  Chart remains visible if the role can read, otherwise the whole workspace is replaced by the notice.
- **offline** — Chart and table show the last synced window with note "Showing the last synced window."
  Apply/Export disabled with reason "Usage actions are unavailable offline."

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| Chart point drill-down | UI-M-01 Drawer (420px) | Row detail for that point's dimension; ESC closes, focus trap. |
| Export CSV with a large range | UI-M-03 Dialog | "This export may be large. Continue?" Cancel / Export. |
| — | UI-M-02 | Not used by this screen. |

## 5. Honesty notes

Chart series, axis values and table cells are all `‹ live value ›` placeholders. No usage numbers,
percentages or trends are invented in this mockup.

End of Document
