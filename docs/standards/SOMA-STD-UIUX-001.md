# SOMA-STD-UIUX-001 — UI/UX Engineering Standard (webui)

## Document Control

| Field | Value |
|---|---|
| Document Title | SOMA-STD-UIUX-001 — UI/UX Engineering Standard (webui) |
| Document Identifier | SOMA-STD-UIUX-001 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2027-01-13 |
| Audience | Every agent and human editing `webui/` or UI-facing docs |
| Scope | `webui/**`, UI design docs, UI control maps, skin tokens |
| Law | Soma law · no shims · no fakes · fail-closed · honest GATED |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | SomaTech Engineering | Initial issue. Single followable UI/UX standard consolidating Soma law, stack lock, naming, AgentSkin, I18N, honesty patterns, module CSS contract, control-map rules, A2A claims, and acceptance gates. |

---

## 1. Purpose / Why

UI work spans many agents and many docs (`SOMA-UI-*`, `SOMA-01-UIUX-*`, mockups,
control maps). Without one working standard, each agent re-invents chrome,
hardcodes colours, ships dead CTAs, or renames product surfaces.

This standard is **the one file every UI agent loads before touching `webui/`**.
It does not replace the feature specs; it states the **hard rules** they all obey.

| This standard owns | Feature specs own |
|---|---|
| Law, naming, skins, I18N, honesty patterns, acceptance gates | Screen layout detail, API field truth, per-surface control tables |
| How any UI file must be written | What a specific surface must show |

**Why it matters:** a themed product cannot ship if every module invents its own
pixels; an agent product cannot ship if controls lie (fake CTA, silent empty,
"allow" when policy denied). Both are defects, not style choices.

---

## 2. When to use

Use this standard whenever you:

- create or edit any file under `webui/src/**` (Lit components, views, styles, i18n)
- write or revise a UI design doc, mockup, or control map
- review a UI diff (you are `soma-adversarial-skeptic` or a peer agent)
- wire a new route, button, field, banner, or status chip
- add a skin pack, token, or shared style class

You do **not** need this standard for Django/Temporal/Vault work except where
the UI contract (API shape, GATED reason, honesty) is part of the change.

---

## 3. Hard rules

Rules are numbered `HR-nn`. **Every one is mandatory.** Violation = defect.

### 3.1 Soma law (real code only)

| ID | Rule |
|---|---|
| HR-01 | **NO SHIMS. NO FAKES. NO MOCKS. NO STUBS. NO PLACEHOLDERS. NO TODO PASSES.** A shim is a bypass. A mock is a lie. A fake is a defect. |
| HR-02 | Every visible control has a **real handler** wired to a real API/WS/route. Failure → **visible error**, never a silent empty state. |
| HR-03 | Acceptance and e2e use **live real services** (T-8/VIBE). Unit tests may use fakes **only** as local test doubles inside test files — never production code. |
| HR-04 | If a dependency is missing, integrate the **real** library/API or the feature does not ship (honest GATED instead). |
| HR-05 | Merge-additive: never revert or overwrite a peer agent's work. Grep before rewrite; extend, do not fork. |

### 3.2 Stack lock

| ID | Rule |
|---|---|
| HR-06 | UI = **Lit 3.x** only. **No React. No Alpine.** No new lanes. |
| HR-07 | Backend contract: Django Ninja · Django ORM · Temporal (async) · Vault (secrets) · Milvus via SomaBrain. No FastAPI / SQLAlchemy / Qdrant. |
| HR-08 | T-1 memory: UI and agent call `MemoryGateway` → `SomaBrainAdapter` only. Never an SFM client. Never a second memory path. |

### 3.3 Product naming

| ID | Rule |
|---|---|
| HR-09 | UI product names are **Agent · Hands · Brain · Memory**. **Never "Capsule" in the UI.** (Internal code/domain may keep `capsule` identifiers; user-visible copy must not.) |
| HR-10 | Route and label names follow `SOMA-UI-IA-001` / `SOMA-UI-NAV-001`. Do not invent alternate homes. |
| HR-11 | **Memory has one home:** `/memory`. All other entries route there. No Memory canvas tab, no Memory mini-panel, no Memory hero card. |
| HR-12 | **Models live full-screen in Settings** — never a left-rail item, never a welcome card. |

### 3.4 A0 chrome (non-negotiable)

| ID | Rule |
|---|---|
| HR-13 | **Composer = hero.** Welcome primary CTA is the composer, not an action-card grid. |
| HR-14 | **Thin top strip** (clock · connection · notifications · project). No settings cluster in chat top. |
| HR-15 | **Left rail = Memory + Settings only** (plus search / New chat / chat list / user). No Models, Channels, or Brain in the rail. |
| HR-16 | Welcome shows **no** Memory / Settings / Models / Channels / Brain hero cards. |
| HR-17 | Every A0 chrome change is verified against `SOMA-UI-IA-001` §checklist before Done. |

### 3.5 AgentSkin (modular styles)

| ID | Rule |
|---|---|
| HR-18 | **One skin owns every visual decision.** Modules own structure and behaviour only. There is no second design system. |
| HR-19 | All visual values come from `--skin-*` custom properties (or the `.mb-*` / `.glass-*` / density bindings that wrap them). **No hex, no magic px, no `font-family:` literals** in `components/**` or `views/**`. |
| HR-20 | Shared classes live in `webui/src/styles/` only: `module-base.ts` (`.mb-*`), `glass.ts` (`.glass-*`), `density.ts` (`SPACE`/`RADIUS`/`TYPE`), `tokens.css` (declarations). `skin-sdk/` owns packs, validate, resolve, aliases. |
| HR-21 | Adding a UI file = compose existing skin modules. Adding a skin pack = change token values only; **zero component edits**. |
| HR-22 | New token names are added to the vocabulary in `SOMA-UI-SKINS-001` §3.2 first, then implemented. Do not invent parallel names (`--platform-*` is a deprecated alias only). |

### 3.6 I18N

| ID | Rule |
|---|---|
| HR-23 | **No literal user-facing English in Lit `html`** — use `t('key')` (`SOMA-UI-I18N-001`). Keys: `domain.camelCase`. |
| HR-24 | Catalogs `webui/src/i18n/en.json` + `es.json` stay at parity. Locale switch is live (no reload). |
| HR-25 | Error, success, toast, and **GATED reason** strings use catalog keys. |
| HR-26 | Dates/numbers via `Intl.DateTimeFormat` / `NumberFormat`. `lang` on `<html>` updates on locale change (WCAG 3.1.1). |

### 3.7 No emojis

| ID | Rule |
|---|---|
| HR-27 | **No emojis** in any UI string, any locale, any doc wireframe that represents shipped UI. Material Symbols (or text labels) for icons. |
| HR-28 | Docs that show wireframes of shipped UI must not use emoji stand-ins for icons the product does not ship. |

### 3.8 Honesty patterns (GATED and friends)

The UI must never lie. Reuse these patterns; do not invent new ones.

| ID | Pattern | Rule |
|---|---|---|
| HR-29 | **GATED (present-but-disabled)** | Control is rendered **visible but disabled**, with a **blocking reason string** shown inline and in `title`. Never a fake destination, never a silent omission. Reference: `/themes` in `webui/src/main.ts` (REQ-UIX-020). |
| HR-30 | **GATED reason is fixed and honest** | Example: `Password change API not mounted` (`soma-password-modal.ts`). Reason is translated (HR-25) and truthful about the blocker (API missing, permission missing, feature flag). |
| HR-31 | **`_loadFailed` (empty vs error)** | Empty state and load-failure state are distinct. On fetch failure set `_loadFailed` and render error + retry — never an empty list that pretends "nothing here". Reference: `soma-cognitive-panel.ts`. |
| HR-32 | **No dead CTA** | A button that is enabled must work. If the route/API does not exist → GATED with reason (HR-29), or the control is not drawn at all. Never enabled-but-inert. |
| HR-33 | **Unknown ≠ zero** | Missing metric renders `—` / GATED, never `0`, never a guess. (Memory WM/LTM counts: honest `—` until a count API ships.) |
| HR-34 | **CLEF decision UI (W-J3+)** | Show probability bars (Clef render style) with **`p_safe` + risk + confidence shown separately**. Override requires a **reason string**. **Never claim allow when OPA denied.** |
| HR-35 | **No invented structure** | Do not draw a tree when the API returns a flat list. Do not draw upload/delete chrome while those endpoints are absent on that surface. Missing fields render `—`. |
| HR-36 | **Permission honesty** | Missing capability (`cognitive:edit`, etc.) → GATED with reason, never a silent no-op and never a hidden control the user cannot diagnose. |

### 3.9 Security-facing UI

| ID | Rule |
|---|---|
| HR-37 | Secrets are never rendered, logged, or echoed in toasts. Settings secret fields follow `SOMA-01-UIUX-005` secrets rule (`*_FILE` / Vault; display is masked or `—`). |
| HR-38 | Untrusted DOM/API payload content is escaped via Lit's default binding. No `unsafeHTML` on untrusted input. |
| HR-39 | No hardcoded credentials, tokens, or environment URLs in `webui/src`. Configuration comes from the served app config / API. |

---

## 4. Module CSS contract

Implemented in `webui/src/styles/` (see `SOMA-UI-SKINS-001` §13A). Binding rule:

```
Skin JSON (tokens + surfaces)
        │ SkinApplier.setProperty
        ▼
  --skin-* (+ --platform-* / --soma-* aliases)
        │ inherit into Lit shadow roots
        ├──────────────┬──────────────┐
        ▼              ▼              ▼
  module-base.ts   glass.ts     density.ts
  (.mb-btn/input)  (.glass-*)   (SPACE/RADIUS/TYPE)
        └──────────────┴──────────────┘
                       ▼
              Lit modules (structure + API)
```

### 4.1 Layer law

| Layer | Owns | Forbidden |
|---|---|---|
| Skin pack | colour · type · space · radius · shadow · motion · z | layout · DOM · logic |
| `webui/src/styles/*` | reusable classes bound to `--skin-*` | hex · magic px · host components |
| `soma-*` modules | structure · events · REST/WS | private design systems · literals |
| `t()` I18N | copy | (orthogonal to skin) |

### 4.2 Composition contract

1. `static styles = [glassCard, moduleBase, css\`…\`]` — shared styles first, local last.
2. Every declaration is `var(--skin-*)` or a `.mb-*` / `.glass-*` / density binding.
3. Local `css` blocks only compose tokens; they never define a second palette or scale.
4. Skin apply restyles **every** module via aliases — no per-module recompile, no per-module retheme.

| Module file | Role | Example consume |
|---|---|---|
| `styles/module-base.ts` | `.mb-btn` `.mb-input` `.mb-row` chips/status | `class="mb-btn primary"` |
| `styles/glass.ts` | `.glass-card` and surface primitives | `class="glass-card"` |
| `styles/density.ts` | `SPACE` `RADIUS` `TYPE` token maps | ``padding: ${SPACE.md}`` |
| `styles/tokens.css` | skin token + structural alias declaration | `var(--skin-glass-bg)` |
| `skin-sdk/` | packs · validate · resolve · aliases · install | pack JSON only |

### 4.3 `scripts/check-skin-literals.mjs` (enforcement gate)

AgentSkin modularity is **mechanically gated**, not advisory.

```bash
node scripts/check-skin-literals.mjs              # ratchet vs baseline (CI default)
node scripts/check-skin-literals.mjs --strict     # fail on ANY residual hit
node scripts/check-skin-literals.mjs --update-baseline   # re-seed debt ledger
```

| Behaviour | Detail |
|---|---|
| Scan root | `webui/src/**/*.{ts,css}` (skips `styles/`, `skin-sdk/`, `i18n/`, `*.test.ts`) |
| Detects | hex colours (`#rgb`…`#rrggbbaa`) and literal `NNpx` lengths outside the exempt set |
| Exempt px | `0`, `1px`, `2px` (borders), plus `auto`/`none`/`%` forms the scanner skips |
| Default mode | **Ratchet:** existing debt is listed; **new** debt vs `scripts/skin-literal-baseline.json` → **exit 1** |
| `--strict` | any residual hit → exit 1 (used when a module family is fully migrated) |
| `--update-baseline` | rewrite the baseline JSON (only when debt is **intentionally** accepted — never to hide new debt) |

**Rule HR-40:** you may never run `--update-baseline` to green a failing change
that introduced **new** literals. Fix the literals (bind `--skin-*`) instead.
Shrinking the baseline is always welcome; growing it needs operator approval.

---

## 5. Control-map and ISO wireframe rules

Design artifacts must stay buildable and honest. Follow `SOMA-UI-CONTROL-MAPS-001`
and `SOMA-UI-TEMPLATE-001`.

### 5.1 Control-map rows

Every button and field gets one row with **all** columns:

| Column | Meaning |
|---|---|
| ID | Stable id (`MM-01`, `SB-60`, `CH-12`, `ST-03`, `UI-C-*` in IDREG) |
| Label | User-visible label (I18N key in code, English in docs) |
| Type | control type (button, input, select, chip, meter, …) |
| API / WS binding | real endpoint or `—` (then GATED or absent) |
| States | render states (default/hover/focus/disabled/loading/error/empty) |
| disabled-when | exact predicate for GATED |
| disabled-reason | fixed honest reason string |
| Status | `LIVE` · `PLANNED` · `GATED` — **derived from code**, never aspirational |

Rules:

- HR-41: `LIVE` is claimed only when the control exists and its handler is wired in `webui/src`.
- HR-42: Disagreements between mockup and code are recorded in the map's disagreement register (see X-02 pattern) — **not silently papered over**.
- HR-43: Screen/surface IDs stay those of IDREG (`UI-S-*`, `UI-X-*`, `UI-M-*`). Control maps do not allocate new screen IDs.

### 5.2 ISO wireframes

- HR-44: ASCII wireframes fix **region layout** (chrome, left, canvas, right), not pixel styling.
- HR-45: Wireframes mark honesty inline: `—` for unknown, `GATED` with reason, no fake numbers.
- HR-46: Wireframes use product names (Agent/Hands/Brain/Memory) — never Capsule (HR-09) — and no emojis (HR-27).
- HR-47: Every region/control in a wireframe traces to a control-map ID, and every control-map ID traces to a route or an honest GATED state.

---

## 6. A2A claims

Multi-agent safety (append-only, never delete peers' entries):

1. **Before large `webui/` or UI-doc edits**, claim the paths in `docs/plans/a2a/CLAIMS.md`.
2. Respect other agents' **ACTIVE** claims; if you must touch a claimed file, merge-additive and note it in `LEDGER.md`.
3. **Log commits** to `docs/plans/a2a/LEDGER.md`. Messages via `INBOX.md` / `OUTBOX.md`.
4. Handshake/ACK per `docs/plans/a2a/` protocol when a peer hands off UI work.
5. Claim granularity: file paths or tight prefixes (`webui/src/views/soma-memory-view.ts`), not entire `webui/` forever — release claims you no longer need (set status `DONE`).

---

## 7. Acceptance (Definition of Done for UI work)

All gates must be **green on real code**. No skip-gating to fake a pass.

| # | Gate | Command / proof | Fails when |
|---|---|---|---|
| A-1 | Types | `npx tsc` (webui) | any TS error |
| A-2 | Build | `npx vite build` (webui) | build error |
| A-3 | Skin literals | `node scripts/check-skin-literals.mjs` | new hex/px debt vs baseline |
| A-4 | I18N | grep: no hardcoded `Save`/`Cancel`/… in components (excl. comments) · en/es parity | literal English or missing key |
| A-5 | Honesty | every new control has handler or GATED+reason · `_loadFailed` on fetch paths | dead CTA, silent empty |
| A-6 | A0 chrome | IA checklist (HR-13…HR-17) | hero cards, rail pollution |
| A-7 | Naming | UI copy uses Agent/Hands/Brain/Memory | "Capsule" in UI strings |
| A-8 | Emojis | grep: no emoji in UI strings/catalogs | any emoji |
| A-9 | Playwright | human session on **live real services** (T-8/VIBE) | any mocked path presented as Done |

**Done = live Playwright session green on real services** — not skip-gated, not mocked.

---

## 8. Examples — DO / DON'T

### 8.1 Styling

| | Example |
|---|---|
| **DO** | `color: var(--skin-color-accent);` · `padding: var(--skin-space-md);` · `class="mb-btn primary"` |
| **DON'T** | `color: #3d7eff;` · `padding: 16px;` · `font-family: Inter` inside a component |
| **DO** | new spacing need → use `--skin-space-*` or `density.SPACE` |
| **DON'T** | `padding: 13px` because it "looks right" |

### 8.2 Honest GATED

| | Example |
|---|---|
| **DO** | Disabled button + inline reason `Password change API not mounted` + `title` + `GATED` chip (`soma-password-modal.ts`) |
| **DON'T** | Enabled button that no-ops · silent hide with no explanation · redirect to an unrelated surface (`/themes` → `/settings`) |
| **DO** | `/themes` present-but-disabled notice with blocking reason and the one real control that works (light/dark toggle) |
| **DON'T** | Claim "Themes coming soon" with no reason and no status |

### 8.3 Empty vs error

| | Example |
|---|---|
| **DO** | `_loadFailed = true` → error banner + Retry (`soma-cognitive-panel.ts`) |
| **DON'T** | catch → leave list `[]` → render "No memories yet" |
| **DO** | unknown metric → `—` + `GATED (no count API)` |
| **DON'T** | unknown metric → `0` |

### 8.4 I18N and naming

| | Example |
|---|---|
| **DO** | ``html`<button>${t('files.upload')}</button>` `` · copy "Memory" · "Brain" |
| **DON'T** | ``html`<button>Upload</button>` `` · "Capsule" · "🚀 Upload" |

### 8.5 CLEF decision UI

| | Example |
|---|---|
| **DO** | probability bars; `p_safe`, risk, confidence as three separate readouts; override modal requires reason string; OPA deny shows deny |
| **DON'T** | single green "Allow" badge · override without reason · claim allow when OPA denied |

### 8.6 New surface

| | Example |
|---|---|
| **DO** | control map first (IDs, API, states, GATED), then Lit module composing `glassCard + moduleBase`, routes in `main.ts`, Playwright proof |
| **DON'T** | ship a styled mock with fake data, dead buttons, and a "PLANNED" banner that claims LIVE |

---

## 9. Definitions

| Term | Definition |
|---|---|
| AgentSkin | The modular theming system: skin packs produce `--skin-*` tokens; modules are skin clients |
| GATED | Present-but-disabled control with a fixed blocking reason (HR-29) |
| A0 chrome | The locked product shell: composer hero, thin top strip, left-rail Memory + Settings only |
| Control map | Per-surface table binding every control to ID, API, states, and delivery status |
| Ratchet (skin literals) | Fail only on **new** literal debt vs baseline; never grow baseline without operator approval |

---

## 10. References

| ID | Document | Role |
|---|---|---|
| REF-01 | `docs/standards/SOMA-STD-TRIAD-001.md` | Shared triad law (stack, T-1 memory path) |
| REF-02 | `docs/standards/SOMA-STD-CODING-001.md` | VIBE coding law (real code, no bullshit) |
| REF-03 | `docs/design/SOMA-UI-IA-001.md` | Authoritative IA + A0 chrome checklist |
| REF-04 | `docs/design/SOMA-UI-NAV-001.md` · `SOMA-UI-BINDINGS-001.md` | Navigation and route/API bindings |
| REF-05 | `docs/design/SOMA-UI-SKINS-001.md` | Skin token vocabulary + §13A module CSS contract |
| REF-06 | `docs/design/SOMA-UI-I18N-001.md` | I18N law |
| REF-07 | `docs/design/SOMA-UI-CONTROL-MAPS-001.md` | Control-map + wireframe specification |
| REF-08 | `docs/design/SOMA-UI-IDREG-001.md` | ID registry (UI-S/X/M/C/A/F, REQ-UIX) |
| REF-09 | `docs/iso/SOMA-01-UIUX-001…005.md` | Feature-level UI/UX ISO suite (screens, modals, catalogue, verification, settings parity) |
| REF-10 | `scripts/check-skin-literals.mjs` | AgentSkin literal gate (this standard §4.3) |
| REF-11 | `docs/plans/a2a/CLAIMS.md` | A2A path claims |

---

## 11. Traceability (this standard → source truth)

| Rule family | Source of truth |
|---|---|
| HR-01…HR-05 | `SOMA-STD-TRIAD-001`, `SOMA-STD-CODING-001`, operator law 2026-10-09 |
| HR-06…HR-08 | `SOMA-STD-TRIAD-001` stack lock + T-1 |
| HR-09…HR-12 | `SOMA-UI-IA-001`, `SOMA-UI-NAV-001` |
| HR-13…HR-17 | `SOMA-UI-IA-001` A0 pattern + checklist |
| HR-18…HR-22 | `SOMA-UI-SKINS-001` §3.2 · §13A |
| HR-23…HR-26 | `SOMA-UI-I18N-001` |
| HR-27…HR-28 | Operator UI law (no emojis) |
| HR-29…HR-36 | Live honesty patterns in `webui/src` (`main.ts` `/themes`, `soma-password-modal.ts`, `soma-cognitive-panel.ts`, `soma-agent-package.ts`, …) + CLEF decision UI law |
| HR-37…HR-39 | `SOMA-STD-SECURITY-001`, `SOMA-01-UIUX-005` secrets rule |
| HR-40 | `scripts/check-skin-literals.mjs` contract |
| HR-41…HR-47 | `SOMA-UI-CONTROL-MAPS-001`, `SOMA-UI-TEMPLATE-001`, `SOMA-UI-IDREG-001` |

---

**End of UI/UX Engineering Standard.**
