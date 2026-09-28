# UI-S-13 — Version rail & diff

Screen UI-S-13 · Facet: Capsule · Route: NEW (not present in `webui/src/main.ts` today).
Source view per `SOMA-UI-IDREG-001.md`: NEW. Also reachable from the chrome version chip
(UI-C-003) as a UI-M-01 drawer preview.

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  Memory  Body  Governance ──────────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Version rail & diff [1]                           │ SURFACES x8             │
│  Chat    │ ┌──────────────┐ ┌──────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule*│ │ VERSION RAIL │ │ DIFF [4]                             │  │ [Editor][Debug][Capsule]│
│  Module  │ │ [2]          │ │  compare ‹version.a› → ‹version.b›   │  │ [Brain][Desktop†] †GATED│
│  Platform│ │ ‹v› ‹ts› [x] │ │  ┌────────────────────────────────┐  │  │                         │
│  Ops     │ │ ‹v› ‹ts› [ ] │ │  │ - ‹removed.line›               │  │  │                         │
│  Settings│ │ ‹v› ‹ts› [ ] │ │  │ + ‹added.line›                 │  │  │                         │
│  │ │ ‹v› ‹ts› [ ] │ │  │ ~ ‹changed.line›               │  │  │                         │
│          │ │ (scroll)     │ │  └────────────────────────────────┘  │  │                         │
│          │ │ COMPARE [3]  │ │ [ Restore this version ] [5]         │  │                         │
│          │ │ a ‹v ▾│ b ‹v ▾│ │ author ‹user.name› · ‹ts›           │  │                         │
│          │ └──────────────┘ └──────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Version rail) | Screen shell. |
| 2 | UI-C-080 | Version list | Rows `‹version›` + `‹ts›` + author; selection marks the compare side. |
| 3 | UI-C-081 | Compare selectors (a / b) | Two version picks bound to the diff pane. |
| 4 | UI-C-082 | Diff viewer | Read-only line diff; `-` / `+` / `~` markers only. |
| 5 | UI-A-036 | Restore this version | DESTRUCTIVE — always opens UI-M-03. |

## 3. State variants

- **loading** — Rail skeleton rows; diff pane verbatim: "Loading versions…"
- **empty** — `UI-C-023` verbatim: "No published versions yet. Publish a version from the capsule editor."
  Diff pane with nothing selected verbatim: "Select two versions to compare."
- **error** — `UI-C-024` verbatim: "Version history could not be loaded. Retry, or check that the
  somaAgent01 API is reachable." Diff failure verbatim: "Diff could not be computed for these versions."
- **permission-denied** — Restore disabled with inline reason "Restore requires the capsule-editor role."
  Rail and diff remain readable; `UI-C-025` verbatim:
  "You do not have permission to restore versions. Ask a platform admin for the capsule-editor role."
- **offline** — Rail shows last cached page ("Showing the last synced page."); Restore disabled
  with reason "Restore is unavailable offline."

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| UI-A-036 Restore this version | UI-M-03 Dialog | "Restore ‹version.a›? A new version is created; history is kept." Cancel / Restore. |
| Chrome version chip (UI-C-003) entry | UI-M-01 Drawer (420px) | Compact rail; link to this full screen. ESC closes, focus trap. |
| — | UI-M-02 | Not used by this screen. |

## 5. Honesty notes

Version identifiers, timestamps and authors are store placeholders. Diff lines are shape markers
(`‹added.line›`) — no fabricated document content.

End of Document
