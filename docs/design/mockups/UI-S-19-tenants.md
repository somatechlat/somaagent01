# UI-S-19 — Tenants

Screen UI-S-19 · Chrome: **UI-S-00 thin** (abbrev) · Catalog: `SOMA-UI-CATALOG-001.md` §2 Platform

**Status: GATED / future — does not ship on this deployment.**

> **Blocking reason:** This is a **standalone agent** deployment. `webui/src/main.ts:131-132`
> states it directly: *“No Soma or billing routes: this is a standalone agent, and the admin
> surface administers the agent only.”* There is **no tenant route** in `main.ts` and no tenant
> list API. ORPH-M1 (`SOMA-UI-NAV-AUDIT-001.md` §5).

Unknown paths fall through to `soma-chat` (`main.ts:408`) — never to this screen. Do not present
tenants as a shipped destination.

---

## 1. ASCII wireframe — future sketch (not routable)

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  ┌─ GATED ───────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                                           │  │
│  │   Tenant administration is not available on this deployment.                              │  │
│  │                                                                                           │  │
│  │   Blocking reason: standalone agent — no tenant routes in main.ts                          │  │
│  │   (main.ts:131-132). No tenant list API.                                                   │  │
│  │                                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  (no tenant table · no New tenant · no Suspend)                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

A future multi-tenant deployment would render a tenant table here. **No fields are specified** —
there is no tenant schema in `somaAgent01`, so any column list would be invented.

---

## 2. Real data

**None.** No tenant API exists on this deployment. Nothing is drawn from a store.

---

## 3. Control map

| # | Control | Behavior | Live? |
|---|---|---|---|
| 1 | Gated notice | Blocking reason verbatim. | live (notice) |
| — | Tenant table / Create / Suspend | **Not rendered** — no API, no route. | GATED |

---

## 4. Numbered journey (stops at the gate)

| Step | Where | Action | Result |
|---|---|---|---|
| **1** | anywhere | Look for a Tenants nav entry | None — tenants are not in the nav (standalone agent). |
| **2** | (bookmark) | Navigate to a tenant URL | Not routed; fallthrough → `soma-chat`. |
| **3** | here | Read the blocking reason | Understands multi-tenancy is out of scope for this deployment. |

---

## 5. States

| State | Behavior |
|---|---|
| default | GATED notice + blocking reason. |

No loading / empty / error — the feature never reaches an API.

---

## 6. Honesty

No invented tenant names, ids, statuses, plans, or counts. This mock exists to record the gap
(ORPH-M1), not to pretend the screen ships.

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/main.ts:131-132` | “No Soma or billing routes: this is a standalone agent” |
| `SOMA-UI-NAV-AUDIT-001.md` §5 ORPH-M1 | Tenant mocks have no route |

End of Document
