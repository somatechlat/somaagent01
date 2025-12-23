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
│   ├── somastack-controllers.js  # Lit Reactive Controllers
│   ├── somastack-components.js   # Lit Web Components
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

### Sidebar Navigation Component (Lit Web Component)

```html
<soma-sidebar ?collapsed="${this.isCollapsed}">
  <div class="soma-sidebar__header">
    <img src="/logo.svg" alt="SomaStack" class="soma-sidebar__logo">
    <button @click="${this._toggleCollapse}" class="soma-sidebar__toggle">
      ${this.isCollapsed ? html`▶` : html`◀`}
    </button>
  </div>
  
  <div class="soma-sidebar__content">
    ${this.navGroups.map(group => html`
      <div class="soma-nav-group">
        <span class="soma-nav-group__label">${group.label}</span>
        ${group.items.filter(item => this._hasPermission(item.permission)).map(item => html`
          <a href="${item.href}"
             class="soma-nav-item ${this._isActive(item) ? 'soma-nav-item--active' : ''}">
            <span class="soma-nav-item__icon">${unsafeHTML(item.icon)}</span>
            <span class="soma-nav-item__label">${item.label}</span>
            ${item.badge ? html`<span class="soma-nav-item__badge">${item.badge}</span>` : nothing}
          </a>
        `)}
      </div>
    `)}
  </div>
</soma-sidebar>
```

### Stats Card Component (Lit Web Component)

```html
<soma-stats-card
  .value="${1234567}"
  .previousValue="${1100000}"
  label="Active Sessions"
  icon="users">
</soma-stats-card>
```

```typescript
// Lit Web Component Implementation
@customElement('soma-stats-card')
export class SomaStatsCard extends LitElement {
  @property({ type: Number }) value = 0;
  @property({ type: Number }) previousValue = 0;
  @property({ type: String }) label = '';
  @property({ type: String }) icon = '';

  private get trendPercent() {
    if (!this.previousValue) return 0;
    return Math.round(((this.value - this.previousValue) / this.previousValue) * 100);
  }

  private get trendClass() {
    return this.trendPercent >= 0 ? 'soma-stats-card__trend--up' : 'soma-stats-card__trend--down';
  }

  render() {
    return html`
      <div class="soma-stats-card">
        <div class="soma-stats-card__icon">
          <span>${unsafeHTML(this._getIcon(this.icon))}</span>
        </div>
        <div class="soma-stats-card__content">
          <span class="soma-stats-card__value">${this._formatNumber(this.value)}</span>
          <span class="soma-stats-card__label">${this.label}</span>
        </div>
        <div class="soma-stats-card__trend ${this.trendClass}">
          <span>${this.trendPercent >= 0 ? '↑' : '↓'}</span>
          <span>${Math.abs(this.trendPercent)}%</span>
        </div>
      </div>
    `;
  }
}
```

### Data Table Component (Lit Web Component)

```html
<soma-data-table
  .columns="${columns}"
  .data="${data}"
  .pageSize="${10}">
</soma-data-table>
```

```typescript
// Lit Web Component Implementation
@customElement('soma-data-table')
export class SomaDataTable extends LitElement {
  @property({ type: Array }) columns: Column[] = [];
  @property({ type: Array }) data: any[] = [];
  @property({ type: Number }) pageSize = 10;
  
  @state() private searchQuery = '';
  @state() private sortColumn = '';
  @state() private sortDirection: 'asc' | 'desc' = 'asc';
  @state() private currentPage = 1;
  @state() private selectedIds = new Set<string>();

  // Inject AuthController for role-based visibility
  private authController = new AuthController(this);

  render() {
    return html`
      <div class="soma-table-container">
        <div class="soma-table__toolbar">
          <input type="search" 
                 .value="${this.searchQuery}"
                 @input="${this._onSearch}"
                 placeholder="Search..."
                 class="soma-input soma-input--search">
          ${this.authController.role === 'admin' ? html`
            <button class="soma-btn soma-btn--primary">Add New</button>
          ` : nothing}
        </div>
        
        <table class="soma-table">
          <thead>
            <tr>
              <th class="soma-table__checkbox">
                <input type="checkbox" @change="${this._toggleSelectAll}">
              </th>
              ${this.columns.map(col => html`
                <th @click="${() => this._sortBy(col.key)}" 
                    class="soma-table__header ${this.sortColumn === col.key ? 'soma-table__header--sorted' : ''}">
                  <span>${col.label}</span>
                  ${this.sortColumn === col.key ? html`<span>${this.sortDirection === 'asc' ? '↑' : '↓'}</span>` : nothing}
                </th>
              `)}
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            ${this._paginatedData.map(row => html`
              <tr class="soma-table__row">
                <td><input type="checkbox" .checked="${this.selectedIds.has(row.id)}"></td>
                ${this.columns.map(col => html`
                  <td>
                    ${col.type === 'status' 
                      ? html`<span class="soma-badge soma-badge--${row[col.key]}">${row[col.key]}</span>`
                      : html`<span>${row[col.key]}</span>`}
                  </td>
                `)}
                <td class="soma-table__actions">
                  <button class="soma-btn soma-btn--ghost soma-btn--sm">View</button>
                  ${this.authController.hasPermission('edit') ? html`
                    <button class="soma-btn soma-btn--ghost soma-btn--sm">Edit</button>
                  ` : nothing}
                  ${this.authController.hasPermission('delete') ? html`
                    <button class="soma-btn soma-btn--ghost soma-btn--sm soma-btn--danger">Delete</button>
                  ` : nothing}
                </td>
              </tr>
            `)}
          </tbody>
        </table>
        
        <div class="soma-table__pagination">
          <span>Showing ${this._startIndex}-${this._endIndex} of ${this._totalItems}</span>
          <div class="soma-pagination">
            <button @click="${this._prevPage}" ?disabled="${this.currentPage === 1}">←</button>
            <span>${this.currentPage} / ${this._totalPages}</span>
            <button @click="${this._nextPage}" ?disabled="${this.currentPage === this._totalPages}">→</button>
          </div>
        </div>
      </div>
    `;
  }
}
```


### Status Indicator Component (Lit Web Component)

```html
<soma-status-indicator service="somabrain"></soma-status-indicator>
```

```typescript
// Lit Web Component Implementation
@customElement('soma-status-indicator')
export class SomaStatusIndicator extends LitElement {
  @property({ type: String }) service = '';
  
  @state() private showTooltip = false;
  
  // Inject StatusController for service health data
  private statusController = new StatusController(this);

  private get status() {
    return this.statusController.getServiceStatus(this.service);
  }

  render() {
    return html`
      <div class="soma-status"
           @mouseenter="${() => this.showTooltip = true}"
           @mouseleave="${() => this.showTooltip = false}">
        
        <span class="soma-status__dot soma-status__dot--${this.status.health}"
              title="${this.status.health}">
        </span>
        
        <span class="soma-status__label">${this.service}</span>
        
        <span class="soma-status__time">${this._formatTime(this.status.lastChecked)}</span>
        
        ${this.showTooltip ? html`
          <div class="soma-status__tooltip">
            <div>Latency: <span>${this.status.latencyMs}ms</span></div>
            <div>Status: <span>${this.status.health}</span></div>
            ${Object.entries(this.status.details).map(([key, value]) => html`
              <div><span>${key}</span>: <span>${value}</span></div>
            `)}
          </div>
        ` : nothing}
      </div>
    `;
  }
}
```

### Modal Component (Lit Web Component)

```html
<soma-modal 
  ?open="${this.isModalOpen}"
  size="md"
  title="Confirm Action"
  @close="${this._onModalClose}"
  @confirm="${this._onModalConfirm}">
  <p>Are you sure you want to proceed?</p>
</soma-modal>
```

```typescript
// Lit Web Component Implementation
@customElement('soma-modal')
export class SomaModal extends LitElement {
  @property({ type: Boolean, reflect: true }) open = false;
  @property({ type: String }) size: 'sm' | 'md' | 'lg' = 'md';
  @property({ type: String }) title = '';
  @property({ type: Boolean }) closeOnBackdrop = true;
  @property({ type: Boolean }) showFooter = true;

  connectedCallback() {
    super.connectedCallback();
    window.addEventListener('keydown', this._handleEscape);
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    window.removeEventListener('keydown', this._handleEscape);
  }

  private _handleEscape = (e: KeyboardEvent) => {
    if (e.key === 'Escape' && this.open) {
      this._close();
    }
  };

  private _close() {
    this.dispatchEvent(new CustomEvent('close'));
  }

  private _confirm() {
    this.dispatchEvent(new CustomEvent('confirm'));
  }

  render() {
    if (!this.open) return nothing;
    
    return html`
      <div class="soma-modal">
        <div class="soma-modal__backdrop" 
             @click="${() => this.closeOnBackdrop && this._close()}"></div>
        
        <div class="soma-modal__content soma-modal__content--${this.size}">
          <div class="soma-modal__header">
            <h2 class="soma-modal__title">${this.title}</h2>
            <button @click="${this._close}" class="soma-modal__close">×</button>
          </div>
          
          <div class="soma-modal__body">
            <slot></slot>
          </div>
          
          ${this.showFooter ? html`
            <div class="soma-modal__footer">
              <button @click="${this._close}" class="soma-btn soma-btn--ghost">Cancel</button>
              <button @click="${this._confirm}" class="soma-btn soma-btn--primary">Confirm</button>
            </div>
          ` : nothing}
        </div>
      </div>
    `;
  }
}
```

### Toast Notification Component (Lit Web Component)

```html
<soma-toast-container></soma-toast-container>
```

```typescript
// Lit Web Component Implementation
@customElement('soma-toast-container')
export class SomaToastContainer extends LitElement {
  @state() private toasts: Toast[] = [];

  // Global toast service integration
  connectedCallback() {
    super.connectedCallback();
    window.addEventListener('soma-toast', this._handleToastEvent as EventListener);
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    window.removeEventListener('soma-toast', this._handleToastEvent as EventListener);
  }

  private _handleToastEvent = (e: CustomEvent<Toast>) => {
    this._addToast(e.detail);
  };

  private _addToast(toast: Toast) {
    const id = crypto.randomUUID();
    this.toasts = [...this.toasts, { ...toast, id, visible: true }];
    
    // Auto-dismiss after timeout
    setTimeout(() => this._dismiss(id), toast.duration || 5000);
  }

  private _dismiss(id: string) {
    this.toasts = this.toasts.filter(t => t.id !== id);
  }

  render() {
    return html`
      <div class="soma-toast-container">
        ${this.toasts.map(toast => html`
          <div class="soma-toast soma-toast--${toast.variant}">
            <span class="soma-toast__icon">${unsafeHTML(this._getIcon(toast.variant))}</span>
            <span class="soma-toast__message">${toast.message}</span>
            <button @click="${() => this._dismiss(toast.id)}" class="soma-toast__close">×</button>
          </div>
        `)}
      </div>
    `;
  }
}

// Global toast function
export function showToast(message: string, variant: 'success' | 'error' | 'warning' | 'info' = 'info') {
  window.dispatchEvent(new CustomEvent('soma-toast', { detail: { message, variant } }));
}
```

---

## Lit Reactive Controller Specifications

### AuthController

```typescript
// Lit Reactive Controller for authentication state
import { ReactiveController, ReactiveControllerHost } from 'lit';

const ROLE_PERMISSIONS: Record<string, string[]> = {
  admin: ['view', 'create', 'edit', 'delete', 'approve', 'admin'],
  operator: ['view', 'create', 'edit', 'execute'],
  viewer: ['view']
};

export class AuthController implements ReactiveController {
  host: ReactiveControllerHost;
  
  isAuthenticated = false;
  role: 'admin' | 'operator' | 'viewer' = 'viewer';
  tenantId: string | null = null;
  userId: string | null = null;
  permissions: string[] = [];

  constructor(host: ReactiveControllerHost) {
    this.host = host;
    host.addController(this);
  }

  hostConnected() {
    this.loadFromToken();
  }

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
      this.host.requestUpdate();
    } catch (e) {
      console.error('Failed to parse JWT:', e);
      this.setRole('viewer');
    }
  }

  setRole(role: 'admin' | 'operator' | 'viewer') {
    this.role = role;
    this.permissions = ROLE_PERMISSIONS[role] || [];
    this.host.requestUpdate();
  }

  hasPermission(permission: string): boolean {
    return this.permissions.includes(permission);
  }

  get isAdmin(): boolean {
    return this.role === 'admin';
  }

  get isOperator(): boolean {
    return this.role === 'operator' || this.role === 'admin';
  }
}
```

### ThemeController

```typescript
// Lit Reactive Controller for theme state
import { ReactiveController, ReactiveControllerHost } from 'lit';

export class ThemeController implements ReactiveController {
  host: ReactiveControllerHost;
  
  mode: 'light' | 'dark' | 'system' = 'system';
  currentTheme = 'default';
  private mediaQuery: MediaQueryList;

  constructor(host: ReactiveControllerHost) {
    this.host = host;
    host.addController(this);
    this.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  }

  hostConnected() {
    this.loadPreference();
    this.applyTheme();
    this.mediaQuery.addEventListener('change', this._handleSystemChange);
  }

  hostDisconnected() {
    this.mediaQuery.removeEventListener('change', this._handleSystemChange);
  }

  private _handleSystemChange = () => {
    if (this.mode === 'system') {
      this.applyTheme();
      this.host.requestUpdate();
    }
  };

  loadPreference() {
    const saved = localStorage.getItem('soma_theme_mode');
    if (saved) this.mode = saved as 'light' | 'dark' | 'system';
  }

  setMode(mode: 'light' | 'dark' | 'system') {
    this.mode = mode;
    localStorage.setItem('soma_theme_mode', mode);
    this.applyTheme();
    this.host.requestUpdate();
  }

  applyTheme() {
    const isDark = this.mode === 'dark' || 
      (this.mode === 'system' && this.mediaQuery.matches);
    
    document.documentElement.classList.toggle('soma-dark', isDark);
  }

  toggle() {
    this.setMode(this.mode === 'dark' ? 'light' : 'dark');
  }
}
```

### StatusController

```typescript
// Lit Reactive Controller for service status
import { ReactiveController, ReactiveControllerHost } from 'lit';

interface ServiceStatus {
  name: string;
  health: 'healthy' | 'degraded' | 'down' | 'unknown';
  lastChecked: Date;
  latencyMs: number;
  details: Record<string, any>;
}

export class StatusController implements ReactiveController {
  host: ReactiveControllerHost;
  
  services: Record<string, ServiceStatus> = {};
  isPolling = false;
  pollIntervalMs = 5000;
  private intervalId: number | null = null;

  private readonly endpoints = {
    somabrain: 'http://localhost:9696/health',
    somamemory: 'http://localhost:9595/healthz',
    somaagent: 'http://localhost:21016/v1/health'
  };

  constructor(host: ReactiveControllerHost) {
    this.host = host;
    host.addController(this);
  }

  hostConnected() {
    this.startPolling();
  }

  hostDisconnected() {
    this.stopPolling();
  }

  async checkHealth(serviceName: string, endpoint: string) {
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
        details: { error: (e as Error).message }
      };
    }
    this.host.requestUpdate();
  }

  async checkAllServices() {
    await Promise.all(
      Object.entries(this.endpoints).map(([name, url]) => this.checkHealth(name, url))
    );
  }

  startPolling() {
    this.isPolling = true;
    this.checkAllServices();
    this.intervalId = window.setInterval(() => this.checkAllServices(), this.pollIntervalMs);
  }

  stopPolling() {
    this.isPolling = false;
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  getServiceStatus(serviceName: string): ServiceStatus {
    return this.services[serviceName] || {
      name: serviceName,
      health: 'unknown',
      lastChecked: new Date(),
      latencyMs: 0,
      details: {}
    };
  }
}
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
