# UI-S-25 — Billing

Screen UI-S-25 · Facet: Platform · Route: `/admin/billing`
Source view per `SOMA-UI-IDREG-001.md`: `saas-tenant-billing` (`webui/src/views/saas-tenant-billing.ts`).
Route matches `webui/src/main.ts:317`. (A separate `/saas/billing` route mounts `saas-billing`
at `main.ts:309` and is not listed in `SOMA-UI-IDREG-001.md`.)

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  Memory  Body  Governance ──────────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Billing [1]                                      │ SURFACES x8             │
│  Chat    │ ┌────────────────────────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule │ │ PLAN CARD [2]                                          │  │ [Editor][Debug][Capsule]│
│  Module  │ │  ‹plan.name› · ‹status› · renews ‹ts›                  │  │ [Brain][Desktop†] †GATED│
│  Platform│ │  [ Change plan ] [3]                                    │  │                         │
│  Ops     │ │ PAYMENT METHOD [4]  ‹brand›  sk-••••••••aBcD (rotate in Vault)│                    │
│  Settings│ │ INVOICES [5]                                            │  │                         │
│          │ │ ┌────────────────────────────────────────────────────┐ │  │                         │
│          │ │ │ ‹invoice.id›  ‹ts›  ‹amount›  ‹status›  [ Download ]│ │  │                         │
│          │ │ │ ‹invoice.id›  ‹ts›  ‹amount›  ‹status›  [ Download ]│ │  │                         │
│          │ │ │ (scroll)                                           │ │  │                         │
│          │ │ └────────────────────────────────────────────────────┘ │  │                         │
│          │ │ balance: ‹ live value ›   as of ‹ timestamp ›           │  │                         │
│          │ └────────────────────────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Billing) | Screen shell. |
| 2 | UI-C-117 | Plan summary card | Read-only `‹plan.name›` / `‹status›` / `‹ts›`. |
| 3 | UI-A-061 | Change plan | Navigates to UI-S-26 / plan picker. |
| 4 | UI-C-118 | Payment method row | Masked instrument only — `sk-••••••••aBcD` + "rotate in Vault". Never a real value. |
| 5 | UI-C-119 | Invoice table | Rows `‹invoice.id›` / `‹ts›` / `‹amount›` / `‹status›`. |
| 5 | UI-A-048 | Download invoice | Per-row action; enabled when `‹status›` says the invoice exists. |
| — | UI-C-028 | Row action menu (⋯) | Download / View. |

## 3. State variants

- **loading** — Invoice table skeleton; plan card verbatim label: "Loading billing…"
- **empty** — Invoices `UI-C-023` verbatim: "No invoices yet. Invoices appear after the first billing cycle."
  Payment method verbatim: "No payment method on file."
- **error** — `UI-C-024` verbatim: "Billing could not be loaded. Retry, or check that the
  billing service is reachable." Download failure verbatim: "Invoice download failed. Try again."
- **permission-denied** — Download/Change plan disabled with inline reason
  "Billing requires the tenant-admin role." `UI-C-025` verbatim:
  "You do not have permission to view billing. Ask a platform admin for the tenant-admin role."
- **offline** — Table shows last cached page ("Showing the last synced page."); Download/Change
  plan disabled with reason "Billing actions are unavailable offline."

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| UI-A-061 Change plan | UI-M-01 Drawer (420px) | Plan comparison against stored plan records; ESC closes, focus trap. |
| Payment method "update" | UI-M-02 Full-screen | Hosted payment-element hand-off; explicit dismiss only. Never an in-page card form. |
| — | UI-M-03 | Not used by this screen. |

## 5. Honesty notes

Amounts, invoice ids and balances are `‹ live value ›` / store placeholders — no fabricated money
figures. The payment instrument is always masked (`sk-••••••••aBcD`) with a "rotate in Vault"
note. Plan prices come from the plan store (UI-S-28 tier builder), never from this mockup.

End of Document
