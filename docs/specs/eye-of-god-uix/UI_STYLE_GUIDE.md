# SomaTech.dev — UI Style Guide

**Document ID:** ST-UI-STYLE-2025-12  
**Version:** 2.0  
**Status:** CANONICAL

---

## Branding

| Property | Value |
|----------|-------|
| **Company** | SomaTech.dev |
| **Product** | SomaAgent |
| **Email** | ai@somatech.dev |
| **GitHub** | github.com/somatechlat |

---

## Design Philosophy

**Minimal. Clean. Professional.**

Inspired by Crisply, Linear, and Vercel. White/light gray backgrounds, black/dark text, subtle borders, minimal color usage (accent colors only for status and actions).

---

## Icons

> [!CAUTION]
> **NO EMOJIS. EVER.**

Use **Google Material Symbols** (outlined, 20px, weight 400).

### Icon Library

```html
<!-- Add to index.html -->
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20,400,0,0" />
```

### Icon Usage

```css
.icon {
    font-family: 'Material Symbols Outlined';
    font-size: 20px;
    font-weight: 400;
    line-height: 1;
    color: inherit;
}
```

### Common Icons

| Purpose | Icon Name | Usage |
|---------|-----------|-------|
| Dashboard | `dashboard` | Nav, headers |
| Tenants | `apartment` | Tenant sections |
| Agents | `smart_toy` | Agent sections |
| Users | `person` | User management |
| Settings | `settings` | Settings screens |
| Billing | `payments` | Billing sections |
| Audit | `history` | Audit log |
| Models | `psychology` | AI models |
| Roles | `admin_panel_settings` | Permissions |
| Flags | `flag` | Feature flags |
| Keys | `vpn_key` | API keys |
| Search | `search` | Search inputs |
| Add | `add` | Create actions |
| Edit | `edit` | Edit actions |
| Delete | `delete` | Delete actions |
| Close | `close` | Close/dismiss |
| Menu | `menu` | Hamburger menu |
| Expand | `expand_more` | Dropdowns |
| Check | `check` | Success states |
| Warning | `warning` | Warning states |
| Error | `error` | Error states |
| Info | `info` | Info states |

### Social Login Icons

| Provider | Icon | Usage |
|----------|------|-------|
| Google | SVG (official) | Login buttons |
| GitHub | SVG (official) | Login buttons |
| Facebook | SVG (official) | Login buttons |

```html
<!-- Google SVG -->
<svg viewBox="0 0 24 24" width="20" height="20">
  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
</svg>

<!-- GitHub SVG -->
<svg viewBox="0 0 24 24" width="20" height="20">
  <path fill="currentColor" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.17 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.604-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.167 22 16.418 22 12c0-5.523-4.477-10-10-10z"/>
</svg>

<!-- Facebook SVG -->
<svg viewBox="0 0 24 24" width="20" height="20">
  <path fill="#1877F2" d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
</svg>
```

---

## Color Palette

## Color Palette

### Base Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--saas-bg-page` | `#f5f5f5` | Page background |
| `--saas-bg-card` | `#ffffff` | Cards, modals, panels |
| `--saas-bg-sidebar` | `#ffffff` | Sidebar background |
| `--saas-bg-hover` | `#fafafa` | Hover states |
| `--saas-bg-active` | `#f0f0f0` | Active/selected states |

### Text Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--saas-text-primary` | `#1a1a1a` | Primary text, headings |
| `--saas-text-secondary` | `#666666` | Secondary text, labels |
| `--saas-text-muted` | `#999999` | Muted text, placeholders |
| `--saas-text-inverse` | `#ffffff` | Text on dark backgrounds |

### Border Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--saas-border-light` | `#e0e0e0` | Default borders |
| `--saas-border-medium` | `#cccccc` | Active/hover borders |
| `--saas-border-dark` | `#1a1a1a` | Focus borders |

### Status Colors (Minimal Use)

| Token | Value | Usage |
|-------|-------|-------|
| `--saas-status-success` | `#22c55e` | Success, online, active |
| `--saas-status-warning` | `#f59e0b` | Warning, pending, medium risk |
| `--saas-status-danger` | `#ef4444` | Error, offline, high risk |
| `--saas-status-info` | `#3b82f6` | Information, links |

### Accent (Primary Action)

| Token | Value | Usage |
|-------|-------|-------|
| `--saas-accent` | `#1a1a1a` | Primary buttons |
| `--saas-accent-hover` | `#333333` | Primary button hover |

---

## Typography

### Font Family

```css
--saas-font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
--saas-font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', Monaco, monospace;
```

### Font Sizes

| Token | Value | Usage |
|-------|-------|-------|
| `--saas-text-xs` | `11px` | Badges, meta |
| `--saas-text-sm` | `13px` | Labels, secondary text |
| `--saas-text-base` | `14px` | Body text |
| `--saas-text-md` | `16px` | Large body |
| `--saas-text-lg` | `18px` | Small headings |
| `--saas-text-xl` | `22px` | Section headings |
| `--saas-text-2xl` | `28px` | Page titles |

### Font Weights

| Token | Value | Usage |
|-------|-------|-------|
| `--saas-font-normal` | `400` | Body text |
| `--saas-font-medium` | `500` | Labels, nav items |
| `--saas-font-semibold` | `600` | Headings, buttons |
| `--saas-font-bold` | `700` | Strong emphasis |

---

## Spacing

| Token | Value |
|-------|-------|
| `--saas-space-xs` | `4px` |
| `--saas-space-sm` | `8px` |
| `--saas-space-md` | `16px` |
| `--saas-space-lg` | `24px` |
| `--saas-space-xl` | `32px` |
| `--saas-space-2xl` | `48px` |

---

## Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--saas-radius-sm` | `4px` | Badges, small elements |
| `--saas-radius-md` | `8px` | Inputs, buttons, cards |
| `--saas-radius-lg` | `12px` | Modals, panels |
| `--saas-radius-full` | `9999px` | Pills, avatars |

---

## Shadows

| Token | Value | Usage |
|-------|-------|-------|
| `--saas-shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | Subtle elevation |
| `--saas-shadow-md` | `0 2px 8px rgba(0,0,0,0.06)` | Cards, dropdowns |
| `--saas-shadow-lg` | `0 8px 24px rgba(0,0,0,0.1)` | Modals |

---

## Component Patterns

### Buttons

```css
/* Primary Button */
.btn-primary {
    background: #1a1a1a;
    color: white;
    padding: 12px 16px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 14px;
    border: none;
}

/* Secondary Button */
.btn-secondary {
    background: white;
    color: #1a1a1a;
    padding: 12px 16px;
    border-radius: 8px;
    font-weight: 500;
    font-size: 14px;
    border: 1px solid #e0e0e0;
}

/* Ghost Button */
.btn-ghost {
    background: transparent;
    color: #666;
    padding: 8px 12px;
}
```

### Inputs

```css
.input {
    width: 100%;
    padding: 12px 14px;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    font-size: 14px;
    background: white;
}

.input:focus {
    outline: none;
    border-color: #1a1a1a;
}

.input::placeholder {
    color: #999;
}
```

### Cards

```css
.card {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
```

### Status Badges

```css
/* Risk: Low */
.badge-low { background: #dcfce7; color: #166534; }

/* Risk: Medium */
.badge-medium { background: #fef3c7; color: #92400e; }

/* Risk: High */
.badge-high { background: #fee2e2; color: #991b1b; }

/* Pending */
.badge-pending { background: #f3f4f6; color: #6b7280; }
```

### Sidebar

```css
.sidebar {
    width: 240px;
    background: white;
    border-right: 1px solid #e0e0e0;
    padding: 16px 0;
}

.sidebar-item {
    padding: 8px 16px;
    font-size: 14px;
    color: #666;
    display: flex;
    align-items: center;
    gap: 10px;
}

.sidebar-item:hover {
    background: #fafafa;
}

.sidebar-item.active {
    background: #f0f0f0;
    color: #1a1a1a;
    font-weight: 500;
}

.sidebar-section {
    font-size: 11px;
    text-transform: uppercase;
    color: #999;
    padding: 16px 16px 8px;
    font-weight: 600;
}
```

---

## Reference Screenshots

````carousel
![Crisply Settings - Minimal sidebar with sections, clean form layout](/Users/macbookpro201916i964gb1tb/.gemini/antigravity/brain/140e7b31-8926-48d0-8168-33c0e621e136/uploaded_image_0_1766461139720.png)
<!-- slide -->
![Document + Chat split view - Clean minimal AI chat interface](/Users/macbookpro201916i964gb1tb/.gemini/antigravity/brain/140e7b31-8926-48d0-8168-33c0e621e136/uploaded_image_1_1766461139720.png)
<!-- slide -->
![Eye of God current UI - Dark theme chat with sidebar](/Users/macbookpro201916i964gb1tb/.gemini/antigravity/brain/140e7b31-8926-48d0-8168-33c0e621e136/uploaded_image_2_1766461139720.png)
<!-- slide -->
![Admin Console - Status badges, forms, clean layout](/Users/macbookpro201916i964gb1tb/.gemini/antigravity/brain/140e7b31-8926-48d0-8168-33c0e621e136/uploaded_image_3_1766461139720.png)
<!-- slide -->
![Chat Input - Minimal floating input with tool buttons](/Users/macbookpro201916i964gb1tb/.gemini/antigravity/brain/140e7b31-8926-48d0-8168-33c0e621e136/uploaded_image_4_1766461139720.png)
````

---

## Key Design Rules

1. **White/Light Gray backgrounds only** - No dark mode by default
2. **Black (#1a1a1a) for primary actions** - Buttons, icons
3. **Subtle borders (#e0e0e0)** - 1px solid, not heavy
4. **Minimal color** - Only use status colors where needed
5. **8px border radius** - Consistent rounded corners
6. **14px base font size** - Clean, readable
7. **Generous whitespace** - Don't crowd elements
8. **Icons: stroke style, 20px** - Not filled, consistent size

---

## Additional Design Patterns (Extended)

### Stat Cards with Trend Badges

```
┌─────────────────────────────────┐
│ Total Campaign Revenue          │
│                                 │
│ $482,500        [↗ +8.2%]      │
│                                 │
│ ▁▂▃▄▅▆▇ Mini sparkline         │
└─────────────────────────────────┘
```

**CSS Pattern:**
```css
.stat-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 24px;
    border: 1px solid #e0e0e0;
}

.stat-value {
    font-size: 36px;
    font-weight: 700;
    color: #1a1a1a;
}

.trend-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border-radius: 9999px;
    font-size: 12px;
    font-weight: 600;
}

.trend-badge.positive {
    background: #dcfce7;
    color: #16a34a;
}

.trend-badge.negative {
    background: #fee2e2;
    color: #dc2626;
}
```

### Semi-Circular Progress (Arc Gauge)

For key insights and completion metrics.

```
        ╭────────╮
      ╱    +12%    ╲
     │              │
      ╲            ╱
        ─────────
```

**CSS Pattern:**
```css
.arc-gauge {
    position: relative;
    width: 120px;
    height: 60px;
    overflow: hidden;
}

.arc-gauge::before {
    content: '';
    position: absolute;
    width: 120px;
    height: 120px;
    border-radius: 50%;
    border: 4px solid #e0e0e0;
    border-bottom-color: transparent;
    border-left-color: transparent;
    transform: rotate(-45deg);
}

.arc-gauge.filled::after {
    content: '';
    position: absolute;
    width: 120px;
    height: 120px;
    border-radius: 50%;
    border: 4px solid #1a1a1a;
    border-bottom-color: transparent;
    border-left-color: transparent;
    transform: rotate(-45deg);
    clip-path: inset(0 0 50% 0);
}
```

### Workflow/Journey Nodes

Connected nodes for processes and customer journeys.

```
   ┌─────────┐         ┌─────────┐
   │  Task   │─────────│  Task   │
   │    A    │         │    B    │
   └─────────┘         └─────────┘
        │                   │
        └───────┬───────────┘
                │
           ┌─────────┐
           │  Task   │
           │    C    │
           └─────────┘
```

**CSS Pattern:**
```css
.workflow-node {
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 16px;
    position: relative;
    min-width: 140px;
}

.workflow-node.active {
    border-color: #1a1a1a;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.workflow-connector {
    position: absolute;
    background: #e0e0e0;
    height: 2px;
}

.workflow-connector.vertical {
    width: 2px;
    height: 32px;
}
```

### Circle Avatar Group

Stacked avatars for team members or assignees.

```css
.avatar-group {
    display: flex;
}

.avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: 2px solid #ffffff;
    margin-left: -8px;
    background: #f0f0f0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 600;
    color: #666;
}

.avatar:first-child {
    margin-left: 0;
}

.avatar.more {
    background: #1a1a1a;
    color: #ffffff;
}
```

### Insight Cards (Key Highlights)

Cards for AI insights with chart icons.

```css
.insight-card {
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 16px;
    padding: 20px;
    position: relative;
}

.insight-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #1a1a1a, #666666);
    border-radius: 16px 16px 0 0;
}

.insight-text {
    font-size: 14px;
    color: #666666;
    line-height: 1.5;
}

.insight-value {
    font-size: 24px;
    font-weight: 700;
    color: #1a1a1a;
    margin-top: 8px;
}
```

### Mini Sparkline Charts

Inline trend visualization.

```css
.sparkline {
    display: flex;
    align-items: flex-end;
    gap: 2px;
    height: 24px;
}

.sparkline-bar {
    width: 4px;
    background: #e0e0e0;
    border-radius: 2px;
    transition: background 0.2s ease;
}

.sparkline-bar.active {
    background: #1a1a1a;
}
```

---

## Reference Screenshots (Extended)

````carousel
![Crisply Settings - Minimal sidebar with sections, clean form layout](/Users/macbookpro201916i964gb1tb/.gemini/antigravity/brain/140e7b31-8926-48d0-8168-33c0e621136/uploaded_image_0_1766461139720.png)
<!-- slide -->
![Document + Chat split view - Clean minimal AI chat interface](/Users/macbookpro201916i964gb1tb/.gemini/antigravity/brain/140e7b31-8926-48d0-8168-33c0e621136/uploaded_image_1_1766461139720.png)
<!-- slide -->
![LeadPilot Analytics - Large stat cards, trend badges, arc gauges](/Users/macbookpro201916i964gb1tb/.gemini/antigravity/brain/140e7b31-8926-48d0-8168-33c0e621136/uploaded_image_0_1766463302937.png)
<!-- slide -->
![StratusCRM Journeys - Workflow nodes, avatar groups, connected tasks](/Users/macbookpro201916i964gb1tb/.gemini/antigravity/brain/140e7b31-8926-48d0-8168-33c0e621136/uploaded_image_1_1766463302937.png)
````

---

## Summary: Design Language

| Element | Pattern | Token |
|---------|---------|-------|
| Background | White/Light Gray | `--saas-bg-page: #f5f5f5` |
| Cards | White + subtle border | `--saas-bg-card: #ffffff` |
| Primary Text | Near-black | `--saas-text-primary: #1a1a1a` |
| Buttons | Black fill | `--saas-accent: #1a1a1a` |
| Trends Up | Green badge | `--saas-status-success` |
| Trends Down | Red badge | `--saas-status-danger` |
| Avatars | Circular, 32-48px | `border-radius: 50%` |
| Nodes | Rounded rect, connected | `border-radius: 12px` |
| Progress | Semi-arc gauge | `SVG or border technique` |
| Charts | Minimal bar/line | Black strokes on white |

---

## Dark Theme Design Patterns (Komma-Inspired)

For God Mode and advanced admin interfaces.

### Dark Theme Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--saas-dark-bg` | `#0f0f0f` | Page background |
| `--saas-dark-surface` | `#1a1a1a` | Cards, panels |
| `--saas-dark-elevated` | `#222222` | Elevated surfaces |
| `--saas-dark-border` | `rgba(255,255,255,0.08)` | Subtle borders |
| `--saas-dark-text` | `#e2e8f0` | Primary text |
| `--saas-dark-muted` | `#64748b` | Muted text |
| `--saas-dark-accent` | `#FF6B00` | Orange accent |

### Large Typography Headers

```css
.dark-hero-title {
    font-size: 64px;
    font-weight: 300;
    letter-spacing: -2px;
    color: rgba(255, 255, 255, 0.08);
    text-transform: uppercase;
    position: absolute;
    top: 0;
    left: 0;
    z-index: 0;
}

.page-title {
    font-size: 32px;
    font-weight: 400;
    color: #e2e8f0;
    position: relative;
    z-index: 1;
}
```

### Circular Progress Rings

For productivity and success metrics.

```css
.progress-ring {
    width: 48px;
    height: 48px;
    position: relative;
}

.progress-ring svg {
    transform: rotate(-90deg);
}

.progress-ring-bg {
    fill: none;
    stroke: rgba(255, 107, 0, 0.2);
    stroke-width: 4;
}

.progress-ring-fill {
    fill: none;
    stroke: #FF6B00;
    stroke-width: 4;
    stroke-linecap: round;
    stroke-dasharray: 126; /* 2πr where r=20 */
    stroke-dashoffset: calc(126 - (126 * var(--progress)) / 100);
    transition: stroke-dashoffset 0.5s ease;
}

.progress-value {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 600;
    color: #e2e8f0;
}
```

### Dark Glassmorphism Cards

```css
.dark-glass-card {
    background: rgba(26, 26, 26, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    padding: 24px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.dark-glass-card:hover {
    border-color: rgba(255, 107, 0, 0.3);
    box-shadow: 0 8px 32px rgba(255, 107, 0, 0.1);
}
```

### User Profile Card

```css
.user-card {
    background: linear-gradient(135deg, #FF6B00 0%, #FF8533 100%);
    border-radius: 20px;
    padding: 20px;
    color: white;
}

.user-card-inner {
    background: rgba(26, 26, 26, 0.9);
    border-radius: 12px;
    padding: 16px;
    margin-top: 60px; /* Space for avatar overlap */
}

.user-avatar-large {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    border: 4px solid #1a1a1a;
    position: absolute;
    top: -40px;
    left: 50%;
    transform: translateX(-50%);
}
```

### Orange Accent Buttons

```css
.btn-accent {
    background: #FF6B00;
    color: white;
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: 500;
    border: none;
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-accent:hover {
    background: #FF8533;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(255, 107, 0, 0.3);
}
```

### Task List (Dark)

```css
.task-list-dark {
    background: transparent;
}

.task-item-dark {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    transition: background 0.2s ease;
}

.task-item-dark:hover {
    background: rgba(255, 255, 255, 0.03);
}

.task-checkbox {
    width: 20px;
    height: 20px;
    border: 2px solid rgba(255, 255, 255, 0.2);
    border-radius: 50%;
    cursor: pointer;
}

.task-checkbox.completed {
    background: #FF6B00;
    border-color: #FF6B00;
}
```

---

## Reference Screenshots (Dark Theme)

````carousel
![StratusCRM Customer Journeys - Workflow nodes, avatar groups](/Users/macbookpro201916i964gb1tb/.gemini/antigravity/brain/140e7b31-8926-48d0-8168-33c0e621e136/uploaded_image_0_1766463484540.png)
<!-- slide -->
![Komma Tasks - Dark theme, orange accent, task list](/Users/macbookpro201916i964gb1tb/.gemini/antigravity/brain/140e7b31-8926-48d0-8168-33c0e621e136/uploaded_image_1_1766463484540.png)
<!-- slide -->
![Komma User Card - Circular progress, glassmorphism, orange gradient](/Users/macbookpro201916i964gb1tb/.gemini/antigravity/brain/140e7b31-8926-48d0-8168-33c0e621e136/uploaded_image_2_1766463484540.png)
````
