# SOMA-UI-SKINS-001 — Capsule Skins — Theming Framework Specification

## Document Control

| Field | Value |
|---|---|
| Document Title | Capsule Skins — Theming Framework Specification |
| Document Identifier | SOMA-UI-SKINS-001 |
| Version | 1.0.0 |
| Date | 2026-10-03 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-28 |
| Related | `SOMA-01-DOCS-001.md`, `SOMA-01-UIUX-001.md`, `SOMA-UI-TEMPLATE-001.md`, `SOMA-SETTINGS-MODEL-001.md`, `docs/standards/SOMA-STD-CODING-001.md` |
| Source of truth | This document for the skins feature contract; `admin/core/models/core.py` for Capsule fields; `admin/core/helpers/capsule_settings.py` for the resolution chain; `policy/skins.rego` for the OPA surface; `webui/src/styles/tokens.css` for the shipped token vocabulary |
| Audience | Product engineering, UI/UX contributors, security reviewers, QA, any agent acting on somaAgent01 |
| Scope | A Capsule-owned theming/skinning framework: skin document shape, resolution order, theme templates, runtime application through Lit 3.x CSS custom properties, isolation, sanitisation, accessibility, and acceptance criteria. **This document is a specification. It does not change code.** |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-03 | SomaTech Engineering | Initial issue. Feature specification for Capsule-owned skins. Measures the current theming state (`webui/src/styles/`, Lit `static styles`, `saas-*` elements, `theme-boot.ts`, `AAAS` palette). Defines the skin document, four-source resolution chain, theme templates, runtime application, isolation, security constraints, accessibility contract, out-of-scope boundary, acceptance criteria and RTM. Records the partial AgentSkin API/store that already exists and its stubs as tracked findings. |

## Normative References

| ID | Reference | Role |
|---|---|---|
| N-1 | SOMA-01-DOCS-001 | Document control and traceability procedure |
| N-2 | SOMA-01-QMS-001 | Quality management system; Document Reference Matrix |
| N-3 | SOMA-A0-PARITY-001 | Error honesty, Plan Gate, no-fake-UI rules |
| N-4 | `SOMA-01-UIUX-001.md` | Master screen and feature specification; honesty vocabulary |
| N-5 | `SOMA-UI-TEMPLATE-001.md` | House ISO template and per-block honesty rules |
| N-6 | `admin/core/models/core.py` | `Capsule`, `CapsuleInstance`, `Capability`, `AgentSetting`, `UISetting` |
| N-7 | `admin/core/helpers/capsule_settings.py` | Categorized settings and the Capsule → AgentSetting → Django → default chain |
| N-8 | `SOMA-SETTINGS-MODEL-001.md` | Settings taxonomy; category C7 UI |
| N-9 | `policy/skins.rego` | OPA policy package `soma.skins` (skin CRUD authorisation surface) |
| N-10 | `webui/src/styles/tokens.css` | Shipped `--aaas-*` design-token vocabulary |
| N-11 | `webui/src/services/theme-boot.ts` | Light/dark polarity boot |
| N-12 | `services/common/skins_store.py`, `admin/ui/api/skins.py` | Existing AgentSkin store and Django Ninja router (partial) |
| N-13 | ISO 9001:2015 clause 7.5 | Control of documented information |
| N-14 | WCAG 2.1 Level AA | Contrast, focus visibility, motion |

---

## 1. Purpose and problem

### 1.1 Purpose

Agent appearance is part of agent identity. Today it is not: it is compiled into components. This
specification defines **skins** — a theming framework owned by the Capsule — so that changing how
an agent looks is a data edit, not a code change. Two Capsules must be able to look entirely
different without either touching component source.

This is a **documented feature**. It is not an implementation. Nothing in this document authorises
code change; the acceptance criteria in §11 are the contract a future implementation must meet.

### 1.2 The measured problem (2026-10-03)

Appearance is hard to change because it lives in component source, not in data.

| Surface | Measured state | Evidence |
|---|---|---|
| Design tokens | One flat CSS file. Header claims "Supports theming via AgentSkin" (`webui/src/styles/tokens.css:7`) but no code reads an AgentSkin document. | `webui/src/styles/tokens.css:1-448` |
| Token vocabulary | Named `--aaas-*`. Two `:root` blocks (`:11`, `:196`) plus an opt-in dark block `[data-theme="dark"]` (`:281-285`). Colour, type, spacing, radius, shadow, motion, z-index and layout are all named here. | `webui/src/styles/tokens.css:15-114`, `:196-278`, `:285-383` |
| Polarity only | The only runtime theme control is light/dark. `theme-boot.ts` stores `soma-theme` in `localStorage` and sets `data-theme` on `documentElement` (`webui/src/services/theme-boot.ts:6`, `:15-25`). There is no skin document, no per-agent appearance, no template pack. | `webui/src/services/theme-boot.ts:1-58` |
| Lit components | **69** TypeScript files declare `static styles = css\`…\`` (measured across `webui/src/components/` and `webui/src/views/`, 2026-10-03). Each holds its own CSS literal. | e.g. `webui/src/components/saas-chat-workspace.ts:33`, `webui/src/components/saas-sidebar.ts:82`, `webui/src/components/saas-composer.ts:43`, `webui/src/views/saas-login.ts:125` |
| Hardcoded colour | **1575** hex/colour literals inside `webui/src/components/` and `webui/src/views/` TypeScript files (measured 2026-10-03), against **468** `var(--aaas-…)` references. Components mix token reads with fallback literals, e.g. `var(--aaas-bg-void, #f5f5f5)` and bare `#1a1a1a`. | `webui/src/components/saas-chat-workspace.ts:39`, `:180`; `webui/src/views/saas-login.ts:202` |
| Dual token names | Some components read `var(--saas-…)` with inline fallbacks (`saas-button.ts`, `saas-toggle.ts`, `saas-glass-modal.ts`) while `tokens.css` defines `--aaas-*`. The `--saas-*` names are not defined in `tokens.css`. | `webui/src/components/saas-button.ts:24-60`; `webui/src/styles/tokens.css:11-114` |
| `saas-*` elements | 30 files under `webui/src/components/` carry the `saas-` prefix (measured 2026-10-03). Each is a self-styled Lit element. | `webui/src/components/` listing |
| Style wiring | `webui/src/main.ts:18-22` imports `tokens.css`, `material-symbols.css` and `theme-boot.js` once at boot. There is no skin application step. | `webui/src/main.ts:18-22` |

**Plain statement of the cost.** A visual change today requires editing component `static styles`
blocks (and often the hex literals inside them), rebuilding the web UI, and redeploying. There is no
data path that restyles an agent. The header comment at `webui/src/styles/tokens.css:7` is an
aspiration, not a mechanism.

### 1.3 What already exists, and what it is not

Honesty about current code (N-3). A partial AgentSkin stack is already in the tree. It is **not**
Capsule-owned skins and it is **not** a theming framework.

| Artefact | What it actually is | What it is not |
|---|---|---|
| `services/common/skins_store.py` | A Redis-backed `SkinRecord` store keyed `skins:{tenant}` (`:39-45`). Record fields: `skin_id`, `tenant_id`, `name`, `description`, `version`, `author`, `variables: Dict[str, str]`, `changelog`, `is_approved` (`:19-33`). | Not Capsule-bound. `variables` is a flat string→string map, not a typed token document. |
| `admin/ui/api/skins.py` | Django Ninja CRUD router: list/get/create/update/delete/approve/reject (`:165-314`), authorising via `services.common.authorization.authorize` with catalog actions `org:read` and `system:configure` (`:168`, `:211`, `:245`). Create starts `is_approved=False` (`:233`). | Not applied to any UI surface. No Lit code fetches skins. |
| `policy/skins.rego` | A separate OPA package `soma.skins` for skin CRUD and tenant isolation. See §8.3 for an accurate reading. | Not the policy the live router consults (the router uses catalog permissions; `admin/core/authz.py:519-523` explicitly retired `skin:upload` as a second authority vocabulary). |
| `webui/src/stores/agent-store.ts:34` | `AgentState.currentAgent.skin_id?: string` — a client-side optional field. | Not backed by any model field or API contract. |

**Tracked findings (current code, not specifications):**

| ID | Finding | Evidence |
|---|---|---|
| S-F-01 | `SkinsStore.get()` always returns `None` ("Simplified: scan all tenant keys" is not implemented). Get-by-id therefore cannot return a skin. | `services/common/skins_store.py:67-70` |
| S-F-02 | `SkinsStore.update()`, `approve()`, `reject()` are `pass`. `delete()` returns `False` without deleting. | `services/common/skins_store.py:92-106` |
| S-F-03 | `validate_no_xss` is a case-insensitive substring denylist (`<script`, `javascript:`, `expression(`, `@import`, `behavior:`). It does not cover `url(`, `image-set(`, `var()` cycles, `attr()`, escaped payloads, or length. | `services/common/skins_store.py:109-112` |
| S-F-04 | No UI reads skins. Appearance remains compiled into `static styles`. | `webui/src/` has no skin fetch or apply path; contrast §1.2 |
| S-F-05 | `policy/skins.rego` and the live `authorize()` path disagree on action vocabulary (`skin:*` vs catalog `org:read` / `system:configure`). | `policy/skins.rego:26-63`; `admin/ui/api/skins.py:168`, `:211`; `admin/core/authz.py:519-535` |

These findings are recorded so a future implementation does not mistake the existing store for the
feature specified here. They are **not** acceptance criteria; they are defects in present code.

---

## 2. The concept: a Skin is Capsule data

### 2.1 Statement

A Capsule already carries identity as data: `persona_config` (`admin/core/models/core.py:254-265`),
`tool_policy` (`:267-277`), `capabilities` (`:243-248`), `constitution` (`:166-172`). Appearance
belongs in the same class of thing.

**A Skin is a typed document of design tokens stored on the Capsule.** Components are machinery;
skins are data. Machinery is written once by engineers. Data is authored by operators.

| Layer | Owner | Changes when |
|---|---|---|
| Components (`saas-*`, views) | Engineering | Structure or behaviour changes |
| Token vocabulary (`--skin-*` custom property names) | Engineering (this spec) | The framework grows a new token |
| Skin document (token **values**, surface overrides) | Capsule / operator | An agent's appearance changes |
| Theme template (a named pack of token values) | Operator / design | A reusable look is authored |

Consequence: two agents in one workspace can look entirely different without either touching
component code. That is the acceptance test of the framework (§11, AC-01, AC-02).

### 2.2 What a Skin changes, and what it does not

A skin changes **values** of a closed token vocabulary: colour ramps, type scale, spacing steps,
corner radii, elevation, motion timings, and per-surface overrides. It does not change DOM
structure, component inventory, layout algorithms, or behaviour. The boundary is normative and is
restated in §10.

### 2.3 Binding to Capsule

The skin document lives on the Capsule alongside `persona_config`, because it is part of agent
identity and must version with the Capsule (`parent`/`children` lineage,
`admin/core/models/core.py:157-163`). Recommended location:

```
Capsule.persona_config.skin          # the skin document (see §3)
```

This keeps the model change at zero new columns while the feature is specified and first built: the
document rides the existing `persona_config` JSONField (`admin/core/models/core.py:254-265`), the
same way `knobs`, `prompts`, `memory` and `learned` already do (`:258-263`).

**OPEN-01.** Should `skin` become a first-class `Capsule.skin` JSONField (like `tool_policy`) once
the shape is stable, or remain a `persona_config` sub-document indefinitely? A first-class field
gives a cleaner export facet and an indexable column; a sub-document avoids a migration now.

---

## 3. Data model

### 3.1 Shape

A skin is a JSON document with a closed set of top-level keys. Unknown keys are rejected at the
sanitiser (§8.2), not ignored — ignoring unknown keys is how injection hides.

| Key | Type | Required | Meaning |
|---|---|---|---|
| `schema_version` | string | yes | Document schema version. This spec defines `"1"`. |
| `name` | string | yes | Human name, 1–50 chars. |
| `description` | string | no | 0–200 chars. |
| `template` | string | no | Name of the theme template this skin started from (§5). Informational. |
| `tokens` | object | yes | Core design tokens. See §3.2. |
| `surfaces` | object | no | Per-surface token overrides. See §3.3. |
| `meta` | object | no | `author`, `version` (semver), `changelog` (list). Never read by the renderer. |

### 3.2 Core tokens (`tokens`)

The vocabulary is the closed set of custom property names the framework writes. Names are stable;
values are skin data.

| Group | Token names (custom properties) | Value domain |
|---|---|---|
| Colour — base | `--skin-color-bg-void`, `--skin-color-bg-base`, `--skin-color-bg-card`, `--skin-color-bg-sidebar`, `--skin-color-bg-hover`, `--skin-color-bg-active` | CSS colour (`#rgb`, `#rrggbb`, `rgb()`, `rgba()`, `hsl()`, `hsla()`, named colours). No `url()`, no `image-set()`. |
| Colour — text | `--skin-color-text-primary`, `--skin-color-text-secondary`, `--skin-color-text-muted`, `--skin-color-text-inverse`, `--skin-color-text-link` | CSS colour |
| Colour — accent | `--skin-color-accent`, `--skin-color-accent-hover`, `--skin-color-accent-text` | CSS colour |
| Colour — semantic | `--skin-color-success`, `--skin-color-warning`, `--skin-color-danger`, `--skin-color-info` (and `-text` companions) | CSS colour |
| Colour — border | `--skin-color-border`, `--skin-color-border-strong`, `--skin-color-border-subtle` | CSS colour |
| Type — family | `--skin-font-sans`, `--skin-font-mono` | Font family list. System fonts and families the platform bundles only (§8.2, §OPEN-04). |
| Type — scale | `--skin-text-xs`, `--skin-text-sm`, `--skin-text-base`, `--skin-text-lg`, `--skin-text-xl`, `--skin-text-2xl` | Length (`px`/`rem`) |
| Type — weight | `--skin-weight-normal`, `--skin-weight-medium`, `--skin-weight-semibold`, `--skin-weight-bold` | Number 100–900 |
| Type — leading | `--skin-leading-tight`, `--skin-leading-normal`, `--skin-leading-relaxed` | Number |
| Spacing | `--skin-space-xs`, `--skin-space-sm`, `--skin-space-md`, `--skin-space-lg`, `--skin-space-xl`, `--skin-space-2xl` | Length |
| Radius | `--skin-radius-sm`, `--skin-radius-md`, `--skin-radius-lg`, `--skin-radius-xl`, `--skin-radius-full` | Length |
| Elevation | `--skin-shadow-sm`, `--skin-shadow-md`, `--skin-shadow-lg`, `--skin-shadow-overlay` | Shadow list (see §8.2 for restrictions) |
| Motion | `--skin-motion-fast`, `--skin-motion-normal`, `--skin-motion-slow`, `--skin-motion-ease` | Time (`ms`/`s`) and timing function |

Rationale for the rename `--aaas-*` → `--skin-*`: the shipped vocabulary
(`webui/src/styles/tokens.css:15-114`) mixes light and dark aliases and an `--aaas-` prefix tied to
the AAAS product name. The skin vocabulary is a **closed, documented contract** independent of any
one product palette. The platform default skin (§3.5) reproduces today's AAAS look under the new
names so migration is a rename of reads, not a redesign.

**OPEN-02.** Confirm the token name set before implementation. The list above is the minimum this
spec requires; it is not a mandate to reject a well-argued addition. Additions after v1 are a
`schema_version` bump.

### 3.3 Per-surface overrides (`surfaces`)

Each surface key holds an object of the same token names, applied only inside that surface's scope
(§7). A surface may override any core token; it may not introduce new token names.

| Surface key | Covers | Example elements (current code) |
|---|---|---|
| `chat` | Message list, message bubbles, streaming placeholder | `saas-chat-workspace`, `saas-message` |
| `sidebar` | Left rail, capsule switcher, nav | `saas-sidebar`, `saas-sidebar-workspace` |
| `composer` | Input, attach menu, send control | `saas-composer`, `saas-composer-menu` |
| `tool_timeline` | Tool-call timeline rows | `saas-tool-timeline` |
| `login` | Auth screens | `saas-login` (`webui/src/views/saas-login.ts:125`) |
| `chrome` | Global header, facet tabs, instance strip | global chrome per `SOMA-01-UIUX-001.md` §7 |
| `right_panel` | Right-rail surfaces | `saas-right-panel` |

**OPEN-03.** Final surface list. The seven above cover the surfaces named in
`SOMA-01-UIUX-001.md` §1.3 and the components measured in §1.2. Modal (`saas-glass-modal`) and
tables (`saas-data-table`) are intentionally left to inherit core tokens in v1.

### 3.4 Complete example

```json
{
  "schema_version": "1",
  "name": "northwind-support",
  "description": "Northwind support desk — cool slate, high-contrast chat",
  "template": "slate-cool",
  "meta": {
    "author": "platform-ops",
    "version": "1.0.0",
    "changelog": [
      { "version": "1.0.0", "date": "2026-10-03", "note": "Initial issue from slate-cool template" }
    ]
  },
  "tokens": {
    "--skin-color-bg-void": "#0f1419",
    "--skin-color-bg-base": "#151b23",
    "--skin-color-bg-card": "#1c2430",
    "--skin-color-bg-sidebar": "#121820",
    "--skin-color-bg-hover": "#222b38",
    "--skin-color-bg-active": "#2a3544",
    "--skin-color-text-primary": "#e7ecf1",
    "--skin-color-text-secondary": "#a8b3c0",
    "--skin-color-text-muted": "#7d8896",
    "--skin-color-text-inverse": "#0f1419",
    "--skin-color-text-link": "#7cb7ff",
    "--skin-color-accent": "#3d7eff",
    "--skin-color-accent-hover": "#5b92ff",
    "--skin-color-accent-text": "#ffffff",
    "--skin-color-success": "#22c55e",
    "--skin-color-warning": "#eab308",
    "--skin-color-danger": "#ef4444",
    "--skin-color-info": "#3b82f6",
    "--skin-color-border": "rgba(255, 255, 255, 0.10)",
    "--skin-color-border-strong": "rgba(255, 255, 255, 0.18)",
    "--skin-color-border-subtle": "rgba(255, 255, 255, 0.06)",
    "--skin-font-sans": "Inter, system-ui, sans-serif",
    "--skin-font-mono": "JetBrains Mono, ui-monospace, monospace",
    "--skin-text-xs": "11px",
    "--skin-text-sm": "13px",
    "--skin-text-base": "14px",
    "--skin-text-lg": "16px",
    "--skin-text-xl": "18px",
    "--skin-text-2xl": "24px",
    "--skin-weight-normal": "400",
    "--skin-weight-medium": "500",
    "--skin-weight-semibold": "600",
    "--skin-weight-bold": "700",
    "--skin-leading-tight": "1.25",
    "--skin-leading-normal": "1.5",
    "--skin-leading-relaxed": "1.75",
    "--skin-space-xs": "4px",
    "--skin-space-sm": "8px",
    "--skin-space-md": "16px",
    "--skin-space-lg": "24px",
    "--skin-space-xl": "32px",
    "--skin-space-2xl": "48px",
    "--skin-radius-sm": "4px",
    "--skin-radius-md": "8px",
    "--skin-radius-lg": "12px",
    "--skin-radius-xl": "16px",
    "--skin-radius-full": "9999px",
    "--skin-shadow-sm": "0 1px 2px rgba(0, 0, 0, 0.4)",
    "--skin-shadow-md": "0 2px 8px rgba(0, 0, 0, 0.45)",
    "--skin-shadow-lg": "0 8px 24px rgba(0, 0, 0, 0.5)",
    "--skin-shadow-overlay": "0 16px 48px rgba(0, 0, 0, 0.55)",
    "--skin-motion-fast": "120ms",
    "--skin-motion-normal": "200ms",
    "--skin-motion-slow": "320ms",
    "--skin-motion-ease": "cubic-bezier(0.2, 0, 0, 1)"
  },
  "surfaces": {
    "chat": {
      "--skin-color-bg-card": "#1a222d",
      "--skin-radius-md": "10px"
    },
    "sidebar": {
      "--skin-color-bg-sidebar": "#0c1117",
      "--skin-space-md": "12px"
    },
    "login": {
      "--skin-color-bg-void": "#0a0e13",
      "--skin-shadow-overlay": "0 24px 64px rgba(0, 0, 0, 0.65)"
    }
  }
}
```

### 3.5 Platform default

The platform default skin **is** a skin document. Its token values reproduce the shipped AAAS light
palette so that "no skin configured" and "platform default" are the same visual result, not two
different code paths. Source values today: `webui/src/styles/tokens.css:15-114` (first `:root`) and
`:196-278` (AAAS light block).

Polarity (light/dark) remains orthogonal in v1: `theme-boot.ts` continues to own
`data-theme="light" | "dark"` (`webui/src/services/theme-boot.ts:15-25`), and a skin may supply a
`dark` variant.

**OPEN-04.** Does v1 ship `tokens.dark` as a second token map inside each skin, or does v1 keep
polarity purely in `tokens.css` and let skins only restyle one polarity? Two maps double authoring
effort; one map leaves dark mode unskinnable. Decision needed before implementation.

### 3.6 Versioning

| Dimension | Rule |
|---|---|
| Document schema | `schema_version`. Renderer refuses unknown values (fail-closed). |
| Skin content | `meta.version` (semver). Bump on every accepted edit. |
| Capsule binding | The Capsule carries the skin; Capsule version lineage (`parent`/`children`, `admin/core/models/core.py:157-163`) versions the binding. Editing an active Capsule's skin spawns a new Capsule version (`SOMA-01-UIUX-001.md` REQ-UIX-012). |
| Template | Template packs are versioned independently (§5). A skin records the template name it started from; it does not track template upgrades. |

---

## 4. The four skin sources, resolved in one order

### 4.1 Order

Highest wins. The first source that defines a value takes it; later sources fill gaps only.

```
1. Capsule.skin          Capsule.persona_config.skin   (agent identity)
2. AgentSetting.skin     AgentSetting key for the agent (runtime override)
3. Tenant default        tenant-scoped default skin    (tenant brand)
4. Platform default      the shipped default skin      (schema / tokens)
```

This is the same layered chain the settings layer already uses —
**Capsule → AgentSetting → Django → schema default** — documented at
`admin/core/helpers/capsule_settings.py:3-8` and implemented in
`resolve_setting()` at `admin/core/helpers/capsule_settings.py:144-181`:

1. Capsule identity defaults from `persona_config.settings` (`:154-158`)
2. `AgentSetting` ORM row for `(agent_id, key)` (`:160-169`)
3. Django settings as infra authority (`:171-179`)
4. Caller-supplied default (`:181`)

Skins stay consistent with that chain. The naming difference is deliberate and small: layer 3 for
skins is a **tenant default** (presentation is tenant-scoped brand, not infra configuration), held
in the existing `UISetting` model (`admin/core/models/core.py:497-518`, unique on
`(tenant, user_id, key)`), which `SOMA-SETTINGS-MODEL-001.md` §9.7 already reserves for UI
preferences. Layer 4 remains the schema/shipped default, which for skins is the platform default
skin document (§3.5).

| Skin layer | Backing store | Settings-layer analogue | Evidence |
|---|---|---|---|
| Capsule.skin | `Capsule.persona_config.skin` | Capsule `persona_config.settings` | `admin/core/models/core.py:254-265` |
| AgentSetting.skin | `AgentSetting(agent_id, key="skin")` | `AgentSetting` | `admin/core/models/core.py:726-741`; `capsule_settings.py:160-169` |
| Tenant default | `UISetting(tenant, user_id, key="skin.default")` | Django settings (infra) — replaced by tenant brand | `admin/core/models/core.py:497-518` |
| Platform default | Shipped skin document | Schema default argument | `capsule_settings.py:181`; §3.5 |

**Merge semantics.** Resolution is per **token**, not per document: if the Capsule skin sets only
`--skin-color-accent`, every other token falls through to AgentSetting, then tenant, then platform.
Per-surface overrides resolve the same way, surface by surface, token by token.

### 4.2 Why this order

1. **Capsule first** — appearance is agent identity. Two agents must differ without tenant or
   platform edits.
2. **AgentSetting second** — an operator must be able to correct or trial a look on one running
   agent without mutating the Capsule definition (the same role `AgentSetting` plays for every
   other runtime key, `capsule_settings.py:160-169`).
3. **Tenant default third** — a tenant brand applies to every agent in the tenant until the agent
   says otherwise.
4. **Platform default last** — a defined appearance exists even with zero configuration. Never a
   blank screen.

### 4.3 Failure behaviour

A source that is absent, not an object, or fails sanitisation is **skipped**, and the next source
is used. A skin that fails sanitisation is never partially applied. If every source fails, the
renderer falls back to the platform default compiled from `tokens.css` values (§3.5) and surfaces a
visible non-blocking notice. Silent "looks fine because of fallbacks" is how the current
`var(--saas-…, #hex)` pattern hides breakage (§1.2); the framework must not repeat it.

**OPEN-05.** Should a sanitisation failure on a Capsule skin surface a user-visible warning in
chrome (recommended) or only an ops log? Spec default: both.

---

## 5. Theme templates

### 5.1 What a template is

A **theme template** is a named, versioned pack of core token values — a starting point. It is skin
data with a name, not a code module. Templates exist so operators create a new look in minutes: pick
a template, change the tokens that matter, save.

Templates are ordinary skin documents with `surfaces` empty and a `template` registry entry. They
are stored as data (file pack or store record — **OPEN-06**: which?) and are referenced by name.

### 5.2 Operator flow

1. Choose a template (`slate-cool`, `paper-light`, `high-contrast`, …).
2. Copy it into a new skin document (`name` + `meta.version`).
3. Override the tokens that differ. Most rebrands change 6–12 tokens (accent, text, background
   ramps), not 50.
4. Assign the skin to a Capsule (`persona_config.skin`) or to a tenant default.
5. Preview (§6.3). Save.

Target time from "template chosen" to "agent restyled" is minutes, with zero component edits. That
is the point of the framework (§1.1).

### 5.3 Minimum contract a template must satisfy

A template SHALL:

| ID | Contract |
|---|---|
| T-1 | Declare `schema_version` equal to a value the renderer supports. |
| T-2 | Define **every** required core token in §3.2 (no partial templates; partials are how fallbacks sneak in). |
| T-3 | Pass sanitisation (§8.2) with zero findings. |
| T-4 | Pass the accessibility floor (§9): WCAG AA contrast for text pairs, visible focus, reduced-motion safe. |
| T-5 | Contain no `surfaces` overrides (surfaces are per-skin differentiators, not template material). |
| T-6 | Carry `meta.version` (semver) and a `name` unique within the template registry. |

### 5.4 Shipping defaults

v1 ships at least two templates so the "create in minutes" claim is testable (AC-11):

- **platform-light** — reproduces the shipped AAAS light palette (`tokens.css:15-114`, `:196-278`).
- **platform-dark** — reproduces the shipped AAAS dark palette (`tokens.css:285-383`).

Additional operator templates are data, not releases.

---

## 6. Runtime application

### 6.1 Mechanism: CSS custom properties

Lit 3.x components consume skins **only** through CSS custom properties. That is the whole runtime
contract.

1. A single **skin applier** (a service beside `theme-boot.ts`) resolves the skin (§4), sanitises
   it (§8.2), and writes the resulting custom properties onto a **skin host** element:
   `document.documentElement` for the workspace root, and each agent-scoped host element for
   isolation (§7).
2. Components read `var(--skin-…)` inside their `static styles` blocks. Shadow DOM custom
   properties inherit from the host, so Lit shadow roots see them without `adoptedStyleSheets`
   changes.
3. A skin change updates custom property values. **No component recompile, no rebuild, no
   stylesheet string regeneration.** The `static styles` CSS text is unchanged; only the variable
   values change.

```
skin document ──resolve──► token map ──sanitise──► CSS custom properties
                                                      │
                                                      ▼
                                          :root / skin host style
                                                      │
                          ┌───────────────────────────┼───────────────────────────┐
                          ▼                           ▼                           ▼
                 saas-sidebar::part            saas-composer::part         saas-message::part
                 var(--skin-color-bg-…)        var(--skin-color-accent)    var(--skin-color-text-…)
```

### 6.2 Token reads in components

Components SHALL read skin tokens, not literals. The migration path from today's state (§1.2) is:

| Today | Target |
|---|---|
| `var(--aaas-bg-void, #f5f5f5)` | `var(--skin-color-bg-void)` |
| bare `#1a1a1a` | `var(--skin-color-text-primary)` |
| `var(--saas-…, #hex)` (undefined name) | `var(--skin-…)` |

Fallback literals are banned inside `static styles` once a token exists: a fallback silently
preserves the hard-coded look when a skin fails, which defeats the framework and hides errors
(§4.3). Exception: a component may fall back to `var(--skin-…, var(--aaas-…))` **only** during the
migration window, and that window is tracked (S-F-06, below).

S-F-06 (tracked migration finding, not a feature): 1575 colour literals and 468 `var(--aaas-…)`
reads across 69 styled files must be moved onto `--skin-*` reads. That is a code migration this
spec does not perform.

### 6.3 Hot-swap and live preview

| Behaviour | Requirement |
|---|---|
| Apply | Writing resolved properties onto the host is enough. No page reload. |
| Preview | An operator previewing a skin SHALL see the change on the live UI within one frame budget of the property write. Preview is apply-without-save (§OPEN-07). |
| Revert | Reverting restores the previously resolved map. No reload. |
| Polarity interaction | Toggling `data-theme` (`theme-boot.ts:15-25`) after a skin is applied SHALL re-resolve the skin's dark/light variant (if the skin has one; §OPEN-04) without dropping the skin. |
| Persistence | The **saved** skin is re-resolved on next boot from §4. The previewed-but-unsaved skin is not persisted. |

Hot-swap is a property of CSS custom properties: values change live; static stylesheets do not
need to be recompiled. The framework's job is only to guarantee no code path caches resolved values
in a way that requires a reload.

### 6.4 What the applier must not do

- Must not inject a `<style>` tag containing skin values as free-form CSS text. It writes custom
  property declarations only (`--skin-*: <value>`), never selectors, never property names outside
  the closed vocabulary.
- Must not call `unsafeCSS` with skin data.
- Must not load fonts or images referenced from a skin (§8.2).

---

## 7. Isolation

### 7.1 Requirement

Two agents in one workspace, rendered side by side (capsule switcher, instance strip, multi-agent
chat), must not leak appearance onto each other. A skin is scoped to the surface it is resolved for.

### 7.2 Scoping rules

| Rule | Statement |
|---|---|
| I-1 | Skin custom properties are written to a **skin host**: the agent-scoped root element that contains that agent's surfaces. |
| I-2 | For a single-agent view, the skin host MAY be `document.documentElement`. For multi-agent views, each agent subtree gets its own host. |
| I-3 | Sibling hosts do not share properties. A property written on agent A's host is not visible under agent B's host. |
| I-4 | Surface overrides (§3.3) write to the corresponding surface element (or a `data-skin-surface` attribute hook), never to `:root`. |
| I-5 | Platform chrome outside any agent host resolves the **platform default** or the operator's own UI preference, never an agent's Capsule skin. |
| I-6 | CSS custom properties inherit. The applier SHALL NOT write agent tokens on `:root` when a narrower host exists — that is the leak. |

### 7.3 Worked case

Workspace shows Capsule "atlas" (skin `northwind-support`) and Capsule "helix" (skin `paper-light`)
in a split chat. `atlas`'s host subtree paints with `northwind-support` values; `helix`'s host
subtree paints with `paper-light` values; the sidebar chrome paints with the platform/tenant value.
Neither skin's `--skin-color-accent` crosses the host boundary. This is acceptance criterion AC-05.

---

## 8. Security and trust

### 8.1 Threat model

A skin is **untrusted Capsule-supplied data**. A Capsule may be authored by a tenant operator, an
imported registry package, or an agent-driven edit path. The renderer is a privileged context (the
operator's browser, often an admin session). Therefore a skin must never be able to execute script,
fetch attacker-controlled resources, or exfiltrate data.

| Threat | Vector in CSS | Control |
|---|---|---|
| Script execution | `expression()`, `-moz-binding`, `behavior`, `<script` in injected text | Denylist at sanitiser; only custom property values are written (§6.4) |
| Network exfil | `url()`, `image-set()`, `@import`, font `src` | Denylist; no external URLs in any token value |
| CSS injection | selectors, at-rules, property names outside vocabulary | Closed token vocabulary; values only |
| Data exfil via attr | `attr()` / `attr(… url)` | Denylist |
| DoS / UI breakage | huge values, deep `var()` cycles, enormous documents | size limits, depth limits, cycle detection |
| Cross-tenant leak | skin from tenant A applied in tenant B | §4 resolution is tenant-scoped; `tenant_allowed` in `policy/skins.rego:66-68`; API tenant check `admin/ui/api/skins.py:197-200` |

### 8.2 Sanitisation contract

The sanitiser runs server-side on write and client-side on apply. Both run. Client-side only is not
sufficient (a compromised store row would be applied blindly).

| ID | Rule |
|---|---|
| X-1 | Accept only `schema_version` values the renderer declares. Unknown → reject. |
| X-2 | Reject unknown top-level keys and unknown token names. Do not pass them through. |
| X-3 | Token **names** must match `^--skin-[a-z0-9-]+$` and appear in the §3.2 vocabulary. |
| X-4 | Token **values** must be parseable as the declared domain (colour, length, time, number, font-family, shadow). Anything else → reject. |
| X-5 | Deny, case-insensitively and after HTML-entity / backslash unescape, the substrings and constructs: `expression(`, `javascript:`, `vbscript:`, `@import`, `behavior`, `-moz-binding`, `<script`, `</script`, `url(`, `image-set(`, `attr(`, `element(`, `@font-face`, `@namespace`, `progid:`, backticks, `;` outside a single declaration value's allowed list, and any `\` escape that reconstitutes a denied construct. |
| X-6 | Reject any value containing `://`, `data:`, `blob:`, or a host-like token (no external references of any kind). |
| X-7 | `var()` references, if allowed at all, may only reference other `--skin-*` names in the same document. Cycles and references to non-skin properties → reject. **OPEN-08:** or ban `var()` in values entirely in v1 (simpler, recommended). |
| X-8 | Size limits: document ≤ 32 KiB UTF-8; ≤ 128 core tokens; ≤ 8 surfaces × ≤ 64 tokens; value length ≤ 256 chars; `meta.changelog` ≤ 50 entries. Exceeding a limit is a rejection, not a truncation. |
| X-9 | Shadow values are limited to a list of lengths/colours; no `url()`, no functions outside `rgba()`/`hsl()`/`hsla()`. |
| X-10 | Font family values are a list of identifiers and generic families only. **OPEN-04/OPEN-09:** platform-bundled families only in v1; remote font URLs are forbidden regardless. |
| X-11 | A rejected skin is rejected whole. No partial application. |
| X-12 | Sanitisation findings are returned with the rejected token name and rule id (X-…), never swallowed. |

Current code is weaker than this contract: `validate_no_xss` (`services/common/skins_store.py:109-112`)
checks five substrings and nothing else (S-F-03). It is not the sanitiser this spec requires; it is
a placeholder that must be replaced, not extended by ad-hoc string adds.

### 8.3 The OPA surface — what `policy/skins.rego` actually governs

Honest reading of `policy/skins.rego` (2026-10-03):

| Aspect | What the file does | Lines |
|---|---|---|
| Package | `package soma.skins` | `:15` |
| Default | `default allow := false` — default deny | `:22` |
| Read | `skin:read` allowed when `input.user.authenticated == true` | `:25-28` |
| Write ops | `skin:upload`, `skin:delete`, `skin:approve`, `skin:reject`, `skin:update` allowed only when authenticated **and** `input.user.role == "admin"` | `:31-63` |
| Tenant isolation | `tenant_allowed` when `input.user.tenant_id == input.resource.tenant_id`; `allow_with_tenant` = `allow` AND `tenant_allowed` | `:66-74` |
| Helpers | `is_admin`, `is_authenticated` | `:77-84` |
| Deny reasons | Diagnostic set for unauthenticated, non-admin write, cross-tenant | `:87-102` |
| Escape hatch | `allow { not input.skin; not input.skins }` — any request that carries **no** `skin`/`skins` field is allowed | `:104-110` |

What this means, stated plainly:

1. This policy governs **skin CRUD authorisation** (who may read/upload/approve a skin record). It
   does **not** govern appearance, token values, Capsule binding, or rendering. There is no policy
   here that inspects CSS.
2. It is **not** what the live skins router uses today. `admin/ui/api/skins.py` authorises with
   catalog permissions `org:read` (`:168`) and `system:configure` (`:211`, `:245`, `:270`, `:286`,
   `:302`) through `services/common/authorization.authorize`. That helper resolves the action to a
   catalog permission and, when OPA is attached, asks the engine about **that permission** — not
   about `skin:upload` (`services/common/authorization.py:143-160`).
3. `admin/core/authz.py:519-523` records that `skin:upload` was deliberately removed from the
   action vocabulary because "a second vocabulary is where authority drifts". The remaining
   synonyms map only `settings:read|write|edit` onto catalog permissions
   (`admin/core/authz.py:533-536`).
4. The final `allow` rule (`policy/skins.rego:107-110`) permits any input that lacks `skin` /
   `skins`. Combined with the live path not sending those fields, this rule is not a skin decision
   at all in practice.

**Conclusion for this specification.** `policy/skins.rego` is a skin-record authorisation draft,
not a theming policy and not the live gate. Skins as Capsule data inherit the platform's normal
authorisation path: RBAC catalog permissions, fail-closed OPA (`docs/standards/SOMA-STD-CODING-001.md`
"Security: Fail-closed OPA gates"), and tenant scoping. Token-value safety is **not** an OPA
question in v1 — it is the sanitiser (§8.2). OPA MAY later gate "which Capsule may assign which
template", but that is out of scope here (§10).

**OPEN-10.** Retire `skin:*` action names in `policy/skins.rego` and rewrite the package to
evaluate catalog permissions (`org:read`, `system:configure`) with a `resource: "skins"` match,
matching `authorize()`? Spec recommendation: **yes**, for one vocabulary. Until then, treat any
document that claims "OPA enforces skin approval" as referring to an unused draft.

**OPEN-11.** Should sanitisation of token values ever move under OPA (input document) so that the
same policy engine that gates writes also validates values? v1 keeps sanitiser-in-code (parseable
domains are a parser problem); record the question.

### 8.4 Non-negotiables

| ID | Rule |
|---|---|
| SEC-1 | A skin SHALL NOT execute. No script, no expression, no binding. |
| SEC-2 | A skin SHALL NOT perform network I/O. No `url()`, no `@import`, no font fetch, no image fetch. |
| SEC-3 | A skin SHALL NOT exfiltrate. Tokens are appearance values only; no `attr()` reads of DOM/state, no `env()`, no `var()` of secrets. |
| SEC-4 | A skin SHALL NOT escape its host scope (§7). |
| SEC-5 | Write paths (API, Capsule save) SHALL run the §8.2 sanitiser and refuse non-conforming documents whole. |
| SEC-6 | Apply paths SHALL re-sanitise. Store contents are not trusted on read. |
| SEC-7 | Approval, where used (existing `is_approved`, `admin/ui/api/skins.py:233`, `:283-297`), is an authorisation state, not a safety substitute. Sanitisation runs on unapproved and approved documents alike. |

---

## 9. Accessibility contract

A skin may restyle. It may not make the product unusable.

| ID | Rule | Floor |
|---|---|---|
| A11Y-1 | Text contrast | Every text-on-background pair a skin defines **SHALL** meet WCAG 2.1 AA: ≥ 4.5:1 for normal text, ≥ 3:1 for large text (≥ 18.66px bold or ≥ 24px). Enforced at sanitisation (§8.2) by computing contrast on declared pairs. A skin that fails is rejected. |
| A11Y-2 | UI component contrast | Focus indicators, borders that convey state, and icons that carry meaning **SHALL** meet ≥ 3:1 against adjacent colours. |
| A11Y-3 | Focus visibility | A skin **SHALL NOT** remove focus indication. The focus token set (when added — **OPEN-12**) must retain a visible ring at ≥ 3:1. `:focus-visible` styling is machinery, not skin data; skins colour it, they do not delete it. |
| A11Y-4 | Reduced motion | When `prefers-reduced-motion: reduce` is set, motion tokens **SHALL** not produce animation. Implementation: the applier writes `--skin-motion-*: 0ms` under that media query, regardless of skin values. A skin cannot override the user's setting. |
| A11Y-5 | No contrast below AA | A skin **SHALL NOT** be applied if it reduces any defined text pair below AA. The platform default and every shipped template already meet AA (`tokens.css:297` states the dark muted-text intent; measured pairs belong in the implementation's test fixtures, not in this prose). |
| A11Y-6 | Text resize | Type-scale tokens are lengths (`px`/`rem`). Skins **SHALL NOT** set font sizes in `pt` or as percentages of viewport units. |
| A11Y-7 | Information not by colour alone | Semantic colour tokens (success/warning/danger) remain paired with iconography in components. Skins recolour; they do not remove the icon channel. |

Note: `prefers-reduced-motion` and `:focus-visible` are **absent** from `tokens.css` today (grep
2026-10-03 returned one WCAG comment at `tokens.css:297` and no reduced-motion rules). A11Y-3 and
A11Y-4 are requirements on the framework, not descriptions of current behaviour.

---

## 10. Out of scope

Honest boundary. The following are **not** skins and **SHALL NOT** be smuggled in as token values:

| Excluded | Why | Where it belongs |
|---|---|---|
| Layout / structure changes | Skinning changes values, not DOM. A skin cannot move the sidebar, hide the composer, or reflow chat. | Screen specifications (`SOMA-01-UIUX-001.md`) |
| New components | A skin cannot introduce elements, slots, or micro design systems. | Module contracts (`SOMA-01-UIUX-003.md`); modules contribute through typed slots only |
| Arbitrary CSS injection | Values only, closed vocabulary (§8.2, §6.4). Free-form CSS is an execution risk and an isolation breach. | Not provided |
| Behaviour / copy changes | Skins do not change strings, icons semantics, or interaction. User-facing text stays in `admin.common.messages.get_message` (`docs/standards/SOMA-STD-CODING-001.md` Messages/I18N). | i18n catalogue |
| Remote assets | No skin-supplied images, fonts, or SVGs. | Platform asset pipeline |
| Runtime code in a skin | No expressions, no Houdini, no `@property` definitions from data. | Not provided |
| Using skins as a security boundary | Skins do not grant or deny authority. | RBAC / OPA catalog permissions |
| Replacing light/dark polarity | Polarity stays (`theme-boot.ts`). Skins may supply variants (§OPEN-04). | `theme-boot.ts` |
| Fixing the existing skins store stubs | S-F-01…S-F-05 are defects in present code. This spec defines the target; it does not repair the store. | Implementation work package |
| The `--aaas-*` → `--skin-*` code migration | Tracked as S-F-06. Large, mechanical, separate. | Implementation work package |

---

## 11. Acceptance criteria

Numbered and testable. Each criterion is written so it can be proven with a Playwright assertion
against the real UI. Status of every row is `NOT YET` until an implementation lands with evidence
(`SOMA-01-DOCS-001.md` REQ-DOCS-012). No criterion is claimed met by this document.

| AC | Criterion | Playwright-shaped proof | Traces |
|---|---|---|---|
| AC-01 | Two Capsules with different skins render different appearance for the same component, with no component source change between the two runs. | Mount Capsule A (skin 1) and Capsule B (skin 2) on the chat screen; assert `getComputedStyle(el).getPropertyValue('--skin-color-accent')` differs across the two hosts; assert the component bundle hash is identical. | REQ-SKIN-001 |
| AC-02 | Changing only skin data (no rebuild) changes the rendered colour of chat chrome. | Apply skin 2 to Capsule A via the data path; assert computed accent changes within 1 rAF; assert no navigation/reload (`page.url()` stable, no `framenavigated`). | REQ-SKIN-001, REQ-SKIN-007 |
| AC-03 | `persona_config.skin` on a Capsule is the highest-precedence source. | Set Capsule skin + AgentSetting skin + tenant default to three different accents; assert computed accent equals the Capsule value. | REQ-SKIN-003 |
| AC-04 | Resolution falls through per token: a token absent from the Capsule skin takes the AgentSetting (then tenant, then platform) value. | Capsule skin sets only `--skin-color-accent`; assert accent is Capsule value and `--skin-color-bg-void` equals AgentSetting/tenant/platform value in turn. | REQ-SKIN-003 |
| AC-05 | Two agents side by side do not leak appearance. | Split view with Capsule A and B; assert A's host computed `--skin-color-accent` ≠ B's, and each equals its own skin; assert chrome host equals platform/tenant value. | REQ-SKIN-006 |
| AC-06 | A skin containing `url(`, `@import`, `expression(`, `javascript:`, or `<script` is rejected whole and applied nowhere. | POST/assign a malicious skin; assert API returns 4xx with rule id; assert UI computed tokens unchanged (still previous skin); assert console has no error-driven partial paint. | REQ-SKIN-008 |
| AC-07 | A skin exceeding size limits (§X-8) is rejected, not truncated. | Assign a 40 KiB document; assert 4xx; assert no partial application. | REQ-SKIN-008 |
| AC-08 | A skin with a text pair below WCAG AA is rejected. | Assign `--skin-color-text-primary` = `#777` on `#777` background; assert 4xx naming A11Y-1; assert not applied. | REQ-SKIN-009 |
| AC-09 | `prefers-reduced-motion: reduce` forces motion tokens to 0ms regardless of skin values. | `page.emulateMedia({ reducedMotion: 'reduce' })`; apply a skin with `--skin-motion-normal: 300ms`; assert computed `transition-duration` on a skin-styled element is `0s`. | REQ-SKIN-009 |
| AC-10 | Hot-swap restores the previous skin on revert without reload. | Preview skin 2, revert to skin 1; assert computed tokens equal skin 1; assert no navigation. | REQ-SKIN-007 |
| AC-11 | An operator can create a skin from a shipped template and assign it to a Capsule without any file edit under `webui/src/`. | Drive the template flow in the UI (or API); assert assignment; assert `git status` of `webui/src/` clean in the test fixture workspace; assert appearance changed. | REQ-SKIN-005 |
| AC-12 | Platform default applies when no source defines a skin; the UI is never unstyled. | Clear Capsule/AgentSetting/tenant skins; assert computed tokens equal the platform default document's values (AAAS light reproduction). | REQ-SKIN-003, REQ-SKIN-004 |
| AC-13 | Focus visibility is preserved under every shipped template. | For each shipped template, `page.keyboard.press('Tab')`; assert `:focus-visible` computed outline/box-shadow is non-`none` and ≥ 3:1 against its background. | REQ-SKIN-009 |
| AC-14 | Cross-tenant skin fetch/assign is denied. | Authenticated as tenant B, GET/assign tenant A's skin; assert 404/403; assert tenant B UI unchanged. | REQ-SKIN-008 |
| AC-15 | Unknown token names in a skin are rejected (not ignored). | Assign a skin with `--skin-color-evil: red`; assert 4xx naming X-2/X-3. | REQ-SKIN-008 |

Evidence location for future results: `docs/iso/evidence/SOMA-UI-SKINS-001/` (Playwright output,
rejection payloads, contrast matrices).

---

## 12. RTM — Requirements Traceability Matrix

Requirement category `REQ-SKIN-*` is owned by this document. Identifier range: `REQ-SKIN-001`…
`REQ-SKIN-012` (this issue). Sub-identifiers follow `SOMA-01-DOCS-001.md` §3.3.2.

### 12.1 Requirements

| ID | Requirement | Priority | Section | Verification | Acceptance |
|---|---|---|---|---|---|
| REQ-SKIN-001 | Appearance **SHALL** be Capsule data. Two Capsules **SHALL** be able to differ in appearance without any component source change. | P1 | §2, §1.2 | Analysis + Playwright | AC-01, AC-02 |
| REQ-SKIN-002 | A skin **SHALL** be a typed document of design tokens (colour ramps, type scale, spacing, radius, elevation, motion) plus optional per-surface overrides for chat, sidebar, composer, tool timeline, login (and chrome, right panel). | P1 | §3 | Schema inspection | AC-01, AC-04 |
| REQ-SKIN-003 | Skin resolution **SHALL** be `Capsule.skin > AgentSetting.skin > tenant default > platform default`, per token, consistent with `admin/core/helpers/capsule_settings.py:144-181`. | P1 | §4 | Playwright precedence and fall-through | AC-03, AC-04, AC-12 |
| REQ-SKIN-004 | A platform default skin **SHALL** exist and reproduce the shipped AAAS appearance so that "no skin" is styled, not blank. | P1 | §3.5, §4.3 | Playwright | AC-12 |
| REQ-SKIN-005 | Operators **SHALL** be able to create a skin from a named theme template in minutes, and a template **SHALL** satisfy the minimum contract T-1…T-6. | P1 | §5 | Playwright + template validation | AC-11 |
| REQ-SKIN-006 | Skins **SHALL** be isolated per agent host; two agents in one workspace **SHALL NOT** leak appearance onto each other or onto chrome. | P1 | §7 | Playwright | AC-05 |
| REQ-SKIN-007 | Runtime application **SHALL** use CSS custom properties consumed by Lit 3.x `static styles` via `var(--skin-…)`, with **zero component recompiles** on a skin change. Hot-swap **SHALL** apply and revert without reload. | P1 | §6 | Playwright + build-artifact comparison | AC-02, AC-10 |
| REQ-SKIN-008 | Skins **SHALL** be treated as untrusted data: no `expression()`, no `url()` to any origin, no `@import`, no script, sanitised on write and on apply, size-limited, tenant-scoped. A skin **SHALL NOT** execute or exfiltrate. | P1 | §8 | Sanitiser tests + Playwright | AC-06, AC-07, AC-14, AC-15 |
| REQ-SKIN-009 | Skins **SHALL NOT** break accessibility: WCAG AA contrast minimums, visible focus, `prefers-reduced-motion` honoured above skin values. | P1 | §9 | Contrast matrix + Playwright | AC-08, AC-09, AC-13 |
| REQ-SKIN-010 | Skins **SHALL NOT** change layout, structure, component inventory, behaviour, or user-facing copy. Arbitrary CSS injection **SHALL NOT** be supported. | P1 | §10, §6.4 | Analysis + negative tests | AC-06, AC-15 |
| REQ-SKIN-011 | The document **SHALL** version (`schema_version`, `meta.version`, Capsule lineage) and an unknown `schema_version` **SHALL** be refused fail-closed. | P2 | §3.6 | API tests | AC-07 (reject path) |
| REQ-SKIN-012 | Claims about current code **SHALL** cite `file:line`. Existing AgentSkin store/API gaps **SHALL** be recorded as findings (S-F-01…S-F-05), not described as the feature. | P1 | §1.2, §1.3, §8.3 | Inspection | Analysis |

### 12.2 Coverage summary

| Requirement Category | Count | Implemented | Tested | Coverage |
|---|---|---|---|---|
| REQ-SKIN (this document) | 12 | 0 | 0 | NOT YET |
| **TOTAL** | **12** | **0** | **0** | **NOT YET** |

Status is `NOT YET` on purpose: this is a specification. A feature with no test is `NOT YET`, not
omitted (`SOMA-01-DOCS-001.md` §6.2).

### 12.3 Chain mapping (this feature's trace)

Per `SOMA-01-DOCS-001.md` §6.1, user-facing features trace
`REQ-* → UI-F-* → UI-S-* → UI-C-*/UI-A-* → component → API/store → UIX-AT-*`. Skins are
cross-cutting rather than a single screen; the chain below is the binding for the feature's user
surfaces. `UI-F-*` / `UI-C-*` / `UIX-AT-*` allocations here are **provisional** and **OPEN-13**
(confirm against `SOMA-UI-IDREG-001.md` before implementation — that document is authoritative for
identifier allocation).

| REQ-SKIN | UI-F-* (prov.) | UI-S-* | UI-C-* / UI-A-* (prov.) | Component / service | API / store | UIX-AT-* (prov.) |
|---|---|---|---|---|---|---|
| REQ-SKIN-001, 002, 007 | UI-F-S101 skin apply & hot-swap | UI-S-00 (chrome), UI-S-07 (chat) | — (no new controls; applier service) | `webui/src/services/` (skin applier, beside `theme-boot.ts:1-58`) | Capsule `persona_config.skin` (`core.py:254-265`) | UIX-AT-S01, S02 |
| REQ-SKIN-003, 004, 011 | UI-F-S102 skin source resolution | — | — | same | `capsule_settings.py:144-181` chain; `AgentSetting` (`core.py:726`); `UISetting` (`core.py:497`) | UIX-AT-S03, S04 |
| REQ-SKIN-005 | UI-F-S103 template picker & skin editor | UI-S-01 (Soul) or Settings — **OPEN-14** | UI-C-S201 template select (prov.) | NEW editor surface | Skins/template store (**OPEN-06**) | UIX-AT-S05 |
| REQ-SKIN-006 | UI-F-S104 multi-agent isolation | UI-S-07 split / workspace | — | skin hosts (§7) | — | UIX-AT-S06 |
| REQ-SKIN-008, 010, 012 | UI-F-S105 sanitisation & rejection | skin editor | UI-C-S202 error banner (prov.) | sanitiser (§8.2) | `admin/ui/api/skins.py` write path (`:208-239`) + Capsule save | UIX-AT-S07, S08 |
| REQ-SKIN-009 | UI-F-S106 a11y floor | all | — | applier + sanitiser contrast check | — | UIX-AT-S09 |

### 12.4 OPEN questions

| ID | Question | Default if unresolved at implementation start | Owner |
|---|---|---|---|
| OPEN-01 | `persona_config.skin` sub-document vs first-class `Capsule.skin` JSONField? | Sub-document; migrate later if needed | Architecture |
| OPEN-02 | Final `--skin-*` token vocabulary (§3.2) before v1 freeze? | Use §3.2 as specified | Design |
| OPEN-03 | Final surface list (§3.3) — include modal and tables? | Seven surfaces as specified | Design |
| OPEN-04 | Skin dark variant (`tokens.dark`) vs polarity-only in `tokens.css`? | v1: one map per skin; dark variant in v1.1 | Design + Product |
| OPEN-05 | Sanitisation failure user-visible notice in chrome, or ops log only? | Both | Product |
| OPEN-06 | Template registry storage: file pack under `docs/design/` or store records? | File pack for v1 shipped templates; store for operator templates | Architecture |
| OPEN-07 | Preview = apply-without-save? Any preview token budget? | Yes; no budget beyond §X-8 | Product |
| OPEN-08 | Allow `var()` inside skin values at all? | Ban in v1 | Security |
| OPEN-09 | Bundled font allowlist (which families ship)? | System fonts only in v1 | Design + Ops |
| OPEN-10 | Rewrite `policy/skins.rego` onto catalog permissions and drop `skin:*` action names? | Yes | Security |
| OPEN-11 | Move value sanitisation under OPA as input validation? | No in v1 | Security |
| OPEN-12 | Add explicit focus-ring tokens to the vocabulary? | Yes before A11Y-3 can be tested against a token; until then focus styling stays in components | Design |
| OPEN-13 | Provisional `UI-F-S10x`, `UI-C-S20x`, `UIX-AT-S0x` identifiers — confirm against `SOMA-UI-IDREG-001.md` (authoritative). | Allocate on implementation | Docs |
| OPEN-14 | Where does the skin editor live — UI-S-01 (Soul) or a Settings screen? | UI-S-01 Soul, because skins are Capsule identity | Product + UI |

---

## 13. Document Reference Matrix

This document is registered in `docs/iso/DOCUMENT-REGISTER.md` and listed in `SOMA-01-QMS-001.md` §7.

| Document | Identifier | ISO Reference | Purpose |
|---|---|---|---|
| Capsule Skins — Theming Framework Specification | SOMA-UI-SKINS-001 | ISO 9001:2015 clause 7.5 | Feature specification for Capsule-owned theming |

End of Document
