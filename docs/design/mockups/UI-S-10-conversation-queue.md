# UI-S-10 — Conversation queue (Agent Soma)

Screen UI-S-10 · Facet: Chat · Host: UI-S-07 composer (C5) — **no separate route** in `main.ts`  
Spec: `docs/iso/SOMA-01-UIUX-001.md` UI-S-10 · Live: `webui/src/components/soma-composer.ts` (`_queue`)

**Honesty.** Queue depth MUST reflect real client state (`soma-composer.ts:32`, `392-395`). Do not simulate
queued items. Pausing the queue is client-side only — say so. This is **message** queue-while-busy,
not a conversation backlog with priorities (that would be invented).

---

## 1. Purpose

Hold messages the user types while a turn is streaming, show how many are waiting, drop them if
needed, and drain one per idle transition so the host can flip `busy` back on before the next send.

---

## 2. ASCII wireframe — queue chip + queue list under C5 (bands A–E kept)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ A TOP · B LEFT · C1 header · C2 memory pulse · C3 stream · C4 HITL  — as UI-S-07              │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ C5 · COMPOSER                                                                                 │
│  ┌────────────────────────────────────────────────────────────────────────────┐              │
│  │ 📎  Describe what you want the agent to do…                          🎤  ➤ │              │
│  └────────────────────────────────────────────────────────────────────────────┘              │
│  [+] Attach · Memory Context · Clear · Export                                                │
│                                                                                              │
│  ⏱ 2 queued [drop all] [1]     ·     Enter send · ⇧↵ newline                                │
│                                                                                              │
│  ┌─ QUEUE LIST [2] ──────────────────────────────────────────────────────────┐               │
│  │ 1  ‹text preview›  ‹attachment count›              [drop] [3]            │               │
│  │ 2  ‹text preview›                                 [drop] [3]            │               │
│  └────────────────────────────────────────────────────────────────────────────┘               │
│     Send-all [4]   (optional host action — disabled while a turn is streaming)                │
│     Pause queue / Resume queue [5]  — CLIENT-SIDE ONLY                                       │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ E STATUS  … queue ‹live› …                                                                   │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

Only the **queue chip + drop-all** row is implemented in `soma-composer.ts` today. The expanded list
(UI-C-035) and per-row drop / Send-all / pause are the UI-C-035/036 surface; draw a control live only
when it is bound (see §3). No priority column, no “requeue”, no operator table.

---

## 3. Control map (UI-C / UI-A → live code)

| # | UI-C / UI-A | Control | Live binding |
|---|---|---|---|
| 1 | UI-C-036 | Queue chip “N queued” + **Drop queued messages** | `soma-composer.ts:603-615`; clear → `_clearQueue` `411-413` |
| 2 | UI-C-035 | Queue list (ordered) | `_queue: ComposerSendDetail[]` `soma-composer.ts:32`. Render the real order; nothing is prefilled. |
| 3 | UI-A-026 | Drop queued message | Today the bound action is **drop all** (`_clearQueue`). Per-row drop ships with the expanded list — do not draw a live per-row button until it is wired. |
| 4 | — | Send-all | Spec convenience. Live behavior is automatic drain one-per-idle (`soma-composer.ts:352-356`). Disable while `busy`. |
| 5 | UI-C-036 | Pause / Resume queue | Client-side gate on the drain loop only. Label it “client-side”. Not a server control. |
| C5 | UI-A-025 | Enqueue message | `_send()` while `busy` → `this._queue = [...this._queue, item]` `soma-composer.ts:392-395` |
| C5 | UI-A-019 | Send (when idle) | `_dispatchSend` `377-383` → WS `chat.message` `soma-chat.ts:1764-1772` |

**Not offered (would be invented):** priority · operator requeue · server-side conversation queue depth · cancellation jobs.

---

## 4. Field / behavior table

| Field | Source | Behavior |
|---|---|---|
| queue item | `ComposerSendDetail { text, attachments }` `soma-composer.ts:16-19` | Exactly what the user typed, plus file chips already staged. |
| depth | `this._queue.length` | Drives the chip label `‹n› queued`. Never hard-coded. |
| enqueue | Send (Enter / ➤) while `busy` | Item is appended and the textarea clears (`392-395`, `402-409`). |
| drain | `updated()` on `busy → false` | One item per idle transition (`352-356`) so the host can raise `busy` again before the next dispatch. |
| drop all | chip close button | `_clearQueue()` sets `_queue = []` (`411-413`). |
| send fail | host `_onComposerSend` / WS | Inline errors (“Still finishing the previous turn…”, “Not connected — message not sent”). Queued items stay in the list until sent or dropped. |
| hint row | `soma-composer.ts:626-630` | “Enter send · Shift+Enter newline” only when queue is empty and mic idle. |

---

## 5. States (verbatim copy)

| State | Verbatim |
|---|---|
| empty | “Queue is empty.” |
| empty (alt, chip hidden) | (no chip when `_queue.length === 0` — `soma-composer.ts:603`) |
| hint | “Enter send · Shift+Enter newline” |
| queue drop title | “Drop queued messages” (`soma-composer.ts:610`) |
| send while busy (host) | “Still finishing the previous turn — message not sent” (`soma-chat.ts:1704`) |
| send when WS down | “Not connected — message not sent” (`soma-chat.ts:1721`) |
| permission | “You do not have permission to post in this conversation.” |
| offline | “Send is unavailable offline.” / “Offline — queued messages will not send.” |
| loading | “Loading queue…” (only if a future expanded list fetches) |
| error | “Queue state unavailable.” |

---

## 6. Navigation in / out

| Direction | Target | Notes |
|---|---|---|
| In | UI-S-07 C5 while a turn is streaming | Type + Send → enqueue (UI-A-025). |
| Out | C3 stream | On idle, the head item is dispatched as a normal send. |
| Out | (none) | No route. Queue lives only inside the composer. |
| — | `/memory` | Not related. Memory has one home. |

---

## 7. Test clicks

1. Start a streaming turn; type “first” + Enter → textarea clears, chip shows `1 queued`.
2. Type “second” + Enter → `2 queued`.
3. Stop or wait for the turn to finish → one item drains to the stream; chip becomes `1 queued`.
4. With items queued, press chip **drop** → list empties; chip disappears.
5. Confirm no priority/requeue chrome exists.
6. Pause queue (when the expanded control is bound) → drain stops locally; Resume → continues. Label reads “client-side”.
7. Offline: queued items remain; they do not silently vanish.

---

## 8. Code verified

| File:line | What |
|---|---|
| `webui/src/components/soma-composer.ts:16-19` | `ComposerSendDetail` |
| `webui/src/components/soma-composer.ts:32`, `352-356`, `385-413` | queue state, drain-on-idle, enqueue, clear |
| `webui/src/components/soma-composer.ts:589-630` | Send button, queue chip, hints |
| `webui/src/views/soma-chat.ts:1697-1777` | host send path + inline errors |
| `webui/src/views/soma-chat.ts:1764-1772` | WS `chat.message` payload (`content`, `conversation_id`, `mode`, `attachments`) |

End of Document
