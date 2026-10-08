# UI-S-40 — Rate limits

Screen UI-S-40 · Routes: **`/platform/ratelimits`** · **`/platform/infrastructure/redis/ratelimits`**
(`main.ts:147` → `soma-infrastructure-dashboard`, `activeTab='ratelimits'`)
Chrome: **UI-S-00 thin** (abbrev) · Catalog: `SOMA-UI-CATALOG-001.md` §2 Platform
Live view: `webui/src/views/soma-infrastructure-dashboard.ts` (same view as UI-S-39)

**Status: LIVE — as a tab, not a separate dashboard.** Per `main.ts:147-152`: “Rate Limits live on
the Infrastructure dashboard (one surface).” This file documents the rate-limits **tab** of
UI-S-39. There is no standalone rate-limits view.

---

## 1. ASCII wireframe — rate-limits tab (of UI-S-39)

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE                                                      [⟳ Refresh]                │
│  tabs: [ Overview ][ Redis ][ Rate limits ● ]                                                    │
│                                                                                                  │
│  ┌─ RATE LIMITS (API values only) ───────────────────────────────────────────────────────────┐  │
│  │  key / scope          limit              window            current                         │  │
│  │  ‹key›                ‹limit | —›        ‹window | —›     ‹current | —›                    │  │
│  │  ‹key›                ‹limit | —›        ‹window | —›     ‹current | —›                    │  │
│  │  (scroll)                                                                                   │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  values from the infrastructure API — `—` when the server omits a figure                         │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Real data

| UI column | Source | Absent handling |
|---|---|---|
| key / scope | rate-limit record | required |
| limit | record | `—` |
| window | record | `—` |
| current | record | `—` (never `0` on failure) |

Same view and API as UI-S-39 — no second endpoint, no second store.

---

## 3. Control map

| # | Control | API / behavior | Live? |
|---|---|---|---|
| 1 | Rate-limits tab | `activeTab='ratelimits'` on `soma-infrastructure-dashboard`. | live |
| 2 | Rate-limit rows | Values from the infrastructure API. | live |
| 3 | Refresh | Re-fetch in place. | live |
| 4 | Overview / Redis tabs | Back to the other panes of UI-S-39. | live |

---

## 4. Numbered journey — inspect rate limits

| Step | Where | Action | API | Result |
|---|---|---|---|---|
| **1** | `/platform/ratelimits` | Screen loads | `soma-infrastructure-dashboard` `activeTab='ratelimits'` | Rate-limits tab paints. |
| **2** | tab | Read a row | — | `—` when the server omits a figure. |
| **3** | tab | Click **Refresh** | re-fetch | Values repainted. |
| **4** | tab | Click **Overview** | same view | UI-S-39 overview pane. |

---

## 5. States

| State | Verbatim / behavior |
|---|---|
| loading | Skeleton rows. No values while loading. |
| empty | “No rate limits configured.” |
| error | “Couldn’t load rate limits. ‹ reason from API ›” |
| permission-denied | “You don’t have access to rate limits. Requires the platform-admin role.” |
| offline | “You’re offline. Values may be stale.” |

---

## 6. Honesty

Values are API numbers only; `—` when absent. This is **one surface** with UI-S-39
(`main.ts:147-152`) — do not present it as a separate dashboard.

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/main.ts:147-152` | `/platform/ratelimits` → `soma-infrastructure-dashboard` + `activeTab='ratelimits'` |
| `webui/src/views/soma-infrastructure-dashboard.ts` | Same live view as UI-S-39 |
| `SOMA-UI-NAV-AUDIT-001.md` §1 #26 | Route OK |

End of Document
