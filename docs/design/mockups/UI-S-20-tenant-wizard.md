# UI-S-20 — Tenant wizard

Screen UI-S-20 · Facet: Platform · Route: `/saas/tenants/new`
Source view per `SOMA-UI-IDREG-001.md`: `saas-tenant-wizard` (`webui/src/views/saas-tenant-wizard.ts`).
Route matches `webui/src/main.ts:154`.

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  Memory  Body  Governance ──────────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — New tenant [1]                                    │ SURFACES x8             │
│  Chat    │ ┌──────────────┐ ┌──────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule │ │ STEPS [2]    │ │ STEP ‹n›: ‹step.title› [3]           │  │ [Editor][Debug][Capsule]│
│  Module  │ │  1 ● Basics  │ │  name      [ ‹tenant.name›        ]  │  │ [Brain][Desktop†] †GATED│
│  Platform│ │  2 ○ Plan    │ │  slug      [ ‹tenant.slug›        ]  │  │                         │
│  Ops     │ │  3 ○ Admin   │ │  region    [ ‹region ▾│           ]  │  │                         │
│  Settings│ │  4 ○ Review  │ │ PLAN [4]                              │  │                         │
│          │ │              │ │  ( ‹plan.name› )  ( ‹plan.name› )    │  │                         │
│          │ │              │ │ REVIEW [5]                            │  │                         │
│          │ │              │ │  ‹tenant.name› · ‹plan.name› · ‹region›│  │                         │
│          │ │              │ │ [ Back ] [6]  [ Next ] [7]  [ Create ] [8]│                         │
│          │ └──────────────┘ └──────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Tenant wizard) | Screen shell. |
| 2 | UI-C-101 | Wizard step rail | Steps 1–4; shows current/completed state only. |
| 3 | UI-C-102 | Wizard form fields | Name, slug, region — validated on Next. |
| 4 | UI-C-103 | Plan select | Options come from the plan store (`‹plan.name›`). |
| 5 | UI-C-104 | Review panel | Read-only summary of entered values. |
| 6 | UI-A-051 | Next | Moves the step rail forward; validates the current step first. |
| 7 | UI-A-044 | Back | Returns one step; keeps entered values. |
| 8 | UI-A-052 | Create tenant | Final submit; enabled only on the review step. |

## 3. State variants

- **loading** — Plan select skeleton. Verbatim label: "Loading plans…"
- **empty** — Plan step verbatim: "No plans are available. Ask a platform admin to define a plan first."
  (Create stays disabled with inline reason "Create is unavailable until a plan is selected.")
- **error** — `UI-C-024` verbatim: "Tenant could not be created. Your details are still here — try again."
  Validation error verbatim: "Check the highlighted fields and try again."
- **permission-denied** — Wizard replaced by `UI-C-025`, verbatim:
  "You do not have permission to create tenants. Ask a platform admin for the platform-admin role."
- **offline** — Create disabled with inline reason "Create is unavailable offline."
  Form fields remain editable locally; Next/Back keep working.

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| Leave wizard with entered values | UI-M-03 Dialog | "Leave this wizard? Entered details will be lost." Cancel / Leave. |
| UI-A-052 Create tenant | — | Submit runs inline; success routes to UI-S-21. No modal. |
| — | UI-M-01 / UI-M-02 | Not used by this screen. |

## 5. Honesty notes

Plan names and region options are store placeholders. No pricing or quota numbers are printed
here — those live on UI-S-25 / UI-S-28 against real plan records.

End of Document
