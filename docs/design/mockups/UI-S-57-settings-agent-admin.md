# UI-S-57-settings-agent-admin — Settings — Agent admin (tools & permissions)

**Settings — Agent admin** — full administration of what the agent may do — route `/settings` (Agent admin tab) or `/settings/agent-admin`.
Audience: sysadmin / org_admin / agent_owner. Chrome abbreviated (UI-S-00).
Complements UI-S-55 (global catalog enable) and UI-X-06 (capsule editor). This screen is the **Hands / permissions** operator surface (PARITY-002 C-5).

**Field truth.** Catalog: `GET /api/v2/tools/catalog`. Capsule `tool_policy` three buckets and `enabled_capabilities` from capsule body. IQ floor: AgentIQ `tool_approval` / `require_hitl` / `egress_allowed` (tighten only). Live preview uses the same decision function as chat (`decide_and_authorize_tool`) via a preview endpoint or dry-run — never a second policy engine. Roles: read from RBAC catalog; full matrix link to `/platform/roles`.

**Design direction.** Dense scannable admin; three-bucket policy as equal columns; Material icons only; unlisted tools = approval is **locked default** (not editable to auto).

## Purpose

Administer per-capsule tool enablement, three-bucket tool_policy, capabilities scope, IQ autonomy floor, and role×resource visibility so every tool action is granular and auditable.

```
┌─ UI-S-00 chrome (abbrev) ─────────────────────────────────────────────────────────────────────────┐
│ ☰ SOMA    Settings · Agent admin                   [Search…]                   [Save] [Cancel]   │
├──────────────┬───────────────────────────────────────────────────────────────────────────────────┤
│ SECTION NAV  │  AGENT ADMIN — tools & permissions                                               │
│  Agent       │  Capsule [‹name› ▾]     Role floor: ‹role› · tool_execute ✓/✗                    │
│  Models      │                                                                                   │
│  Voice       │  ── CATALOG (global) ──────────────────────────────────────────────────────────    │
│  Interface   │  search [____]  category [all ▾]                                                 │
│  Tools       │  │ tool          │ category │ tier │ enabled │ policy (per capsule)             │  │
│  Integrations│  │ file_read     │ file     │ 1    │ ●       │ auto                             │  │
│  SomaBrain   │  │ file_write    │ file     │ 2    │ ●       │ approval                         │  │
│  **Agent admin●**│ shell_exec   │ os       │ 3    │ ○       │ denied                           │  │
│  Connectivity│  Unlisted tools = approval (default — locked)                                   │
│  Advanced    │                                                                                   │
│              │  ── TOOL_POLICY (capsule) — three buckets ────────────────────────────────────    │
│              │  AUTO-EXECUTE              APPROVAL REQUIRED           DENIED                    │
│              │  ┌────────────────┐    ┌────────────────┐   ┌────────────┐                      │
│              │  │ timestamp      │    │ file_write     │   │ shell_exec │                      │
│              │  │ file_list      │    │ research_report│   │ (opt-in)   │                      │
│              │  │ file_read      │    │ code_execute   │   └────────────┘                      │
│              │  │ memory_*       │    │ http_fetch     │                                       │
│              │  └────────────────┘    └────────────────┘                                       │
│              │  [ Save tool_policy ]                                                           │
│              │                                                                                   │
│              │  ── CAPABILITIES (enabled_capabilities) ──────────────────────────────────────    │
│              │  ☑ file_read ☑ file_write ☐ shell_exec ☑ research_report                       │
│              │  [ Save capabilities ]   (UnifiedGate scope)                                     │
│              │                                                                                   │
│              │  ── IQ FLOOR (tighten only) ──────────────────────────────────────────────────    │
│              │  tool_approval ( none | dangerous | all )   require_hitl [ ]   egress [none▾]    │
│              │  [ Save IQ ]                                                                     │
│              │                                                                                   │
│              │  ── LIVE PREVIEW (same choke as chat) ────────────────────────────────────────    │
│              │  file_write → approval_required   why: capsule + IQ                              │
│              │  shell_exec → denied               why: capsule denied                           │
│              │  [ Refresh ]                                                                     │
│              │                                                                                   │
│              │  ── ROLES (read) ──────────────────────────────────────────────────────────────    │
│              │  resource:tool_execute ✓   [ Open full role matrix ]                             │
├──────────────┴───────────────────────────────────────────────────────────────────────────────────┤
│ status: ‹load/save› · permission: tool_configure / settings:edit · fail-closed on error         │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Field table (API field)

| Human label | Control | API field |
|---|---|---|
| Capsule | select | current capsule id |
| Tool enabled | toggle | catalog `enabled` |
| Policy bucket | select/drag | `tool_policy.auto_execute|approval_required|denied` |
| Capability | checkbox | capsule capabilities M2M |
| tool_approval | select | IQ |
| require_hitl | toggle | IQ |
| egress_allowed | select | IQ |
| Live preview decision | table | choke dry-run |

## Control map

| # | control | notes |
|---|---|---|
| 1 | capsule select | scopes all edits |
| 2 | catalog table | live `/tools/catalog` |
| 3 | three buckets | save `tool_policy` |
| 4 | capabilities | save M2M / enabled list |
| 5 | IQ floor | tighten only |
| 6 | live preview | same `decide_and_authorize_tool` |
| 7 | role read + link | no wildcard grants in UI |

## States

- **Loading.** Skeleton buckets; no fake tool names.
- **Empty catalog.** "No tools in the catalog yet."
- **Error.** "Couldn't load agent admin. ‹reason›"
- **Permission-denied.** "Requires tool_configure."
- **Preview fail-closed.** "Decision unavailable — denied until policy resolves."

**Modals.** Save confirmation dialog if policy denies all tools.

## Sync note

UI-S-055 remains global catalog enable. This screen is per-capsule policy + permissions. Both stay; Agent admin is the full Hands surface.
