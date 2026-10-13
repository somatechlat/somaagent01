# SOMA-UI-I18N-001 — Internationalization (UI-wide)

## Document Control

| Field | Value |
|---|---|
| Document Title | UI Internationalization Standard |
| Document Identifier | SOMA-UI-I18N-001 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9241-210 · WCAG 2.1 AA (3.1.1 Language of Page) |
| Next Review | 2027-01-13 |
| Source of truth | `webui/src/i18n/` (to implement) · all Lit templates |
| Related | `SOMA-UI-PROFILE-001` · `SOMA-01-UIUX-005` Messages/I18N law |
| Law | Soma law · no mocks · no hardcoded UI English in components |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | SomaTech Engineering | Initial I18N standard for full UI/UX. |

---

## 1. Purpose

**Every** user-visible string in `webui/` is translatable. Locale switch is live (no reload). Default `en`, second locale `es`.

## 2. Rules (Soma + ISO)

| ID | Rule |
|---|---|
| I18N-01 | No literal user-facing English in Lit `html` — use `t('key')` |
| I18N-02 | Keys: `domain.camelCase` (`profile.save`, `files.upload`, `chat.settings`) |
| I18N-03 | Catalogs: `webui/src/i18n/en.json` · `es.json` — complete parity |
| I18N-04 | Dates/numbers via `Intl.DateTimeFormat` / `NumberFormat` |
| I18N-05 | `lang` on `<html>` updates on locale change (WCAG 3.1.1) |
| I18N-06 | Error/success toasts use catalog keys |
| I18N-07 | GATED reasons also translated |
| I18N-08 | No emojis in any locale (Material icons remain) |
| I18N-09 | Feature: Settings › Interface › Language already selects `en`/`es` |
| I18N-10 | Missing key → show key in dev, English fallback in prod + log |

## 3. Architecture

```
webui/src/i18n/
  index.ts        t(), setLocale(), getLocale(), onLocaleChange()
  en.json
  es.json
```

```ts
// Usage in Lit
import { t } from '../i18n/index.js';
html`<button>${t('files.upload')}</button>`
```

Locale persistence: `soma_locale` + Settings Interface language (one source).

## 4. Domain coverage (must be catalogued)

| Domain | Examples |
|---|---|
| `app.*` | brand, chrome, nav |
| `auth.*` | login, register, mfa |
| `chat.*` | composer, tools, settings, display |
| `profile.*` | account, channels, display, security |
| `files.*` | tree, upload, delete, move |
| `memory.*` | recall, remember, forget |
| `brain.*` | modulators, knobs, diagnostics |
| `settings.*` | tabs, models, tools |
| `errors.*` | network, permission, gated reasons |
| `common.*` | save, cancel, close, retry |

## 5. Acceptance

1. Grep: zero hardcoded `Save`/`Cancel`/`Upload`… in `webui/src/components` (excluding code comments).  
2. Switch `es` → chrome + profile + files labels change.  
3. Playwright: locale toggle persists after reload.  

---

**End of I18N Standard.**
