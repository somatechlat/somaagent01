# UI-S-25 — Billing

Screen UI-S-25 · Chrome: **UI-S-00 thin** (abbrev) · Catalog: `SOMA-UI-CATALOG-001.md` §2 Platform

**Status: GATED / future — does not ship on this deployment.**

> **Blocking reason:** Standalone agent — **no billing routes** in `main.ts`
> (`main.ts:131-132`: “No Soma or billing routes: this is a standalone agent, and the admin
> surface administers the agent only.”). No billing API. ORPH-M2
> (`SOMA-UI-NAV-AUDIT-001.md` §5). Out of scope for this deployment.

---

## 1. ASCII wireframe — future sketch (not routable)

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  ┌─ GATED ───────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                                           │  │
│  │   Billing is not available on this deployment.                                            │  │
│  │                                                                                           │  │
│  │   Blocking reason: standalone agent — no billing routes in main.ts                         │  │
│  │   (main.ts:131-132). No billing API.                                                       │  │
│  │                                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  (no invoices · no payment methods · no plan table)                                              │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Real data

**None.** No billing schema or endpoint exists. Any invoice, amount, or plan name would be invented.

---

## 3. Control map

| # | Control | Behavior | Live? |
|---|---|---|---|
| 1 | Gated notice | Blocking reason verbatim. | live (notice) |
| — | Invoices / payments / plans | **Not rendered** — no API, no route. | GATED |

---

## 4. Numbered journey (stops at the gate)

| Step | Where | Action | Result |
|---|---|---|---|
| **1** | anywhere | Look for a Billing nav entry | None — billing is not in the nav (standalone agent). |
| **2** | (bookmark) | Navigate to a billing URL | Not routed; fallthrough → `soma-chat`. |
| **3** | here | Read the blocking reason | Understands billing is out of scope for this deployment. |

---

## 5. States

| State | Behavior |
|---|---|
| default | GATED notice + blocking reason. |

---

## 6. Honesty

No invented invoices, amounts, plans, or payment states. This mock records the gap (ORPH-M2).

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/main.ts:131-132` | Standalone agent — no billing routes |
| `SOMA-UI-NAV-AUDIT-001.md` §5 ORPH-M2 | Billing mocks have no route |

End of Document
