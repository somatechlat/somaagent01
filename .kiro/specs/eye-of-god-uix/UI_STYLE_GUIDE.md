# SomaAgent SaaS — UI Style Guide

**Document ID:** SA01-UI-STYLE-2025-12  
**Version:** 1.0  
**Status:** CANONICAL

---

## Design Philosophy

**Minimal. Clean. Professional.**

Inspired by Crisply, Linear, and Vercel. White/light gray backgrounds, black/dark text, subtle borders, minimal color usage (accent colors only for status and actions).

---

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
