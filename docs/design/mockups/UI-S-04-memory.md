# UI-S-04 — Memory (the one Memory screen)

Screen UI-S-04 · Route: **`/memory`** (`main.ts:329` → `soma-memory-view`)
Chrome: **UI-S-00 thin** (abbrev) · IA: `SOMA-UI-IA-001.md` · Catalog: `SOMA-UI-CATALOG-001.md` §3 Memory
Live view: `webui/src/views/soma-memory-view.ts` (`soma-memory-view`)

**Status: LIVE.** This is **the only Memory UI** in the product.

## 0. One-screen rule (binding)

Memory is implemented once — **here**. Everything else is an *entry point* that routes to this
same view. There is no second Memory surface.

| Entry | Behavior | What it is NOT |
|---|---|---|
| Left rail **Memory** | `router → /memory` | — |
| C2 **Open Memory** (chat pulse) | `router → /memory?turn=current` (same view, this-turn filter on) | **Not a Memory UI.** C2 is a readout + one link (`UI-S-07` C2). |
| ⋮ menu **Open Memory** | `router → /memory` | — |
| ⌘K “Memory” | `router → /memory` | — |
| Composer **Memory Context** | `router → /memory` | — |

**Forbidden homes:** welcome card · canvas tab (UI-X has no Memory tab) · chat mini-panel ·
Settings section · a second dashboard. C2’s `recall n` strip is a **readout only** — clicking it
does not expand a memory panel; only **Open Memory** navigates here.

---

## 1. ASCII wireframe — Memory workspace

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├───────────────────────┬──────────────────────────────────────────────────────────────────────────┤
│ LEFT (this route only)│  MEMORY                                                     [⟳ Refresh] │
│                       │  [Search recall…                    ] [ Run probe ]  layer [both ▾]      │
│  ← Back to chat       │                                                                          │
│                       │  FILTER  this turn [clear]     ← present when ?turn=current              │
│  ─────────────────    │                                                                          │
│  TYPE                 │  ┌─ THIS TURN (readout of this turn's recall) ──────┐                    │
│  [All ▾]              │  │  ‹n› hits · “Nothing recalled this turn.”        │                    │
│   conversation        │  │  ‹score›  ‹summary›                              │                    │
│   fact                │  │  ‹score›  ‹summary›                              │                    │
│   episode             │  └──────────────────────────────────────────────────┘                    │
│   semantic            │                                                                          │
│  ─────────────────    │  ┌─ MEMORY DASHBOARD (API numbers only — no count API) ────────────────┐ │
│  SORT                 │  │  [WM —]   [LTM —]   [recall ‹live›]   [list ‹live›]                 │ │
│  [Newest ▾]           │  │  GATED      GATED     this turn         GET /api/v2/memory/         │ │
│   oldest              │  │  (no count API — show — until one ships. Never 0, never a guess.)   │ │
│   relevance           │  └─────────────────────────────────────────────────────────────────────┘ │
│  ─────────────────    │                                                                          │
│  Total                │  ACTIONS  [Open record] [Remember…] [Forget…] [Export JSON]              │
│  ‹n | —›              │                                                                          │
│                       │  ┌─ RESULT GRID / TIMELINE (server order) ────────────────────────────┐  │
│                       │  │ [kind] ‹summary or content›                      ‹score | —›      │  │
│                       │  │ ‹created_at | —›                        [copy] [Forget…]          │  │
│                       │  │ [kind] ‹summary or content›                      ‹score | —›      │  │
│                       │  └───────────────────────────────────────────────────────────────────┘  │
└───────────────────────┴──────────────────────────────────────────────────────────────────────────┘
```

No chat left-rail, no canvas surface rail — this route mounts its own workspace chrome
(UI-S-00 §2). The wireframe above is the **whole** Memory UI.

---

## 2. Real data — endpoints & fields

| Action | Endpoint | Request | Response used |
|---|---|---|---|
| **List** | `GET /api/v2/memory/` | — | rows + `total` |
| **Recall** | `POST /api/v2/memory/recall` | `{query}` (server `top_k`) | `[{score, summary, …}]` |
| **Forget** | `POST /api/v2/memory/forget` | `{coord}` | ok / error |
| **Remember** | `POST /api/v2/memory/remember` | `{text, …}` | created row |

| Field shown | Source | Absent handling |
|---|---|---|
| `summary` / `content` | row from list/recall | `—` |
| `score` | recall row | `—` (never invent) |
| `kind` (conversation/fact/episode/semantic) | server kind | `untyped` |
| `created_at` | row | `—` |
| `coord` | row | Forget disabled (no coord → cannot forget) |
| `total` | `GET /api/v2/memory/` `total` | `—` (a failed load is **not** `0`) |
| **WM / LTM counts** | **no count API exists** | **`—` / GATED** — never `0`, never a guess |

`C2` in chat shows `recall n` from `chat.turn_meta.memory_hits[]` — that is a chat readout, not a
count API, and it does not populate the WM/LTM tiles.

---

## 3. Control map

| # | Control | API / behavior | Live? |
|---|---|---|---|
| 1 | Search / recall probe | Free text → `POST /api/v2/memory/recall` `{query}`. Enter or **Run probe**. | live (Enter) |
| 2 | Run probe | Same call as #1; explicit submit. | live |
| 3 | Layer filter `wm \| ltm \| both` | Client filter when the server sends a layer. One vocabulary. | design |
| 4 | This-turn filter | From `?turn=current`. `[clear]` returns to the full list. | live (param) |
| 5 | This-turn hits | Score + summary of the current turn’s recall. | design |
| 6 | Timeline / result grid | Rows from `GET /api/v2/memory/` (`kind · summary · score · created_at`). | live |
| 7 | **Dashboard** | WM / LTM → **`—` (no count API)**; recall → this-turn hit count; list → `total`. | live (`—`) |
| 8 | Type filter chips | `all · conversation · fact · episode · semantic`. Server kind only. | live |
| 9 | Sort | `newest · oldest · relevance`. Missing ts/score sort last — no sentinel. | live |
| 10 | Total Memories | `response.total`. `—` until the server reports. | live |
| 11 | Open record | Drawer **UI-M-01** — full stored fields (coord, kind, score, text, created_at, tags). | design |
| 12 | **Remember…** | UI-M-03 form → `POST /api/v2/memory/remember` `{text}`. Row appears in the list. | live (API) |
| 13 | **Forget…** / row delete | Destructive confirm **UI-M-03** → `POST /api/v2/memory/forget` `{coord}`. | live (confirm) |
| 14 | Export JSON | Client download of the currently loaded rows. No server round-trip. | live |
| 15 | Refresh | `GET /api/v2/memory/` again. | live |
| 16 | ← Back to chat | `router → /chat`. | live |

---

## 4. Numbered journey — remember → Open Memory → see row → forget → recall empty

| Step | Where | Action | API | Result on this screen |
|---|---|---|---|---|
| **1** | `/chat` (UI-S-07) | Agent runs `remember` during a turn (“Remember: the EU plan is €4.8M”) | `POST /api/v2/memory/remember` | Nothing here yet — the row is stored server-side. |
| **2** | `/chat` C2 | Pulse strip shows `recall n · [Open Memory]` | readout only (`chat.turn_meta`) | **Not a Memory UI.** One link. |
| **3** | C2 | Click **Open Memory** | `router → /memory?turn=current` | This screen opens with the this-turn filter on. |
| **4** | `/memory` | See the row in **This turn** + the result grid | `GET /api/v2/memory/` | Row: `fact · "EU plan is €4.8M" · score · created_at`. |
| **5** | `/memory` | Row → **Forget…** → confirm | `POST /api/v2/memory/forget` `{coord}` | Row disappears. Total decrements (or shows `—`). |
| **6** | `/memory` | Search the same text / **Run probe** | `POST /api/v2/memory/recall` `{query}` | **Empty state:** `No memories match "‹query›"`. |
| **7** | `/memory` | WM / LTM tiles | — (no count API) | Still `—`. Forgetting does not fake a count. |

---

## 5. Open record drawer (UI-M-01)

Trigger: **Open record** or row open. Right-side drawer over this workspace.

```
┌─ RECORD ────────────────────────────────┐
│  coord     ‹coord | —›                  │
│  kind      ‹kind | untyped›             │
│  score     ‹score | —›                  │
│  created   ‹created_at | —›             │
│  tags      ‹tags | (none)›              │
│  text      ‹content›                    │
│                                        │
│  [Copy]  [Forget…]           [Close]    │
└────────────────────────────────────────┘
```

No derived fields. Missing server fields render `—`, not a default.

---

## 6. Forget / Remember confirm (UI-M-03)

| Item | Forget | Remember |
|---|---|---|
| Title | “Forget this memory?” | “Remember this?” |
| Body | “This removes the stored record. It cannot be undone.” | “Store this text as a memory.” |
| Field | — | `text` (textarea, required) |
| Cancel | “Cancel” | “Cancel” |
| Confirm | “Forget” (destructive) | “Remember” |
| Call | `POST /api/v2/memory/forget` `{coord}` | `POST /api/v2/memory/remember` `{text}` |
| No coord | Button disabled: “This record has no coord and cannot be forgotten.” | — |
| Fail | “Forget did not finish. Nothing was changed.” | “Remember did not finish. Nothing was stored.” |

---

## 7. States

| State | Verbatim / behavior |
|---|---|
| empty (no search) | “No Memories Found” / “Start chatting with the agent to create memories.” |
| empty (search) | `No memories match "‹query›"` |
| empty (this turn) | “Nothing recalled this turn.” |
| loading | “Loading memories…” |
| error (list) | “Memories could not be loaded. Retry, or check that the memory service is reachable.” |
| error (recall) | “Recall did not finish. Nothing was changed.” |
| error (remember) | “Remember did not finish. Nothing was stored.” |
| error (forget) | “Forget did not finish. Nothing was changed.” |
| offline | “Memory actions are unavailable offline.” |
| count unknown | Total shows `—` (never `0`) |
| **WM/LTM no count API** | Tiles show `—` (label GATED). Never `0`, never a fabricated number. |

---

## 8. Navigation

| In | Out |
|---|---|
| Left rail **Memory** | ← Back to chat (`/chat`) |
| C2 **Open Memory** → `?turn=current` | Open record drawer (UI-M-01) |
| ⋮ **Open Memory** | Forget / Remember confirm (UI-M-03) |
| ⌘K “Memory” | — |

Canvas surfaces are UI-X-01…UI-X-08 only — **no Memory tab** (`SOMA-UI-IA-001` §2.4).
C2 is **not** a Memory UI (`UI-S-07` C2 — readout + Open Memory link only).

---

## 9. Honesty

- Counts and scores are store/API values. `—` when absent.
- **WM / LTM have no count API — always `—` / GATED.**
- Kind/type only from the server. Missing kind renders `untyped`.
- Tags empty if the server omits them — never padded.
- Never show a model id for an unbound role.
- No fake counts, no fake charts, no storage-used invention.
- Forgetting is destructive and confirmed; a failed call changes nothing.
- C2’s `recall n` is a chat-turn readout — it never renders as a Memory panel.

---

## 10. Source map

| Source | Role |
|---|---|
| `webui/src/views/soma-memory-view.ts` | Live list/recall/forget — the single Memory view |
| `GET /api/v2/memory/` | List + `total` |
| `POST /api/v2/memory/recall` | Search / probe (`{query}`; server `top_k`) |
| `POST /api/v2/memory/forget` | Forget `{coord}` |
| `POST /api/v2/memory/remember` | Remember `{text}` (via chat/tools or this screen) |
| `SOMA-UI-IA-001.md` §2.3–2.4 | C2 is readout-only · Memory never on canvas |
| `SOMA-UI-CATALOG-001.md` §3 | Real memory endpoints · WM/LTM no count API |

End of Document
