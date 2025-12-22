# AgentSkin UIX Requirements

## Overview

This specification defines the requirements for the AgentSkin UIX (User Interface Experience) system - a comprehensive theming and skinning framework for SomaAgent01's web interface. The system enables dynamic theme switching, custom skin creation, and a theme gallery for users to browse and apply visual styles.

## Current State Analysis

### Existing Architecture

| Component | Location | Status |
|-----------|----------|--------|
| Design Tokens | `webui/design-system/tokens.css` | ✅ 200+ CSS variables defined |
| Theme Loader SDK | `webui/js/theme.js` | ✅ Basic implementation (loadLocal, loadRemote, validate, apply) |
| Alpine Store | `webui/js/AlpineStore.js` | ✅ Reactive state management |
| Theme Files | `webui/themes/*.json` | ✅ 2 themes (default, midnight) |
| Main UI | `webui/index.html` | ⚠️ Monolithic (1323 lines, inline styles) |
| App Styles | `webui/css/app.css` | ✅ Component styles using CSS variables |

### Architecture Issues

1. **Monolithic index.html**: 1323 lines with inline `<style>` blocks duplicating CSS variables
2. **Duplicate Theme Variables**: Variables defined in both `tokens.css` and inline in `index.html`
3. **No Theme Gallery UI**: Users cannot browse/preview themes visually
4. **No Admin Controls**: No upload/approve/reject workflow for themes
5. **No WCAG Validation**: Contrast ratios not validated on theme upload
6. **No Theme Versioning**: No changelog or version tracking

---

## User Stories

### US-AGS-001: Theme Gallery Browsing

**As a** user  
**I want to** browse available themes in a visual gallery  
**So that** I can discover and preview themes before applying them

**Acceptance Criteria:**
1. WHEN a user opens the Theme Gallery THEN the system SHALL display theme cards with preview images
2. WHEN a user hovers over a theme card THEN the system SHALL show a live preview tooltip
3. WHEN a user searches for a theme THEN the system SHALL filter results by name and description
4. WHEN displaying theme cards THEN the system SHALL show name, description, version, and rating
5. THE theme card dimensions SHALL be 280×180 pixels with 12px border radius

### US-AGS-002: One-Click Theme Switching

**As a** user  
**I want to** switch themes with a single click  
**So that** I can quickly change the visual appearance without page reload

**Acceptance Criteria:**
1. WHEN a user clicks "Apply" on a theme THEN the system SHALL apply the theme within 300ms
2. WHEN a theme is applied THEN the system SHALL NOT require a page reload
3. WHEN a theme is applied THEN the system SHALL persist the selection to localStorage
4. WHEN the application loads THEN the system SHALL restore the previously selected theme
5. THE theme switch animation SHALL complete within 300ms using CSS transitions

### US-AGS-003: Theme Live Preview

**As a** user  
**I want to** preview a theme before applying it  
**So that** I can see how it looks without committing to the change

**Acceptance Criteria:**
1. WHEN a user clicks "Preview" on a theme THEN the system SHALL apply the theme temporarily
2. WHEN previewing THEN the system SHALL show a "Cancel Preview" button
3. WHEN a user cancels preview THEN the system SHALL restore the previous theme
4. WHEN a user applies during preview THEN the system SHALL persist the previewed theme
5. THE preview mode SHALL be indicated by a visual banner

### US-AGS-004: Theme Import/Export

**As a** user  
**I want to** import and export themes as JSON files  
**So that** I can share themes with others or backup my customizations

**Acceptance Criteria:**
1. WHEN a user clicks "Export" on a theme THEN the system SHALL download a JSON file
2. WHEN a user drags a JSON file to the gallery THEN the system SHALL validate and import it
3. WHEN importing THEN the system SHALL validate the JSON schema before accepting
4. IF the imported theme is invalid THEN the system SHALL display a descriptive error
5. THE exported JSON SHALL include name, description, version, and all CSS variables

### US-AGS-005: Remote Theme Loading

**As a** user  
**I want to** load themes from HTTPS URLs  
**So that** I can use themes hosted externally

**Acceptance Criteria:**
1. WHEN a user enters a valid HTTPS URL THEN the system SHALL fetch and validate the theme
2. IF the URL is not HTTPS THEN the system SHALL reject it with a security warning
3. WHEN a remote theme is loaded THEN the system SHALL cache it locally
4. IF the remote fetch fails THEN the system SHALL display a descriptive error
5. THE system SHALL support CORS-enabled theme endpoints

### US-AGS-006: Admin Theme Management (ADMIN MODE ONLY)

**As a** system administrator  
**I want to** upload, approve, reject, and delete themes  
**So that** I can curate the theme gallery for all users

**Acceptance Criteria:**
1. WHEN in ADMIN mode THEN the system SHALL show upload/approve/reject/delete controls
2. WHEN NOT in ADMIN mode THEN the system SHALL hide admin controls
3. WHEN an admin uploads a theme THEN the system SHALL validate it before accepting
4. WHEN an admin approves a theme THEN the system SHALL make it visible to all users
5. WHEN an admin rejects a theme THEN the system SHALL remove it from the gallery
6. THE admin controls SHALL be gated by OPA policy check

### US-AGS-007: Custom Palette Creation

**As a** user  
**I want to** create custom color palettes  
**So that** I can personalize my theme beyond preset options

**Acceptance Criteria:**
1. WHEN a user opens the palette editor THEN the system SHALL show color pickers for key variables
2. WHEN a user changes a color THEN the system SHALL validate WCAG AA contrast
3. IF a color fails contrast validation THEN the system SHALL show a warning
4. WHEN a user saves a custom palette THEN the system SHALL create a new theme variant
5. THE palette editor SHALL support at least 10 customizable color variables

### US-AGS-008: Theme Versioning and Changelog

**As a** user  
**I want to** see theme version history and changelogs  
**So that** I can understand what changed between versions

**Acceptance Criteria:**
1. WHEN viewing a theme THEN the system SHALL display the current version
2. WHEN a theme is updated THEN the system SHALL show a "New Version" badge
3. WHEN a user clicks on version info THEN the system SHALL show the changelog
4. THE version format SHALL follow semantic versioning (MAJOR.MINOR.PATCH)
5. THE changelog SHALL be stored in the theme JSON metadata

---

## Technical Requirements

### TR-AGS-001: CSS Variable Architecture

| ID | Requirement | Priority |
|----|-------------|----------|
| TR-AGS-001.1 | All theme colors MUST be defined as CSS custom properties | HIGH |
| TR-AGS-001.2 | The system MUST support 26 required CSS variables (see Appendix A) | HIGH |
| TR-AGS-001.3 | Inline styles in index.html MUST be extracted to external CSS files | HIGH |
| TR-AGS-001.4 | CSS variables MUST cascade from `:root` to all components | HIGH |

### TR-AGS-002: ThemeLoader SDK

| ID | Requirement | Priority |
|----|-------------|----------|
| TR-AGS-002.1 | ThemeLoader MUST implement `loadLocal(name)` method | HIGH |
| TR-AGS-002.2 | ThemeLoader MUST implement `loadRemote(url)` method | HIGH |
| TR-AGS-002.3 | ThemeLoader MUST implement `validate(skin)` method | HIGH |
| TR-AGS-002.4 | ThemeLoader MUST implement `apply(skin)` method | HIGH |
| TR-AGS-002.5 | ThemeLoader MUST implement `use(nameOrUrl)` convenience method | HIGH |
| TR-AGS-002.6 | ThemeLoader MUST implement `switch(name)` with persistence | HIGH |
| TR-AGS-002.7 | ThemeLoader MUST implement `preview(skin)` for temporary application | MEDIUM |
| TR-AGS-002.8 | ThemeLoader MUST implement `cancelPreview()` to restore previous | MEDIUM |

### TR-AGS-003: Alpine.js Integration

| ID | Requirement | Priority |
|----|-------------|----------|
| TR-AGS-003.1 | Theme state MUST be managed via Alpine.js store | HIGH |
| TR-AGS-003.2 | Theme gallery MUST be an Alpine.js component | HIGH |
| TR-AGS-003.3 | Theme switching MUST trigger Alpine reactivity | HIGH |
| TR-AGS-003.4 | No build step required - vanilla Alpine.js only | HIGH |

### TR-AGS-004: Backend API

| ID | Requirement | Priority |
|----|-------------|----------|
| TR-AGS-004.1 | API MUST expose `GET /v1/skins` to list available themes | HIGH |
| TR-AGS-004.2 | API MUST expose `GET /v1/skins/{id}` to get theme details | HIGH |
| TR-AGS-004.3 | API MUST expose `POST /v1/skins` to upload new theme (ADMIN) | HIGH |
| TR-AGS-004.4 | API MUST expose `DELETE /v1/skins/{id}` to remove theme (ADMIN) | HIGH |
| TR-AGS-004.5 | API MUST validate theme JSON schema on upload | HIGH |
| TR-AGS-004.6 | API MUST reject themes with `url()` values (XSS prevention) | HIGH |

### TR-AGS-005: Database Schema

| ID | Requirement | Priority |
|----|-------------|----------|
| TR-AGS-005.1 | Create `agent_skins` table with JSONB variables column | HIGH |
| TR-AGS-005.2 | Include tenant_id for multi-tenancy isolation | HIGH |
| TR-AGS-005.3 | Include version, created_at, updated_at columns | HIGH |
| TR-AGS-005.4 | Include is_approved boolean for admin workflow | HIGH |

---

## Security Requirements

### SEC-AGS-001: Admin Authorization

| ID | Requirement | Priority |
|----|-------------|----------|
| SEC-AGS-001.1 | Theme upload MUST require ADMIN mode | HIGH |
| SEC-AGS-001.2 | Theme deletion MUST require ADMIN mode | HIGH |
| SEC-AGS-001.3 | Admin operations MUST be gated by OPA policy | HIGH |

### SEC-AGS-002: XSS Prevention

| ID | Requirement | Priority |
|----|-------------|----------|
| SEC-AGS-002.1 | Theme JSON MUST NOT contain `url()` CSS values | HIGH |
| SEC-AGS-002.2 | Theme JSON MUST NOT contain `<script>` tags | HIGH |
| SEC-AGS-002.3 | Theme JSON MUST be validated against strict schema | HIGH |
| SEC-AGS-002.4 | Remote theme URLs MUST be HTTPS only | HIGH |

### SEC-AGS-003: Tenant Isolation

| ID | Requirement | Priority |
|----|-------------|----------|
| SEC-AGS-003.1 | All theme queries MUST be scoped by tenant_id | HIGH |
| SEC-AGS-003.2 | Users MUST NOT access themes from other tenants | HIGH |

---

## Performance Requirements

### PERF-AGS-001: Load Times

| ID | Requirement | Priority |
|----|-------------|----------|
| PERF-AGS-001.1 | Theme load time MUST be <100ms p95 | HIGH |
| PERF-AGS-001.2 | Theme switch time MUST be <50ms | HIGH |
| PERF-AGS-001.3 | Gallery render time MUST be <200ms for 50 themes | HIGH |

### PERF-AGS-002: Caching

| ID | Requirement | Priority |
|----|-------------|----------|
| PERF-AGS-002.1 | Theme JSON MUST be cached with `max-age=86400` | MEDIUM |
| PERF-AGS-002.2 | Theme preview images MUST be lazy-loaded | MEDIUM |

---

## Accessibility Requirements

### A11Y-AGS-001: WCAG Compliance

| ID | Requirement | Priority |
|----|-------------|----------|
| A11Y-AGS-001.1 | All themes MUST pass WCAG AA contrast requirements | HIGH |
| A11Y-AGS-001.2 | Theme gallery MUST be keyboard navigable | HIGH |
| A11Y-AGS-001.3 | Theme cards MUST have proper ARIA labels | HIGH |
| A11Y-AGS-001.4 | Color pickers MUST announce changes to screen readers | MEDIUM |

---

## Quality Assurance Requirements

### QA-AGS-001: Unit Tests

| ID | Requirement | Priority |
|----|-------------|----------|
| QA-AGS-001.1 | ThemeLoader validation MUST have unit tests | HIGH |
| QA-AGS-001.2 | XSS blocking MUST have unit tests | HIGH |
| QA-AGS-001.3 | Theme persistence MUST have unit tests | HIGH |

### QA-AGS-002: Integration Tests

| ID | Requirement | Priority |
|----|-------------|----------|
| QA-AGS-002.1 | Theme gallery flow MUST have Playwright E2E tests | HIGH |
| QA-AGS-002.2 | Theme switch flow MUST have Playwright E2E tests | HIGH |
| QA-AGS-002.3 | Drag/drop import MUST have Playwright E2E tests | HIGH |

### QA-AGS-003: Performance Tests

| ID | Requirement | Priority |
|----|-------------|----------|
| QA-AGS-003.1 | Theme load time MUST be measured and asserted <100ms | HIGH |
| QA-AGS-003.2 | Theme switch time MUST be measured and asserted <50ms | HIGH |

---

## Appendix A: Required CSS Variables

The following 26 CSS variables MUST be defined in every theme:

```css
/* Background Colors */
--bg-void
--bg-primary
--bg-secondary
--bg-tertiary

/* Surface Colors */
--surface-1
--surface-2
--surface-3

/* Text Colors */
--text-primary
--text-secondary
--text-muted
--text-main
--text-dim

/* Border Colors */
--border-color
--border-subtle

/* Accent Colors */
--accent-primary
--accent-hover
--accent-subtle

/* Semantic Colors */
--success
--warning
--error
--info

/* Glass Effects */
--glass-surface
--glass-border

/* Legacy Compatibility */
--bg-void (duplicate for legacy)
```

---

## Appendix B: Theme JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["name", "version", "variables"],
  "properties": {
    "name": { "type": "string", "minLength": 1, "maxLength": 50 },
    "description": { "type": "string", "maxLength": 200 },
    "version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" },
    "author": { "type": "string" },
    "variables": {
      "type": "object",
      "additionalProperties": { "type": "string" }
    },
    "changelog": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "version": { "type": "string" },
          "date": { "type": "string", "format": "date" },
          "changes": { "type": "array", "items": { "type": "string" } }
        }
      }
    }
  }
}
```

---

## Dependencies

- Alpine.js 3.x (already in vendor/)
- FastAPI backend (existing)
- PostgreSQL database (existing)
- OPA for admin authorization (existing)

## References

- CANONICAL_REQUIREMENTS.md Section 15 (AGS-*)
- webui/design-system/tokens.css
- webui/js/theme.js
- webui/themes/*.json

---

**Last Updated:** 2025-12-21  
**Status:** DRAFT - Pending Review
