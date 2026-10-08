# UI-S-16 — Tool detail

Screen UI-S-16 · Subview of **`/admin/agents`** (from UI-S-15) · Chrome: **UI-S-00 thin** (abbrev)
Catalog: `SOMA-UI-CATALOG-001.md` §3 Tools · Live: `GET /api/v2/tools` → `ToolInfo`

**Status: LIVE.** Read-only detail of one runtime tool — **`ToolInfo` fields only**:
`name` · `description` · `parameters` (`admin/tools/api/tools.py:25-30`).

No config form, no dependencies, no health readout, no uninstall — those are not `ToolInfo` fields.
Enabling/disabling is UI-S-17/UI-S-18 (`GET/PUT /tools/catalog`) and Settings › Tools (UI-S-55).

---

## 1. ASCII wireframe — tool detail

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  TOOL   ‹name›                                                     ← Back to tools list         │
│                                                                                                  │
│  ┌─ ABOUT ───────────────────────────────────────────────────────────────────────────────────┐  │
│  │  name         ‹name›                                                                       │  │
│  │  description  ‹description | —›                                                            │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  ┌─ PARAMETERS (schema dict) ────────────────────────────────────────────────────────────────┐  │
│  │  ┌──────────────────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ ‹parameters›  (JSON schema as the server sent it)                                   │  │  │
│  │  │ or “No schema” when parameters is null/absent                                        │  │  │
│  │  └──────────────────────────────────────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Real data — `ToolInfo`

| UI block | API field | Type | Absent handling |
|---|---|---|---|
| Name | `name` | `str` | required |
| Description | `description` | `Optional[str]` | `—` |
| Parameters | `parameters` | `Optional[dict]` | “No schema” |

Endpoint: `GET /api/v2/tools` (filter to `name`). Source query
`Capability.objects.filter(is_enabled=True).values("name", "description", "schema")` — `schema`
is returned as `parameters`.

---

## 3. Control map

| # | Control | API / behavior | Live? |
|---|---|---|---|
| 1 | About panel | Read-only `name` · `description`. | live |
| 2 | Parameters panel | Renders the `parameters` schema dict verbatim. | live |
| 3 | Back to tools list | `router →` UI-S-15. | live |
| — | Enable/Disable | **Not here** — UI-S-18 / UI-S-55. | — |

---

## 4. Numbered journey — read a tool’s schema

| Step | Where | Action | API | Result |
|---|---|---|---|---|
| **1** | UI-S-15 | Click **Open** on a row | `router →` UI-S-16 | Detail loads. |
| **2** | detail | Read `description` | from `ToolInfo` | `—` if the server omitted it. |
| **3** | detail | Read `parameters` | from `ToolInfo` | Schema dict, or “No schema”. |
| **4** | detail | Need enable/category edit | — | UI-S-18 or Settings › Tools (UI-S-55). |
| **5** | detail | Back | `router →` UI-S-15 | List. |

---

## 5. States

| State | Verbatim / behavior |
|---|---|
| loading | “Loading tool…” — skeleton blocks. |
| not found | “Tool could not be loaded. It may have been disabled or removed.” |
| no schema | Parameters panel: “No schema”. |
| offline | “Tool data is unavailable offline.” |

---

## 6. Honesty

Only `ToolInfo` fields render. No config keys, no dependency chips, no health metric, no masked
secrets — those fields do not exist on `ToolInfo`. `parameters` is shown as the server sent it.

---

## 7. Source map

| Source | Role |
|---|---|
| `GET /api/v2/tools` | `ToolInfo[]` (`tools.py:51-68`) |
| `admin/tools/api/tools.py:25-30` | `ToolInfo` schema |
| `SOMA-UI-CATALOG-001.md` §3 | Real tool fields |

End of Document
