# CM-09 — Command Palette Control Map (PLANNED)

## Document Control

| Field | Value |
|---|---|
| Document Title | Control Map — Command Palette (M-021 `soma-command-palette`) |
| Document Identifier | SOMA-UI-CM-09 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | SomaTech Engineering (soma-ui-engineer) |
| Classification | Internal |
| ISO Reference | ISO 9241-210:2019 |
| Next Review | 2027-01-13 |
| Related | `SOMA-UI-AGENT-FRONTEND-MASTER-001.md` §3.6 · `SOMA-UI-MODULE-CATALOG-001.md` M-021 · `SOMA-UI-NAV-001.md` |
| Status law | **All controls PLANNED.** Real actions only (routes, skins, chat commands, files). No fake rows. |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | soma-ui-engineer | Command palette control map. Every planned row names a real execute target. |

---

## 1. ASCII wireframe

```
⌘K / Ctrl-K
┌────────────────────────────────────────────────────────────────┐
│ P-01  > open memory                                  (search)  │
├────────────────────────────────────────────────────────────────┤
│ P-10  route   Open Memory                    → /memory          │
│ P-11  route   Open Settings                  → /settings        │
│ P-12  route   Open Settings › Models         → /settings/models │
│ P-13  route   Open Settings › Channels       → /settings/channels │
│ P-14  route   Open File Manager              → UI-X-01 / /files │
│ P-15  action  New chat                        → POST /chat/conversations │
│ P-16  action  Export conversation            → client Blob      │
│ P-17  action  Apply skin · soma brand        → skin-applier     │
│ P-18  action  Toggle surface rail            → local            │
│ P-19  file    Open file ‹name›               → UI-X-04          │
│ P-20  conversation  Switch to ‹title›        → load messages    │
│ P-21  action  Start voice chat               → /voice/chat      │
│ P-22  action  Open Cognitive                 → /cognitive       │
├────────────────────────────────────────────────────────────────┤
│ P-30 footer: navigate ↑↓ · Enter execute · Esc close            │
└────────────────────────────────────────────────────────────────┘
```

---

## 2. Control map

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| P-00 | Palette host | modal | `soma-command-palette` in shell `overlays` slot | closed, open | Not shipped in `webui/` yet — module catalog M-021 | `dialog` role, focus trap | PLANNED |
| P-01 | Query input | input.search | `soma-palette-query` `{query}` → provider `search()` | empty, typing, results | — | `combobox` + `listbox` | PLANNED |
| P-02 | Open shortcut (⌘K / Ctrl-K) | key | local key handler | default | — | documented shortcut | PLANNED |
| P-03 | Close (Esc / backdrop) | key/button | `soma-palette-close` | open | — | Esc closes | PLANNED |
| P-10 | Open Memory | list-row | `execute()` → navigate `/memory` (**single home**) | default | — | `option` | PLANNED |
| P-11 | Open Settings | list-row | navigate `/settings` | default | — | `option` | PLANNED |
| P-12 | Open Settings › Models | list-row | navigate `/settings/models` | default | — | `option` | PLANNED |
| P-13 | Open Settings › Channels | list-row | navigate `/settings/channels` | default | — | `option` | PLANNED |
| P-14 | Open File Manager | list-row | select UI-X-01 / planned `/files` | default | — | `option` | PLANNED |
| P-15 | New chat | list-row | `POST /chat/conversations` | default, busy | — | `option` | PLANNED |
| P-16 | Export conversation | list-row | `GET /chat/conversations/{id}/messages` + Blob | default | Disabled when no active conversation | `option` | PLANNED |
| P-17 | Apply skin | list-row | skin-applier apply pack id | default, busy | — | `option` | PLANNED |
| P-18 | Toggle surface rail | list-row | local `_toggleRightPanel` | default | — | `option` | PLANNED |
| P-19 | Open file (provider) | list-row | file provider `search()` over filesv2 list → UI-X-04 | results, empty | — | `option` | PLANNED |
| P-20 | Switch conversation | list-row | conversation provider → load messages | results | — | `option` | PLANNED |
| P-21 | Start voice chat | list-row | navigate `/voice/chat` | default | — | `option` | PLANNED |
| P-22 | Open Cognitive | list-row | navigate `/cognitive` | default | — | `option` | PLANNED |
| P-23 | Run tool (if catalog allows) | list-row | tool execute API when exposed | default | Manual tool invoke not exposed → row omitted (never a dead action) | `option` | PLANNED |
| P-24 | Recent ids section | list-row | `recentIds` | default | — | `option` | PLANNED |
| P-25 | Provider error banner | readout | partial results | error | — | `alert` (partial results + banner) | PLANNED |
| P-26 | Empty results | readout | — | empty | — | text | PLANNED |
| P-30 | Footer key help | readout | — | always | — | text | PLANNED |

---

## 3. Provider contract (from module catalog)

| Provider kind | `search()` source | `execute()` target |
|---|---|---|
| route | static route table (CM-01/05/03/06 routes) | `soma-navigate` |
| action | static action list above | named handler (WS/REST/local as in Binding column) |
| file | `GET /api/v2/filesv2/` rows | open UI-X-04 |
| conversation | `GET /chat/conversations` | load thread |

**Law:** Memory/Settings entries navigate to their **single home**; no duplicate destinations.

---

## 4. Honesty notes

1. No decorative or “coming soon” rows. A row exists only if `execute()` is real.
2. If a provider fails, other providers still show + banner (partial results).
3. File and conversation providers fail to empty/error honestly — never invented recents.

---

## 5. Source map

| Source | Role |
|---|---|
| `SOMA-UI-MODULE-CATALOG-001.md` M-021 | Module contract |
| `SOMA-UI-AGENT-FRONTEND-MASTER-001.md` §3.6 | Wireframe + product intent |
| (pending) `webui/src/components/soma-command-palette.ts` | Implementation target |

End of Document
