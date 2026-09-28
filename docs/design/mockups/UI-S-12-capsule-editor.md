# UI-S-12 — Capsule editor

Screen UI-S-12 · Facet: Capsule · Route: `/workspace/:id`
Source view per `SOMA-UI-IDREG-001.md`: `saas-workspace` (`webui/src/views/saas-workspace.ts`).
Note: `webui/src/main.ts` routes only exact `/workspace` (`main.ts:396`); `/workspace/:id` is not
matched and falls through to the default `saas-chat` mount (`main.ts:467`). The register's source
view holds for the list screen; the per-id editor route is not implemented today.

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  Memory  Body  Governance ──────────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Capsule editor [1]                               │ SURFACES x8             │
│  Chat    │ ┌────────────────────────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule*│ │ ‹capsule.name›  v‹semver›  ‹lifecycle›   [dirty ‹›] [2]│  │ [Editor][Debug][Capsule]│
│  Module  │ │ TABS [3] ( Soul )( Body )( Hands )( Memory )( Governance)│  │ [Brain][Desktop†] †GATED│
│  Platform│ │ ┌────────────────────────────────────────────────────┐ │  │                         │
│  Ops     │ │ │ EDITOR [4]                                         │ │  │                         │
│  Settings│ │ │ ‹capsule.document›                                 │ │  │                         │
│          │ │ │ (structured / YAML editor for the active tab)      │ │  │                         │
│          │ │ └────────────────────────────────────────────────────┘ │  │                         │
│          │ │ VALIDATION [5]  ‹validation.summary›                   │  │                         │
│          │ │  ‹error.path›  ‹error.message›                         │  │                         │
│          │ │ [ Save draft ] [6]  [ Diff preview ] [7]  [ Publish ] [8]│  │                         │
│          │ └────────────────────────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Capsule editor) | Screen shell. |
| 2 | UI-C-075 | Dirty-state indicator | Read-only chip; shows unsaved state of the draft. |
| 3 | UI-C-076 | Section tabs | Soul / Body / Hands / Memory / Governance — same sections the capsule stores. |
| 4 | UI-C-077 | Document editor | Structured editor bound to `‹capsule.document›` for the active tab. |
| 5 | UI-C-078 | Validation panel | Read-only list of `‹error.path›` / `‹error.message›` from the validator. |
| 6 | UI-A-033 | Save draft | Saves without publishing a new version. |
| 7 | UI-C-079 | Diff preview toggle | Opens UI-S-13 content in a UI-M-01 drawer. |
| 8 | UI-A-034 | Publish version | Writes a new version; disabled while validation errors exist (reason inline: "Fix validation errors before publishing."). |

## 3. State variants

- **loading** — Editor skeleton. Verbatim label: "Loading capsule…"
- **empty** — New capsule draft; editor placeholder (verbatim):
  "This section is empty. Add the fields this capsule needs."
  Validation panel verbatim: "No validation results yet."
- **error** — `UI-C-024` verbatim: "Capsule could not be loaded. It may have been deleted."
  Save failure verbatim: "Draft was not saved. Your edits are still here — try again."
  Validation failure verbatim: "Validation could not run. Publishing is blocked until it can."
- **permission-denied** — Editor read-only; Publish/Save disabled with inline reason
  "Editing requires the capsule-editor role." `UI-C-025` verbatim:
  "You do not have permission to edit this capsule. Ask a platform admin for the capsule-editor role."
- **offline** — Editor stays open for local edits; Save/Publish disabled with inline reason
  "Saving is unavailable offline." Chrome offline banner shown.

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| UI-C-079 Diff preview | UI-M-01 Drawer (420px) | Compact diff against last published; ESC closes, focus trap. |
| UI-A-034 Publish | UI-M-03 Dialog | "Publish a new version of ‹capsule.name›?" Cancel / Publish. |
| UI-A-035 Discard draft | UI-M-03 Dialog | "Discard unsaved draft edits?" Cancel / Discard. |
| — | UI-M-02 | Not used by this screen. |

## 5. Honesty notes

`‹capsule.document›`, validation messages and dirty state are store placeholders. The full
version rail is UI-S-13 — this screen only previews a diff.

End of Document
