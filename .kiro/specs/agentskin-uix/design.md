# AgentSkin UIX Design Document

## Overview

Technical architecture for the AgentSkin UIX theming system. Follows Clean Architecture with presentation, application, and infrastructure layers.

## Current vs Target Architecture

### Current Issues
- index.html: 1323 lines with inline styles duplicating CSS variables
- No theme gallery UI
- No admin controls
- No WCAG validation

### Target Architecture

```
Presentation Layer
├── index.html (refactored - no inline styles)
├── components/theme-gallery.html
├── components/theme-card.html
└── components/palette-editor.html

Application Layer
├── js/theme.js (ThemeLoader SDK)
└── js/stores/theme-store.js (Alpine Store)

Infrastructure Layer
├── Backend API: GET/POST/DELETE /v1/skins
├── Database: agent_skins table
└── Static: themes/*.json
```

## Data Models

### Skin Interface
```typescript
interface Skin {
  name: string;           // Required, 1-50 chars
  description?: string;   // Optional, max 200 chars
  version: string;        // Semver format: X.Y.Z
  author?: string;
  variables: Record<string, string>;  // CSS variable map
  changelog?: ChangelogEntry[];
}

interface ChangelogEntry {
  version: string;
  date: string;  // ISO date
  changes: string[];
}
```

### Database Schema
```sql
CREATE TABLE agent_skins (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  name VARCHAR(50) NOT NULL,
  description VARCHAR(200),
  version VARCHAR(20) NOT NULL,
  author VARCHAR(100),
  variables JSONB NOT NULL,
  changelog JSONB,
  is_approved BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(tenant_id, name)
);

CREATE INDEX idx_skins_tenant ON agent_skins(tenant_id);
CREATE INDEX idx_skins_approved ON agent_skins(is_approved);
```


## Component Design

### ThemeLoader SDK (js/theme.js)

Methods:
- `loadLocal(name)` - Load from /static/themes/{name}.json
- `loadRemote(url)` - Load from HTTPS URL (validates HTTPS)
- `validate(skin)` - Validate schema, reject url() values
- `apply(skin)` - Set CSS variables on :root
- `switch(name)` - Load + apply + persist to localStorage
- `preview(skin)` - Temporary apply without persistence
- `cancelPreview()` - Restore previous theme
- `exportTheme(skin)` - Return Blob for download

### Theme Store (js/stores/theme-store.js)

```javascript
// Alpine.js store for theme state
const themeStore = {
  themes: [],           // Available themes
  currentTheme: 'default',
  previewTheme: null,
  isAdmin: false,
  searchQuery: '',
  isLoading: false,
  
  async loadThemes() { /* fetch from API */ },
  async applyTheme(name) { /* use ThemeLoader */ },
  async uploadTheme(file) { /* POST to API */ },
  filterThemes() { /* filter by searchQuery */ }
};
```

### Theme Gallery Component

```html
<div x-data="themeGallery" class="theme-gallery">
  <div class="gallery-header">
    <input type="search" x-model="$store.theme.searchQuery" 
           placeholder="Search themes...">
    <template x-if="$store.theme.isAdmin">
      <button @click="showUpload = true">Upload Theme</button>
    </template>
  </div>
  
  <div class="theme-grid">
    <template x-for="theme in filteredThemes" :key="theme.name">
      <div class="theme-card" 
           @mouseenter="previewTheme(theme)"
           @mouseleave="cancelPreview()">
        <div class="theme-preview" :style="getPreviewStyle(theme)"></div>
        <div class="theme-info">
          <h3 x-text="theme.name"></h3>
          <p x-text="theme.description"></p>
          <span class="version" x-text="'v' + theme.version"></span>
        </div>
        <div class="theme-actions">
          <button @click="applyTheme(theme.name)">Apply</button>
          <template x-if="$store.theme.isAdmin">
            <button @click="deleteTheme(theme.name)" class="danger">Delete</button>
          </template>
        </div>
      </div>
    </template>
  </div>
</div>
```

## API Design

### Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /v1/skins | User | List themes for tenant |
| GET | /v1/skins/{id} | User | Get theme details |
| POST | /v1/skins | Admin | Upload new theme |
| DELETE | /v1/skins/{id} | Admin | Delete theme |
| PATCH | /v1/skins/{id}/approve | Admin | Approve theme |

### Request/Response Models

```python
class SkinCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = Field(None, max_length=200)
    version: str = Field(..., pattern=r'^\d+\.\d+\.\d+$')
    variables: dict[str, str]

class SkinResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    version: str
    variables: dict[str, str]
    is_approved: bool
    created_at: datetime
```


## Security Design

### XSS Prevention
1. Reject themes with `url()` in CSS values
2. Reject themes with `<script>` tags
3. Validate JSON schema strictly
4. Remote URLs must be HTTPS only

### Admin Authorization
```python
@router.post("/v1/skins")
async def upload_skin(
    skin: SkinCreate,
    current_user: User = Depends(get_current_user),
    opa: OPAClient = Depends(get_opa)
):
    # Check admin permission via OPA
    allowed = await opa.check_permission(
        subject=current_user.id,
        action="skin:upload",
        resource="skins"
    )
    if not allowed:
        raise HTTPException(403, "Admin access required")
    # ... create skin
```

### Tenant Isolation
All queries filtered by tenant_id from JWT token.

## Migration Plan

### Phase 1: Extract Inline Styles
1. Extract inline `<style>` from index.html to css/index-extracted.css
2. Remove duplicate CSS variables (keep tokens.css as source of truth)
3. Update index.html to link external CSS

### Phase 2: Enhance ThemeLoader
1. Add preview/cancelPreview methods
2. Add exportTheme method
3. Add WCAG contrast validation

### Phase 3: Create Theme Gallery
1. Create theme-store.js Alpine store
2. Create theme-gallery component
3. Add to settings modal

### Phase 4: Backend API
1. Create agent_skins table migration
2. Implement FastAPI router
3. Add OPA policies for admin

### Phase 5: Testing
1. Unit tests for ThemeLoader
2. Playwright E2E for gallery
3. Performance benchmarks

## Correctness Properties

*Properties are formal specifications that should hold for all valid inputs.*

### Property 1: Theme Application Idempotence
*For any* valid theme, applying it twice should produce the same result as applying it once.
**Validates: US-AGS-002**

### Property 2: Preview/Cancel Round-Trip
*For any* theme preview followed by cancel, the UI should return to its exact previous state.
**Validates: US-AGS-003**

### Property 3: Export/Import Round-Trip
*For any* valid theme, exporting then importing should produce an equivalent theme object.
**Validates: US-AGS-004**

### Property 4: XSS Rejection
*For any* theme containing `url()` or `<script>`, validation should return false.
**Validates: SEC-AGS-002**

### Property 5: Tenant Isolation
*For any* API request, returned themes should only include those matching the request's tenant_id.
**Validates: SEC-AGS-003**

## Error Handling

| Error | Response | User Message |
|-------|----------|--------------|
| Theme not found | 404 | "Theme not found" |
| Invalid JSON | 400 | "Invalid theme format" |
| XSS detected | 400 | "Theme contains unsafe values" |
| Not admin | 403 | "Admin access required" |
| Remote fetch failed | 502 | "Could not load remote theme" |

## Testing Strategy

### Unit Tests
- ThemeLoader.validate() with valid/invalid inputs
- XSS detection for url() and script tags
- Semver validation

### Property Tests (Hypothesis)
- Theme application idempotence
- Preview/cancel round-trip
- Export/import round-trip

### E2E Tests (Playwright)
- Theme gallery navigation
- Theme switching
- Drag/drop import
- Admin upload flow

---

**Last Updated:** 2025-12-21
