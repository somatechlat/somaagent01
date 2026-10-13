# SOMA-RPT-UIUX-FULL-AUDIT-001 — Full UI/UX review (operator wave 2026-10-13)

## Document Control

| Field | Value |
|---|---|
| Document Title | SOMA-RPT-UIUX-FULL-AUDIT-001 — Full UI/UX review |
| Document Identifier | SOMA-RPT-UIUX-FULL-AUDIT-001 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | soma-ui-engineer |
| Classification | Internal |
| Scope | `webui/src/**` screens, controls, contrast, icons, handlers, transitions, modularization |
| Law | SOMA-STD-UIUX-001 · SOMA-LAW-SECURITY-001 · no shims · no fakes · honest GATED |
| Sources | `SOMA-STD-UIUX-001`, `SOMA-UI-IA-001`, `SOMA-UI-BINDINGS-001`, `SOMA-UI-NAV-001`, `SOMA-UI-SKINS-001`, `SOMA-UI-CONTROL-MAPS-001`, `SOMA-UI-MODULE-CATALOG-001`, `SOMA-UI-PROFILE-001`, `SOMA-UI-TOOLS-MARKETPLACE-001`, `SOMA-CHAT-UI-001`, `UI-X-01-files`, `UI-S-07`, live `webui/src` |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | soma-ui-engineer | Full audit against operator report items 1–5. Chat bubbles, modularization, Brain admin knobs, file browser, system-wide motion/effect tokens. file:line evidence. |

---

## 0. Verification snapshot (this wave)

| Check | Command | Result |
|---|---|---|
| TypeScript | `bun node_modules/typescript/bin/tsc --noEmit` (webui) | **PASS** (exit 0) |
| Skin literals | `node scripts/check-skin-literals.mjs` | **PASS** — 0 new debt files (3259 existing hits / 69 debt files in baseline) |
| Emojis in catalogs / soma-message | unicode emoji scan | **0 hits** |
| Product naming in `soma-message` / catalogs | `Capsule` as user copy | **0 hits** (code identifiers only) |
| Node runtime | `node`/`npx` on this host | **BROKEN** host-side (`libada.3.dylib`); use Bun for tsc. Not a webui defect. |

---

## 1. Operator item 1 — Chat message bubbles (P0)

**Surface:** `webui/src/components/soma-message.ts` (CH-12 / C2) consumed by `webui/src/views/soma-chat.ts:3264-3276`.

### 1.1 Contrast — FAIL (multiple WCAG AA breaks)

| # | Where | file:line | Problem | Severity |
|---|---|---|---|---|
| C-01 | Bubble action buttons | `soma-message.ts:904` `.action-btn { color: var(--skin-color-text-muted) }` | Light theme `#999999` on glass ≈ 2.9:1 — **fails WCAG AA (4.5:1)**. Dark `#8b8b8b` is borderline. | **P0** |
| C-02 | Confidence readout | `soma-message.ts:865` `.confidence-wrap { color: var(--skin-color-text-muted) }` | Same muted-on-glass failure. | **P0** |
| C-03 | Timestamp | `soma-message.ts` footer `.time` / `text-muted` family | Muted text on bubble surface fails AA for small text. | **P0** |
| C-04 | Stopped badge | `soma-message.ts:854` `color: var(--skin-color-warning)` (`#eab308` / `#f59e0b`) | Warning on light glass ≈ 2:1 — fails AA. Border mix does not fix text contrast. | **P0** |
| C-05 | `md-h1` gradient text | `soma-message.ts:213-218` `color: transparent` + `background-clip: text` | If clip unsupported or forced-colors mode, heading is invisible (no solid fallback color). | **P1** |
| C-06 | Inline `md-code` color token | `soma-message.ts:326` `color: var(--skin-color-text-link)` | `--skin-color-text-link` is aliased to `--platform-accent` (`tokens.css:497`) — the **same** value as the user-bubble background in both themes. User-bubble override exists (`:329-333`) but assistant inline code is accent-on-card (near-invisible hierarchy vs body). | **P1** |
| C-07 | User bubble markdown children | `soma-message.ts:221-224, 236-240, 248-249, 329-333, 419-421` | Most children correctly rebind to `accent-text`. Remaining risk: any unbound deep child (raw HTML the model emits) inherits assistant colors onto an accent fill. | **P1** |
| C-08 | Glass assistant bubble | `soma-message.ts:172` `background: var(--skin-glass-bg)` | `--skin-glass-bg` is 88% alpha (`tokens.css:463`). Over a non-solid page the effective contrast drifts. Acceptable if page is solid; not declared. | **P2** |

### 1.2 Icons — FAIL (wrong glyphs / product-name collision)

| # | Where | file:line | Problem | Fix |
|---|---|---|---|---|
| I-01 | Model chip | `soma-message.ts:1078` `>memory<` | Uses the **Memory** product glyph for "model". Collides with HR-09 product naming (Memory = the memory home). Operator: "icons wrong". | `smart_toy` (model) |
| I-02 | Tools expander chevron | `soma-message.ts:1221` `play_arrow` | Play triangle for expand/collapse — wrong semantic. A0 / Material pattern is `expand_more` rotated, or `chevron_right`. | `expand_more` |
| I-03 | Recall chip | `soma-message.ts:1084` `psychology` | Acceptable for recall, but sits next to the Memory product surface; `search` / `database` is clearer for "hits recalled". Keep or swap — low severity. | P2 |
| I-04 | CTX chip | `soma-message.ts:1093` `data_object` | Acceptable. | — |
| I-05 | Attachment icons | `utils/file-icons.ts` + `soma-message.ts:1135+` | Material Symbols via shared `attachmentIcon` — **correct** (HR-27). | keep |
| I-06 | Icon font load | `styles/material-symbols.css` + `main.ts:19` + `index.html:8` | Local woff2 only (CSP-safe). **Correct.** If font missing, icons render as ligature text — needs a load-fail note in ops docs. | P2 |

### 1.3 Bubble actions / functionality — FAIL (incomplete + silent failure)

| # | Where | file:line | Problem | Severity |
|---|---|---|---|---|
| A-01 | Only Copy exists | `soma-message.ts:1269-1282` | Design (`SOMA-CHAT-UI-001:150-151`) requires **Copy + Retry** on agent bubbles. Control map CH-35 Regenerate is PLANNED. Operator: "actions/functionality wrong". | **P0** |
| A-02 | Copy failure is silent | `soma-message.ts:1034-1036` `console.warn` only | HR-02: failure must be a **visible error**. Clipboard reject leaves the user thinking copy worked. | **P0** |
| A-03 | No Edit on user bubbles | `soma-message.ts` | Operator asked for copy/edit/etc. Design gives user bubble "✓" only; edit-and-resend is the real handler that fits the live WS (`chat.message`). | **P1** |
| A-04 | Actions hover-only | `soma-message.ts:883-894` `opacity: 0` until `:hover` / `:focus-within` | Touch devices have no hover — actions are unreachable. Keyboard is OK (`:focus-within`) but discoverability is poor. | **P0** |
| A-05 | No `messageId` on the bubble | `soma-chat.ts:3266-3276` | Parent cannot correlate retry/edit to a row. | **P0** (needed for A-01/A-03) |
| A-06 | Hardcoded English in bubble chrome | `soma-message.ts` (`Copy`, `Copied`, `stopped`, `N tools`, `Preview unavailable`, `Download`, `Not uploaded`) | HR-23 / A-4 I18N gate. | **P1** |
| A-07 | Tool count grammar | `soma-message.ts:1222` string concat `tool`/`tools` | Not `t()`; English-only. | P2 |

### 1.4 What is already correct (do not "fix")

- User vs assistant vs system bubble alignment and role attribute (`message-role`, not `role`) — `soma-message.ts:75-76, 137-144`.
- Code-block copy via delegated listener (`bindCodeCopy`) — correct pattern for `unsafeHTML` bodies (`:936-942`).
- Attachment media honesty: no `file_id` → "Not uploaded" / "Preview unavailable", never a broken frame (`:1184-1195`).
- `prefers-reduced-motion` block (`:122-135`).
- Streaming cursor + typing indicator (`:1239-1248`).
- Turn chips only render fields the server sent (`:1056-1065`) — HR-35.

---

## 2. Operator item 2 — System-wide standardization / modularization

### 2.1 Module CSS contract status

| Module | Role | Status |
|---|---|---|
| `styles/tokens.css` | `--skin-*` + `--platform-*` aliases | Present. Dual declaration blocks (`:11-114` and `:196-278`) re-declare spacing/type — **duplication debt**. |
| `styles/module-base.ts` | `.mb-*` | Present (182 lines). Contains `transition: background-color 5000s ease-in-out 0s` (`:94`) — autofill hack, not a skin motion token. |
| `styles/glass.ts` | `.glass-*` | Present (144 lines). Transitions are partially token-bound (`:26,61,83,119`). |
| `styles/density.ts` | `SPACE`/`RADIUS`/`TYPE` | Present (72 lines). |
| `skin-sdk/` | packs · validate · resolve · aliases | Present. Vocabulary is the token authority (`skin-sdk/tokens/vocabulary.ts`). |

### 2.2 Modularization gaps (file:line)

| # | Gap | Evidence | Severity |
|---|---|---|---|
| M-01 | **Chat view carries a private design system** | `soma-chat.ts:603-935` hardcodes `#FF4D00`, `#22c55e`, `#94A3B8`, `#34d399`, `#fbbf24`, `#f87171`, `#F59E0B`, `#FF7A3D`, `#10B981`, `#FFFFFF`, `#C4C4C4` | **P0** (HR-19 / baseline debt owner) |
| M-02 | Bubble chrome does not reuse `.mb-btn` | `soma-message.ts:896-918` redefines `.action-btn` instead of `class="mb-btn ghost"` | P1 |
| M-03 | File manager buttons | `soma-file-manager.ts` `.btn` / `.icon-btn` private classes | P1 |
| M-04 | Brain manager sliders/toggles | `soma-brain-manager.ts:354-516` private range/toggle CSS | P1 |
| M-05 | Settings somabrain toggles | `soma-settings-somabrain.ts:182-211` second copy of toggle CSS | P1 |
| M-06 | Transition tokens not uniformly used | `--skin-motion-*` exists (`tokens.css:559-562`) but components mix raw `0.2s` / `all` transitions | **P1** (operator item 5) |
| M-07 | Effect tokens missing | No `--skin-effect-*` vocabulary for glow / scrim / overlay blur shared across modals. `glass.ts` blur is local. | **P1** |
| M-08 | `tokens.css` double `:root` blocks | `:11-114` vs `:196-278` redefine the same family | P2 |
| M-09 | `--skin-color-text-link` = accent | `tokens.css:497` | P1 (see C-06) |

### 2.3 I18N modularization

- `soma-message.ts` (bubble), `soma-file-manager.ts` (browser), `soma-brain-manager.ts` (knobs) all hardcode English chrome. Catalog has 108 keys and **zero** `message.*` keys. en/es are at parity (108/108) — good — but coverage is far below surface count.

---

## 3. Operator item 3 — SomaBrain admin / agent settings / knobs

**Files:** `views/soma-settings-somabrain.ts` (772) · `components/soma-brain-manager.ts` (1480) · `views/soma-settings.ts` · `components/soma-chat-settings.ts`.

### 3.1 Correct (keep)

| Control | Binding | Evidence |
|---|---|---|
| Connection URL / namespace / retention / sleep / consolidation | `GET/PUT /core/settings/somabrain` | `soma-settings-somabrain.ts:52, 544-628` |
| `canEdit` GATED on `system:configure` | `DISABLED_REASON` | `:48-50, 340` |
| Cognitive knobs honesty note | "Cognitive knobs are per-agent on /cognitive" | `:734-735` |
| Brain-settings gap note | "editors are omitted rather than invented" | `:740-742` |
| Neuromodulator baseline via capsule PATCH | `PATCH /agents/{agentId}/capsule` | `soma-brain-manager.ts:10, 814-843` |
| IQ knobs via AgentIQ PUT (not invented capsule body) | `PUT /core/agentiq/{capsuleId}` | `soma-brain-manager.ts:11-14, 889-891` |
| Neuromod clamp ranges mirror backend | `NEUROMOD_RANGES` | `:30-37` |
| Mode STD/DEV/TRN/ADM | live mode API | `:47-52` |

### 3.2 Incorrect / remove-or-fix

| # | Finding | file:line | Verdict |
|---|---|---|---|
| B-01 | **Connection knobs duplicated** — same URL/namespace/retention/sleep/consolidation rendered in `soma-settings-somabrain` **and** embedded again in `soma-brain-manager` (`SomabrainSettingsValues`, settings section) | both files | **Remove the duplicate editor from one home.** IA: Settings owns connection (`UI-S-56`). Brain manager should read-only show status, not a second write form. |
| B-02 | "Capsule" appears in Brain manager copy/comments and `soma-chat.ts:3284` surface label "Capsule" | `soma-brain-manager.ts` header, `soma-chat.ts:3284` | HR-09: user-visible **surface label** "Capsule" must become product language (Agent package / Hands) or stay internal-only. Control-map still lists Capsule as UI-X-06 — treat label as a naming fix, not a route delete. |
| B-03 | Sleep interval field claims "settings field only — not a Temporal schedule" (honest) but sits next to a Sleep status card that implies scheduling | `soma-settings-somabrain.ts:593-607` vs brain-manager sleep block | Keep the hint; split "retention/sleep config" from "sleep status" so the knob is not read as a scheduler. |
| B-04 | IQ knobs write path takes `capsuleId` from a local `_knobCapsuleId` in chat | `soma-chat.ts:1237` | Ensure this is sourced from the live agent row, never a hardcoded id. Audit of the feed path is P1. |
| B-05 | No `t()` on any of the above strings | both files | P1 I18N. |

**Rule applied:** do not delete a live route or a live write path without proof. B-01 removes a **duplicate form**, not the API binding.

---

## 4. Operator item 4 — File browser

**Files:** `components/soma-file-manager.ts` (1639) · `soma-file-manager-modal.ts` · `soma-file-preview.ts` · surface `UI-X-01` via `soma-right-panel`.

### 4.1 What works (LIVE)

| Capability | API | Evidence |
|---|---|---|
| List | `GET /api/v2/filesv2/?page=&per_page=` | `:718-743` |
| Empty vs error vs denied | `LoadStatus` + retry | `:68, 1333-1347` |
| Download signed URL | `GET /filesv2/{id}/download-url` | `:869+` |
| Upload | `POST /filesv2/upload` | `:803+` |
| Rename / move / delete (manage mode) | `PATCH` / `workroot/move` / `DELETE` | `:956, 1043, 1005` |
| Tree probe honest GATED | `GET /workroot/tree` | `:747-778` |
| Attach-to-chat (select mode) | event `soma-attach` | `:935` |

### 4.2 Broken / incorrect (operator: "needs a lot of work")

> **Code=truth note (re-read 2026-10-13):** `_loadFiles` in the working tree
> already pages `GET /filesv2/?page=&per_page=` until `total` is covered or
> `LIST_MAX_PAGES` (20) ceiling (`soma-file-manager.ts:728-757`) and shows an
> honest truncation banner (`:748-750, 1235-1236`). Earlier "always page=1"
> is **no longer true**. Remaining gaps below.

| # | Finding | file:line | Severity |
|---|---|---|---|
| F-01 | Multi-page ceiling truncates silently beyond 20 pages — banner exists, but no "load more" control | `:106, 747-751` | **P1** |
| F-02 | **Search is client-only** over the collected list — no server search (`GET /workroot/search` still NEW API). Must say so when `_filesTotal > _files.length` | `:703-710` | **P0** |
| F-03 | Mixed I18N — some keys exist (`files.searchFiles`…); row status lines still English (`showing X of Y`) | `:1464-1466` | **P1** (HR-23) |
| F-04 | Tree answered ≠ tree rendered — honest note but the probe UX reads like a broken tree | `:754-758` | P1 |
| F-05 | Row click opens preview; checkbox/keyboard OK — but no multi-select "select all" / bulk delete | `:1383-1469` | P2 |
| F-06 | `updated_at.slice(0, 10)` is a raw string date — not `Intl.DateTimeFormat` (HR-26) | `:1416` | P1 |
| F-07 | Upload tray retry marked PLANNED in control map; confirm against code | `:803-864` | P2 |
| F-08 | Private `.btn`/`.icon-btn`/`.row` design system (M-03) | styles block | P1 |

---

## 5. Operator item 5 — Transitions / effects standardization

| # | Finding | Evidence | Severity |
|---|---|---|---|
| T-01 | Motion tokens exist (`--skin-motion-fast/normal/slow/ease`) but are not mandatory in modules | `tokens.css:559-562` vs mixed raw transitions in `soma-message.ts`, `soma-chat.ts`, `soma-file-manager.ts` | **P1** |
| T-02 | No shared **effect** vocabulary (glow, scrim, overlay, glass-blur strength, skeleton shimmer) | `skin-sdk/tokens/vocabulary.ts` has color/space/type/motion — no effect domain | **P1** |
| T-03 | Entry animations ad hoc (`msgIn` keyframes local to soma-message) | `soma-message.ts:111-120` | P2 |
| T-04 | `module-base.ts:94` `5000s` autofill transition hack | not a design token | P2 |
| T-05 | Reduced-motion handled in soma-message but not audited module-wide | `soma-message.ts:122-135` | P1 |

---

## 6. Screen roll-up (contrast · icons · handlers · transitions · modularity)

| Screen (ID) | File | Contrast | Icons | Handlers | Transitions | Modularity | Top gap |
|---|---|---|---|---|---|---|---|
| Chat workspace (UI-S-07) | `soma-chat.ts` | M-01 hex debt | Material OK | live WS OK | ad hoc | **FAIL** private palette | M-01 / bubble actions |
| Message bubble (CH-12) | `soma-message.ts` | **FAIL** C-01…C-04 | **FAIL** I-01/I-02 | **FAIL** A-01…A-04 | local `msgIn` | partial (glassCard+moduleBase) | P0 cluster |
| Composer (CH-15+) | `soma-composer.ts` | ok tokens | Material OK | live | ok | ok | — |
| Left rail | `soma-sidebar.ts` | ok | Material OK | live routes | ok | ok | — |
| Files (UI-X-01) | `soma-file-manager.ts` | token-based | `attachmentIcon` OK | live + honest GATED tree | private | **FAIL** M-03 | F-01/F-02 |
| Brain surface (UI-X-07) | `soma-brain-manager.ts` | token-based | Material OK | live PATCH/PUT | private sliders | **FAIL** M-04 | B-01 duplicate form |
| Settings · SomaBrain (UI-S-56) | `soma-settings-somabrain.ts` | token-based | Material OK | live GET/PUT | private toggles | **FAIL** M-05 | B-01 |
| Settings · Models | `soma-settings-models.ts` | ok | Material OK | live `/llm/*` | ok | ok | — |
| Settings · root | `soma-settings.ts` | mixed | Material OK | live | mixed | partial | I18N |
| Memory (UI-S-04) | `soma-memory-view.ts` | ok | Material OK | live + `—` honesty | ok | ok | prior audit PASS |
| Cognitive panel | `soma-cognitive-panel.ts` | ok | Material OK | `_loadFailed` correct | ok | ok | reference honesty pattern |
| Welcome | `soma-welcome-dashboard.ts` + chat `_renderWelcome` | mixed | Material OK | real CTAs | mixed | partial | IA hero checks |
| Login | `soma-login.ts` | mixed | Material OK | live | mixed | partial | — |

---

## 7. Honesty spot-check (HR-29…HR-36)

| Pattern | Verdict | Evidence |
|---|---|---|
| GATED present-but-disabled | PASS on tree / delete-in-browse / password modal | `soma-file-manager.ts:747+`, `soma-password-modal.ts` |
| `_loadFailed` empty vs error | PASS cognitive panel; PASS file list `LoadStatus` | `soma-cognitive-panel.ts`, `soma-file-manager.ts:68` |
| No dead CTA | **FAIL** on bubble Retry (absent) and copy silent fail | §1.3 |
| Unknown ≠ zero | PASS memory WM/LTM `—` | prior audit |
| CLEF decision UI | not in this wave's surface | — |
| Permission honesty | PASS `files:read` denied state | `soma-file-manager.ts:1344-1347` |

---

## 8. Priority extract

See `docs/plans/SOMA-PLAN-UIUX-P0-P3-001.md` for the full P0–P3 plan. Summary:

| Priority | Theme | Items |
|---|---|---|
| **P0** | Chat bubbles | C-01…C-04 contrast · I-01/I-02 icons · A-01/A-02/A-04/A-05 actions · F-02 file search honesty |
| **P1** | Modularization + file browser + Brain admin | M-01…M-06 · A-03/A-06 · F-03/F-06 · B-01/B-02 · T-01/T-02 |
| **P2** | Polish | C-05…C-08 · I-03/I-06 · F-05/F-07 · T-03/T-04 · B-03 |
| **P3** | Deep IA / catalog | full I18N coverage · skin pack effect domain · control-map sync · Playwright proofs |

---

## 9. Acceptance for the follow-on code wave

1. `bun node_modules/typescript/bin/tsc --noEmit` clean.
2. `node scripts/check-skin-literals.mjs` — **no new debt** (never `--update-baseline` to hide debt).
3. Bubble actions: Copy (visible failure) + Retry (real WS re-send) + Edit (user, real re-send) or honest GATED.
4. No route deleted without proof.
5. Chat still sends/receives on live WS.

End of audit.
