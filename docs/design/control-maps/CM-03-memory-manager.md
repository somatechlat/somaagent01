# CM-03 — Memory Manager Control Map

## Document Control

| Field | Value |
|---|---|
| Document Title | Control Map — Memory Manager (search / remember / forget) |
| Document Identifier | SOMA-UI-CM-03 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | SomaTech Engineering (soma-ui-engineer) |
| Classification | Internal |
| ISO Reference | ISO 9241-210:2019 |
| Next Review | 2027-01-13 |
| Related | `SOMA-UI-BINDINGS-001.md` §2 · `UI-S-04-memory.md` · `SOMA-UI-NAV-001.md` §3 · `SOMA-UI-IA-001.md` |
| Live sources | `webui/src/views/soma-memory-view.ts` |
| Route | `/memory` — **one home** (no canvas Memory tab, no second surface) |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | soma-ui-engineer | Exhaustive Memory Manager control map incl. remember/forget/search/export and honesty gates for WM/LTM counts. |

---

## 1. ASCII wireframe

```
┌─ Memory  (/memory only) ──────────────────────────────────────────────────────────────────────┐
│ M-00 Back to chat                                                                               │
│ M-01 [Search recall…]  M-02 [Search]   M-03 filter chips: all | wm | ltm | this-turn           │
│ M-04 sort ▾              M-05 [Remember…] toggle   M-06 [Export]   M-07 [Refresh]              │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ M-10 dashboard tiles: Total  M-11 WM  M-12 LTM  M-13 last write   M-14 brain ●                │
│     (WM/LTM render `—` until server reports; never invent 0)                                   │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ M-20 memory row                                                                                 │
│     ▣ 2026-10-13 09:41  text: "…"  score .91  source · coord 0x3f…                             │
│     M-20a [Open]   M-20b [Copy]   M-20c [Forget/Delete]                                       │
│ M-21 detail drawer (fields already on the row)                                                  │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ M-30 Remember form (when open)                                                                  │
│    M-31 textarea #remember-text     M-32 [Save to Brain]   M-33 [Cancel]                       │
│ M-34 Probe row: M-35 query  → recall live · scores + provenance   M-36 [Run probe]             │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Control map

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| M-00 | Back | link | `window.location.href = '/chat'` | default | — | `link` “Back to chat” | LIVE |
| M-01 | Search recall | input.search | Enter → `POST /api/v2/memory/recall` `{query}` | empty, focus, filled, loading | — | `searchbox` placeholder “Search recall…” | LIVE |
| M-02 | Search button | button | `_performSearch` → `POST /api/v2/memory/recall` | default, busy | — | `button` | LIVE |
| M-03a | Filter all | chip | client filter over server rows | active, inactive | — | `button` / `radio` in group | LIVE |
| M-03b | Filter WM | chip | client filter when `store` present | active, inactive | Server may omit `store` → chip filtered only when field exists | same | GATED (honest filter) |
| M-03c | Filter LTM | chip | same | active, inactive | same | same | GATED (honest filter) |
| M-03d | This-turn filter / clear | chip/button | filter over hits already in `chat.turn_meta.memory_hits` or loaded rows | active, inactive | No separate turn API — filter is local over known hits | `button` | GATED |
| M-04 | Sort | select | client sort over loaded rows | default | — | `combobox` “Sort memories” | LIVE |
| M-05 | Remember… toggle | button | local `_rememberOpen` | open, closed (`aria-expanded`) | — | `button` aria-expanded | LIVE |
| M-06 | Export JSON | button | client Blob of loaded rows | default | — | `button` | LIVE |
| M-07 | Refresh | button | `GET /api/v2/memory/` | default, busy, error | — | `button` | LIVE |
| M-10 | Total memories stat | stat | `response.total` from `GET /memory/` | number or `—` | Server not reporting → `—` (never fake 0) | labelled stat | LIVE |
| M-11 | WM count tile | stat | — | `—` | No WM/LTM count field on `GET /memory/` or `POST /memory/recall` | tile label + `—` | GATED |
| M-12 | LTM count tile | stat | — | `—` | same | same | GATED |
| M-13 | Last write | readout | latest `created_at` on loaded rows | default / `—` | — | text | LIVE |
| M-14 | Brain connected chip | status-dot | brain diagnostics | ok, degraded, error | — | `img`/status | LIVE |
| M-20 | Memory row | list-row | `GET /memory/` `{memories[{text, coord, score, store, created_at, content?, kind?}], total, tenant_id}` | loading, empty, error, populated | — | `listitem` | LIVE |
| M-20a | Open record | button | local drawer over loaded hit | default | — | `button` “Open” | LIVE |
| M-20b | Copy | button | `navigator.clipboard` | default | — | `button` title “Copy” | LIVE |
| M-20c | Forget / Delete | button | `POST /api/v2/memory/forget` `{coord}` (prefer body over `DELETE /memory/{coord}`) | default, confirm, busy, error | No `coord` on row → disabled + “Cannot delete memory without coord” | `button` title “Delete” | LIVE |
| M-21 | Detail drawer | modal | local over row fields | open, closed | — | `dialog` focus trap | LIVE |
| M-22 | Export filename note | readout | — | default | — | explains client-side export | LIVE |
| M-23 | Error state + retry | button | reload `GET /memory/` | error | — | `alert` + `button` | LIVE |
| M-24 | Empty state | readout | — | empty | — | empty ≠ error copy | LIVE |
| M-25 | Load-failed flag banner | readout | `_loadFailed` | error | — | distinguishes empty vs error | LIVE |
| M-26 | Page source note | readout | — | empty | — | names `GET /memory/` | LIVE |
| M-30 | Remember form | form | — | open, closed | — | `form` aria-label “Remember” | LIVE |
| M-31 | Remember textarea | textarea | local draft `#remember-text` | empty, filled, error | — | labelled textbox | LIVE |
| M-32 | Save to Brain | button | `POST /api/v2/memory/save` `{text, kind, salience}` | default, busy, error | Brain down → fail closed with visible error (never silent) | `button` | LIVE |
| M-33 | Cancel remember | button | local close + clear | default | — | `button` | LIVE |
| M-34 | Probe row | readout | — | idle, running, results | — | `region` “Probe” | LIVE |
| M-35 | Probe query | input.text | feeds `POST /memory/recall` | empty, filled | — | labelled textbox | LIVE |
| M-36 | Run probe | button | `POST /api/v2/memory/recall` | default, busy | — | `button` | LIVE |
| M-40 | Store layer label on row | readout | per-hit `store` when server sends it | default / `—` | Missing field → `—` | text | LIVE |
| M-41 | Score bar | readout | per-hit `score` | default / `—` | Missing score → `—` (no invented bar) | `meter` with text fallback | LIVE |
| M-42 | Provenance / coord chip | readout | per-hit `coord` | default | — | monospace text | LIVE |
| M-50 | Memory metrics (Kafka) | readout | `GET /api/v2/memory/metrics` | default / hidden | Not on this screen by design (Brain-only diagnostics surface) | — | PLANNED (elsewhere) |
| M-51 | Bulk forget | button | `POST /memory/forget` multi-coord | default | Not in UI today; target when multi-select ships | `button` | PLANNED |
| M-52 | Multi-select rows | input.checkbox | local selection | default | — | `checkbox` | PLANNED |
| M-53 | Kind tag editor | select | `POST /memory/save` kind / future patch | default | No kind-patch API → disabled with reason | `combobox` | PLANNED |
| M-54 | Salience slider | slider | `POST /memory/save` `{salience}` | default | — | `slider` valuetext | PLANNED |
| M-55 | Pin / unpin | button | future memory API | default | No pin API → “Pin needs a memory metadata API.” | `button` | PLANNED |
| M-56 | Cross-link to chat turn | link | navigate `/chat/{id}` when `conversation_id` known | default | hidden when id unknown | `link` | PLANNED |

---

## 3. States

| State | Verbatim / behavior |
|---|---|
| loading | “Loading memories…” (no fake counts while loading) |
| empty | “No memories stored.” + `GET /memory/` source note |
| error | “Memory list failed.” + failed request + Retry |
| denied | “You need `memory:read` to view memories.” |
| forget fail | visible error on the row; row stays until server acks `{forgotten, coord, memory_id}` |
| brain down (save) | fail closed; form keeps draft; error visible |

---

## 4. Honesty notes

1. **Anti-triplication:** Chat C2 is readout + route link only. Canvas has **no** Memory tab. Cognitive `memory_stats` is Brain-only.
2. WM/LTM tiles render `—` until an API reports them. Never invent 0.
3. Layer filter is a client filter only when the server sent `store` on hits.
4. This-turn filter has no separate API; it filters hits already received (`chat.turn_meta.memory_hits`) or loaded rows.
5. Export is a client Blob of **loaded** rows only — not a server archive claim.
6. Empty ≠ error (`_loadFailed`).

---

## 5. Source map

| Source | Role |
|---|---|
| `webui/src/views/soma-memory-view.ts` | All live controls M-00…M-36 |
| `admin/memory/api/memory.py` | `GET /memory/` · `POST /memory/recall` · `POST /memory/save` · `POST /memory/forget` · `GET /memory/metrics` |
| `docs/design/mockups/UI-S-04-memory.md` | Screen mockup |
| `SOMA-UI-BINDINGS-001.md` §2 | Click-path bindings |

End of Document
