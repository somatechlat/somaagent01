# UI-S-52 — Settings — Integrations

**Settings — Integrations** — section **Integrations** inside the one Settings shell — routes `/settings/channels` · `/agent/channels`.
Chrome abbreviated (UI-S-00). Left section nav (7) is visible; Integrations is active.

**Keys law.** Credentials are Vault-backed and **write-only**. UI shows `● set` / `○ missing` (or `•••••• (saved in Vault)`). Never an editable echo of the secret. Rotate in Vault.
**Memory rule.** No Memory controls here. Memory lives at `/memory` (UI-S-04) only.

```
┌─ UI-S-00 chrome (abbrev) ────────────────────────────────────────────────────────────────────────┐
│ ☰ SOMA    Settings · Integrations     [Search settings…]                     [Save] [Cancel]     │
├──────────────┬───────────────────────────────────────────────────────────────────────────────────┤
│ SECTION NAV  │  PROVIDERS & KEYS     (write-only — never shown after save)                       │
│  Agent       │  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  Models      │  │ Groq          [● on]   key [● set]   address [api.groq.com/openai/v1]       │   │
│  Voice       │  │   [Manage key] [Test connection]                                             │   │
│  Interface   │  │ OpenAI        [● on]   key [○ missing]  address [api.openai.com/v1]         │   │
│  Tools       │  │   [Add key]   [Test connection]                                              │   │
│  Integrations●│ │ Ollama        [○ off]  key [—]           address [localhost:11434]          │   │
│  Advanced    │  │   [Add key]   [Test connection]                                              │   │
│              │  │ Custom URL    [● on]   key [● set]   address [<gateway-url>]                 │   │
│              │  │   [Manage key] [Test connection]                                             │   │
│              │  └─────────────────────────────────────────────────────────────────────────────┘   │
│              │  Secret storage: Vault · Events · OAuth   (see Advanced links, UI-S-53)             │
│              │                                                                                   │
│              │  CHANNELS                                                                           │
│              │  Capsule modules                                                       [+ Add]     │
│              │  | module | title | enabled | [enable/disable] |                                   │
│              │  | <name> | <title> | yes/no | [toggle] |                                          │
│              │  (empty: "No channel modules registered")                                          │
│              │                                                                                   │
│              │  Add channel                                                                        │
│              │  Kind         [WhatsApp v]   Mode [poll / baileys v]                               │
│              │  Capsule ID   ┌──────────────────────────┐                                         │
│              │               │ <capsule.id>             │                                         │
│              │  Bot token    └──────────────────────────┘                                         │
│              │  (write-only) | •••••• (saved in Vault)  rotate in Vault                           │
│              │  Group mode   [mention v]  Allowlist ┌────────────────┐                             │
│              │                                 │ <csv allowlist>  │                               │
│              │  [Create channel]                                                                  │
│              │                                                                                   │
│              │  Configured channels                                                                │
│              │  | channel | kind | capsule | state | [edit][x] |                                  │
├──────────────┴───────────────────────────────────────────────────────────────────────────────────┤
│ status: <load / save state> · keys write-only · Vault                                           │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Providers & keys (Screen 7F)

| Human label | Control | Notes |
|---|---|---|
| Provider on/off | toggle | `enabled` on the provider record |
| Key | masked + **Manage key** / **Add key** | Write-only. Status only: `● set` / `○ missing`. |
| API address | text | Real base URL from the provider record (never a hard-coded URL) |
| Test connection | button → ok / ms / error | disabled-when: no key and provider requires auth |

## Channels (route body)

| Human label | Control | Notes |
|---|---|---|
| Kind | select | Real enum: `whatsapp` · `telegram` · … |
| Mode | select | WhatsApp: `poll` / `baileys`. Telegram: `webhook` / `cloud`. |
| Capsule ID | text | Required for dispatch |
| Bot token | write-only input | Vault-backed. Never echoed. |
| Group mode | select | Real enum from API |
| Allowlist | csv text | Plain CSV field |

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-101 | provider row | enabled / key status / address from the provider record. |
| 2 | UI-C-084 | key status (write-only) | `● set` / `○ missing` / `—`. When set: `•••••• (saved in Vault)` + "rotate in Vault". Never a real value. |
| 3 | UI-C-068 | Test connection | Calls the real test. disabled-when: no key stored — disabled-reason: "No API key stored for this provider." |
| 4 | UI-C-103 | channel module row | Module name/title/enabled from registered capsule modules. |
| 5 | UI-C-113 | channel create form | Kind/mode enums from API. Capsule ID required for dispatch. |
| 6 | UI-C-071 | configured channels table | Rows from the channels API. `state` is the real dispatch state. |
| 7 | UI-C-069 | delete channel (destructive) | Opens UI-M-03. disabled-when: channel is mid-dispatch — disabled-reason: "Channel is dispatching. Try again when it is idle." |

**State variants.**

- **Loading.** Skeleton rows. No counts while loading.
- **Empty (providers).** "Add a provider key to connect a model." → [Keys →] / Manage key.
- **Empty (channels).** "No channels configured. Add a channel to start dispatching."
- **Error.** "Couldn't load integrations. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to integration settings. Requires the agent-owner role."
- **Offline.** "You're offline. Changes will not be saved until the connection returns."

**Modal overlays.** UI-M-01 Drawer — key write / channel edit (token write-only, never echoes the stored value). UI-M-03 Dialog — "Revoke the stored key for `‹ provider ›`?" / "Delete channel `‹ channel.id ›`?" (destructive).

**Route evidence.** `webui/src/main.ts` `'/settings/channels' || '/agent/channels'` → `soma-settings-channels`. Channels fields from `webui/src/views/soma-settings-channels.ts` (kind, mode, capsule_id, bot_token, group_mode). Key status type `SecretProviderStatus` in `webui/src/views/soma-settings.ts`.
