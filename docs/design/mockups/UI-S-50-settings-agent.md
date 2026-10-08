# UI-S-50 — Settings — Shell + Agent

**Settings workspace (one shell)** — left section nav + right content — route `/settings` — facet **Settings**.
Chrome abbreviated (UI-S-00). This mock is the **shell** (7 sections) with the **Agent** section body (Screen 7).

**Language law.** Binding copy is **Used for: Chat / Help / Memory**. The banned admin noun never appears in UI strings.
**Memory rule.** Memory is not a Settings section. Its only home is `/memory` (UI-S-04, left rail).

```
┌─ UI-S-00 chrome (abbrev) ────────────────────────────────────────────────────────────────────────┐
│ ☰ SOMA    Settings     [Search settings…]                                    [Save] [Cancel]     │
├──────────────┬───────────────────────────────────────────────────────────────────────────────────┤
│ SECTION NAV  │  AGENT                                                                            │
│  Agent    ●  │  How new chats behave.                                                            │
│  Models      │  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  Voice       │  │ Default personality     [Friendly assistant                    ▼]           │   │
│  Interface   │  │   What new chats use for tone and style.                                      │   │
│  Tools       │  │                                                                                │   │
│  Integrations│  │ System instructions                                                         │   │
│  Advanced    │  │ ┌─────────────────────────────────────────────────────────────────────────┐ │   │
│              │  │ │ You are helpful, precise, and honest.                                   │ │   │
│              │  │ └─────────────────────────────────────────────────────────────────────────┘ │   │
│              │  │   Standing rules the agent always follows.                                   │   │
│              │  │                                                                                │   │
│              │  │ Knowledge folder      [general-kb                               ▼]           │   │
│              │  │   Extra docs the agent may use.                                              │   │
│              │  │                                                                                │   │
│              │  │ Inherit current project  [● on]                                             │   │
│              │  │   New chats keep this project’s context.                                     │   │
│              │  │                                                                                │   │
│              │  │ Max failed replies in a row  [ 5 ]                                          │   │
│              │  │   Stop after this many broken answers.                                       │   │
│              │  └─────────────────────────────────────────────────────────────────────────────┘   │
│              │                                                                                   │
│              │  (section content scrolls; Save / Cancel stay in the header)                      │
├──────────────┴───────────────────────────────────────────────────────────────────────────────────┤
│ status: <save state> · permission: settings:edit → write, else read-only banner                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Section nav (the 7, always visible)

| Section | Body | Spec / mock |
|---|---|---|
| **Agent** | personality, system instructions, knowledge, inherit project, failed-reply cap | Screen 7 · **this file** |
| **Models** | model cards + modal (Normal / Advanced / Used for) | Screen 7B · UI-S-51 |
| **Voice** | personas CRUD, TTS/STT, Test speak/listen | Screen 7C · UI-S-48-settings-voice · run: UI-S-46/47/48 |
| **Interface** | theme, language, timezone, date format, notifications | Screen 7D · UI-S-54-settings-interface |
| **Tools** | catalog enable cards + timeout / max size / iterations | Screen 7E · UI-S-55-settings-tools |
| **Integrations** | providers & keys (Vault), channels, events, OAuth | Screen 7F · UI-S-52 |
| **Advanced** | modules, quotas, experimental, backup, developer | Screen 7G · UI-S-53 |

One Settings entry from the app header. No second settings portal. No Memory item in this nav.

## Agent fields (test table)

| Label | Control | Default | Help |
|---|---|---|---|
| Default personality | select | Friendly assistant | New chat behavior |
| System instructions | textarea | (template) | Standing rules |
| Knowledge folder | select | general-kb | Extra docs |
| Inherit current project | toggle | on | Project context in new chats |
| Max failed replies in a row | number ≥1 | 5 | Stop broken loops |

These are **agent behavior** controls. They are not `ModelIn` fields (those live only on model cards, UI-S-51).

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-100 | section nav (7) | Agent · Models · Voice · Interface · Tools · Integrations · Advanced. Each item swaps the right pane inside one shell. |
| 2 | UI-C-116 | settings search | Filters section titles and field labels client-side. |
| 3 | UI-C-067 | Save (primary, header) | Saves the active section form. disabled-while: request in flight. |
| 4 | UI-C-069 | Cancel (secondary, header) | Restores last saved values. |
| 5 | — | permission banner | When `system:configure` is absent: read-only banner, Save disabled-reason: "Requires settings edit permission." |

**State variants.**

- **Loading.** Skeleton field blocks. No counts or metrics while loading.
- **Empty.** "No agent configuration saved yet. Set a personality and system instructions to begin."
- **Error.** "Couldn't load settings. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to settings. Requires settings edit permission."
- **Offline.** "You're offline. Changes will not be saved until the connection returns."

**Modal overlays.** UI-M-03 Dialog — "Reset agent settings to defaults?" (destructive). Key entry is never on this screen (Integrations / UI-S-52).

**Route evidence.** `webui/src/main.ts` `path === '/settings'` → `soma-settings`. Live tab labels (`webui/src/views/soma-settings.ts` `_tabs`) currently omit Interface and Tools — see `SOMA-UI-NAV-AUDIT-001.md` GAP-S1.
