# UI-S-27 — Usage analytics

Screen UI-S-27 · Chrome: **UI-S-00 thin** (abbrev) · Catalog: `SOMA-UI-CATALOG-001.md` §2 Platform

**Status: GATED / future — does not ship on this deployment.**

> **Blocking reason:** Standalone agent — **no billing/usage routes** in `main.ts`
> (`main.ts:131-132`: “No Soma or billing routes: this is a standalone agent”). No usage-metering
> API. ORPH-M2 (`SOMA-UI-NAV-AUDIT-001.md` §5). Out of scope for this deployment.

Agent-level metrics (if any) belong to **UI-S-45 agent metrics** (`/admin/metrics`), not to a
billing usage screen. Do not fabricate a metering story here.

---

## 1. ASCII wireframe — future sketch (not routable)

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  ┌─ GATED ───────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                                           │  │
│  │   Usage analytics are not available on this deployment.                                   │  │
│  │                                                                                           │  │
│  │   Blocking reason: standalone agent — no billing routes in main.ts                         │  │
│  │   (main.ts:131-132). No usage-metering API.                                                │  │
│  │                                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  (no usage charts · no quota meters · no cost breakdown)                                         │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Real data

**None.** No usage-metering schema or endpoint exists. Any chart or quota number would be a
fabricated metric.

---

## 3. Control map

| # | Control | Behavior | Live? |
|---|---|---|---|
| 1 | Gated notice | Blocking reason verbatim. | live (notice) |
| — | Usage charts / quotas | **Not rendered** — no API, no route. | GATED |

---

## 4. Numbered journey (stops at the gate)

| Step | Where | Action | Result |
|---|---|---|---|
| **1** | anywhere | Look for a Usage nav entry | None — not in the nav (standalone agent). |
| **2** | (bookmark) | Navigate to a usage URL | Not routed; fallthrough → `soma-chat`. |
| **3** | here | Read the blocking reason | Understands usage metering is out of scope. |

---

## 5. States

| State | Behavior |
|---|---|
| default | GATED notice + blocking reason. |

---

## 6. Honesty

No invented usage numbers, charts, or quota figures. This mock records the gap (ORPH-M2).

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/main.ts:131-132` | Standalone agent — no billing routes |
| `SOMA-UI-NAV-AUDIT-001.md` §5 ORPH-M2 | Billing mocks have no route |

End of Document
