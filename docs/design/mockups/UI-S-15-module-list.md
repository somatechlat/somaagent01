# UI-S-15 — Tools list (runtime)

Screen UI-S-15 · Subview of **`/admin/agents`** (`main.ts:258` → `soma-agents-view`)
Chrome: **UI-S-00 thin** (abbrev) · Catalog: `SOMA-UI-CATALOG-001.md` §3 Tools
Live: `GET /api/v2/tools` → `ToolInfo[]`

**Status: LIVE.** This screen lists the agent’s **enabled runtime tools** — `ToolInfo` fields only:
`name` · `description` · `parameters` (`admin/tools/api/tools.py:25-30`).

The admin registry (enable / category) is **UI-S-17** (`GET/PUT /tools/catalog`). Agent-owner
enable + limits is **Settings › Tools** (UI-S-55). One catalog store (`admin.core.models.Capability`),
three audiences — no duplicate inventories.

---

## 1. ASCII wireframe — runtime tool list

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  TOOLS — enabled for this agent                                            [⟳ Refresh]          │
│  [Search tools…                     ]                                                              │
│                                                                                                  │
│  ┌─ TOOL LIST (server order) ────────────────────────────────────────────────────────────────┐  │
│  │ name              description                                          parameters         │  │
│  │ ‹name›            ‹description | —›                                    ‹present | —›      │  │
│  │ ‹name›            ‹description | —›                                    ‹present | —›      │  │
│  │ (scroll)                                                                                   │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  total: ‹n | —› enabled tools                                                    [Open]         │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

No install/uninstall, no `module.ver`, no `module.state`, no dependency or health panels — those
are not `ToolInfo` fields. No chrome IQ/AUTO/BUDGET knobs, no facet tabs (`UI-S-00` §3).

---

## 2. Real data — `ToolInfo` / `ToolCatalogItem`

| Screen | Endpoint | Schema | Fields |
|---|---|---|---|
| **UI-S-15 (this)** | `GET /api/v2/tools` | `ToolInfo` | `name` · `description` · `parameters` |
| UI-S-16 detail | `GET /api/v2/tools` | `ToolInfo` | same |
| UI-S-17 registry | `GET /tools/catalog` | `ToolCatalogItem` | `name` · `description` · `category` · `enabled` |
| UI-S-18 detail | `PUT /tools/catalog/{name}` | `ToolCatalogItem` | same (write) |

Canonical store: `admin.core.models.Capability` (`is_enabled`, `category`, `schema`).

| UI column | API field | Absent handling |
|---|---|---|
| Name | `name` | required |
| Description | `description` | `—` |
| Parameters | `parameters` (schema dict) | `—` (“no schema”) |

`GET /api/v2/tools` returns **enabled** tools only (`Capability.objects.filter(is_enabled=True)`).
The enable switch lives in UI-S-17/UI-S-18/UI-S-55 — not here.

---

## 3. Control map

| # | Control | API / behavior | Live? |
|---|---|---|---|
| 1 | Search | Client filter over loaded rows. | live |
| 2 | Tool row | `name` · `description` · `parameters` presence. | live |
| 3 | Open | `router →` UI-S-16 for that tool. | live |
| 4 | Refresh | `GET /api/v2/tools` again. | live |
| 5 | Total | `—` until the server reports. | live |

---

## 4. Numbered journey — inspect a runtime tool

| Step | Where | Action | API | Result |
|---|---|---|---|---|
| **1** | `/admin/agents` | Open Tools | `GET /api/v2/tools` | List of enabled `ToolInfo` rows. |
| **2** | list | Search `name` | client filter | Table narrows. |
| **3** | list | Click **Open** on a row | `router →` UI-S-16 | Tool detail with `parameters` schema. |
| **4** | list | Need to enable/disable | — | Goes to UI-S-17 registry or Settings › Tools (UI-S-55). Not on this screen. |

---

## 5. States

| State | Verbatim / behavior |
|---|---|
| loading | “Loading tools…” — skeleton rows. |
| empty | “No tools are enabled for this agent.” |
| empty (filter) | “No tools match this filter. Clear the filter to see all.” |
| error | “Tools could not be loaded. Retry, or check that the tools service is reachable.” |
| offline | “Tool data is unavailable offline.” |

---

## 6. Honesty

Rows are `ToolInfo` fields only. No install counts, no catalogue sizes, no invented versions or
states. `parameters` is a schema dict — presence is shown, not fabricated content.

---

## 7. Source map

| Source | Role |
|---|---|
| `GET /api/v2/tools` | `ToolInfo[]` (`tools.py:51-68`) |
| `admin/tools/api/tools.py:25-30` | `ToolInfo` schema |
| `SOMA-UI-CATALOG-001.md` §3 | Real tool fields |

End of Document
