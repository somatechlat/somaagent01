# UI-S-45 — Agent metrics

Screen UI-S-45 · Routes: **`/admin/metrics`** (`main.ts:179`) · **`/platform`** · **`/soma`** ·
**`/soma/dashboard`** (`main.ts:133-136`) — all load **`soma-agent-metrics`**
Chrome: **UI-S-00 thin** (abbrev) · Catalog: `SOMA-UI-CATALOG-001.md` §2 Platform
Live view: `webui/src/views/soma-agent-metrics.ts` (`soma-agent-metrics`)

**Status: LIVE.** This is **the one metrics surface** (DUP-5).

> **GAP-N1 (resolved here).** `SOMA-UI-NAV-001.md` claimed `/platform` → a platform-dashboard
> (UI-S-37). **`main.ts:133-136` actually loads `soma-agent-metrics`** — this view. UI-S-37 is a
> retargeted gap note, not a destination. Do not keep both claims.

---

## 1. ASCII wireframe — agent metrics workspace

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  AGENT METRICS                                                           [⟳ Refresh]           │
│  agent [‹agent_id› ▾]   range [▾]                                                                │
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
│                                                                                                  │
│  ┌─ ACTIVITY (real events only) ─────────────────────────────────────────────────────────────┐  │
│  │  ‹ts›   ‹actor›   ‹event›                                                    [inspect]    │  │
│  │  ‹ts›   ‹actor›   ‹event›                                                    [inspect]    │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Real data

| UI element | Source | Absent handling |
|---|---|---|
| Metric tiles | `soma-agent-metrics` API values | `—` (never `0`, never a guess) |
| Charts / series | only when the API returns series | omit the chart entirely |
| Activity rows | real audit/activity events | `—` for optional fields |

No hard-coded numbers. No sparklines without series data. No derived AgentIQ dump on chrome.

---

## 3. Control map

| # | Control | API / behavior | Live? |
|---|---|---|---|
| 1 | Agent selector | Scopes the metrics read. | live |
| 2 | Range selector | Scopes the metrics read. | live |
| 3 | Metric tiles | Label + value from the agent metrics API. | live |
| 4 | Series panel | Renders only when series data is returned. | live |
| 5 | Activity rows | Real events only. inspect → UI-M-01 drawer. | live |
| 6 | Refresh | Re-fetch in place. | live |

---

## 4. Numbered journey — read agent metrics

| Step | Where | Action | API | Result |
|---|---|---|---|---|
| **1** | `/platform` (or `/admin/metrics`) | Screen loads | `soma-agent-metrics` (`main.ts:133-136`, `179`) | Tiles paint real values. |
| **2** | metrics | Pick an agent / range | re-fetch | Tiles repainted for that scope. |
| **3** | metrics | Read a tile | — | `—` when the server omits the figure. |
| **4** | activity | Click **inspect** | — | UI-M-01 drawer with the event record. |
| **5** | metrics | Need **platform** metrics | — | UI-S-38 (`/platform/metrics`). Not this screen. |
| **6** | metrics | Expect UI-S-37 platform dashboard | — | It does not exist — GAP-N1. This **is** the `/platform` surface. |

---

## 5. States

| State | Verbatim / behavior |
|---|---|
| loading | Skeleton tiles + `loading` chip. No counts or charts while loading. |
| empty | “No agent metrics yet. Values will appear here as the agent is used.” |
| empty (activity) | “No activity yet.” |
| error | “Couldn’t load agent metrics. ‹ reason from API ›” |
| permission-denied | “You don’t have access to agent metrics. Requires the platform-admin role.” |
| offline | “You’re offline. Metrics may be stale.” |

---

## 6. Honesty

Tile values are API numbers only; `—` when absent. No charts without series data. `/platform` ·
`/soma` · `/soma/dashboard` · `/admin/metrics` all land **here** — one surface (DUP-5). UI-S-37 is
not a second home (GAP-N1).

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/main.ts:133-136` | `/platform` · `/soma` · `/soma/dashboard` → `soma-agent-metrics` |
| `webui/src/main.ts:179` | `/admin/metrics` → `soma-agent-metrics` |
| `webui/src/views/soma-agent-metrics.ts` | Live view |
| `SOMA-UI-NAV-AUDIT-001.md` GAP-N1 · DUP-5 | `/platform` = agent metrics, not a platform dashboard |

End of Document
