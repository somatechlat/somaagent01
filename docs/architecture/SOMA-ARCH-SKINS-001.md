# SOMA-ARCH-SKINS-001 — Skinnable UI Theme System Architecture

## Document Control

| Field | Value |
|---|---|
| Document Title | Skinnable UI Theme System Architecture |
| Document Identifier | SOMA-ARCH-SKINS-001 |
| Version | 1.0.0 |
| Date | 2026-10-12 |
| Status | Proposed |
| Author | Architecture |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 clause 7.5 |
| Related | `SOMA-UI-SKINS-001.md` (feature contract), `SOMA-UI-CATALOG-001.md`, `SOMA-MOD-ARCH-001.md`, `docs/standards/SOMA-STD-CODING-001.md` |
| Source of truth | This document for the implementation architecture. `SOMA-UI-SKINS-001.md` remains the feature contract. Where the two overlap, the contract's requirements bind; this document supplies the buildable structure. |
| Audience | Product engineering, UI contributors, agents implementing skins |
| Stack lock | Lit 3.x · Django Ninja · Django ORM · no React/Alpine/FastAPI |
| Status vocabulary | Every capability row is `NOT YET` until evidence lands. No row is claimed met by this document. |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-12 | Architecture | Initial issue. Implementation architecture for the skinnable UI theme system: token system, skin manifest schema, module/style-slot structure, runtime application flow, authoring SDK, settings UI, and phased plan. Extends `SOMA-UI-SKINS-001.md` with the module + theme + component layering and the developer/agent SDK contract the operator requires. |

---

## 1. Scope and problem

### 1.1 What this document delivers

**This document EXTENDS and IMPLEMENTS `SOMA-UI-SKINS-001.md`. It does not invent a parallel skins system.** Every normative requirement in that contract binds: the skin JSON document shape (`schema_version`, `tokens`, `surfaces`, `meta`), the closed `--skin-*` vocabulary, the four-source resolution chain (Capsule.skin > AgentSetting > tenant default > platform default), runtime application via CSS custom properties on skin host elements, sanitisation X-1…X-12, isolation I-1…I-6, templates `platform-light` / `platform-dark`, and acceptance criteria AC-01…AC-15.

What this architecture adds on top of the contract, as the operator requires:

1. **Skin authoring SDK** — a typed contract so a developer or coding agent authors a skin in minutes from a template (§7).
2. **Module style slots keyed to the surface list** — the contract's `surfaces` (chat, sidebar, composer, tool_timeline, login, chrome, right_panel) become the declared style-slot keys modules expose to skins (§5).
3. **Settings UI for apply / preview / switch** — Settings → Interface → Skins (§6.4).
4. **Phased implementation plan** — ordered work packages with real exit criteria (§11).

Plus the buildable structure the contract leaves open: token alias bridge for the `--platform-*` / `--soma-*` migration, the component override scope, the real `SkinsStore` implementation (contract findings S-F-01…S-F-05), and the runtime applier algorithm.

### 1.2 Measured current state (2026-10-12, verified this session)

| Surface | State | Evidence |
|---|---|---|
| Token vocabulary | Two competing namespaces. `tokens.css` defines `--platform-*`. Components and `index.html` `#soma-brand` use `--soma-*`. 435 `var(--platform-…)` reads and 1118 `var(--soma-…)` reads across `webui/src/`. | `webui/src/styles/tokens.css:11-114`, `:196-278`; `webui/index.html:27-80` |
| Hardcoded colour | Lit `static styles` mix `var(--x, #hex)` fallbacks with bare hex literals. A skin that fails silently leaves the hard-coded look in place. | e.g. `webui/src/components/soma-button.ts:24-57` |
| Theme runtime | `theme-boot.ts` is light/dark only. Stores `soma-theme` in `localStorage`, sets `data-theme` on `documentElement`. No skin document, no apply path. | `webui/src/services/theme-boot.ts:1-58` |
| Skin backend | `admin/ui/api/skins.py` exposes real CRUD + approve/reject. `SkinsStore` persists to Redis `skins:{tenant}`. Record shape is `variables: Dict[str,str]` — a flat map, not a typed manifest. | `admin/ui/api/skins.py:48-314`; `services/common/skins_store.py:19-33` |
| Store defects | `SkinsStore.get()` always returns `None`. `update()`, `approve()`, `reject()` are `pass`. `delete()` returns `False`. These are **stubs** and must be replaced with real implementations — not left as-is. | `services/common/skins_store.py:67-106` (tracked in `SOMA-UI-SKINS-001.md` S-F-01, S-F-02) |
| Sanitiser | `validate_no_xss` is a 5-substring denylist. Far below the contract's X-1…X-12. | `services/common/skins_store.py:107-110` (S-F-03) |
| User preference | `UserPreferences.theme` is `light\|dark\|system` only. No skin id. | `admin/platform/models/profiles.py:279-293` |
| Agent binding | `Agent.skin_id` UUID field exists. `agent-store.ts` carries optional `skin_id`. Neither is wired to a skin apply path. | `admin/platform/models/agents.py:63`; `webui/src/stores/agent-store.ts:34` |
| Settings UI | Interface tab has Theme (dark/light), Language, Timezone. No skin list, no preview, no assign. | `webui/src/views/soma-settings.ts:846-916` |
| Module structure | Views/components are flat files under `webui/src/views/` and `webui/src/components/`. No module registry, no declared style slots. | `webui/src/views/index.ts`, `webui/src/components/index.ts` |
| Shadow DOM | All 35+ styled components use `static styles = css\`…\``. CSS custom properties inherit into shadow roots — this is the theming seam. | grep `static styles` across `webui/src/components/` |

### 1.3 Architectural constraints (non-negotiable)

| ID | Constraint | Source |
|---|---|---|
| C-1 | CSS custom properties are the only theme channel. No `unsafeCSS` with skin data. No free-form CSS injection. | `SOMA-UI-SKINS-001.md` §6.4 |
| C-2 | Skins are untrusted data. Sanitise on write and on apply. Reject whole, never partial. | `SOMA-UI-SKINS-001.md` §8 |
| C-3 | No shims, fakes, mocks, stubs, or TODO passes. Missing store methods get real implementations. | CLAUDE.md ABSOLUTE LAW |
| C-4 | Stack lock: Lit 3.x, Django Ninja, Django ORM. No React/Alpine/FastAPI/SQLAlchemy. | CLAUDE.md |
| C-5 | Two agents side by side must not leak appearance. Skin hosts scope properties. | `SOMA-UI-SKINS-001.md` §7 |
| C-6 | Skins change values only — never DOM structure, layout, behaviour, or copy. | `SOMA-UI-SKINS-001.md` §10 |
| C-7 | One permission vocabulary: catalog `org:read` / `system:configure` with `resource="skins"`. No `skin:*` action names. | `admin/core/authz.py:519-535`; `policy/skins.rego` |

---

## 2. Architecture overview

### 2.1 Three-layer model: Module (surface) → Theme → Component

The operator requires a module + theme + component architecture. This maps 1:1 onto the feature contract's model (`SOMA-UI-SKINS-001.md` §2.1): components are machinery, skins are data. The middle layer is organised by **UI modules**, whose style slots are keyed to the contract's **surface list**.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  MODULE LAYER  (what can be themed) — style slots keyed to surfaces      │
│  Surface keys (contract §3.3): chat · sidebar · composer ·               │
│  tool_timeline · login · chrome · right_panel                            │
│  Each UI module declares a StyleSlot registry (closed token groups).     │
│  Owner: engineering. Changes when product structure changes.             │
├─────────────────────────────────────────────────────────────────────────┤
│  THEME LAYER  (what themes them)                                         │
│  Skin document: tokens + surfaces.{key}.tokens + components.{tag}.tokens │
│  Resolution (contract §4.1): Capsule.skin → AgentSetting.skin →          │
│  tenant default → platform default.                                      │
│  Owner: operator / Capsule. Changes when appearance changes.             │
├─────────────────────────────────────────────────────────────────────────┤
│  COMPONENT LAYER  (what renders)                                         │
│  Lit 3.x elements. Read only var(--skin-*). Static styles never change   │
│  on a skin swap. Shadow DOM inherits custom properties from the host.    │
│  Owner: engineering. Changes when structure or behaviour changes.        │
└─────────────────────────────────────────────────────────────────────────┘
```

A **UI module** is the implementation grouping of Lit components that render one surface. The seven surface keys in the contract are the v1 module keys; additional product areas (memory, voice, settings, admin, …) register as further surface keys in a later `schema_version` bump, not as a second vocabulary.

**The seam between layers is a closed custom-property vocabulary.** Modules declare which tokens they consume. Skins supply values. Components read values. Nothing crosses layers except `--skin-*` names.

### 2.2 Component diagram (runtime)

```
                    Django Ninja                         Lit 3.x webui
              ┌──────────────────────┐          ┌─────────────────────────────┐
              │  GET /ui/skins        │          │  skin-boot.ts               │
              │  GET /ui/skins/active │──────────►│    │                      │
              │  POST /ui/skins       │          │    ▼                      │
              │  PUT  /ui/skins/{id}  │          │  SkinApplier              │
              │  PATCH .../approve    │          │    │  resolve             │
              │  PATCH .../reject     │          │    │  sanitise (client)   │
              └──────────┬───────────┘          │    │  write tokens        │
                         │                      │    ▼                      │
              ┌──────────▼───────────┐          │  :root / skin hosts        │
              │  SkinsStore (Redis)  │          │  [data-skin-surface="…"]    │
              │  skins:{tenant}      │          │  generated component sheet │
              │  skins:id:{id}       │          │         │                  │
              │  REAL get/update/    │          │         ▼                  │
              │  delete/approve/     │          │  Lit shadow roots          │
              │  reject              │          │  var(--skin-*) inherit     │
              └──────────────────────┘          └─────────────────────────────┘

  Resolution chain (server-side, per token):
  Capsule.persona_config.skin  →  AgentSetting(key="skin")  →  UISetting(tenant,"skin.default")  →  platform default
```

### 2.3 File layout (target)

```
webui/src/
  skin-sdk/
    types.ts              SkinManifest, TokenMap, SurfaceOverride, ComponentOverride
    schema.ts             runtime validation (names, domains, size, X-rules)
    tokens.ts             canonical vocabulary + alias map (--platform-*, --soma-*)
    templates.ts          shipped template packs (platform-light, platform-dark, …)
    author.ts             authoring helpers: fromTemplate, validate, diff, preview
    applier.ts            SkinApplier class (resolve → sanitise → write)
    index.ts              public SDK surface
  surfaces/
    registry.ts           surface/module registry (surface keys, style slots, component tags)
    chat.surface.ts       surface declaration (style slots) — key `chat`
    sidebar.surface.ts    key `sidebar`
    … one file per surface key (contract §3.3)
  services/
    theme-boot.ts         (kept) light/dark polarity
    skin-boot.ts          NEW: fetch + apply active skin on boot
  styles/
    tokens.css            (kept during migration) --platform-* definitions
    skin-aliases.css      NEW: --platform-* / --soma-* → --skin-* bridge

services/common/skins/
    __init__.py
    schema.py             pydantic SkinManifest (mirrors types.ts)
    sanitizer.py          X-1…X-12 + A11Y-1 contrast check
    store.py              REAL Redis store (replaces skins_store.py stubs)
    templates.py          shipped template documents
    resolve.py            four-source resolution chain

admin/ui/api/skins.py     (extended) manifest-aware CRUD
```

---

## 3. Token system design

### 3.1 Decision: canonical vocabulary is `--skin-*`

Per `SOMA-UI-SKINS-001.md` §3.2. Skins **write** only `--skin-*` names. The vocabulary is closed; unknown names are rejected (X-2/X-3).

**Why not keep `--platform-*`?** The prefix is product-palette-tied, the file mixes light/dark aliases inconsistently, and `--soma-*` already forked a second namespace. One closed contract independent of palette is what makes skins portable across Capsules.

### 3.2 Canonical token groups (v1 freeze)

The full name list is normative in `SOMA-UI-SKINS-001.md` §3.2 and is **not duplicated** here. Summary of groups:

| Group | Count | Value domain |
|---|---|---|
| Colour — base (bg-void/base/card/sidebar/hover/active) | 6 | CSS colour |
| Colour — text (primary/secondary/muted/inverse/link) | 5 | CSS colour |
| Colour — accent (accent/accent-hover/accent-text) | 3 | CSS colour |
| Colour — semantic (success/warning/danger/info + text) | 8 | CSS colour |
| Colour — border (border/border-strong/border-subtle) | 3 | CSS colour |
| Type — family (sans/mono) | 2 | font-family list |
| Type — scale (xs…2xl) | 6 | length |
| Type — weight (normal…bold) | 4 | number 100–900 |
| Type — leading (tight/normal/relaxed) | 3 | number |
| Spacing (xs…2xl) | 6 | length |
| Radius (sm…full) | 5 | length |
| Elevation (sm/md/lg/overlay) | 4 | shadow list |
| Motion (fast/normal/slow/ease) | 4 | time / timing function |
| Focus (ring colour / ring width / ring offset) — **added** | 3 | colour / length |

The focus trio resolves `SOMA-UI-SKINS-001.md` OPEN-12: A11Y-3 needs a token to test. Without it, focus styling stays in components and cannot be skinned. Adding three tokens is a small, necessary expansion of §3.2.

**Total core tokens: 62.** Documented in `webui/src/skin-sdk/tokens.ts` as the single source of the name set. The Python schema imports the same list (generated or checked by test).

### 3.3 Alias bridge (migration without a big-bang rewrite)

Today's code reads `--platform-*` (435 sites) and `--soma-*` (1118 sites). Rewriting every read before any skin can apply is a multi-thousand-line migration with no user-visible value until the end. The architecture therefore ships a **bridge** first:

```css
/* webui/src/styles/skin-aliases.css — loaded after tokens.css */
:root {
  /* Colour — base */
  --platform-bg-void:        var(--skin-color-bg-void);
  --platform-bg-base:        var(--skin-color-bg-base);
  --platform-bg-card:        var(--skin-color-bg-card);
  --platform-bg-sidebar:     var(--skin-color-bg-sidebar);
  --platform-bg-hover:       var(--skin-color-bg-hover);
  --platform-bg-active:      var(--skin-color-bg-active);
  --platform-bg-page:        var(--skin-color-bg-base);
  /* …every --platform-* and --soma-* name maps to a --skin-* name… */

  /* --soma-* aliases (second namespace) */
  --soma-bg-page:            var(--skin-color-bg-base);
  --soma-bg-card:            var(--skin-color-bg-card);
  --soma-text-primary:       var(--skin-color-text-primary);
  --soma-accent:             var(--skin-color-accent);
  /* …complete map in tokens.ts ALIAS_TABLE … */
}
```

| Rule | Statement |
|---|---|
| T-bridge-1 | The bridge is generated from `ALIAS_TABLE` in `webui/src/skin-sdk/tokens.ts`, not hand-written. A test asserts every alias name used in `webui/src/` appears in the table. |
| T-bridge-2 | The bridge exists only during migration (Phase 2). Component reads are progressively rewritten to `var(--skin-*)`. When the alias-use count reaches zero, the bridge is deleted. |
| T-bridge-3 | Skins **never** write `--platform-*` or `--soma-*`. The alias direction is one-way: skin → bridge → legacy read. |
| T-bridge-4 | `tokens.css` keeps its existing definitions during migration so a no-skin boot still paints. Once Phase 2 completes, `tokens.css` is reduced to the platform-default skin compiled from the same values (SOMA-UI-SKINS-001 §3.5). |

### 3.4 Token authoring rules (for skin authors)

| Rule | Statement |
|---|---|
| T-a-1 | A skin MUST define every required core token (template contract T-2). Partial skins are rejected at the API boundary; they are not "filled with fallbacks" at render time. |
| T-a-2 | Surface/module/component overrides MAY define a subset. Unset tokens inherit from the parent scope. |
| T-a-3 | Values are literals only. No `var()` inside skin values in v1 (OPEN-08 decision: **ban**). |
| T-a-4 | Colours are `#rgb`, `#rrggbb`, `rgb()`, `rgba()`, `hsl()`, `hsla()`, or named colours. No `url()`, no `image-set()`. |

---

## 4. Skin manifest schema

### 4.1 Top-level document

```jsonc
{
  "schema_version": "1",
  "name": "northwind-support",
  "description": "Cool slate, high-contrast chat",
  "template": "slate-cool",
  "meta": {
    "author": "platform-ops",
    "version": "1.0.0",
    "changelog": [
      { "version": "1.0.0", "date": "2026-10-12", "note": "From slate-cool" }
    ]
  },
  "tokens": { /* required core token map — see §3.2 */ },
  "surfaces": { /* optional per-surface token overrides — contract §3.3 */ },
  "components": { /* optional per-component token overrides — §4.4 */ },
  "polarity": { /* optional: "dark" map; see §4.5 */ }
}
```

| Key | Type | Required | Meaning |
|---|---|---|---|
| `schema_version` | string | yes | `"1"`. Unknown → reject fail-closed (X-1). |
| `name` | string | yes | 1–50 chars. Unique per tenant. |
| `description` | string | no | 0–200 chars. |
| `template` | string | no | Template name this skin started from. Informational. |
| `meta` | object | no | `author`, `version` (semver), `changelog` (≤50). Never read by the renderer. |
| `tokens` | object | yes | Core token map. Every §3.2 name present. |
| `surfaces` | object | no | Per-surface token overrides. Keys from the contract §3.3 surface list. §4.3. |
| `components` | object | no | Per-component token overrides. §4.4. |
| `polarity` | object | no | `dark` / `light` variant maps. §4.5. |

**Binding to `SOMA-UI-SKINS-001.md` §3.1.** The top-level keys `schema_version`, `name`, `description`, `template`, `tokens`, `surfaces`, `meta` are **exactly** the contract's shape — this architecture does not rename or fork them. The single addition to the document shape is `components` (per-component token overrides) and `polarity` (OPEN-04 resolution). `components` is additive and optional; a contract-shaped skin without it remains valid. If the contract's next revision adopts `components` / `polarity`, no migration is needed — both are already optional keys.

### 4.2 Core token map (`tokens`)

Same names as `SOMA-UI-SKINS-001.md` §3.2 plus the focus trio (§3.2 above). Example is in that spec §3.4 and is not duplicated.

### 4.3 Surface overrides (`surfaces`) — module style slots keyed to the surface list

Keys are the contract's surface list (`SOMA-UI-SKINS-001.md` §3.3): `chat`, `sidebar`, `composer`, `tool_timeline`, `login`, `chrome`, `right_panel`. Each key resolves to a UI module that declares its style slots (§5).

```jsonc
"surfaces": {
  "chat": {
    "tokens": {
      "--skin-color-bg-card": "#1a222d",
      "--skin-radius-md": "10px"
    }
  },
  "sidebar": {
    "tokens": {
      "--skin-color-bg-sidebar": "#0c1117",
      "--skin-space-md": "12px"
    }
  },
  "login": {
    "tokens": {
      "--skin-color-bg-void": "#0a0e13",
      "--skin-shadow-overlay": "0 24px 64px rgba(0,0,0,0.65)"
    }
  }
}
```

| Rule | Statement |
|---|---|
| M-1 | Surface keys MUST be one of the contract §3.3 keys (v1) or a key registered in the surface registry for a later `schema_version`. Unknown key → reject (X-2). |
| M-2 | A surface override contains only `tokens`. No free CSS. No selectors. No new token names. |
| M-3 | Surface tokens are written to the surface's host element (`[data-skin-surface="chat"]`). They override core tokens inside that subtree only. |
| M-4 | Inheritance: surface host → component host → shadow root. A token unset in a surface falls through to core `tokens`. |
| M-5 | A surface override's token names MUST appear in that surface module's declared style slots (§5.2). A token the module does not declare is rejected — typo-driven dead overrides are errors, not silence. |

### 4.4 Component overrides (`components`)

```jsonc
"components": {
  "soma-button": {
    "tokens": {
      "--skin-color-accent": "#ff4d00",
      "--skin-radius-md": "2px"
    }
  },
  "soma-glass-modal": {
    "tokens": {
      "--skin-shadow-overlay": "0 24px 64px rgba(0,0,0,0.65)"
    }
  }
}
```

| Rule | Statement |
|---|---|
| K-1 | Component keys MUST be registered custom-element tags from the component registry. Unknown tag → reject. |
| K-2 | Component overrides contain only `tokens`. Values only. |
| K-3 | Application method: the SkinApplier generates a **stylesheet whose selectors come from the registry, never from skin data**. Skin data supplies only `--skin-*: <value>` declarations. This satisfies C-1 ("never selectors from skin data") while allowing per-component scoping. |
| K-4 | Generated sheet example (applier output, not author input): |

```css
/* generated by SkinApplier — selectors from registry, values from skin */
[data-skin-scope] soma-button {
  --skin-color-accent: #ff4d00;
  --skin-radius-md: 2px;
}
[data-skin-scope] soma-glass-modal {
  --skin-shadow-overlay: 0 24px 64px rgba(0,0,0,0.65);
}
```

| Rule | Statement |
|---|---|
| K-5 | The generated sheet is a `CSSStyleSheet` adopted via `document.adoptedStyleSheets` (or a single `<style id="skin-components">` element owned by the applier). It is **replaced wholesale** on skin change. No accumulation. |
| K-6 | Component overrides MAY NOT introduce token names outside §3.2. |

### 4.5 Polarity variants (`polarity`)

Resolves OPEN-04: **v1 ships one map per skin plus an optional `polarity.dark` / `polarity.light` map.**

```jsonc
"polarity": {
  "dark": {
    "tokens": { /* subset or full core map */ },
    "surfaces": { /* optional */ },
    "components": { /* optional */ }
  }
}
```

| Rule | Statement |
|---|---|
| P-1 | `theme-boot.ts` keeps owning `data-theme`. When polarity flips, the applier re-resolves: core map ← `polarity.{theme}` overlaid on `tokens`, then surfaces, then components. |
| P-2 | A skin without `polarity` applies its single map in both polarities. That is allowed; templates that ship both variants are preferred. |
| P-3 | The applier writes `--skin-motion-*: 0ms` under `prefers-reduced-motion: reduce` regardless of skin values (A11Y-4). |

### 4.6 Size and limit envelope (X-8, restated)

| Limit | Value | Behaviour on exceed |
|---|---|---|
| Document size | ≤ 32 KiB UTF-8 | reject whole |
| Core tokens | ≤ 128 | reject |
| Surface overrides | ≤ 8 surfaces × ≤ 64 tokens (contract X-8) | reject |
| Component overrides | ≤ 32 components × ≤ 32 tokens | reject |
| Value length | ≤ 256 chars | reject |
| `meta.changelog` | ≤ 50 entries | reject |

### 4.7 Storage mapping (backend)

The existing `SkinRecord.variables: Dict[str,str]` is **insufficient**. The architecture extends the record without a PostgreSQL migration (Redis store):

```python
# services/common/skins/store.py
@dataclass
class SkinRecord:
    skin_id: str
    tenant_id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    manifest: dict = field(default_factory=dict)   # full SkinManifest document
    variables: dict = field(default_factory=dict)  # DEPRECATED: flattened core tokens
    changelog: list = field(default_factory=list)
    is_approved: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
```

| Rule | Statement |
|---|---|
| S-1 | `manifest` is the authoritative document. `variables` is written as a flatten of `manifest["tokens"]` for backward compatibility with any existing readers, and is **derived**, never authoritative. |
| S-2 | Redis keys: `skins:{tenant}` (id list) + `skin:{skin_id}` (record). `get()`, `update()`, `delete()`, `approve()`, `reject()` are **real** implementations — no `pass`, no `return None` stubs (C-3). |
| S-3 | `get(skin_id)` indexes by `skin:{skin_id}`. The current "scan all tenant keys" comment is replaced by a direct key read. |

---

## 5. Module and style structure (slots keyed to the surface list)

### 5.1 What a UI module is

A **UI module** is the named group of Lit components and views that render one **surface** from the contract's surface list (`SOMA-UI-SKINS-001.md` §3.3). It is a logical registry entry — not necessarily a directory move. Physical reorganisation under `webui/src/surfaces/` is optional and deferred.

**v1 surface keys (contract §3.3) → UI module → current elements:**

| Surface key (skin `surfaces.{key}`) | UI module | Covers (current elements) | Example tags |
|---|---|---|---|
| `chat` | `chat` | Workspace, message, composer body, tool timeline, topbar | `soma-chat`, `soma-message`, `soma-tool-timeline`, `soma-chat-topbar` |
| `sidebar` | `sidebar` | Left rail, capsule switcher, nav | `soma-sidebar` |
| `composer` | `composer` | Input, attach menu, send control | `soma-composer`, `soma-composer-menu` |
| `tool_timeline` | `tool_timeline` | Tool-call timeline rows | `soma-tool-timeline` |
| `login` | `auth` | Auth screens | `soma-login`, `soma-register`, `soma-forgot-password`, `soma-mfa-setup` |
| `chrome` | `chrome` | Global header, facet tabs, instance strip | `soma-agent-header`, workspace shell |
| `right_panel` | `right_panel` | Right-rail surfaces | `soma-right-panel` |

The seven keys above are the **only** `surfaces` keys accepted in `schema_version: "1"` (contract OPEN-03 default). Modal (`soma-glass-modal`) and tables (`soma-data-table`) inherit core tokens in v1, as the contract states.

**Beyond v1.** Additional product areas already exist in the codebase (memory, voice, settings, admin, dashboard, profile, cognitive) and shared primitives (`soma-button`, `soma-select`, `soma-toggle`, `soma-data-table`, `soma-glass-modal`, …). They are skinned through core `tokens` and `components` overrides in v1. Promoting any of them to a first-class surface key is a `schema_version` bump, not a silent key invention.

### 5.2 Surface module declaration (style slots)

Each surface module declares its **style slots** — the closed set of `--skin-*` token names that surface is allowed to override — and the component tags it owns. This is the contract skin authors code against.

```typescript
// webui/src/surfaces/chat.surface.ts
import { defineSurface } from './registry.js';

export default defineSurface({
  key: 'chat',                    // must equal contract §3.3 surface key
  title: 'Chat workspace',
  hostAttribute: 'data-skin-surface',
  components: [
    'soma-chat', 'soma-message',
    'soma-chat-topbar', 'soma-welcome-dashboard', 'soma-capsule-editor',
  ],
  styleSlots: {
    // slot name → token names this slot controls
    surface: [
      '--skin-color-bg-card',
      '--skin-color-bg-hover',
      '--skin-color-bg-active',
      '--skin-color-border',
    ],
    typography: [
      '--skin-text-base',
      '--skin-text-sm',
      '--skin-font-sans',
    ],
    accent: [
      '--skin-color-accent',
      '--skin-color-accent-hover',
      '--skin-color-accent-text',
    ],
    elevation: [
      '--skin-shadow-sm',
      '--skin-shadow-md',
      '--skin-shadow-lg',
    ],
  },
});
```

| Rule | Statement |
|---|---|
| U-1 | `webui/src/surfaces/registry.ts` is the **only** authority for surface keys, style slots, and component tags. The Python schema loads the same list (JSON export or test-enforced parity). |
| U-2 | `styleSlots` is documentation + validation, not a second token vocabulary. Slot names are human labels; token names are the `--skin-*` contract. |
| U-3 | A skin's `surfaces.{key}.tokens` is validated against that surface module's declared slots (M-5). |
| U-4 | Components listed in a surface MUST sit under a `[data-skin-surface="{key}"]` host (or carry the attribute on their own root). Nested inheritance covers composed views. |
| U-5 | Surface keys in the registry MUST match the contract §3.3 list exactly for `schema_version: "1"`. A test enforces set equality. |

### 5.3 How components consume tokens

**Target pattern** (post-migration):

```typescript
// webui/src/components/soma-button.ts
static styles = css`
  :host { display: inline-block; }
  button {
    background: var(--skin-color-accent);
    color: var(--skin-color-accent-text);
    border-radius: var(--skin-radius-md);
    font-family: var(--skin-font-sans);
    transition: background var(--skin-motion-fast) var(--skin-motion-ease);
  }
`;
```

| Rule | Statement |
|---|---|
| V-1 | Components read `var(--skin-*)` with **no fallback literal** once a token exists. A fallback silently preserves the hard-coded look when a skin fails and hides errors. |
| V-2 | During the migration window only, `var(--skin-*, var(--platform-*))` is allowed. The window is tracked by an alias-use counter and closes in Phase 2. |
| V-3 | Components do not read `localStorage`, do not fetch skins, and do not branch on theme. The applier writes; components paint. |
| V-4 | Structure and behaviour stay in the component. Skins cannot hide a button, move a sidebar, or change a label (C-6). |

### 5.4 Style-slot declaration for primitives

Primitives (`soma-button`, `soma-select`, …) declare the **part tokens** they expose. This is what makes component-level skin overrides meaningful:

```typescript
// webui/src/skin-sdk/tokens.ts (excerpt)
export const COMPONENT_SLOTS = {
  'soma-button': {
    tokens: [
      '--skin-color-accent', '--skin-color-accent-hover', '--skin-color-accent-text',
      '--skin-radius-md', '--skin-font-sans', '--skin-text-base', '--skin-motion-fast',
    ],
  },
  'soma-glass-modal': {
    tokens: [
      '--skin-color-bg-card', '--skin-color-border',
      '--skin-radius-lg', '--skin-shadow-overlay',
    ],
  },
  // … every skinnable primitive
} as const;
```

`COMPONENT_SLOTS` is generated from what each component's `static styles` actually reads (a CI check greps `var(--skin-…)` inside each component and asserts it ⊆ the declared list).

---

## 6. Runtime application flow

### 6.1 Boot sequence

```
index.html
  └─ <style id="soma-brand">        (kept until Phase 2; then deleted)
  └─ src/main.ts
       ├─ import styles/tokens.css
       ├─ import styles/skin-aliases.css      (NEW)
       ├─ import services/theme-boot.js       (polarity)
       └─ import services/skin-boot.js        (NEW)
            │
            ├─ 1. read localStorage preview flag (if any)
            ├─ 2. GET /api/v2/ui/skins/active   (resolved skin document)
            ├─ 3. sanitise client-side (schema.ts)
            ├─ 4. SkinApplier.apply(manifest, host)
            ├─ 5. dispatch 'soma-skin-ready'
            └─ 6. subscribe 'soma-theme-change' → re-resolve polarity
```

### 6.2 SkinApplier algorithm

```
apply(manifest, rootHost):
  1. validate = schema.validate(manifest)          # X-1…X-8
     if fail → throw SkinRejected(findings); do not write anything
  2. core = manifest.tokens
     if polarity active and manifest.polarity[active]:
        core = { ...core, ...manifest.polarity[active].tokens }
  3. writeTokens(rootHost, core)                   # setProperty --skin-*: value
  4. for (surfaceKey, override) of manifest.surfaces:
        host = rootHost.querySelector(`[data-skin-surface="${surfaceKey}"]`)
             ?? ensureSurfaceHost(rootHost, surfaceKey)
        writeTokens(host, override.tokens)
  5. sheet = generateComponentSheet(manifest.components, COMPONENT_SLOTS)
        # selectors from registry; declarations are --skin-*: value only
     replaceSkinSheet(sheet)                       # swap one adopted stylesheet
  6. if prefers-reduced-motion:
        rootHost.style.setProperty('--skin-motion-fast', '0ms')
        … (all motion tokens)
  7. return AppliedSkinHandle { revert() }
```

| Rule | Statement |
|---|---|
| F-1 | `writeTokens` uses `HTMLElement.style.setProperty('--skin-…', value)`. Never `innerHTML`, never `unsafeCSS`, never a selector built from skin strings. |
| F-2 | Hot-swap: `apply` again with a new manifest. Previous handle `revert()` restores the prior property map. No navigation, no re-render of Lit trees. CSS custom properties update live. |
| F-3 | Preview = `apply` with a session-scoped handle and no persistence. Leaving the preview UI calls `revert()`. |
| F-4 | Client sanitiser **re-runs** even though the server sanitised on write (SEC-6). A compromised store row must not apply blindly. |
| F-5 | Failure is visible: `apply` throwing dispatches `soma-skin-error` with findings. The chrome shows a non-blocking notice (OPEN-05 decision: **both** user notice and ops log). |

### 6.3 Multi-agent isolation

```
workspace root
  ├─ [data-skin-host="agent:atlas"]     ← northwind-support tokens
  │    ├─ [data-skin-surface="chat"]
  │    └─ [data-skin-surface="chrome"]  (agent-scoped chrome if any)
  ├─ [data-skin-host="agent:helix"]     ← paper-light tokens
  │    └─ [data-skin-surface="chat"]
  └─ platform chrome (no agent host)    ← tenant/platform default
```

| Rule | Statement |
|---|---|
| I-1 | Single-agent views MAY use `document.documentElement` as the skin host. |
| I-2 | Multi-agent views MUST give each agent subtree its own `[data-skin-host]`. The applier writes only on that host. |
| I-3 | Sibling hosts do not share properties. A property written on A is invisible under B (CSS inheritance stops at the host boundary when both define it; unset tokens fall through — so every agent host MUST receive a **complete** resolved map, not a delta). |
| I-4 | Platform chrome outside any agent host resolves the tenant/platform default, never a Capsule skin (I-5 in the feature contract). |

**Critical implementation note:** because CSS custom properties inherit downward, an agent host must receive the **fully resolved** token map (all 62 core tokens), not just the tokens the Capsule skin overrode. Otherwise unset tokens leak from `:root` (the platform skin). The applier therefore always writes the complete map per host.

### 6.4 Settings UI flow

Lives in **Settings → Interface** (`soma-settings.ts` `_renderInterfaceTab`), extended with a Skins section. Rationale for Settings rather than Soul (OPEN-14): skins are applied from settings per the operator requirement, while Capsule binding remains available for agent identity. Both paths exist; the settings surface is the operator's daily driver.

```
Settings · Interface
├─ Polarity: [Light | Dark]                     (existing, kept)
├─ Skin:      [ platform-light ▾ ]              (NEW — active skin select)
│             [ Preview ] [ Apply ] [ Revert ]  (NEW)
│             [ Create from template… ]         (NEW)
├─ Language   (existing)
└─ Timezone   (existing)
```

| Behaviour | Requirement |
|---|---|
| List | `GET /api/v2/ui/skins` → cards: name, description, version, author, approved state. Unapproved visible only to `org:manage` (existing `_may_see_unapproved`). |
| Select | Choosing a skin calls `GET /api/v2/ui/skins/{id}` → client sanitise → `SkinApplier.apply` (preview). |
| Apply | Persists the choice (see §6.5) and leaves the preview handle committed. |
| Revert | `handle.revert()` → previous skin restored. No reload. |
| Create from template | Pick template → edit 6–12 token values in a small form → validate (client + server) → `POST /api/v2/ui/skins`. |
| Assign scope | Radio: *My preference* / *Tenant default* / *This agent* (when an agent context is active). |

### 6.5 Persistence of the choice

| Scope | Store | Key |
|---|---|---|
| User preference | `UserPreferences` (extend) | add `skin_id` UUID nullable. Existing `theme` stays for polarity. |
| Tenant default | `UISetting` | `(tenant, user_id="", key="skin.default")` → skin_id |
| Agent / Capsule | `Capsule.persona_config.skin` or `Agent.skin_id` | per feature contract §2.3 / existing field |

Resolution chain on the server (`GET /ui/skins/active`):

```
Capsule.persona_config.skin  (if agent context)
  → AgentSetting(key="skin")
  → UISetting(tenant, key="skin.default")
  → UserPreferences.skin_id
  → platform default manifest
```

This matches `SOMA-UI-SKINS-001.md` §4.1 with `UserPreferences.skin_id` added as the personal layer (the operator's "applied easily from settings" path). Per-token merge semantics as specified there.

### 6.6 API contract additions

Existing routes stay. Additions (all under `admin/ui/api/skins.py` or a thin `admin/ui/api/skin_apply.py`):

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v2/ui/skins` | List (exists) |
| `GET` | `/api/v2/ui/skins/{id}` | Get one (exists; **fix** `SkinsStore.get`) |
| `POST` | `/api/v2/ui/skins` | Create from manifest (exists; **extend** body to full manifest) |
| `PUT` | `/api/v2/ui/skins/{id}` | Update (exists; **fix** store) |
| `DELETE` | `/api/v2/ui/skins/{id}` | Delete (exists; **fix** store) |
| `PATCH` | `/api/v2/ui/skins/{id}/approve` | Approve (exists; **fix** store) |
| `PATCH` | `/api/v2/ui/skins/{id}/reject` | Reject (exists; **fix** store) |
| `GET` | `/api/v2/ui/skins/active` | **NEW** — resolved skin for caller + optional `?agent_id=` |
| `GET` | `/api/v2/ui/skins/templates` | **NEW** — shipped template list |
| `PUT` | `/api/v2/ui/skins/active` | **NEW** — set preference scope (`user` \| `tenant` \| `agent`) |

Request/response models are the pydantic `SkinManifest` (`services/common/skins/schema.py`). The old `variables: dict[str,str]` field remains in responses as a derived flatten during the compatibility window.

---

## 7. Skin SDK (developer / agent authoring)

### 7.1 Goal

A developer or coding agent authors a new skin **in minutes** from a template, with validation before it ever reaches the server, and without touching `webui/src/`.

### 7.2 SDK surface

```typescript
// webui/src/skin-sdk/index.ts — the whole public API
export type {
  SkinManifest, TokenMap, SurfaceOverrides, ComponentOverrides,
  SkinValidationFinding, SkinTemplate,
} from './types.js';

export {
  TOKENS, ALIAS_TABLE, COMPONENT_SLOTS, SURFACES,
} from './tokens.js';

export {
  validate,            // (manifest) => { ok, findings }
  fromTemplate,        // (templateName, patch) => SkinManifest
  diff,                // (a, b) => TokenMap
  flatten,             // (manifest, polarity?) => TokenMap
  apply,               // (manifest, host?) => AppliedSkinHandle
  preview,             // (manifest) => AppliedSkinHandle
  revert,
} from './author.js';

export { TEMPLATES } from './templates.js';
```

### 7.3 Authoring workflow (target: < 10 minutes)

```
1. Pick a template          fromTemplate('slate-cool', {})
2. Override 6–12 tokens     { '--skin-color-accent': '#FF4D00', … }
3. Optional surface tweaks  { surfaces: { chat: { tokens: { … } } } }
4. Validate locally         validate(manifest)  → findings[]
5. Preview live             preview(manifest)   → one-frame paint
6. Save                     POST /api/v2/ui/skins  (server sanitises again)
7. Assign                   PUT  /api/v2/ui/skins/active
```

Steps 1–5 run entirely client-side. Step 6 is the first server round-trip. The coding-agent path is identical via HTTP: the agent POSTs a manifest JSON and receives findings on failure.

### 7.4 Template packs (v1 ship list)

| Template | Purpose | Source |
|---|---|---|
| `platform-light` | Reproduces shipped light palette | `tokens.css` `:root` + Soma Platform light block |
| `platform-dark` | Reproduces shipped dark palette | `tokens.css` `[data-theme="dark"]` + `#soma-brand` |
| `slate-cool` | Cool slate, high-contrast chat | new |
| `paper-light` | Warm paper, editorial | new |
| `high-contrast` | A11y-forward, maximum contrast | new |

Template contract T-1…T-6 from `SOMA-UI-SKINS-001.md` §5.3 binds. Templates are complete token maps with empty `surfaces`/`components` (contract T-5).

### 7.5 Python twin (server validation)

`services/common/skins/schema.py` defines the same manifest shape with pydantic. A shared JSON Schema (`schemas/skin-manifest.schema.json`) is the third artefact; a test asserts TS types, pydantic models, and the JSON Schema agree on required keys and enums. **One contract, three bindings, parity-tested.**

### 7.6 What the SDK deliberately does not provide

| Not provided | Why |
|---|---|
| Free-form CSS editor | C-1: values only. |
| Layout / structure editing | C-6. |
| Remote font/image picker | SEC-2: no network I/O from skins. |
| Runtime script in a skin | SEC-1. |

---

## 8. Security and sanitisation (architecture summary)

The full threat model and X-1…X-12 live in `SOMA-UI-SKINS-001.md` §8. Architecture-level commitments:

| ID | Commitment |
|---|---|
| SEC-A-1 | `services/common/skins/sanitizer.py` **replaces** `validate_no_xss`. Not an extension. It enforces X-1…X-12 plus A11Y-1 contrast. |
| SEC-A-2 | Sanitiser runs on **every write** and **every apply**. |
| SEC-A-3 | Component sheet selectors come from `COMPONENT_SLOTS` (registry), never from skin strings. |
| SEC-A-4 | `policy/skins.rego` is rewritten onto catalog permissions (`org:read` / `system:configure`, `resource="skins"`) and drops `skin:*` action names (OPEN-10 decision: **yes**). |
| SEC-A-5 | Tenant isolation: every store read is tenant-scoped; cross-tenant get/assign returns 404 (AC-14). |

---

## 9. Accessibility floor (architecture summary)

| ID | Commitment |
|---|---|
| A11Y-A-1 | Sanitiser computes WCAG AA contrast on declared text pairs and rejects below-floor skins (AC-08). |
| A11Y-A-2 | Focus ring tokens exist in the vocabulary (§3.2) so A11Y-3 is testable. |
| A11Y-A-3 | Applier forces `--skin-motion-*: 0ms` under `prefers-reduced-motion: reduce` (AC-09). |
| A11Y-A-4 | Shipped templates pass the floor; a fixture test asserts it. |

---

## 10. Trade-off analysis (key decisions)

### D-1: Token rename `--platform-*` → `--skin-*` with an alias bridge

| | |
|---|---|
| **Pros** | One closed contract; skins portable; decouples vocabulary from product palette; enables component overrides by name. |
| **Cons** | Two-hop indirection during migration; bridge must be generated and tested; long tail of component read rewrites. |
| **Alternatives** | (a) Keep `--platform-*` as canonical — rejected: name is product-tied and already forked with `--soma-*`. (b) Big-bang rewrite before any skin ships — rejected: thousands of lines, zero user value until the end. |
| **Decision** | **Adopt `--skin-*` + generated alias bridge.** Bridge deleted when alias-use count hits zero. |

### D-2: Surface + component overrides as token maps, not free CSS

| | |
|---|---|
| **Pros** | Satisfies the operator's module/component requirement; keeps C-1 (no injection); registry-driven selectors keep skin data inert. |
| **Cons** | Less expressive than raw CSS; a skin cannot invent new visual effects outside the token set. |
| **Alternatives** | (a) Allow scoped CSS blocks — rejected: XSS surface, isolation breach, spec §10 forbids. (b) Tokens only, no module/component layer — rejected: operator explicitly requires module + component granularity. |
| **Decision** | **Token maps at three scopes (core / surface / component). Keys for surfaces are the contract §3.3 list. Selectors generated from registry.** |

### D-3: SkinsStore remains Redis-backed (no PostgreSQL migration)

| | |
|---|---|
| **Pros** | No migration; matches existing store; tenants already keyed; low latency. |
| **Cons** | Redis durability depends on persistence config; not queryable relationally. |
| **Alternatives** | Django ORM table — better durability/queries, but a migration + dual-write window. |
| **Decision** | **v1 stays on Redis with real get/update/delete/approve/reject** (C-3). Durability = Redis AOF/RDB as already required for other stores. An ORM table is a v2 option if audit/query needs appear. |

### D-4: Settings UI is the primary skin switcher (OPEN-14)

| | |
|---|---|
| **Pros** | Matches operator requirement; reuses existing Interface tab; user-scoped preference is the daily path. |
| **Cons** | Capsule-identity view (Soul) also needs an assign path. |
| **Alternatives** | Soul-only — rejected: operator said "applied easily from settings". |
| **Decision** | **Settings → Interface → Skins is primary.** Capsule assign is a secondary path on the agent detail surface. |

### D-5: `polarity` as an in-manifest variant map (OPEN-04)

| | |
|---|---|
| **Pros** | One document per skin; polarity flip re-resolves without a second skin id; templates can ship both. |
| **Cons** | Authoring two maps when a skin wants different dark treatment. |
| **Alternatives** | Two separate skins (light-id / dark-id) — rejected: users pick one skin, not two. |
| **Decision** | **`polarity.dark` / `polarity.light` optional maps.** Single-map skins valid. |

---

## 11. Phased implementation plan

Each phase has a real exit criterion (live behaviour, not a checkbox). No phase leaves a stub behind.

### Phase 0 — Vocabulary freeze and bridge (foundation)

| Work | Detail |
|---|---|
| 0.1 | Freeze §3.2 token list in `webui/src/skin-sdk/tokens.ts` (+ focus trio). |
| 0.2 | Build `ALIAS_TABLE` covering every `--platform-*` and `--soma-*` name in use (grep-derived). |
| 0.3 | Generate `webui/src/styles/skin-aliases.css` from the table. Load after `tokens.css` in `main.ts`. |
| 0.4 | CI check: every `var(--platform-…)` / `var(--soma-…)` in `webui/src/` resolves through the bridge to a `--skin-*` name. |

**Exit:** `make -C webui type-check` green; Playwright chat visual test paints unchanged; alias-use counter instrumented.

### Phase 1 — SDK + sanitiser + real store

| Work | Detail |
|---|---|
| 1.1 | `webui/src/skin-sdk/types.ts`, `schema.ts` (X-1…X-8 client-side). |
| 1.2 | `services/common/skins/schema.py` (pydantic) + `schemas/skin-manifest.schema.json`; parity test. |
| 1.3 | `services/common/skins/sanitizer.py` replacing `validate_no_xss` (X-1…X-12 + A11Y-1). |
| 1.4 | `services/common/skins/store.py` — **real** `get`/`update`/`delete`/`approve`/`reject` on `skin:{id}` + `skins:{tenant}`. |
| 1.5 | Extend `admin/ui/api/skins.py` request/response to full manifest; keep `variables` as derived flatten. |
| 1.6 | Unit tests: sanitiser rejection matrix (each X-rule), store CRUD round-trip on real Redis, schema parity. |

**Exit:** `POST /api/v2/ui/skins` accepts a full manifest, rejects each X-rule class with rule id, `GET/{id}` returns the stored record. **Zero `pass`/`return None` store methods remain.**

### Phase 2 — SkinApplier + polarity + hot-swap

| Work | Detail |
|---|---|
| 2.1 | `webui/src/skin-sdk/applier.ts` — `apply` / `revert` / `preview` per §6.2. |
| 2.2 | `webui/src/services/skin-boot.ts` — fetch `GET /ui/skins/active`, apply on boot, listen to `soma-theme-change`. |
| 2.3 | Component read migration: rewrite `var(--platform-…)` / `var(--soma-…)` / hex fallbacks in `static styles` to `var(--skin-*)`. Instrument alias-use counter to zero. |
| 2.4 | Delete `#soma-brand` block from `index.html` once `platform-dark` template reproduces it (verified by screenshot diff). |
| 2.5 | Reduced-motion enforcement in applier. |

**Exit:** AC-02 (skin data change repaints chrome within 1 rAF, no reload) and AC-10 (revert) pass in Playwright. Alias-use count = 0 → delete `skin-aliases.css`.

### Phase 3 — Surface registry + surface/component overrides

| Work | Detail |
|---|---|
| 3.1 | `webui/src/surfaces/registry.ts` + per-surface declarations keyed to contract §3.3 (§5.2). Set-equality test against the contract surface list. |
| 3.2 | Tag surface hosts with `data-skin-surface`. Composed views inherit. |
| 3.3 | Applier step 4–5: surface host writes + generated component sheet (registry selectors). |
| 3.4 | CI check: every `var(--skin-…)` inside a component is declared in `COMPONENT_SLOTS` / surface style slots. |
| 3.5 | Multi-agent host scoping (`data-skin-host`) for split chat. |

**Exit:** AC-01 (two Capsules, two looks, identical bundle hash) and AC-05 (no leak between agents) pass.

### Phase 4 — Settings UI + templates + authoring

| Work | Detail |
|---|---|
| 4.1 | Ship 5 templates (`platform-light`, `platform-dark`, `slate-cool`, `paper-light`, `high-contrast`). |
| 4.2 | `GET /ui/skins/templates` + `GET|PUT /ui/skins/active`. |
| 4.3 | Settings → Interface → Skins section: list, preview, apply, revert, create-from-template, assign scope. |
| 4.4 | `UserPreferences.skin_id` migration + read/write endpoints. |
| 4.5 | SDK `author.ts` helpers wired to the UI form. |

**Exit:** AC-11 (operator creates a skin from a template and assigns it with `git status` of `webui/src/` clean) passes. AC-12 (platform default when no skin) passes.

### Phase 5 — Capsule binding + resolution chain + isolation hardening

| Work | Detail |
|---|---|
| 5.1 | `resolve.py` four-source chain (Capsule → AgentSetting → UISetting → platform), per-token merge. |
| 5.2 | `GET /ui/skins/active?agent_id=` returns agent-resolved skin. |
| 5.3 | Cross-tenant denial tests (AC-14). |
| 5.4 | Sanitisation-failure notice in chrome + ops log (OPEN-05). |

**Exit:** AC-03, AC-04, AC-12, AC-14 pass.

### Phase 6 — Accessibility + acceptance evidence

| Work | Detail |
|---|---|
| 6.1 | Contrast matrix fixtures for shipped templates (A11Y-1). |
| 6.2 | Focus-ring tests (AC-13). |
| 6.3 | Reduced-motion test (AC-09). |
| 6.4 | Full AC-01…AC-15 Playwright suite green against real services. |
| 6.5 | Evidence filed under `docs/iso/evidence/SOMA-UI-SKINS-001/`. |

**Exit:** Every AC row in `SOMA-UI-SKINS-001.md` §11 marked with evidence. Feature contract status flips from `NOT YET` to met per criterion.

### Phase dependency graph

```
Phase 0 ──► Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 6
                │                      ▲
                └──────► Phase 4 ──────┘
                └──────► Phase 5 ──────┘
```

Phases 3, 4, 5 can proceed in parallel after Phase 2. Phase 6 closes everything.

### Definition of Done (feature)

Human Playwright session green on real services (CLAUDE.md "Done ="), specifically: create skin from template → preview → apply → two agents side by side show different skins → revert → sanitiser rejects a malicious skin → reduced-motion honoured. Not skip-gated, not mocked.

---

## 12. Risk register

| Risk | Impact | Mitigation |
|---|---|---|
| Alias bridge incomplete (a `--soma-*` name missed) | Hard-coded colour reappears | CI grep parity test (Phase 0.4) |
| Component migration stalls | Bridge never deletable | Alias-use counter as a burn-down metric; Phase 2 exit blocks Phase 3 sign-off |
| Redis durability loss | Skins lost | Redis AOF as required for existing stores; export endpoint in Phase 4 |
| Sanitiser gap (X-rule miss) | CSS injection | Rejection matrix test per rule; fuzz values in Phase 1.6 |
| Multi-agent leak via `:root` write | AC-05 fail | Applier always writes full map per host (§6.3); isolation test in Phase 3.5 |
| `#soma-brand` overrides fight the applier | Visual flicker / wrong colours | Delete the block in Phase 2.4 behind a screenshot-diff gate |

---

## 13. RTM (architecture-level)

| ID | Requirement | Traces to |
|---|---|---|
| ARCH-SKIN-001 | One closed `--skin-*` vocabulary with a generated alias bridge | §3, D-1 |
| ARCH-SKIN-002 | Skin manifest extends contract §3.1: tokens + surfaces + components + polarity | §4 |
| ARCH-SKIN-003 | UI module style slots keyed to contract §3.3 surface list; skins validated against them | §5 |
| ARCH-SKIN-004 | Components read only `var(--skin-*)`; no fallbacks after migration | §5.3 |
| ARCH-SKIN-005 | Runtime apply via CSS custom properties; zero re-render; hot-swap + revert | §6.2, F-2 |
| ARCH-SKIN-006 | Multi-agent host isolation with complete resolved maps per host | §6.3, I-1…I-4 |
| ARCH-SKIN-007 | Settings UI lists, previews, applies, creates skins | §6.4 |
| ARCH-SKIN-008 | SDK: types, validate, fromTemplate, preview, apply; author in minutes | §7 |
| ARCH-SKIN-009 | Real store implementations; no stubs | §4.7 S-2, Phase 1.4 |
| ARCH-SKIN-010 | Sanitiser replaces substring denylist; enforce X-1…X-12 + A11Y-1 | §8, Phase 1.3 |

---

## 14. Document Reference Matrix

| Document | Identifier | ISO Reference | Purpose |
|---|---|---|---|
| Skinnable UI Theme System Architecture | SOMA-ARCH-SKINS-001 | ISO 9001:2015 clause 7.5 | Implementation architecture |
| Capsule Skins — Theming Framework Specification | SOMA-UI-SKINS-001 | ISO 9001:2015 clause 7.5 | Feature contract (requirements bind) |

End of Document
