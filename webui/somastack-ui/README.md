# SomaStack Unified UI Design System

A comprehensive, standardized visual language and component library for all SomaStack platform applications.

## Overview

The SomaStack Unified UI Design System (SUIDS) provides:

- **Design Tokens**: Centralized CSS custom properties for colors, typography, spacing, and effects
- **Glassmorphism Surfaces**: Modern frosted glass aesthetic with subtle depth
- **Component Library**: Reusable Alpine.js components for common UI patterns
- **Role-Based Access**: Dynamic UI visibility based on user roles (Admin/Operator/Viewer)
- **Theme Support**: Light/dark/system theme switching with persistence
- **Status Monitoring**: Real-time service health visualization
- **Accessibility**: WCAG 2.1 AA compliant

## Quick Start

### Installation

Add the design system to your HTML:

```html
<!-- CSS -->
<link rel="stylesheet" href="/somastack-ui/dist/somastack-ui.css">

<!-- JavaScript (requires Alpine.js 3.x) -->
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
<script src="/somastack-ui/dist/somastack-ui.js"></script>
```

### Basic Usage

```html
<!DOCTYPE html>
<html lang="en" class="soma-light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SomaStack App</title>
  <link rel="stylesheet" href="/somastack-ui/dist/somastack-ui.css">
</head>
<body class="soma-body">
  <div class="soma-layout" x-data>
    <!-- Sidebar -->
    <nav class="soma-sidebar" x-data="sidebarNav">
      <!-- Navigation items -->
    </nav>
    
    <!-- Main Content -->
    <main class="soma-main">
      <!-- Your content here -->
    </main>
  </div>
  
  <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
  <script src="/somastack-ui/dist/somastack-ui.js"></script>
</body>
</html>
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
│   ├── stores/
│   │   ├── auth-store.js         # Authentication/role state
│   │   ├── theme-store.js        # Theme state
│   │   └── status-store.js       # Service health state
│   └── components/
│       ├── sidebar-nav.js        # Sidebar navigation
│       ├── stats-card.js         # Stats card component
│       ├── data-table.js         # Data table component
│       ├── status-indicator.js   # Status indicator
│       ├── modal.js              # Modal dialog
│       ├── toast.js              # Toast notifications
│       └── form-validation.js    # Form validation
├── fonts/
│   └── geist/                    # Geist font files
├── dist/
│   ├── somastack-ui.css          # Bundled CSS
│   ├── somastack-ui.js           # Bundled JS
│   ├── somastack-ui.min.css      # Minified CSS
│   └── somastack-ui.min.js       # Minified JS
├── package.json
└── README.md
```

## Design Tokens

All visual attributes are defined as CSS custom properties:

### Colors

```css
/* Neutral */
--color-neutral-50 through --color-neutral-900

/* Primary (Blue) */
--color-primary-50, --color-primary-500, --color-primary-600

/* Semantic */
--color-success-500  /* Green */
--color-warning-500  /* Amber */
--color-error-500    /* Red */
```

### Typography

```css
--font-sans: 'Geist', system-ui, sans-serif;
--text-xs: 0.75rem;   /* 12px */
--text-sm: 0.875rem;  /* 14px */
--text-base: 1rem;    /* 16px */
--text-lg: 1.125rem;  /* 18px */
--text-xl: 1.25rem;   /* 20px */
--text-2xl: 1.5rem;   /* 24px */
```

### Spacing

```css
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
```

### Effects

```css
--radius-sm: 4px;
--radius-md: 8px;
--radius-lg: 12px;
--shadow-sm, --shadow-md, --shadow-lg
--glass-blur: blur(12px);
--glass-bg: rgba(255, 255, 255, 0.7);
```

## Components

### Stats Card

```html
<div x-data="statsCard({ value: 1234567, label: 'Active Sessions' })"
     class="soma-stats-card">
  <span class="soma-stats-card__value" x-text="formatNumber(value)"></span>
  <span class="soma-stats-card__label" x-text="label"></span>
</div>
```

### Data Table

```html
<div x-data="dataTable({ columns: [...], data: [...] })"
     class="soma-table-container">
  <!-- Table renders automatically -->
</div>
```

### Status Indicator

```html
<div x-data="statusIndicator({ service: 'somabrain' })"
     class="soma-status">
  <span class="soma-status__dot" :class="'soma-status__dot--' + status.health"></span>
  <span class="soma-status__label" x-text="service"></span>
</div>
```

### Modal

```html
<div x-data="modal({ size: 'md' })" x-show="isOpen" class="soma-modal">
  <div class="soma-modal__content">
    <h2 class="soma-modal__title">Modal Title</h2>
    <div class="soma-modal__body">Content here</div>
  </div>
</div>
```

### Toast

```html
<div x-data="toastContainer" class="soma-toast-container">
  <!-- Toasts render automatically -->
</div>

<!-- Trigger toast -->
<button @click="$store.toast.show('Success!', 'success')">Show Toast</button>
```

## Alpine.js Stores

### Auth Store

```javascript
// Access role information
$store.auth.role        // 'admin' | 'operator' | 'viewer'
$store.auth.isAdmin     // boolean
$store.auth.isOperator  // boolean (includes admin)
$store.auth.hasPermission('edit')  // boolean
```

### Theme Store

```javascript
// Toggle theme
$store.theme.toggle()
$store.theme.setMode('dark')  // 'light' | 'dark' | 'system'
```

### Status Store

```javascript
// Access service health
$store.status.services.somabrain.health  // 'healthy' | 'degraded' | 'down'
$store.status.services.somabrain.latencyMs
```

## Role-Based Visibility

Use Alpine.js directives for role-based UI:

```html
<!-- Admin only -->
<button x-show="$store.auth.isAdmin">Delete</button>

<!-- Operator and above -->
<button x-show="$store.auth.isOperator">Edit</button>

<!-- All users -->
<button>View</button>
```

## Theming

Toggle between light and dark themes:

```html
<button @click="$store.theme.toggle()">
  <span x-show="$store.theme.mode === 'light'">🌙</span>
  <span x-show="$store.theme.mode === 'dark'">☀️</span>
</button>
```

## Accessibility

- WCAG 2.1 AA compliant
- Keyboard navigation support
- Screen reader compatible
- Focus indicators
- Reduced motion support
- High contrast mode support

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

MIT License - See LICENSE file for details.

## Documentation

- [Design Tokens Reference](docs/tokens.md)
- [Component API](docs/components.md)
- [Store Reference](docs/stores.md)
- [Accessibility Guide](docs/accessibility.md)

---

**SomaStack Platform Team** | Version 1.0.0 | December 2025
