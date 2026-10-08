# UI-S-09 — Conversation export (Agent Soma)

Screen UI-S-09 · Facet: Chat · Entry: UI-S-07 (conversation row ⋮ Export · composer menu Export Chat)  
Spec: `docs/iso/SOMA-01-UIUX-001.md` UI-S-09 · Live: `webui/src/views/soma-chat.ts` (`_exportConversation`, `_onExportChat`)

**Honesty.** There is no separate export route in `main.ts`. Export is a client-side JSON download built
from real message rows. Do **not** offer a format the exporter cannot produce (REQ-UIX-004). Today that
means **JSON only, whole conversation only** — the UI-C-033/034 controls exist as single-option selects
so the next implemented option can appear without inventing a dead button.

---

## 1. Purpose

Package the current conversation into a file the user can keep. Preview is the real payload that will
be written; download is the real Blob the code creates (`soma-chat-‹id›.json`).

---

## 2. ASCII wireframe — export dialog over UI-S-07 (chrome unchanged)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ A · TOP BAR · B LEFT · C chat · D canvas · E status  — UI-S-07 bands, untouched               │
│                                                                                              │
│      ┌──────────────────── Conversation export ────────────────────┐                         │
│      │ SOURCE [1]  ‹conversation.title›  ·  ‹message.count› msgs  │                         │
│      │            id ‹conversation.id›                            │                         │
│      │ SCOPE   [2]  ( whole conversation ▾ )                      │                         │
│      │ FORMAT  [3]  ( JSON ▾ )                                    │                         │
│      │ PREVIEW [4]                                                │                         │
│      │  ┌──────────────────────────────────────────────────────┐  │                         │
│      │  │ {                                                    │  │                         │
│      │  │   "conversation_id": "‹conversation.id›",            │  │                         │
│      │  │   "title": "‹conversation.title›",                   │  │                         │
│      │  │   "exported_at": "‹ISO timestamp›",                  │  │                         │
│      │  │   "messages": [ { "role": "…", "content": "…",       │  │                         │
│      │  │       "timestamp": "…", "tools": [ … ],              │  │                         │
│      │  │       "attachments": [ … ] } , … ]                   │  │                         │
│      │  │ }                                                    │  │                         │
│      │  └──────────────────────────────────────────────────────┘  │                         │
│      │  status: ‹export.status›     file: soma-chat-‹id›.json     │                         │
│      │  [ Start export ] [5]      [ Download ] [6]                │                         │
│      └─────────────────────────────────────────────────────────────┘                         │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Control map (UI-C / UI-A → live code)

| # | UI-C / UI-A | Control | Live binding |
|---|---|---|---|
| 1 | — | Source readout | `conv.title` / `conv.id` / server `message_count` when present (`soma-chat.ts:44-51`, `1048`). Never defaulted to 0. |
| 2 | UI-C-033 | Scope select | **Only “whole conversation”** is offered — the exporter writes exactly that (`soma-chat.ts:1105-1141`, `1658-1691`). Other scopes stay hidden until implemented. |
| 3 | UI-C-034 | Format select | **Only `JSON`** — `JSON.stringify(…, null, 2)` + `application/json` Blob (`1120-1134`, `1670-1684`). No Markdown option. |
| 4 | UI-C-068 | Export preview | READ-ONLY render of the object that will be stringified. Shape illustration; values are the live rows. |
| 5 | UI-A-023 | Start export | Row path: GET `/chat/conversations/:id/messages` when the conversation is not already in memory (`1107-1118`). Menu path: uses in-memory `_messages` (`1658-1669`). |
| 6 | UI-A-024 | Download export | `URL.createObjectURL` + `<a download="soma-chat-‹id›.json">` (`1135-1140`, `1685-1690`). Enabled once the Blob is built. |

**Not offered (would be a fake control):** Markdown / PDF formats · redaction toggles · server-side export jobs · encryption or retention claims the code does not implement.

---

## 4. Field / behavior table

| Field | Source | Behavior |
|---|---|---|
| `conversation_id` | active or selected row id | Written as-is. |
| `title` | conversation title | Missing title exports as empty string — not an invented name. |
| `exported_at` | `new Date().toISOString()` | Client clock **for the file envelope only** (not message time). |
| `messages[].role/content/timestamp` | message rows | History rows carry `created_at`; live rows may have empty `timestamp` (`soma-chat.ts:1358-1361`). |
| `messages[].tools` | `msg.tools ?? []` | Process-group steps as stored (`1667`). |
| `messages[].attachments` | `msg.attachments ?? []` | name / type / size only. |
| filename | `soma-chat-‹conversation.id›.json` | Falls back to `soma-chat-export.json` when id is empty (`1138`, `1688`). |
| empty transcript | `_messages.length === 0` | Row export still fetches messages; menu export raises inline “Nothing to export yet” (`1659-1661`). |

---

## 5. States (verbatim copy)

| State | Verbatim |
|---|---|
| loading | “Preparing export preview…” |
| empty | “This conversation has no messages to export.” |
| preview empty | “Nothing to preview yet.” |
| menu empty | “Nothing to export yet” (`soma-chat.ts:1660`) |
| error | “Export could not be prepared. Retry, or check that the somaAgent01 API is reachable.” |
| download fail | “Download failed. Start the export again.” |
| permission | “You do not have permission to export this conversation. Ask a platform admin for the member role.” |
| offline | “Export is unavailable offline.” (fetch of foreign conversation messages fails; in-memory export of the open transcript still works and is labelled as such) |

---

## 6. Navigation in / out

| Direction | Target | Notes |
|---|---|---|
| In | UI-S-07 row **Export** (⋮ / download icon) | `_exportConversation` `soma-chat.ts:2055-2063`, `1105-1141` |
| In | UI-S-07 composer **+ → Export Chat** | `soma-composer-menu.ts:165-168` → `_onExportChat` `1658-1691` |
| Out | Filesystem | Browser download; no second surface. |
| Out | UI-S-07 | Dialog dismiss returns to the same workspace. |
| — | `/memory` | Not an export target. Memory export lives on UI-S-04. |

---

## 7. Test clicks

1. Open a conversation with messages → row **Export** → download starts as `soma-chat-‹id›.json`.
2. Verify JSON contains `conversation_id`, `title`, `exported_at`, `messages[]` with `role`/`content`/`timestamp`/`tools`/`attachments`.
3. Composer **+ → Export Chat** on an empty transcript → “Nothing to export yet”.
4. Switch conversation (not loaded) → Export → GET messages first, then download.
5. Scope/Format selects show only the implemented options; no dead Markdown row.
6. Offline + export a foreign conversation → error copy; export of the open transcript still downloads.

---

## 8. Code verified

| File:line | What |
|---|---|
| `webui/src/views/soma-chat.ts:1105-1141` | `_exportConversation` — GET messages + JSON Blob download |
| `webui/src/views/soma-chat.ts:1658-1691` | `_onExportChat` — in-memory export + download |
| `webui/src/views/soma-chat.ts:44-51` | `Conversation.messageCount` only when server sent it |
| `webui/src/views/soma-chat.ts:2055-2063` | Row Export button |
| `webui/src/components/soma-composer-menu.ts:165-168` | Export Chat menu item |

End of Document
