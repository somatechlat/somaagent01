# UI-S-55-settings-tools — Settings — Tools

**Settings — Tools** — section **Tools** inside the one Settings shell — route `/settings` (Tools tab).
Chrome abbreviated (UI-S-00). Left section nav (7) is visible; Tools is active.

**Field truth.** Tool cards come from the live catalog only:
`GET /api/v2/tools` → `ToolsListResponse` `{tools[ToolInfo], count}` and `GET /api/v2/tools/catalog` → `ToolCatalogItem[]` (`admin/tools/api/tools.py` 25–90).
`ToolInfo`: `name` · `description` · `parameters`. `ToolCatalogItem`: `name` · `description` · `category` · `enabled`.
Enable write: `PUT /api/v2/tools/catalog/{name}` with `ToolCatalogItem` (`tools.py:93-111`).
Shared limits: `tool_exec_timeout_s` · `tool_result_max_chars` · `tool_max_iterations` on settings entity `agent` (`admin/core/api/settings_v2.py:203-217`).
No tool is listed that the API did not return. Card labels in Screen 7E (web, code, files, browser, documents, voice, git, email) are UI examples — the grid is always live catalog rows.

**Language law.** Binding copy is **Used for: Chat / Help / Memory**. The banned admin noun never appears in UI strings.
**Memory rule.** Memory is not a Settings section. Its only home is `/memory` (UI-S-04, left rail).

## Purpose

Enable or disable each real tool card and set the three shared execution limits. Cards are catalog-driven; limits are one agent settings write.

```
┌─ UI-S-00 chrome (abbrev) ────────────────────────────────────────────────────────────────────────┐
│ ☰ SOMA    Settings · Tools     [Search settings…]                            [Save] [Cancel]     │
├──────────────┬───────────────────────────────────────────────────────────────────────────────────┤
│ SECTION NAV  │  TOOLS — what the agent may run                                      [Refresh]   │
│  Agent       │  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐     │
│  Models      │  │ ‹tool.name›      [●] │  │ ‹tool.name›      [●] │  │ ‹tool.name›      [○] │     │
│  Voice       │  │ ‹tool.description›   │  │ ‹tool.description›   │  │ ‹tool.description›   │     │
│  Interface   │  │ category ‹category›  │  │ category ‹category›  │  │ category ‹category›  │     │
│  Tools    ●  │  │ [schema ▸]           │  │ [schema ▸]           │  │ [schema ▸]           │     │
│  Integrations│  └──────────────────────┘  └──────────────────────┘  └──────────────────────┘     │
│  Advanced    │  (rows = GET /api/v2/tools/catalog · live names only · Screen 7E card shape)       │
│              │                                                                                   │
│              │  EXECUTION LIMITS (settings entity: agent)                                        │
│              │  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│              │  │ Timeout (seconds)     [30        ]  ← tool_exec_timeout_s                   │   │
│              │  │ Max result size       [‹chars›   ]  ← tool_result_max_chars                 │   │
│              │  │ Max tool iterations   [‹n›       ]  ← tool_max_iterations                   │   │
│              │  └─────────────────────────────────────────────────────────────────────────────┘   │
├──────────────┴───────────────────────────────────────────────────────────────────────────────────┤
│ status: <load / save state> · source: live catalog · <n> tools · permission: settings:edit       │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Field table (API field)

| Human label | Control | API field | Notes | Evidence |
|---|---|---|---|---|
| Tool name | text (card) | `name` | From catalog / `ToolInfo.name` | `tools.py:28`, `35` |
| Description | text (card) | `description` | one line | `tools.py:29`, `36` |
| Category | chip (card) | `category` | `ToolCatalogItem` only | `tools.py:37`, `87` |
| Enable | toggle | `enabled` | `PUT /api/v2/tools/catalog/{name}` body | `tools.py:39`, `93-111` |
| Schema | expand | `parameters` | `ToolInfo.parameters` dict | `tools.py:30`, `67` |
| Timeout (seconds) | number | `tool_exec_timeout_s` | settings entity `agent`, key setting `TOOL_EXEC_TIMEOUT_S` | `settings_v2.py:208-212` |
| Max result size | number | `tool_result_max_chars` | `TOOL_RESULT_MAX_CHARS` | `settings_v2.py:213-217` |
| Max tool iterations | number | `tool_max_iterations` | `TOOL_MAX_ITERATIONS` | `settings_v2.py:203-207` |

No invented per-tool timeout/size columns exist in `ToolCatalogItem` — the three limits are the shared `agent` settings.

## Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-100 | section nav (7) | Agent · Models · Voice · Interface · Tools · Integrations · Advanced. |
| 2 | UI-C-097 | tool enable card | One card per live catalog row. `name` / `description` / `category` / `enabled` from API. |
| 3 | UI-C-065 | enable toggle | Writes `PUT /api/v2/tools/catalog/{name}`. disabled-when: `tool_configure` absent — disabled-reason: "Requires tool configure permission." |
| 4 | UI-C-071 | schema expand | Local expand over live `parameters`. No schema is drawn that the API did not return. |
| 5 | UI-C-063 | execution-limit numbers | Bind the three `agent` settings keys only. |
| 6 | UI-C-067 | Save (primary, header) | Saves dirty limit fields via `PUT /api/v2/core/settings/agent`. disabled-while: request in flight. |
| 7 | UI-C-068 | Refresh | Re-calls `GET /api/v2/tools/catalog` + `GET /api/v2/tools`. |
| 8 | — | permission banner | `settings:edit` / `system:configure` absent → read-only, Save disabled-reason: "Requires settings edit permission." |

## States

- **Loading.** Skeleton cards. No counts while loading.
- **Empty.** "No tools in the catalog yet."
- **Error.** "Couldn't load tools. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to tools. Requires `tool_read` / `tool_configure`."
- **Offline.** "You're offline. Changes will not be saved until the connection returns."

**Modal overlays.** None destructive here. Per-card schema is an inline expand, not a modal.

## Nav

Settings shell section nav = Agent · Models · Voice · Interface · **Tools** · Integrations · Advanced (UI-S-50). No Memory item.
Canvas Tools surface (UI-X-02) stays the run log; this section is the enable + limits config home.

## Test clicks

| Click | Expect |
|---|---|
| Open Tools tab | `GET /api/v2/tools/catalog` + `GET /api/v2/tools` 200; cards match `count` |
| Toggle Enable on a card | `PUT /api/v2/tools/catalog/{name}` 200 with `enabled` flipped |
| Expand schema | Shows live `parameters` JSON; no placeholder schema |
| Set Timeout → Save | `PUT /api/v2/core/settings/agent` `{tool_exec_timeout_s:…}` 200 |
| Set Max result size → Save | `PUT` `{tool_result_max_chars:…}` 200 |
| Toggle without `tool_configure` | Toggle disabled + reason; no write |
| Refresh | Catalog re-fetched; no invented rows |

## file:line evidence

| Evidence | Path |
|---|---|
| `ToolInfo` · `ToolCatalogItem` · `ToolsListResponse` | `somaAgent01/admin/tools/api/tools.py:25-46` |
| List tools / catalog / upsert | `somaAgent01/admin/tools/api/tools.py:49-111` |
| `tool_max_iterations` · `tool_exec_timeout_s` · `tool_result_max_chars` | `somaAgent01/admin/core/api/settings_v2.py:203-217` |
| Settings GET/PUT paths | `somaAgent01/webui/src/components/settings-form.ts:8-9`, `330`, `344` |
| Router mounts `/tools`, `/core`→`/settings` | `somaAgent01/admin/api.py:141`; `admin/core/api/__init__.py:31` |
| Canvas tools bindings | `somaAgent01/docs/design/mockups/UI-X-02-tools.md:45`, `100-102` |
| Screen 7E | `somabrain/docs/project/SOMA-UI-MOCKUPS-001.md:611-615` |
| Nav shell | `somaAgent01/docs/design/mockups/UI-S-50-settings-agent.md:41-53` |
