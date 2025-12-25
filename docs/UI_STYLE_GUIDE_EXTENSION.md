# SomaAgent UI/UX Style Guide Extension

## Design Reference Analysis

Based on industry-leading SaaS UI references (Crisply, Google Gemini, Graceview, modern e-commerce):

---

## 1. Core Design Philosophy

### Minimalism & Clarity
- **White space is a feature** - generous padding, uncluttered layouts
- **Content-first design** - UI disappears, content shines
- **Progressive disclosure** - show only what's needed, dropdowns for more

### Color Palette

| Token | Purpose | Value |
|-------|---------|-------|
| `--saas-bg-page` | Page background | `#f5f5f5` (soft warm gray) |
| `--saas-bg-card` | Card surfaces | `#ffffff` |
| `--saas-bg-hover` | Hover states | `#fafafa` |
| `--saas-bg-active` | Active/selected | `#f0f0f0` |
| `--saas-text-primary` | Headings, body | `#1a1a1a` |
| `--saas-text-secondary` | Labels | `#666666` |
| `--saas-text-muted` | Hints, timestamps | `#999999` |
| `--saas-border-light` | Card borders | `#e0e0e0` |
| `--saas-accent` | Primary action | `#1a1a1a` (black) |
| `--saas-status-success` | Healthy/success | `#22c55e` |
| `--saas-status-warning` | Degraded/warning | `#f59e0b` |
| `--saas-status-danger` | Down/error | `#ef4444` |

---

## 2. Typography

### Font Stack
```css
--saas-font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
--saas-font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', Monaco, monospace;
```

### Type Scale
| Name | Size | Weight | Use Case |
|------|------|--------|----------|
| `h1` | 22px | 600 | Page titles |
| `h2` | 15px | 600 | Section titles |
| `h3` | 14px | 600 | Card titles |
| `body` | 14px | 400 | Body text |
| `small` | 13px | 400 | Nav items |
| `caption` | 11px | 600 | Labels, timestamps |
| `micro` | 10px | 600 | Badges, uppercase labels |

---

## 3. Spacing System

Based on 4px grid:
- `xs`: 4px
- `sm`: 8px
- `md`: 16px
- `lg`: 24px
- `xl`: 32px
- `2xl`: 48px

**Card padding**: 20-24px
**Section gaps**: 24-32px
**Component gaps**: 8-12px

---

## 4. Components

### Sidebar (Crisply Pattern)
- **Width**: 260px
- **Background**: `--saas-bg-card` (white)
- **Border-right**: 1px solid `--saas-border-light`
- **Logo section**: 24px padding, separated by border
- **Nav items**: 11px 14px padding, 8px border-radius
- **Section titles**: 10px uppercase, letter-spacing 1px, color muted

### Header Bar
- **Height**: ~60px
- **Background**: `--saas-bg-card`
- **Border-bottom**: 1px solid `--saas-border-light`
- **Title**: 22px semibold
- **Subtitle**: 13px muted color
- **Actions**: right-aligned, 12px gap

### Metric Cards
- **Background**: white
- **Border**: 1px solid `--saas-border-light`
- **Border-radius**: 12px
- **Padding**: 24px
- **Hover**: translateY(-2px), box-shadow 0 4px 12px rgba(0,0,0,0.04)
- **Featured card**: black gradient `linear-gradient(135deg, #1a1a1a, #333)`

### Buttons

#### Primary Button
```css
.btn-primary {
  background: #1a1a1a;
  color: white;
  border: 1px solid #1a1a1a;
  padding: 10px 18px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
}
.btn-primary:hover {
  background: #333;
}
```

#### Secondary Button
```css
.btn-secondary {
  background: white;
  color: #1a1a1a;
  border: 1px solid #e0e0e0;
  padding: 10px 18px;
  border-radius: 8px;
}
.btn-secondary:hover {
  background: #fafafa;
}
```

#### Pill Buttons (Gemini-style)
```css
.pill-btn {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 9999px; /* full round */
  padding: 10px 16px;
  font-size: 14px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
```

### Dropdown Menus (Gemini Pattern)
- **Background**: white
- **Border-radius**: 12px
- **Box-shadow**: 0 8px 24px rgba(0,0,0,0.12)
- **Padding**: 8px
- **Item padding**: 12px 16px
- **Item hover**: background `#f5f5f5`
- **Icons**: 20px, muted color

### Form Inputs (E-commerce Pattern)
```css
.input {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 14px;
  background: white;
}
.input:focus {
  border-color: #1a1a1a;
  outline: none;
}
```

### Tables
- **Header**: 11px uppercase, muted color, letter-spacing 0.5px
- **Row padding**: 14px 20px
- **Row border**: 1px solid `--saas-border-light`
- **Row hover**: background `--saas-bg-hover`
- **No last-child border-bottom**

### Status Badges
```css
.badge-healthy {
  background: rgba(34, 197, 94, 0.15);
  color: #16a34a;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}
```

### Toggle Switches
- **Track**: 40px × 20px, border-radius full
- **Knob**: 16px circle
- **Off state**: #e5e7eb track
- **On state**: #1a1a1a track (or accent color)

---

## 5. Layout Patterns

### Sidebar + Main Content
```
┌─────────────┬──────────────────────────────────────┐
│  Sidebar    │  Header                              │
│  (260px)    ├──────────────────────────────────────┤
│             │  Tabs (optional)                     │
│  Logo       ├──────────────────────────────────────┤
│  Nav        │  Content (scrollable)                │
│  Sections   │                                      │
│             │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐│
│  User       │  │Card  │ │Card  │ │Card  │ │Card  ││
│             │  └──────┘ └──────┘ └──────┘ └──────┘│
└─────────────┴──────────────────────────────────────┘
```

### Settings Panel (Crisply Pattern)
```
┌──────────┬────────────────────────────────────────────────┐
│ Sidebar  │ Content Header                                 │
│          ├──────────────┬──────────────────────────────────┤
│ SECTION  │ Settings Nav │ Form Content                     │
│ • Item   │              │                                  │
│ • Item   │ Nav Item 1   │ Section Title                    │
│          │ Nav Item 2 ← │ ┌──────────┐ ┌──────────┐       │
│          │ Nav Item 3   │ │ Input    │ │ Input    │       │
│          │              │ └──────────┘ └──────────┘       │
└──────────┴──────────────┴──────────────────────────────────┘
```

### Modal Dialog (E-commerce Pattern)
```
┌────────────────────────────────────────────╳─┐
│ Modal Title                                   │
├───────────────────────────────────────────────┤
│                                               │
│ Form fields with clear labels                 │
│                                               │
│ ┌─────────────────────────────────────────┐   │
│ │ Input field                             │   │
│ └─────────────────────────────────────────┘   │
│                                               │
├───────────────────────────────────────────────┤
│                      [Cancel]  [Primary CTA]  │
└───────────────────────────────────────────────┘
```

---

## 6. Transitions & Animations

### Standard Easing
```css
--transition-fast: 100ms ease;
--transition-normal: 200ms ease;
--transition-slow: 300ms ease;
```

### Hover Effects
- Cards: `translateY(-2px)` + shadow increase
- Buttons: slight opacity or background change
- Icons: color change only

### Loading States
- Spinner: Simple border-based CSS spinner
- Skeleton: Pulse animation on gray placeholder

---

## 7. Icons

### Primary: Google Material Symbols
- Style: Outlined
- Size: 18-20px for nav, 16px for buttons
- Weight: 400 (default)
- Color: Inherit or `--saas-text-secondary`

```html
<span class="material-symbols-outlined">visibility</span>
<span class="material-symbols-outlined">apartment</span>
<span class="material-symbols-outlined">dns</span>
<span class="material-symbols-outlined">speed</span>
```

### Icon + Text Patterns
- Nav items: 12px gap, icon first
- Buttons: 8px gap, icon first
- Badges: 6px gap

---

## 8. Responsive Breakpoints

| Name | Width | Adaptation |
|------|-------|------------|
| Desktop | 1400px+ | 4-column grid |
| Laptop | 1200px | 3-column grid |
| Tablet | 768px | 2-column, sidebar collapses |
| Mobile | 480px | 1-column, bottom nav |

---

## 9. Reference Images

The following reference images were used to derive this style guide:

![Gemini Chat Dropdown](/Users/macbookpro201916i964gb1tb/.gemini/antigravity/brain/1fcf5f85-5d07-4a6a-b266-d0a4f08c29e7/uploaded_image_0_1766678009368.png)

![Crisply Settings Page](/Users/macbookpro201916i964gb1tb/.gemini/antigravity/brain/1fcf5f85-5d07-4a6a-b266-d0a4f08c29e7/uploaded_image_1_1766678009368.png)

![Gemini Chat Input](/Users/macbookpro201916i964gb1tb/.gemini/antigravity/brain/1fcf5f85-5d07-4a6a-b266-d0a4f08c29e7/uploaded_image_2_1766678009368.png)

![Graceview Document Chat](/Users/macbookpro201916i964gb1tb/.gemini/antigravity/brain/1fcf5f85-5d07-4a6a-b266-d0a4f08c29e7/uploaded_image_3_1766678009368.png)

![E-commerce Modal](/Users/macbookpro201916i964gb1tb/.gemini/antigravity/brain/1fcf5f85-5d07-4a6a-b266-d0a4f08c29e7/uploaded_image_4_1766678009368.png)

---

*Style guide extracted from reference designs on December 25, 2025*
