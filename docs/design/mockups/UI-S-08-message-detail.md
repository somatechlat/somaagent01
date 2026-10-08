# UI-S-08 — Message detail (Agent Soma)

Screen UI-S-08 · Facet: Chat · Route: `/chat/:id` (same `soma-chat` element as UI-S-07)  
Spec: `docs/iso/SOMA-01-UIUX-001.md` UI-S-08 · Bands: `docs/design/SOMA-UI-CHAT-WORKSPACE-001.md`  
Live: `webui/src/views/soma-chat.ts` + `soma-message.ts` + `soma-tool-timeline.ts`

**Honesty:** `main.ts:316-318` mounts `soma-chat` for every `/chat/*` path. There is **no separate message-detail view today** — UI-S-08 is the inspect posture of a selected message inside UI-S-07 (UI-C-031 / UI-C-032). Do not claim a dedicated detail route.

---

## 1. Purpose

Inspect one message in place: full body, the tool-call process group that produced it, and read-only
turn metadata that the server actually sent. Memory is not on this screen — only the C2 readout of
UI-S-07 and a link to `/memory`.

---

## 2. ASCII wireframe — inspect posture inside UI-S-07 (bands A–E kept)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ A · TOP BAR   [S] SOMA  Agent ▾  ● ‹conn›  [‹model›]  [‹mode›]  ⚙️  👤                      │
├──────────────┬───────────────────────────────────────────────────────────────┬───────────────┤
│ B · LEFT     │ C1  Analyze Q3 data          [Pause][Nudge][Stop][Reset] [⋯]  │ D · CANVAS    │
│  (as UI-S-07)│     Soma Assistant · ‹model› · live                       ● ‹t›│  [Files][Tools]│
│              ├───────────────────────────────────────────────────────────────┤ [Browser†]    │
│              │ C2  🧠 recall ‹n› · … · [Open Memory] → /memory               │ [Editor]      │
│              ├───────────────────────────────────────────────────────────────┤ [Debug] ← raw │
│              │ C3  MESSAGE DETAIL (selected)                                 │ [Capsule]     │
│              │  ┌────────────────────────────────────────────────────────┐   │ [Brain]       │
│              │  │ ‹message.role› · ‹created_at ›          [ Copy ] [1]   │   │ [Desktop†]    │
│              │  │ ┌────────────────────────────────────────────────────┐ │   │               │
│              │  │ │ ‹message.content›  (markdown · code · images ·     │ │   │  NO Memory    │
│              │  │ │  files) — full body, wrapped                      │ │   │  tab.         │
│              │  │ └────────────────────────────────────────────────────┘ │   │               │
│              │  │ ATTACHMENTS [2]  ‹name› ‹size› …                        │   │               │
│              │  │ TOOL-CALL TRACE / PROCESS GROUP [3]                    │   │               │
│              │  │  ┌─ ⚙ ‹tool.name› · ‹status› · ‹durationMs›ms ── [▼] ┐│   │               │
│              │  │  │  ‹arguments› / ‹result›  (Expand → UI-M-01)        ││   │               │
│              │  │  └────────────────────────────────────────────────────┘│   │               │
│              │  │ META [4]  model ‹live›  confidence ‹live›              │   │               │
│              │  │           context ‹live› tokens   timestamp ‹created_at›│  │               │
│              │  │ [ Open conversation ] [5]                              │   │               │
│              │  └────────────────────────────────────────────────────────┘   │               │
│              ├───────────────────────────────────────────────────────────────┤               │
│              │ C4 HITL (only when a step is approval_required)               │               │
│              │ C5 Composer (unchanged — still typeable)                      │               │
├──────────────┴───────────────────────────────────────────────────────────────┴───────────────┤
│ E · STATUS  turn ‹live› · context ‹live› · recall ‹live› · tools ‹live› │ DA ‹live› …        │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Control map (UI-C / UI-A → live code)

| # | UI-C / UI-A | Control | Live binding |
|---|---|---|---|
| 1 | UI-A-021 | Copy message | `soma-message.ts:455-459` (`navigator.clipboard.writeText`); button `542-555` |
| 2 | — | Attachment chips (name · type · size) | `ChatMessage.attachments` `soma-chat.ts:41`, render `soma-message.ts:506-508` |
| 3 | UI-C-031 | Message payload viewer (body + tool-call trace) | `soma-message.ts:23-32`; tools → `soma-tool-timeline` `500` |
| 3a | — | Process-group row: name · status · durationMs | `ToolCallStep` `soma-tool-timeline.ts:25-39`; status labels `340-349` |
| 3b | — | Expand / collapse tool activity | `soma-message.ts:470`, `489-501` |
| 3c | — | HITL Approve / Deny when `approval_required` | `soma-tool-timeline.ts:375-384` → `tool-approval` → WS `tool.approval` `soma-chat.ts:1547-1562` |
| 4 | UI-C-032 | Message meta panel (read-only) | role / timestamp / confidence / stopped / error from `ChatMessage` `soma-chat.ts:31-42`; confidence bar `soma-message.ts:534-539` |
| 5 | UI-A-032 | Open conversation | Select the parent conversation row → GET `/chat/conversations/:id/messages` `soma-chat.ts:1815` |
| D | — | Debug surface (raw WS frames) | `soma-right-panel` UI-X-05 — same registry, no second Memory UI |

**Spec-only (not in `soma-chat.ts` / `soma-message.ts` today — do not draw as live):** UI-A-022 Jump to branch point · UI-A-020 Branch conversation. There is no branch tree in the live view.

---

## 4. Field / behavior table

| Field | Source | Behavior |
|---|---|---|
| `role` | `ChatMessage.role` | `user` · `assistant` · `system` (`soma-chat.ts:33`). Rendered via `message-role` (never the ARIA `role`). |
| body | `content` / stream buffer | Markdown + code + images + files. Code fences get a language chip and a working copy (`soma-message.ts:433`, `bindCodeCopy`). |
| `timestamp` | history `created_at` | Live stream commits carry empty timestamp on purpose (`soma-chat.ts:1358-1361`) — no client clock is shown as message time. |
| `confidence` | history `metadata.confidence` or `chat.done` | Bar + percent only when present (`soma-message.ts:534-539`). Never defaulted. |
| `tools[]` | WS `tool.call` / `tool.delta` / `tool.done` | Collapsed header keeps **tool name + status**; expand materializes arguments/result. |
| `durationMs` | `tool.done.duration_ms` | Shown only when the server sent it (`soma-tool-timeline.ts:346-348`). |
| `attachments[]` | composer send | name · type · size chips. |
| `error` | WS `error` / send failure | Inline on the message (`soma-message.ts:523-527`), not a global banner. |
| `stopped` | UI-A Stop | Badge “stopped” (`soma-message.ts:533`). |
| secrets | tool arguments | Masked in any drawer (`sk-••••••••aBcD`) + “rotate in Vault”. |

---

## 5. States (verbatim copy)

| State | Verbatim |
|---|---|
| loading | “Loading message…” |
| empty | “This message has no body.” |
| trace empty | “No tool calls on this message.” (`soma-tool-timeline.ts:396` “No tool calls”) |
| error | “Message could not be loaded. It may have been deleted.” |
| not found | “Message not found.” |
| permission | “You do not have permission to read this message. Ask a platform admin for the member role.” |
| offline cached | “Showing the cached copy.” |
| offline uncached | “Message is unavailable offline.” |
| offline branch (if ever wired) | “Branch is unavailable offline.” |

---

## 6. Navigation in / out

| Direction | Target | Notes |
|---|---|---|
| In | `/chat/:id` | Same `soma-chat` shell (`main.ts:316-318`). |
| In | Message row select in UI-S-07 C3 | Focuses inspect posture. |
| Out | UI-S-07 C3 stream | “Open conversation” / dismiss selection. |
| Out | `/memory?turn=current` | C2 **Open Memory** only — not from this pane. |
| Out | Debug surface UI-X-05 | Raw frames for the selected turn. |

---

## 7. Test clicks

1. Open `/chat/:id` → bands A–E still present; selected message expanded.
2. **Copy** → clipboard receives the message body verbatim; label flips to “Copied”.
3. Expand process group → arguments/result; collapse → header keeps tool name + status + duration.
4. HITL step → **Approve** / **Deny** sends WS `tool.approval`; disconnect → inline error.
5. Confidence bar renders only when `metadata.confidence` exists.
6. C2 **Open Memory** → `/memory` (single Memory home).
7. Offline: cached body + “Showing the cached copy.”

---

## 8. Code verified

| File:line | What |
|---|---|
| `webui/src/main.ts:316-318` | `/chat/` mounts `soma-chat` (no detail view) |
| `webui/src/views/soma-chat.ts:31-42` | `ChatMessage` fields |
| `webui/src/views/soma-chat.ts:1332-1372` | `chat.done` commit (empty timestamp honesty) |
| `webui/src/views/soma-chat.ts:1812-1834` | GET `/chat/conversations/:id/messages` |
| `webui/src/components/soma-message.ts:22-32`, `455-459`, `489-555` | props, copy, tools, attachments, error, meta |
| `webui/src/components/soma-tool-timeline.ts:25-39`, `332-384` | step shape, status chrome, approval row |

End of Document
