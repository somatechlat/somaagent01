# UI-S-44 — Audit log (pane)

Screen UI-S-44 · Same routes as UI-S-43: **`/platform/audit`** · **`/soma/audit`** · **`/audit`** ·
**`/admin/audit`** (`main.ts:265`, `main.ts:308` → `soma-audit-dashboard`)
Chrome: **UI-S-00 thin** (abbrev) · Catalog: `SOMA-UI-CATALOG-001.md` §2 Platform
Live view: `webui/src/views/soma-audit-dashboard.ts` (`soma-audit-dashboard`)

**Status: LIVE — as a pane, not a destination.** The event log is the **log pane** of the same
audit screen (UI-S-43 is the dashboard chrome). One live view serves every alias (DUP-4).
Do not present this as a second nav target.

---

## 1. ASCII wireframe — event log (pane of UI-S-43)

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  AUDIT                                                                     [⟳ Refresh]          │
│  [Search events…                     ]  actor [all ▾]   action [all ▾]   range [▾]              │
│                                                                                                  │
│  ┌─ EVENT LOG (this pane) ───────────────────────────────────────────────────────────────────┐  │
│  │  ts                  actor              action              target            [inspect]   │  │
│  │  ─────────────────   ──────────────     ──────────────      ──────────────                 │  │
│  │  ‹ts›                ‹actor›            ‹action›            ‹target | —›                  │  │
│  │  ‹ts›                ‹actor›            ‹action›            ‹target | —›                  │  │
│  │  ‹ts›                ‹actor›            ‹action›            ‹target | —›                  │  │
│  │  (scroll)                                                                                   │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  total: ‹n | —› events                                                           [Export]       │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

Inspect opens the event-detail drawer (UI-M-01) over the same screen.

---

## 2. Real data

| UI column | Source | Absent handling |
|---|---|---|
| ts | audit record | `—` |
| actor | audit record | `—` |
| action | audit record | `—` |
| target | audit record | `—` |
| total | list response | `—` (never `0` on failure) |

Same `soma-audit-dashboard` view as UI-S-43 — no second endpoint, no second store.

---

## 3. Control map

| # | Control | API / behavior | Live? |
|---|---|---|---|
| 1 | Search / filters | Query the audit API (actor · action · range). | live |
| 2 | Event rows | `ts` · `actor` · `action` · `target`. | live |
| 3 | inspect | UI-M-01 drawer with the full event record. | live |
| 4 | Export | Client download of the loaded rows. | live |
| 5 | Refresh | Re-fetch the list. | live |
| 6 | Total | `—` until the server reports. | live |

---

## 4. Numbered journey — read and inspect events

| Step | Where | Action | API | Result |
|---|---|---|---|---|
| **1** | `/platform/audit` | Screen loads | audit API | Log rows paint. |
| **2** | log | Filter by `action` | audit API | Rows narrow. |
| **3** | log | Click **inspect** on a row | — | UI-M-01 drawer with the full record. |
| **4** | log | **Export** | client download | JSON of loaded rows. |
| **5** | log | **Refresh** | audit API | Server truth repainted. |

---

## 5. States

| State | Verbatim / behavior |
|---|---|
| loading | “Loading events…” — skeleton rows. |
| empty | “No audit events yet.” |
| empty (filter) | “No events match this filter. Clear the filter to see all.” |
| error | “Couldn’t load the audit log. ‹ reason from API ›” |
| permission-denied | Read-only; “You don’t have access to the audit log. Requires the platform-admin role.” |
| offline | “You’re offline. The log may be stale.” |

---

## 6. Honesty

Event fields come from the record. No invented actors, actions, or totals. This pane never appears
as its own nav entry (DUP-4).

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/main.ts:265` · `308` | All four aliases → `soma-audit-dashboard` |
| `webui/src/views/soma-audit-dashboard.ts` | Live view (chrome + log pane) |
| `SOMA-UI-NAV-AUDIT-001.md` §3 DUP-4 | UI-S-43 + UI-S-44 are one screen |

End of Document
