# CM-01 — Chat Workspace Control Map

## Document Control

| Field | Value |
|---|---|
| Document Title | Control Map — Chat Workspace (chrome, sidebar, composer, stream, tools) |
| Document Identifier | SOMA-UI-CM-01 |
| Version | 1.1.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | SomaTech Engineering (soma-ui-engineer) |
| Classification | Internal |
| ISO Reference | ISO 9241-210:2019 |
| Next Review | 2027-01-13 |
| Related | `SOMA-UI-BINDINGS-001.md` §1 · `UI-S-00` · `UI-S-07` · `UI-S-08` · `UI-S-09` · `UI-S-10` · `SOMA-UI-IA-001.md` · `SOMA-UI-NAV-001.md` |
| Live sources | `webui/src/views/soma-chat.ts` · `webui/src/components/soma-composer.ts` · `soma-composer-menu.ts` · `soma-chat-topbar.ts` · `soma-message.ts` · `soma-tool-timeline.ts` · `soma-sidebar.ts` · `soma-welcome-dashboard.ts` · `soma-status-dot.ts` · `soma-agent-header.ts` · `soma-agent-iq.ts` |
| Routes | `/` · `/chat` · `/chat/:id` · `/workspace` · `/soma/chat` |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | soma-ui-engineer | Exhaustive control map for chat chrome, sidebar, composer, stream, tool timeline, welcome hero. |
| 1.1.0 | 2026-10-13 | soma-ui-engineer | Attachment display polish: Material file-type icons (no emojis), honest media/attachment cards (no stuck spinner), tool chevron as Material icon. C-30/C-30a/C-67 as-built. |

---

## 1. ASCII wireframe — active conversation

```
┌─ thin top strip (UI-S-00) ─────────────────────────────────────────────────────────────────────┐
│ C-01 logo/home   C-02 agent select ▾   C-03 mode STD|DEV|RO|DGR (+TRN/ADM locked)             │
│                 C-04 brain ◉  C-05 sync ○  C-06 memory ◌          C-07 user initials  C-08 ⋯  │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
┌─ left rail ────────┬─ chat stream (hero) ───────────────────────────────────┬─ right canvas ─┐
│ C-10 New chat      │ C-20 title / title_update                              │ C-40 rail toggle│
│ C-11 search        │ C-21 topbar: Pause Resume Stop Reset Nudge             │  UI-X-01…08     │
│ C-12 conv list     │ C-22 turn meta: model · context · lanes · recall       │  (see CM-06)    │
│   C-12a select     │ C-23 user bubble                                       │                 │
│   C-12b rename     │ C-24 assistant bubble (markdown + code)                │                 │
│   C-12c export     │   C-24a copy                                           │                 │
│   C-12d delete     │   C-24b tools expand/collapse                          │                 │
│   C-12e rename in  │ C-25 tool timeline step                                │                 │
│   C-12f rename ok  │   C-25a approve  C-25b deny                            │                 │
│ C-13 Memory →      │ C-26 typing / streaming indicator                      │                 │
│ C-14 Settings →    │ C-27 message skeleton (loading)                        │                 │
│ C-15 user avatar   │ ┌─ composer (hero) ──────────────────────────────────┐ │                 │
│ C-16 logout        │ │ C-30 attach chips (remove)                         │ │                 │
│                    │ │ C-31 composer menu ▾ (attach/memory/clear/export)  │ │                 │
│                    │ │ C-32 textarea Message                              │ │                 │
│                    │ │ C-33 mic   C-34 send                               │ │                 │
│                    │ │ C-35 queue chip + drop                             │ │                 │
│                    │ └────────────────────────────────────────────────────┘ │                 │
└────────────────────┴────────────────────────────────────────────────────────┴─────────────────┘
```

## 2. ASCII wireframe — welcome (empty chat)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  greeting                          C-50 warning banner + Open Settings + Dismiss │
│  hero composer (same C-30…C-35)    C-51 quick: Modules / Tools / New chat        │
│  C-52 Connect channels section + Manage › (→ /settings/channels)                 │
│  C-53 System section (RAM/CPU/Disk from diagnostics; hidden if API down)         │
│  LAW: no Memory / Settings / Models hero cards                                   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Control map

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| C-01 | Logo / home | link | local navigate `/chat` | default, hover, focus | — | `link` “Chat home” | LIVE |
| C-02 | Agent select | select | `GET /agents/` then WS reconnect `/ws/v2/chat/{wsId}` | default, loading, error | — | `combobox` labelled “Agent” | LIVE |
| C-03a | Mode STD | chip | local `mode` on next `chat.message` | default, active | — | `radio` group “Agent mode” | LIVE |
| C-03b | Mode DEV | chip | same | default, active | — | same | LIVE |
| C-03c | Mode RO | chip | same | default, active | — | same | LIVE |
| C-03d | Mode DGR | chip | same | default, active | — | same | LIVE |
| C-03e | Mode TRN | chip | — | disabled | Locked in this build (`locked: true` mode list) | `aria-disabled` + reason | GATED |
| C-03f | Mode ADM | chip | — | disabled | Locked in this build (`locked: true` mode list) | `aria-disabled` + reason | GATED |
| C-04 | Brain status ◉ | status-dot | `GET /core/brain-connector` `{connected, circuit, last_error?}` | ok, degraded, error | — | `img` role + `title` tooltip | LIVE |
| C-05 | Sync status ○ | status-dot | brain-connector (status only) | ok, degraded | — | labelled “sync” | LIVE |
| C-06 | Memory status ◌ | status-dot | brain-connector + memory list freshness | ok, degraded | — | labelled “memory” | LIVE |
| C-07 | User avatar / initials | readout | `GET /auth/me` | default, loading | — | `img` alt initials | LIVE |
| C-08 | Account menu / logout | button | `POST /auth/logout` then `/login` | default, busy | — | `button` “Logout” | LIVE |
| C-10 | New chat | button | `POST /chat/conversations` `{agent_id}` | default, busy | — | `button` title “New conversation” | LIVE |
| C-11 | Search conversations | input.search | **local** filter over loaded list | default, focus, filled | — | `searchbox` aria-label “Search conversations” | LIVE |
| C-12 | Conversation list | list-row | `GET /chat/conversations` | loading skeleton, empty, error, populated | — | `listbox` / `nav` | LIVE |
| C-12a | Conversation row | list-row | `GET /chat/conversations/{id}/messages` | default, active (`aria-current`) | — | `option` + keyboard Enter/Space | LIVE |
| C-12b | Rename conversation (pencil) | button | opens inline rename | default | — | aria-label “Rename conversation” | LIVE |
| C-12c | Export conversation | button | `GET /chat/conversations/{id}/messages` + client Blob | default, busy | — | aria-label “Export conversation” | LIVE |
| C-12d | Delete conversation | button | `DELETE /chat/conversations/{id}` (confirm modal) | default, pending-confirm | — | aria-label “Delete conversation” | LIVE |
| C-12e | Rename input | input.text | local draft | focus, dirty | — | aria-label “Conversation title” | LIVE |
| C-12f | Save rename | button | `PATCH /chat/conversations/{id}` `{title}` | default, busy | — | aria-label “Save rename” | LIVE |
| C-12g | Cancel rename | button | local | default | — | aria-label “Cancel rename” | LIVE |
| C-12h | Confirm delete modal — Cancel | button | local | default | — | `dialog` “Delete conversation” | LIVE |
| C-12i | Confirm delete modal — Delete | button | `DELETE /chat/conversations/{id}` | default, busy | — | `button` destructive | LIVE |
| C-13 | Memory | link/button | `soma-navigate` → `/memory` | default | — | `link` “Memory” (one home) | LIVE |
| C-14 | Settings | link/button | `soma-navigate` → `/settings` | default | — | `link` “Settings” | LIVE |
| C-15 | User profile card | readout | `GET /auth/me` | default | — | labelled region | LIVE |
| C-16 | Logout | button | `POST /auth/logout` | default, busy | — | aria-label “Logout” | LIVE |
| C-17 | Sidebar collapse | button | local `_toggleCollapse` | default, collapsed | — | `button` aria-expanded | LIVE |
| C-20 | Conversation title | readout | WS `title_update` + PATCH | default, updating | — | heading level 1 | LIVE |
| C-21a | Pause | button | WS `chat.pause` `{conversation_id}` | default, disabled when idle | Streaming not active | aria-label “Pause” | LIVE |
| C-21b | Resume | button | WS `chat.resume` | default, disabled when not paused | Not paused | aria-label “Resume” | LIVE |
| C-21c | Nudge | button | WS `chat.nudge` | default | — | aria-label “Nudge” | LIVE |
| C-21d | Stop | button | WS `chat.stop` + local finalize | default, disabled when idle | Streaming not active | aria-label “Stop” | LIVE |
| C-21e | Reset | button | WS `chat.reset` + `POST /chat/conversations` | default, busy | — | aria-label “Reset” | LIVE |
| C-22 | Turn meta strip | readout | WS `chat.turn_meta` `{model, lanes, memory_hits, context_tokens}` | default | — | `group` “Turn metadata” | LIVE |
| C-22a | Recall hit chip (in strip) | chip | `chat.turn_meta.memory_hits[]` → navigate `/memory` | default | — | `link` to memory home | LIVE |
| C-23 | User message bubble | readout | WS `chat.message` / local echo | default, error-on-upload-fail | — | `article` “user message” | LIVE |
| C-24 | Assistant bubble | readout | WS `chat.delta` / `chat.done` | streaming, complete, stopped, error | — | `article` “assistant message” | LIVE |
| C-24a | Copy message | button | `navigator.clipboard` | default | — | aria-label “Copy message text” | LIVE |
| C-24b | Tools expand/collapse | button | local `_expanded` over live tool frames | collapsed, expanded | — | aria-expanded | LIVE |
| C-25 | Tool step row | list-row | WS `tool.call` `tool.delta` `tool.done` | pending, running, success, failed | — | `listitem` in `log` | LIVE |
| C-25a | Approve tool | button | WS `tool.approval` `{approved:true}` | default | — | `button` “Approve” | LIVE |
| C-25b | Deny / Reject tool | button | WS `tool.approval` `{approved:false}` | default | — | `button` “Deny” | LIVE |
| C-25c | Tool schema expand | button | local over `ToolInfo.parameters` | collapsed, expanded | — | aria-expanded | LIVE |
| C-26 | Typing / thinking | readout | local streaming state | visible/hidden | — | `status` “Assistant is thinking” | LIVE |
| C-27 | Message skeleton | readout | — | loading | — | `aria-hidden` decorative | LIVE |
| C-30 | Attachment chip | chip | `composerStore` + `POST /api/v2/filesv2/upload` | uploading, ready, failed | — | `listitem` with remove; **Material file-type icon** via `attachmentIcon()` (`utils/file-icons.ts`) — no emojis | LIVE |
| C-30a | Remove attachment | button | `composerStore.removeAttachment` | default | — | aria-label “Remove {file.name}” | LIVE |
| C-31 | Composer menu | menu | local `_toggleMenu` | closed, open | — | `button` aria-label “Composer menu” + `menu` | LIVE |
| C-31a | Attach files (menu) | input.file | `POST /api/v2/filesv2/upload` (+ presigned PUT or `/upload-local/{file_id}`) | default, uploading | — | `menuitem` | LIVE |
| C-31b | Open Memory (menu) | button | navigate `/memory` | default | — | `menuitem` | LIVE |
| C-31c | Clear chat (menu) | button | local clear transcript | default | — | `menuitem` | LIVE |
| C-31d | Export chat (menu) | button | client Blob of `_messages` | default | — | `menuitem` | LIVE |
| C-32 | Message textarea | textarea | local composer store; Enter sends | empty, focus, filled, disabled-while-busy-queue | — | aria-label “Message” | LIVE |
| C-33 | Mic / STT | button | `POST /voice/transcribe` `{audio_base64, format, language}` | idle, recording, processing, error | — | aria-label “Start/Stop voice input” | LIVE |
| C-34 | Send | button | WS `chat.message` `{content, conversation_id, mode, attachments}` | default, disabled-empty, busy | — | aria-label “Send message” | LIVE |
| C-35 | Queue chip + drop | button | local `_queue` drained on idle → WS `chat.message` | visible when queue > 0 | — | aria-label “Drop queued messages” | LIVE |
| C-40 | Surface rail toggle | button | local show/hide `soma-right-panel` | open, closed (`aria-pressed`) | — | aria-label “Toggle surface rail” | LIVE |
| C-41 | Agent knobs dock toggle | button | local `_knobPanelOpen` | open, closed | — | aria-expanded “Show/Hide agent knobs” | LIVE |
| C-42 | Knobs dock close | button | local | open | — | aria-label “Close knobs” | LIVE |
| C-43 | Open admin agents | button | navigate `/admin/agents` | default | — | `button` | LIVE |
| C-50 | Warning banner dismiss | button | local | visible | — | aria-label “Dismiss” | LIVE |
| C-50a | Warning banner Open Settings | button | navigate `/settings` | default | — | `button` | LIVE |
| C-51 | Quick action — canvas / Files | button | `_toggleRightPanel` | default | — | `button` in `navigation` | LIVE |
| C-52 | Quick action — Tools | button | navigate `/settings/tools` | default | — | `button` | LIVE |
| C-53 | Quick action — New chat | button | `_startNewChat` | default | — | `button` | LIVE |
| C-54 | Channels Manage › | button | navigate `/settings/channels` | default | — | `link` | LIVE |
| C-55 | Channel connect CTA | button | navigate `/settings/channels` | default | — | `button` | LIVE |
| C-56 | System RAM/CPU/Disk | stat | `GET /api/v2/somabrain/admin/diagnostics` | default, hidden-if-error | Diagnostics API down → section hidden (not fake zeros) | labelled group | LIVE |
| C-60 | Syntax-highlighted code block | readout | client render of streamed text | plain / highlighted | — | `pre`/`code` + copy control | PLANNED |
| C-61 | Markdown tables | readout | client render | rendered | — | semantic `table` | PLANNED |
| C-62 | In-chat message search | input.search | client or `M-039` search API | idle, results, empty, error | — | `searchbox` | PLANNED |
| C-63 | Message regenerate | button | WS resend / `POST` regenerate lane | default, busy | — | `button` | PLANNED |
| C-64 | Message edit | textarea | PATCH message lane (target) | default, dirty | — | `button` Edit + form | PLANNED |
| C-65 | Branch prev / next / create | button | branch API (target `M-040`) | single, multi, disabled | Branch API not deployed → create hidden; navigate only when server provides branches | aria-label “Previous/Next branch” | PLANNED |
| C-66 | Drag-and-drop attach dropzone | surface | same as C-31a upload | idle, dragover, uploading | — | `button` equivalent for keyboard | PLANNED |
| C-67 | Attachment card (in message) | figure | `GET /filesv2/{id}/content` (images) · `GET /filesv2/{id}/download-url` (other) | media-ok, download-card, not-uploaded, preview-unavailable | — | `figure` with Material file-type icon (`attachmentIcon`); name + type + size; Download link when URL resolved; honest “Not uploaded” / “Preview unavailable” — **never a stuck spinner** | LIVE |
| C-67a | Attachment media frame (image/audio/video) | figure | same `/content` or signed URL | loaded, error→icon card | — | `img`/`audio`/`video` with filename caption | LIVE |
| C-67b | Attachment download link | link | signed `download_url` | default | URL unresolved → no link (honest card) | `link` “Download” | LIVE |
| C-68 | Tool approval reason field | textarea | WS `tool.approval` `{reason}` (optional) | default | — | labelled textbox | PLANNED |
| C-70 | AgentIQ knobs (intelligence, autonomy, resource, style) | slider/select | `GET/PATCH /agents/{id}/capsule` `persona_config.knobs` | dirty, saved, busy | No capsule selected — knobs are not loaded. | `slider` with valuetext | LIVE |
| C-71 | AgentIQ Save | button | `PATCH /agents/{id}/capsule` | default, disabled-when-clean, busy | — | `button` | LIVE |
| C-72 | AgentIQ Reset | button | local reset to server values | default, disabled-when-clean | — | `button` | LIVE |

---

## 4. States (screen-level)

| State | Verbatim / behavior |
|---|---|
| loading conversations | skeleton list (`aria-hidden`) |
| empty workspace | welcome hero (no fake history) |
| WS disconnected | offline banner; composer disabled with reason |
| send failure | error on the user bubble (attachment upload failure never invents `file_id`) |
| tool denied by OPA | timeline shows denial + reason; never claims allow |
| empty recall in turn meta | strip omits fake scores |

---

## 5. Honesty notes

1. Conversation search is local over the loaded list — it is not a server FTS claim.
2. Queue is client-side; draining reuses the same WS `chat.message` contract.
3. TRN/ADM modes stay visible-but-disabled with the lock reason (not hidden silently).
4. Brain micro-indicator uses live `GET /core/brain-connector`; no invented latency.
5. Welcome system panel disappears when diagnostics fail — it does not print zeros.
6. **No emojis in user-facing UI.** Icons are Material Symbols only (file trees, chips, labels, chevrons, status marks).
7. Attachment cards use `attachmentIcon(name, type)` for the file-type glyph; unresolved media renders an honest card, never a perpetual spinner.
8. Product names in UI: Agent / Hands / Brain / Memory — never “Capsule” as a product label (API field names may keep capsule).

---

## 6. Source map

| Source | Role |
|---|---|
| `webui/src/views/soma-chat.ts` | Screen host, WS, conversation CRUD, welcome, dock |
| `webui/src/components/soma-composer.ts` | Hero input, attach, mic, send, queue |
| `webui/src/components/soma-composer-menu.ts` | Attach / Memory / Clear / Export menu |
| `webui/src/components/soma-chat-topbar.ts` | Pause / Resume / Stop / Reset / Nudge |
| `webui/src/components/soma-message.ts` | Bubbles, copy, tools toggle, typing |
| `webui/src/components/soma-tool-timeline.ts` | Tool steps + HITL approve/deny |
| `webui/src/components/soma-sidebar.ts` | Left rail nav + collapse |
| `webui/src/components/soma-welcome-dashboard.ts` | Welcome quick actions / warnings |
| `webui/src/components/soma-agent-iq.ts` | Knob strip (C-70…C-72) |
| `webui/src/services/websocket-client.ts` | WS transport + frame log feed |

End of Document

## Chat list (left rail) — compact glass cards (2026-10-13)

| Control | Spec |
|---|---|
| Card | min-height 52px · glass bg · radius-md · icon + title + meta |
| Active | accent border + accent icon tile |
| Scroll | thin scrollbar · `overscroll-behavior: contain` · only list scrolls (sidebar fixed) |
| Actions | hover/focus reveal: rename · export · delete |
| Skin | `--skin-*` only · no huge scroll jump |

WIREFRAME:
```
[+ New chat]
[🔍 Search]
──────
[🟦] Q3 report          2h
[🟦] Fix WS bug          1d
[🟦] API docs           3d
```
