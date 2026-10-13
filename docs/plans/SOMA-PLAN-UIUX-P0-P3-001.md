# SOMA-PLAN-UIUX-P0-P3-001 — UI/UX remediation plan (operator wave 2026-10-13)

## Document Control

| Field | Value |
|---|---|
| Document Title | SOMA-PLAN-UIUX-P0-P3-001 — UI/UX remediation plan |
| Document Identifier | SOMA-PLAN-UIUX-P0-P3-001 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | soma-ui-engineer |
| Classification | Internal |
| Related | `docs/reports/SOMA-RPT-UIUX-FULL-AUDIT-001.md`, `SOMA-STD-UIUX-001`, `SOMA-UI-IA-001`, `SOMA-UI-SKINS-001`, `SOMA-UI-CONTROL-MAPS-001` |
| Law | no shims · no fakes · honest GATED · `--skin-*` only · `t()` I18N · no emojis |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | soma-ui-engineer | P0–P3 plan keyed to FULL-AUDIT findings. Chat bubbles first. |

---

## P0 — Ship now (this code wave)

### P0-1 · Chat bubble contrast

| ID | Change | File | Acceptance |
|---|---|---|---|
| P0-1a | `.action-btn`, `.confidence-wrap`, footer `.time` → `--skin-color-text-secondary` (AA on glass) | `soma-message.ts` | 4.5:1 min for body/controls |
| P0-1b | `.stopped-badge` → solid/soft fill + AA text (not bare warning-on-glass) | `soma-message.ts` | readable in light + dark |
| P0-1c | `md-h1` gradient gets solid `color` fallback before `transparent` clip | `soma-message.ts` | visible if `background-clip` fails |
| P0-1d | Inline `md-code` color ≠ `--skin-color-text-link` (accent alias); use `--skin-color-text-primary` + muted border | `soma-message.ts` | code readable on both bubbles |

### P0-2 · Chat bubble icons

| ID | Change | File | Acceptance |
|---|---|---|---|
| P0-2a | Model chip `memory` → `smart_toy` | `soma-message.ts` | no Memory product glyph collision |
| P0-2b | Tools expander `play_arrow` → `expand_more` | `soma-message.ts` | expand/collapse semantics |

### P0-3 · Chat bubble actions (real handlers only)

| ID | Change | File | Acceptance |
|---|---|---|---|
| P0-3a | Copy failure → `pushToast` error (never silent `console.warn`) | `soma-message.ts` | HR-02 visible failure |
| P0-3b | **Retry** on assistant bubbles — re-sends the preceding user message over live WS `chat.message` | `soma-message.ts` + `soma-chat.ts` | real handler; no fake regenerate API |
| P0-3c | **Edit** on user bubbles — inline edit + re-send via live WS | `soma-message.ts` + `soma-chat.ts` | real handler |
| P0-3d | Actions visible on touch (`@media (hover: none)`) and `:focus-within` | `soma-message.ts` | A-04 |
| P0-3e | `messageId` property on `soma-message`; parent correlation | both | A-05 |
| P0-3f | `t()` labels for all action chrome; en/es parity | `i18n/en.json`, `es.json` | HR-23 |

### P0-4 · File browser honesty (minimal)

| ID | Change | File | Acceptance |
|---|---|---|---|
| P0-4a | Paging loop already collects `?page=` up to `LIST_MAX_PAGES` with truncation banner — keep; add "load more" only in P1 | `soma-file-manager.ts:728-757` | no fake "page 1 only" claim |
| P0-4b | Search hint: "searches the loaded list only" (client filter; no server search API) | `soma-file-manager.ts` | F-02 honest |

**Not in P0 (do not sneak):** deleting routes, skin pack redesign, full I18N of every screen.

---

## P1 — Next wave

| ID | Theme | Change | Acceptance |
|---|---|---|---|
| P1-1 | Modularization | Replace `soma-chat.ts:603-935` hex palette with `--skin-*` (or shared `.mb-*` status classes) | `check-skin-literals` baseline shrinks |
| P1-2 | Modularization | Bubble/file/brain controls reuse `moduleBase` buttons; kill private `.btn`/`.icon-btn` forks | HR-18/HR-20 |
| P1-3 | Motion | All transitions bind `--skin-motion-*`; no raw `0.2s` / `all` in components | T-01 |
| P1-4 | Effects | Add `--skin-effect-glow/scrim/overlay-blur/shimmer` to vocabulary + `tokens.css` + packs | T-02 · HR-22 |
| P1-5 | File browser | Real page navigation (`?page=`) + `Intl.DateTimeFormat` dates | F-01/F-06 |
| P1-6 | File browser | I18N chrome | HR-23 |
| P1-7 | Brain admin | **Remove duplicate connection form** from `soma-brain-manager` (keep read-only status); Settings owns writes | B-01 · single-home |
| P1-8 | Naming | User-visible "Capsule" surface label → product language; routes untouched | HR-09 |
| P1-9 | Bubble I18N | remaining tool/attachment strings | A-06 |
| P1-10 | Chat settings | `_knobCapsuleId` feed path proof from live agent row | B-04 |

---

## P2 — Polish

| ID | Change |
|---|---|
| P2-1 | `md-h1` forced-colors / clip edge cases (C-05) |
| P2-2 | Glass bubble declared over solid page token (C-08) |
| P2-3 | File select-all / bulk ops (F-05) |
| P2-4 | Upload tray retry truth vs control map (F-07) |
| P2-5 | `module-base` autofill `5000s` hack → named token or comment + review (T-04) |
| P2-6 | Entry animation tokens (`--skin-motion-enter`) shared (T-03) |
| P2-7 | Sleep config vs sleep status split (B-03) |
| P2-8 | Attachment/recall icon review (I-03) |

---

## P3 — Structural

| ID | Change |
|---|---|
| P3-1 | Full `t()` coverage across all views/components (A-4 gate green without exemptions) |
| P3-2 | Skin pack effect domain + pack-only retheme proof (HR-21) |
| P3-3 | Control-map / IDREG sync after P0–P2 (HR-41…HR-43) |
| P3-4 | Playwright human session on live services for bubble actions, file browse→download, Brain knobs save (A-9) |
| P3-5 | `tokens.css` single declaration block (M-08) |
| P3-6 | `--skin-color-text-link` real link hue (not accent alias) (M-09) |

---

## Execution order (this wave)

```
P0-1 contrast ─┐
P0-2 icons    ─┼─► soma-message.ts ─► i18n keys ─► soma-chat.ts action handlers
P0-3 actions  ─┘                                      │
P0-4 file honesty ─────────────────────────────────────┴─► gates (tsc · skin · smoke)
```

## Gates (every wave)

| Gate | Command |
|---|---|
| Types | `bun node_modules/typescript/bin/tsc --noEmit` (or `npx tsc` when node is healthy) |
| Build | `npx vite build` |
| Skin | `node scripts/check-skin-literals.mjs` — **zero new debt** |
| I18N | en/es key parity; no new literal English in touched files |
| Honesty | every new control has a real handler or GATED+reason |
| Chat | send + receive still works on live WS |

## Out of scope (explicit)

- No route deletions without proof.
- No `--update-baseline` to hide new literals (HR-40).
- No mocks/fakes/shims in production paths.
- No React/Alpine.
- No emoji.

End of plan.
