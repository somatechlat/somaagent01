# UI-S-09 — Conversation export

Screen UI-S-09 · Facet: Chat · Route: NEW (not present in `webui/src/main.ts` today).
Source view per `SOMA-UI-IDREG-001.md`: NEW.

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  Memory  Body  Governance ──────────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Conversation export [1]                          │ SURFACES x8             │
│  Chat *  │ ┌────────────────────────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule │ │ SOURCE  ‹conversation.title›  ·  ‹message.count› msgs │  │ [Editor][Debug][Capsule]│
│  Module  │ │ FORMAT [2]  ( JSON ▾ )   SCOPE [3] ( whole ▾ )         │  │ [Brain][Desktop†] †GATED│
│  Platform│ │ REDACTION [4]                                           │  │                         │
│  Ops     │ │  [x] mask secrets     [x] strip tool args               │  │                         │
│  Settings│ │  [ ] include traces   [ ] include attachments           │  │                         │
│          │ │ PREVIEW [5]                                             │  │                         │
│          │ │ ┌────────────────────────────────────────────────────┐ │  │                         │
│          │ │ │ { … redacted export preview … }                    │ │  │                         │
│          │ │ └────────────────────────────────────────────────────┘ │  │                         │
│          │ │ [ Start export ] [6]    [ Download ] [7]               │  │                         │
│          │ │ status: ‹export.status›   file: ‹export.filename›     │  │                         │
│          │ └────────────────────────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Export) | Screen shell; source conversation is fixed by entry point. |
| 2 | UI-C-065 | Format select | Options only for formats the exporter actually writes. |
| 3 | UI-C-066 | Scope select | Whole conversation / date range / selection, as supported. |
| 4 | UI-C-067 | Redaction toggles | "mask secrets" defaults ON and cannot be turned off when secrets are detected (reason inline: "Secrets were detected in this conversation."). |
| 5 | UI-C-068 | Export preview | READ-ONLY redacted preview; secrets rendered `sk-••••••••aBcD`. |
| 6 | UI-A-027 | Start export | Produces `‹export.status›` → `‹export.filename›`. |
| 7 | UI-A-028 | Download export | Enabled only when status is ready. |

## 3. State variants

- **loading** — Preview skeleton. Verbatim label: "Preparing export preview…"
- **empty** — Verbatim: "This conversation has no messages to export."
  Preview verbatim: "Nothing to preview yet."
- **error** — `UI-C-024` verbatim: "Export could not be prepared. Retry, or check that the
  somaAgent01 API is reachable." Download failure verbatim: "Download failed. Start the export again."
- **permission-denied** — Start/Download disabled; `UI-C-025` verbatim:
  "You do not have permission to export this conversation. Ask a platform admin for the member role."
- **offline** — Start/Download disabled with inline reason "Export is unavailable offline."
  Preview keeps the last prepared copy with note "Showing the last prepared preview."

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| Start export with "include attachments" on | UI-M-03 Dialog | "Attachments may contain secrets. Export them anyway?" Cancel / Export. |
| Large export ready | UI-M-01 Drawer (420px) | File list + per-file download; ESC closes, focus trap. |
| — | UI-M-02 | Not used by this screen. |

## 5. Honesty notes

Preview content is a shape illustration only. Export filenames, sizes and message counts are
placeholders. Secrets never render as values — masked plus "rotate in Vault".

End of Document
