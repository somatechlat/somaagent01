# UI-S-41 — Integrations dashboard

Screen UI-S-41 · Routes: **`/platform/integrations`** · **`/soma/settings/integrations`**
(`main.ts:156` → `soma-integrations-dashboard`)
Chrome: **UI-S-00 thin** (abbrev) · Catalog: `SOMA-UI-CATALOG-001.md` §2 Platform
Live view: `webui/src/views/soma-integrations-dashboard.ts` (`soma-integrations-dashboard`)

**Status: LIVE.** **Platform integrations catalogue** (audience: platform admin).

Distinct from (DUP-3):
- **UI-S-52** Settings · Integrations — agent-owner provider keys + channels (`/settings/channels`).
- **UI-S-53** Settings · Advanced / External & Developer — platform API keys (`/platform/api-keys`).

Names must stay distinct in nav. This screen does **not** hold agent-owner Vault keys.

---

## 1. ASCII wireframe — platform integrations workspace

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  PLATFORM INTEGRATIONS                                                   [⟳ Refresh]            │
│  [Search integrations…                  ]  status [all ▾]                                        │
│                                                                                                  │
│  ┌─ INTEGRATION CATALOGUE (server order) ────────────────────────────────────────────────────┐  │
│  │  name                  category             status                  [⋯]                    │  │
│  │  ‹name›                ‹category | —›       ‹status | —›                                  │  │
│  │  ‹name›                ‹category | —›       ‹status | —›                                  │  │
│  │  (scroll)                                                                                   │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  total: ‹n | —› integrations                                                     [Open]          │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Real data

| UI field | Source | Absent handling |
|---|---|---|
| name | integration record | required |
| category | record | `—` |
| status | record | `—` |
| total | list response | `—` (never `0` on failure) |

No secret material is shown here. Provider keys live in UI-S-52 (Vault-backed, write-only).

---

## 3. Control map

| # | Control | API / behavior | Live? |
|---|---|---|---|
| 1 | Search | Client filter over loaded rows. | live |
| 2 | Status filter | Filter on `status` as stored. | live |
| 3 | Integration row | `name` · `category` · `status`. | live |
| 4 | Open | Detail of that integration (same view). | live |
| 5 | Refresh | Re-fetch the list. | live |
| 6 | Total | `—` until the server reports. | live |

---

## 4. Numbered journey — browse platform integrations

| Step | Where | Action | API | Result |
|---|---|---|---|---|
| **1** | `/platform/integrations` | Screen loads | integrations API | Catalogue rows paint. |
| **2** | catalogue | Search / filter `status` | client filter | Table narrows. |
| **3** | catalogue | Click **Open** | same view | Detail of that integration. |
| **4** | catalogue | Need **agent-owner** keys/channels | — | UI-S-52 (`/settings/channels`). Not here. |
| **5** | catalogue | Need **API keys** | — | UI-S-53 (`/platform/api-keys`). Not here. |

---

## 5. States

| State | Verbatim / behavior |
|---|---|
| loading | “Loading integrations…” — skeleton rows. |
| empty | “No platform integrations configured.” |
| empty (filter) | “No integrations match this filter. Clear the filter to see all.” |
| error | “Couldn’t load platform integrations. ‹ reason from API ›” |
| permission-denied | “You don’t have access to platform integrations. Requires the platform-admin role.” |
| offline | “You’re offline. Integration data may be stale.” |

---

## 6. Honesty

Rows are catalogue fields only. No secret values, no invented status enums, no fabricated counts.
The three integrations surfaces (UI-S-41 / UI-S-52 / UI-S-53) stay audience-distinct (DUP-3).

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/main.ts:156` | `/platform/integrations` · `/soma/settings/integrations` → `soma-integrations-dashboard` |
| `webui/src/views/soma-integrations-dashboard.ts` | Live view |
| `SOMA-UI-NAV-AUDIT-001.md` §3 DUP-3 | Split by audience: 41 / 52 / 53 |

End of Document
