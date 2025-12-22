# SomaStack Unified UI Design System - Design Document

## Document Control

| Field | Value |
|-------|-------|
| **Document ID** | SOMASTACK-UI-DESIGN-2025-12 |
| **Version** | 1.0 |
| **Date** | 2025-12-22 |
| **Status** | DRAFT |
| **Implements** | SOMASTACK-UI-REQ-2025-12 |

---

## Overview

This document defines the technical architecture for the SomaStack Unified UI Design System. The system provides a consistent visual language, component library, and theming infrastructure shared across SomaAgent01, SomaBrain, SomaFractalMemory, and AgentVoiceBox.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SomaStack Unified UI                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Design Tokens Layer                                                        │
│  ├── somastack-tokens.css (CSS Custom Properties)                          │
│  ├── Colors: neutral, primary, success, warning, error                     │
│  ├── Typography: Inter font, 6 scale values                                │
│  ├── Spacing: 8 scale values (4px - 64px)                                  │
│  └── Effects: minimal shadows, borders (no glassmorphism)                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  Component Layer (Lit Web Components)                                       │
│  ├── Layout: soma-sidebar, soma-header, soma-main, soma-footer             │
│  ├── Navigation: soma-nav-item, soma-nav-group, soma-breadcrumb            │
│  ├── Data Display: soma-stats-card, soma-data-table, soma-status           │
│  ├── Forms: soma-input, soma-select, soma-checkbox, soma-toggle            │
│  ├── Feedback: soma-toast, soma-modal, soma-skeleton, soma-spinner         │
│  └── Agent-Specific: soma-dashboard, soma-memory-browser, soma-voice       │
├─────────────────────────────────────────────────────────────────────────────┤
│  State Management Layer (Lit Reactive Controllers)                          │
│  ├── AuthController - Role management                                       │
│  ├── ThemeController - Theme state                                          │
│  ├── SettingsController - User preferences                                  │
│  └── StatusController - Service health                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  Integration Layer                                                          │
│  ├── JWT Token Parser                                                       │
│  ├── Health Check Client                                                    │
│  └── Settings API Client                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```


## File Structure

```
somastack-ui/
├── css/
│   ├── somastack-tokens.css      # Design tokens (CSS custom properties)
│   ├── somastack-base.css        # Reset and base styles
│   ├── somastack-components.css  # Component styles
│   └── somastack-utilities.css   # Utility classes
├── js/
│   ├── somastack-core.js         # Core utilities
│   ├── somastack-stores.js       # Alpine.js stores
│   ├── somastack-components.js   # Alpine.js components
│   └── somastack-theme.js        # Theme engine
├── fonts/
│   └── geist/                    # Geist font files
└── dist/
    ├── somastack-ui.css          # Bundled CSS
    └── somastack-ui.js           # Bundled JS
```

---

## Data Models

### Role Model

```typescript
type UserRole = 'admin' | 'operator' | 'viewer';

interface AuthState {
  isAuthenticated: boolean;
  role: UserRole;
  tenantId: string | null;
  userId: string | null;
  permissions: string[];
}

// Role permission matrix
const ROLE_PERMISSIONS: Record<UserRole, string[]> = {
  admin: ['view', 'create', 'edit', 'delete', 'approve', 'admin'],
  operator: ['view', 'create', 'edit', 'execute'],
  viewer: ['view']
};
```

### Theme Model

```typescript
interface ThemeState {
  mode: 'light' | 'dark' | 'system';
  currentTheme: string;
  customTokens: Record<string, string>;
}

interface ThemeDefinition {
  name: string;
  mode: 'light' | 'dark';
  tokens: Record<string, string>;
}
```

### Service Status Model

```typescript
type ServiceHealth = 'healthy' | 'degraded' | 'down' | 'unknown';

interface ServiceStatus {
  name: string;
  health: ServiceHealth;
  lastChecked: Date;
  latencyMs: number;
  details: Record<string, any>;
}

interface StatusState {
  services: Record<string, ServiceStatus>;
  isPolling: boolean;
  pollIntervalMs: number;
}
```


---

## Design Token Specification

### Color Tokens

```css
:root {
  /* Neutral Palette */
  --color-neutral-50: #fafafa;
  --color-neutral-100: #f5f5f5;
  --color-neutral-200: #e5e5e5;
  --color-neutral-300: #d4d4d4;
  --color-neutral-400: #a3a3a3;
  --color-neutral-500: #737373;
  --color-neutral-600: #525252;
  --color-neutral-700: #404040;
  --color-neutral-800: #262626;
  --color-neutral-900: #171717;
  
  /* Primary Palette (Blue) */
  --color-primary-50: #eff6ff;
  --color-primary-100: #dbeafe;
  --color-primary-500: #3b82f6;
  --color-primary-600: #2563eb;
  --color-primary-700: #1d4ed8;
  
  /* Success Palette (Green) */
  --color-success-50: #f0fdf4;
  --color-success-500: #22c55e;
  --color-success-600: #16a34a;
  
  /* Warning Palette (Amber) */
  --color-warning-50: #fffbeb;
  --color-warning-500: #f59e0b;
  --color-warning-600: #d97706;
  
  /* Error Palette (Red) */
  --color-error-50: #fef2f2;
  --color-error-500: #ef4444;
  --color-error-600: #dc2626;
}
```

### Semantic Tokens

```css
:root {
  /* Backgrounds */
  --bg-page: var(--color-neutral-50);
  --bg-surface-1: #ffffff;
  --bg-surface-2: rgba(255, 255, 255, 0.8);
  --bg-surface-3: rgba(255, 255, 255, 0.6);
  
  /* Text */
  --text-primary: var(--color-neutral-900);
  --text-secondary: var(--color-neutral-600);
  --text-muted: var(--color-neutral-400);
  
  /* Borders */
  --border-default: var(--color-neutral-200);
  --border-subtle: rgba(0, 0, 0, 0.1);
  
  /* Status Colors */
  --status-healthy: var(--color-success-500);
  --status-degraded: var(--color-warning-500);
  --status-down: var(--color-error-500);
  --status-unknown: var(--color-neutral-400);
}
```

### Typography Tokens

```css
:root {
  /* Font Family */
  --font-sans: 'Geist', system-ui, -apple-system, sans-serif;
  --font-mono: 'Geist Mono', ui-monospace, monospace;
  
  /* Font Sizes */
  --text-xs: 0.75rem;    /* 12px */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1rem;     /* 16px */
  --text-lg: 1.125rem;   /* 18px */
  --text-xl: 1.25rem;    /* 20px */
  --text-2xl: 1.5rem;    /* 24px */
  
  /* Font Weights */
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;
  
  /* Line Heights */
  --leading-tight: 1.25;
  --leading-normal: 1.5;
  --leading-relaxed: 1.75;
}
```

### Spacing Tokens

```css
:root {
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */
  --space-12: 3rem;     /* 48px */
  --space-16: 4rem;     /* 64px */
}
```

### Effect Tokens

```css
:root {
  /* Border Radius */
  --radius-none: 0;
  --radius-sm: 0.25rem;   /* 4px */
  --radius-md: 0.5rem;    /* 8px */
  --radius-lg: 0.75rem;   /* 12px */
  --radius-full: 9999px;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
  
  /* Glassmorphism */
  --glass-blur: blur(12px);
  --glass-bg: rgba(255, 255, 255, 0.7);
  --glass-border: rgba(255, 255, 255, 0.2);
  
  /* Transitions */
  --transition-fast: 100ms ease;
  --transition-normal: 200ms ease;
  --transition-slow: 300ms ease;
}
```


---

## Component Specifications

### Sidebar Navigation Component

```html
<nav x-data="sidebarNav" 
     class="soma-sidebar"
     :class="{ 'soma-sidebar--collapsed': isCollapsed }">
  
  <div class="soma-sidebar__header">
    <img src="/logo.svg" alt="SomaStack" class="soma-sidebar__logo">
    <button @click="toggleCollapse()" class="soma-sidebar__toggle">
      <span x-show="!isCollapsed">◀</span>
      <span x-show="isCollapsed">▶</span>
    </button>
  </div>
  
  <div class="soma-sidebar__content">
    <template x-for="group in navGroups" :key="group.id">
      <div class="soma-nav-group">
        <span class="soma-nav-group__label" x-text="group.label"></span>
        <template x-for="item in group.items" :key="item.id">
          <a :href="item.href"
             class="soma-nav-item"
             :class="{ 'soma-nav-item--active': isActive(item) }"
             x-show="hasPermission(item.permission)">
            <span class="soma-nav-item__icon" x-html="item.icon"></span>
            <span class="soma-nav-item__label" x-text="item.label"></span>
            <span x-show="item.badge" 
                  class="soma-nav-item__badge" 
                  x-text="item.badge"></span>
          </a>
        </template>
      </div>
    </template>
  </div>
</nav>
```

### Stats Card Component

```html
<div x-data="statsCard({ 
       value: 1234567, 
       previousValue: 1100000,
       label: 'Active Sessions',
       icon: 'users'
     })"
     class="soma-stats-card">
  
  <div class="soma-stats-card__icon">
    <span x-html="getIcon(icon)"></span>
  </div>
  
  <div class="soma-stats-card__content">
    <span class="soma-stats-card__value" x-text="formatNumber(value)"></span>
    <span class="soma-stats-card__label" x-text="label"></span>
  </div>
  
  <div class="soma-stats-card__trend"
       :class="trendClass">
    <span x-text="trendIcon"></span>
    <span x-text="trendPercent + '%'"></span>
  </div>
</div>
```

### Data Table Component

```html
<div x-data="dataTable({ 
       columns: [...],
       data: [...],
       pageSize: 10
     })"
     class="soma-table-container">
  
  <!-- Search/Filter -->
  <div class="soma-table__toolbar">
    <input type="search" 
           x-model="searchQuery"
           placeholder="Search..."
           class="soma-input soma-input--search">
    <template x-if="$store.auth.role === 'admin'">
      <button class="soma-btn soma-btn--primary">Add New</button>
    </template>
  </div>
  
  <!-- Table -->
  <table class="soma-table">
    <thead>
      <tr>
        <th class="soma-table__checkbox">
          <input type="checkbox" @change="toggleSelectAll()">
        </th>
        <template x-for="col in columns" :key="col.key">
          <th @click="sortBy(col.key)" 
              class="soma-table__header"
              :class="{ 'soma-table__header--sorted': sortColumn === col.key }">
            <span x-text="col.label"></span>
            <span x-show="sortColumn === col.key" x-text="sortDirection === 'asc' ? '↑' : '↓'"></span>
          </th>
        </template>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      <template x-for="row in paginatedData" :key="row.id">
        <tr class="soma-table__row">
          <td><input type="checkbox" :checked="isSelected(row.id)"></td>
          <template x-for="col in columns" :key="col.key">
            <td>
              <template x-if="col.type === 'status'">
                <span class="soma-badge" :class="'soma-badge--' + row[col.key]" x-text="row[col.key]"></span>
              </template>
              <template x-if="col.type !== 'status'">
                <span x-text="row[col.key]"></span>
              </template>
            </td>
          </template>
          <td class="soma-table__actions">
            <button class="soma-btn soma-btn--ghost soma-btn--sm">View</button>
            <template x-if="$store.auth.hasPermission('edit')">
              <button class="soma-btn soma-btn--ghost soma-btn--sm">Edit</button>
            </template>
            <template x-if="$store.auth.hasPermission('delete')">
              <button class="soma-btn soma-btn--ghost soma-btn--sm soma-btn--danger">Delete</button>
            </template>
          </td>
        </tr>
      </template>
    </tbody>
  </table>
  
  <!-- Pagination -->
  <div class="soma-table__pagination">
    <span x-text="'Showing ' + startIndex + '-' + endIndex + ' of ' + totalItems"></span>
    <div class="soma-pagination">
      <button @click="prevPage()" :disabled="currentPage === 1">←</button>
      <span x-text="currentPage + ' / ' + totalPages"></span>
      <button @click="nextPage()" :disabled="currentPage === totalPages">→</button>
    </div>
  </div>
</div>
```


### Status Indicator Component

```html
<div x-data="statusIndicator({ service: 'somabrain' })"
     class="soma-status">
  
  <span class="soma-status__dot"
        :class="'soma-status__dot--' + status.health"
        :title="status.health">
  </span>
  
  <span class="soma-status__label" x-text="service"></span>
  
  <span class="soma-status__time" x-text="formatTime(status.lastChecked)"></span>
  
  <!-- Tooltip on hover -->
  <div class="soma-status__tooltip" x-show="showTooltip">
    <div>Latency: <span x-text="status.latencyMs + 'ms'"></span></div>
    <div>Status: <span x-text="status.health"></span></div>
    <template x-for="(value, key) in status.details" :key="key">
      <div><span x-text="key"></span>: <span x-text="value"></span></div>
    </template>
  </div>
</div>
```

### Modal Component

```html
<div x-data="modal({ size: 'md' })"
     x-show="isOpen"
     x-transition:enter="soma-modal--enter"
     x-transition:leave="soma-modal--leave"
     class="soma-modal"
     @keydown.escape.window="close()">
  
  <!-- Backdrop -->
  <div class="soma-modal__backdrop" @click="closeOnBackdrop && close()"></div>
  
  <!-- Content -->
  <div class="soma-modal__content" :class="'soma-modal__content--' + size"
       x-trap.noscroll="isOpen">
    
    <div class="soma-modal__header">
      <h2 class="soma-modal__title" x-text="title"></h2>
      <button @click="close()" class="soma-modal__close">×</button>
    </div>
    
    <div class="soma-modal__body">
      <slot></slot>
    </div>
    
    <div class="soma-modal__footer" x-show="showFooter">
      <button @click="close()" class="soma-btn soma-btn--ghost">Cancel</button>
      <button @click="confirm()" class="soma-btn soma-btn--primary">Confirm</button>
    </div>
  </div>
</div>
```

### Toast Notification Component

```html
<div x-data="toastContainer"
     class="soma-toast-container">
  
  <template x-for="toast in toasts" :key="toast.id">
    <div class="soma-toast"
         :class="'soma-toast--' + toast.variant"
         x-show="toast.visible"
         x-transition>
      
      <span class="soma-toast__icon" x-html="getIcon(toast.variant)"></span>
      <span class="soma-toast__message" x-text="toast.message"></span>
      <button @click="dismiss(toast.id)" class="soma-toast__close">×</button>
    </div>
  </template>
</div>
```

---

## Alpine.js Store Specifications

### Auth Store

```javascript
Alpine.store('auth', {
  isAuthenticated: false,
  role: 'viewer',
  tenantId: null,
  userId: null,
  permissions: [],
  
  init() {
    this.loadFromToken();
  },
  
  loadFromToken() {
    const token = localStorage.getItem('soma_token');
    if (!token) {
      this.setRole('viewer');
      return;
    }
    
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      this.isAuthenticated = true;
      this.role = payload.role || 'viewer';
      this.tenantId = payload.tenant_id;
      this.userId = payload.sub;
      this.permissions = ROLE_PERMISSIONS[this.role] || [];
    } catch (e) {
      console.error('Failed to parse JWT:', e);
      this.setRole('viewer');
    }
  },
  
  setRole(role) {
    this.role = role;
    this.permissions = ROLE_PERMISSIONS[role] || [];
  },
  
  hasPermission(permission) {
    return this.permissions.includes(permission);
  },
  
  get isAdmin() {
    return this.role === 'admin';
  },
  
  get isOperator() {
    return this.role === 'operator' || this.role === 'admin';
  }
});
```

### Theme Store

```javascript
Alpine.store('theme', {
  mode: 'system',
  currentTheme: 'default',
  
  init() {
    this.loadPreference();
    this.applyTheme();
    this.watchSystemPreference();
  },
  
  loadPreference() {
    const saved = localStorage.getItem('soma_theme_mode');
    if (saved) this.mode = saved;
  },
  
  setMode(mode) {
    this.mode = mode;
    localStorage.setItem('soma_theme_mode', mode);
    this.applyTheme();
  },
  
  applyTheme() {
    const isDark = this.mode === 'dark' || 
      (this.mode === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    
    document.documentElement.classList.toggle('soma-dark', isDark);
  },
  
  watchSystemPreference() {
    window.matchMedia('(prefers-color-scheme: dark)')
      .addEventListener('change', () => {
        if (this.mode === 'system') this.applyTheme();
      });
  },
  
  toggle() {
    this.setMode(this.mode === 'dark' ? 'light' : 'dark');
  }
});
```

### Status Store

```javascript
Alpine.store('status', {
  services: {},
  isPolling: false,
  pollIntervalMs: 5000,
  
  init() {
    this.startPolling();
  },
  
  async checkHealth(serviceName, endpoint) {
    try {
      const start = performance.now();
      const response = await fetch(endpoint);
      const latency = Math.round(performance.now() - start);
      const data = await response.json();
      
      this.services[serviceName] = {
        name: serviceName,
        health: data.ok ? 'healthy' : 'degraded',
        lastChecked: new Date(),
        latencyMs: latency,
        details: data.components || {}
      };
    } catch (e) {
      this.services[serviceName] = {
        name: serviceName,
        health: 'down',
        lastChecked: new Date(),
        latencyMs: 0,
        details: { error: e.message }
      };
    }
  },
  
  async checkAllServices() {
    const endpoints = {
      somabrain: 'http://localhost:9696/health',
      somamemory: 'http://localhost:9595/healthz',
      somaagent: 'http://localhost:21016/v1/health'
    };
    
    await Promise.all(
      Object.entries(endpoints).map(([name, url]) => this.checkHealth(name, url))
    );
  },
  
  startPolling() {
    this.isPolling = true;
    this.checkAllServices();
    setInterval(() => this.checkAllServices(), this.pollIntervalMs);
  }
});
```


---

## Responsive Breakpoints

```css
/* Mobile First Approach */
:root {
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;
  --breakpoint-2xl: 1536px;
}

/* Layout Behavior */
@media (max-width: 639px) {
  /* Mobile: Bottom navigation, stacked cards */
  .soma-sidebar { display: none; }
  .soma-bottom-nav { display: flex; }
  .soma-stats-grid { grid-template-columns: 1fr; }
}

@media (min-width: 640px) and (max-width: 1023px) {
  /* Tablet: Collapsed sidebar (icons only) */
  .soma-sidebar { width: 64px; }
  .soma-sidebar__label { display: none; }
  .soma-stats-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (min-width: 1024px) {
  /* Desktop: Full sidebar */
  .soma-sidebar { width: 240px; }
  .soma-stats-grid { grid-template-columns: repeat(4, 1fr); }
}
```

---

## Accessibility Implementation

### Focus Management

```css
/* Focus ring for all interactive elements */
.soma-focusable:focus-visible {
  outline: 2px solid var(--color-primary-500);
  outline-offset: 2px;
}

/* Skip link for keyboard users */
.soma-skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  z-index: 100;
}

.soma-skip-link:focus {
  top: 0;
}
```

### ARIA Patterns

```html
<!-- Live region for status updates -->
<div aria-live="polite" aria-atomic="true" class="soma-sr-only" id="status-announcer"></div>

<!-- Navigation landmark -->
<nav aria-label="Main navigation" class="soma-sidebar">...</nav>

<!-- Table with proper semantics -->
<table role="grid" aria-label="Data table">
  <thead>
    <tr role="row">
      <th role="columnheader" aria-sort="ascending">Column</th>
    </tr>
  </thead>
</table>
```

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```


---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: CSS Token Propagation
*For any* CSS custom property defined in `somastack-tokens.css`, changing its value at `:root` level SHALL cause all components using that token to update their rendered appearance without code changes.
**Validates: Requirements 1.1, 1.2**

### Property 2: WCAG Contrast Compliance
*For any* text color and background color combination defined in the design system, the contrast ratio SHALL be at least 4.5:1 for normal text and 3:1 for large text (WCAG AA).
**Validates: Requirements 2.4, 13.1**

### Property 3: Role-Based UI Visibility
*For any* user with a given role (admin/operator/viewer), UI elements SHALL be visible if and only if the user's role has the required permission for that element.
**Validates: Requirements 3.2, 3.3, 3.4, 10.6**

### Property 4: JWT Role Extraction
*For any* valid JWT token containing a `role` claim, the Role_Manager SHALL correctly extract and apply that role; for invalid or missing tokens, the system SHALL default to 'viewer' role.
**Validates: Requirements 3.5, 3.6**

### Property 5: Number Formatting
*For any* numeric value >= 1000, the Stats_Card_Component SHALL format it with appropriate suffix (K for thousands, M for millions, B for billions) while preserving 1-3 significant digits.
**Validates: Requirement 5.5**

### Property 6: Table Sorting Correctness
*For any* column in a Data_Table, clicking the header SHALL sort all rows by that column's values in ascending order; clicking again SHALL reverse to descending order.
**Validates: Requirement 6.2**

### Property 7: Table Pagination Activation
*For any* Data_Table with more than `pageSize` rows (default 10), pagination controls SHALL be displayed and functional; for tables with <= `pageSize` rows, pagination SHALL be hidden.
**Validates: Requirement 6.6**

### Property 8: Status Update Latency
*For any* service health change, the Status_Indicator SHALL reflect the new status within 5 seconds of the change occurring.
**Validates: Requirement 7.2**

### Property 9: Settings Validation
*For any* settings input, the Settings_Panel SHALL validate the input before saving; invalid inputs SHALL be rejected with an error message and the previous value SHALL be preserved.
**Validates: Requirements 8.5, 8.6**

### Property 10: Memory Search Accuracy
*For any* search query in the Memory_Browser, all returned results SHALL contain the search term in their content, coordinate, or metadata fields.
**Validates: Requirement 10.2**

### Property 11: Responsive Layout Correctness
*For any* viewport width, the Layout_System SHALL apply the correct layout configuration: mobile (<640px) shows bottom nav, tablet (640-1023px) shows collapsed sidebar, desktop (>=1024px) shows full sidebar.
**Validates: Requirements 12.2, 12.3**

### Property 12: Touch Target Size
*For any* interactive element on mobile viewports (<640px), the touch target size SHALL be at least 44x44 pixels.
**Validates: Requirement 12.6**

### Property 13: Keyboard Navigation
*For any* interactive element in the UI, it SHALL be reachable and activatable using only keyboard (Tab for focus, Enter/Space for activation, Arrow keys for navigation within components).
**Validates: Requirements 4.6, 13.2**

### Property 14: Focus Indicator Visibility
*For any* focusable element, when focused via keyboard, a visible focus indicator SHALL be displayed with sufficient contrast against the background.
**Validates: Requirement 13.5**

### Property 15: ARIA Label Completeness
*For any* non-text content (icons, images, interactive elements), an appropriate ARIA label or accessible name SHALL be provided.
**Validates: Requirement 13.3**

### Property 16: Theme Switching Performance
*For any* theme toggle action, the visual change SHALL complete within 100ms and all components SHALL render correctly in the new theme.
**Validates: Requirements 14.2, 14.6**

### Property 17: State Persistence Round-Trip
*For any* user preference stored in localStorage (theme, sidebar state, settings), refreshing the page SHALL restore the exact same state.
**Validates: Requirements 4.7, 8.3, 14.3**

### Property 18: Toast Auto-Dismiss
*For any* toast notification without explicit user dismissal, it SHALL automatically disappear after the configured timeout (default 5 seconds).
**Validates: Requirement 15.7**

### Property 19: Form Focus Ring
*For any* form input element, when focused, a visible focus ring with the accent color SHALL be displayed.
**Validates: Requirement 16.5**

### Property 20: Modal Behavior Correctness
*For any* open modal: (a) focus SHALL be trapped within the modal, (b) pressing Escape SHALL close it, (c) clicking backdrop SHALL close it (if configured), (d) body scroll SHALL be prevented, (e) stacked modals SHALL have correct z-index ordering.
**Validates: Requirements 17.2, 17.3, 17.4, 17.6, 17.7**

### Property 21: Error Message Display
*For any* error condition, the Error_Component SHALL display a user-friendly message (not raw error text or stack traces) along with an error code for support reference.
**Validates: Requirement 15.4**


---

## Error Handling

| Error | Response | User Message |
|-------|----------|--------------|
| JWT parse failure | Default to viewer | (Silent - no message) |
| Health check timeout | Mark service as 'unknown' | "Unable to reach service" |
| Settings save failure | Preserve previous value | "Failed to save settings. Please try again." |
| Theme load failure | Fall back to default | "Theme could not be loaded" |
| API 401 response | Redirect to login | "Session expired. Please log in again." |
| API 403 response | Show permission error | "You don't have permission for this action" |
| Network error | Show retry option | "Connection error. Check your network." |

---

## Testing Strategy

### Unit Tests
- Token validation (all required tokens present)
- Role permission matrix correctness
- Number formatting function
- Contrast ratio calculation
- JWT parsing

### Property Tests (Hypothesis/fast-check)
- WCAG contrast compliance for all color combinations
- Role-based visibility for all UI elements
- Sorting correctness for all data types
- Pagination boundary conditions
- State persistence round-trip

### E2E Tests (Playwright)
- Theme switching flow
- Navigation keyboard accessibility
- Modal focus trap
- Form validation
- Responsive layout at all breakpoints
- Status indicator updates

### Visual Regression Tests
- Component snapshots at all breakpoints
- Theme variants (light/dark)
- Loading/error states

---

## Integration Points

### SomaAgent01
- Import: `<link rel="stylesheet" href="/static/somastack-ui/somastack-ui.css">`
- Import: `<script src="/static/somastack-ui/somastack-ui.js"></script>`
- Health endpoint: `GET /v1/health`
- Settings API: `GET/POST /v1/settings`

### SomaBrain
- Health endpoint: `GET /health`
- Neuromodulator API: `GET/POST /neuromodulators`
- Adaptation API: `GET /context/adaptation/state`

### SomaFractalMemory
- Health endpoint: `GET /healthz`
- Memory API: `GET/POST /memories`
- Search API: `POST /memories/search`

### AgentVoiceBox
- Health endpoint: `GET /health`
- Voice API: WebSocket `/ws/voice`

---

## Migration Plan

### Phase 1: Create Design System Package
1. Create `somastack-ui/` directory structure
2. Implement design tokens CSS
3. Implement base styles and utilities
4. Package as distributable bundle

### Phase 2: Implement Core Components
1. Layout components (Sidebar, Header, Main)
2. Navigation components
3. Data display components (StatsCard, DataTable, StatusIndicator)
4. Form components
5. Feedback components (Toast, Modal, Skeleton)

### Phase 3: Implement Alpine.js Stores
1. Auth store with JWT parsing
2. Theme store with persistence
3. Status store with polling
4. Settings store

### Phase 4: Integrate with SomaAgent01
1. Replace existing styles with design system
2. Update index.html to use new components
3. Migrate existing Alpine components

### Phase 5: Integrate with Other Projects
1. Add design system to SomaBrain (if UI exists)
2. Add design system to SomaFractalMemory (if UI exists)
3. Add design system to AgentVoiceBox

### Phase 6: Testing and Documentation
1. Write unit tests
2. Write property tests
3. Write E2E tests
4. Create component documentation

---

**Last Updated:** 2025-12-22  
**Status:** DRAFT - Pending Review
