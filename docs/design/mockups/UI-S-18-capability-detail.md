# UI-S-18 — Capability detail

Screen UI-S-18 · Subview of **`/admin/agents`** (from UI-S-17) · Chrome: **UI-S-00 thin** (abbrev)
Catalog: `SOMA-UI-CATALOG-001.md` §3 Tools · Live: `GET /tools/catalog` · `PUT /tools/catalog/{name}`

**Status: LIVE.** Detail + edit of one catalog entry — **`ToolCatalogItem` fields only**:
`name` · `description` · `category` · `enabled` (`admin/tools/api/tools.py:33-39`).

No hook bindings, no trigger/policy selects, no derived `require_hitl` / `tool_approval` readouts —
those are not `ToolCatalogItem` fields and no such endpoint exists.

---

## 1. ASCII wireframe — capability detail

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  CAPABILITY   ‹name›                                          [Save]  ← Back to registry        │
│                                                                                                  │
│  ┌─ CATALOG ENTRY (ToolCatalogItem) ─────────────────────────────────────────────────────────┐  │
│  │  name          ‹name›  (read-only — the path key)                                          │  │
│  │  description   [‹description | ›                          ]   ← description               │  │
│  │  category      [‹category | ›                             ]   ← category                  │  │
│  │  enabled       [● on / ○ off]                                    ← enabled                  │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  ┌─ SCHEMA (read-only, from the capability store) ───────────────────────────────────────────┐  │
│  │  ‹schema›  — only if the store returns it; otherwise “No schema”                          │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Real data — `ToolCatalogItem`

| UI field | API field | Type | Editable |
|---|---|---|---|
| Name | `name` | `str` | read-only (path key of `PUT /tools/catalog/{name}`) |
| Description | `description` | `Optional[str]` | write |
| Category | `category` | `Optional[str]` | write |
| Enabled | `enabled` | `bool` (default true) | write |
| Schema | `schema` (store) | `dict` | read-only |

| Action | Endpoint | Payload |
|---|---|---|
| Read list | `GET /tools/catalog` | — → `ToolCatalogItem[]` (filter to `name`) |
| Save | `PUT /tools/catalog/{name}` | `ToolCatalogItem` `{name, description, category, enabled}` |

The PUT is an **upsert** into `admin.core.models.Capability` (`description`, `category`,
`is_enabled`). It returns the stored row.

---

## 3. Control map

| # | Control | API / behavior | Live? |
|---|---|---|---|
| 1 | Name | Read-only (the `{name}` path key). | live |
| 2 | Description | Text input → `description`. | live |
| 3 | Category | Text/select → `category`. | live |
| 4 | Enabled | Toggle → `enabled`. | live |
| 5 | Schema panel | Read-only `schema` from the store. | live |
| 6 | Save | `PUT /tools/catalog/{name}` with the typed `ToolCatalogItem`. Disabled until dirty. | live |
| 7 | Back to registry | `router →` UI-S-17. | live |

---

## 4. Numbered journey — edit a capability

| Step | Where | Action | API | Result |
|---|---|---|---|---|
| **1** | UI-S-17 | Click **Open** on a row | `router →` UI-S-18 | Detail loads that entry. |
| **2** | detail | Read `description` · `category` · `enabled` | from `GET /tools/catalog` | Real values; `—` when absent. |
| **3** | detail | Change `category` / flip `enabled` | — | Dirty → **Save** enabled. |
| **4** | detail | Click **Save** | `PUT /tools/catalog/{name}` | Stored; dirty cleared. |
| **5** | detail | Back | `router →` UI-S-17 | Registry reflects the new `enabled`. |
| **6** | detail | Need runtime-only schema list | — | UI-S-15 (`GET /api/v2/tools`). Not here. |

---

## 5. States

| State | Verbatim / behavior |
|---|---|
| loading | “Loading capability…” — skeleton fields. |
| not found | “Capability could not be loaded. It may have been removed.” |
| no schema | Schema panel: “No schema”. |
| dirty | **Save** enabled. |
| saving | Button “Saving…”; inputs stay as typed. |
| save fail | “Could not update this capability. Nothing was changed.” |
| offline | Save disabled: “Capability actions are unavailable offline.” |

---

## 6. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| — | — | No destructive action on this screen (disabling is reversible). |

---

## 7. Honesty

Only `ToolCatalogItem` fields render. No hook bindings, no trigger/policy rows, no derived HITL
or tool-approval readouts. `schema` is shown only when the store returns it.

---

## 8. Source map

| Source | Role |
|---|---|
| `GET /tools/catalog` | `ToolCatalogItem[]` (`tools.py:74-91`) |
| `PUT /tools/catalog/{name}` | Upsert (`tools.py:93-110`) |
| `admin/tools/api/tools.py:33-39` | `ToolCatalogItem` schema |
| `admin.core.models.Capability` | Canonical store (`is_enabled`, `category`, `schema`) |
| `SOMA-UI-CATALOG-001.md` §3 | Real tool fields |

End of Document
