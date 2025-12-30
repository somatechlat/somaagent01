# AgentSkin UIX - Implementation Tasks

## Document Control

| Field | Value |
|-------|-------|
| **Document ID** | SA01-AGS-TASKS-2025-12 |
| **Version** | 1.0 |
| **Date** | 2025-12-21 |
| **Status** | CANONICAL |
| **Implements** | SA01-AGS-DESIGN-2025-12 |

---

## Task Overview

| ID | Task | Priority | Effort | Dependencies | Status |
|----|------|----------|--------|--------------|--------|
| T1 | Extract Inline Styles from index.html | P0 | 3h | None | ⏳ PENDING |
| T2 | Enhance ThemeLoader SDK | P0 | 3h | T1 | ⏳ PENDING |
| T3 | Create Theme Lit Controller | P0 | 2h | T2 | ⏳ PENDING |
| T4 | Create Theme Gallery Component | P0 | 4h | T3 | ⏳ PENDING |
| T5 | Create Theme Card Component | P0 | 2h | T3 | ⏳ PENDING |
| T6 | Create Palette Editor Component | P1 | 3h | T3 | ⏳ PENDING |
| T7 | Create Database Migration | P0 | 1h | None | ⏳ PENDING |
| T8 | Create Backend API Endpoints | P0 | 4h | T7 | ✅ COMPLETE |
| T9 | Add XSS Validation | P0 | 2h | T2 | ⏳ PENDING |
| T10 | Add WCAG Contrast Validation | P1 | 2h | T2 | ⏳ PENDING |
| T11 | Add OPA Admin Authorization | P0 | 2h | T8 | ⏳ PENDING |
| T12 | Unit Tests | P1 | 3h | T2, T9 | ⏳ PENDING |
| T13 | Property Tests | P1 | 2h | T2 | ⏳ PENDING |
| T14 | E2E Tests (Playwright) | P2 | 4h | T4-T6 | ⏳ PENDING |
| T15 | Documentation | P2 | 2h | All | ⏳ PENDING |

---

## Phase 1: CSS Architecture Cleanup

### Task 1: Extract Inline Styles from index.html

**Files:**
- `somaAgent01/webui/index.html` (modify)
- `somaAgent01/webui/css/index-extracted.css` (create)

**Requirements:** TR-AGS-001.3

### Acceptance Criteria
- [ ] Extract all inline `<style>` blocks from index.html
- [ ] Create css/index-extracted.css with extracted styles
- [ ] Remove duplicate CSS variables (keep tokens.css as source of truth)
- [ ] Update index.html to link external CSS file
- [ ] Verify no visual regression after extraction
- [ ] Reduce index.html from 1323 lines to <500 lines

### Implementation Notes
```html
<!-- Before: inline styles in index.html -->
<style>
  :root { --bg-void: #0a0a0f; ... }
</style>

<!-- After: external CSS link -->
<link rel="stylesheet" href="/static/css/index-extracted.css">
```

---

## Phase 2: ThemeLoader SDK Enhancement

### Task 2: Enhance ThemeLoader SDK

**File:** `somaAgent01/webui/js/theme.js` (modify existing)

**Requirements:** TR-AGS-002.1 - TR-AGS-002.8

### Acceptance Criteria
- [ ] Verify `loadLocal(name)` loads from /static/themes/{name}.json
- [ ] Verify `loadRemote(url)` validates HTTPS and fetches theme
- [ ] Verify `validate(skin)` checks schema and rejects url() values
- [ ] Verify `apply(skin)` sets CSS variables on :root
- [ ] Add `switch(name)` method with localStorage persistence
- [ ] Add `preview(skin)` method for temporary application
- [ ] Add `cancelPreview()` method to restore previous theme
- [ ] Add `exportTheme(skin)` method returning Blob for download
- [ ] Theme switch completes within 300ms

### Implementation Notes
```javascript
// New methods to add:
const ThemeLoader = {
  // ... existing methods ...
  
  _previousTheme: null,
  _isPreview: false,
  
  async switch(name) {
    const skin = await this.loadLocal(name);
    if (this.validate(skin)) {
      this.apply(skin);
      localStorage.setItem('soma-theme', name);
    }
  },
  
  preview(skin) {
    if (!this._isPreview) {
      this._previousTheme = this.getCurrentTheme();
    }
    this._isPreview = true;
    this.apply(skin);
  },
  
  cancelPreview() {
    if (this._isPreview && this._previousTheme) {
      this.apply(this._previousTheme);
      this._isPreview = false;
    }
  },
  
  exportTheme(skin) {
    const json = JSON.stringify(skin, null, 2);
    return new Blob([json], { type: 'application/json' });
  }
};
```

---

## Phase 3: Lit Web Components Integration

### Task 3: Create Theme Lit Controller

**File:** `somaAgent01/webui/js/controllers/theme-controller.js` (create)

**Requirements:** TR-AGS-003.1 - TR-AGS-003.3

### Acceptance Criteria
- [ ] Creates Lit Reactive Controller for theme state
- [ ] Stores: themes[], currentTheme, previewTheme, isAdmin, searchQuery
- [ ] Implements loadThemes() to fetch from API
- [ ] Implements applyTheme(name) using ThemeLoader
- [ ] Implements uploadTheme(file) for admin upload
- [ ] Implements filterThemes() for search functionality
- [ ] Integrates with Lit component lifecycle

### Implementation Notes
```javascript
// webui/js/controllers/theme-controller.js
import { ReactiveController } from 'lit';

export class ThemeController {
  host;
  themes = [];
  currentTheme = localStorage.getItem('soma-theme') || 'default';
  previewTheme = null;
  isAdmin = false;
  searchQuery = '';
  isLoading = false;

  constructor(host) {
    this.host = host;
    host.addController(this);
  }

  async hostConnected() {
    await this.loadThemes();
    await ThemeLoader.switch(this.currentTheme);
  }

  async loadThemes() {
    this.isLoading = true;
    this.host.requestUpdate();
    const response = await fetch('/v1/skins');
    this.themes = await response.json();
    this.isLoading = false;
    this.host.requestUpdate();
  }

  get filteredThemes() {
    if (!this.searchQuery) return this.themes;
    const q = this.searchQuery.toLowerCase();
    return this.themes.filter(t => 
      t.name.toLowerCase().includes(q) ||
      (t.description || '').toLowerCase().includes(q)
    );
  }

  setSearchQuery(query) {
    this.searchQuery = query;
    this.host.requestUpdate();
  }
}
```

---

### Task 4: Create Theme Gallery Component

**File:** `somaAgent01/webui/components/theme-gallery.js` (create)

**Requirements:** US-AGS-001, US-AGS-002

### Acceptance Criteria
- [ ] Creates theme gallery Lit Web Component with search input
- [ ] Displays theme cards in responsive grid
- [ ] Shows upload button for admin users only
- [ ] Implements drag-drop zone for theme import
- [ ] Gallery renders <200ms for 50 themes
- [ ] Keyboard navigable (Tab, Enter, Escape)

### Implementation Notes
```javascript
// webui/components/theme-gallery.js
import { LitElement, html, css } from 'lit';
import { ThemeController } from '../js/controllers/theme-controller.js';
import './theme-card.js';

export class ThemeGallery extends LitElement {
  static properties = {
    showUpload: { type: Boolean, state: true },
    dragOver: { type: Boolean, state: true }
  };

  themeCtrl = new ThemeController(this);

  static styles = css`
    .theme-gallery { padding: var(--spacing-lg); }
    .gallery-header { display: flex; gap: var(--spacing-md); margin-bottom: var(--spacing-lg); }
    .theme-search { flex: 1; padding: var(--spacing-sm); border-radius: var(--radius-md); }
    .theme-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: var(--spacing-lg); }
    .theme-grid.drag-over { border: 2px dashed var(--accent-primary); }
  `;

  constructor() {
    super();
    this.showUpload = false;
    this.dragOver = false;
  }

  render() {
    return html`
      <div class="theme-gallery">
        <div class="gallery-header">
          <input type="search"
                 .value=${this.themeCtrl.searchQuery}
                 @input=${e => this.themeCtrl.setSearchQuery(e.target.value)}
                 placeholder="Search themes..."
                 class="theme-search">
          ${this.themeCtrl.isAdmin ? html`
            <button @click=${() => this.showUpload = true} class="btn-upload">
              Upload Theme
            </button>
          ` : ''}
        </div>
        
        <div class="theme-grid ${this.dragOver ? 'drag-over' : ''}"
             @dragover=${this._onDragOver}
             @dragleave=${() => this.dragOver = false}
             @drop=${this._onDrop}>
          ${this.themeCtrl.filteredThemes.map(theme => html`
            <theme-card .theme=${theme} .isAdmin=${this.themeCtrl.isAdmin}></theme-card>
          `)}
        </div>
      </div>
    `;
  }

  _onDragOver(e) {
    e.preventDefault();
    this.dragOver = true;
  }

  _onDrop(e) {
    e.preventDefault();
    this.dragOver = false;
    const file = e.dataTransfer?.files[0];
    if (file) this.themeCtrl.uploadTheme(file);
  }
}
customElements.define('theme-gallery', ThemeGallery);
```

---

### Task 5: Create Theme Card Component

**File:** `somaAgent01/webui/components/theme-card.js` (create)

**Requirements:** US-AGS-001, US-AGS-003

### Acceptance Criteria
- [ ] Card dimensions: 280×180 pixels with 12px border radius
- [ ] Shows theme preview with color swatches
- [ ] Shows name, description, version
- [ ] Preview on hover (mouseenter/mouseleave)
- [ ] Apply button triggers theme switch
- [ ] Delete button for admin users only
- [ ] Proper ARIA labels for accessibility

### Implementation Notes
```javascript
// webui/components/theme-card.js
import { LitElement, html, css } from 'lit';

export class ThemeCard extends LitElement {
  static properties = {
    theme: { type: Object },
    isAdmin: { type: Boolean }
  };

  static styles = css`
    .theme-card {
      width: 280px;
      height: 180px;
      border-radius: 12px;
      background: var(--surface-1);
      overflow: hidden;
      cursor: pointer;
    }
    .theme-preview { display: flex; gap: 4px; padding: var(--spacing-sm); }
    .color-swatch { width: 24px; height: 24px; border-radius: 4px; }
    .theme-info { padding: var(--spacing-sm); }
    .theme-info h3 { margin: 0; font-size: var(--font-size-md); }
    .theme-info p { margin: 4px 0; color: var(--text-muted); font-size: var(--font-size-sm); }
    .theme-actions { display: flex; gap: var(--spacing-sm); padding: var(--spacing-sm); }
    .btn-apply, .btn-preview, .btn-delete { padding: 4px 8px; border-radius: 4px; border: none; cursor: pointer; }
    .btn-delete { background: var(--error); color: white; }
  `;

  render() {
    const { theme, isAdmin } = this;
    return html`
      <div class="theme-card"
           @mouseenter=${this._onPreview}
           @mouseleave=${this._onCancelPreview}
           role="article"
           aria-label="${theme.name} theme">
        <div class="theme-preview">
          <div class="color-swatch" style="background:${theme.variables?.['--bg-primary'] || '#000'}"></div>
          <div class="color-swatch" style="background:${theme.variables?.['--accent-primary'] || '#0af'}"></div>
        </div>
        <div class="theme-info">
          <h3>${theme.name}</h3>
          <p>${theme.description || 'No description'}</p>
          <span class="version">v${theme.version}</span>
        </div>
        <div class="theme-actions">
          <button @click=${this._onApply} class="btn-apply">Apply</button>
          <button @click=${this._onPreview} class="btn-preview">Preview</button>
          ${isAdmin ? html`
            <button @click=${this._onDelete} class="btn-delete">Delete</button>
          ` : ''}
        </div>
      </div>
    `;
  }

  _onApply() {
    this.dispatchEvent(new CustomEvent('theme-apply', { detail: this.theme, bubbles: true }));
  }

  _onPreview() {
    this.dispatchEvent(new CustomEvent('theme-preview', { detail: this.theme, bubbles: true }));
  }

  _onCancelPreview() {
    this.dispatchEvent(new CustomEvent('theme-cancel-preview', { bubbles: true }));
  }

  _onDelete() {
    this.dispatchEvent(new CustomEvent('theme-delete', { detail: this.theme, bubbles: true }));
  }
}
customElements.define('theme-card', ThemeCard);
```

---

### Task 6: Create Palette Editor Component

**File:** `somaAgent01/webui/components/palette-editor.js` (create)

**Requirements:** US-AGS-007

### Acceptance Criteria
- [ ] Shows color pickers for 10+ key CSS variables
- [ ] Real-time preview as colors change
- [ ] WCAG AA contrast validation with warnings
- [ ] Save creates new theme variant
- [ ] Cancel restores original colors
- [ ] Accessible color picker with keyboard support

### Implementation Notes
```javascript
// webui/components/palette-editor.js
import { LitElement, html, css } from 'lit';
import { checkWcagAA } from '../js/theme.js';

export class PaletteEditor extends LitElement {
  static properties = {
    editableVariables: { type: Object, state: true },
    contrastWarnings: { type: Object, state: true }
  };

  static styles = css`
    .palette-editor { padding: var(--spacing-lg); background: var(--surface-1); border-radius: var(--radius-lg); }
    .color-inputs { display: grid; gap: var(--spacing-md); }
    .color-input-group { display: flex; align-items: center; gap: var(--spacing-sm); }
    .color-input-group label { flex: 1; }
    .color-input-group input[type="color"] { width: 48px; height: 32px; border: none; cursor: pointer; }
    .contrast-warning { color: var(--warning); font-size: var(--font-size-sm); }
    .editor-actions { display: flex; gap: var(--spacing-md); margin-top: var(--spacing-lg); }
  `;

  constructor() {
    super();
    this.editableVariables = {};
    this.contrastWarnings = {};
  }

  render() {
    return html`
      <div class="palette-editor">
        <h3>Custom Palette</h3>
        <div class="color-inputs">
          ${Object.entries(this.editableVariables).map(([key, value]) => html`
            <div class="color-input-group">
              <label>${this._formatLabel(key)}</label>
              <input type="color"
                     .value=${value}
                     @input=${e => this._updateColor(key, e.target.value)}
                     aria-label="${this._formatLabel(key)} color picker">
              ${this.contrastWarnings[key] ? html`
                <span class="contrast-warning">⚠️ Low contrast</span>
              ` : ''}
            </div>
          `)}
        </div>
        <div class="editor-actions">
          <button @click=${this._saveAsVariant}>Save as New Theme</button>
          <button @click=${this._cancel}>Cancel</button>
        </div>
      </div>
    `;
  }

  _formatLabel(key) {
    return key.replace(/^--/, '').replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }

  _updateColor(key, value) {
    this.editableVariables = { ...this.editableVariables, [key]: value };
    this._checkContrast(key, value);
    document.documentElement.style.setProperty(key, value);
  }

  _checkContrast(key, value) {
    const bgKey = key.includes('text') ? '--bg-primary' : null;
    if (bgKey) {
      const bgValue = this.editableVariables[bgKey] || getComputedStyle(document.documentElement).getPropertyValue(bgKey);
      const passes = checkWcagAA(value, bgValue);
      this.contrastWarnings = { ...this.contrastWarnings, [key]: !passes };
    }
  }

  _saveAsVariant() {
    this.dispatchEvent(new CustomEvent('palette-save', { detail: this.editableVariables, bubbles: true }));
  }

  _cancel() {
    this.dispatchEvent(new CustomEvent('palette-cancel', { bubbles: true }));
  }
}
customElements.define('palette-editor', PaletteEditor);
```

---

## Phase 4: Backend Implementation

### Task 7: Create Database Migration

**File:** `somaAgent01/migrations/versions/xxx_add_agent_skins.py`

**Requirements:** TR-AGS-005.1 - TR-AGS-005.4

### Acceptance Criteria
- [ ] Creates `agent_skins` table with all required columns
- [ ] Adds JSONB column for variables
- [ ] Adds tenant_id foreign key for multi-tenancy
- [ ] Adds is_approved boolean for admin workflow
- [ ] Creates indexes on tenant_id and is_approved
- [ ] Reversible migration

### Implementation Notes
```python
def upgrade():
    op.create_table(
        'agent_skins',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.UUID(), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(200)),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('author', sa.String(100)),
        sa.Column('variables', sa.dialects.postgresql.JSONB, nullable=False),
        sa.Column('changelog', sa.dialects.postgresql.JSONB),
        sa.Column('is_approved', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_skins_tenant_name')
    )
    op.create_index('idx_skins_tenant', 'agent_skins', ['tenant_id'])
    op.create_index('idx_skins_approved', 'agent_skins', ['is_approved'])
```

---

### Task 8: Create Backend API Endpoints

**Files:**
- `somaAgent01/services/gateway/routers/skins.py` (created)
- `somaAgent01/services/common/skins_store.py` (created)
- `somaAgent01/services/gateway/routers/__init__.py` (modified)

**Requirements:** TR-AGS-004.1 - TR-AGS-004.6

### Acceptance Criteria
- [x] GET /v1/skins - List themes for tenant (approved only for non-admin)
- [x] GET /v1/skins/{id} - Get theme details
- [x] POST /v1/skins - Upload new theme (admin only)
- [x] DELETE /v1/skins/{id} - Delete theme (admin only)
- [x] PATCH /v1/skins/{id}/approve - Approve theme (admin only)
- [x] Validates JSON schema on upload
- [x] Rejects themes with url() values (XSS prevention)
- [x] All queries scoped by tenant_id

### Implementation Notes

**Created Files:**

1. `services/common/skins_store.py`:
   - `SkinRecord` dataclass for skin data
   - `SkinsStore` class with PostgreSQL operations
   - `validate_no_xss()` function for XSS pattern detection
   - Methods: `list()`, `get()`, `get_by_name()`, `create()`, `update()`, `delete()`, `approve()`, `reject()`

2. `services/gateway/routers/skins.py`:
   - Pydantic models: `SkinCreateRequest`, `SkinUpdateRequest`, `SkinResponse`, `SkinListResponse`
   - Endpoints following capsules.py pattern
   - OPA authorization via `authorize()` for admin operations
   - Tenant isolation via X-Tenant-Id header

3. Updated `services/gateway/routers/__init__.py`:
   - Added `skins` import
   - Added `skins.router` to `build_router()`

**Security Implementation:**
- XSS patterns rejected: `url()`, `<script>`, `javascript:`, `expression()`, `@import`
- Admin operations require OPA policy check (skin:upload, skin:delete, skin:approve, skin:reject)
- Tenant isolation enforced on all queries

---

### Task 9: Add XSS Validation

**File:** `somaAgent01/webui/js/theme.js` (modify) + `somaAgent01/services/gateway/routes/skins.py`

**Requirements:** SEC-AGS-002.1 - SEC-AGS-002.4

### Acceptance Criteria
- [ ] Frontend: ThemeLoader.validate() rejects url() in CSS values
- [ ] Frontend: ThemeLoader.validate() rejects <script> tags
- [ ] Backend: validate_no_xss() function checks all variable values
- [ ] Backend: Rejects themes failing validation with 400 error
- [ ] Remote URLs must be HTTPS only

### Implementation Notes
```javascript
// Frontend validation
validate(skin) {
  if (!skin || !skin.name || !skin.variables) return false;
  
  // Check for XSS patterns
  const xssPatterns = [/url\s*\(/i, /<script/i, /javascript:/i];
  for (const [key, value] of Object.entries(skin.variables)) {
    for (const pattern of xssPatterns) {
      if (pattern.test(value)) {
        console.error(`XSS pattern detected in ${key}`);
        return false;
      }
    }
  }
  return true;
}
```

```python
# Backend validation
def validate_no_xss(variables: dict[str, str]) -> None:
    xss_patterns = [r'url\s*\(', r'<script', r'javascript:']
    for key, value in variables.items():
        for pattern in xss_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                raise HTTPException(400, f"XSS pattern detected in {key}")
```

---

### Task 10: Add WCAG Contrast Validation

**File:** `somaAgent01/webui/js/theme.js` (modify)

**Requirements:** A11Y-AGS-001.1

### Acceptance Criteria
- [ ] Implements `checkContrast(fg, bg)` function
- [ ] Returns true if contrast ratio ≥ 4.5:1 (WCAG AA)
- [ ] Validates text colors against background colors
- [ ] Shows warning in palette editor for failing combinations
- [ ] Does not block theme application (warning only)

### Implementation Notes
```javascript
// WCAG contrast calculation
function getLuminance(hex) {
  const rgb = hexToRgb(hex);
  const [r, g, b] = rgb.map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function getContrastRatio(fg, bg) {
  const l1 = getLuminance(fg);
  const l2 = getLuminance(bg);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

function checkWcagAA(fg, bg) {
  return getContrastRatio(fg, bg) >= 4.5;
}
```

---

### Task 11: Add OPA Admin Authorization

**File:** `somaAgent01/policy/skins.rego` (create)

**Requirements:** SEC-AGS-001.1 - SEC-AGS-001.3

### Acceptance Criteria
- [ ] Creates OPA policy for skin operations
- [ ] skin:upload requires admin role
- [ ] skin:delete requires admin role
- [ ] skin:approve requires admin role
- [ ] skin:read allowed for all authenticated users
- [ ] Integrates with existing OPA client

### Implementation Notes
```rego
package somaagent.skins

default allow = false

# Anyone can read skins
allow {
    input.action == "skin:read"
    input.user.authenticated
}

# Only admins can upload/delete/approve
allow {
    input.action == "skin:upload"
    input.user.role == "admin"
}

allow {
    input.action == "skin:delete"
    input.user.role == "admin"
}

allow {
    input.action == "skin:approve"
    input.user.role == "admin"
}
```

---

## Phase 5: Testing

### Task 12: Unit Tests

**Files:**
- `somaAgent01/tests/unit/test_theme_loader.py`
- `somaAgent01/tests/unit/test_skin_validation.py`

**Requirements:** QA-AGS-001.1 - QA-AGS-001.3

### Acceptance Criteria
- [ ] Tests ThemeLoader.validate() with valid themes
- [ ] Tests ThemeLoader.validate() rejects url() values
- [ ] Tests ThemeLoader.validate() rejects <script> tags
- [ ] Tests theme persistence to localStorage
- [ ] Tests backend validate_no_xss() function
- [ ] Tests WCAG contrast calculation

---

### Task 13: Property Tests

**File:** `somaAgent01/tests/property/test_theme_properties.py`

**Requirements:** Design correctness properties

### Acceptance Criteria
- [ ]* **Property 1: Theme Application Idempotence**
  - *For any* valid theme, applying twice produces same result as once
  - **Validates: US-AGS-002**

- [ ]* **Property 2: Preview/Cancel Round-Trip**
  - *For any* theme preview followed by cancel, UI returns to exact previous state
  - **Validates: US-AGS-003**

- [ ]* **Property 3: Export/Import Round-Trip**
  - *For any* valid theme, export then import produces equivalent theme
  - **Validates: US-AGS-004**

- [ ]* **Property 4: XSS Rejection**
  - *For any* theme containing url() or <script>, validation returns false
  - **Validates: SEC-AGS-002**

### Implementation Notes
```python
from hypothesis import given, strategies as st

@given(st.dictionaries(
    st.text(min_size=1, max_size=20),
    st.text(min_size=1, max_size=50)
))
def test_xss_rejection(variables):
    # Inject XSS pattern
    variables['--test'] = 'url(javascript:alert(1))'
    skin = {'name': 'test', 'version': '1.0.0', 'variables': variables}
    assert not validate_skin(skin)
```

---

### Task 14: E2E Tests (Playwright)

**File:** `somaAgent01/tests/e2e/test_theme_gallery.spec.js`

**Requirements:** QA-AGS-002.1 - QA-AGS-002.3

### Acceptance Criteria
- [ ] Tests theme gallery navigation
- [ ] Tests theme search filtering
- [ ] Tests theme switching via Apply button
- [ ] Tests theme preview on hover
- [ ] Tests drag-drop import
- [ ] Tests admin upload flow
- [ ] Tests keyboard navigation

### Implementation Notes
```javascript
// tests/e2e/test_theme_gallery.spec.js
const { test, expect } = require('@playwright/test');

test('theme gallery displays themes', async ({ page }) => {
  await page.goto('/ui');
  await page.click('[data-testid="settings-button"]');
  await page.click('[data-testid="themes-tab"]');
  
  const themeCards = page.locator('.theme-card');
  await expect(themeCards).toHaveCount.greaterThan(0);
});

test('theme switch applies without reload', async ({ page }) => {
  await page.goto('/ui');
  const initialBg = await page.evaluate(() => 
    getComputedStyle(document.documentElement).getPropertyValue('--bg-primary')
  );
  
  await page.click('[data-testid="theme-midnight"]');
  await page.click('[data-testid="apply-theme"]');
  
  const newBg = await page.evaluate(() => 
    getComputedStyle(document.documentElement).getPropertyValue('--bg-primary')
  );
  
  expect(newBg).not.toBe(initialBg);
});
```

---

### Task 15: Documentation

**File:** `somaAgent01/docs/agentskin.md`

**Requirements:** All

### Acceptance Criteria
- [ ] Architecture overview with diagram
- [ ] ThemeLoader SDK API reference
- [ ] Theme JSON schema documentation
- [ ] API endpoint documentation
- [ ] Admin workflow guide
- [ ] Custom palette creation guide
- [ ] Troubleshooting guide

---

## Implementation Order

```
Week 1:
├── T1: Extract Inline Styles
├── T7: Database Migration
└── T9: XSS Validation

Week 2:
├── T2: Enhance ThemeLoader SDK
├── T3: Create Theme Alpine Store
└── T8: Backend API Endpoints

Week 3:
├── T4: Theme Gallery Component
├── T5: Theme Card Component
└── T11: OPA Admin Authorization

Week 4:
├── T6: Palette Editor Component
├── T10: WCAG Contrast Validation
└── T12: Unit Tests

Week 5:
├── T13: Property Tests
├── T14: E2E Tests
└── T15: Documentation
```

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests passing
- [ ] Property tests passing
- [ ] E2E tests passing
- [ ] No VIBE violations (no mocks, no placeholders, no TODOs)
- [ ] XSS validation working
- [ ] WCAG contrast validation working
- [ ] Admin authorization working
- [ ] Documentation complete
- [ ] Code reviewed

---

## Notes

- Tasks marked with `*` are property-based tests
- All tests use real infrastructure per VIBE Coding Rules
- UI uses Lit 3.x Web Components (Alpine.js is FORBIDDEN)
- Theme switch must complete within 300ms

