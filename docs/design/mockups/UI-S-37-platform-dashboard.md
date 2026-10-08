# UI-S-37 — Platform dashboard

Screen UI-S-37 · Chrome: **UI-S-00 thin** (abbrev) · Catalog: `SOMA-UI-CATALOG-001.md` §2 Platform

**Status: GATED / orphan claim — retargeted.** Read this file as a **gap note**, not a shipped screen.

> **Blocking reason (GAP-N1 / ORPH-M4).** This mock claimed `/saas/dashboard`, which is **not a
> route in `main.ts`**. The paths that look like a platform home — **`/platform`** · **`/soma`** ·
> **`/soma/dashboard`** — all load **`soma-agent-metrics`** (`main.ts:133-136`). There is **no**
> `platform-dashboard` view on this deployment.
>
> **The real surface for those paths is UI-S-45 agent metrics.** Do not keep both claims
> (`SOMA-UI-NAV-AUDIT-001.md` GAP-N1). This file is not routable.

---

## 1. ASCII wireframe — gap notice (not routable)

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  ┌─ GATED / RETARGETED ──────────────────────────────────────────────────────────────────────┐  │
│  │                                                                                           │  │
│  │   This platform-dashboard mock is not routable.                                           │  │
│  │                                                                                           │  │
│  │   /platform · /soma · /soma/dashboard load soma-agent-metrics (main.ts:133-136).           │  │
│  │   Open UI-S-45 (agent metrics) for the real surface.                                      │  │
│  │                                                                                           │  │
│  │   Blocking reason: no platform-dashboard view exists (GAP-N1 / ORPH-M4).                  │  │
│  │                                                                                           │  │
│  │   [ Open agent metrics → /admin/metrics ]                                                 │  │
│  │                                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Real data

**None for a separate platform dashboard.** The metrics those paths actually serve are specified
in **UI-S-45** (`soma-agent-metrics`). Duplicating them here would be triplication.

| Claimed in the old mock | Reality |
|---|---|
| `/saas/dashboard` route | **not in `main.ts`** |
| platform KPI tiles | served by `soma-agent-metrics` → UI-S-45 |
| service status / activity feed | no `platform-dashboard` view to host them |

---

## 3. Control map

| # | Control | Behavior | Live? |
|---|---|---|---|
| 1 | Gap notice | Names the real route + view (GAP-N1). | live (notice) |
| 2 | Open agent metrics | `router → /admin/metrics` (UI-S-45). | live |
| — | KPI tiles / service table / activity | **Not rendered here** — see UI-S-45. | — |

---

## 4. Numbered journey (retarget, not a dead end)

| Step | Where | Action | API | Result |
|---|---|---|---|---|
| **1** | nav / bookmark | Expect a platform home at `/platform` | `main.ts:133-136` | `soma-agent-metrics` mounts — **UI-S-45**, not this file. |
| **2** | here | Read the gap notice | — | Learns the mock claim `/saas/dashboard` was wrong (GAP-N1). |
| **3** | here | Click **Open agent metrics** | `router → /admin/metrics` | UI-S-45 — the one metrics surface (DUP-5). |

---

## 5. States

| State | Behavior |
|---|---|
| default | Gap notice + retarget link. |

---

## 6. Honesty

No KPI tiles, service rows, or activity feed are drawn here — that would duplicate UI-S-45 and
invent a view the router never mounts. GAP-N1 is recorded, not papered over.

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/main.ts:133-136` | `/platform` · `/soma` · `/soma/dashboard` → `soma-agent-metrics` |
| `SOMA-UI-NAV-AUDIT-001.md` GAP-N1 · ORPH-M4 | `/saas/dashboard` is not a route; retarget to UI-S-45 |
| `UI-S-45-agent-metrics.md` | The real metrics surface |

End of Document
