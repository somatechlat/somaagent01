# UI-S-38 — Platform metrics

Screen UI-S-38 · Routes: **`/platform/metrics`** · **`/soma/metrics`** (`main.ts:193` → `platform-metrics-dashboard`)
Chrome: **UI-S-00 thin** (abbrev) · Catalog: `SOMA-UI-CATALOG-001.md` §2 Platform
Live view: `webui/src/views/platform-metrics-dashboard.ts` (`platform-metrics-dashboard`)

**Status: LIVE.** Platform-wide metrics dashboard. **Not** the agent metrics surface —
that is **UI-S-45** (`/admin/metrics`, `soma-agent-metrics`). Distinct views, distinct routes.

---

## 1. ASCII wireframe — platform metrics workspace

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  PLATFORM METRICS                                                     [⟳ Refresh]               │
│                                                                                                  │
│  ┌─ METRIC TILES (API numbers only) ─────────────────────────────────────────────────────────┐  │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐                                  │  │
│  │  │ ‹value›   │ │ ‹value›   │ │ ‹value›   │ │ ‹value›   │                                  │  │
│  │  │ ‹label›   │ │ ‹label›   │ │ ‹label›   │ │ ‹label›   │                                  │  │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘                                  │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  ┌─ SERIES (only if the API returns series) ─────────────────────────────────────────────────┐  │
│  │  ‹metric›  ‹series›                                                                       │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Real data

| UI element | Source | Absent handling |
|---|---|---|
| Metric tiles | `platform-metrics-dashboard` API values | `—` (never `0`, never a guess) |
| Charts / series | only when the API returns series | omit the chart entirely |

No hard-coded numbers. No sparklines without series data.

---

## 3. Control map

| # | Control | API / behavior | Live? |
|---|---|---|---|
| 1 | Metric tiles | Label + value from the platform metrics API. | live |
| 2 | Series panel | Renders only when series data is returned. | live |
| 3 | Refresh | Re-fetch all tiles in place. | live |

---

## 4. Numbered journey — read platform metrics

| Step | Where | Action | API | Result |
|---|---|---|---|---|
| **1** | `/platform/metrics` | Screen loads | platform metrics API | Tiles paint real values. |
| **2** | metrics | Read a tile | — | `—` when the server omits the figure. |
| **3** | metrics | Click **Refresh** | re-fetch | Values repainted. |
| **4** | metrics | Need **agent** metrics | — | UI-S-45 (`/admin/metrics`). Not this screen. |

---

## 5. States

| State | Verbatim / behavior |
|---|---|
| loading | Skeleton tiles. No counts or charts while loading. |
| empty | “No platform metrics yet. Values will appear here as the platform is used.” |
| error | “Couldn’t load platform metrics. ‹ reason from API ›” |
| permission-denied | “You don’t have access to platform metrics. Requires the platform-admin role.” |
| offline | “You’re offline. Metrics may be stale.” |

---

## 6. Honesty

Tile values are API numbers only. `—` when absent. No charts without series data. This screen is
**not** UI-S-45 — do not merge the two metric stories.

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/main.ts:193` | `/platform/metrics` · `/soma/metrics` → `platform-metrics-dashboard` |
| `webui/src/views/platform-metrics-dashboard.ts` | Live view |
| `SOMA-UI-NAV-AUDIT-001.md` §1 #32 | Route OK |

End of Document
