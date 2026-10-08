# UI-S-43 — Audit dashboard

Screen UI-S-43 · Routes: **`/platform/audit`** · **`/soma/audit`** · **`/audit`** · **`/admin/audit`**
(`main.ts:265` and `main.ts:308` → `soma-audit-dashboard`)
Chrome: **UI-S-00 thin** (abbrev) · Catalog: `SOMA-UI-CATALOG-001.md` §2 Platform
Live view: `webui/src/views/soma-audit-dashboard.ts` (`soma-audit-dashboard`)

**Status: LIVE.** This file is the **dashboard chrome** of the audit surface. The log table is the
**pane** of the same screen (**UI-S-44**) — not a second destination (DUP-4). All four route
aliases load one view.

---

## 1. ASCII wireframe — audit dashboard (chrome + summary)

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  AUDIT                                                                     [⟳ Refresh]          │
│  [Search events…                     ]  actor [all ▾]   action [all ▾]   range [▾]              │
│                                                                                                  │
│  ┌─ SUMMARY (API numbers only) ──────────────────────────────────────────────────────────────┐  │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐                                  │  │
│  │  │ ‹value›   │ │ ‹value›   │ │ ‹value›   │ │ ‹value›   │                                  │  │
│  │  │ ‹label›   │ │ ‹label›   │ │ ‹label›   │ │ ‹label›   │                                  │  │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘                                  │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  ┌─ EVENT LOG (UI-S-44 pane) ───────────────────────────────────────────────────────────────┐  │
│  │  ts                  actor              action              target            [inspect]   │  │
│  │  ‹ts›                ‹actor›            ‹action›            ‹target | —›                  │  │
│  │  ‹ts›                ‹actor›            ‹action›            ‹target | —›                  │  │
│  │  (scroll)                                                                                   │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Real data

| UI element | Source | Absent handling |
|---|---|---|
| Summary tiles | audit API counts | `—` (never `0` on failure) |
| Event rows | audit records (`ts` · `actor` · `action` · `target`) | `—` for optional fields |
| Filters | actor · action · range as the API supports | omit a filter the API cannot honour |

One live view (`soma-audit-dashboard`) for all aliases (`main.ts:265`, `main.ts:308`).

---

## 3. Control map

| # | Control | API / behavior | Live? |
|---|---|---|---|
| 1 | Search / filters | Query the audit API (actor · action · range). | live |
| 2 | Summary tiles | API counts only. | live |
| 3 | Event log pane | UI-S-44 rows — same screen. | live |
| 4 | inspect | Opens the event-detail drawer (UI-M-01). | live |
| 5 | Refresh | Re-fetch the list. | live |

---

## 4. Numbered journey — investigate an audit event

| Step | Where | Action | API | Result |
|---|---|---|---|---|
| **1** | `/platform/audit` | Screen loads | audit API | Summary tiles + event log paint. |
| **2** | dashboard | Filter by `actor` / `action` | audit API | Log narrows. |
| **3** | log (UI-S-44) | Click **inspect** on a row | — | Event-detail drawer (UI-M-01). |
| **4** | dashboard | Click **Refresh** | audit API | Values repainted. |
| **5** | any alias | `/soma/audit` · `/audit` · `/admin/audit` | same view | Same screen (DUP-4) — not a second destination. |

---

## 5. States

| State | Verbatim / behavior |
|---|---|
| loading | Skeleton rows + `loading` chip. No counts while loading. |
| empty | “No audit events yet. Events will appear here as the platform is used.” |
| empty (filter) | “No events match this filter. Clear the filter to see all.” |
| error | “Couldn’t load the audit log. ‹ reason from API ›” |
| permission-denied | “You don’t have access to the audit log. Requires the platform-admin role.” |
| offline | “You’re offline. The log may be stale.” |

---

## 6. Honesty

Tiles are API counts only (`—` when absent). Event fields come from the record. No invented
actors, actions or totals. UI-S-43 + UI-S-44 are one surface (DUP-4).

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/main.ts:265` | `/platform/audit` · `/soma/audit` → `soma-audit-dashboard` |
| `webui/src/main.ts:308` | `/audit` · `/admin/audit` → same view |
| `webui/src/views/soma-audit-dashboard.ts` | Live view |
| `SOMA-UI-NAV-AUDIT-001.md` §3 DUP-4 | One surface; 43 = chrome, 44 = log pane |

End of Document
