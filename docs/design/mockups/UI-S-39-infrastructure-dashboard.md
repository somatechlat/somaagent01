# UI-S-39 — Infrastructure dashboard

Screen UI-S-39 · Routes: **`/platform/infrastructure`** · **`/soma/infrastructure`**
(`main.ts:186` → `soma-infrastructure-dashboard`)
Chrome: **UI-S-00 thin** (abbrev) · Catalog: `SOMA-UI-CATALOG-001.md` §2 Platform
Live view: `webui/src/views/soma-infrastructure-dashboard.ts` (`soma-infrastructure-dashboard`)

**Status: LIVE.** Infrastructure administration surface. The rate-limits tab is **UI-S-40** —
the same view with `activeTab = 'ratelimits'` (`main.ts:147`). One surface, two entry paths.

---

## 1. ASCII wireframe — infrastructure workspace

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE                                                      [⟳ Refresh]                │
│  tabs: [ Overview ][ Redis ][ Rate limits (UI-S-40) ]                                            │
│                                                                                                  │
│  ┌─ SERVICE STATUS (from the health endpoint) ───────────────────────────────────────────────┐  │
│  │  service            status              last check                                         │  │
│  │  ‹name›             ‹state›             ‹ts | —›                                           │  │
│  │  ‹name›             ‹state›             ‹ts | —›                                           │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  ┌─ INFRA METRICS (API numbers only) ────────────────────────────────────────────────────────┐  │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐                                  │  │
│  │  │ ‹value›   │ │ ‹value›   │ │ ‹value›   │ │ ‹value›   │                                  │  │
│  │  │ ‹label›   │ │ ‹label›   │ │ ‹label›   │ │ ‹label›   │                                  │  │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘                                  │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Real data

| UI element | Source | Absent handling |
|---|---|---|
| Service status | health endpoint | `—` for last-check when the service reports none |
| Infra metric tiles | infrastructure API values | `—` (never `0`) |
| Rate-limits tab | `soma-infrastructure-dashboard` `activeTab='ratelimits'` | see UI-S-40 |

No hard-coded service names, no invented uptime percentages.

---

## 3. Control map

| # | Control | API / behavior | Live? |
|---|---|---|---|
| 1 | Overview tab | Service status + infra metrics. | live |
| 2 | Redis tab | Redis-side infra detail (same view). | live |
| 3 | Rate limits tab | `activeTab='ratelimits'` → UI-S-40. | live |
| 4 | Service status row | `status` from health; `last check` only when reported. | live |
| 5 | Refresh | Re-fetch in place. | live |

---

## 4. Numbered journey — check infrastructure health

| Step | Where | Action | API | Result |
|---|---|---|---|---|
| **1** | `/platform/infrastructure` | Screen loads | health endpoint | Service rows paint real states. |
| **2** | overview | Read a service row | — | `last check` is `—` when the service reports none. |
| **3** | tabs | Click **Rate limits** | `activeTab='ratelimits'` | UI-S-40 (same view). |
| **4** | any | Click **Refresh** | re-fetch | Values repainted. |

---

## 5. States

| State | Verbatim / behavior |
|---|---|
| loading | Skeleton rows + `loading` chip. No metrics while loading. |
| empty | “No infrastructure services reported.” |
| error | “Couldn’t load the infrastructure dashboard. ‹ reason from API ›” |
| permission-denied | “You don’t have access to infrastructure. Requires the platform-admin role.” |
| offline | “You’re offline. Values may be stale.” |

---

## 6. Honesty

Service names, states and timestamps come from the health endpoint only. No fabricated uptime or
capacity numbers. The rate-limits tab is the **same** surface as UI-S-40 (not a second dashboard).

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/main.ts:186` | `/platform/infrastructure` · `/soma/infrastructure` → `soma-infrastructure-dashboard` |
| `webui/src/main.ts:147` | `/platform/ratelimits` → same view, `activeTab='ratelimits'` |
| `webui/src/views/soma-infrastructure-dashboard.ts` | Live view |
| `SOMA-UI-NAV-AUDIT-001.md` §1 #31 | Route OK |

End of Document
