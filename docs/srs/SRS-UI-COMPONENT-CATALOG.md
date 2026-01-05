# SRS: UI Component Catalog (Atomic Library)

**Document ID:** SA01-SRS-UI-CATALOG-2026-01
**Status:** 🔴 DRAFT
**Architecture:** Visual LIT 3 (Shadow DOM + `tokens.css`)
**Authors:** 10-Persona Collective

> **PURPOSE:** This document defines the **Atomic Building Blocks** of the SaaS Admin Interface. It explains **WHAT** exists, **WHY** it exists, and **HOW** to use it. All operational screens must be assembled from these components.

---

## 1. Governance
- **Base Class:** All components extend `LitElement`.
- **Styling:** STRICT adherence to `tokens.css` (CSS Variables).
- **Encapsulation:** Shadow DOM `mode: 'open'`.
- **Registry:** All components are registered in `webui/src/components/index.ts`.

---

## 2. Atoms (Primitives)
*Indivisible UI elements. The base styling integration points.*

### 2.1 `saas-button`
- **Why:** Standardizes click targets, loading states, and focus capability.
- **Variants:**
    - `primary` (Black/Accent) - Main actions.
    - `secondary` (Gray) - Cancel/Back.
    - `outline` (Border) - Low priority.
    - `danger` (Red) - Destructive.
    - `ghost` (Transparent) - Icon-only buttons.
- **Props:** `variant`, `size`, `loading`, `disabled`.
- **Usage:**
  ```html
  <saas-button variant="primary" ?loading=${this.saving} @click=${this.save}>
    Save Changes
  </saas-button>
  ```

### 2.2 `saas-input`
- **Why:** Enforces accessibility (labels, ARIA) and validation visuals globally.
- **Features:** Floating labels, error message slot, helper text, icon prefix.
- **Usage:**
  ```html
  <saas-input label="Email Address" type="email" error="Invalid format"></saas-input>
  ```

### 2.3 `saas-badge`
- **Why:** Provides semantic status indicators for grids and headers.
- **Variants:** `success` (Green), `warning` (Orange), `danger` (Red), `info` (Blue), `neutral` (Gray).
- **Usage:**
  ```html
  <saas-badge status="success">Active</saas-badge>
  ```

### 2.4 `saas-toggle`
- **Why:** Standard "Switch" control for boolean settings (Feature Flags).
- **Style:** iOS-style sliding pill.
- **Usage:**
  ```html
  <saas-toggle label="Enable Magic Auth" .checked=${true}></saas-toggle>
  ```

---

## 3. Molecules (Composites)
*Functional groups of atoms.*

### 3.1 `saas-toast`
- **Why:** Non-blocking feedback for async actions.
- **Behavior:** Auto-dismiss after 3s. Stackable.
- **Usage:** Dispatched via global event `show-toast`.

### 3.2 `saas-search-input`
- **Why:** Standardized search experience with debounce and clear functionality.
- **Composition:** `saas-input` + Search Icon + Clear Button.
- **Event:** `search` (debounced).

### 3.3 `saas-stats-card`
- **Why:** Dashboard KPI display.
- **Visuals:** Glassmorphism background.
- **Slots:** Icon, Title, Value, Trend.
- **Usage:**
  ```html
  <saas-stats-card title="MRR" value="$50,200" trend="+12%" trend-dir="up"></saas-stats-card>
  ```

---

## 4. Organisms (Complex Structures)
*Complete operational sections.*

### 4.1 `saas-wizard`
- **Why:** Multi-step flows (System Config, Tenant Creation) need state management.
- **Features:** Progress bar, step validation, "Next/Back" navigation.
- **Location:** Used in `/platform/setup/config`.

### 4.2 `saas-data-table`
- **Why:** The workhorse of the admin panel. Handles millions of rows.
- **Features:** Server-side pagination, Column Sorting, Row Selection, Action Menu.
- **Usage:**
  ```html
  <saas-data-table 
    .columns=${this.columns} 
    .data=${this.tenants} 
    @page-change=${this.loadPage}
  ></saas-data-table>
  ```

### 4.3 `saas-shell`
- **Why:** The "App" container. Enforces the layout structure.
- **Features:** Collapsible Sidebar, Sticky Header, Main Content Slot.
- **Visuals:** Grid layout.

---

## 5. Templates (Views)
*How components fit into Routes.*

1.  **Dashboard Layout:** `saas-shell` > `saas-stats-card` + `saas-data-table`
2.  **Form Layout:** `saas-shell` > `saas-card` > `saas-wizard`
3.  **Detail Layout:** `saas-shell` > `saas-header` (with tabs) > Content

---

**Execution:**
This catalog is the **Bill of Materials** for Phase 1. We build these first.
