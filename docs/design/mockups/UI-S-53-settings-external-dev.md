# UI-S-53 — Settings — Advanced (External & Developer)

**Settings — Advanced** — section **Advanced** inside the one Settings shell — live route `/platform/api-keys` (`soma-admin-api-keys`) plus the Advanced pane of `/settings`.
Chrome abbreviated (UI-S-00). Left section nav (7) is visible; Advanced is active.

**Keys law.** API keys and external credentials are Vault-backed and **write-only**. Status only (`● set` / `○ missing`). Rotate in Vault. Never echo a secret.
**Field truth.** No `ModelIn` fields on this screen. Model editing is UI-S-51 only.

```
┌─ UI-S-00 chrome (abbrev) ────────────────────────────────────────────────────────────────────────┐
│ ☰ SOMA    Settings · Advanced     [Search settings…]                          [Save] [Cancel]     │
├──────────────┬───────────────────────────────────────────────────────────────────────────────────┤
│ SECTION NAV  │  MODULES                                                                            │
│  Agent       │  | module | title | enabled | [enable/disable] |                                   │
│  Models      │  | <name> | <title> | yes/no | [toggle] |                                          │
│  Voice       │                                                                                   │
│  Interface   │  QUOTAS                                                                             │
│  Tools       │  Requests / day   [        ]   Tokens / day   [        ]                           │
│  Integrations│  Concurrent jobs  [        ]   Storage (MB)   [        ]                           │
│  Advanced ●  │                                                                                   │
│              │  EXPERIMENTAL FEATURES                                                              │
│              │  [●] feature-flag-tools          Tools surface (feature flag)                      │
│              │  [○] experimental-name           (only flags the API reports)                      │
│              │                                                                                   │
│              │  EXTERNAL SERVICES & API KEYS     (write-only · Vault · rotate in Vault)           │
│              │  | service / key name | credential | status | [edit][rotate] |                     │
│              │  | <name>             | ••••••     | ● set   | [edit][rotate] |                    │
│              │  | <name>             | —          | ○ missing | [add]        |                    │
│              │  note: credentials are write-only. Never a real value on screen.                   │
│              │                                                                                   │
│              │  DEVELOPER                                                                          │
│              │  | tool | state | reason when gated |                                             │
│              │  | API keys | available | — |                                                     │
│              │  | Feature flags | available | — |                                                │
│              │  | WebSocket event console | gated | moved to Debug surface (UI-X-05) |            │
│              │  | WebSocket tester | gated | moved to Debug surface (UI-X-05) |                   │
│              │                                                                                   │
│              │  BACKUP / RESTORE                                                                   │
│              │  [Export settings]  [Restore…]  [Reset to defaults…]                               │
├──────────────┴───────────────────────────────────────────────────────────────────────────────────┤
│ status: <load / save state> · permission: system:configure / platform-admin                      │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Field tables

**Modules / quotas / experimental / backup (Screen 7G)**

| Human label | Control |
|---|---|
| Modules | card list (enable/disable per registered module) |
| Quotas | numbers (requests/day, tokens/day, jobs, storage) |
| Experimental features | toggles — only feature flags the API reports |
| Backup / Restore | buttons (Export · Restore · Reset to defaults) |

**External services & API keys**

| Human label | Control |
|---|---|
| Service / key name | text (from API) |
| Credential | masked `••••••` when set · `—` when missing (write-only) |
| Status | chip `● set` / `○ missing` |
| edit / add | UI-M-01 drawer — write a new value, never echoes the stored secret |
| rotate | UI-M-03 confirm → Vault rotate |

**Developer tools**

| Tool | State | Note |
|---|---|---|
| API keys | available | This screen (`/platform/api-keys`) |
| Feature flags | available | API-backed flags only |
| WebSocket event console | gated | Lives in Debug surface (UI-X-05) |
| WebSocket tester | gated | Lives in Debug surface (UI-X-05) |

A gated row prints its blocking reason inline. Nothing is drawn as a working control over nothing.

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-115 | external credential row | Name + masked credential + status. Write-only. |
| 2 | UI-C-068 | edit / add (secondary) | Opens UI-M-01 write form. Never echoes the stored secret. |
| 3 | UI-C-069 | rotate (destructive) | Opens UI-M-03. disabled-when: no credential stored — disabled-reason: "No credential stored to rotate." |
| 4 | UI-C-104 | developer tool row | Real availability only. Debug-surface tools say so. |
| 5 | UI-C-073 | status chip | `● set` / `○ missing` · `available` / `gated` with inline blocking reason. |
| 6 | UI-C-067 | Save (header) | Saves module / quota / flag changes. disabled-while: request in flight. |

**State variants.**

- **Loading.** Skeleton rows. No counts while loading.
- **Empty.** "No external services configured."
- **Error.** "Couldn't load advanced settings. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to advanced settings. Requires the platform-admin role."
- **Offline.** "You're offline. Changes will not be saved until the connection returns."

**Modal overlays.** UI-M-01 Drawer — credential write form (write-only). UI-M-03 Dialog — "Rotate the stored credential for `‹ service ›`?" / "Reset all settings to defaults?" (destructive).

**Route evidence.** `webui/src/main.ts` `'/platform/api-keys'` → `soma-admin-api-keys`. Advanced pane of `'/settings'` → `soma-settings` (tab `system` → label Advanced). Feature flags from `webui/src/views/soma-settings.ts` (`FEATURE_FLAG_KEYS`, e.g. `toolsEnabled`).
