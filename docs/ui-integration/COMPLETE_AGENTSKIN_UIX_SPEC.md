# 🎨 COMPLETE AGENTSKIN UIX FEATURES & CHARACTERISTICS
## The Definitive Specification from All 7 VIBE Coding Personas

**Document Version:** 2.0  
**Last Updated:** 2025-12-14  
**Status:** Ready for Review & Implementation

---

## 🎯 PERSONA 1: PRODUCT MANAGER — Vision & Features

### Product Vision
**AgentSkin** transforms somaAgent01 into a **fully customizable, themeable agent platform** where users can express their personality and optimize their workspace with beautiful, functional UI themes.

### Core Value Propositions
1. **Personal Expression** - Make your agent truly yours
2. **Visual Comfort** - Reduce eye strain with perfect color schemes
3. **Brand Alignment** - Match corporate/personal branding
4. **Community Sharing** - Discover and share themes
5. **Instant Transformation** - One-click theme switching

### Feature Set (17 Features)

#### 🎨 **F1: Theme Gallery**
- **User Story**: As a user, I want to browse beautiful themes so I can find one that matches my style
- **Features**:
  - Grid layout with theme previews
  - Search and filter (dark/light, categories, popularity)
  - Theme ratings and downloads count
  - Preview before applying
  - Featured themes section

#### 🔄 **F2: One-Click Theme Switching**
- **User Story**: As a user, I want to switch themes instantly without page reload
- **Features**:
  - Live CSS variable injection
  - Smooth transitions (300ms fade)
  - Instant activation
  - No page reload required
  - Persistent across sessions (localStorage)

#### 📦 **F3: Drag-and-Drop Installation**
- **User Story**: As a user, I want to install custom themes by dragging JSON files
- **Features**:
  - Drag JSON file onto settings modal
  - Visual drop zone with hover effects
  - Automatic validation before install
  - Error messages for invalid themes
  - Success confirmation with preview

#### 🎭 **F4: Live Theme Preview**
- **User Story**: As a user, I want to preview themes before activating them
- **Features**:
  - Side-by-side comparison mode
  - Hover preview (show changes in real-time)
  - Revert button (undo last change)
  - Preview different UI sections
  - Screenshot generation

#### 🏪 **F5: Theme Marketplace** (Future)
- **User Story**: As a user, I want to discover community-created themes
- **Features**:
  - Browse curated marketplace
  - Download themes with one click
  - Rate and review themes
  - Report inappropriate themes
  - Creator profiles

#### 🛠️ **F6: Theme Creator Tool** (Future)
- **User Story**: As a creator, I want to build themes visually
- **Features**:
  - Visual color picker
  - Live preview while editing
  - Export as JSON
  - Import base themes
  - Validation before export

#### 🔐 **F7: Admin Theme Management**
- **User Story**: As an admin, I want to control which themes are available
- **Features**:
  - Admin-only upload endpoint
  - Approve/reject themes
  - Set default theme
  - Delete themes
  - View usage analytics

#### 📱 **F8: Responsive Theme System**
- **User Story**: As a user, I want themes to work on all screen sizes
- **Features**:
  - Mobile-optimized themes
  - Tablet breakpoints
  - Desktop layouts
  - Auto-scaling fonts
  - Touch-friendly controls

#### 🌙 **F9: Dark/Light Mode Toggle**
- **User Story**: As a user, I want to toggle dark/light modes independently
- **Features**:
  - Theme-aware mode switching
  - System preference detection
  - Manual override
  - Smooth transitions
  - Per-theme customization

#### 🎨 **F10: Custom Color Palettes**
- **User Story**: As a user, I want to customize specific colors
- **Features**:
  - Override individual variables
  - Save custom palettes
  - Color picker interface
  - Contrast validation (WCAG AA)
  - Reset to defaults

#### 📊 **F11: Theme Analytics**
- **User Story**: As an admin, I want to see theme usage stats
- **Features**:
  - Most popular themes
  - Active users per theme
  - Switch frequency
  - Error rates
  - User satisfaction scores

#### 🔔 **F12: Theme Notifications**
- **User Story**: As a user, I want to know when themes are updated
- **Features**:
  - Update notifications
  - Changelog display
  - Auto-update option
  - Breaking change warnings
  - Version history

#### 🌐 **F13: Remote Theme Loading**
- **User Story**: As a user, I want to load themes from URLs
- **Features**:
  - Remote URL support
  - HTTPS validation
  - CORS handling
  - CDN caching
  - Local theme pack (explicit selection)

#### 🎯 **F14: Theme Categories**
- **User Story**: As a user, I want to browse themes by category
- **Categories**:
  - Professional (corporate, minimal)
  - Creative (vibrant, artistic)
  - Developer (syntax-inspired)
  - Gaming (cyberpunk, neon)
  - Seasonal (holidays, weather)
  - Accessibility (high contrast, large text)

#### 💾 **F15: Theme Import/Export**
- **User Story**: As a user, I want to backup and share my themes
- **Features**:
  - Export current theme as JSON
  - Import from file
  - Bulk export/import
  - Cloud sync (future)
  - QR code sharing

#### 🔍 **F16: Theme Search & Discovery**
- **User Story**: As a user, I want to find themes easily
- **Features**:
  - Full-text search
  - Tag filtering
  - Color-based search
  - Similar themes recommendations
  - Trending themes

#### ⚡ **F17: Performance Optimization**
- **User Story**: As a user, I want themes to load instantly
- **Features**:
  - Theme preloading
  - CSS variable caching
  - Lazy loading for previews
  - Compression for remote themes
  - Service Worker caching

---

## 🎨 PERSONA 2: UX DESIGNER — User Experience & Flows

### Design Principles
1. **Instant Gratification** - See changes immediately
2. **No Friction** - Maximum 2 clicks to switch themes
3. **Safe Exploration** - Always allow undo
4. **Visual Delight** - Smooth animations, premium feel
5. **Accessibility First** - WCAG AA contrast, keyboard nav

### User Flows

#### 🔄 **Flow 1: First-Time User Installing Theme**
```
1. User opens Settings → Themes tab
2. Sees default theme active + gallery of 5 featured themes
3. Hovers over "Midnight Ocean" theme
   → Preview shows in background (50% opacity overlay)
4. Clicks "Apply"
   → Smooth 300ms transition
   → Success toast: "Midnight Ocean activated!"
   → Theme persists in localStorage
```

#### 📥 **Flow 2: Drag-and-Drop Installation**
```
1. User downloads "Coral Reef.json" from website
2. Opens Settings → Themes tab
3. Drags file onto drop zone
   → Drop zone highlights in coral color
   → "Drop to install Coral Reef" message
4. Drops file
   → Auto-validation runs (schema check)
   → If valid: "Coral Reef installed! Click to apply"
   → If invalid: Error modal with specific issues
```

#### 🔄 **Flow 3: Theme Switching with Preview**
```
1. User clicks "Preview" on theme card
   → Split-screen mode activates
   → Left: Current theme
   → Right: Preview theme
2. User interacts with preview (send test message)
3. Satisfied → Click "Apply"
   → Full screen switches to new theme
4. Not satisfied → Click "Cancel"
   → Returns to original theme
```

#### 🎨 **Flow 4: Creating Custom Theme**
```
1. User clicks "Create Theme" button
2. Opens Theme Creator modal
3. Selects base theme (e.g., "Default Light")
4. Customizes colors via color pickers
   → Live preview updates in real-time
5. Names theme "My Custom Theme"
6. Clicks "Save"
   → Validates contrast ratios
   → If pass: Saves to localStorage
   → If fail: Shows contrast warnings
```

### UI Component Specifications

#### **Theme Card Component**
```css
Dimensions: 280px × 180px
Border Radius: 12px
Shadow: 0 2px 8px rgba(0,0,0,0.1)
Hover: Lift 4px, shadow intensity +50%
Transition: all 200ms ease-out

Layout:
- Preview image (180px height)
- Theme name (16px bold)
- Author badge
- Apply button (coral, white text)
- Preview button (ghost)
```

#### **Theme Gallery Grid**
```css
Grid: auto-fill, minmax(280px, 1fr)
Gap: 24px
Max columns: 4
Responsive breakpoints:
  - Mobile (<768px): 1 column
  - Tablet (768-1024px): 2 columns
  - Desktop (>1024px): 3-4 columns
```

#### **Drag-Drop Zone**
```css
Height: 200px
Border: 2px dashed var(--accent-coral)
Border Radius: 16px
Background: var(--glass-surface)
Backdrop Filter: blur(10px)

States:
- Default: Dashed border, "Drag theme file here"
- Hover: Solid border, coral glow
- Dropping: Pulsing animation
- Success: Green checkmark, fade out
- Error: Red X, shake animation
```

### Color System

#### **Required CSS Variables** (26 total)
```css
/* Core Colors */
--bg-void: #0a0a0f;
--bg-canvas: #141419;
--bg-surface: #1e1e26;
--glass-surface: rgba(30, 30, 38, 0.6);

/* Text */
--text-main: #e4e4e7;
--text-dim: #a1a1aa;
--text-subtle: #71717a;

/* Accent */
--accent-coral: #ff6b47;
--accent-coral-dim: #ff8c73;
--accent-hover: #ff5533;

/* Semantic */
--success: #10b981;
--warning: #f59e0b;
--error: #ef4444;
--info: #3b82f6;

/* UI Elements */
--border-subtle: rgba(255, 255, 255, 0.1);
--border-medium: rgba(255, 255, 255, 0.2);
--shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
--shadow-md: 0 4px 12px rgba(0,0,0,0.1);
--shadow-lg: 0 8px 24px rgba(0,0,0,0.15);

/* Interactive */
--interactive-hover: rgba(255, 107, 71, 0.1);
--interactive-active: rgba(255, 107, 71, 0.2);
--interactive-disabled: rgba(161, 161, 170, 0.3);

/* Gradients */
--gradient-primary: linear-gradient(135deg, #ff6b47 0%, #ff8c73 100%);
--gradient-glass: linear-gradient(135deg, 
    rgba(255,255,255,0.05) 0%, 
    rgba(255,255,255,0.02) 100%);
```

### Animation Specifications

#### **Theme Switch Transition**
```css
@keyframes theme-switch {
  0% {
    opacity: 1;
    filter: blur(0px);
  }
  50% {
    opacity: 0.3;
    filter: blur(8px);
  }
  100% {
    opacity: 1;
    filter: blur(0px);
  }
}

Duration: 300ms
Easing: cubic-bezier(0.4, 0, 0.2, 1)
```

#### **Card Hover Animation**
```css
Lift: translateY(-4px)
Shadow: 0 12px 24px rgba(0,0,0,0.15)
Scale: 1.02
Duration: 200ms
Easing: ease-out
```

---

## 💻 PERSONA 3: FRONTEND DEVELOPER — Technical Architecture

### Tech Stack
- **Framework**: Alpine.js 3.x (lightweight, reactive)
- **Styling**: CSS Custom Properties + Vanilla CSS
- **Build**: No build step required (ES6 modules)
- **Storage**: localStorage for persistence
- **Validation**: JSON Schema with AJV

### File Structure
```
webui/
├── design-system/
│   └── tokens.css           # All CSS variables
├── css/
│   ├── app.css             # Main app styles
│   └── theme.css           # Theme-specific styles
├── js/
│   ├── theme.js            # Theme loader (SDK)
│   ├── agentskins.js       # Alpine component
│   └── validation.js       # Schema validation
├── themes/
│   ├── default.json        # Default light theme
│   ├── midnight.json       # Dark theme
│   └── coral-reef.json     # Custom theme
└── schemas/
    └── agentskin.schema.json  # JSON Schema
```

### Theme Loader SDK (`js/theme.js`)

```javascript
class ThemeLoader {
  constructor() {
    this.currentTheme = null;
    this.themes = new Map();
    this.root = document.documentElement;
  }

  /**
   * Load theme from local JSON file
   * @param {string} name - Theme filename (without .json)
   * @returns {Promise<Theme>}
   */
  async loadLocal(name) {
    const response = await fetch(`/themes/${name}.json`);
    if (!response.ok) throw new Error(`Theme ${name} not found`);
    const theme = await response.json();
    return this.validate(theme);
  }

  /**
   * Load theme from remote URL
   * @param {string} url - HTTPS URL to theme JSON
   * @returns {Promise<Theme>}
   */
  async loadRemote(url) {
    if (!url.startsWith('https://')) {
      throw new Error('Only HTTPS URLs allowed');
    }
    const response = await fetch(url, { mode: 'cors' });
    const theme = await response.json();
    return this.validate(theme);
  }

  /**
   * Validate theme against JSON Schema
   * @param {object} theme - Theme object
   * @returns {Theme} Validated theme
   */
  validate(theme) {
    const ajv = new Ajv();
    const schema = {
      type: 'object',
      required: ['name', 'version', 'variables'],
      properties: {
        name: { type: 'string', minLength: 1 },
        description: { type: 'string' },
        version: { type: 'string', pattern: '^\\d+\\.\\d+\\.\\d+$' },
        author: { type: 'string' },
        variables: {
          type: 'object',
          additionalProperties: { type: 'string' }
        }
      }
    };

    const valid = ajv.validate(schema, theme);
    if (!valid) throw new Error(ajv.errorsText());

    // Security: Reject url() in CSS values
    for (const [key, value] of Object.entries(theme.variables)) {
      if (value.includes('url(')) {
        throw new Error(`XSS attempt: url() not allowed in ${key}`);
      }
    }

    return theme;
  }

  /**
   * Apply theme to DOM
   * @param {Theme} theme - Validated theme object
   */
  apply(theme) {
    // Apply CSS variables to :root
    for (const [varName, value] of Object.entries(theme.variables)) {
      this.root.style.setProperty(varName, value);
    }

    // Update internal state
    this.currentTheme = theme;
    this.themes.set(theme.name, theme);

    // Persist to localStorage
    localStorage.setItem('active-theme', theme.name);
    localStorage.setItem(`theme-${theme.name}`, JSON.stringify(theme));

    // Dispatch custom event
    window.dispatchEvent(new CustomEvent('theme-changed', {
      detail: { theme: theme.name }
    }));
  }

  /**
   * Load and apply theme (convenience method)
   * @param {string} nameOrUrl - Theme name or HTTPS URL
   */
  async use(nameOrUrl) {
    const theme = nameOrUrl.startsWith('http')
      ? await this.loadRemote(nameOrUrl)
      : await this.loadLocal(nameOrUrl);
    
    this.apply(theme);
    return theme;
  }

  /**
   * Get currently active theme
   * @returns {Theme|null}
   */
  getCurrent() {
    return this.currentTheme;
  }

  /**
   * List all installed themes
   * @returns {Array<string>} Theme names
   */
  listInstalled() {
    const installed = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key.startsWith('theme-')) {
        installed.push(key.replace('theme-', ''));
      }
    }
    return installed;
  }
}

// Export singleton
export const themeLoader = new ThemeLoader();
```

### Alpine.js Component (`js/agentskins.js`)

```javascript
Alpine.data('agentskins', () => ({
  themes: [],
  activeTheme: null,
  previewTheme: null,
  loading: false,
  error: null,

  async init() {
    await this.loadThemes();
    this.restoreActiveTheme();
  },

  async loadThemes() {
    this.loading = true;
    try {
      // Load from backend API
      const response = await fetchApi('/api/skins');
      this.themes = response.skins || [];
    } catch (err) {
      this.error = `Failed to load themes: ${err.message}`;
    } finally {
      this.loading = false;
    }
  },

  restoreActiveTheme() {
    const saved = localStorage.getItem('active-theme');
    if (saved) {
      this.activeTheme = saved;
      themeLoader.use(saved).catch(console.error);
    }
  },

  async applyTheme(name) {
    try {
      await themeLoader.use(name);
      this.activeTheme = name;
      this.showToast('Theme applied successfully!');
    } catch (err) {
      this.error = `Failed to apply theme: ${err.message}`;
    }
  },

  async previewTheme(name) {
    this.previewTheme = name;
    // FEATURE: Split-screen preview (see UI spec §2.2)
  },

  async uploadTheme(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetchApi('/api/skins/upload', {
        method: 'POST',
        body: formData
      });
      
      this.themes.push(response.skin);
      this.showToast(`Theme "${response.skin.name}" installed!`);
    } catch (err) {
      this.error = `Upload failed: ${err.message}`;
    }
  },

  handleDragDrop(event) {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    
    if (!file || !file.name.endsWith('.json')) {
      this.error = 'Please drop a valid JSON theme file';
      return;
    }

    this.uploadTheme(file);
  },

  showToast(message) {
    // FEATURE: Toast notifications (see Notification System requirements)
    console.log(message);
  }
}));
```

### JSON Schema (`schemas/agentskin.schema.json`)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AgentSkin Theme",
  "type": "object",
  "required": ["name", "version", "variables"],
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 50,
      "description": "Theme name"
    },
    "description": {
      "type": "string",
      "maxLength": 200,
      "description": "Brief description"
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "description": "Semantic version (e.g., 1.0.0)"
    },
    "author": {
      "type": "string",
      "maxLength": 50,
      "description": "Creator name"
    },
    "license": {
      "type": "string",
      "enum": ["MIT", "Apache-2.0", "GPL-3.0", "CC-BY-4.0"],
      "description": "License type"
    },
    "tags": {
      "type": "array",
      "items": { "type": "string" },
      "maxItems": 10,
      "description": "Categories/tags"
    },
    "variables": {
      "type": "object",
      "additionalProperties": {
        "type": "string",
        "pattern": "^(?!.*url\\().*$"
      },
      "minProperties": 10,
      "description": "CSS variable overrides"
    },
    "preview": {
      "type": "string",
      "format": "uri",
      "description": "Preview screenshot URL"
    }
  }
}
```

---

## 🔧 PERSONA 4: BACKEND DEVELOPER — API & Data Layer

### Backend Architecture

#### **Database Schema** (`agent_skins` table)
```sql
CREATE TABLE agent_skins (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(200),
    version VARCHAR(20) NOT NULL,  -- semver
    author VARCHAR(50),
    license VARCHAR(20),
    tags TEXT[],  -- ARRAY of tags
    variables JSONB NOT NULL,  -- Theme variables
    preview_url TEXT,
    downloads INTEGER DEFAULT 0,
    rating DECIMAL(3,2) DEFAULT 0.0,  -- 0.00 to 5.00
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id VARCHAR(50)  -- For multi-tenancy
);

CREATE INDEX idx_agent_skins_name ON agent_skins(name);
CREATE INDEX idx_agent_skins_tags ON agent_skins USING GIN(tags);
CREATE INDEX idx_agent_skins_tenant ON agent_skins(tenant_id);
```

#### **Store Implementation** (`services/common/agent_skins_store.py`)

```python
class AgentSkinsStore:
    """PostgreSQL store for AgentSkin themes."""
    
    def __init__(self, dsn: Optional[str] = None):
        raw_dsn = dsn or cfg.settings().database.dsn
        self.dsn = os.expandvars(raw_dsn)
        self._pool: Optional[asyncpg.Pool] = None
    
    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            min_size = int(cfg.env("PG_POOL_MIN_SIZE", "1") or "1")
            max_size = int(cfg.env("PG_POOL_MAX_SIZE", "2") or "2")
            self._pool = await asyncpg.create_pool(
                self.dsn,
                min_size=max(0, min_size),
                max_size=max(1, max_size),
            )
        return self._pool
    
    async def ensure_schema(self):
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(""" 
                CREATE TABLE IF NOT EXISTS agent_skins (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) UNIQUE NOT NULL,
                    description VARCHAR(200),
                    version VARCHAR(20) NOT NULL,
                    author VARCHAR(50),
                    license VARCHAR(20),
                    tags TEXT[],
                    variables JSONB NOT NULL,
                    preview_url TEXT,
                    downloads INTEGER DEFAULT 0,
                    rating DECIMAL(3,2) DEFAULT 0.0,
                    active BOOLEAN DEFAULT true,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    tenant_id VARCHAR(50)
                );
                CREATE INDEX IF NOT EXISTS idx_agent_skins_name 
                    ON agent_skins(name);
                CREATE INDEX IF NOT EXISTS idx_agent_skins_tags 
                    ON agent_skins USING GIN(tags);
            """)
    
    async def create(self, skin: Dict[str, Any]) -> Dict[str, Any]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO agent_skins 
                    (name, description, version, author, license, 
                     tags, variables, preview_url, tenant_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9)
                RETURNING *
            """,
                skin["name"],
                skin.get("description"),
                skin["version"],
                skin.get("author"),
                skin.get("license"),
                skin.get("tags", []),
                json.dumps(skin["variables"]),
                skin.get("preview"),
                skin.get("tenant_id"),
            )
            return dict(row)
    
    async def get_all(self, tenant_id: Optional[str] = None) -> List[Dict]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            query = "SELECT * FROM agent_skins WHERE active = true"
            params = []
            
            if tenant_id:
                query += " AND tenant_id = $1"
                params.append(tenant_id)
            
            query += " ORDER BY downloads DESC, rating DESC"
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def get_by_name(self, name: str) -> Optional[Dict]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM agent_skins WHERE name = $1", name
            )
            return dict(row) if row else None
    
    async def increment_downloads(self, name: str):
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE agent_skins SET downloads = downloads + 1 WHERE name = $1",
                name
            )
```

#### **FastAPI Router** (`services/gateway/routers/agentskins.py`)

```python
router = APIRouter(prefix="/v1/skins", tags=["agentskins"])

def _get_store():
    return AgentSkinsStore()

@router.get("")
async def list_skins(store=Depends(_get_store)):
    """List all active themes."""
    await store.ensure_schema()
    skins = await store.get_all()
    return {"skins": skins}

@router.get("/{name}")
async def get_skin(name: str, store=Depends(_get_store)):
    """Get specific theme by name."""
    skin = await store.get_by_name(name)
    if not skin:
        raise HTTPException(status_code=404, detail="Theme not found")
    
    # Increment download counter
    await store.increment_downloads(name)
    
    return {"skin": skin}

@router.post("/upload")
async def upload_skin(
    request: Request,
    file: UploadFile = File(...),
    store=Depends(_get_store)
):
    """Upload new theme (admin only)."""
    
    # Admin authorization
    await authorize_request(request, {"action": "skins.upload"})
    
    # Validate file
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files allowed")
    
    # Read and parse
    content = await file.read()
    try:
        theme = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Validate schema
    if not _validate_theme_schema(theme):
        raise HTTPException(status_code=400, detail="Invalid theme schema")
    
    # Security: Reject url() in values
    for key, value in theme.get("variables", {}).items():
        if "url(" in value:
            raise HTTPException(
                status_code=400,
                detail=f"XSS attempt: url() not allowed in {key}"
            )
    
    # Save to database
    await store.ensure_schema()
    skin = await store.create(theme)
    
    return {"skin": skin, "message": "Theme uploaded successfully"}

@router.delete("/{name}")
async def delete_skin(
    name: str,
    request: Request,
    store=Depends(_get_store)
):
    """Delete theme (admin only)."""
    await authorize_request(request, {"action": "skins.delete"})
    
    # Soft delete
    pool = await store._ensure_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE agent_skins SET active = false WHERE name = $1",
            name
        )
    
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Theme not found")
    
    return {"message": f"Theme '{name}' deleted"}
```

---

## 🔐 PERSONA 5: SECURITY ENGINEER — Security Model

### Security Requirements

#### **SR-1: Admin-Only Uploads**
- **Requirement**: Only admins can upload themes
- **Implementation**: OPA policy evaluation
- **Policy**:
```rego
allow {
    input.action == "skins.upload"
    input.user.role == "admin"
}
```

#### **SR-2: XSS Prevention**
- **Requirement**: Prevent malicious code in themes
- **Implementation**:
  - Reject `url()` in CSS values
  - Reject `<script>` tags in JSON
  - Sanitize all user inputs
  - CSP headers: `default-src 'self'; style-src 'self' 'unsafe-inline'`

#### **SR-3: HTTPS-Only Remote Themes**
- **Requirement**: Only load themes from HTTPS URLs
- **Implementation**:
```javascript
if (!url.startsWith('https://')) {
  throw new Error('Only HTTPS URLs allowed');
}
```

#### **SR-4: Tenant Isolation**
- **Requirement**: Users only see their tenant's themes
- **Implementation**: Filter by `tenant_id` in all queries

#### **SR-5: Rate Limiting**
- **Requirement**: Prevent abuse of upload endpoint
- **Implementation**:
  - Max 10 uploads per hour per user
  - Max file size: 100KB
  - Rate limit key: `skins:upload:{user_id}`

#### **SR-6: Content Validation**
- **Requirement**: All themes pass JSON Schema validation
- **Implementation**: AJV validation before storage

#### **SR-7: SQL Injection Prevention**
- **Requirement**: No SQL injection vulnerabilities
- **Implementation**: Parameterized queries only

#### **SR-8: WCAG AA Compliance**
- **Requirement**: Minimum 4.5:1 contrast ratio
- **Implementation**:
```javascript
function validateContrast(fg, bg) {
  const ratio = getContrastRatio(fg, bg);
  if (ratio < 4.5) {
    throw new Error(`Insufficient contrast:  ${ratio.toFixed(2)}:1`);
  }
}
```

---

## 🚀 PERSONA 6: DEVOPS ENGINEER — Deployment & Monitoring

### Deployment Strategy

#### **D-1: Zero-Downtime Deployment**
- Themes stored in PostgreSQL (persistent)
- CSS served from CDN (Cloudflare)
- Version rollback in < 60 seconds

#### **D-2: Performance Targets**
- Theme load: < 100ms (p95)
- Theme switch: < 50ms
- Preview generation: < 200ms
- Database query: < 20ms

#### **D-3: Caching Strategy**
```nginx
# Nginx config for theme files
location /themes/ {
    proxy_cache THEMES;
    proxy_cache_valid 200 24h;
    add_header Cache-Control "public, max-age=86400";
}
```

#### **D-4: Monitoring & Alerts**

**Prometheus Metrics:**
```python
theme_loads_total = Counter(
    "theme_loads_total",
    "Total theme loads",
    labelnames=["theme_name", "status"]
)

theme_load_duration = Histogram(
    "theme_load_duration_seconds",
    "Theme load duration",
    buckets=(0.01, 0.05, 0.1, 0.2, 0.5, 1.0)
)

theme_validation_errors = Counter(
    "theme_validation_errors_total",
    "Theme validation errors",
    labelnames=["error_type"]
)
```

**Grafana Dashboard:**
- Active themes count
- Most popular themes
- Load times (p50, p95, p99)
- Validation error rate
- Upload failures

#### **D-5: Backup & Recovery**
```bash
# Daily backup
pg_dump -t agent_skins > skins_backup_$(date +%Y%m%d).sql

# Recovery
psql < skins_backup_20251214.sql
```

---

## 🧪 PERSONA 7: QA ENGINEER — Testing Strategy

### Test Coverage Requirements

#### **Unit Tests** (60% coverage minimum)

**Theme Loader Tests:**
```javascript
describe('ThemeLoader', () => {
  test('loads local theme successfully', async () => {
    const theme = await loader.loadLocal('default');
    expect(theme.name).toBe('Default Light');
    expect(theme.variables).toHaveProperty('--bg-void');
  });

  test('rejects invalid schema', async () => {
    const invalid = { name: 'Bad' }; // Missing version, variables
    await expect(loader.validate(invalid)).rejects.toThrow();
  });

  test('blocks XSS via url()', async () => {
    const xss = {
      name: 'XSS',
      version: '1.0.0',
      variables: { '--bg': 'url(javascript:alert(1))' }
    };
    await expect(loader.validate(xss)).rejects.toThrow('XSS');
  });

  test('persists theme to localStorage', async () => {
    await loader.use('midnight');
    expect(localStorage.getItem('active-theme')).toBe('midnight');
  });
});
```

**Backend Tests:**
```python
@pytest.mark.asyncio
async def test_upload_theme_admin_only():
    """Non-admin uploads should be rejected."""
    response = await client.post(
        "/v1/skins/upload",
        files={"file": ("theme.json", json.dumps(valid_theme))},
        headers={"Authorization": "Bearer user_token"}
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_sql_injection_prevention():
    """SQL injection attempts should fail."""
    malicious_name = "'; DROP TABLE agent_skins;--"
    response = await client.get(f"/v1/skins/{malicious_name}")
    assert response.status_code == 404  # Not 500
```

#### **Integration Tests**

```javascript
test('end-to-end theme switching', async () => {
  // 1. Load theme gallery
  await page.goto('/settings');
  await page.click('[x-data="agentskins"]');
  
  // 2. Verify themes loaded
  const themes = await page.$$('.theme-card');
  expect(themes.length).toBeGreaterThan(0);
  
  // 3. Switch theme
  await page.click('[data-theme="midnight"]');
  await page.click('button:has-text("Apply")');
  
  // 4. Verify CSS variables changed
  const bgColor = await page.evaluate(() => 
    getComputedStyle(document.documentElement)
      .getPropertyValue('--bg-void')
  );
  expect(bgColor).toBe('#0a0a0f');
});
```

#### **E2E Tests (Playwright)**

```javascript
test('drag and drop theme installation', async ({ page }) => {
  await page.goto('/settings?tab=themes');
  
  // Create test file
  const themeJson = {
    name: 'Test Theme',
    version: '1.0.0',
    variables: { '--bg-void': '#000000' }
  };
  const file = new File([JSON.stringify(themeJson)], 'test.json');
  
  // Drag and drop
  const dropZone = page.locator('.theme-drop-zone');
  await dropZone.setInputFiles(file);
  
  // Verify success
  await expect(page.locator('.toast')).toContainText('Test Theme installed');
});
```

#### **Performance Tests**

```javascript
test('theme load performance', async () => {
  const start = performance.now();
  await loader.use('default');
  const duration = performance.now() - start;
  
  expect(duration).toBeLessThan(100); // < 100ms requirement
});
```

#### **Accessibility Tests**

```javascript
test('WCAG AA contrast compliance', async () => {
  const theme = await loader.loadLocal('default');
  const fg = theme.variables['--text-main'];
  const bg = theme.variables['--bg-void'];
  
  const ratio = getContrastRatio(fg, bg);
  expect(ratio).toBeGreaterThanOrEqual(4.5);
});
```

---

## 📋 COMPLETE FEATURE MATRIX

| Feature | Product | UX | Frontend | Backend | Security | DevOps | QA |
|---------|---------|----|-----------|---------|-----------|---------|----|
| Theme Gallery | ✅ | ✅ | ✅ | ✅ | - | ✅ | ✅ |
| Live Preview | ✅ | ✅ | ✅ | - | - | ✅ | ✅ |
| Drag-Drop Install | ✅ | ✅ | ✅ | ✅ | ✅ | - | ✅ |
| Remote Loading | ✅ | - | ✅ | - | ✅ | ✅ | ✅ |
| Admin Controls | ✅ | - | - | ✅ | ✅ | - | ✅ |
| Analytics | ✅ | - | - | ✅ | - | ✅ | - |
| Theme Creator | ✅ | ✅ | 🚧 | - | ✅ | - | 🚧 |
| Marketplace | ✅ | ✅ | 🚧 | 🚧 | ✅ | 🚧 | 🚧 |

✅ = Complete Spec | 🚧 = Future Enhancement | - = Not Applicable

---

## 🎯 SUCCESS CRITERIA

### Product Success
- [ ] 90% user adoption (9/10 users customize theme)
- [ ] 5+ themes installed per user
- [ ] < 1% validation errors
- [ ] 4.5+ user satisfaction score

### UX Success
- [ ] < 2 clicks to switch themes
- [ ] < 300ms perceived latency
- [ ] WCAG AA compliance (all themes)
- [ ] Zero accessibility violations

### Technical Success
- [ ] < 100ms theme load time (p95)
- [ ] < 50ms theme switch
- [ ] 99.9% uptime
- [ ] Zero XSS vulnerabilities

### Security Success
- [ ] 100% SQL injection prevention
- [ ] Admin-only uploads enforced
- [ ] HTTPS-only remote loads
- [ ] All secrets in Vault

---

**This document represents the COMPLETE vision of AgentSkin as seen through ALL 7 VIBE CODING personas. Ready for implementation!** 🎨✨
