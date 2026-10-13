# CM-08 — Skins Gallery Control Map

## Document Control

| Field | Value |
|---|---|
| Document Title | Control Map — Skins gallery (preview / apply / uninstall / revert / install bundled) |
| Document Identifier | SOMA-UI-CM-08 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | SomaTech Engineering (soma-ui-engineer) |
| Classification | Internal |
| ISO Reference | ISO 9241-210:2019 |
| Next Review | 2027-01-13 |
| Related | `SOMA-UI-SKINS-001.md` · `UI-S-54` settings-interface · `SOMA-UI-MODULE-CATALOG-001.md` skin surfaces |
| Live sources | `webui/src/components/soma-skin-gallery.ts` · `webui/src/services/skin-applier.ts` · `skin-boot.ts` · `theme-boot.ts` · `webui/src/skin-sdk/` |
| Routes | `/themes` · Settings › Interface (embedded gallery) |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | soma-ui-engineer | Skins gallery control map with data-testid inventory and token/surface notes. |

---

## 1. ASCII wireframe

```
┌─ Skins gallery  (/themes or Settings › Interface) ─────────────────────────────────────────────┐
│ SK-01 status line (data-testid=skin-status)                                                     │
│ SK-02 [Install bundled]  SK-03 [Revert] (shown when previewing)                                 │
├────────────────────────────────────────────────────────────────────────────────────────────────┤
│  grid (data-testid=skin-grid)                                                                   │
│  ┌─ card (skin-card) ─────────────┐  ┌─ card ─────────────┐                                    │
│  │ SK-10 swatches (per surface)   │  │ …                   │                                    │
│  │ SK-11 [Active] badge           │  │                     │                                    │
│  │ SK-12 [Apply]                  │  │                     │                                    │
│  │ SK-13 [Preview]                │  │                     │                                    │
│  │ SK-14 [Uninstall]              │  │                     │                                    │
│  └────────────────────────────────┘  └─────────────────────┘                                    │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Control map

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| SK-01 | Status line | readout | `data-testid="skin-status"` local/SDK status | idle, applied, error | — | `status` | LIVE |
| SK-02 | Install bundled | button | `data-testid="skin-install-bundled"` → `_installBundled()` skin-sdk install | default, busy, error | — | `button` | LIVE |
| SK-03 | Revert preview | button | `data-testid="skin-revert"` → `_revert()` | visible while previewing | — | `button` | LIVE |
| SK-10 | Surface swatch | readout | pack surface tokens (`--skin-*` via aliases) | default | — | `img`/swatch with `title` label | LIVE |
| SK-11 | Active badge | readout | `data-testid="skin-active"` | shown on active pack | — | text badge | LIVE |
| SK-12 | Apply | button | `data-testid="skin-apply"` → `_applyPack(pack)` skin-applier | default, busy, applied | — | `button` | LIVE |
| SK-13 | Preview | button | `data-testid="skin-preview"` → `_previewPack(pack)` | default, previewing | — | `button` | LIVE |
| SK-14 | Uninstall | button | `data-testid="skin-uninstall"` → `_uninstall(pack)` | default, confirm, busy | Pack in use / bundled → reason | `button` | LIVE |
| SK-15 | Pack card | surface | skin-sdk pack list | populated, empty, error | — | `region` `data-testid="skin-card"` | LIVE |
| SK-16 | Grid | surface | gallery host | default | — | `data-testid="skin-grid"` | LIVE |
| SK-20 | Import pack (file) | input.file | skin-sdk `install` | default | Import API surface not exposed → “Pack import needs the skin install API.” | `button` + file picker | PLANNED |
| SK-21 | Export current pack | button | skin-sdk `pack` | default | same class of API | `button` | PLANNED |
| SK-22 | Token preview mode | toggle | local preview of surface tokens | on/off | — | `switch` | PLANNED |
| SK-23 | Hardcoded hex audit | readout | — | always in dev | Component hex literals are known debt; aliases map `--platform-*` → `--skin-*` until rename ships | text note | LIVE (note) |
| SK-30 | Apply without persistence claim | — | — | **forbidden** | Apply must go through skin-applier / settings persistence; never claim saved when not | — | GATED (law) |

---

## 3. Skin surfaces (closed vocabulary host map)

| Surface key | Covers | Host module |
|---|---|---|
| chrome | top strip, facet tabs, instance strip | app shell / topbar |
| sidebar | left rail, chat list, nav | `soma-sidebar` |
| chat | message list, bubbles, streaming | `soma-message` |
| composer | input, attach menu, send | `soma-composer` |
| tool_timeline | tool-call rows | `soma-tool-timeline` |
| right_panel | canvas hosts + File Manager | `soma-right-panel`, planned `soma-file-manager` |
| login | auth screens | login family |

Token contract: modules read **only** `var(--skin-*)` (closed vocabulary). No component may invent hex for skinnable chrome (1575 known literals are burn-down debt).

---

## 4. States

| State | Behavior |
|---|---|
| previewing | Revert visible; Apply not claimed until applied |
| applied | Active badge on pack; status line updated |
| uninstall confirm | destructive confirm |
| error | visible error in SK-01; never silent |

---

## 5. Source map

| Source | Role |
|---|---|
| `webui/src/components/soma-skin-gallery.ts` | SK-01…SK-16 |
| `webui/src/services/skin-applier.ts` | Apply / revert DOM token application |
| `webui/src/skin-sdk/install.ts` `pack.ts` `validate.ts` | Install/pack/validate (SK-20/21) |
| `webui/src/services/theme-boot.ts` `skin-boot.ts` | Boot alias map |

End of Document
