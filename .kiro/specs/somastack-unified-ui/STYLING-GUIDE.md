# SomaStack UI Styling Guide

## Reference Analysis

Based on the provided reference images, the design follows a **clean, minimal, professional SaaS dashboard** aesthetic.

---

## Color Palette

### Backgrounds
| Token | Value | Usage |
|-------|-------|-------|
| `--bg-page` | `#FFFFFF` | Main content area |
| `--bg-sidebar` | `#FAFAFA` | Sidebar background |
| `--bg-card` | `#FFFFFF` | Card backgrounds |
| `--bg-hover` | `#F5F5F5` | Hover states |
| `--bg-active` | `#F0F0F0` | Active/selected states |
| `--bg-input` | `#FFFFFF` | Form inputs |

### Text
| Token | Value | Usage |
|-------|-------|-------|
| `--text-primary` | `#111111` | Headings, primary text |
| `--text-secondary` | `#666666` | Secondary text, descriptions |
| `--text-muted` | `#999999` | Placeholder, hints |
| `--text-link` | `#111111` | Links (underline on hover) |

### Borders
| Token | Value | Usage |
|-------|-------|-------|
| `--border-default` | `#E5E5E5` | Card borders, dividers |
| `--border-input` | `#D4D4D4` | Input borders |
| `--border-focus` | `#111111` | Focus state |

### Status Colors
| Token | Value | Usage |
|-------|-------|-------|
| `--status-success` | `#22C55E` | Success, approved |
| `--status-success-bg` | `#F0FDF4` | Success background |
| `--status-warning` | `#F97316` | Warning, medium risk |
| `--status-warning-bg` | `#FFF7ED` | Warning background |
| `--status-error` | `#EF4444` | Error, rejected, high risk |
| `--status-error-bg` | `#FEF2F2` | Error background |
| `--status-info` | `#3B82F6` | Info, pending |
| `--status-info-bg` | `#EFF6FF` | Info background |

### Accent (Primary Action)
| Token | Value | Usage |
|-------|-------|-------|
| `--accent` | `#111111` | Primary buttons |
| `--accent-hover` | `#333333` | Primary button hover |
| `--accent-text` | `#FFFFFF` | Text on accent |

---

## Typography

### Font Family
```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```

### Font Sizes
| Token | Size | Line Height | Usage |
|-------|------|-------------|-------|
| `--text-xs` | 11px | 16px | Badges, timestamps |
| `--text-sm` | 13px | 20px | Secondary text, table cells |
| `--text-base` | 14px | 22px | Body text, inputs |
| `--text-lg` | 16px | 24px | Card titles |
| `--text-xl` | 20px | 28px | Section headings |
| `--text-2xl` | 28px | 36px | Page titles |
| `--text-3xl` | 36px | 44px | Large stats numbers |

### Font Weights
| Token | Weight | Usage |
|-------|--------|-------|
| `--font-normal` | 400 | Body text |
| `--font-medium` | 500 | Labels, nav items |
| `--font-semibold` | 600 | Headings, buttons |
| `--font-bold` | 700 | Stats numbers |

---

## Spacing

| Token | Value | Usage |
|-------|-------|-------|
| `--space-1` | 4px | Tight spacing |
| `--space-2` | 8px | Icon gaps |
| `--space-3` | 12px | Small padding |
| `--space-4` | 16px | Default padding |
| `--space-5` | 20px | Card padding |
| `--space-6` | 24px | Section gaps |
| `--space-8` | 32px | Large gaps |
| `--space-10` | 40px | Page margins |

---

## Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 4px | Small elements |
| `--radius-md` | 6px | Inputs, small cards |
| `--radius-lg` | 8px | Cards, modals |
| `--radius-xl` | 12px | Large cards |
| `--radius-full` | 9999px | Pills, avatars |

---

## Shadows

**Minimal shadows - rely on borders instead**

| Token | Value | Usage |
|-------|-------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.04)` | Subtle lift |
| `--shadow-md` | `0 2px 8px rgba(0,0,0,0.08)` | Dropdowns, popovers |
| `--shadow-lg` | `0 4px 16px rgba(0,0,0,0.12)` | Modals |

---

## Component Specifications

### Sidebar
- Width: 240px
- Background: `--bg-sidebar` (#FAFAFA)
- Border right: 1px solid `--border-default`
- Logo area: 64px height
- Nav items:
  - Padding: 10px 16px
  - Icon: 20px, color `--text-secondary`
  - Text: 14px, `--font-medium`
  - Active: background `--bg-active`, left border 2px `--accent`
  - Hover: background `--bg-hover`

### Top Navigation Tabs
- Container: pill-shaped background `#F5F5F5`, padding 4px, border-radius full
- Tab item:
  - Padding: 8px 16px
  - Font: 14px `--font-medium`
  - Inactive: transparent, `--text-secondary`
  - Active: white background, `--text-primary`, subtle shadow

### Stats Cards
- Background: white
- Border: 1px solid `--border-default`
- Border-radius: `--radius-lg`
- Padding: 20px 24px
- Layout:
  - Top row: Label (13px, `--text-secondary`) + Icon (right aligned, 20px, `--text-muted`)
  - Middle: Large number (28-36px, `--font-bold`, `--text-primary`)
  - Bottom: Trend text (12px, green/red for +/-)

### Data Tables
- No outer border on container
- Header:
  - Background: transparent or very subtle `#FAFAFA`
  - Text: 12px uppercase, `--font-semibold`, `--text-muted`
  - Padding: 12px 16px
- Rows:
  - Border-bottom: 1px solid `--border-default`
  - Padding: 16px
  - Hover: `--bg-hover`
- Last row: no border

### Status Badges
- Padding: 4px 10px
- Border-radius: full
- Font: 12px `--font-medium`
- Variants:
  - **Approved**: bg `#F5F5F5`, text `#666666`, border 1px `#E5E5E5`
  - **Pending**: bg `--status-info-bg`, text `--status-info`
  - **Rejected**: bg `--status-error`, text white
  - **Risk Low**: bg `#F5F5F5`, text `#666666`
  - **Risk Medium**: bg `--status-warning-bg`, text `--status-warning`
  - **Risk High**: bg `--status-error-bg`, text `--status-error`

### Form Inputs
- Height: 40px
- Padding: 0 12px
- Border: 1px solid `--border-input`
- Border-radius: `--radius-md`
- Font: 14px
- Focus: border `--border-focus`, no shadow or subtle shadow
- Placeholder: `--text-muted`

### Select Dropdowns
- Same as inputs
- Chevron icon on right
- Options dropdown: white bg, subtle shadow

### Toggle Switch
- Width: 44px, Height: 24px
- Off: bg `#E5E5E5`
- On: bg `--accent` (#111111)
- Knob: white, 20px circle

### Primary Button
- Background: `--accent` (#111111)
- Text: white, 14px `--font-semibold`
- Padding: 12px 24px
- Border-radius: `--radius-md`
- Hover: `--accent-hover`
- Full width in forms

### Secondary Button
- Background: white
- Border: 1px solid `--border-default`
- Text: `--text-primary`
- Hover: `--bg-hover`

### Ghost Button
- Background: transparent
- Text: `--text-secondary`
- Hover: `--bg-hover`

### Cards
- Background: white
- Border: 1px solid `--border-default`
- Border-radius: `--radius-lg`
- No shadow (or very subtle)
- Header: border-bottom 1px, padding 16px 20px
- Body: padding 20px

### Tags/Pills
- Padding: 4px 8px
- Border-radius: `--radius-sm` (4px)
- Font: 12px
- Background: `#F5F5F5`
- Text: `--text-secondary`

### Notifications Panel
- Cards with left color indicator (green dot for success, red for error)
- Timestamp on right
- Clean typography hierarchy

---

## Layout Structure

### Page Layout
```
┌─────────────────────────────────────────────────────────┐
│ [Logo]              [Top Nav Tabs]        [Icons] [User]│
├──────────┬──────────────────────────────────────────────┤
│          │                                              │
│ Sidebar  │  Main Content Area                           │
│          │                                              │
│ - Home   │  ┌─────────────────────────────────────────┐ │
│ - Items  │  │ Page Title                              │ │
│ - etc    │  ├─────────────────────────────────────────┤ │
│          │  │ Stats Cards Row                         │ │
│          │  ├─────────────────────────────────────────┤ │
│          │  │ Main Content (Tables, Forms, etc)       │ │
│          │  └─────────────────────────────────────────┘ │
│          │                                              │
└──────────┴──────────────────────────────────────────────┘
```

### Two-Column Layout (List + Form)
```
┌─────────────────────────────────────────────────────────┐
│ Main Content                                            │
│ ┌───────────────────────────┐ ┌───────────────────────┐ │
│ │ List Panel                │ │ Form Panel            │ │
│ │ - Search bar              │ │ - Title               │ │
│ │ - List items              │ │ - Form fields         │ │
│ │   - Item 1                │ │ - Submit button       │ │
│ │   - Item 2                │ │                       │ │
│ │   - Item 3                │ │                       │ │
│ └───────────────────────────┘ └───────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## Key Design Principles

1. **White Space** - Generous padding and margins, let content breathe
2. **Minimal Borders** - Use borders sparingly, prefer whitespace for separation
3. **No Heavy Shadows** - Flat design with subtle depth through borders
4. **Typography Hierarchy** - Use weight and size to create hierarchy, not color
5. **Consistent Spacing** - Use the spacing scale consistently
6. **Subtle Interactions** - Hover states are subtle, not dramatic
7. **Black Accent** - Primary actions use black (#111111), not blue
8. **Status Through Color** - Use color only for status indication

---

## Anti-Patterns (What NOT to do)

❌ Heavy drop shadows  
❌ Gradient backgrounds  
❌ Colorful sidebar  
❌ Blue primary buttons (use black)  
❌ Rounded corners > 12px on cards  
❌ Dense, cramped layouts  
❌ Multiple font families  
❌ Decorative icons  
❌ Glassmorphism effects  
❌ Dark mode as default  

---

## File Structure

```
webui/
├── index.html              # Main HTML with Alpine.js
├── design-system/
│   └── somastack-ui.css    # All styles (tokens + components)
└── js/
    └── app.js              # Alpine.js components (optional)
```

