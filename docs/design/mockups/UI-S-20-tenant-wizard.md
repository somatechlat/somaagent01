# UI-S-20 — Tenant wizard

Screen UI-S-20 · Chrome: **UI-S-00 thin** (abbrev) · Catalog: `SOMA-UI-CATALOG-001.md` §2 Platform

**Status: GATED / future — does not ship on this deployment.**

> **Blocking reason:** Standalone agent — **no tenant routes** in `main.ts`
> (`main.ts:131-132`: “No Soma or billing routes: this is a standalone agent”). No tenant-create
> API. ORPH-M1 (`SOMA-UI-NAV-AUDIT-001.md` §5). There is no UI-S-19 to launch this wizard from.

---

## 1. ASCII wireframe — future sketch (not routable)

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  ┌─ GATED ───────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                                           │  │
│  │   Tenant creation is not available on this deployment.                                    │  │
│  │                                                                                           │  │
│  │   Blocking reason: standalone agent — no tenant routes in main.ts                          │  │
│  │   (main.ts:131-132). No tenant-create API.                                                 │  │
│  │                                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  (no wizard steps · no Create tenant)                                                            │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Real data

**None.** No tenant schema exists on this deployment — any wizard field list would be invented.

---

## 3. Control map

| # | Control | Behavior | Live? |
|---|---|---|---|
| 1 | Gated notice | Blocking reason verbatim. | live (notice) |
| — | Wizard steps / Create | **Not rendered** — no API, no route. | GATED |

---

## 4. Numbered journey (stops at the gate)

| Step | Where | Action | Result |
|---|---|---|---|
| **1** | UI-S-19 | Look for “New tenant” | UI-S-19 is itself gated — no entry point ships. |
| **2** | (bookmark) | Navigate to a tenant-wizard URL | Not routed; fallthrough → `soma-chat`. |
| **3** | here | Read the blocking reason | Understands tenant creation is out of scope. |

---

## 5. States

| State | Behavior |
|---|---|
| default | GATED notice + blocking reason. |

---

## 6. Honesty

No invented wizard fields, plan names, or limits. This mock records the gap (ORPH-M1).

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/main.ts:131-132` | Standalone agent — no tenant routes |
| `SOMA-UI-NAV-AUDIT-001.md` §5 ORPH-M1 | Tenant mocks have no route |

End of Document
