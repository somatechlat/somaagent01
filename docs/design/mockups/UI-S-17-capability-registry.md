# UI-S-17 — Capability registry (tools catalog)

Screen UI-S-17 · Subview of **`/admin/agents`** (`main.ts:258` → `soma-agents-view`)
Chrome: **UI-S-00 thin** (abbrev) · Catalog: `SOMA-UI-CATALOG-001.md` §3 Tools
Live: `GET /tools/catalog` → `ToolCatalogItem[]`

**Status: LIVE.** The **catalog registry** of every capability — `ToolCatalogItem` fields only:
`name` · `description` · `category` · `enabled` (`admin/tools/api/tools.py:33-39`).

One canonical store: `admin.core.models.Capability` (`is_enabled`, `category`, `schema`).
Same store powers UI-S-15/16 (runtime `ToolInfo`) and Settings › Tools (UI-S-55) — this screen is
the full registry with category + enable; it is **not** a second inventory.

---

## 1. ASCII wireframe — capability registry

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  CAPABILITIES — tools catalog                                                [⟳ Refresh]        │
│  [Search capabilities…              ]  category [all ▾]                                          │
│                                                                                                  │
│  ┌─ CATALOG TABLE (server order) ────────────────────────────────────────────────────────────┐  │
│  │ name               description                    category        enabled                 │  │
│  │ ‹name›             ‹description | —›              ‹category | —›  [● on / ○ off]           │  │
│  │ ‹name›             ‹description | —›              ‹category | —›  [● on / ○ off]           │  │
│  │ (scroll)                                                                                   │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  total: ‹n | —› capabilities                                                 [Open]             │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

No “Register capability” button, no registry-source line, no last-scan timestamp — none of those
are `ToolCatalogItem` fields and no such endpoint exists.

---

## 2. Real data — `ToolCatalogItem`

| UI column | API field | Type | Absent handling |
|---|---|---|---|
| Name | `name` | `str` | required |
| Description | `description` | `Optional[str]` | `—` |
| Category | `category` | `Optional[str]` | `—` |
| Enabled | `enabled` | `bool` (default true) | toggle state |

| Action | Endpoint | Payload |
|---|---|---|
| List | `GET /tools/catalog` | — → `ToolCatalogItem[]` (from `Capability.objects.all()`) |
| Enable/Disable | `PUT /tools/catalog/{name}` | `ToolCatalogItem` (`enabled`, `category`, `description`) |

Note the path shape: `GET /tools/catalog` · `PUT /tools/catalog/{name}` (the catalog router, not
`/api/v2/tools` — that one is the runtime `ToolInfo` list, UI-S-15).

---

## 3. Control map

| # | Control | API / behavior | Live? |
|---|---|---|---|
| 1 | Search | Client filter over loaded rows. | live |
| 2 | Category filter | Filter on `category` as stored. | live |
| 3 | Catalog row | `name` · `description` · `category` · `enabled`. | live |
| 4 | Enabled toggle | `PUT /tools/catalog/{name}` with `{name, description, category, enabled}`. | live |
| 5 | Open | `router →` UI-S-18 for that `name`. | live |
| 6 | Refresh | `GET /tools/catalog` again. | live |
| 7 | Total | `—` until the server reports. | live |

---

## 4. Numbered journey — toggle a capability

| Step | Where | Action | API | Result |
|---|---|---|---|---|
| **1** | `/admin/agents` | Open Capabilities | `GET /tools/catalog` | Registry rows with real fields. |
| **2** | registry | Filter `category` / search `name` | client filter | Table narrows. |
| **3** | registry | Flip **enabled** on a row | `PUT /tools/catalog/{name}` | Toggle reflects the saved `enabled`. |
| **4** | registry | Click **Open** | `router →` UI-S-18 | Detail/edit for that name. |
| **5** | registry | Need runtime-only view | — | UI-S-15 (`GET /api/v2/tools`). Not a second registry. |

---

## 5. States

| State | Verbatim / behavior |
|---|---|
| loading | “Loading capabilities…” — skeleton rows. |
| empty | “No capabilities registered.” |
| empty (filter) | “No capabilities match this filter. Clear the filter to see all.” |
| error | “Capability registry could not be loaded. Retry, or check that the tools service is reachable.” |
| save fail (toggle) | “Could not update this capability. Nothing was changed.” |
| offline | “Capability actions are unavailable offline.” |

---

## 6. Honesty

Rows are `ToolCatalogItem` fields only. No invented kind/provider/state columns, no registry
source, no scan timestamps, no install counts. `category` and `description` render `—` when the
server omits them.

---

## 7. Source map

| Source | Role |
|---|---|
| `GET /tools/catalog` | `ToolCatalogItem[]` (`tools.py:74-91`) |
| `PUT /tools/catalog/{name}` | Upsert enable/category/description (`tools.py:93-110`) |
| `admin/tools/api/tools.py:33-39` | `ToolCatalogItem` schema |
| `admin.core.models.Capability` | Canonical store |
| `SOMA-UI-CATALOG-001.md` §3 | Real tool fields |

End of Document
