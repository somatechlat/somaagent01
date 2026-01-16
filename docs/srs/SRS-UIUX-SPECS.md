# SRS: Complete UI/UX Screen Specifications

**Document ID:** SA01-SRS-UIUX-SPECS-2025-12
**Purpose:** Detailed UI/UX specification for every screen
**Status:** CANONICAL REFERENCE FOR IMPLEMENTATION

---

## 1. Design System Reference

### 1.1 Canonical Token Source

> **⚠️ ALWAYS USE:** [tokens.css](file:///Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/webui/src/styles/tokens.css)

```css
/* Key Light Theme Tokens */
--saas-bg-page: #f5f5f5;
--saas-bg-card: #ffffff;
--saas-text-primary: #1a1a1a;
--saas-text-secondary: #666666;
--saas-accent: #1a1a1a;
--saas-border-light: #e0e0e0;

/* Status Colors (Universal) */
--saas-status-success: #22c55e;
--saas-status-warning: #f59e0b;
--saas-status-danger: #ef4444;
--saas-status-info: #3b82f6;

/* Spacing */
--saas-space-xs: 4px;
--saas-space-sm: 8px;
--saas-space-md: 16px;
--saas-space-lg: 24px;
```

### 1.2 Common Patterns

| Pattern | Usage |
|---------|-------|
| Card | Container for content sections |
| Data Table | Paginated lists |
| Modal | Edit forms, confirmations |
| Toast | Success/error notifications |
| Loading Skeleton | Loading states |

---

## 2. Platform Admin Screens

### 2.1 Infrastructure Dashboard

**Route:** `/platform/infrastructure`

#### Wireframe
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Platform Admin > Infrastructure                            🔄 Refresh     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SYSTEM STATUS: 🟢 All Systems Operational     Last check: 30 seconds ago  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  CORE SERVICES                                                      │   │
│  ├──────────────┬──────────────┬──────────────┬────────────────────────┤   │
│  │              │              │              │                        │   │
│  │  PostgreSQL  │    Redis     │   Temporal   │      Qdrant            │   │
│  │  🟢 45ms     │  🟢 2ms      │  🟢 5 active │    🟢 1.2M vectors     │   │
│  │  [Details]   │  [Details]   │  [Details]   │    [Details]           │   │
│  │              │              │              │                        │   │
│  └──────────────┴──────────────┴──────────────┴────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  EXTERNAL SERVICES                                                  │   │
│  ├──────────────┬──────────────┬──────────────┬────────────────────────┤   │
│  │              │              │              │                        │   │
│  │  Keycloak    │    Lago      │  SomaBrain   │      Voice             │   │
│  │  🟢 3 realms │  🟢 $12K MRR │  🟡 Degraded │    🟢 STT+TTS OK       │   │
│  │  [Details]   │  [Details]   │  [Details]   │    [Details]           │   │
│  │              │              │              │                        │   │
│  └──────────────┴──────────────┴──────────────┴────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  INFRASTRUCTURE                                                     │   │
│  ├──────────────┬──────────────┬──────────────┬────────────────────────┤   │
│  │              │              │              │                        │   │
│  │  MCP Servers │   Storage    │    Email     │    Rate Limits         │   │
│  │  🟢 12 OK    │  🟢 S3 OK    │  🟢 SMTP OK  │    🟢 Normal           │   │
│  │  [Manage]    │  [Manage]    │  [Manage]    │    [Configure]         │   │
│  │              │              │              │                        │   │
│  └──────────────┴──────────────┴──────────────┴────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Data Requirements

| Field | Source | Type | Update |
|-------|--------|------|--------|
| `services[]` | API | Array | Poll 30s |
| `services[].name` | API | String | - |
| `services[].status` | API | Enum | healthy/degraded/down |
| `services[].latency_ms` | API | Number | - |
| `services[].metric` | API | String | Service-specific |
| `last_check` | Local | Timestamp | On refresh |

#### Interactions

| Action | Trigger | Result |
|--------|---------|--------|
| Click service card | Click | Navigate to service detail |
| Click Refresh | Click | Re-fetch all health data |
| Auto-refresh | Timer | Poll every 30 seconds |

#### Loading State

```
┌───────────────────────────────────────┐
│  ▓▓▓▓▓▓▓▓░░░░░░░░░░  Loading...      │
│  ┌────────────────┐  ┌────────────────┐
│  │  ░░░░░░░░░░░░  │  │  ░░░░░░░░░░░░  │
│  │  ░░░░░░░░░░░░  │  │  ░░░░░░░░░░░░  │
│  └────────────────┘  └────────────────┘
└───────────────────────────────────────┘
```

#### Error State

```
┌──────────────────────────────────────────┐
│  ⚠️ Unable to fetch service health       │
│                                          │
│  [Retry]                                 │
└──────────────────────────────────────────┘
```

---

### 2.2 Rate Limit Editor

**Route:** `/platform/infrastructure/redis/ratelimits`

#### Wireframe
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Infrastructure > Redis > Rate Limits                       [+ Add Limit]  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Tabs: [Global Limits] [Tier Overrides] [Audit Trail]                       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  KEY            LIMIT      WINDOW     POLICY    USAGE    ACTIONS   │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  api_calls      1,000      1 hour     HARD      45%      [✏️][🗑️]  │   │
│  │  llm_tokens     100,000    24 hours   SOFT      23%      [✏️][🗑️]  │   │
│  │  voice_minutes  60         24 hours   SOFT      78%      [✏️][🗑️]  │   │
│  │  file_uploads   50         1 hour     HARD      12%      [✏️][🗑️]  │   │
│  │  memory_queries 500        1 hour     SOFT      34%      [✏️][🗑️]  │   │
│  │  websocket_conn 100        -          HARD      8%       [✏️][🗑️]  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Showing 6 of 6 rate limits                                 [< 1 2 3 >]   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Edit Modal
```
┌─────────────────────────────────────────────────────────────┐
│  Edit Rate Limit: api_calls                            [X] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Key:           api_calls (read-only)                       │
│                                                             │
│  Limit:         [1000        ] requests                     │
│                                                             │
│  Window:        [1 hour      ▼]                             │
│                                                             │
│  Enforcement:   ○ HARD - Block when exceeded                │
│                 ● SOFT - Warn but allow                     │
│                 ○ NONE - No enforcement                     │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  TIER OVERRIDES                                       │ │
│  ├───────────────────────────────────────────────────────┤ │
│  │  Free:       [100     ]                               │ │
│  │  Starter:    [1000    ]                               │ │
│  │  Team:       [10000   ]                               │ │
│  │  Enterprise: [999999  ] (unlimited)                   │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│                              [Cancel]  [Save Changes]       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Form Validation

| Field | Rule | Error Message |
|-------|------|---------------|
| `limit` | Required, > 0 | "Limit must be a positive number" |
| `window_seconds` | Required, > 0 | "Window is required" |
| `tier_overrides.*` | Optional, >= 0 | "Override must be non-negative" |

#### Data Requirements

| Field | Source | Type |
|-------|--------|------|
| `ratelimits[]` | API | Array |
| `ratelimits[].key` | API | String |
| `ratelimits[].limit` | API | Number |
| `ratelimits[].window_seconds` | API | Number |
| `ratelimits[].policy` | API | Enum |
| `ratelimits[].tier_overrides` | API | Object |
| `current_usage[]` | API | Array (percentage) |

---

### 2.3 Platform Metrics Dashboard

**Route:** `/platform/metrics`

#### Wireframe
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Platform Admin > Metrics                          Period: [Last 24h ▼]    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌────────────┐│
│  │  API REQUESTS   │ │   LLM CALLS     │ │  TOOL EXECS     │ │  ERRORS    ││
│  │  1.2M           │ │   456K          │ │   89K           │ │  0.02%     ││
│  │  +12% ▲         │ │   +5% ▲         │ │   -3% ▼         │ │  -0.01% ▼  ││
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ └────────────┘│
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LATENCY DISTRIBUTION                                               │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  [============================================]  CHART AREA         │   │
│  │                                                                     │   │
│  │  ── p50   ── p95   ── p99                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌───────────────────────────────┐ ┌───────────────────────────────────┐   │
│  │  TOKEN USAGE                  │ │  CIRCUIT BREAKERS                 │   │
│  ├───────────────────────────────┤ ├───────────────────────────────────┤   │
│  │  Input:  45.2M   ($2,890)     │ │  somabrain_memory   🟢 CLOSED     │   │
│  │  Output: 12.8M   ($1,245)     │ │  openai_llm         🟢 CLOSED     │   │
│  │  Total:  58.0M   ($4,135)     │ │  qdrant_vectors     🟢 CLOSED     │   │
│  └───────────────────────────────┘ └───────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  SLA COMPLIANCE                                                     │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  METRIC              TARGET    ACTUAL    STATUS                     │   │
│  │  LLM Latency p99     < 5s      3.2s      ✅ PASS                    │   │
│  │  API Availability    99.9%     99.95%    ✅ PASS                    │   │
│  │  Memory Durability   99.99%    100%      ✅ PASS                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Data Requirements

| Field | Source | Type | Update |
|-------|--------|------|--------|
| `api_requests.total` | Prometheus | Number | Poll 60s |
| `api_requests.change` | Prometheus | Percentage | - |
| `llm_calls.total` | Prometheus | Number | - |
| `tool_executions.total` | Prometheus | Number | - |
| `error_rate` | Prometheus | Percentage | - |
| `latency.p50/p95/p99` | Prometheus | Number[] | - |
| `tokens.input/output` | Prometheus | Number | - |
| `circuit_breakers[]` | API | Array | - |
| `sla_compliance[]` | API | Array | - |

---

## 3. Tenant Admin Screens

### 3.1 Tenant Usage Dashboard

**Route:** `/admin/usage`

#### Wireframe
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Dashboard > Usage                         Billing Period: Dec 1-31, 2025  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  QUOTA USAGE                                                        │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  API Calls       ████████████░░░░░░░░  52,345 / 100,000   52%       │   │
│  │                                                                     │   │
│  │  LLM Tokens      █████████░░░░░░░░░░░ 523,456 / 1,000,000  52%      │   │
│  │                                                                     │   │
│  │  Images          ████████████████░░░░     312 / 500       62%       │   │
│  │                                                                     │   │
│  │  Voice Minutes   █████████░░░░░░░░░░░     245 / 500       49%       │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  USAGE BY AGENT                                                     │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  AGENT           API CALLS    TOKENS     IMAGES    VOICE    COST   │   │
│  │  Support-AI      23,456       245K       156       120m     $156    │   │
│  │  Sales-Bot       18,234       178K       98        80m      $124    │   │
│  │  Internal-AI     10,655       100K       58        45m      $89     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ESTIMATED COST THIS PERIOD                                         │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │   Base Subscription:    $99.00                                      │   │
│  │   LLM Usage:            $156.78                                     │   │
│  │   Image Generation:     $12.48                                      │   │
│  │   Voice Minutes:        $24.50                                      │   │
│  │   ────────────────────────────────                                  │   │
│  │   ESTIMATED TOTAL:      $292.76                                     │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Data Requirements

| Field | Source | Type |
|-------|--------|------|
| `quotas[]` | API | Array |
| `quotas[].name` | API | String |
| `quotas[].used` | API | Number |
| `quotas[].limit` | API | Number |
| `agent_usage[]` | API | Array |
| `cost_breakdown` | API | Object |
| `billing_period` | API | Object |

---

### 3.2 Agent Configuration

**Route:** `/settings/models`

#### Wireframe
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Agent Settings > Models                                      [Save]       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  CHAT MODEL (Primary)                                               │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  Provider:    [OpenAI          ▼]                                   │   │
│  │  Model:       [GPT-4o          ▼]                                   │   │
│  │                                                                     │   │
│  │  ℹ️ Vision: ✓  Context: 128K  Cost: $5/1M input, $15/1M output     │   │
│  │                                                                     │   │
│  │  [▼ Advanced Settings]                                              │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │  Temperature:     [0.7      ]                               │   │   │
│  │  │  Context Length:  [128000   ]                               │   │   │
│  │  │  Context History: [70       ] %                             │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  UTILITY MODEL (Background Tasks)                                   │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  Provider:    [OpenAI          ▼]                                   │   │
│  │  Model:       [GPT-4o-mini     ▼]                                   │   │
│  │                                                                     │   │
│  │  ℹ️ Cost-effective for summarization, extraction                   │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  EMBEDDING MODEL (Memory Search)                                    │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  Provider:    [HuggingFace     ▼]                                   │   │
│  │  Model:       [all-MiniLM-L6-v2▼]                                   │   │
│  │                                                                     │   │
│  │  ℹ️ Local model, no API cost                                       │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Form Validation

| Field | Rule | Error |
|-------|------|-------|
| `chat_model_provider` | Required | "Provider is required" |
| `chat_model_name` | Required | "Model is required" |
| `temperature` | 0-2 | "Temperature must be 0-2" |
| `ctx_length` | > 0 | "Context length must be positive" |

---

## 4. Agent User Screens

### 4.1 Multimodal Settings

**Route:** `/settings/multimodal`

#### Wireframe
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Agent Settings > Multimodal                                  [Save]       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  IMAGE GENERATION                                                   │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  [✓] Enable Image Generation                                        │   │
│  │                                                                     │   │
│  │  Provider:  [DALLE 3 ▼]                                             │   │
│  │  Quality:   [Standard ▼]  (HD costs 2x)                             │   │
│  │  Style:     [Vivid    ▼]                                            │   │
│  │                                                                     │   │
│  │  Monthly Usage: 312 / 500 images (62%)                              │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  DIAGRAM GENERATION                                                 │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  [✓] Enable Diagram Generation                                      │   │
│  │                                                                     │   │
│  │  Provider:  [Mermaid ▼] (Local - Free)                              │   │
│  │  Format:    [SVG ▼]                                                 │   │
│  │  Theme:     [Default ▼]                                             │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  VISION (Image Understanding)                                       │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  [✓] Enable Vision for Chat                                         │   │
│  │  [✓] Enable Vision for Browser                                      │   │
│  │                                                                     │   │
│  │  ℹ️ Allows agent to understand images in conversations             │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Common UI Patterns

### 5.1 Confirmation Modal

```
┌─────────────────────────────────────────────────────────────┐
│  Confirm Action                                        [X] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⚠️ Are you sure you want to delete this rate limit?       │
│                                                             │
│  This action cannot be undone.                              │
│                                                             │
│                              [Cancel]  [Delete]             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Toast Notifications

```
Success:
┌──────────────────────────────────────────┐
│  ✓ Rate limit updated successfully       │
└──────────────────────────────────────────┘

Error:
┌──────────────────────────────────────────┐
│  ✗ Failed to update rate limit           │
│    Try again or contact support.         │
└──────────────────────────────────────────┘
```

### 5.3 Empty State

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                     📋                                      │
│                                                             │
│              No rate limits configured                      │
│                                                             │
│              [+ Add Rate Limit]                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.4 Permission Denied

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                     🔒                                      │
│                                                             │
│              You don't have permission                      │
│              to access this page                            │
│                                                             │
│              Required: infra:configure                      │
│                                                             │
│              [Go Back]  [Request Access]                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Responsive Breakpoints

| Breakpoint | Width | Layout |
|------------|-------|--------|
| Mobile | < 768px | Single column, stacked cards |
| Tablet | 768-1024px | 2 column grid |
| Desktop | > 1024px | Full layout, side nav |

---

## 7. Accessibility Requirements

| Requirement | Implementation |
|-------------|----------------|
| Keyboard navigation | All interactive elements focusable |
| Screen reader | ARIA labels on all actions |
| Color contrast | WCAG AA minimum |
| Focus indicators | Visible focus rings |
| Error announcements | Live regions for errors |

---

## 8. Animation Guidelines

| Animation | Duration | Easing |
|-----------|----------|--------|
| Modal open | 200ms | ease-out |
| Modal close | 150ms | ease-in |
| Toast slide | 300ms | ease-out |
| Card hover | 150ms | ease |
| Loading skeleton | 1.5s | linear (loop) |
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
# SRS: UI Component Architecture & Permission Patterns

**Document ID:** SA01-SRS-UI-ARCHITECTURE-2025-12-25
**Purpose:** Define reusable UI patterns that reduce code bloat while preserving full permission granularity
**Status:** CANONICAL REFERENCE

---

## 1. Core Principle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PERMISSIONS: Full 78 granular permissions preserved (NO REDUCTION)        │
│  (tenant:create, tenant:delete, agent:configure, infra:ratelimit:edit)     │
├─────────────────────────────────────────────────────────────────────────────┤
│  ROLES: Combine permissions into reusable groups (convenience layer)       │
│  (SysAdmin = all, TenantAdmin = tenant:*, AgentUser = agent:chat)          │
├─────────────────────────────────────────────────────────────────────────────┤
│  UI COMPONENTS: Generic, data-driven, permission-aware                     │
│  (EntityManager checks user permissions dynamically before showing actions)│
└─────────────────────────────────────────────────────────────────────────────┘
```

**Result**: 66 screens → ~15 generic components
**Granularity**: 78 permissions fully preserved

---

## 2. Pattern 1: Generic Entity Manager

One component handles CRUD for ANY entity type:

```typescript
@customElement('entity-manager')
export class EntityManager extends LitElement {
  @property() entity: 'tenant' | 'agent' | 'user' | 'feature' | 'ratelimit';
  @property() apiBase: string;
  @property() columns: ColumnDef[];
  @property() permissions: string[];  // User's actual permissions
  
  render() {
    return html`
      <div class="entity-header">
        <h1>${this.entity}s</h1>
        <!-- Only show Create if user has permission -->
        ${this.hasPermission(`${this.entity}:create`) ? html`
          <button @click=${this.openCreate}>+ Create</button>
        ` : nothing}
      </div>
      
      <data-table
        .data=${this.items}
        .columns=${this.columns}
        .actions=${this.getAvailableActions()}
      />
    `;
  }
  
  private getAvailableActions(): Action[] {
    const actions: Action[] = [];
    if (this.hasPermission(`${this.entity}:view`)) actions.push({ icon: 'visibility', handler: this.view });
    if (this.hasPermission(`${this.entity}:edit`)) actions.push({ icon: 'edit', handler: this.edit });
    if (this.hasPermission(`${this.entity}:delete`)) actions.push({ icon: 'delete', handler: this.delete });
    return actions;
  }
  
  private hasPermission(perm: string): boolean {
    return this.permissions.includes(perm) || this.permissions.includes('*');
  }
}
```

**Usage:**
```html
<entity-manager
  entity="tenant"
  api-base="/api/v2/saas"
  :columns="tenantColumns"
  :permissions="currentUser.permissions"
/>
```

---

## 3. Pattern 2: Settings Inheritance Tree

Three-level settings with cascading overrides:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PLATFORM DEFAULTS (God Layer)                                              │
│  └── max_agents: 10                                                         │
│  └── max_voice_minutes: 60                                                  │
│  └── default_llm: gpt-4o                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  TENANT OVERRIDES (Tier-based or custom)                                    │
│  └── max_agents: 50  (inherits rest from Platform)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  AGENT OVERRIDES (Per-agent customization)                                  │
│  └── default_llm: claude-3.5  (inherits rest from Tenant)                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Django Model:**
```python
class Setting(models.Model):
    key = models.CharField(max_length=100)
    value = models.JSONField()
    level = models.CharField(choices=['PLATFORM', 'TENANT', 'AGENT'])
    platform = models.ForeignKey('Platform', null=True)
    tenant = models.ForeignKey('Tenant', null=True)
    agent = models.ForeignKey('Agent', null=True)
    
    class Meta:
        unique_together = ['key', 'level', 'platform', 'tenant', 'agent']

def get_effective_setting(key: str, agent_id: UUID) -> Any:
    """Cascade: Agent → Tenant → Platform → Default"""
    agent = Agent.objects.get(id=agent_id)
    
    # Try agent-level
    if (s := Setting.objects.filter(key=key, agent=agent).first()):
        return s.value
    
    # Try tenant-level
    if (s := Setting.objects.filter(key=key, tenant=agent.tenant).first()):
        return s.value
    
    # Platform default
    if (s := Setting.objects.filter(key=key, level='PLATFORM').first()):
        return s.value
    
    return DEFAULTS.get(key)
```

---

## 4. Pattern 3: Dynamic Form Builder

Forms generated from JSON Schema (no hardcoded forms):

```typescript
@customElement('settings-form')
export class SettingsForm extends LitElement {
  @property() schemaUrl: string;  // e.g., /api/v2/schemas/postgresql
  @property() values: Record<string, any>;
  @property() permissions: string[];
  
  @state() schema: JSONSchema;
  
  async connectedCallback() {
    this.schema = await fetch(this.schemaUrl).then(r => r.json());
  }
  
  render() {
    return html`
      <form @submit=${this.save}>
        ${this.schema.properties.map(prop => this.renderField(prop))}
        
        ${this.hasPermission('settings:write') ? html`
          <button type="submit">Save</button>
        ` : html`
          <p class="read-only-notice">View only</p>
        `}
      </form>
    `;
  }
  
  private renderField(prop: SchemaProperty) {
    switch(prop.type) {
      case 'string': return html`<input-text .field=${prop} .value=${this.values[prop.key]}/>`;
      case 'number': return html`<input-number .field=${prop} .value=${this.values[prop.key]}/>`;
      case 'boolean': return html`<input-toggle .field=${prop} .value=${this.values[prop.key]}/>`;
      case 'enum': return html`<input-select .field=${prop} .value=${this.values[prop.key]}/>`;
    }
  }
}
```

**Backend Schema API:**
```python
@router.get("/schemas/{entity}")
def get_schema(entity: str) -> dict:
    """Return JSON Schema from Django model introspection."""
    model = apps.get_model('admin.core', entity.title())
    return model_to_json_schema(model)
```

---

## 5. Pattern 4: Tab-Based Composition

One route, multiple views via tabs:

```typescript
// Instead of 5 routes:
// /platform/infrastructure/database
// /platform/infrastructure/redis
// /platform/infrastructure/temporal
// /platform/infrastructure/health
// /platform/infrastructure/degradation

// One route with tabs:
@customElement('infrastructure-dashboard')
export class InfrastructureDashboard extends LitElement {
  @state() activeTab: 'health' | 'ratelimits' | 'degradation' = 'health';
  
  render() {
    return html`
      <tab-bar .active=${this.activeTab} @change=${(e) => this.activeTab = e.detail}>
        <tab name="health">Service Health</tab>
        <tab name="ratelimits">Rate Limits</tab>
        <tab name="degradation">Degradation Mode</tab>
      </tab-bar>
      
      ${this.activeTab === 'health' ? this.renderHealth() : nothing}
      ${this.activeTab === 'ratelimits' ? this.renderRateLimits() : nothing}
      ${this.activeTab === 'degradation' ? this.renderDegradation() : nothing}
    `;
  }
}
```

**Benefit**: 5 routes → 1 route, 5 components → 1 component with 3 render methods

---

## 6. Pattern 5: Permission-Aware Action Menus

Generic action menu that filters based on permissions:

```typescript
@customElement('action-menu')
export class ActionMenu extends LitElement {
  @property() entity: string;
  @property() entityId: string;
  @property() permissions: string[];
  
  private actions = [
    { key: 'view', icon: 'visibility', label: 'View', permission: ':view' },
    { key: 'edit', icon: 'edit', label: 'Edit', permission: ':edit' },
    { key: 'duplicate', icon: 'content_copy', label: 'Duplicate', permission: ':create' },
    { key: 'delete', icon: 'delete', label: 'Delete', permission: ':delete', danger: true },
    { key: 'suspend', icon: 'pause', label: 'Suspend', permission: ':suspend' },
    { key: 'impersonate', icon: 'person', label: 'Impersonate', permission: ':impersonate' },
  ];
  
  render() {
    const available = this.actions.filter(a => 
      this.permissions.includes(`${this.entity}${a.permission}`)
    );
    
    return html`
      <dropdown-menu>
        ${available.map(a => html`
          <menu-item 
            icon=${a.icon} 
            ?danger=${a.danger}
            @click=${() => this.emit(a.key)}
          >${a.label}</menu-item>
        `)}
      </dropdown-menu>
    `;
  }
}
```

---

## 7. Permission Hierarchy (Preserved Granularity)

```
PLATFORM PERMISSIONS (28)
├── platform:manage           # Full platform control
├── tenant:list               # List all tenants
├── tenant:view               # View tenant details
├── tenant:create             # Create new tenant
├── tenant:edit               # Edit tenant settings
├── tenant:delete             # Delete tenant
├── tenant:suspend            # Suspend tenant
├── tenant:impersonate        # Act as tenant admin
├── tier:list                 # List subscription tiers
├── tier:create               # Create tier
├── tier:edit                 # Modify tier limits
├── tier:delete               # Remove tier
├── billing:view              # View platform revenue
├── billing:refund            # Issue refunds
├── infra:health:view         # View service health
├── infra:ratelimit:view      # View rate limits
├── infra:ratelimit:edit      # Modify rate limits
├── infra:degradation:view    # View degradation status
├── infra:degradation:control # Start/stop monitoring
├── role:list                 # List roles
├── role:create               # Create roles
├── role:edit                 # Modify roles
├── role:delete               # Delete roles
├── permission:view           # Browse SpiceDB
├── audit:view                # View all audit logs
├── feature:manage            # Enable/disable features
├── mcp:manage                # MCP server registry
└── secret:manage             # Platform secrets

TENANT PERMISSIONS (25)
├── tenant:settings           # Tenant settings
├── user:list                 # List tenant users
├── user:invite               # Invite users
├── user:edit                 # Edit user roles
├── user:remove               # Remove users
├── agent:list                # List agents
├── agent:create              # Create agent
├── agent:edit                # Configure agent
├── agent:delete              # Delete agent
├── usage:view                # View usage metrics
├── billing:view              # View invoices
├── billing:pay               # Make payments
├── apikey:list               # List API keys
├── apikey:create             # Generate keys
├── apikey:revoke             # Revoke keys
├── integration:list          # List integrations
├── integration:enable        # Enable integrations
├── integration:configure     # Configure integrations
├── audit:view                # Tenant audit log
├── role:list                 # Tenant roles
├── role:assign               # Assign roles
├── webhook:manage            # Webhook configuration
├── export:data               # Export tenant data
├── mcp:enable                # Enable MCP servers
└── voice:configure           # Voice settings

AGENT PERMISSIONS (25)
├── agent:chat                # Use chat
├── agent:voice               # Use voice
├── agent:memory:read         # Read memories
├── agent:memory:write        # Create memories
├── agent:memory:delete       # Delete memories
├── agent:tool:use            # Use approved tools
├── agent:tool:configure      # Configure tool access
├── agent:settings:view       # View settings
├── agent:settings:edit       # Edit settings
├── agent:model:select        # Choose LLM model
├── agent:persona:edit        # Edit persona
├── agent:context:manage      # Manage context
├── agent:file:upload         # Upload files
├── agent:file:delete         # Delete files
├── agent:image:generate      # Generate images
├── agent:screenshot:capture  # Screen capture
├── agent:diagram:generate    # Generate diagrams
├── agent:code:execute        # Run code
├── agent:web:browse          # Web browsing
├── agent:api:call            # External APIs
├── agent:share               # Share conversations
├── agent:export              # Export data
├── dev:console               # Developer console
├── dev:metrics               # Dev metrics
└── trn:cognitive             # Trainer mode
```

**Total: 78 permissions** → All preserved, UI components just filter based on user's granted permissions.

---

## 8. Implementation Priority

| Phase | Pattern | Components |
|-------|---------|------------|
| **P0** | Tab Composition | ✅ Done (Infrastructure Dashboard) |
| **P1** | Entity Manager | `<entity-manager>` for CRUD screens |
| **P2** | Settings Form | `<settings-form>` with JSON Schema |
| **P3** | Action Menu | `<action-menu>` permission-aware |
| **P4** | Settings Cascade | Django model + API |

---

*Document created: December 25, 2025*
*Maintains full 78-permission granularity while reducing UI code through reusable patterns*
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
# SomaStack Unified UI Design System - Requirements Document

## Document Control

| Field | Value |
|-------|-------|
| **Document ID** | SOMASTACK-UI-REQ-2025-12 |
| **Version** | 1.0 |
| **Date** | 2025-12-22 |
| **Status** | DRAFT |
| **Applies To** | SomaAgent01, SomaBrain, SomaFractalMemory, AgentVoiceBox |

---

## Introduction

This specification defines the requirements for the **SomaStack Unified UI Design System** - a comprehensive, standardized visual language and component library that will be shared across all SomaStack projects. The system provides consistent theming, role-based access controls, real-time status indicators, and a modern glassmorphism aesthetic.

## Glossary

- **SomaStack**: The unified platform comprising SomaAgent01, SomaBrain, SomaFractalMemory, and AgentVoiceBox
- **Design_System**: The collection of CSS variables, components, and patterns that define the visual language
- **Theme_Engine**: The JavaScript module responsible for loading, validating, and applying themes
- **Role_Manager**: The system component that manages user roles and permissions for UI access
- **Status_Indicator**: Visual elements that display real-time system health and state
- **Glassmorphism**: A design style featuring frosted glass effects with subtle transparency and blur
- **Geist_Font**: The primary sans-serif typeface used throughout the system
- **Admin_Mode**: Elevated access level with full system control capabilities
- **Operator_Mode**: Standard access level for day-to-day operations
- **Viewer_Mode**: Read-only access level for monitoring

---

## Requirements

### Requirement 1: Design Token Architecture

**User Story:** As a developer, I want a centralized design token system, so that I can maintain visual consistency across all SomaStack applications.

#### Acceptance Criteria

1. THE Design_System SHALL define CSS custom properties for all visual attributes in a single `somastack-tokens.css` file
2. WHEN a token value changes THEN the Design_System SHALL propagate the change to all components without code modifications
3. THE Design_System SHALL support 5 color palettes: neutral, primary, success, warning, error
4. THE Design_System SHALL define 8 spacing scale values: 4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px
5. THE Design_System SHALL define 6 typography scale values: xs (12px), sm (14px), base (16px), lg (18px), xl (20px), 2xl (24px)
6. THE Design_System SHALL use Geist font family as primary with system-ui fallback
7. THE Design_System SHALL define 3 elevation levels using box-shadow for depth hierarchy
8. THE Design_System SHALL define border-radius tokens: none (0), sm (4px), md (8px), lg (12px), full (9999px)

---

### Requirement 2: Glassmorphism Surface System

**User Story:** As a user, I want a modern, clean interface with subtle depth, so that I can focus on content without visual clutter.

#### Acceptance Criteria

1. THE Design_System SHALL implement glassmorphism surfaces with `backdrop-filter: blur(12px)`
2. THE Design_System SHALL define 3 surface levels: surface-1 (cards), surface-2 (modals), surface-3 (overlays)
3. WHEN displaying a surface THEN the Design_System SHALL apply subtle border with 10% opacity
4. THE Design_System SHALL maintain minimum 4.5:1 contrast ratio for text on all surfaces (WCAG AA)
5. THE Design_System SHALL use white/light-grey base palette with minimal color accents
6. WHEN a surface contains interactive elements THEN the Design_System SHALL apply hover state with 5% opacity increase

---

### Requirement 3: Role-Based UI Access Control

**User Story:** As a system administrator, I want UI elements to adapt based on user roles, so that users only see controls appropriate to their access level.

#### Acceptance Criteria

1. THE Role_Manager SHALL support 3 access levels: Admin, Operator, Viewer
2. WHEN a user has Admin role THEN the UI SHALL display all management controls (create, edit, delete, approve)
3. WHEN a user has Operator role THEN the UI SHALL display operational controls (view, execute, monitor)
4. WHEN a user has Viewer role THEN the UI SHALL display read-only views (view, monitor)
5. THE Role_Manager SHALL retrieve role information from JWT token claims
6. WHEN role information is unavailable THEN the UI SHALL default to Viewer mode
7. THE Role_Manager SHALL cache role state in Lit Reactive Controller for reactive updates
8. WHEN displaying admin-only controls THEN the UI SHALL use Lit conditional rendering with `?hidden=${!this.authController.isAdmin}`

---

### Requirement 4: Navigation System

**User Story:** As a user, I want intuitive navigation, so that I can quickly access different sections of the application.

#### Acceptance Criteria

1. THE Navigation_Component SHALL implement a collapsible sidebar with icon + label format
2. WHEN sidebar is collapsed THEN the Navigation_Component SHALL display icons only with tooltips
3. THE Navigation_Component SHALL highlight the active section with accent color background
4. THE Navigation_Component SHALL group items by category: Main, Tools, Settings, Admin
5. WHEN user hovers over a nav item THEN the Navigation_Component SHALL display subtle highlight
6. THE Navigation_Component SHALL support keyboard navigation (Tab, Enter, Arrow keys)
7. THE Navigation_Component SHALL persist collapsed/expanded state to localStorage
8. THE Navigation_Component SHALL display notification badges for items requiring attention

---

### Requirement 5: Dashboard Stats Cards

**User Story:** As a user, I want to see key metrics at a glance, so that I can quickly assess system status.

#### Acceptance Criteria

1. THE Stats_Card_Component SHALL display: icon, metric value, label, and trend indicator
2. WHEN metric has changed THEN the Stats_Card_Component SHALL display percentage change with up/down arrow
3. THE Stats_Card_Component SHALL use subtle color coding for trend: green (positive), red (negative), grey (neutral)
4. THE Stats_Card_Component SHALL support 4 card sizes: sm (160px), md (200px), lg (280px), full (100%)
5. WHEN displaying large numbers THEN the Stats_Card_Component SHALL format with K/M/B suffixes
6. THE Stats_Card_Component SHALL animate value changes with 300ms transition
7. THE Stats_Card_Component SHALL be responsive and stack on mobile viewports

---

### Requirement 6: Data Tables

**User Story:** As a user, I want to view and manage data in organized tables, so that I can efficiently work with lists of items.

#### Acceptance Criteria

1. THE Data_Table_Component SHALL display columns with sortable headers
2. WHEN a column header is clicked THEN the Data_Table_Component SHALL sort by that column (asc/desc toggle)
3. THE Data_Table_Component SHALL support row selection with checkboxes
4. THE Data_Table_Component SHALL display status badges with semantic colors: approved (green), pending (amber), rejected (red)
5. THE Data_Table_Component SHALL support action buttons per row: View, Edit, Delete (role-dependent)
6. WHEN table has more than 10 rows THEN the Data_Table_Component SHALL implement pagination
7. THE Data_Table_Component SHALL support search/filter functionality
8. THE Data_Table_Component SHALL display loading skeleton during data fetch
9. WHEN no data exists THEN the Data_Table_Component SHALL display empty state with helpful message

---

### Requirement 7: Real-Time Status Indicators

**User Story:** As an operator, I want to see real-time system status, so that I can monitor health and respond to issues.

#### Acceptance Criteria

1. THE Status_Indicator SHALL display service health with colored dots: green (healthy), amber (degraded), red (down), grey (unknown)
2. WHEN service status changes THEN the Status_Indicator SHALL update within 5 seconds
3. THE Status_Indicator SHALL display last-checked timestamp
4. THE Status_Indicator SHALL support pulse animation for active/processing states
5. WHEN hovering over status THEN the Status_Indicator SHALL display detailed tooltip with metrics
6. THE Status_Indicator SHALL integrate with `/health` endpoints of all SomaStack services
7. THE Status_Indicator SHALL display connection status for: PostgreSQL, Redis, Milvus, Kafka, Temporal

---

### Requirement 8: Settings Panel Architecture

**User Story:** As a user, I want organized settings, so that I can configure the application according to my needs.

#### Acceptance Criteria

1. THE Settings_Panel SHALL organize settings into tabs: General, Appearance, Notifications, Security, Admin
2. WHEN user lacks Admin role THEN the Settings_Panel SHALL hide the Admin tab
3. THE Settings_Panel SHALL persist settings to localStorage for client-side preferences
4. THE Settings_Panel SHALL persist settings to backend API for server-side preferences
5. WHEN a setting changes THEN the Settings_Panel SHALL apply immediately without page reload
6. THE Settings_Panel SHALL validate inputs before saving
7. THE Settings_Panel SHALL display success/error feedback after save operations

---

### Requirement 9: Agent-Specific UI Components

**User Story:** As an agent operator, I want specialized UI components for agent management, so that I can effectively control and monitor agents.

#### Acceptance Criteria

1. THE Agent_Dashboard SHALL display: active sessions, cognitive load, memory usage, tool executions
2. THE Agent_Dashboard SHALL display neuromodulator levels with visual gauges (dopamine, serotonin, noradrenaline, acetylcholine)
3. THE Agent_Dashboard SHALL display FSM state with visual state machine diagram
4. WHEN agent is processing THEN the Agent_Dashboard SHALL display real-time reasoning stream
5. THE Agent_Dashboard SHALL display conversation history with message bubbles
6. THE Agent_Dashboard SHALL support tool execution monitoring with status indicators
7. THE Agent_Dashboard SHALL display memory browser with search and filter capabilities

---

### Requirement 10: Memory Browser Component

**User Story:** As a user, I want to browse and search memories, so that I can understand what the agent knows.

#### Acceptance Criteria

1. THE Memory_Browser SHALL display memories in card or list view (toggleable)
2. THE Memory_Browser SHALL support search by content, coordinate, and metadata
3. THE Memory_Browser SHALL display memory type badges: episodic (blue), semantic (purple)
4. THE Memory_Browser SHALL display memory age and decay status
5. WHEN clicking a memory THEN the Memory_Browser SHALL display full details in side panel
6. THE Memory_Browser SHALL support memory deletion (Admin only)
7. THE Memory_Browser SHALL display vector similarity scores when searching

---

### Requirement 11: Voice Interface Components

**User Story:** As a voice user, I want visual feedback during voice interactions, so that I can understand the system state.

#### Acceptance Criteria

1. THE Voice_Interface SHALL display audio waveform visualization during recording
2. THE Voice_Interface SHALL display transcription in real-time as speech is recognized
3. THE Voice_Interface SHALL display TTS playback progress indicator
4. THE Voice_Interface SHALL support push-to-talk and voice-activity-detection modes
5. WHEN voice is processing THEN the Voice_Interface SHALL display animated indicator
6. THE Voice_Interface SHALL display connection status to voice backend

---

### Requirement 12: Responsive Layout System

**User Story:** As a user, I want the UI to work on different screen sizes, so that I can use the application on any device.

#### Acceptance Criteria

1. THE Layout_System SHALL support 4 breakpoints: mobile (<640px), tablet (640-1024px), desktop (1024-1440px), wide (>1440px)
2. WHEN viewport is mobile THEN the Layout_System SHALL collapse sidebar to bottom navigation
3. WHEN viewport is tablet THEN the Layout_System SHALL collapse sidebar to icon-only mode
4. THE Layout_System SHALL use CSS Grid for main layout structure
5. THE Layout_System SHALL use Flexbox for component-level layouts
6. THE Layout_System SHALL maintain minimum touch target size of 44x44px on mobile

---

### Requirement 13: Accessibility Compliance

**User Story:** As a user with accessibility needs, I want the UI to be fully accessible, so that I can use all features effectively.

#### Acceptance Criteria

1. THE Design_System SHALL comply with WCAG 2.1 AA standards
2. THE Design_System SHALL support keyboard navigation for all interactive elements
3. THE Design_System SHALL provide ARIA labels for all non-text content
4. THE Design_System SHALL support screen reader announcements for dynamic content
5. THE Design_System SHALL maintain focus indicators for keyboard navigation
6. THE Design_System SHALL support reduced-motion preference via `prefers-reduced-motion`
7. THE Design_System SHALL support high-contrast mode via `prefers-contrast`

---

### Requirement 14: Theme Switching

**User Story:** As a user, I want to switch between light and dark themes, so that I can use the application comfortably in different lighting conditions.

#### Acceptance Criteria

1. THE Theme_Engine SHALL support light and dark color schemes
2. WHEN user toggles theme THEN the Theme_Engine SHALL apply changes within 100ms
3. THE Theme_Engine SHALL persist theme preference to localStorage
4. THE Theme_Engine SHALL respect `prefers-color-scheme` system preference by default
5. THE Theme_Engine SHALL provide smooth transition animation between themes (300ms)
6. THE Theme_Engine SHALL ensure all components render correctly in both themes

---

### Requirement 15: Loading and Error States

**User Story:** As a user, I want clear feedback during loading and errors, so that I understand what the system is doing.

#### Acceptance Criteria

1. THE Design_System SHALL provide skeleton loading components for all data-driven views
2. THE Design_System SHALL provide spinner component for action-in-progress states
3. THE Design_System SHALL provide error boundary component with retry action
4. WHEN an error occurs THEN the Error_Component SHALL display user-friendly message with error code
5. THE Design_System SHALL provide toast notification component for transient messages
6. THE Toast_Component SHALL support 4 variants: info, success, warning, error
7. THE Toast_Component SHALL auto-dismiss after 5 seconds (configurable)

---

### Requirement 16: Form Components

**User Story:** As a user, I want consistent form controls, so that I can input data efficiently.

#### Acceptance Criteria

1. THE Form_System SHALL provide: text input, textarea, select, checkbox, radio, toggle, slider, color picker
2. THE Form_System SHALL display validation errors inline below inputs
3. THE Form_System SHALL support disabled and readonly states
4. THE Form_System SHALL support placeholder text and helper text
5. WHEN input is focused THEN the Form_System SHALL display focus ring with accent color
6. THE Form_System SHALL support form-level validation before submission
7. THE Form_System SHALL integrate with Lit Web Components for reactive state management

---

### Requirement 17: Modal and Dialog System

**User Story:** As a user, I want modal dialogs for focused interactions, so that I can complete tasks without losing context.

#### Acceptance Criteria

1. THE Modal_Component SHALL support sizes: sm (400px), md (600px), lg (800px), full (100%)
2. THE Modal_Component SHALL trap focus within modal when open
3. THE Modal_Component SHALL close on Escape key press
4. THE Modal_Component SHALL close on backdrop click (configurable)
5. THE Modal_Component SHALL animate open/close with fade and scale (200ms)
6. THE Modal_Component SHALL prevent body scroll when open
7. THE Modal_Component SHALL support stacked modals with proper z-index management

---

### Requirement 18: Cross-Project Consistency

**User Story:** As a developer, I want the same UI components across all SomaStack projects, so that users have a consistent experience.

#### Acceptance Criteria

1. THE Design_System SHALL be packaged as a standalone CSS + JS bundle
2. THE Design_System SHALL be importable via `<link>` and `<script>` tags (no build step required)
3. THE Design_System SHALL provide Lit Web Components for all interactive elements
4. THE Design_System SHALL document all components with usage examples
5. WHEN updating the Design_System THEN all projects SHALL receive updates via shared import
6. THE Design_System SHALL version components following semantic versioning

---

## Technical Requirements

### TR-UI-001: CSS Architecture

| ID | Requirement | Priority |
|----|-------------|----------|
| TR-UI-001.1 | All styles MUST use CSS custom properties for theming | HIGH |
| TR-UI-001.2 | CSS MUST be organized using BEM naming convention | HIGH |
| TR-UI-001.3 | CSS file size MUST be under 100KB (minified) | MEDIUM |
| TR-UI-001.4 | CSS MUST not use `!important` except for utility classes | HIGH |

### TR-UI-002: JavaScript Architecture

| ID | Requirement | Priority |
|----|-------------|----------|
| TR-UI-002.1 | All interactive components MUST use Lit 3.x Web Components | HIGH |
| TR-UI-002.2 | Components MUST be ES modules, importable without build step | HIGH |
| TR-UI-002.3 | JS file size MUST be under 50KB (minified) | MEDIUM |
| TR-UI-002.4 | All components MUST be tree-shakeable | MEDIUM |

### TR-UI-003: Performance

| ID | Requirement | Priority |
|----|-------------|----------|
| TR-UI-003.1 | First Contentful Paint MUST be under 1.5 seconds | HIGH |
| TR-UI-003.2 | Time to Interactive MUST be under 3 seconds | HIGH |
| TR-UI-003.3 | Layout shifts (CLS) MUST be under 0.1 | HIGH |
| TR-UI-003.4 | All animations MUST run at 60fps | MEDIUM |

---

## Security Requirements

### SEC-UI-001: XSS Prevention

| ID | Requirement | Priority |
|----|-------------|----------|
| SEC-UI-001.1 | All user input MUST be sanitized before rendering | HIGH |
| SEC-UI-001.2 | Theme JSON MUST NOT contain executable code | HIGH |
| SEC-UI-001.3 | CSP headers MUST be configured to prevent inline scripts | HIGH |

### SEC-UI-002: Authentication Integration

| ID | Requirement | Priority |
|----|-------------|----------|
| SEC-UI-002.1 | UI MUST validate JWT tokens before displaying protected content | HIGH |
| SEC-UI-002.2 | UI MUST redirect to login on 401 responses | HIGH |
| SEC-UI-002.3 | UI MUST clear sensitive data on logout | HIGH |

---

## Dependencies

- Lit 3.x (Web Components framework)
- Geist Font (typography)
- No other external dependencies

## References

- AgentSkin UIX Requirements (SA01-AGS-REQ-2025-12)
- SomaStack Platform Requirements (SOMASTACK-REQ-2025-12)
- WCAG 2.1 Guidelines
- Material Design 3 Guidelines (inspiration)

---

**Last Updated:** 2025-12-22  
**Status:** DRAFT - Pending Review
# Software Requirements Specification

## SomaStack Unified UI Design System

---

## Document Control

| Field | Value |
|-------|-------|
| **Document ID** | SRS-SOMASTACK-UI-2025-001 |
| **Version** | 1.0.0 |
| **Classification** | Internal |
| **Status** | APPROVED |
| **Effective Date** | 2025-12-22 |
| **Review Date** | 2026-06-22 |
| **Owner** | SomaStack Platform Team |
| **Standard** | ISO/IEC/IEEE 29148:2018 |

### Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 0.1.0 | 2025-12-22 | Kiro AI | Initial draft |
| 1.0.0 | 2025-12-22 | Kiro AI | Approved for implementation |

### Approval Signatures

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | _________________ | _________________ | ________ |
| Technical Lead | _________________ | _________________ | ________ |
| QA Lead | _________________ | _________________ | ________ |
| Security Officer | _________________ | _________________ | ________ |

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [Specific Requirements](#3-specific-requirements)
4. [System Features](#4-system-features)
5. [External Interface Requirements](#5-external-interface-requirements)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [Security Requirements](#7-security-requirements)
8. [Data Requirements](#8-data-requirements)
9. [Constraints](#9-constraints)
10. [Assumptions and Dependencies](#10-assumptions-and-dependencies)
11. [Acceptance Criteria](#11-acceptance-criteria)
12. [Traceability Matrix](#12-traceability-matrix)
13. [Appendices](#13-appendices)

---


## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) document provides a complete and comprehensive description of the requirements for the **SomaStack Unified UI Design System**. This document serves as the authoritative source for all functional, non-functional, and interface requirements governing the design, development, testing, and deployment of the unified user interface framework across the SomaStack platform.

The intended audience for this document includes:
- Software Architects and Developers
- UI/UX Designers
- Quality Assurance Engineers
- Project Managers
- Security Auditors
- Operations Teams
- External Auditors and Compliance Officers

### 1.2 Scope

#### 1.2.1 System Name
**SomaStack Unified UI Design System** (SUIDS)

#### 1.2.2 System Overview
The SomaStack Unified UI Design System is a comprehensive, standardized visual language and component library that provides consistent theming, role-based access controls, real-time status indicators, and a modern glassmorphism aesthetic across all SomaStack platform applications.

#### 1.2.3 In-Scope Applications
| Application | Description | Port |
|-------------|-------------|------|
| SomaAgent01 | AI Agent Orchestration Platform | 21016 |
| SomaBrain | Cognitive Memory Runtime | 9696 |
| SomaFractalMemory | Fractal Memory Storage System | 9595 |
| AgentVoiceBox | Voice Interface System | 25000 |

#### 1.2.4 Out of Scope
- Backend API implementations (covered by separate SRS documents)
- Database schema design (covered by separate DDS documents)
- Infrastructure provisioning (covered by IaC specifications)
- Mobile native applications
- Third-party integrations not listed in Section 10

### 1.3 Definitions, Acronyms, and Abbreviations

#### 1.3.1 Definitions

| Term | Definition |
|------|------------|
| Design Token | A named entity that stores a visual design attribute (color, spacing, typography) as a CSS custom property |
| Glassmorphism | A design style featuring frosted glass effects with subtle transparency, blur, and layered surfaces |
| Component | A reusable, self-contained UI element with defined behavior and styling |
| Store | An Alpine.js reactive state container shared across components |
| Theme | A collection of design tokens that define the visual appearance of the application |
| Role | A named set of permissions that determines UI element visibility and functionality |
| Tenant | An isolated organizational unit within the multi-tenant SomaStack platform |

#### 1.3.2 Acronyms

| Acronym | Expansion |
|---------|-----------|
| SUIDS | SomaStack Unified UI Design System |
| CSS | Cascading Style Sheets |
| JWT | JSON Web Token |
| WCAG | Web Content Accessibility Guidelines |
| ARIA | Accessible Rich Internet Applications |
| API | Application Programming Interface |
| SRS | Software Requirements Specification |
| UI | User Interface |
| UX | User Experience |
| SSE | Server-Sent Events |
| WebSocket | Full-duplex communication protocol |
| OPA | Open Policy Agent |
| RBAC | Role-Based Access Control |

#### 1.3.3 Abbreviations

| Abbreviation | Meaning |
|--------------|---------|
| req. | requirement |
| sec. | section |
| fig. | figure |
| tbl. | table |
| ms | milliseconds |
| px | pixels |
| rem | root em (CSS unit) |

### 1.4 References

| ID | Document | Version | Date |
|----|----------|---------|------|
| REF-001 | ISO/IEC/IEEE 29148:2018 - Systems and software engineering — Life cycle processes — Requirements engineering | 2018 | 2018-11 |
| REF-002 | WCAG 2.1 - Web Content Accessibility Guidelines | 2.1 | 2018-06 |
| REF-003 | Alpine.js Documentation | 3.x | 2024 |
| REF-004 | SomaAgent01 Product Requirements Document | 1.0 | 2025-12 |
| REF-005 | SomaBrain Technical Manual | 1.0 | 2025-12 |
| REF-006 | SomaFractalMemory API Specification | 1.0 | 2025-12 |
| REF-007 | AgentVoiceBox Architecture Document | 1.0 | 2025-12 |
| REF-008 | VIBE Coding Rules | 1.0 | 2025-12 |
| REF-009 | Material Design 3 Guidelines | 3.0 | 2024 |
| REF-010 | Geist Font License | 1.0 | 2024 |

### 1.5 Document Overview

This SRS is organized according to ISO/IEC/IEEE 29148:2018 structure:

- **Section 1** provides introduction, scope, and definitions
- **Section 2** describes the overall system context and constraints
- **Section 3** specifies detailed functional requirements
- **Section 4** describes system features and use cases
- **Section 5** defines external interface requirements
- **Section 6** specifies non-functional requirements (performance, reliability, etc.)
- **Section 7** details security requirements
- **Section 8** describes data requirements
- **Section 9** lists constraints and limitations
- **Section 10** documents assumptions and dependencies
- **Section 11** defines acceptance criteria
- **Section 12** provides requirements traceability matrix
- **Section 13** contains appendices with supplementary information


---

## 2. Overall Description

### 2.1 Product Perspective

#### 2.1.1 System Context

The SomaStack Unified UI Design System operates as a shared foundation layer across all SomaStack platform applications. It provides the visual language, component library, and state management infrastructure that ensures consistency and maintainability across the platform.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SOMASTACK PLATFORM                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ SomaAgent01 │  │  SomaBrain  │  │ SomaFractal │  │AgentVoiceBox│           │
│  │   WebUI     │  │   WebUI     │  │   Memory    │  │   WebUI     │           │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘           │
│         │                │                │                │                   │
│         └────────────────┴────────────────┴────────────────┘                   │
│                                   │                                             │
│                                   ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                 SOMASTACK UNIFIED UI DESIGN SYSTEM                      │   │
│  ├─────────────────────────────────────────────────────────────────────────┤   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│  │  │   Design    │  │  Component  │  │    State    │  │ Integration │    │   │
│  │  │   Tokens    │  │   Library   │  │   Stores    │  │    Layer    │    │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                   │                                             │
│                                   ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        BACKEND SERVICES                                  │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │   │
│  │  │   JWT   │  │  Health │  │Settings │  │   OPA   │  │  WebSocket│      │   │
│  │  │  Auth   │  │  APIs   │  │  APIs   │  │ Policies│  │   APIs   │       │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

#### 2.1.2 System Interfaces

| Interface | Type | Description |
|-----------|------|-------------|
| SI-001 | REST API | Health check endpoints for status monitoring |
| SI-002 | REST API | Settings persistence endpoints |
| SI-003 | JWT | Authentication token parsing |
| SI-004 | WebSocket | Real-time updates for voice interface |
| SI-005 | SSE | Server-sent events for status updates |
| SI-006 | localStorage | Client-side preference persistence |

#### 2.1.3 Hardware Interfaces

The system has no direct hardware interfaces. All hardware interaction occurs through the browser's standard APIs.

#### 2.1.4 Software Interfaces

| Interface | Software | Version | Purpose |
|-----------|----------|---------|---------|
| SWI-001 | Alpine.js | 3.x | Reactive component framework |
| SWI-002 | Modern Browsers | ES2020+ | Runtime environment |
| SWI-003 | CSS Custom Properties | Level 1 | Design token implementation |
| SWI-004 | Web Audio API | Standard | Voice waveform visualization |
| SWI-005 | Intersection Observer | Standard | Lazy loading |
| SWI-006 | ResizeObserver | Standard | Responsive behavior |

#### 2.1.5 Communication Interfaces

| Interface | Protocol | Port | Purpose |
|-----------|----------|------|---------|
| CI-001 | HTTPS | 443 | Secure API communication |
| CI-002 | WSS | 443 | Secure WebSocket communication |
| CI-003 | HTTP | 80 | Development only (redirects to HTTPS) |

### 2.2 Product Functions

The SomaStack Unified UI Design System provides the following major functions:

| ID | Function | Description |
|----|----------|-------------|
| PF-001 | Design Token Management | Centralized CSS custom properties for visual consistency |
| PF-002 | Theme Switching | Light/dark/system theme support with persistence |
| PF-003 | Role-Based UI Control | Dynamic UI element visibility based on user roles |
| PF-004 | Component Library | Reusable UI components with consistent styling |
| PF-005 | State Management | Alpine.js stores for shared application state |
| PF-006 | Status Monitoring | Real-time service health visualization |
| PF-007 | Accessibility Support | WCAG 2.1 AA compliant interface |
| PF-008 | Responsive Layout | Adaptive layouts for all screen sizes |
| PF-009 | Form Handling | Validated form inputs with feedback |
| PF-010 | Notification System | Toast notifications and alerts |

### 2.3 User Classes and Characteristics

#### 2.3.1 User Class: Administrator

| Attribute | Description |
|-----------|-------------|
| **Role ID** | UC-ADMIN |
| **Description** | System administrators with full platform access |
| **Technical Expertise** | High |
| **Frequency of Use** | Daily |
| **Primary Tasks** | System configuration, user management, monitoring, troubleshooting |
| **UI Permissions** | Full access to all UI elements and controls |

#### 2.3.2 User Class: Operator

| Attribute | Description |
|-----------|-------------|
| **Role ID** | UC-OPERATOR |
| **Description** | Day-to-day operators managing agent workflows |
| **Technical Expertise** | Medium |
| **Frequency of Use** | Daily |
| **Primary Tasks** | Agent management, conversation monitoring, task execution |
| **UI Permissions** | View, create, edit, execute operations |

#### 2.3.3 User Class: Viewer

| Attribute | Description |
|-----------|-------------|
| **Role ID** | UC-VIEWER |
| **Description** | Read-only users for monitoring and reporting |
| **Technical Expertise** | Low to Medium |
| **Frequency of Use** | Occasional |
| **Primary Tasks** | Dashboard viewing, report generation, status monitoring |
| **UI Permissions** | View-only access |

### 2.4 Operating Environment

#### 2.4.1 Supported Browsers

| Browser | Minimum Version | Support Level |
|---------|-----------------|---------------|
| Google Chrome | 90+ | Full |
| Mozilla Firefox | 88+ | Full |
| Microsoft Edge | 90+ | Full |
| Safari | 14+ | Full |
| Safari iOS | 14+ | Full |
| Chrome Android | 90+ | Full |

#### 2.4.2 Screen Resolutions

| Category | Width Range | Layout |
|----------|-------------|--------|
| Mobile | < 640px | Single column, bottom navigation |
| Tablet | 640px - 1023px | Two column, collapsed sidebar |
| Desktop | 1024px - 1439px | Multi-column, full sidebar |
| Wide | ≥ 1440px | Multi-column, expanded layout |

#### 2.4.3 Network Requirements

| Requirement | Specification |
|-------------|---------------|
| Minimum Bandwidth | 1 Mbps |
| Recommended Bandwidth | 10 Mbps |
| Latency Tolerance | < 200ms for interactive operations |
| Offline Support | Limited (cached assets only) |

### 2.5 Design and Implementation Constraints

#### 2.5.1 Technical Constraints

| ID | Constraint | Rationale |
|----|------------|-----------|
| TC-001 | No build step required | Simplify deployment and reduce toolchain complexity |
| TC-002 | Vanilla JavaScript only | Avoid framework lock-in and reduce bundle size |
| TC-003 | Alpine.js 3.x for reactivity | Lightweight, declarative, HTML-first approach |
| TC-004 | CSS Custom Properties for theming | Native browser support, no preprocessing required |
| TC-005 | Maximum 100KB CSS (minified) | Performance budget for initial load |
| TC-006 | Maximum 50KB JS (minified) | Performance budget for initial load |

#### 2.5.2 Regulatory Constraints

| ID | Constraint | Standard |
|----|------------|----------|
| RC-001 | WCAG 2.1 AA compliance | Accessibility |
| RC-002 | GDPR compliance for user preferences | Data protection |
| RC-003 | No third-party tracking | Privacy |

#### 2.5.3 Development Constraints

| ID | Constraint | Source |
|----|------------|--------|
| DC-001 | VIBE Coding Rules compliance | REF-008 |
| DC-002 | No mocks or placeholders | VIBE Rule #1 |
| DC-003 | Real implementations only | VIBE Rule #4 |
| DC-004 | Complete context required | VIBE Rule #6 |

### 2.6 Assumptions and Dependencies

See Section 10 for detailed assumptions and dependencies.


---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 Design Token System

##### FR-DT-001: Token Definition
| Attribute | Value |
|-----------|-------|
| **ID** | FR-DT-001 |
| **Title** | CSS Custom Property Token Definition |
| **Priority** | P0 - Critical |
| **Description** | THE Design_System SHALL define all visual attributes as CSS custom properties in a single `somastack-tokens.css` file. |
| **Rationale** | Centralized tokens enable consistent theming and easy maintenance. |
| **Source** | Requirement 1.1 |
| **Verification** | Inspection of CSS file; automated token validation test |

##### FR-DT-002: Token Propagation
| Attribute | Value |
|-----------|-------|
| **ID** | FR-DT-002 |
| **Title** | Token Value Propagation |
| **Priority** | P0 - Critical |
| **Description** | WHEN a token value changes at `:root` level THEN the Design_System SHALL propagate the change to all components using that token without code modifications. |
| **Rationale** | CSS cascade ensures automatic propagation. |
| **Source** | Requirement 1.2 |
| **Verification** | Property-based test: change token, verify all usages update |

##### FR-DT-003: Color Palettes
| Attribute | Value |
|-----------|-------|
| **ID** | FR-DT-003 |
| **Title** | Color Palette Definition |
| **Priority** | P0 - Critical |
| **Description** | THE Design_System SHALL define 5 color palettes: neutral (10 shades), primary (5 shades), success (3 shades), warning (3 shades), error (3 shades). |
| **Rationale** | Comprehensive palette covers all UI states and semantic meanings. |
| **Source** | Requirement 1.3 |
| **Verification** | CSS inspection; color contrast validation |

##### FR-DT-004: Spacing Scale
| Attribute | Value |
|-----------|-------|
| **ID** | FR-DT-004 |
| **Title** | Spacing Scale Definition |
| **Priority** | P0 - Critical |
| **Description** | THE Design_System SHALL define 8 spacing scale values: 4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px as CSS custom properties. |
| **Rationale** | Consistent spacing creates visual rhythm and hierarchy. |
| **Source** | Requirement 1.4 |
| **Verification** | CSS inspection |

##### FR-DT-005: Typography Scale
| Attribute | Value |
|-----------|-------|
| **ID** | FR-DT-005 |
| **Title** | Typography Scale Definition |
| **Priority** | P0 - Critical |
| **Description** | THE Design_System SHALL define 6 typography scale values: xs (12px), sm (14px), base (16px), lg (18px), xl (20px), 2xl (24px). |
| **Rationale** | Limited scale ensures typographic consistency. |
| **Source** | Requirement 1.5 |
| **Verification** | CSS inspection |

##### FR-DT-006: Font Family
| Attribute | Value |
|-----------|-------|
| **ID** | FR-DT-006 |
| **Title** | Primary Font Family |
| **Priority** | P0 - Critical |
| **Description** | THE Design_System SHALL use Geist font family as primary with system-ui, -apple-system, sans-serif as fallback chain. |
| **Rationale** | Geist provides modern, readable typography; fallbacks ensure graceful degradation. |
| **Source** | Requirement 1.6 |
| **Verification** | CSS inspection; visual verification |

##### FR-DT-007: Elevation Levels
| Attribute | Value |
|-----------|-------|
| **ID** | FR-DT-007 |
| **Title** | Shadow Elevation Levels |
| **Priority** | P1 - High |
| **Description** | THE Design_System SHALL define 3 elevation levels using box-shadow: sm (subtle), md (medium), lg (prominent). |
| **Rationale** | Elevation creates depth hierarchy without heavy visual weight. |
| **Source** | Requirement 1.7 |
| **Verification** | CSS inspection; visual verification |

##### FR-DT-008: Border Radius Tokens
| Attribute | Value |
|-----------|-------|
| **ID** | FR-DT-008 |
| **Title** | Border Radius Token Definition |
| **Priority** | P1 - High |
| **Description** | THE Design_System SHALL define border-radius tokens: none (0), sm (4px), md (8px), lg (12px), full (9999px). |
| **Rationale** | Consistent border radius creates cohesive component appearance. |
| **Source** | Requirement 1.8 |
| **Verification** | CSS inspection |

#### 3.1.2 Glassmorphism Surface System

##### FR-GL-001: Backdrop Blur
| Attribute | Value |
|-----------|-------|
| **ID** | FR-GL-001 |
| **Title** | Glassmorphism Backdrop Blur |
| **Priority** | P0 - Critical |
| **Description** | THE Design_System SHALL implement glassmorphism surfaces with `backdrop-filter: blur(12px)`. |
| **Rationale** | Blur effect creates frosted glass appearance. |
| **Source** | Requirement 2.1 |
| **Verification** | CSS inspection; visual verification |

##### FR-GL-002: Surface Levels
| Attribute | Value |
|-----------|-------|
| **ID** | FR-GL-002 |
| **Title** | Surface Level Definition |
| **Priority** | P0 - Critical |
| **Description** | THE Design_System SHALL define 3 surface levels: surface-1 (cards, 100% opacity), surface-2 (modals, 80% opacity), surface-3 (overlays, 60% opacity). |
| **Rationale** | Layered surfaces create depth without obscuring content. |
| **Source** | Requirement 2.2 |
| **Verification** | CSS inspection |

##### FR-GL-003: Surface Borders
| Attribute | Value |
|-----------|-------|
| **ID** | FR-GL-003 |
| **Title** | Surface Border Styling |
| **Priority** | P1 - High |
| **Description** | WHEN displaying a surface THEN the Design_System SHALL apply a subtle border with 10% opacity. |
| **Rationale** | Subtle borders define surface boundaries without harsh lines. |
| **Source** | Requirement 2.3 |
| **Verification** | CSS inspection |

##### FR-GL-004: WCAG Contrast
| Attribute | Value |
|-----------|-------|
| **ID** | FR-GL-004 |
| **Title** | WCAG AA Contrast Compliance |
| **Priority** | P0 - Critical |
| **Description** | THE Design_System SHALL maintain minimum 4.5:1 contrast ratio for normal text and 3:1 for large text on all surfaces. |
| **Rationale** | WCAG 2.1 AA compliance ensures accessibility. |
| **Source** | Requirement 2.4 |
| **Verification** | Automated contrast ratio testing |

##### FR-GL-005: Hover States
| Attribute | Value |
|-----------|-------|
| **ID** | FR-GL-005 |
| **Title** | Interactive Surface Hover |
| **Priority** | P1 - High |
| **Description** | WHEN a surface contains interactive elements THEN the Design_System SHALL apply hover state with 5% opacity increase. |
| **Rationale** | Subtle hover feedback indicates interactivity. |
| **Source** | Requirement 2.6 |
| **Verification** | Visual verification; E2E test |

#### 3.1.3 Role-Based Access Control

##### FR-RBAC-001: Access Levels
| Attribute | Value |
|-----------|-------|
| **ID** | FR-RBAC-001 |
| **Title** | User Access Level Support |
| **Priority** | P0 - Critical |
| **Description** | THE Role_Manager SHALL support 3 access levels: Admin (full access), Operator (operational access), Viewer (read-only access). |
| **Rationale** | Role-based access ensures appropriate UI visibility. |
| **Source** | Requirement 3.1 |
| **Verification** | Unit test; E2E test |

##### FR-RBAC-002: Admin UI Visibility
| Attribute | Value |
|-----------|-------|
| **ID** | FR-RBAC-002 |
| **Title** | Admin Role UI Elements |
| **Priority** | P0 - Critical |
| **Description** | WHEN a user has Admin role THEN the UI SHALL display all management controls including create, edit, delete, and approve actions. |
| **Rationale** | Admins require full control capabilities. |
| **Source** | Requirement 3.2 |
| **Verification** | E2E test with admin JWT |

##### FR-RBAC-003: Operator UI Visibility
| Attribute | Value |
|-----------|-------|
| **ID** | FR-RBAC-003 |
| **Title** | Operator Role UI Elements |
| **Priority** | P0 - Critical |
| **Description** | WHEN a user has Operator role THEN the UI SHALL display operational controls including view, execute, and monitor actions, but NOT delete or approve actions. |
| **Rationale** | Operators need operational access without destructive capabilities. |
| **Source** | Requirement 3.3 |
| **Verification** | E2E test with operator JWT |

##### FR-RBAC-004: Viewer UI Visibility
| Attribute | Value |
|-----------|-------|
| **ID** | FR-RBAC-004 |
| **Title** | Viewer Role UI Elements |
| **Priority** | P0 - Critical |
| **Description** | WHEN a user has Viewer role THEN the UI SHALL display read-only views with view and monitor actions only. |
| **Rationale** | Viewers should not have access to modify operations. |
| **Source** | Requirement 3.4 |
| **Verification** | E2E test with viewer JWT |

##### FR-RBAC-005: JWT Role Extraction
| Attribute | Value |
|-----------|-------|
| **ID** | FR-RBAC-005 |
| **Title** | JWT Token Role Parsing |
| **Priority** | P0 - Critical |
| **Description** | THE Role_Manager SHALL retrieve role information from the `role` claim in the JWT token payload. |
| **Rationale** | JWT provides secure, stateless role transmission. |
| **Source** | Requirement 3.5 |
| **Verification** | Unit test with various JWT payloads |

##### FR-RBAC-006: Default Role Fallback
| Attribute | Value |
|-----------|-------|
| **ID** | FR-RBAC-006 |
| **Title** | Missing Role Default Behavior |
| **Priority** | P0 - Critical |
| **Description** | WHEN role information is unavailable or JWT is invalid THEN the UI SHALL default to Viewer mode with read-only access. |
| **Rationale** | Fail-safe default prevents unauthorized access. |
| **Source** | Requirement 3.6 |
| **Verification** | Unit test with invalid/missing JWT |

##### FR-RBAC-007: Alpine Store Integration
| Attribute | Value |
|-----------|-------|
| **ID** | FR-RBAC-007 |
| **Title** | Role State in Alpine Store |
| **Priority** | P0 - Critical |
| **Description** | THE Role_Manager SHALL cache role state in Alpine.js store (`$store.auth`) for reactive UI updates. |
| **Rationale** | Alpine store enables reactive role-based rendering. |
| **Source** | Requirement 3.7 |
| **Verification** | Unit test; integration test |

##### FR-RBAC-008: Admin Control Directive
| Attribute | Value |
|-----------|-------|
| **ID** | FR-RBAC-008 |
| **Title** | Admin-Only Control Visibility |
| **Priority** | P1 - High |
| **Description** | WHEN displaying admin-only controls THEN the UI SHALL use `x-show="$store.auth.isAdmin"` Alpine directive. |
| **Rationale** | Declarative visibility simplifies role-based UI. |
| **Source** | Requirement 3.8 |
| **Verification** | Code inspection; E2E test |


#### 3.1.4 Navigation System

##### FR-NAV-001: Collapsible Sidebar
| Attribute | Value |
|-----------|-------|
| **ID** | FR-NAV-001 |
| **Title** | Sidebar Collapse Functionality |
| **Priority** | P0 - Critical |
| **Description** | THE Navigation_Component SHALL implement a collapsible sidebar with icon + label format in expanded state and icon-only with tooltips in collapsed state. |
| **Rationale** | Collapsible sidebar maximizes content area while maintaining navigation access. |
| **Source** | Requirement 4.1, 4.2 |
| **Verification** | E2E test |

##### FR-NAV-002: Active Section Highlight
| Attribute | Value |
|-----------|-------|
| **ID** | FR-NAV-002 |
| **Title** | Active Navigation Highlight |
| **Priority** | P0 - Critical |
| **Description** | THE Navigation_Component SHALL highlight the active section with accent color background. |
| **Rationale** | Visual indication of current location aids navigation. |
| **Source** | Requirement 4.3 |
| **Verification** | Visual verification; E2E test |

##### FR-NAV-003: Category Grouping
| Attribute | Value |
|-----------|-------|
| **ID** | FR-NAV-003 |
| **Title** | Navigation Category Groups |
| **Priority** | P1 - High |
| **Description** | THE Navigation_Component SHALL group items by category: Main, Tools, Settings, Admin. |
| **Rationale** | Logical grouping improves navigation discoverability. |
| **Source** | Requirement 4.4 |
| **Verification** | Visual verification |

##### FR-NAV-004: Keyboard Navigation
| Attribute | Value |
|-----------|-------|
| **ID** | FR-NAV-004 |
| **Title** | Navigation Keyboard Support |
| **Priority** | P0 - Critical |
| **Description** | THE Navigation_Component SHALL support keyboard navigation using Tab (focus), Enter (activate), and Arrow keys (navigate within groups). |
| **Rationale** | Keyboard navigation is essential for accessibility. |
| **Source** | Requirement 4.6 |
| **Verification** | E2E test with keyboard-only navigation |

##### FR-NAV-005: State Persistence
| Attribute | Value |
|-----------|-------|
| **ID** | FR-NAV-005 |
| **Title** | Sidebar State Persistence |
| **Priority** | P1 - High |
| **Description** | THE Navigation_Component SHALL persist collapsed/expanded state to localStorage and restore on page load. |
| **Rationale** | Persistent state respects user preference. |
| **Source** | Requirement 4.7 |
| **Verification** | E2E test with page reload |

##### FR-NAV-006: Notification Badges
| Attribute | Value |
|-----------|-------|
| **ID** | FR-NAV-006 |
| **Title** | Navigation Item Badges |
| **Priority** | P1 - High |
| **Description** | THE Navigation_Component SHALL display notification badges for items requiring attention. |
| **Rationale** | Badges draw attention to actionable items. |
| **Source** | Requirement 4.8 |
| **Verification** | Visual verification; unit test |

#### 3.1.5 Stats Card Component

##### FR-SC-001: Card Content
| Attribute | Value |
|-----------|-------|
| **ID** | FR-SC-001 |
| **Title** | Stats Card Content Elements |
| **Priority** | P0 - Critical |
| **Description** | THE Stats_Card_Component SHALL display: icon, metric value, label, and trend indicator. |
| **Rationale** | Complete information enables quick status assessment. |
| **Source** | Requirement 5.1 |
| **Verification** | Visual verification; unit test |

##### FR-SC-002: Trend Indicator
| Attribute | Value |
|-----------|-------|
| **ID** | FR-SC-002 |
| **Title** | Metric Trend Display |
| **Priority** | P0 - Critical |
| **Description** | WHEN metric has changed THEN the Stats_Card_Component SHALL display percentage change with up arrow (positive), down arrow (negative), or dash (neutral). |
| **Rationale** | Trend indicators show metric direction at a glance. |
| **Source** | Requirement 5.2 |
| **Verification** | Unit test with various trend values |

##### FR-SC-003: Trend Color Coding
| Attribute | Value |
|-----------|-------|
| **ID** | FR-SC-003 |
| **Title** | Trend Color Semantics |
| **Priority** | P1 - High |
| **Description** | THE Stats_Card_Component SHALL use subtle color coding for trend: green (positive), red (negative), grey (neutral). |
| **Rationale** | Color reinforces trend direction. |
| **Source** | Requirement 5.3 |
| **Verification** | Visual verification |

##### FR-SC-004: Number Formatting
| Attribute | Value |
|-----------|-------|
| **ID** | FR-SC-004 |
| **Title** | Large Number Formatting |
| **Priority** | P0 - Critical |
| **Description** | WHEN displaying numbers >= 1000 THEN the Stats_Card_Component SHALL format with K (thousands), M (millions), B (billions) suffixes with 1-3 significant digits. |
| **Rationale** | Formatted numbers are more readable. |
| **Source** | Requirement 5.5 |
| **Verification** | Unit test with various number ranges |

##### FR-SC-005: Value Animation
| Attribute | Value |
|-----------|-------|
| **ID** | FR-SC-005 |
| **Title** | Value Change Animation |
| **Priority** | P1 - High |
| **Description** | THE Stats_Card_Component SHALL animate value changes with 300ms CSS transition. |
| **Rationale** | Animation draws attention to changes. |
| **Source** | Requirement 5.6 |
| **Verification** | Visual verification |

#### 3.1.6 Data Table Component

##### FR-DT-001: Sortable Columns
| Attribute | Value |
|-----------|-------|
| **ID** | FR-TBL-001 |
| **Title** | Column Sorting |
| **Priority** | P0 - Critical |
| **Description** | THE Data_Table_Component SHALL display columns with sortable headers. WHEN a column header is clicked THEN the component SHALL sort by that column, toggling between ascending and descending order. |
| **Rationale** | Sorting enables users to organize data by relevance. |
| **Source** | Requirement 6.1, 6.2 |
| **Verification** | E2E test |

##### FR-TBL-002: Row Selection
| Attribute | Value |
|-----------|-------|
| **ID** | FR-TBL-002 |
| **Title** | Checkbox Row Selection |
| **Priority** | P1 - High |
| **Description** | THE Data_Table_Component SHALL support row selection with checkboxes, including select-all functionality. |
| **Rationale** | Bulk selection enables batch operations. |
| **Source** | Requirement 6.3 |
| **Verification** | E2E test |

##### FR-TBL-003: Status Badges
| Attribute | Value |
|-----------|-------|
| **ID** | FR-TBL-003 |
| **Title** | Status Badge Display |
| **Priority** | P0 - Critical |
| **Description** | THE Data_Table_Component SHALL display status badges with semantic colors: approved (green), pending (amber), rejected (red). |
| **Rationale** | Color-coded badges enable quick status identification. |
| **Source** | Requirement 6.4 |
| **Verification** | Visual verification |

##### FR-TBL-004: Action Buttons
| Attribute | Value |
|-----------|-------|
| **ID** | FR-TBL-004 |
| **Title** | Row Action Buttons |
| **Priority** | P0 - Critical |
| **Description** | THE Data_Table_Component SHALL support action buttons per row: View (all roles), Edit (operator+), Delete (admin only), with visibility controlled by user role. |
| **Rationale** | Role-based actions enforce access control. |
| **Source** | Requirement 6.5 |
| **Verification** | E2E test with different roles |

##### FR-TBL-005: Pagination
| Attribute | Value |
|-----------|-------|
| **ID** | FR-TBL-005 |
| **Title** | Table Pagination |
| **Priority** | P0 - Critical |
| **Description** | WHEN table has more than pageSize rows (default 10) THEN the Data_Table_Component SHALL implement pagination with page navigation controls. |
| **Rationale** | Pagination improves performance and usability for large datasets. |
| **Source** | Requirement 6.6 |
| **Verification** | E2E test with >10 rows |

##### FR-TBL-006: Search Filter
| Attribute | Value |
|-----------|-------|
| **ID** | FR-TBL-006 |
| **Title** | Table Search/Filter |
| **Priority** | P1 - High |
| **Description** | THE Data_Table_Component SHALL support search/filter functionality that filters visible rows based on search query. |
| **Rationale** | Search enables quick data location. |
| **Source** | Requirement 6.7 |
| **Verification** | E2E test |

##### FR-TBL-007: Loading State
| Attribute | Value |
|-----------|-------|
| **ID** | FR-TBL-007 |
| **Title** | Table Loading Skeleton |
| **Priority** | P1 - High |
| **Description** | THE Data_Table_Component SHALL display loading skeleton during data fetch. |
| **Rationale** | Loading state provides feedback during async operations. |
| **Source** | Requirement 6.8 |
| **Verification** | Visual verification |

##### FR-TBL-008: Empty State
| Attribute | Value |
|-----------|-------|
| **ID** | FR-TBL-008 |
| **Title** | Table Empty State |
| **Priority** | P1 - High |
| **Description** | WHEN no data exists THEN the Data_Table_Component SHALL display empty state with helpful message. |
| **Rationale** | Empty state guides users on next actions. |
| **Source** | Requirement 6.9 |
| **Verification** | Visual verification |

#### 3.1.7 Status Indicator Component

##### FR-SI-001: Health Dots
| Attribute | Value |
|-----------|-------|
| **ID** | FR-SI-001 |
| **Title** | Service Health Visualization |
| **Priority** | P0 - Critical |
| **Description** | THE Status_Indicator SHALL display service health with colored dots: green (healthy), amber (degraded), red (down), grey (unknown). |
| **Rationale** | Color-coded dots enable instant health assessment. |
| **Source** | Requirement 7.1 |
| **Verification** | Visual verification; unit test |

##### FR-SI-002: Update Latency
| Attribute | Value |
|-----------|-------|
| **ID** | FR-SI-002 |
| **Title** | Status Update Timing |
| **Priority** | P0 - Critical |
| **Description** | WHEN service status changes THEN the Status_Indicator SHALL update within 5 seconds. |
| **Rationale** | Near real-time updates enable timely response to issues. |
| **Source** | Requirement 7.2 |
| **Verification** | Integration test with timing assertion |

##### FR-SI-003: Timestamp Display
| Attribute | Value |
|-----------|-------|
| **ID** | FR-SI-003 |
| **Title** | Last Checked Timestamp |
| **Priority** | P1 - High |
| **Description** | THE Status_Indicator SHALL display last-checked timestamp in relative format (e.g., "2s ago"). |
| **Rationale** | Timestamp indicates data freshness. |
| **Source** | Requirement 7.3 |
| **Verification** | Visual verification |

##### FR-SI-004: Pulse Animation
| Attribute | Value |
|-----------|-------|
| **ID** | FR-SI-004 |
| **Title** | Active State Animation |
| **Priority** | P1 - High |
| **Description** | THE Status_Indicator SHALL support pulse animation for active/processing states. |
| **Rationale** | Animation indicates ongoing activity. |
| **Source** | Requirement 7.4 |
| **Verification** | Visual verification |

##### FR-SI-005: Detail Tooltip
| Attribute | Value |
|-----------|-------|
| **ID** | FR-SI-005 |
| **Title** | Status Detail Tooltip |
| **Priority** | P1 - High |
| **Description** | WHEN hovering over status THEN the Status_Indicator SHALL display detailed tooltip with latency, status, and component details. |
| **Rationale** | Tooltip provides detailed information on demand. |
| **Source** | Requirement 7.5 |
| **Verification** | E2E test |

##### FR-SI-006: Health Endpoint Integration
| Attribute | Value |
|-----------|-------|
| **ID** | FR-SI-006 |
| **Title** | Health API Integration |
| **Priority** | P0 - Critical |
| **Description** | THE Status_Indicator SHALL integrate with `/health` endpoints of all SomaStack services: SomaBrain (9696), SomaFractalMemory (9595), SomaAgent01 (21016). |
| **Rationale** | Real health data ensures accurate status display. |
| **Source** | Requirement 7.6 |
| **Verification** | Integration test |

##### FR-SI-007: Service Coverage
| Attribute | Value |
|-----------|-------|
| **ID** | FR-SI-007 |
| **Title** | Infrastructure Status Display |
| **Priority** | P0 - Critical |
| **Description** | THE Status_Indicator SHALL display connection status for: PostgreSQL, Redis, Milvus, Kafka, Temporal. |
| **Rationale** | Infrastructure health is critical for system operation. |
| **Source** | Requirement 7.7 |
| **Verification** | Visual verification |


#### 3.1.8 Settings Panel

##### FR-SET-001: Tab Organization
| Attribute | Value |
|-----------|-------|
| **ID** | FR-SET-001 |
| **Title** | Settings Tab Structure |
| **Priority** | P0 - Critical |
| **Description** | THE Settings_Panel SHALL organize settings into tabs: General, Appearance, Notifications, Security, Admin. |
| **Rationale** | Tab organization improves settings discoverability. |
| **Source** | Requirement 8.1 |
| **Verification** | Visual verification |

##### FR-SET-002: Admin Tab Visibility
| Attribute | Value |
|-----------|-------|
| **ID** | FR-SET-002 |
| **Title** | Admin Tab Role Restriction |
| **Priority** | P0 - Critical |
| **Description** | WHEN user lacks Admin role THEN the Settings_Panel SHALL hide the Admin tab. |
| **Rationale** | Admin settings should only be visible to administrators. |
| **Source** | Requirement 8.2 |
| **Verification** | E2E test with non-admin role |

##### FR-SET-003: Client Persistence
| Attribute | Value |
|-----------|-------|
| **ID** | FR-SET-003 |
| **Title** | LocalStorage Settings Persistence |
| **Priority** | P0 - Critical |
| **Description** | THE Settings_Panel SHALL persist client-side preferences to localStorage. |
| **Rationale** | Local persistence enables offline preference retention. |
| **Source** | Requirement 8.3 |
| **Verification** | Unit test; E2E test with page reload |

##### FR-SET-004: Server Persistence
| Attribute | Value |
|-----------|-------|
| **ID** | FR-SET-004 |
| **Title** | API Settings Persistence |
| **Priority** | P1 - High |
| **Description** | THE Settings_Panel SHALL persist server-side preferences to backend API. |
| **Rationale** | Server persistence enables cross-device settings sync. |
| **Source** | Requirement 8.4 |
| **Verification** | Integration test |

##### FR-SET-005: Immediate Application
| Attribute | Value |
|-----------|-------|
| **ID** | FR-SET-005 |
| **Title** | Settings Immediate Effect |
| **Priority** | P0 - Critical |
| **Description** | WHEN a setting changes THEN the Settings_Panel SHALL apply immediately without page reload. |
| **Rationale** | Immediate feedback improves user experience. |
| **Source** | Requirement 8.5 |
| **Verification** | E2E test |

##### FR-SET-006: Input Validation
| Attribute | Value |
|-----------|-------|
| **ID** | FR-SET-006 |
| **Title** | Settings Input Validation |
| **Priority** | P0 - Critical |
| **Description** | THE Settings_Panel SHALL validate inputs before saving and reject invalid values with error messages. |
| **Rationale** | Validation prevents invalid configuration. |
| **Source** | Requirement 8.6 |
| **Verification** | Unit test; E2E test |

##### FR-SET-007: Save Feedback
| Attribute | Value |
|-----------|-------|
| **ID** | FR-SET-007 |
| **Title** | Settings Save Feedback |
| **Priority** | P1 - High |
| **Description** | THE Settings_Panel SHALL display success/error feedback after save operations via toast notification. |
| **Rationale** | Feedback confirms operation result. |
| **Source** | Requirement 8.7 |
| **Verification** | E2E test |

#### 3.1.9 Theme System

##### FR-TH-001: Color Schemes
| Attribute | Value |
|-----------|-------|
| **ID** | FR-TH-001 |
| **Title** | Light and Dark Theme Support |
| **Priority** | P0 - Critical |
| **Description** | THE Theme_Engine SHALL support light and dark color schemes with complete token definitions for each. |
| **Rationale** | Theme options accommodate user preferences and environments. |
| **Source** | Requirement 14.1 |
| **Verification** | Visual verification |

##### FR-TH-002: Switch Performance
| Attribute | Value |
|-----------|-------|
| **ID** | FR-TH-002 |
| **Title** | Theme Switch Timing |
| **Priority** | P0 - Critical |
| **Description** | WHEN user toggles theme THEN the Theme_Engine SHALL apply changes within 100ms. |
| **Rationale** | Fast switching provides responsive feel. |
| **Source** | Requirement 14.2 |
| **Verification** | Performance test |

##### FR-TH-003: Preference Persistence
| Attribute | Value |
|-----------|-------|
| **ID** | FR-TH-003 |
| **Title** | Theme Preference Storage |
| **Priority** | P0 - Critical |
| **Description** | THE Theme_Engine SHALL persist theme preference to localStorage and restore on page load. |
| **Rationale** | Persistent preference respects user choice. |
| **Source** | Requirement 14.3 |
| **Verification** | E2E test with page reload |

##### FR-TH-004: System Preference
| Attribute | Value |
|-----------|-------|
| **ID** | FR-TH-004 |
| **Title** | System Theme Detection |
| **Priority** | P1 - High |
| **Description** | THE Theme_Engine SHALL respect `prefers-color-scheme` system preference by default when no user preference is set. |
| **Rationale** | System preference provides sensible default. |
| **Source** | Requirement 14.4 |
| **Verification** | E2E test with system preference |

##### FR-TH-005: Transition Animation
| Attribute | Value |
|-----------|-------|
| **ID** | FR-TH-005 |
| **Title** | Theme Transition Effect |
| **Priority** | P1 - High |
| **Description** | THE Theme_Engine SHALL provide smooth transition animation (300ms) between themes. |
| **Rationale** | Smooth transition prevents jarring visual change. |
| **Source** | Requirement 14.5 |
| **Verification** | Visual verification |

##### FR-TH-006: Component Rendering
| Attribute | Value |
|-----------|-------|
| **ID** | FR-TH-006 |
| **Title** | Theme Component Compatibility |
| **Priority** | P0 - Critical |
| **Description** | THE Theme_Engine SHALL ensure all components render correctly in both light and dark themes. |
| **Rationale** | Complete theme support ensures consistent experience. |
| **Source** | Requirement 14.6 |
| **Verification** | Visual regression test |

#### 3.1.10 Modal and Dialog System

##### FR-MOD-001: Size Variants
| Attribute | Value |
|-----------|-------|
| **ID** | FR-MOD-001 |
| **Title** | Modal Size Options |
| **Priority** | P0 - Critical |
| **Description** | THE Modal_Component SHALL support sizes: sm (400px), md (600px), lg (800px), full (100%). |
| **Rationale** | Size variants accommodate different content needs. |
| **Source** | Requirement 17.1 |
| **Verification** | Visual verification |

##### FR-MOD-002: Focus Trap
| Attribute | Value |
|-----------|-------|
| **ID** | FR-MOD-002 |
| **Title** | Modal Focus Management |
| **Priority** | P0 - Critical |
| **Description** | THE Modal_Component SHALL trap focus within modal when open, preventing focus from escaping to background content. |
| **Rationale** | Focus trap is essential for accessibility. |
| **Source** | Requirement 17.2 |
| **Verification** | E2E test with keyboard navigation |

##### FR-MOD-003: Escape Close
| Attribute | Value |
|-----------|-------|
| **ID** | FR-MOD-003 |
| **Title** | Escape Key Dismissal |
| **Priority** | P0 - Critical |
| **Description** | THE Modal_Component SHALL close on Escape key press. |
| **Rationale** | Escape key is standard modal dismissal pattern. |
| **Source** | Requirement 17.3 |
| **Verification** | E2E test |

##### FR-MOD-004: Backdrop Close
| Attribute | Value |
|-----------|-------|
| **ID** | FR-MOD-004 |
| **Title** | Backdrop Click Dismissal |
| **Priority** | P1 - High |
| **Description** | THE Modal_Component SHALL close on backdrop click (configurable per modal). |
| **Rationale** | Backdrop click is intuitive dismissal pattern. |
| **Source** | Requirement 17.4 |
| **Verification** | E2E test |

##### FR-MOD-005: Animation
| Attribute | Value |
|-----------|-------|
| **ID** | FR-MOD-005 |
| **Title** | Modal Open/Close Animation |
| **Priority** | P1 - High |
| **Description** | THE Modal_Component SHALL animate open/close with fade and scale effect (200ms duration). |
| **Rationale** | Animation provides visual continuity. |
| **Source** | Requirement 17.5 |
| **Verification** | Visual verification |

##### FR-MOD-006: Scroll Lock
| Attribute | Value |
|-----------|-------|
| **ID** | FR-MOD-006 |
| **Title** | Body Scroll Prevention |
| **Priority** | P0 - Critical |
| **Description** | THE Modal_Component SHALL prevent body scroll when open. |
| **Rationale** | Scroll lock maintains modal focus. |
| **Source** | Requirement 17.6 |
| **Verification** | E2E test |

##### FR-MOD-007: Stacked Modals
| Attribute | Value |
|-----------|-------|
| **ID** | FR-MOD-007 |
| **Title** | Modal Stacking Support |
| **Priority** | P1 - High |
| **Description** | THE Modal_Component SHALL support stacked modals with proper z-index management. |
| **Rationale** | Stacked modals enable nested workflows. |
| **Source** | Requirement 17.7 |
| **Verification** | E2E test with multiple modals |

#### 3.1.11 Toast Notification System

##### FR-TST-001: Variants
| Attribute | Value |
|-----------|-------|
| **ID** | FR-TST-001 |
| **Title** | Toast Notification Variants |
| **Priority** | P0 - Critical |
| **Description** | THE Toast_Component SHALL support 4 variants: info (blue), success (green), warning (amber), error (red). |
| **Rationale** | Variants communicate message severity. |
| **Source** | Requirement 15.6 |
| **Verification** | Visual verification |

##### FR-TST-002: Auto Dismiss
| Attribute | Value |
|-----------|-------|
| **ID** | FR-TST-002 |
| **Title** | Toast Auto-Dismissal |
| **Priority** | P0 - Critical |
| **Description** | THE Toast_Component SHALL auto-dismiss after 5 seconds (configurable). |
| **Rationale** | Auto-dismiss prevents notification accumulation. |
| **Source** | Requirement 15.7 |
| **Verification** | E2E test with timing |

##### FR-TST-003: Manual Dismiss
| Attribute | Value |
|-----------|-------|
| **ID** | FR-TST-003 |
| **Title** | Toast Manual Dismissal |
| **Priority** | P1 - High |
| **Description** | THE Toast_Component SHALL provide close button for manual dismissal. |
| **Rationale** | Manual dismiss enables immediate removal. |
| **Source** | Requirement 15.5 |
| **Verification** | E2E test |

##### FR-TST-004: Stacking
| Attribute | Value |
|-----------|-------|
| **ID** | FR-TST-004 |
| **Title** | Toast Stacking Behavior |
| **Priority** | P1 - High |
| **Description** | THE Toast_Component SHALL stack multiple toasts vertically with newest at top. |
| **Rationale** | Stacking prevents toast overlap. |
| **Source** | Requirement 15.5 |
| **Verification** | Visual verification |

#### 3.1.12 Form Components

##### FR-FRM-001: Input Types
| Attribute | Value |
|-----------|-------|
| **ID** | FR-FRM-001 |
| **Title** | Form Input Component Types |
| **Priority** | P0 - Critical |
| **Description** | THE Form_System SHALL provide: text input, textarea, select, checkbox, radio, toggle, slider, color picker. |
| **Rationale** | Complete input set covers all form needs. |
| **Source** | Requirement 16.1 |
| **Verification** | Visual verification |

##### FR-FRM-002: Inline Validation
| Attribute | Value |
|-----------|-------|
| **ID** | FR-FRM-002 |
| **Title** | Inline Validation Errors |
| **Priority** | P0 - Critical |
| **Description** | THE Form_System SHALL display validation errors inline below inputs with error styling. |
| **Rationale** | Inline errors provide immediate feedback. |
| **Source** | Requirement 16.2 |
| **Verification** | E2E test |

##### FR-FRM-003: Input States
| Attribute | Value |
|-----------|-------|
| **ID** | FR-FRM-003 |
| **Title** | Input State Support |
| **Priority** | P0 - Critical |
| **Description** | THE Form_System SHALL support disabled and readonly states with appropriate visual styling. |
| **Rationale** | State styling communicates input availability. |
| **Source** | Requirement 16.3 |
| **Verification** | Visual verification |

##### FR-FRM-004: Helper Text
| Attribute | Value |
|-----------|-------|
| **ID** | FR-FRM-004 |
| **Title** | Input Helper Text |
| **Priority** | P1 - High |
| **Description** | THE Form_System SHALL support placeholder text and helper text below inputs. |
| **Rationale** | Helper text provides input guidance. |
| **Source** | Requirement 16.4 |
| **Verification** | Visual verification |

##### FR-FRM-005: Focus Ring
| Attribute | Value |
|-----------|-------|
| **ID** | FR-FRM-005 |
| **Title** | Input Focus Indicator |
| **Priority** | P0 - Critical |
| **Description** | WHEN input is focused THEN the Form_System SHALL display focus ring with accent color. |
| **Rationale** | Focus ring indicates active input. |
| **Source** | Requirement 16.5 |
| **Verification** | Visual verification; E2E test |

##### FR-FRM-006: Form Validation
| Attribute | Value |
|-----------|-------|
| **ID** | FR-FRM-006 |
| **Title** | Form-Level Validation |
| **Priority** | P0 - Critical |
| **Description** | THE Form_System SHALL support form-level validation before submission. |
| **Rationale** | Form validation prevents invalid submissions. |
| **Source** | Requirement 16.6 |
| **Verification** | E2E test |

##### FR-FRM-007: Alpine Integration
| Attribute | Value |
|-----------|-------|
| **ID** | FR-FRM-007 |
| **Title** | Alpine.js Form Binding |
| **Priority** | P0 - Critical |
| **Description** | THE Form_System SHALL integrate with Alpine.js for reactive state management using x-model directive. |
| **Rationale** | Alpine integration enables reactive forms. |
| **Source** | Requirement 16.7 |
| **Verification** | Unit test |


---

## 4. System Features

### 4.1 Feature: Design Token Management (PF-001)

#### 4.1.1 Description
Centralized CSS custom properties system that defines all visual attributes for the SomaStack UI.

#### 4.1.2 Stimulus/Response Sequences

| Stimulus | Response |
|----------|----------|
| Page load | Design tokens loaded from CSS file |
| Token value change | All components using token update automatically |
| Theme switch | Token values updated to new theme values |

#### 4.1.3 Functional Requirements
- FR-DT-001 through FR-DT-008

### 4.2 Feature: Theme Switching (PF-002)

#### 4.2.1 Description
Light/dark/system theme support with persistence and smooth transitions.

#### 4.2.2 Stimulus/Response Sequences

| Stimulus | Response |
|----------|----------|
| User clicks theme toggle | Theme switches within 100ms |
| Page load | Previous theme preference restored |
| System preference changes | Theme updates if set to "system" |

#### 4.2.3 Functional Requirements
- FR-TH-001 through FR-TH-006

### 4.3 Feature: Role-Based UI Control (PF-003)

#### 4.3.1 Description
Dynamic UI element visibility based on user roles extracted from JWT tokens.

#### 4.3.2 Stimulus/Response Sequences

| Stimulus | Response |
|----------|----------|
| User authenticates | Role extracted from JWT, UI updates |
| JWT expires | UI reverts to viewer mode |
| Role changes | UI elements show/hide accordingly |

#### 4.3.3 Functional Requirements
- FR-RBAC-001 through FR-RBAC-008

### 4.4 Feature: Status Monitoring (PF-006)

#### 4.4.1 Description
Real-time service health visualization with polling and status indicators.

#### 4.4.2 Stimulus/Response Sequences

| Stimulus | Response |
|----------|----------|
| Page load | Health check initiated for all services |
| Poll interval (5s) | Health status refreshed |
| Service status change | Indicator color updates within 5s |
| User hovers status | Detailed tooltip displayed |

#### 4.4.3 Functional Requirements
- FR-SI-001 through FR-SI-007

### 4.5 Feature: Agent Dashboard (PF-011)

#### 4.5.1 Description
Specialized dashboard for agent management with cognitive metrics, neuromodulator visualization, and FSM state display.

#### 4.5.2 Stimulus/Response Sequences

| Stimulus | Response |
|----------|----------|
| Dashboard load | Agent metrics fetched and displayed |
| Agent state change | Dashboard updates in real-time |
| User clicks agent | Detail panel opens |
| Reasoning stream | Real-time text display |

#### 4.5.3 Functional Requirements
- FR-AGT-001: Agent metrics display
- FR-AGT-002: Neuromodulator gauges
- FR-AGT-003: FSM state visualization
- FR-AGT-004: Reasoning stream display
- FR-AGT-005: Conversation history
- FR-AGT-006: Tool execution monitoring
- FR-AGT-007: Memory browser integration

### 4.6 Feature: Memory Browser (PF-012)

#### 4.6.1 Description
Interface for browsing, searching, and managing agent memories.

#### 4.6.2 Stimulus/Response Sequences

| Stimulus | Response |
|----------|----------|
| Browser load | Memories fetched and displayed |
| User searches | Results filtered by query |
| User clicks memory | Detail panel opens |
| Admin deletes memory | Memory removed, list updated |

#### 4.6.3 Functional Requirements
- FR-MEM-001: Card/list view toggle
- FR-MEM-002: Search by content/coordinate/metadata
- FR-MEM-003: Memory type badges
- FR-MEM-004: Age and decay display
- FR-MEM-005: Detail panel
- FR-MEM-006: Admin delete capability
- FR-MEM-007: Similarity score display

### 4.7 Feature: Voice Interface (PF-013)

#### 4.7.1 Description
Visual feedback components for voice interactions including waveform, transcription, and playback.

#### 4.7.2 Stimulus/Response Sequences

| Stimulus | Response |
|----------|----------|
| Recording starts | Waveform visualization begins |
| Speech detected | Real-time transcription displayed |
| TTS playback | Progress indicator shown |
| Voice processing | Animated indicator displayed |

#### 4.7.3 Functional Requirements
- FR-VOI-001: Waveform visualization
- FR-VOI-002: Real-time transcription
- FR-VOI-003: TTS progress indicator
- FR-VOI-004: PTT and VAD mode support
- FR-VOI-005: Processing animation
- FR-VOI-006: Connection status display

---

## 5. External Interface Requirements

### 5.1 User Interfaces

#### 5.1.1 UI-001: Main Application Layout

| Attribute | Specification |
|-----------|---------------|
| **ID** | UI-001 |
| **Name** | Main Application Layout |
| **Description** | Primary layout structure with sidebar, header, main content, and footer |
| **Components** | Sidebar navigation, header bar, main content area, footer |
| **Responsive Behavior** | Sidebar collapses on tablet, becomes bottom nav on mobile |

#### 5.1.2 UI-002: Dashboard View

| Attribute | Specification |
|-----------|---------------|
| **ID** | UI-002 |
| **Name** | Dashboard View |
| **Description** | Overview dashboard with stats cards, status indicators, and activity feed |
| **Components** | Stats cards grid, status panel, activity list, quick actions |
| **Data Sources** | Health APIs, metrics APIs, activity APIs |

#### 5.1.3 UI-003: Data Management View

| Attribute | Specification |
|-----------|---------------|
| **ID** | UI-003 |
| **Name** | Data Management View |
| **Description** | Table-based data management with CRUD operations |
| **Components** | Data table, search/filter, action buttons, pagination |
| **Role Restrictions** | Edit/Delete visible only to authorized roles |

#### 5.1.4 UI-004: Settings View

| Attribute | Specification |
|-----------|---------------|
| **ID** | UI-004 |
| **Name** | Settings View |
| **Description** | Tabbed settings interface for user and system configuration |
| **Components** | Tab navigation, form inputs, save/cancel buttons |
| **Role Restrictions** | Admin tab visible only to administrators |

### 5.2 Hardware Interfaces

No direct hardware interfaces. All hardware interaction through browser APIs.

### 5.3 Software Interfaces

#### 5.3.1 SI-001: Health Check API

| Attribute | Specification |
|-----------|---------------|
| **ID** | SI-001 |
| **Name** | Health Check API |
| **Protocol** | HTTPS REST |
| **Endpoints** | GET /health (SomaBrain), GET /healthz (SomaFractalMemory), GET /v1/health (SomaAgent01) |
| **Response Format** | JSON with `ok` boolean and `components` object |
| **Poll Interval** | 5 seconds |

#### 5.3.2 SI-002: Settings API

| Attribute | Specification |
|-----------|---------------|
| **ID** | SI-002 |
| **Name** | Settings API |
| **Protocol** | HTTPS REST |
| **Endpoints** | GET /v1/settings, POST /v1/settings |
| **Authentication** | Bearer token (JWT) |
| **Request/Response** | JSON |

#### 5.3.3 SI-003: JWT Authentication

| Attribute | Specification |
|-----------|---------------|
| **ID** | SI-003 |
| **Name** | JWT Token Interface |
| **Token Location** | localStorage key `soma_token` |
| **Required Claims** | `sub` (user ID), `role` (user role), `tenant_id` (tenant ID) |
| **Validation** | Client-side payload parsing (signature validation on server) |

### 5.4 Communication Interfaces

#### 5.4.1 CI-001: HTTPS Communication

| Attribute | Specification |
|-----------|---------------|
| **ID** | CI-001 |
| **Protocol** | HTTPS (TLS 1.2+) |
| **Port** | 443 |
| **Certificate** | Valid SSL certificate required |
| **CORS** | Configured for SomaStack domains |

#### 5.4.2 CI-002: WebSocket Communication

| Attribute | Specification |
|-----------|---------------|
| **ID** | CI-002 |
| **Protocol** | WSS (WebSocket Secure) |
| **Port** | 443 |
| **Use Cases** | Voice streaming, real-time updates |
| **Heartbeat** | 20 second keepalive |


---

## 6. Non-Functional Requirements

### 6.1 Performance Requirements

#### 6.1.1 NFR-PERF-001: Initial Load Time

| Attribute | Specification |
|-----------|---------------|
| **ID** | NFR-PERF-001 |
| **Metric** | First Contentful Paint (FCP) |
| **Target** | < 1.5 seconds |
| **Measurement** | Lighthouse performance audit |
| **Conditions** | 3G network simulation, cold cache |

#### 6.1.2 NFR-PERF-002: Time to Interactive

| Attribute | Specification |
|-----------|---------------|
| **ID** | NFR-PERF-002 |
| **Metric** | Time to Interactive (TTI) |
| **Target** | < 3 seconds |
| **Measurement** | Lighthouse performance audit |
| **Conditions** | 3G network simulation, cold cache |

#### 6.1.3 NFR-PERF-003: Layout Stability

| Attribute | Specification |
|-----------|---------------|
| **ID** | NFR-PERF-003 |
| **Metric** | Cumulative Layout Shift (CLS) |
| **Target** | < 0.1 |
| **Measurement** | Lighthouse performance audit |
| **Conditions** | Full page load |

#### 6.1.4 NFR-PERF-004: Animation Performance

| Attribute | Specification |
|-----------|---------------|
| **ID** | NFR-PERF-004 |
| **Metric** | Animation frame rate |
| **Target** | 60 fps |
| **Measurement** | Chrome DevTools Performance panel |
| **Conditions** | All CSS animations and transitions |

#### 6.1.5 NFR-PERF-005: Theme Switch Time

| Attribute | Specification |
|-----------|---------------|
| **ID** | NFR-PERF-005 |
| **Metric** | Theme application time |
| **Target** | < 100ms |
| **Measurement** | Performance.now() timing |
| **Conditions** | Light to dark or dark to light switch |

#### 6.1.6 NFR-PERF-006: Bundle Size

| Attribute | Specification |
|-----------|---------------|
| **ID** | NFR-PERF-006 |
| **Metric** | Total bundle size (minified + gzipped) |
| **Target** | CSS < 30KB, JS < 20KB |
| **Measurement** | Build output analysis |
| **Conditions** | Production build |

### 6.2 Safety Requirements

Not applicable for UI system. Safety requirements handled by backend services.

### 6.3 Security Requirements

See Section 7 for detailed security requirements.

### 6.4 Software Quality Attributes

#### 6.4.1 NFR-QUAL-001: Maintainability

| Attribute | Specification |
|-----------|---------------|
| **ID** | NFR-QUAL-001 |
| **Metric** | Code modularity |
| **Target** | Single responsibility per component |
| **Measurement** | Code review |
| **Criteria** | Each component < 200 lines, clear interfaces |

#### 6.4.2 NFR-QUAL-002: Testability

| Attribute | Specification |
|-----------|---------------|
| **ID** | NFR-QUAL-002 |
| **Metric** | Test coverage |
| **Target** | > 80% for utility functions, > 60% for components |
| **Measurement** | Coverage report |
| **Criteria** | All public APIs tested |

#### 6.4.3 NFR-QUAL-003: Reusability

| Attribute | Specification |
|-----------|---------------|
| **ID** | NFR-QUAL-003 |
| **Metric** | Component reuse |
| **Target** | All components usable across SomaStack applications |
| **Measurement** | Integration testing |
| **Criteria** | No application-specific dependencies |

#### 6.4.4 NFR-QUAL-004: Portability

| Attribute | Specification |
|-----------|---------------|
| **ID** | NFR-QUAL-004 |
| **Metric** | Browser compatibility |
| **Target** | All supported browsers (Section 2.4.1) |
| **Measurement** | Cross-browser testing |
| **Criteria** | No browser-specific code without fallback |

### 6.5 Reliability Requirements

#### 6.5.1 NFR-REL-001: Graceful Degradation

| Attribute | Specification |
|-----------|---------------|
| **ID** | NFR-REL-001 |
| **Scenario** | JavaScript disabled |
| **Behavior** | Core content visible, interactive features disabled |
| **Measurement** | Manual testing |

#### 6.5.2 NFR-REL-002: Error Recovery

| Attribute | Specification |
|-----------|---------------|
| **ID** | NFR-REL-002 |
| **Scenario** | API request failure |
| **Behavior** | Error message displayed, retry option provided |
| **Measurement** | E2E testing |

#### 6.5.3 NFR-REL-003: Offline Behavior

| Attribute | Specification |
|-----------|---------------|
| **ID** | NFR-REL-003 |
| **Scenario** | Network disconnection |
| **Behavior** | Cached assets served, offline indicator shown |
| **Measurement** | Manual testing |

### 6.6 Availability Requirements

#### 6.6.1 NFR-AVAIL-001: Asset Availability

| Attribute | Specification |
|-----------|---------------|
| **ID** | NFR-AVAIL-001 |
| **Metric** | Static asset availability |
| **Target** | 99.9% uptime |
| **Measurement** | CDN/server monitoring |
| **Dependency** | Hosting infrastructure |

### 6.7 Scalability Requirements

#### 6.7.1 NFR-SCALE-001: Concurrent Users

| Attribute | Specification |
|-----------|---------------|
| **ID** | NFR-SCALE-001 |
| **Metric** | Concurrent UI sessions |
| **Target** | No client-side limit (server-dependent) |
| **Measurement** | Load testing |
| **Notes** | UI is stateless; scalability depends on backend |

---

## 7. Security Requirements

### 7.1 Authentication Requirements

#### 7.1.1 SEC-AUTH-001: Token Validation

| Attribute | Specification |
|-----------|---------------|
| **ID** | SEC-AUTH-001 |
| **Requirement** | THE UI SHALL validate JWT token presence before displaying protected content |
| **Implementation** | Check localStorage for `soma_token` on page load |
| **Failure Behavior** | Redirect to login page |

#### 7.1.2 SEC-AUTH-002: Session Expiry

| Attribute | Specification |
|-----------|---------------|
| **ID** | SEC-AUTH-002 |
| **Requirement** | THE UI SHALL redirect to login on 401 API responses |
| **Implementation** | Global fetch interceptor |
| **User Feedback** | "Session expired. Please log in again." |

#### 7.1.3 SEC-AUTH-003: Logout Cleanup

| Attribute | Specification |
|-----------|---------------|
| **ID** | SEC-AUTH-003 |
| **Requirement** | THE UI SHALL clear all sensitive data from localStorage on logout |
| **Data Cleared** | `soma_token`, cached user data, session state |
| **Verification** | Unit test |

### 7.2 Authorization Requirements

#### 7.2.1 SEC-AUTHZ-001: Role Enforcement

| Attribute | Specification |
|-----------|---------------|
| **ID** | SEC-AUTHZ-001 |
| **Requirement** | THE UI SHALL enforce role-based visibility for all protected elements |
| **Implementation** | Alpine.js `x-show` directives with role checks |
| **Verification** | E2E tests with different roles |

#### 7.2.2 SEC-AUTHZ-002: Default Deny

| Attribute | Specification |
|-----------|---------------|
| **ID** | SEC-AUTHZ-002 |
| **Requirement** | THE UI SHALL default to minimum permissions (viewer) when role is unknown |
| **Implementation** | Fallback in auth store initialization |
| **Verification** | Unit test with invalid JWT |

### 7.3 Data Protection Requirements

#### 7.3.1 SEC-DATA-001: XSS Prevention

| Attribute | Specification |
|-----------|---------------|
| **ID** | SEC-DATA-001 |
| **Requirement** | THE UI SHALL sanitize all user input before rendering |
| **Implementation** | Alpine.js `x-text` (auto-escaped), explicit sanitization for `x-html` |
| **Verification** | Security testing |

#### 7.3.2 SEC-DATA-002: CSP Headers

| Attribute | Specification |
|-----------|---------------|
| **ID** | SEC-DATA-002 |
| **Requirement** | THE UI SHALL be compatible with strict Content Security Policy |
| **Policy** | No inline scripts, no eval(), no unsafe-inline styles |
| **Verification** | CSP violation monitoring |

#### 7.3.3 SEC-DATA-003: Sensitive Data Handling

| Attribute | Specification |
|-----------|---------------|
| **ID** | SEC-DATA-003 |
| **Requirement** | THE UI SHALL NOT log or display sensitive data (passwords, tokens, PII) |
| **Implementation** | Explicit exclusion in logging, masked display |
| **Verification** | Code review, security audit |

### 7.4 Communication Security

#### 7.4.1 SEC-COMM-001: HTTPS Only

| Attribute | Specification |
|-----------|---------------|
| **ID** | SEC-COMM-001 |
| **Requirement** | THE UI SHALL only communicate with backend services over HTTPS |
| **Implementation** | Absolute URLs with https:// protocol |
| **Verification** | Network traffic analysis |

#### 7.4.2 SEC-COMM-002: Token Transmission

| Attribute | Specification |
|-----------|---------------|
| **ID** | SEC-COMM-002 |
| **Requirement** | THE UI SHALL transmit JWT tokens only in Authorization header |
| **Implementation** | `Authorization: Bearer <token>` header |
| **Verification** | Network traffic analysis |


---

## 8. Data Requirements

### 8.1 Data Models

#### 8.1.1 DM-001: User Role Model

```typescript
type UserRole = 'admin' | 'operator' | 'viewer';

interface AuthState {
  isAuthenticated: boolean;
  role: UserRole;
  tenantId: string | null;
  userId: string | null;
  permissions: string[];
}
```

#### 8.1.2 DM-002: Theme State Model

```typescript
type ThemeMode = 'light' | 'dark' | 'system';

interface ThemeState {
  mode: ThemeMode;
  currentTheme: string;
  customTokens: Record<string, string>;
}
```

#### 8.1.3 DM-003: Service Status Model

```typescript
type ServiceHealth = 'healthy' | 'degraded' | 'down' | 'unknown';

interface ServiceStatus {
  name: string;
  health: ServiceHealth;
  lastChecked: Date;
  latencyMs: number;
  details: Record<string, any>;
}
```

#### 8.1.4 DM-004: Toast Notification Model

```typescript
type ToastVariant = 'info' | 'success' | 'warning' | 'error';

interface Toast {
  id: string;
  variant: ToastVariant;
  message: string;
  duration: number;
  visible: boolean;
}
```

#### 8.1.5 DM-005: Navigation Item Model

```typescript
interface NavItem {
  id: string;
  label: string;
  icon: string;
  href: string;
  permission?: string;
  badge?: number;
}

interface NavGroup {
  id: string;
  label: string;
  items: NavItem[];
}
```

### 8.2 Data Storage

#### 8.2.1 DS-001: LocalStorage Schema

| Key | Type | Description | Persistence |
|-----|------|-------------|-------------|
| `soma_token` | string | JWT authentication token | Session |
| `soma_theme_mode` | string | Theme preference (light/dark/system) | Permanent |
| `soma_sidebar_collapsed` | boolean | Sidebar collapse state | Permanent |
| `soma_settings` | JSON | User preferences | Permanent |

#### 8.2.2 DS-002: Session Storage Schema

| Key | Type | Description | Persistence |
|-----|------|-------------|-------------|
| `soma_active_tab` | string | Current settings tab | Session |
| `soma_table_sort` | JSON | Table sort state | Session |
| `soma_table_page` | number | Current table page | Session |

### 8.3 Data Validation

#### 8.3.1 DV-001: JWT Token Validation

| Field | Validation |
|-------|------------|
| `sub` | Required, non-empty string |
| `role` | Optional, one of: admin, operator, viewer |
| `tenant_id` | Optional, UUID format |
| `exp` | Optional, Unix timestamp |

#### 8.3.2 DV-002: Settings Validation

| Setting | Validation |
|---------|------------|
| Theme mode | One of: light, dark, system |
| Notification duration | Integer, 1000-30000 ms |
| Poll interval | Integer, 1000-60000 ms |

---

## 9. Constraints

### 9.1 Technical Constraints

| ID | Constraint | Rationale |
|----|------------|-----------|
| CON-001 | No build step required | Simplify deployment, reduce toolchain complexity |
| CON-002 | Vanilla JavaScript only | Avoid framework lock-in, reduce bundle size |
| CON-003 | Alpine.js 3.x for reactivity | Lightweight, declarative, HTML-first |
| CON-004 | CSS Custom Properties for theming | Native browser support, no preprocessing |
| CON-005 | Maximum 100KB CSS (minified) | Performance budget |
| CON-006 | Maximum 50KB JS (minified) | Performance budget |
| CON-007 | ES2020+ JavaScript | Modern browser support only |
| CON-008 | No jQuery or legacy libraries | Modern standards only |

### 9.2 Regulatory Constraints

| ID | Constraint | Standard |
|----|------------|----------|
| CON-REG-001 | WCAG 2.1 AA compliance | Accessibility |
| CON-REG-002 | GDPR compliance for preferences | Data protection |
| CON-REG-003 | No third-party tracking | Privacy |

### 9.3 Development Constraints

| ID | Constraint | Source |
|----|------------|--------|
| CON-DEV-001 | VIBE Coding Rules compliance | REF-008 |
| CON-DEV-002 | No mocks or placeholders | VIBE Rule #1 |
| CON-DEV-003 | Real implementations only | VIBE Rule #4 |
| CON-DEV-004 | Complete context required | VIBE Rule #6 |
| CON-DEV-005 | Documentation must be truth | VIBE Rule #5 |

### 9.4 Business Constraints

| ID | Constraint | Rationale |
|----|------------|-----------|
| CON-BUS-001 | Open source compatible | SomaStack is open source |
| CON-BUS-002 | No proprietary dependencies | Avoid licensing issues |
| CON-BUS-003 | Self-hostable | Enterprise deployment requirement |

---

## 10. Assumptions and Dependencies

### 10.1 Assumptions

| ID | Assumption | Impact if False |
|----|------------|-----------------|
| ASM-001 | Users have modern browsers (ES2020+) | Polyfills required |
| ASM-002 | JavaScript is enabled | Core functionality unavailable |
| ASM-003 | Network connectivity available | Offline mode limited |
| ASM-004 | Backend services implement health endpoints | Status monitoring unavailable |
| ASM-005 | JWT tokens contain role claim | Role-based UI fails |
| ASM-006 | Geist font available or fallback acceptable | Typography degraded |

### 10.2 Dependencies

#### 10.2.1 External Dependencies

| ID | Dependency | Version | Purpose | Fallback |
|----|------------|---------|---------|----------|
| DEP-001 | Alpine.js | 3.x | Reactive components | None (required) |
| DEP-002 | Geist Font | Latest | Typography | system-ui fallback |

#### 10.2.2 Internal Dependencies

| ID | Dependency | Purpose |
|----|------------|---------|
| DEP-INT-001 | SomaAgent01 Gateway | Health API, Settings API |
| DEP-INT-002 | SomaBrain API | Health API, Cognitive APIs |
| DEP-INT-003 | SomaFractalMemory API | Health API, Memory APIs |
| DEP-INT-004 | AgentVoiceBox API | Health API, Voice WebSocket |

#### 10.2.3 Infrastructure Dependencies

| ID | Dependency | Purpose |
|----|------------|---------|
| DEP-INFRA-001 | HTTPS/TLS | Secure communication |
| DEP-INFRA-002 | CDN (optional) | Asset delivery |
| DEP-INFRA-003 | Web server | Static file serving |


---

## 11. Acceptance Criteria

### 11.1 Functional Acceptance Criteria

#### 11.1.1 Design Token System

| ID | Criterion | Verification Method |
|----|-----------|---------------------|
| AC-DT-001 | All 26 required CSS variables defined | CSS inspection |
| AC-DT-002 | Token changes propagate to all components | Property test |
| AC-DT-003 | 5 color palettes with correct shades | CSS inspection |
| AC-DT-004 | 8 spacing scale values correct | CSS inspection |
| AC-DT-005 | 6 typography scale values correct | CSS inspection |
| AC-DT-006 | Geist font loads with fallback | Visual verification |

#### 11.1.2 Role-Based Access Control

| ID | Criterion | Verification Method |
|----|-----------|---------------------|
| AC-RBAC-001 | Admin sees all controls | E2E test |
| AC-RBAC-002 | Operator sees operational controls only | E2E test |
| AC-RBAC-003 | Viewer sees read-only views only | E2E test |
| AC-RBAC-004 | Invalid JWT defaults to viewer | Unit test |
| AC-RBAC-005 | Role extracted from JWT correctly | Unit test |

#### 11.1.3 Navigation System

| ID | Criterion | Verification Method |
|----|-----------|---------------------|
| AC-NAV-001 | Sidebar collapses/expands | E2E test |
| AC-NAV-002 | Active section highlighted | Visual verification |
| AC-NAV-003 | Keyboard navigation works | E2E test |
| AC-NAV-004 | State persists across reload | E2E test |

#### 11.1.4 Theme System

| ID | Criterion | Verification Method |
|----|-----------|---------------------|
| AC-TH-001 | Light theme renders correctly | Visual verification |
| AC-TH-002 | Dark theme renders correctly | Visual verification |
| AC-TH-003 | Theme switch < 100ms | Performance test |
| AC-TH-004 | Theme persists across reload | E2E test |
| AC-TH-005 | System preference respected | E2E test |

#### 11.1.5 Status Monitoring

| ID | Criterion | Verification Method |
|----|-----------|---------------------|
| AC-SI-001 | Health dots show correct colors | Integration test |
| AC-SI-002 | Status updates within 5 seconds | Integration test |
| AC-SI-003 | Tooltip shows detailed info | E2E test |
| AC-SI-004 | All services monitored | Integration test |

### 11.2 Non-Functional Acceptance Criteria

#### 11.2.1 Performance

| ID | Criterion | Target | Verification |
|----|-----------|--------|--------------|
| AC-PERF-001 | First Contentful Paint | < 1.5s | Lighthouse |
| AC-PERF-002 | Time to Interactive | < 3s | Lighthouse |
| AC-PERF-003 | Cumulative Layout Shift | < 0.1 | Lighthouse |
| AC-PERF-004 | CSS bundle size | < 30KB gzip | Build output |
| AC-PERF-005 | JS bundle size | < 20KB gzip | Build output |

#### 11.2.2 Accessibility

| ID | Criterion | Target | Verification |
|----|-----------|--------|--------------|
| AC-A11Y-001 | WCAG 2.1 AA compliance | Pass | axe-core audit |
| AC-A11Y-002 | Keyboard navigation | All elements | E2E test |
| AC-A11Y-003 | Screen reader compatibility | NVDA/VoiceOver | Manual test |
| AC-A11Y-004 | Color contrast | 4.5:1 minimum | Contrast checker |

#### 11.2.3 Browser Compatibility

| ID | Criterion | Browsers | Verification |
|----|-----------|----------|--------------|
| AC-COMPAT-001 | Chrome 90+ | Full functionality | E2E test |
| AC-COMPAT-002 | Firefox 88+ | Full functionality | E2E test |
| AC-COMPAT-003 | Safari 14+ | Full functionality | E2E test |
| AC-COMPAT-004 | Edge 90+ | Full functionality | E2E test |

### 11.3 Security Acceptance Criteria

| ID | Criterion | Verification |
|----|-----------|--------------|
| AC-SEC-001 | No XSS vulnerabilities | Security scan |
| AC-SEC-002 | CSP compatible | CSP header test |
| AC-SEC-003 | Tokens in Authorization header only | Network analysis |
| AC-SEC-004 | Sensitive data not logged | Code review |
| AC-SEC-005 | HTTPS only communication | Network analysis |

---

## 12. Traceability Matrix

### 12.1 Requirements to Features

| Requirement | Feature | Priority |
|-------------|---------|----------|
| FR-DT-001 - FR-DT-008 | PF-001 Design Token Management | P0 |
| FR-GL-001 - FR-GL-005 | PF-001 Design Token Management | P0 |
| FR-RBAC-001 - FR-RBAC-008 | PF-003 Role-Based UI Control | P0 |
| FR-NAV-001 - FR-NAV-006 | PF-004 Component Library | P0 |
| FR-SC-001 - FR-SC-005 | PF-004 Component Library | P0 |
| FR-TBL-001 - FR-TBL-008 | PF-004 Component Library | P0 |
| FR-SI-001 - FR-SI-007 | PF-006 Status Monitoring | P0 |
| FR-SET-001 - FR-SET-007 | PF-004 Component Library | P1 |
| FR-TH-001 - FR-TH-006 | PF-002 Theme Switching | P0 |
| FR-MOD-001 - FR-MOD-007 | PF-004 Component Library | P0 |
| FR-TST-001 - FR-TST-004 | PF-010 Notification System | P0 |
| FR-FRM-001 - FR-FRM-007 | PF-009 Form Handling | P0 |

### 12.2 Requirements to Tests

| Requirement | Test Type | Test ID |
|-------------|-----------|---------|
| FR-DT-002 | Property | PT-001 |
| FR-GL-004 | Property | PT-002 |
| FR-RBAC-001 - FR-RBAC-004 | Property | PT-003 |
| FR-RBAC-005 | Unit | UT-001 |
| FR-SC-004 | Unit | UT-002 |
| FR-TBL-001 | Property | PT-004 |
| FR-TBL-005 | Property | PT-005 |
| FR-SI-002 | Integration | IT-001 |
| FR-TH-002 | Performance | PERF-001 |
| FR-NAV-004 | E2E | E2E-001 |
| FR-MOD-002 - FR-MOD-007 | E2E | E2E-002 |

### 12.3 Requirements to Acceptance Criteria

| Requirement | Acceptance Criteria |
|-------------|---------------------|
| FR-DT-001 | AC-DT-001 |
| FR-DT-002 | AC-DT-002 |
| FR-RBAC-001 - FR-RBAC-004 | AC-RBAC-001 - AC-RBAC-003 |
| FR-RBAC-005 - FR-RBAC-006 | AC-RBAC-004, AC-RBAC-005 |
| FR-NAV-001 - FR-NAV-006 | AC-NAV-001 - AC-NAV-004 |
| FR-TH-001 - FR-TH-006 | AC-TH-001 - AC-TH-005 |
| FR-SI-001 - FR-SI-007 | AC-SI-001 - AC-SI-004 |
| NFR-PERF-001 - NFR-PERF-006 | AC-PERF-001 - AC-PERF-005 |
| SEC-AUTH-001 - SEC-DATA-003 | AC-SEC-001 - AC-SEC-005 |


---

## 13. Appendices

### Appendix A: Design Token Reference

#### A.1 Color Tokens

```css
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

/* Primary Palette */
--color-primary-50: #eff6ff;
--color-primary-100: #dbeafe;
--color-primary-500: #3b82f6;
--color-primary-600: #2563eb;
--color-primary-700: #1d4ed8;

/* Success Palette */
--color-success-50: #f0fdf4;
--color-success-500: #22c55e;
--color-success-600: #16a34a;

/* Warning Palette */
--color-warning-50: #fffbeb;
--color-warning-500: #f59e0b;
--color-warning-600: #d97706;

/* Error Palette */
--color-error-50: #fef2f2;
--color-error-500: #ef4444;
--color-error-600: #dc2626;
```

#### A.2 Spacing Tokens

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

#### A.3 Typography Tokens

```css
--font-sans: 'Geist', system-ui, -apple-system, sans-serif;
--font-mono: 'Geist Mono', ui-monospace, monospace;

--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */

--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

#### A.4 Effect Tokens

```css
--radius-none: 0;
--radius-sm: 0.25rem;   /* 4px */
--radius-md: 0.5rem;    /* 8px */
--radius-lg: 0.75rem;   /* 12px */
--radius-full: 9999px;

--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);

--glass-blur: blur(12px);
--glass-bg: rgba(255, 255, 255, 0.7);
--glass-border: rgba(255, 255, 255, 0.2);

--transition-fast: 100ms ease;
--transition-normal: 200ms ease;
--transition-slow: 300ms ease;
```

### Appendix B: Component CSS Class Reference

#### B.1 Layout Classes

| Class | Description |
|-------|-------------|
| `.soma-layout` | Main layout container |
| `.soma-sidebar` | Sidebar navigation |
| `.soma-sidebar--collapsed` | Collapsed sidebar state |
| `.soma-header` | Header bar |
| `.soma-main` | Main content area |
| `.soma-footer` | Footer |

#### B.2 Component Classes

| Class | Description |
|-------|-------------|
| `.soma-btn` | Button base |
| `.soma-btn--primary` | Primary button variant |
| `.soma-btn--ghost` | Ghost button variant |
| `.soma-btn--danger` | Danger button variant |
| `.soma-btn--sm` | Small button size |
| `.soma-input` | Input base |
| `.soma-input--search` | Search input variant |
| `.soma-select` | Select dropdown |
| `.soma-checkbox` | Checkbox |
| `.soma-toggle` | Toggle switch |
| `.soma-badge` | Status badge |
| `.soma-badge--approved` | Approved status |
| `.soma-badge--pending` | Pending status |
| `.soma-badge--rejected` | Rejected status |

#### B.3 Utility Classes

| Class | Description |
|-------|-------------|
| `.soma-sr-only` | Screen reader only |
| `.soma-focusable` | Focus ring on focus-visible |
| `.soma-skip-link` | Skip navigation link |

### Appendix C: Alpine.js Store Reference

#### C.1 Auth Store (`$store.auth`)

| Property | Type | Description |
|----------|------|-------------|
| `isAuthenticated` | boolean | Authentication status |
| `role` | string | User role (admin/operator/viewer) |
| `tenantId` | string | Tenant identifier |
| `userId` | string | User identifier |
| `permissions` | string[] | Permission list |
| `isAdmin` | boolean | Admin role check (computed) |
| `isOperator` | boolean | Operator+ role check (computed) |

| Method | Parameters | Description |
|--------|------------|-------------|
| `loadFromToken()` | none | Parse JWT and update state |
| `setRole(role)` | role: string | Set role and permissions |
| `hasPermission(perm)` | perm: string | Check permission |

#### C.2 Theme Store (`$store.theme`)

| Property | Type | Description |
|----------|------|-------------|
| `mode` | string | Theme mode (light/dark/system) |
| `currentTheme` | string | Active theme name |

| Method | Parameters | Description |
|--------|------------|-------------|
| `setMode(mode)` | mode: string | Set theme mode |
| `applyTheme()` | none | Apply current theme |
| `toggle()` | none | Toggle light/dark |

#### C.3 Status Store (`$store.status`)

| Property | Type | Description |
|----------|------|-------------|
| `services` | object | Service status map |
| `isPolling` | boolean | Polling active |
| `pollIntervalMs` | number | Poll interval |

| Method | Parameters | Description |
|--------|------------|-------------|
| `checkHealth(name, url)` | name, url | Check single service |
| `checkAllServices()` | none | Check all services |
| `startPolling()` | none | Start health polling |

### Appendix D: API Endpoint Reference

#### D.1 Health Endpoints

| Service | Endpoint | Response |
|---------|----------|----------|
| SomaBrain | GET /health | `{ ok: boolean, components: {...} }` |
| SomaFractalMemory | GET /healthz | `{ status: string }` |
| SomaAgent01 | GET /v1/health | `{ ok: boolean, components: {...} }` |

#### D.2 Settings Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /v1/settings | GET | Get user settings |
| /v1/settings | POST | Update user settings |

### Appendix E: Glossary of Terms

| Term | Definition |
|------|------------|
| Alpine.js | Lightweight JavaScript framework for reactive UI |
| ARIA | Accessible Rich Internet Applications specification |
| BEM | Block Element Modifier CSS naming convention |
| CSS Custom Property | CSS variable defined with `--` prefix |
| Design Token | Named value for design attribute |
| Glassmorphism | Frosted glass visual effect |
| JWT | JSON Web Token for authentication |
| WCAG | Web Content Accessibility Guidelines |

---

## Document End

**Document ID:** SRS-SOMASTACK-UI-2025-001  
**Version:** 1.0.0  
**Total Pages:** ~50  
**Classification:** Internal  

---

*This document is the authoritative source for SomaStack Unified UI Design System requirements. All implementation must conform to the specifications herein.*

*© 2025 SomaStack Platform Team. All rights reserved.*
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

# SomaStack Unified UI - Implementation Tasks

## Document Control

| Field | Value |
|-------|-------|
| **Document ID** | SOMASTACK-UI-TASKS-2025-12 |
| **Version** | 1.0 |
| **Date** | 2025-12-22 |
| **Status** | CANONICAL |
| **Implements** | SOMASTACK-UI-DESIGN-2025-12, SRS-SOMASTACK-UI-2025-001 |

---

## Task Overview

| ID | Task | Priority | Effort | Dependencies | Status |
|----|------|----------|--------|--------------|--------|
| T1 | Create Design System Directory Structure | P0 | 1h | None | ✅ DONE |
| T2 | Implement Design Tokens CSS | P0 | 2h | T1 | ✅ DONE |
| T3 | Implement Base Styles and Utilities | P0 | 2h | T2 | ✅ DONE |
| T4 | Implement Layout Components | P0 | 3h | T3 | ✅ DONE |
| T5 | Implement Navigation Components | P0 | 3h | T4 | ✅ DONE |
| T6 | Implement Stats Card Component | P0 | 2h | T3 | ✅ DONE |
| T7 | Implement Data Table Component | P0 | 4h | T3 | ✅ DONE |
| T8 | Implement Status Indicator Component | P0 | 2h | T3 | ✅ DONE |
| T9 | Implement Form Components | P0 | 3h | T3 | ✅ DONE |
| T10 | Implement Modal Component | P0 | 2h | T3 | ✅ DONE |
| T11 | Implement Toast Component | P0 | 2h | T3 | ✅ DONE |
| T12 | Implement Auth Store | P0 | 2h | T1 | ✅ DONE |
| T13 | Implement Theme Store | P0 | 2h | T2 | ✅ DONE |
| T14 | Implement Status Store | P0 | 2h | T8 | ✅ DONE |
| T15 | Implement Agent Dashboard (SomaAgent01) | P1 | 4h | T6, T8 | ✅ DONE |
| T16 | Implement Memory Browser (SomaFractalMemory) | P1 | 3h | T7 | ✅ DONE |
| T17 | Implement Voice Interface (AgentVoiceBox) | P2 | 3h | T3 | ✅ DONE |
| T18 | Implement Brain Dashboard (SomaBrain) | P1 | 3h | T6, T8 | ✅ DONE |
| T19 | API Integration | P0 | 3h | T15-T18 | ✅ DONE |
| T20 | Accessibility Audit | P1 | 3h | T15-T18 | ⏳ READY |
| T21 | Documentation | P2 | 3h | All | ⏳ READY |

---

## Phase 1: Foundation

### Task 1: Create Design System Directory Structure
- [ ] 1.1 Create `somaAgent01/webui/somastack-ui/` root directory
- [ ] 1.2 Create subdirectories: `css/`, `js/`, `fonts/`, `dist/`
- [ ] 1.3 Create `somastack-ui/package.json` with metadata and version
- [ ] 1.4 Download and add Geist font files to `fonts/geist/`
- [ ] 1.5 Create `somastack-ui/README.md` with usage instructions
- _Requirements: FR-DT-006, 18.1, 18.2_

### Task 2: Implement Design Tokens CSS
- [ ] 2.1 Create `css/somastack-tokens.css` with all design tokens
  - Color palettes: neutral (10 shades), primary (5), success (3), warning (3), error (3)
  - Typography: font-family, 6 sizes, 4 weights, line-heights
  - Spacing: 8 scale values (4px - 64px)
  - Effects: 3 shadows, 5 border-radius, 3 transitions
  - Glassmorphism: blur(12px), glass backgrounds, glass borders
  - _Requirements: FR-DT-001 through FR-DT-008, FR-GL-001 through FR-GL-003_

- [ ] 2.2 Write property test for token propagation
  - **Property 1: CSS Token Propagation**
  - *For any* CSS custom property, changing its value at `:root` SHALL update all usages
  - **Validates: FR-DT-002**


- [ ] 2.3 Write property test for WCAG contrast compliance
  - **Property 2: WCAG Contrast Compliance**
  - *For any* text/background color combination, contrast ratio SHALL be >= 4.5:1
  - **Validates: FR-GL-004**

### Task 3: Implement Base Styles and Utilities
- [ ] 3.1 Create `css/somastack-base.css` with CSS reset and base styles
  - Box-sizing border-box
  - Font smoothing
  - Focus-visible styles
  - Reduced motion support
  - _Requirements: FR-GL-004, 13.5, 13.6_

- [ ] 3.2 Create `css/somastack-utilities.css` with utility classes
  - Screen reader only (.soma-sr-only)
  - Focus ring (.soma-focusable)
  - Skip link (.soma-skip-link)
  - Spacing utilities
  - _Requirements: 13.2, 13.3_

### Task 4: Implement Layout Components
- [ ] 4.1 Create layout CSS in `css/somastack-components.css`
  - .soma-layout (main container with CSS Grid)
  - .soma-sidebar (sidebar with collapse support)
  - .soma-header (header bar)
  - .soma-main (main content area)
  - .soma-footer (footer)
  - _Requirements: 12.4, 12.5_

- [ ] 4.2 Create responsive breakpoints
  - Mobile: < 640px (bottom nav)
  - Tablet: 640-1023px (collapsed sidebar)
  - Desktop: >= 1024px (full sidebar)
  - _Requirements: 12.1, 12.2, 12.3_

- [ ] 4.3 Write property test for responsive layout
  - **Property 11: Responsive Layout Correctness**
  - *For any* viewport width, correct layout configuration SHALL be applied
  - **Validates: FR-NAV-001, 12.2, 12.3**

### Task 5: Implement Navigation Components
- [ ] 5.1 Create navigation CSS
  - .soma-nav-group (navigation group)
  - .soma-nav-item (navigation item)
  - .soma-nav-item--active (active state)
  - .soma-nav-item__badge (notification badge)
  - _Requirements: FR-NAV-001 through FR-NAV-006_

- [ ] 5.2 Create `js/components/sidebar-nav.js` Lit Web Component
  - Collapse/expand functionality
  - Active section tracking
  - localStorage persistence
  - Keyboard navigation (Tab, Enter, Arrow keys)
  - _Requirements: FR-NAV-001, FR-NAV-004, FR-NAV-005_

- [ ] 5.3 Write property test for keyboard navigation
  - **Property 13: Keyboard Navigation**
  - *For any* interactive element, Tab/Enter/Arrow keys SHALL work correctly
  - **Validates: FR-NAV-004, 13.2**

---

## Phase 2: Core Components

### Task 6: Implement Stats Card Component
- [ ] 6.1 Create stats card CSS
  - .soma-stats-card (card container)
  - .soma-stats-card__icon (icon area)
  - .soma-stats-card__value (metric value)
  - .soma-stats-card__label (metric label)
  - .soma-stats-card__trend (trend indicator)
  - Size variants: sm, md, lg, full
  - _Requirements: FR-SC-001 through FR-SC-005_

- [ ] 6.2 Create `js/components/stats-card.js` Lit Web Component
  - Number formatting (K/M/B suffixes)
  - Trend calculation and display
  - Value animation (300ms transition)
  - _Requirements: FR-SC-002, FR-SC-004, FR-SC-005_

- [ ] 6.3 Write property test for number formatting
  - **Property 5: Number Formatting**
  - *For any* number >= 1000, SHALL format with K/M/B suffix
  - **Validates: FR-SC-004**

### Task 7: Implement Data Table Component
- [ ] 7.1 Create data table CSS
  - .soma-table-container (wrapper)
  - .soma-table (table element)
  - .soma-table__header (sortable header)
  - .soma-table__row (data row)
  - .soma-table__checkbox (selection checkbox)
  - .soma-table__actions (action buttons)
  - .soma-table__pagination (pagination controls)
  - .soma-badge (status badges: approved, pending, rejected)
  - _Requirements: FR-TBL-001 through FR-TBL-008_

- [ ] 7.2 Create `js/components/data-table.js` Lit Web Component
  - Column sorting (asc/desc toggle)
  - Row selection with select-all
  - Pagination (configurable page size)
  - Search/filter functionality
  - Loading skeleton state
  - Empty state display
  - Role-based action visibility
  - _Requirements: FR-TBL-001 through FR-TBL-008_

- [ ] 7.3 Write property test for table sorting
  - **Property 6: Table Sorting Correctness**
  - *For any* column click, rows SHALL sort correctly
  - **Validates: FR-TBL-001**

- [ ] 7.4 Write property test for pagination
  - **Property 7: Table Pagination Activation**
  - *For any* table with > pageSize rows, pagination SHALL be displayed
  - **Validates: FR-TBL-005**

### Task 8: Implement Status Indicator Component
- [ ] 8.1 Create status indicator CSS
  - .soma-status (container)
  - .soma-status__dot (health dot)
  - .soma-status__dot--healthy (green)
  - .soma-status__dot--degraded (amber)
  - .soma-status__dot--down (red)
  - .soma-status__dot--unknown (grey)
  - .soma-status__tooltip (detail tooltip)
  - Pulse animation for active states
  - _Requirements: FR-SI-001 through FR-SI-007_

- [ ] 8.2 Create `js/components/status-indicator.js` Lit Web Component
  - Health status display
  - Relative timestamp formatting
  - Tooltip on hover
  - _Requirements: FR-SI-001, FR-SI-003, FR-SI-005_

### Task 9: Implement Form Components
- [ ] 9.1 Create form CSS
  - .soma-input (text input)
  - .soma-textarea (textarea)
  - .soma-select (select dropdown)
  - .soma-checkbox (checkbox)
  - .soma-radio (radio button)
  - .soma-toggle (toggle switch)
  - .soma-slider (range slider)
  - .soma-color-picker (color input)
  - States: focus, disabled, readonly, error
  - Helper text and validation error styling
  - _Requirements: FR-FRM-001 through FR-FRM-007_

- [ ] 9.2 Create `js/components/form-validation.js` Lit Web Component
  - Inline validation
  - Form-level validation
  - Error message display
  - Lit reactive property integration
  - _Requirements: FR-FRM-002, FR-FRM-006, FR-FRM-007_

- [ ] 9.3 Write property test for form validation
  - **Property 9: Settings Validation**
  - *For any* invalid input, validation SHALL reject with error message
  - **Validates: FR-FRM-002, FR-SET-006**

### Task 10: Implement Modal Component
- [ ] 10.1 Create modal CSS
  - .soma-modal (container)
  - .soma-modal__backdrop (backdrop overlay)
  - .soma-modal__content (content container)
  - .soma-modal__header (header with title and close)
  - .soma-modal__body (body content)
  - .soma-modal__footer (action buttons)
  - Size variants: sm (400px), md (600px), lg (800px), full
  - Open/close animations (fade + scale, 200ms)
  - _Requirements: FR-MOD-001 through FR-MOD-007_

- [ ] 10.2 Create `js/components/modal.js` Lit Web Component
  - Focus trap
  - Escape key close
  - Backdrop click close (configurable)
  - Body scroll lock
  - Stacked modal z-index management
  - _Requirements: FR-MOD-002 through FR-MOD-007_

- [ ] 10.3 Write property test for modal behavior
  - **Property 20: Modal Behavior Correctness**
  - *For any* open modal, focus trap, escape close, backdrop close, scroll lock SHALL work
  - **Validates: FR-MOD-002 through FR-MOD-007**

### Task 11: Implement Toast Component
- [ ] 11.1 Create toast CSS
  - .soma-toast-container (fixed position container)
  - .soma-toast (toast notification)
  - .soma-toast--info (blue)
  - .soma-toast--success (green)
  - .soma-toast--warning (amber)
  - .soma-toast--error (red)
  - .soma-toast__icon (variant icon)
  - .soma-toast__message (message text)
  - .soma-toast__close (close button)
  - Enter/exit animations
  - _Requirements: FR-TST-001 through FR-TST-004_

- [ ] 11.2 Create `js/components/toast.js` Lit Web Component
  - Toast creation with variants
  - Auto-dismiss (configurable timeout, default 5s)
  - Manual dismiss
  - Toast stacking
  - _Requirements: FR-TST-001 through FR-TST-004_

- [ ] 11.3 Write property test for toast auto-dismiss
  - **Property 18: Toast Auto-Dismiss**
  - *For any* toast, SHALL auto-dismiss after configured timeout
  - **Validates: FR-TST-002**

---

## Phase 3: State Management

### Task 12: Implement Auth Controller
- [ ] 12.1 Create `js/controllers/auth-controller.js`
  - AuthState interface implementation
  - JWT token parsing from localStorage
  - Role extraction from token claims
  - Permission calculation based on role
  - Default to viewer on invalid/missing token
  - Computed properties: isAdmin, isOperator, hasPermission()
  - _Requirements: FR-RBAC-001 through FR-RBAC-008_

- [ ] 12.2 Write property test for role-based visibility
  - **Property 3: Role-Based UI Visibility**
  - *For any* user role, UI elements SHALL be visible according to permissions
  - **Validates: FR-RBAC-002 through FR-RBAC-004**

- [ ] 12.3 Write property test for JWT parsing
  - **Property 4: JWT Role Extraction**
  - *For any* valid JWT, role SHALL be correctly extracted; invalid defaults to viewer
  - **Validates: FR-RBAC-005, FR-RBAC-006**

### Task 13: Implement Theme Store
- [ ] 13.1 Create `js/stores/theme-store.js`
  - ThemeState interface implementation
  - Light/dark/system mode support
  - localStorage persistence
  - System preference detection (prefers-color-scheme)
  - Theme application via CSS class toggle
  - Smooth transition (300ms)
  - _Requirements: FR-TH-001 through FR-TH-006_

- [ ] 13.2 Write property test for theme switching
  - **Property 16: Theme Switching Performance**
  - *For any* theme toggle, change SHALL complete within 100ms
  - **Validates: FR-TH-002**

- [ ] 13.3 Write property test for state persistence
  - **Property 17: State Persistence Round-Trip**
  - *For any* preference stored in localStorage, page reload SHALL restore exact state
  - **Validates: FR-TH-003, FR-NAV-005, FR-SET-003**

### Task 14: Implement Status Store
- [ ] 14.1 Create `js/stores/status-store.js`
  - StatusState interface implementation
  - Health check polling (5 second interval)
  - Service status tracking
  - Latency measurement
  - Integration with health endpoints:
    - SomaBrain: GET /health (port 9696)
    - SomaFractalMemory: GET /healthz (port 9595)
    - SomaAgent01: GET /v1/health (port 21016)
  - _Requirements: FR-SI-001 through FR-SI-007_

- [ ] 14.2 Write property test for status update latency
  - **Property 8: Status Update Latency**
  - *For any* service status change, indicator SHALL update within 5 seconds
  - **Validates: FR-SI-002**

---

## Phase 4: Agent-Specific Components

### Task 15: Implement Agent Dashboard Components
- [ ] 15.1 Create agent dashboard CSS
  - .soma-agent-dashboard (container)
  - .soma-neuro-gauge (neuromodulator gauge)
  - .soma-fsm-diagram (FSM state visualization)
  - .soma-reasoning-stream (reasoning text stream)
  - .soma-conversation (conversation history)
  - .soma-tool-monitor (tool execution status)
  - _Requirements: FR-AGT-001 through FR-AGT-007_

- [ ] 15.2 Create `js/components/agent-dashboard.js` Alpine component
  - Neuromodulator level display (dopamine, serotonin, noradrenaline, acetylcholine)
  - FSM state visualization
  - Real-time reasoning stream
  - Conversation history with message bubbles
  - Tool execution monitoring
  - _Requirements: FR-AGT-001 through FR-AGT-006_

### Task 16: Implement Memory Browser Component
- [ ] 16.1 Create memory browser CSS
  - .soma-memory-browser (container)
  - .soma-memory-card (memory card view)
  - .soma-memory-list (memory list view)
  - .soma-memory-detail (detail panel)
  - .soma-memory-badge--episodic (blue)
  - .soma-memory-badge--semantic (purple)
  - _Requirements: FR-MEM-001 through FR-MEM-007_

- [ ] 16.2 Create `js/components/memory-browser.js` Alpine component
  - Card/list view toggle
  - Search by content, coordinate, metadata
  - Memory type badges
  - Age and decay display
  - Detail panel on click
  - Admin delete capability
  - Similarity score display
  - _Requirements: FR-MEM-001 through FR-MEM-007_

- [ ] 16.3 Write property test for memory search
  - **Property 10: Memory Search Accuracy**
  - *For any* search query, all results SHALL contain the search term
  - **Validates: FR-MEM-002**

### Task 17: Implement Voice Interface Components
- [ ] 17.1 Create voice interface CSS
  - .soma-voice-interface (container)
  - .soma-waveform (audio waveform visualization)
  - .soma-transcription (real-time transcription)
  - .soma-tts-progress (TTS playback progress)
  - .soma-voice-indicator (processing animation)
  - .soma-voice-status (connection status)
  - _Requirements: FR-VOI-001 through FR-VOI-006_

- [ ] 17.2 Create `js/components/voice-interface.js` Alpine component
  - Waveform visualization using Web Audio API
  - Real-time transcription display
  - TTS progress indicator
  - PTT and VAD mode support
  - Processing animation
  - Connection status display
  - _Requirements: FR-VOI-001 through FR-VOI-006_

---

## Phase 5: Integration and Testing

### Task 18: Create Bundle and Distribution
- [ ] 18.1 Create `dist/somastack-ui.css` (concatenated, minified)
  - Include: tokens, base, utilities, components
  - Target: < 30KB gzipped
  - _Requirements: NFR-PERF-006_

- [ ] 18.2 Create `dist/somastack-ui.js` (concatenated, minified)
  - Include: core, stores, components
  - Target: < 20KB gzipped
  - _Requirements: NFR-PERF-006_

- [ ] 18.3 Create `dist/somastack-ui.min.css` and `dist/somastack-ui.min.js`
  - Minified production builds
  - Source maps for debugging

### Task 19: Integrate with SomaAgent01
- [ ] 19.1 Update `somaAgent01/webui/index.html`
  - Add link to somastack-ui.css
  - Add script for somastack-ui.js
  - Remove duplicate inline styles
  - Update Alpine components to use new stores
  - _Requirements: 18.2, 18.3_

- [ ] 19.2 Update existing components to use design system
  - Replace hardcoded colors with tokens
  - Replace custom components with design system components
  - Ensure role-based visibility works

- [ ] 19.3 Verify no visual regression
  - Compare before/after screenshots
  - Test all major views

### Task 20: Unit Tests
- [ ] 20.1 Create `tests/unit/test_tokens.py`
  - Verify all required tokens present
  - Verify token values correct
  - _Requirements: FR-DT-001 through FR-DT-008_

- [ ] 20.2 Create `tests/unit/test_auth_store.js`
  - Test JWT parsing
  - Test role extraction
  - Test permission calculation
  - Test default fallback
  - _Requirements: FR-RBAC-005, FR-RBAC-006_

- [ ] 20.3 Create `tests/unit/test_number_format.js`
  - Test K/M/B formatting
  - Test edge cases (999, 1000, 999999, etc.)
  - _Requirements: FR-SC-004_

- [ ] 20.4 Create `tests/unit/test_contrast.js`
  - Test contrast ratio calculation
  - Test WCAG AA compliance
  - _Requirements: FR-GL-004_

### Task 21: Property Tests
- [ ] 21.1 Property Test: Token Propagation
  - **Property 1: CSS Token Propagation**
  - **Validates: FR-DT-002**

- [ ] 21.2 Property Test: WCAG Contrast
  - **Property 2: WCAG Contrast Compliance**
  - **Validates: FR-GL-004**

- [ ] 21.3 Property Test: Role Visibility
  - **Property 3: Role-Based UI Visibility**
  - **Validates: FR-RBAC-002 through FR-RBAC-004**

- [ ] 21.4 Property Test: JWT Parsing
  - **Property 4: JWT Role Extraction**
  - **Validates: FR-RBAC-005, FR-RBAC-006**

- [ ] 21.5 Property Test: Number Formatting
  - **Property 5: Number Formatting**
  - **Validates: FR-SC-004**

- [ ] 21.6 Property Test: Table Sorting
  - **Property 6: Table Sorting Correctness**
  - **Validates: FR-TBL-001**

- [ ] 21.7 Property Test: Pagination
  - **Property 7: Table Pagination Activation**
  - **Validates: FR-TBL-005**

- [ ] 21.8 Property Test: Status Latency
  - **Property 8: Status Update Latency**
  - **Validates: FR-SI-002**

- [ ] 21.9 Property Test: Theme Switching
  - **Property 16: Theme Switching Performance**
  - **Validates: FR-TH-002**

- [ ] 21.10 Property Test: State Persistence
  - **Property 17: State Persistence Round-Trip**
  - **Validates: FR-TH-003, FR-NAV-005, FR-SET-003**

### Task 22: E2E Tests (Playwright)
- [ ] 22.1 Create `tests/e2e/test_navigation.spec.js`
  - Test sidebar collapse/expand
  - Test keyboard navigation
  - Test active section highlight
  - _Requirements: FR-NAV-001 through FR-NAV-006_

- [ ] 22.2 Create `tests/e2e/test_theme.spec.js`
  - Test theme toggle
  - Test theme persistence
  - Test system preference
  - _Requirements: FR-TH-001 through FR-TH-006_

- [ ] 22.3 Create `tests/e2e/test_rbac.spec.js`
  - Test admin UI visibility
  - Test operator UI visibility
  - Test viewer UI visibility
  - _Requirements: FR-RBAC-001 through FR-RBAC-008_

- [ ] 22.4 Create `tests/e2e/test_table.spec.js`
  - Test sorting
  - Test pagination
  - Test search/filter
  - Test row selection
  - _Requirements: FR-TBL-001 through FR-TBL-008_

- [ ] 22.5 Create `tests/e2e/test_modal.spec.js`
  - Test focus trap
  - Test escape close
  - Test backdrop close
  - Test stacked modals
  - _Requirements: FR-MOD-001 through FR-MOD-007_

- [ ] 22.6 Create `tests/e2e/test_accessibility.spec.js`
  - Run axe-core audit
  - Test keyboard navigation
  - Test focus indicators
  - _Requirements: 13.1 through 13.7_

### Task 23: Documentation
- [ ] 23.1 Create `docs/somastack-ui/README.md`
  - Installation instructions
  - Quick start guide
  - _Requirements: 18.4_

- [ ] 23.2 Create `docs/somastack-ui/tokens.md`
  - Complete token reference
  - Usage examples
  - _Requirements: 18.4_

- [ ] 23.3 Create `docs/somastack-ui/components.md`
  - Component API reference
  - Usage examples for each component
  - _Requirements: 18.4_

- [ ] 23.4 Create `docs/somastack-ui/stores.md`
  - Store API reference
  - Integration examples
  - _Requirements: 18.4_

- [ ] 23.5 Create `docs/somastack-ui/accessibility.md`
  - WCAG compliance guide
  - Keyboard navigation reference
  - ARIA usage guide
  - _Requirements: 13.1 through 13.7_

---

## Checkpoint Tasks

### Checkpoint 1: Foundation Complete
- [ ] CP1 Ensure all Phase 1 tasks complete
  - Design tokens CSS created and validated
  - Base styles and utilities implemented
  - Layout components working
  - Navigation components functional
  - Ask user if questions arise

### Checkpoint 2: Core Components Complete
- [ ] CP2 Ensure all Phase 2 tasks complete
  - All core components implemented
  - Property tests passing
  - Visual verification complete
  - Ask user if questions arise

### Checkpoint 3: State Management Complete
- [ ] CP3 Ensure all Phase 3 tasks complete
  - All stores implemented
  - JWT parsing working
  - Theme switching working
  - Status polling working
  - Ask user if questions arise

### Checkpoint 4: Integration Complete
- [ ] CP4 Ensure all Phase 5 tasks complete
  - Bundle created
  - SomaAgent01 integrated
  - All tests passing
  - Documentation complete
  - Ask user if questions arise

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests passing
- [ ] Property tests passing (21 properties)
- [ ] E2E tests passing
- [ ] No VIBE violations (no mocks, no placeholders, no TODOs)
- [ ] WCAG 2.1 AA compliance verified
- [ ] Performance budgets met (CSS < 30KB, JS < 20KB)
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Visual regression tests passing

---

## Notes

- All property-based tests are required (comprehensive testing)
- All tests use real infrastructure per VIBE Coding Rules
- Lit Web Components only - no build step required
- Theme switch must complete within 100ms
- Status updates must occur within 5 seconds
- All components must work in both light and dark themes
# Agent User — Complete UI SRS

**Document ID:** SA01-AGENT-USER-UI-SRS-2025-12  
**Version:** 1.0  
**Date:** 2025-12-22  
**Status:** CANONICAL  
**Compliance:** ISO/IEC/IEEE 29148:2018  
**Stack:** Django 5.x + Django Ninja API + Lit 3.x Web Components

---

## 1. Overview

This document covers ALL agent-facing UI screens for users interacting with a SomaAgent instance. Covers all 6 modes: STD, TRN, ADM, DEV, RO, DGR.

---

## 2. Complete Settings Architecture

### 2.1 Settings Tab Structure

**Route:** `/settings`  
**Component:** `saas-settings.ts`  
**Permission:** `settings:view` (edit requires `settings:edit`)

```
Settings
├── Agent Tab
│   ├── Chat Model
│   ├── Utility Model
│   ├── Browser Model
│   ├── Embedding Model
│   └── Memory/SomaBrain
│
├── External Tab
│   ├── API Keys
│   ├── MCP Client
│   ├── MCP Server
│   ├── A2A Server
│   └── Tunnel
│
├── Connectivity Tab
│   ├── Proxy
│   ├── SSE
│   ├── Voice/Speech
│   └── Health
│
└── System Tab
    ├── Authentication
    ├── Backup/Restore
    ├── Developer
    ├── Feature Flags
    ├── Secrets
    └── Agent Config
```

---

## 3. Screen 1: Settings - Agent Tab

### 3.1 Chat Model Settings

**Route:** `/settings/agent/chat-model`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Settings › Agent › Chat Model                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Primary Chat Model                                                         │
│                                                                             │
│  Provider *                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ OpenAI                                                          ▼   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Model *                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ gpt-4o                                                          ▼   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  GPT-4o: 128K context, vision enabled, function calling                    │
│                                                                             │
│  Context Length                     Max Output Tokens                       │
│  ┌──────────────────────────┐       ┌──────────────────────────┐           │
│  │ 128000                   │       │ 16384                    │           │
│  └──────────────────────────┘       └──────────────────────────┘           │
│                                                                             │
│  Rate Limits                                                                │
│  RPM (Requests/Min)                 TPM (Tokens/Min)                        │
│  ┌──────────────────────────┐       ┌──────────────────────────┐           │
│  │ 500                      │       │ 30000                    │           │
│  └──────────────────────────┘       └──────────────────────────┘           │
│                                                                             │
│  Capabilities                                                               │
│  ☑ Vision (process images)                                                 │
│  ☑ Function Calling                                                        │
│  ☐ JSON Mode (structured output)                                           │
│                                                                             │
│  Temperature                                                                │
│  Deterministic ────────●───────────── Creative                             │
│        0.0      0.7              2.0                                        │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  [Reset to Default]                                [Save Changes]           │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### API Endpoint

```python
# Django Ninja API
@router.get("/settings/agent/chat-model", response=ChatModelSettingsSchema)
async def get_chat_model(request):
    """GET /api/v2/settings/agent/chat-model"""
    pass

@router.put("/settings/agent/chat-model", response=ChatModelSettingsSchema)
async def update_chat_model(request, data: ChatModelSettingsSchema):
    """PUT /api/v2/settings/agent/chat-model"""
    pass
```

### 3.2 Memory/SomaBrain Settings

**Route:** `/settings/agent/memory`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Settings › Agent › Memory (SomaBrain)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SomaBrain Connection                                                       │
│                                                                             │
│  ☑ Enable Memory Integration                                               │
│                                                                             │
│  SomaBrain URL *                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ http://localhost:8100                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  Status: 🟢 Connected (latency: 12ms)                     [Test Connection] │
│                                                                             │
│  Memory Settings                                                            │
│                                                                             │
│  ☑ Semantic Recall (retrieve relevant memories)                            │
│  ☑ Auto-Save Conversations                                                 │
│  ☐ Emotional Context Tracking                                              │
│                                                                             │
│  Recall Settings                                                            │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  Max Memories Per Query              Similarity Threshold                   │
│  ┌──────────────────────────┐       ┌──────────────────────────┐           │
│  │ 10                       │       │ 0.75                     │           │
│  └──────────────────────────┘       └──────────────────────────┘           │
│                                                                             │
│  Recall Interval (messages)         Context Window (memories)               │
│  ┌──────────────────────────┐       ┌──────────────────────────┐           │
│  │ 3                        │       │ 5                        │           │
│  └──────────────────────────┘       └──────────────────────────┘           │
│                                                                             │
│  Storage                                                                    │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Used: 2.3 GB / 10 GB                                                       │
│  ██████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 23%                │
│                                                                             │
│  [🗑️ Clear All Memories]  [📤 Export Memories]  [📥 Import Memories]        │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  [Reset to Default]                                [Save Changes]           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Screen 2: Settings - External Tab

### 4.1 API Keys Settings

**Route:** `/settings/external/api-keys`  
**Permission:** `settings:api_keys` (sysadmin only)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Settings › External › API Keys                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ⚠️ API keys are stored encrypted in Vault. Only sysadmins can edit.        │
│                                                                             │
│ LLM PROVIDERS                                                               │
│ ┌───────────────────────────────────────────────────────────────────────┐  │
│ │ Provider     API Key                              Status     Actions  │  │
│ │ ───────────────────────────────────────────────────────────────────── │  │
│ │ OpenAI       sk-proj-****...8x9K                  🟢 Valid   [Edit]   │  │
│ │ Anthropic    sk-ant-****...JKL2                   🟢 Valid   [Edit]   │  │
│ │ Google       AIzaSy****...mnop                    🟢 Valid   [Edit]   │  │
│ │ Groq         gsk_****...qrst                      🟡 Exp.5d  [Edit]   │  │
│ │ Mistral      (not configured)                     ⚪ —       [Add]    │  │
│ │ Cohere       (not configured)                     ⚪ —       [Add]    │  │
│ └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│ EXTERNAL SERVICES                                                           │
│ ┌───────────────────────────────────────────────────────────────────────┐  │
│ │ Service      API Key                              Status     Actions  │  │
│ │ ───────────────────────────────────────────────────────────────────── │  │
│ │ Serper       ****...xyz                           🟢 Valid   [Edit]   │  │
│ │ Firecrawl    (not configured)                     ⚪ —       [Add]    │  │
│ └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│ [+ Add Custom Provider]                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Edit API Key Modal

```
┌─────────────────────────────────────────────────────────────────────┐
│  Edit API Key: OpenAI                                            ✕  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  API Key *                                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ⚠️ Key will be encrypted before storage                          │
│                                                                     │
│  Organization ID (optional)                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ org-xxxxxxxxxxxxxxxxxxxxxxxx                                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Base URL (optional, for proxies)                                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ https://api.openai.com/v1                                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  [Test Key]  Status: 🟢 Valid                                       │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  [Cancel]  [🗑️ Remove Key]                         [Save Key]       │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 MCP Client Settings

**Route:** `/settings/external/mcp-client`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Settings › External › MCP Client                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Model Context Protocol (MCP) allows the agent to connect to external tools │
│                                                                             │
│ ☑ Enable MCP Client                                                        │
│                                                                             │
│ CONNECTED SERVERS                                      [+ Add MCP Server]   │
│ ┌───────────────────────────────────────────────────────────────────────┐  │
│ │ Server           Transport   Tools      Status        Actions         │  │
│ │ ───────────────────────────────────────────────────────────────────── │  │
│ │ filesystem       stdio       12         🟢 Running    [···]           │  │
│ │ database         stdio       8          🟢 Running    [···]           │  │
│ │ browser          stdio       5          🟡 Starting   [···]           │  │
│ │ github           http        15         🔴 Error      [···]           │  │
│ └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│ Timeouts                                                                    │
│ Init Timeout (seconds)              Tool Timeout (seconds)                  │
│ ┌──────────────────────────┐       ┌──────────────────────────┐            │
│ │ 30                       │       │ 60                       │            │
│ └──────────────────────────┘       └──────────────────────────┘            │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  [Restart All Servers]                                 [Save Changes]       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Screen 3: Settings - Connectivity Tab

### 5.1 Voice/Speech Settings (Shared Component)

**Route:** `/settings/connectivity/voice`  
**Component:** `saas-voice-settings.ts` (reused from agentVoiceBox)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Settings › Connectivity › Voice & Speech                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ☑ Enable Voice Input/Output                                                │
│                                                                             │
│ Voice Provider *                                                            │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ ○ Local Voice (Whisper + Kokoro)                                       ││
│ │   • On-device processing                                               ││
│ │   • Full privacy (no network)                                          ││
│ │   • Latency: ~300ms                                                    ││
│ │   • Requires: CPU/GPU for local models                                 ││
│ ├─────────────────────────────────────────────────────────────────────────┤│
│ │ ● AgentVoiceBox (External Service)                                     ││
│ │   • Cloud-optimized processing                                         ││
│ │   • Latency: ~150ms                                                    ││
│ │   • Requires: Network connection + AgentVoiceBox server                ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ ─────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│ AGENTVOICEBOX CONFIGURATION                                                 │
│                                                                             │
│ Server URL *                                                                │
│ ┌─────────────────────────────────────────────────────────────────────┐    │
│ │ https://voice.somaagent.io                                          │    │
│ └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│ API Token *                                                                 │
│ ┌─────────────────────────────────────────────────────────────────────┐    │
│ │ ••••••••••••••••••••••••••••••••                           [Show]   │    │
│ └─────────────────────────────────────────────────────────────────────┘    │
│ [Test Connection] Status: 🟢 Connected (latency: 142ms)                    │
│                                                                             │
│ Voice Selection                                                             │
│ ┌─────────────────────────────────────────────────────────────────────┐    │
│ │ am_onyx (Deep Male, American)                                   ▼   │    │
│ └─────────────────────────────────────────────────────────────────────┘    │
│ [▶️ Preview Voice]                                                          │
│                                                                             │
│ Speech Rate                                                                 │
│ Slow ──────────────●──────────────── Fast                                  │
│  0.5x              1.0x              2.0x                                   │
│                                                                             │
│ VAD Sensitivity (Voice Activity Detection)                                  │
│ Less Sensitive ──────────●──────────── More Sensitive                       │
│         0.3              0.5               0.8                              │
│                                                                             │
│ Language                                                                    │
│ ┌─────────────────────────────────────────────────────────────────────┐    │
│ │ English (US)                                                    ▼   │    │
│ └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│ ─────────────────────────────────────────────────────────────────────────── │
│                                                                             │
│ AUDIO DEVICES                                                               │
│                                                                             │
│ Input (Microphone)                                                          │
│ ┌─────────────────────────────────────────────────────────────────────┐    │
│ │ Built-in Microphone                                             ▼   │    │
│ └─────────────────────────────────────────────────────────────────────┘    │
│ [🎤 Test Microphone]  Level: ████████░░░░░░░░░░░░░░░░░░░░░░░░░░             │
│                                                                             │
│ Output (Speaker)                                                            │
│ ┌─────────────────────────────────────────────────────────────────────┐    │
│ │ Built-in Speakers                                               ▼   │    │
│ └─────────────────────────────────────────────────────────────────────┘    │
│ [🔊 Test Speaker]                                                           │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  [Reset to Default]                                    [Save Changes]       │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Django Ninja API Endpoints

```python
# Voice Settings API
@router.get("/settings/voice", response=VoiceSettingsSchema)
async def get_voice_settings(request):
    """GET /api/v2/settings/voice"""
    pass

@router.put("/settings/voice", response=VoiceSettingsSchema)
async def update_voice_settings(request, data: VoiceSettingsSchema):
    """PUT /api/v2/settings/voice"""
    pass

@router.post("/settings/voice/test", response=VoiceTestResultSchema)
async def test_voice_connection(request):
    """POST /api/v2/settings/voice/test"""
    pass

# Pydantic Schema
class VoiceSettingsSchema(Schema):
    enabled: bool = False
    provider: Literal["local", "agentvoicebox"] = "local"
    # Local settings
    stt_engine: str = "whisper"
    stt_model_size: str = "base"
    tts_engine: str = "kokoro"
    tts_voice: str = "am_onyx"
    # AgentVoiceBox settings
    agentvoicebox_url: str = ""
    agentvoicebox_token: SecretStr = ""
    # Common
    tts_speed: float = 1.0
    vad_threshold: float = 0.5
    language: str = "en-US"
    audio_input_device: int = 0
    audio_output_device: int = 0
```

---

## 6. Screen 4: Settings - System Tab

### 6.1 Feature Flags Settings

**Route:** `/settings/system/features`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Settings › System › Feature Flags                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Feature Profile                                                             │
│ ┌─────────────────────────────────────────────────────────────────────┐    │
│ │ Enhanced                                                        ▼   │    │
│ └─────────────────────────────────────────────────────────────────────┘    │
│ Profiles: Minimal | Standard | Enhanced | Maximum                          │
│                                                                             │
│ INDIVIDUAL FLAGS                                          [Reset to Profile]│
│ ┌───────────────────────────────────────────────────────────────────────┐  │
│ │ AI & PROCESSING                                                       │  │
│ │ ──────────────────────────────────────────────────────────────────── │  │
│ │ SSE Streaming               Stream responses in real-time    [🟢 ON] │  │
│ │ Embeddings Ingest           Process embeddings pipeline       [🟢 ON] │  │
│ │ Semantic Recall             SomaBrain memory retrieval        [🟢 ON] │  │
│ │ Learning Context            Track learning progress           [🟢 ON] │  │
│ │ Streaming Responses         LLM streaming mode                [🟢 ON] │  │
│ │                                                                       │  │
│ │ TOOLS & CAPABILITIES                                                  │  │
│ │ ──────────────────────────────────────────────────────────────────── │  │
│ │ Browser Agent               Web browsing capability           [🟢 ON] │  │
│ │ Code Execution              Execute code snippets             [🟢 ON] │  │
│ │ Vision Support              Image analysis                    [🟢 ON] │  │
│ │ Tool Sandboxing             Sandbox tool execution            [🟢 ON] │  │
│ │ Agent Delegation            Multi-agent delegation            [🟢 ON] │  │
│ │                                                                       │  │
│ │ INTEGRATIONS                                                          │  │
│ │ ──────────────────────────────────────────────────────────────────── │  │
│ │ MCP Client                  Connect to MCP servers            [🟢 ON] │  │
│ │ MCP Server                  Expose as MCP server              [🟡 OFF]│  │
│ │ Audio Support               Voice subsystem                   [🟢 ON] │  │
│ │ Voice Local                 Local Whisper/Kokoro              [🟢 ON] │  │
│ │ Voice AgentVoiceBox         External voice service            [🟡 OFF]│  │
│ │                                                                       │  │
│ │ SECURITY                                                              │  │
│ │ ──────────────────────────────────────────────────────────────────── │  │
│ │ Content Masking             Hide sensitive content            [🟢 ON] │  │
│ └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  [Reset All to Default]                                [Save Changes]       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Screen 5: Chat View (STD Mode)

**Route:** `/chat`  
**Component:** `saas-chat-view.ts`  
**Permission:** `chat:send`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ┌─────────┐ │ Support-AI                      [Mode: STD ▼] [☰]            │
│ │   🤖    │ │─────────────────────────────────────────────────────────────│
│ │ Support │ │                                                              │
│ │   -AI   │ │ ┌──────────────────────────────────────────────────────────┐│
│ │         │ │ │                                                          ││
│ │ ─────── │ │ │  🤖 Agent                                     12:34 PM   ││
│ │         │ │ │  Hello! I'm Support-AI. How can I help you today?       ││
│ │ CONVERS.│ │ │                                                          ││
│ │ ─────── │ │ │  ─────────────────────────────────────────────────────  ││
│ │ 📝 New  │ │ │                                                          ││
│ │ 📝 Serve│ │ │  👤 You                                       12:35 PM   ││
│ │ 📝 Data │ │ │  I need help configuring my database connection.        ││
│ │ 📝 Code │ │ │                                                          ││
│ │         │ │ │  ─────────────────────────────────────────────────────  ││
│ │ ─────── │ │ │                                                          ││
│ │ QUICK   │ │ │  🤖 Agent                                     12:35 PM   ││
│ │ ─────── │ │ │  I'd be happy to help! What database are you using?     ││
│ │ 🧠Memory│ │ │                                                          ││
│ │ 🔧Tools │ │ │  • PostgreSQL                                           ││
│ │ ⚙️Setti │ │ │  • MySQL                                                 ││
│ │ 🎨Theme │ │ │  • MongoDB                                               ││
│ │         │ │ │                                                          ││
│ │ ─────── │ │ │  [PostgreSQL] [MySQL] [MongoDB] [Other]                 ││
│ │ [Avatar]│ │ │                                                          ││
│ │ John D. │ │ └──────────────────────────────────────────────────────────┘│
│ │ Member  │ │                                                              │
│ └─────────┘ │ ┌──────────────────────────────────────────────────────────┐│
│             │ │ ➕ │ Type your message...                    🎤 │ ▶️     ││
│             │ └──────────────────────────────────────────────────────────┘│
└─────────────┴──────────────────────────────────────────────────────────────┘
```

### Mode Selector Dropdown

```
┌─────────────────────────────────┐
│ Select Mode                     │
├─────────────────────────────────┤
│ ● STD  Standard Mode            │
│   Normal operation              │
├─────────────────────────────────┤
│ ○ DEV  Developer Mode   [🔒]    │
│   Debug tools, logs             │
│   (Requires developer role)     │
├─────────────────────────────────┤
│ ○ TRN  Training Mode    [🔒]    │
│   Cognitive parameters          │
│   (Requires trainer role)       │
├─────────────────────────────────┤
│ ○ RO   Read-Only Mode           │
│   View only, no actions         │
└─────────────────────────────────┘
```

---

## 8. Screen 6: Memory View

**Route:** `/memory`  
**Component:** `saas-memory-view.ts`  
**Permission:** `memory:read`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Memory Browser                            [🔍 Search] [+ Add Memory]       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ [All] [Conversations] [Facts] [Episodes] [Semantic]     [Sort: Newest ▼]   │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │                                                                         ││
│ │ 🔵 CONVERSATION • Dec 22, 2024 14:32                   [☰]              ││
│ │ Database configuration help                                             ││
│ │ "User asked about PostgreSQL connection pooling..."                     ││
│ │ Tags: #database #postgresql #configuration                              ││
│ │ Relevance: 0.92                                                         ││
│ │                                                                         ││
│ │ ─────────────────────────────────────────────────────────────────────── ││
│ │                                                                         ││
│ │ 🟢 FACT • Dec 21, 2024 10:15                           [☰]              ││
│ │ User prefers PostgreSQL for production databases                        ││
│ │ Confidence: 0.95 • Source: Conversation                                 ││
│ │                                                                         ││
│ │ ─────────────────────────────────────────────────────────────────────── ││
│ │                                                                         ││
│ │ 🟣 EPISODE • Dec 20, 2024 16:45                        [☰]              ││
│ │ Successfully helped user migrate from MySQL to PostgreSQL               ││
│ │ Duration: 45 min • Outcome: Positive                                    ││
│ │                                                                         ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ Showing 1-3 of 156 memories                    [← 1  2  3 ... 52 →]       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Memory Actions Menu [☰]

```
┌─────────────────────────┐
│ 👁️  View Details        │
│ 📋  Copy Content        │
│ 🏷️  Edit Tags           │
│ ───────────────────────│
│ 🗑️  Delete       [🔒]   │  ← Requires memory:delete
│ 📤  Export       [🔒]   │  ← Requires memory:export
└─────────────────────────┘
```

---

## 9. Screen 7: Cognitive Panel (TRN Mode)

**Route:** `/cognitive`  
**Component:** `saas-cognitive-panel.ts`  
**Permission:** `cognitive:view`, `cognitive:edit`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Cognitive Panel                                            [Mode: TRN]     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ NEUROMODULATOR SYSTEM (ACE Framework)                                       │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │                                                                         ││
│ │ Dopamine (Reward/Motivation)                                            ││
│ │ Low ─────────────────●───────────────────────────── High                ││
│ │     0.0              0.72                          1.0    [Reset]       ││
│ │                                                                         ││
│ │ Serotonin (Emotional Stability)                                         ││
│ │ Low ────────────────●────────────────────────────── High                ││
│ │     0.0            0.65                            1.0    [Reset]       ││
│ │                                                                         ││
│ │ Norepinephrine (Alertness/Focus)                                        ││
│ │ Low ───────────●─────────────────────────────────── High                ││
│ │     0.0       0.48                                 1.0    [Reset]       ││
│ │                                                                         ││
│ │ Acetylcholine (Learning/Memory)                                         ││
│ │ Low ────────────────────────●───────────────────── High                 ││
│ │     0.0                    0.81                    1.0    [Reset]       ││
│ │                                                                         ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ ADAPTATION PARAMETERS                                                       │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ Learning Rate          Adaptation Weights        Consolidation Interval ││
│ │ ┌─────────────────┐    ┌─────────────────┐       ┌─────────────────┐   ││
│ │ │ 0.001           │    │ 1.2             │       │ 24 hours        │   ││
│ │ └─────────────────┘    └─────────────────┘       └─────────────────┘   ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ ACTIONS                                                                     │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ [🔄 Trigger Sleep Cycle]  [🧹 Reset Adaptation]  [📊 Export Data]       ││
│ │                                                                         ││
│ │ Last Sleep Cycle: 2 hours ago                                           ││
│ │ Memories Consolidated: 45                                               ││
│ │ Adaptation Loops: 234                                                   ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  [Reset All to Default]                                [Apply Changes]      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Complete Screen List by Mode

### 10.1 STD (Standard) Mode - All Users

| # | Screen | Route | Component | Permissions |
|---|--------|-------|-----------|-------------|
| 1 | Chat View | `/chat` | `saas-chat-view.ts` | `chat:send` |
| 2 | Memory Browser | `/memory` | `saas-memory-view.ts` | `memory:read` |
| 3 | Tools List | `/tools` | `saas-tools-view.ts` | `tools:execute` |
| 4 | Settings | `/settings` | `saas-settings.ts` | `settings:view` |
| 5 | Themes | `/themes` | `saas-themes-view.ts` | All |
| 6 | Profile | `/profile` | `saas-profile.ts` | All |

### 10.2 TRN (Training) Mode - Trainers

| # | Screen | Route | Component | Permissions |
|---|--------|-------|-----------|-------------|
| 1 | Cognitive Panel | `/cognitive` | `saas-cognitive-panel.ts` | `cognitive:view` |
| 2 | Training Sessions | `/training` | `saas-training-view.ts` | `cognitive:view` |
| 3 | Learning Curves | `/training/curves` | `saas-learning-curves.ts` | `cognitive:view` |
| 4 | Adaptation History | `/training/history` | `saas-adaptation-history.ts` | `cognitive:view` |

### 10.3 DEV (Developer) Mode

| # | Screen | Route | Component | Permissions |
|---|--------|-------|-----------|-------------|
| 1 | Debug Console | `/dev/console` | `saas-debug-console.ts` | `tools:debug` |
| 2 | API Logs | `/dev/logs` | `saas-api-logs.ts` | `tools:debug` |
| 3 | MCP Inspector | `/dev/mcp` | `saas-mcp-inspector.ts` | `tools:debug` |
| 4 | Component Playground | `/dev/playground` | `saas-playground.ts` | `tools:debug` |

### 10.4 ADM (Admin) Mode - Tenant Admins

| # | Screen | Route | Component | Permissions |
|---|--------|-------|-----------|-------------|
| 1 | Agent Configuration | `/admin/config` | `saas-agent-config.ts` | `agent:configure` |
| 2 | Agent Users | `/admin/users` | `saas-agent-users.ts` | `admin:users` |
| 3 | Model Selection | `/admin/models` | `saas-model-select.ts` | `settings:models` |
| 4 | API Key Management | `/admin/keys` | `saas-api-keys.ts` | `settings:api_keys` |

---

## 11. Django Ninja API Summary

```python
# All Django Ninja routes for Agent UI

# Settings
GET/PUT /api/v2/settings/agent/chat-model
GET/PUT /api/v2/settings/agent/utility-model
GET/PUT /api/v2/settings/agent/browser-model
GET/PUT /api/v2/settings/agent/embedding-model
GET/PUT /api/v2/settings/agent/memory
GET/PUT /api/v2/settings/external/api-keys
GET/PUT /api/v2/settings/external/mcp-client
GET/PUT /api/v2/settings/external/mcp-server
GET/PUT /api/v2/settings/connectivity/voice
GET/PUT /api/v2/settings/connectivity/proxy
GET/PUT /api/v2/settings/system/features
GET/PUT /api/v2/settings/system/auth

# Chat
GET    /api/v2/chat/conversations
POST   /api/v2/chat/conversations
GET    /api/v2/chat/conversations/{id}/messages
POST   /api/v2/chat/conversations/{id}/messages
DELETE /api/v2/chat/conversations/{id}

# Memory (SomaBrain)
GET    /api/v2/memory
POST   /api/v2/memory
GET    /api/v2/memory/{id}
PUT    /api/v2/memory/{id}
DELETE /api/v2/memory/{id}
POST   /api/v2/memory/search

# Cognitive (TRN Mode)
GET    /api/v2/cognitive/neuromodulators
PUT    /api/v2/cognitive/neuromodulators
GET    /api/v2/cognitive/adaptation
PUT    /api/v2/cognitive/adaptation
POST   /api/v2/cognitive/sleep-cycle
POST   /api/v2/cognitive/reset

# Voice
POST   /api/v2/voice/transcribe
POST   /api/v2/voice/synthesize
GET    /api/v2/voice/voices
POST   /api/v2/voice/test
```

---

**Document Status:** CANONICAL — Complete  
**Stack:** Django 5.x + Django Ninja + Lit 3.x + SpiceDB
# Eye of God UIX — Technical Design Document

## Document Control

| Field | Value |
|-------|-------|
| **Document ID** | SA01-EOG-DES-2025-12 |
| **Version** | 1.0 |
| **Date** | 2025-12-21 |
| **Status** | DRAFT |
| **Classification** | CANONICAL |
| **Implements** | SA01-EOG-REQ-2025-12 |

---

## 1. Architecture Overview

### 1.1 System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                         │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│   Web Browser   │  Tauri Desktop  │   Rust CLI      │   External A2A        │
│   (Lit 3.x)     │  (Lit + Rust)   │   (Ratatui)     │   Agents              │
└────────┬────────┴────────┬────────┴────────┬────────┴───────────┬───────────┘
         │                 │                 │                     │
         │ HTTPS/WSS       │ IPC + HTTPS     │ HTTPS               │ HTTPS
         ▼                 ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DJANGO NINJA API GATEWAY                             │
│                              (Port 8020)                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ REST API     │  │ WebSocket    │  │ OpenAPI 3.1  │  │ Rate Limiter │    │
│  │ (Ninja)      │  │ (Channels)   │  │ Schema       │  │ (Redis)      │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└────────┬────────────────┬────────────────┬────────────────┬─────────────────┘
         │                │                │                │
         ▼                ▼                ▼                ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│    SpiceDB      │ │   PostgreSQL    │ │     Redis       │ │     Kafka       │
│  (Permissions)  │ │   (Primary DB)  │ │   (Cache/WS)    │ │   (Events)      │
│  Port 50051     │ │   Port 5432     │ │   Port 6379     │ │   Port 9092     │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘
```

### 1.2 Parallel Build Strategy

**CRITICAL**: This is a PARALLEL BUILD, not a replacement of FastAPI.

| Component | Current (FastAPI) | New (Django Ninja) | Coexistence |
|-----------|-------------------|--------------------| ------------|
| Gateway | Port 8010 | Port 8020 | Both run simultaneously |
| WebUI | `/webui/` (Alpine.js) | `/ui/` (Lit 3.x) | Both served |
| API Prefix | `/v1/` | `/api/v2/` | No collision |
| WebSocket | `/ws/` | `/ws/v2/` | Separate channels |

**Migration Path:**
1. Phase 1: Django Ninja runs alongside FastAPI (feature parity)
2. Phase 2: Lit UI consumes Django Ninja API exclusively
3. Phase 3: Gradual traffic migration via nginx routing
4. Phase 4: FastAPI deprecated after 6-month overlap

---

## 2. Component Design

### 2.1 Django Project Structure

```
somaAgent01/ui/
├── backend/                          # Django + Django Ninja
│   ├── eog/                          # Django project root
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # Common settings
│   │   │   ├── development.py        # Dev overrides
│   │   │   └── production.py         # Prod overrides
│   │   ├── urls.py                   # Root URL config
│   │   ├── asgi.py                   # ASGI entry (Channels)
│   │   └── wsgi.py                   # WSGI fallback
│   │
│   ├── api/                          # Django Ninja API app
│   │   ├── __init__.py
│   │   ├── router.py                 # Main NinjaAPI instance
│   │   ├── schemas/                  # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── settings.py
│   │   │   ├── themes.py
│   │   │   ├── modes.py
│   │   │   ├── memory.py
│   │   │   └── tools.py
│   │   ├── endpoints/                # API endpoint modules
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # /api/v2/auth/*
│   │   │   ├── settings.py           # /api/v2/settings/*
│   │   │   ├── themes.py             # /api/v2/themes/*
│   │   │   ├── modes.py              # /api/v2/modes/*
│   │   │   ├── memory.py             # /api/v2/memory/*
│   │   │   ├── tools.py              # /api/v2/tools/*
│   │   │   ├── cognitive.py          # /api/v2/cognitive/*
│   │   │   └── admin.py              # /api/v2/admin/*
│   │   └── middleware/
│   │       ├── __init__.py
│   │       ├── tenant.py             # X-Tenant-Id extraction
│   │       ├── permission.py         # SpiceDB check
│   │       └── audit.py              # Audit logging
│   │
│   ├── core/                         # Django models app
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── tenant.py
│   │   │   ├── user.py
│   │   │   ├── settings.py
│   │   │   ├── theme.py
│   │   │   ├── feature_flag.py
│   │   │   └── audit_log.py
│   │   ├── admin.py
│   │   └── migrations/
│   │
│   ├── permissions/                  # SpiceDB integration
│   │   ├── __init__.py
│   │   ├── client.py                 # SpiceDB gRPC client
│   │   ├── schema.zed                # Permission schema
│   │   └── decorators.py             # @require_permission
│   │
│   ├── realtime/                     # Django Channels
│   │   ├── __init__.py
│   │   ├── consumers.py              # WebSocket consumers
│   │   ├── routing.py                # WS URL routing
│   │   └── events.py                 # Event types
│   │
│   ├── manage.py
│   ├── requirements.txt
│   └── pyproject.toml
```

### 2.2 Lit Frontend Structure

```
somaAgent01/ui/
├── frontend/                         # Lit Web Components
│   ├── src/
│   │   ├── components/               # Reusable UI components
│   │   │   ├── eog-button.ts         # <eog-button>
│   │   │   ├── eog-input.ts          # <eog-input>
│   │   │   ├── eog-select.ts         # <eog-select>
│   │   │   ├── eog-toggle.ts         # <eog-toggle>
│   │   │   ├── eog-slider.ts         # <eog-slider>
│   │   │   ├── eog-modal.ts          # <eog-modal>
│   │   │   ├── eog-toast.ts          # <eog-toast>
│   │   │   ├── eog-card.ts           # <eog-card>
│   │   │   ├── eog-tabs.ts           # <eog-tabs>
│   │   │   └── index.ts              # Barrel export
│   │   │
│   │   ├── views/                    # Page-level components
│   │   │   ├── eog-app.ts            # Root app shell
│   │   │   ├── eog-chat.ts           # Chat interface
│   │   │   ├── eog-settings.ts       # Settings panel
│   │   │   ├── eog-themes.ts         # Theme gallery
│   │   │   ├── eog-memory.ts         # Memory browser
│   │   │   ├── eog-tools.ts          # Tool catalog
│   │   │   ├── eog-cognitive.ts      # Cognitive panel
│   │   │   ├── eog-admin.ts          # Admin dashboard
│   │   │   └── eog-audit.ts          # Audit logs
│   │   │
│   │   ├── stores/                   # State management (Lit Context)
│   │   │   ├── auth-store.ts         # Auth state + token
│   │   │   ├── mode-store.ts         # Agent mode state
│   │   │   ├── settings-store.ts     # Settings cache
│   │   │   ├── theme-store.ts        # Active theme
│   │   │   └── permission-store.ts   # Permission cache
│   │   │
│   │   ├── services/                 # API clients
│   │   │   ├── api-client.ts         # Base fetch wrapper
│   │   │   ├── websocket-client.ts   # WS connection manager
│   │   │   ├── auth-service.ts       # Auth API calls
│   │   │   ├── settings-service.ts   # Settings API calls
│   │   │   ├── theme-service.ts      # Theme API calls
│   │   │   └── permission-service.ts # SpiceDB proxy calls
│   │   │
│   │   ├── styles/                   # Global styles
│   │   │   ├── tokens.css            # CSS custom properties
│   │   │   ├── reset.css             # CSS reset
│   │   │   └── themes/
│   │   │       ├── default-light.json
│   │   │       └── midnight-dark.json
│   │   │
│   │   ├── utils/                    # Utilities
│   │   │   ├── validators.ts         # Input validation
│   │   │   ├── formatters.ts         # Data formatting
│   │   │   └── constants.ts          # App constants
│   │   │
│   │   └── index.ts                  # Entry point
│   │
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   │
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── web-test-runner.config.js
```

### 2.3 SpiceDB Permission Schema

```zed
// File: somaAgent01/ui/backend/permissions/schema.zed

definition user {}

definition tenant {
    relation sysadmin: user
    relation admin: user
    relation developer: user
    relation trainer: user
    relation member: user
    relation viewer: user
    
    // Computed permissions
    permission manage = sysadmin
    permission administrate = sysadmin + admin
    permission develop = sysadmin + admin + developer
    permission train = sysadmin + admin + trainer
    permission use = sysadmin + admin + developer + trainer + member
    permission view = sysadmin + admin + developer + trainer + member + viewer
}

definition agent_mode {
    relation tenant: tenant
    relation allowed_role: tenant#admin | tenant#developer | tenant#trainer | tenant#member | tenant#viewer
    
    permission activate = allowed_role
}

definition setting_section {
    relation tenant: tenant
    relation edit_role: tenant#sysadmin | tenant#admin
    relation view_role: tenant#sysadmin | tenant#admin | tenant#developer | tenant#trainer | tenant#member | tenant#viewer
    
    permission edit = edit_role
    permission view = view_role
}

definition cognitive_parameter {
    relation tenant: tenant
    
    permission view = tenant->view
    permission edit = tenant->train + tenant->administrate
}

definition theme {
    relation tenant: tenant
    relation owner: user
    
    permission view = tenant->view
    permission apply = tenant->use
    permission edit = owner + tenant->administrate
    permission delete = tenant->administrate
}

definition tool {
    relation tenant: tenant
    relation required_mode: agent_mode
    
    permission execute = tenant->use & required_mode->activate
    permission view = tenant->view
    permission configure = tenant->administrate
}

definition memory {
    relation tenant: tenant
    
    permission read = tenant->view
    permission write = tenant->use
    permission delete = tenant->administrate
    permission export = tenant->administrate
}
```

---

## 3. API Design

### 3.1 Django Ninja Router Configuration

```python
# File: somaAgent01/ui/backend/api/router.py

from ninja import NinjaAPI
from ninja.security import HttpBearer

class BearerAuth(HttpBearer):
    def authenticate(self, request, token: str):
        # Validate JWT token
        # Return user or None
        pass

api = NinjaAPI(
    title="Eye of God API",
    version="2.0.0",
    urls_namespace="eog_api",
    auth=BearerAuth(),
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# Register endpoint routers
from api.endpoints import auth, settings, themes, modes, memory, tools, cognitive, admin

api.add_router("/auth", auth.router, tags=["Authentication"])
api.add_router("/settings", settings.router, tags=["Settings"])
api.add_router("/themes", themes.router, tags=["Themes"])
api.add_router("/modes", modes.router, tags=["Agent Modes"])
api.add_router("/memory", memory.router, tags=["Memory"])
api.add_router("/tools", tools.router, tags=["Tools"])
api.add_router("/cognitive", cognitive.router, tags=["Cognitive"])
api.add_router("/admin", admin.router, tags=["Admin"])
```

### 3.2 Endpoint Mapping (FastAPI → Django Ninja)

| FastAPI Endpoint | Django Ninja Endpoint | Notes |
|------------------|----------------------|-------|
| `GET /v1/health` | `GET /api/v2/health` | Health check |
| `GET /v1/sessions` | `GET /api/v2/sessions` | Session list |
| `POST /v1/llm/invoke` | `POST /api/v2/llm/invoke` | LLM invocation |
| `GET /v1/runtime-config` | `GET /api/v2/settings/runtime` | Runtime config |
| `GET /v1/capsules` | `GET /api/v2/capsules` | Capsule registry |
| `POST /v1/chat` | `POST /api/v2/chat` | Chat message |
| `GET /v1/memory/recall` | `GET /api/v2/memory/recall` | Memory recall |
| `POST /v1/memory/remember` | `POST /api/v2/memory/remember` | Memory store |
| `GET /v1/tools` | `GET /api/v2/tools` | Tool catalog |
| `POST /v1/tools/execute` | `POST /api/v2/tools/execute` | Tool execution |
| `GET /v1/feature-flags` | `GET /api/v2/settings/flags` | Feature flags |
| `WS /ws/chat` | `WS /ws/v2/chat` | Chat WebSocket |
| `WS /ws/events` | `WS /ws/v2/events` | Event stream |

### 3.3 Schema Examples

```python
# File: somaAgent01/ui/backend/api/schemas/settings.py

from ninja import Schema
from typing import Optional, Dict, Any
from enum import Enum

class SettingsTab(str, Enum):
    AGENT = "agent"
    EXTERNAL = "external"
    CONNECTIVITY = "connectivity"
    SYSTEM = "system"

class ModelConfig(Schema):
    provider: str
    model: str
    context_length: int = 4096
    rpm: int = 60
    tpm: int = 100000
    vision: bool = False

class AgentSettings(Schema):
    chat_model: ModelConfig
    utility_model: ModelConfig
    browser_model: Optional[ModelConfig] = None
    embedding_model: Optional[ModelConfig] = None
    memory_enabled: bool = True
    recall_interval: int = 30
    max_memories: int = 100
    similarity_threshold: float = 0.7

class SettingsResponse(Schema):
    tab: SettingsTab
    data: Dict[str, Any]
    updated_at: str
    version: int

class SettingsUpdateRequest(Schema):
    tab: SettingsTab
    data: Dict[str, Any]
    version: int  # Optimistic locking
```

```python
# File: somaAgent01/ui/backend/api/schemas/themes.py

from ninja import Schema
from typing import Optional, Dict, List
from pydantic import HttpUrl

class ThemeVariables(Schema):
    bg_void: str
    glass_surface: str
    glass_border: str
    text_main: str
    text_dim: str
    accent_slate: str
    # ... 26 total variables

class Theme(Schema):
    id: str
    name: str
    version: str
    author: str
    description: Optional[str] = None
    variables: ThemeVariables
    preview_url: Optional[HttpUrl] = None
    downloads: int = 0
    rating: float = 0.0
    tags: List[str] = []

class ThemeListResponse(Schema):
    themes: List[Theme]
    total: int
    page: int
    page_size: int
```

---

## 4. Lit Component Design

### 4.1 Base Component Pattern

```typescript
// File: somaAgent01/ui/frontend/src/components/eog-button.ts

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('eog-button')
export class EogButton extends LitElement {
  static styles = css`
    :host {
      display: inline-block;
    }
    
    button {
      padding: var(--eog-spacing-sm) var(--eog-spacing-md);
      border-radius: var(--eog-radius-md);
      border: 1px solid var(--eog-border-color);
      background: var(--eog-surface);
      color: var(--eog-text-main);
      font-family: var(--eog-font-sans);
      font-size: var(--eog-text-sm);
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    
    button:hover:not(:disabled) {
      background: var(--eog-surface-hover);
      border-color: var(--eog-border-hover);
    }
    
    button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    
    button.primary {
      background: var(--eog-accent);
      color: white;
      border-color: var(--eog-accent);
    }
    
    button.danger {
      background: var(--eog-danger);
      color: white;
      border-color: var(--eog-danger);
    }
  `;

  @property({ type: String }) variant: 'default' | 'primary' | 'danger' = 'default';
  @property({ type: Boolean }) disabled = false;
  @property({ type: Boolean }) loading = false;

  render() {
    return html`
      <button
        class=${this.variant}
        ?disabled=${this.disabled || this.loading}
        @click=${this._handleClick}
      >
        ${this.loading ? html`<eog-spinner size="sm"></eog-spinner>` : ''}
        <slot></slot>
      </button>
    `;
  }

  private _handleClick(e: Event) {
    if (!this.disabled && !this.loading) {
      this.dispatchEvent(new CustomEvent('eog-click', {
        bubbles: true,
        composed: true,
        detail: { originalEvent: e }
      }));
    }
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'eog-button': EogButton;
  }
}
```

### 4.2 Store Pattern (Lit Context)

```typescript
// File: somaAgent01/ui/frontend/src/stores/mode-store.ts

import { createContext } from '@lit/context';
import { LitElement, html } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { provide } from '@lit/context';

export type AgentMode = 'STD' | 'TRN' | 'ADM' | 'DEV' | 'RO' | 'DGR';

export interface ModeState {
  current: AgentMode;
  available: AgentMode[];
  loading: boolean;
  error: string | null;
}

export const modeContext = createContext<ModeState>('mode-state');

@customElement('eog-mode-provider')
export class EogModeProvider extends LitElement {
  @provide({ context: modeContext })
  @property({ attribute: false })
  state: ModeState = {
    current: 'STD',
    available: ['STD'],
    loading: false,
    error: null,
  };

  async setMode(mode: AgentMode): Promise<void> {
    this.state = { ...this.state, loading: true, error: null };
    
    try {
      const response = await fetch('/api/v2/modes/current', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to set mode: ${response.status}`);
      }
      
      const data = await response.json();
      this.state = { ...this.state, current: data.mode, loading: false };
      
      // Dispatch event for WebSocket sync
      this.dispatchEvent(new CustomEvent('mode-changed', {
        bubbles: true,
        composed: true,
        detail: { mode: data.mode }
      }));
    } catch (error) {
      this.state = { ...this.state, loading: false, error: String(error) };
    }
  }

  render() {
    return html`<slot></slot>`;
  }
}
```

### 4.3 API Client Service

```typescript
// File: somaAgent01/ui/frontend/src/services/api-client.ts

export interface ApiClientConfig {
  baseUrl: string;
  timeout: number;
  retries: number;
}

export class ApiClient {
  private config: ApiClientConfig;
  private token: string | null = null;

  constructor(config: Partial<ApiClientConfig> = {}) {
    this.config = {
      baseUrl: config.baseUrl ?? '/api/v2',
      timeout: config.timeout ?? 30000,
      retries: config.retries ?? 3,
    };
  }

  setToken(token: string): void {
    this.token = token;
  }

  async request<T>(
    method: string,
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.config.baseUrl}${path}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
      ...(options.headers ?? {}),
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

    try {
      const response = await fetch(url, {
        method,
        headers,
        signal: controller.signal,
        ...options,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new ApiError(response.status, error.detail ?? 'Request failed');
      }

      return response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof ApiError) throw error;
      throw new ApiError(0, String(error));
    }
  }

  get<T>(path: string): Promise<T> {
    return this.request<T>('GET', path);
  }

  post<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>('POST', path, { body: JSON.stringify(body) });
  }

  put<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>('PUT', path, { body: JSON.stringify(body) });
  }

  delete<T>(path: string): Promise<T> {
    return this.request<T>('DELETE', path);
  }
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export const apiClient = new ApiClient();
```


---

## 5. Voice System Design

### 5.1 Voice Provider Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         VOICE PROVIDER ABSTRACTION                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      VoiceProviderInterface                          │   │
│   │  + start_session() -> SessionId                                      │   │
│   │  + stop_session(session_id)                                          │   │
│   │  + transcribe(audio_bytes) -> str                                    │   │
│   │  + synthesize(text) -> audio_bytes                                   │   │
│   │  + is_available() -> bool                                            │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                    ▲                              ▲                          │
│                    │                              │                          │
│   ┌────────────────┴────────────┐  ┌─────────────┴──────────────────┐      │
│   │     LocalVoiceProvider      │  │   AgentVoiceBoxProvider        │      │
│   │  - whisper_model            │  │  - ws_connection               │      │
│   │  - kokoro_model             │  │  - api_token                   │      │
│   │  - vad_detector             │  │  - realtime_session            │      │
│   │  - audio_capture            │  │  - turn_detector               │      │
│   └─────────────────────────────┘  └────────────────────────────────┘      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Local Voice Implementation

```python
# File: somaAgent01/ui/backend/voice/local_provider.py

from dataclasses import dataclass
from typing import Optional
import numpy as np

@dataclass
class LocalVoiceConfig:
    stt_engine: str = "whisper"
    stt_model_size: str = "base"
    tts_engine: str = "kokoro"
    tts_voice: str = "am_onyx"
    tts_speed: float = 1.0
    vad_threshold: float = 0.5
    language: str = "en-US"
    sample_rate: int = 24000

class LocalVoiceProvider:
    """Local voice provider using Whisper STT + Kokoro TTS.
    
    NOTE: Does NOT support real-time speech-on-speech.
    For speech-on-speech, use AgentVoiceBoxProvider.
    """
    
    def __init__(self, config: LocalVoiceConfig):
        self.config = config
        self._whisper_model = None
        self._kokoro_model = None
        self._vad = None
    
    async def initialize(self) -> None:
        """Load models based on detected hardware (CPU/GPU)."""
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load Whisper
        if self.config.stt_engine == "whisper":
            import whisper
            self._whisper_model = whisper.load_model(
                self.config.stt_model_size,
                device=device
            )
        
        # Load Kokoro
        if self.config.tts_engine == "kokoro":
            from kokoro import KokoroTTS
            self._kokoro_model = KokoroTTS(
                voice=self.config.tts_voice,
                device=device
            )
    
    async def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio to text using Whisper."""
        result = self._whisper_model.transcribe(
            audio,
            language=self.config.language[:2]
        )
        return result["text"]
    
    async def synthesize(self, text: str) -> np.ndarray:
        """Synthesize text to audio using Kokoro."""
        audio = self._kokoro_model.generate(
            text,
            speed=self.config.tts_speed
        )
        return audio
    
    def is_available(self) -> bool:
        return self._whisper_model is not None and self._kokoro_model is not None
```


### 5.3 AgentVoiceBox Provider Implementation

```python
# File: somaAgent01/ui/backend/voice/agentvoicebox_provider.py

from dataclasses import dataclass
from typing import Optional, Callable
import asyncio
import websockets
import json

@dataclass
class AgentVoiceBoxConfig:
    base_url: str = ""
    ws_url: str = ""
    api_token: str = ""
    model: str = "ovos-voice-1"
    voice: str = "default"
    turn_detection: bool = True
    input_audio_format: str = "pcm16"
    output_audio_format: str = "pcm16"

class AgentVoiceBoxProvider:
    """AgentVoiceBox provider for full speech-on-speech capability.
    
    Connects to AgentVoiceBox server via WebSocket for real-time
    bidirectional audio streaming with OpenAI Realtime API compatibility.
    """
    
    def __init__(self, config: AgentVoiceBoxConfig):
        self.config = config
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._session_id: Optional[str] = None
        self._on_transcription: Optional[Callable] = None
        self._on_audio: Optional[Callable] = None
    
    async def connect(self) -> str:
        """Establish WebSocket connection to AgentVoiceBox."""
        headers = {"Authorization": f"Bearer {self.config.api_token}"}
        self._ws = await websockets.connect(
            self.config.ws_url,
            extra_headers=headers
        )
        
        # Send session.create
        await self._ws.send(json.dumps({
            "type": "session.create",
            "session": {
                "model": self.config.model,
                "voice": self.config.voice,
                "turn_detection": {"type": "server_vad"} if self.config.turn_detection else None,
                "input_audio_format": self.config.input_audio_format,
                "output_audio_format": self.config.output_audio_format,
            }
        }))
        
        # Wait for session.created
        response = json.loads(await self._ws.recv())
        if response["type"] == "session.created":
            self._session_id = response["session"]["id"]
            return self._session_id
        raise ConnectionError(f"Failed to create session: {response}")
    
    async def send_audio(self, audio_base64: str) -> None:
        """Send audio chunk to AgentVoiceBox."""
        await self._ws.send(json.dumps({
            "type": "input_audio_buffer.append",
            "audio": audio_base64
        }))
    
    async def listen(self) -> None:
        """Listen for events from AgentVoiceBox."""
        async for message in self._ws:
            event = json.loads(message)
            event_type = event.get("type")
            
            if event_type == "conversation.item.input_audio_transcription.completed":
                if self._on_transcription:
                    await self._on_transcription(event["transcript"])
            
            elif event_type == "response.audio.delta":
                if self._on_audio:
                    await self._on_audio(event["delta"])
    
    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        if self._ws:
            await self._ws.close()
            self._ws = None
            self._session_id = None
```


---

## 6. AgentSkin Theme System Design

### 6.1 Theme Manager Implementation

```typescript
// File: somaAgent01/ui/frontend/src/services/theme-manager.ts

import { Theme, ThemeVariables } from '../types/theme';

const THEME_STORAGE_KEY = 'eog-active-theme';
const CSS_VAR_PREFIX = '--eog-';

export class ThemeManager {
  private activeTheme: Theme | null = null;
  private root: HTMLElement;

  constructor() {
    this.root = document.documentElement;
  }

  async loadTheme(theme: Theme): Promise<void> {
    // Validate theme
    this.validateTheme(theme);
    
    // Apply CSS variables
    this.applyVariables(theme.variables);
    
    // Store active theme
    this.activeTheme = theme;
    localStorage.setItem(THEME_STORAGE_KEY, JSON.stringify(theme));
    
    // Dispatch event
    window.dispatchEvent(new CustomEvent('theme-changed', { detail: theme }));
  }

  private validateTheme(theme: Theme): void {
    // Check required variables (26 minimum)
    const required = [
      'bg_void', 'glass_surface', 'glass_border', 'text_main', 'text_dim',
      'accent_primary', 'accent_secondary', 'accent_success', 'accent_warning', 'accent_danger',
      'shadow_soft', 'radius_sm', 'radius_md', 'radius_lg', 'radius_full',
      'spacing_xs', 'spacing_sm', 'spacing_md', 'spacing_lg', 'spacing_xl',
      'font_sans', 'font_mono', 'text_xs', 'text_sm', 'text_base', 'text_lg'
    ];
    
    for (const key of required) {
      if (!(key in theme.variables)) {
        throw new Error(`Missing required theme variable: ${key}`);
      }
    }
    
    // Security: Check for url() in values (XSS prevention)
    for (const [key, value] of Object.entries(theme.variables)) {
      if (typeof value === 'string' && value.includes('url(')) {
        throw new Error(`Security violation: url() not allowed in theme variable: ${key}`);
      }
    }
    
    // Validate contrast ratios (WCAG AA)
    this.validateContrast(theme.variables);
  }

  private validateContrast(vars: ThemeVariables): void {
    // Calculate contrast ratio between text and background
    const bgColor = this.parseColor(vars.bg_void);
    const textColor = this.parseColor(vars.text_main);
    const ratio = this.contrastRatio(bgColor, textColor);
    
    if (ratio < 4.5) {
      console.warn(`Theme contrast ratio ${ratio.toFixed(2)} is below WCAG AA (4.5:1)`);
    }
  }

  private applyVariables(variables: ThemeVariables): void {
    for (const [key, value] of Object.entries(variables)) {
      const cssVar = `${CSS_VAR_PREFIX}${key.replace(/_/g, '-')}`;
      this.root.style.setProperty(cssVar, value);
    }
  }

  // Color utility methods
  private parseColor(color: string): [number, number, number] { /* ... */ }
  private luminance(r: number, g: number, b: number): number { /* ... */ }
  private contrastRatio(c1: [number, number, number], c2: [number, number, number]): number { /* ... */ }
}

export const themeManager = new ThemeManager();
```


### 6.2 Default Themes

```json
// File: somaAgent01/ui/frontend/src/styles/themes/midnight-dark.json
{
  "name": "Midnight Dark",
  "version": "1.0.0",
  "author": "SomaAgent Team",
  "description": "Dark theme with blue accents and glassmorphism",
  "category": "Professional",
  "tags": ["dark", "glassmorphism", "professional"],
  "variables": {
    "bg_void": "#0f172a",
    "glass_surface": "rgba(30, 41, 59, 0.85)",
    "glass_border": "rgba(255, 255, 255, 0.05)",
    "text_main": "#e2e8f0",
    "text_dim": "#64748b",
    "accent_primary": "#3b82f6",
    "accent_secondary": "#8b5cf6",
    "accent_success": "#22c55e",
    "accent_warning": "#f59e0b",
    "accent_danger": "#ef4444",
    "shadow_soft": "0 10px 40px -10px rgba(0, 0, 0, 0.5)",
    "radius_sm": "4px",
    "radius_md": "8px",
    "radius_lg": "16px",
    "radius_full": "9999px",
    "spacing_xs": "4px",
    "spacing_sm": "8px",
    "spacing_md": "16px",
    "spacing_lg": "24px",
    "spacing_xl": "32px",
    "font_sans": "'Space Grotesk', sans-serif",
    "font_mono": "'JetBrains Mono', monospace",
    "text_xs": "10px",
    "text_sm": "12px",
    "text_base": "14px",
    "text_lg": "16px",
    "text_xl": "20px"
  }
}
```

---

## 7. WebSocket Real-Time Design

### 7.1 Django Channels Consumer

```python
# File: somaAgent01/ui/backend/realtime/consumers.py

import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

class EventConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time events."""
    
    async def connect(self):
        # Authenticate
        token = self.scope.get("query_string", b"").decode()
        user = await self.authenticate(token)
        if not user:
            await self.close(code=4001)
            return
        
        self.user = user
        self.tenant_id = user.tenant_id
        self.group_name = f"tenant_{self.tenant_id}"
        
        # Join tenant group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        
        # Send initial state
        await self.send_json({
            "type": "connection.established",
            "user_id": str(user.id),
            "tenant_id": str(self.tenant_id)
        })
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
    
    async def receive_json(self, content):
        event_type = content.get("type")
        
        if event_type == "ping":
            await self.send_json({"type": "pong"})
        elif event_type == "mode.change":
            await self.handle_mode_change(content)
        elif event_type == "settings.update":
            await self.handle_settings_update(content)
    
    # Event handlers for group broadcasts
    async def mode_changed(self, event):
        await self.send_json(event)
    
    async def settings_changed(self, event):
        await self.send_json(event)
    
    async def theme_changed(self, event):
        await self.send_json(event)
    
    async def voice_event(self, event):
        await self.send_json(event)
```


---

## 5. Django Models

### 5.1 Core Models

```python
# File: somaAgent01/ui/backend/core/models/tenant.py

from django.db import models
from django.contrib.postgres.fields import ArrayField
import uuid

class Tenant(models.Model):
    """Multi-tenant organization model."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, unique=True)
    display_name = models.CharField(max_length=256)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='children'
    )
    settings = models.JSONField(default=dict)
    feature_flags = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'eog_tenants'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['parent']),
        ]


class User(models.Model):
    """User model with tenant association."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users')
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=64, unique=True)
    display_name = models.CharField(max_length=128)
    avatar_url = models.URLField(null=True, blank=True)
    roles = ArrayField(models.CharField(max_length=32), default=list)
    preferences = models.JSONField(default=dict)
    last_mode = models.CharField(max_length=8, default='STD')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'eog_users'
        indexes = [
            models.Index(fields=['tenant', 'email']),
            models.Index(fields=['username']),
        ]
```

### 5.2 Settings Models

```python
# File: somaAgent01/ui/backend/core/models/settings.py

from django.db import models
import uuid

class SettingsCategory(models.TextChoices):
    AGENT = 'agent', 'Agent'
    EXTERNAL = 'external', 'External'
    CONNECTIVITY = 'connectivity', 'Connectivity'
    SYSTEM = 'system', 'System'


class TenantSettings(models.Model):
    """Tenant-level settings storage."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='settings_entries')
    category = models.CharField(max_length=32, choices=SettingsCategory.choices)
    key = models.CharField(max_length=128)
    value = models.JSONField()
    is_secret = models.BooleanField(default=False)
    version = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'eog_tenant_settings'
        unique_together = ['tenant', 'category', 'key']
        indexes = [
            models.Index(fields=['tenant', 'category']),
        ]


class UserSettings(models.Model):
    """User-level settings (preferences)."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='settings_entries')
    key = models.CharField(max_length=128)
    value = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'eog_user_settings'
        unique_together = ['user', 'key']
```

### 5.3 Theme Models

```python
# File: somaAgent01/ui/backend/core/models/theme.py

from django.db import models
from django.contrib.postgres.fields import ArrayField
import uuid

class ThemeCategory(models.TextChoices):
    PROFESSIONAL = 'Professional', 'Professional'
    CREATIVE = 'Creative', 'Creative'
    DEVELOPER = 'Developer', 'Developer'
    GAMING = 'Gaming', 'Gaming'
    ACCESSIBILITY = 'Accessibility', 'Accessibility'


class Theme(models.Model):
    """AgentSkin theme storage."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='themes')
    owner = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='themes')
    name = models.CharField(max_length=64)
    version = models.CharField(max_length=16)
    author = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=32, choices=ThemeCategory.choices)
    tags = ArrayField(models.CharField(max_length=32), default=list)
    variables = models.JSONField()  # 26+ CSS custom properties
    preview_url = models.URLField(null=True, blank=True)
    downloads = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    is_default = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'eog_themes'
        unique_together = ['tenant', 'name', 'version']
        indexes = [
            models.Index(fields=['tenant', 'category']),
            models.Index(fields=['is_public']),
        ]
```


### 7.2 Frontend WebSocket Client

```typescript
// File: somaAgent01/ui/frontend/src/services/websocket-client.ts

type EventHandler = (event: any) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private token: string;
  private handlers: Map<string, Set<EventHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private heartbeatInterval: number | null = null;

  constructor(url: string, token: string) {
    this.url = url;
    this.token = token;
  }

  connect(): void {
    this.ws = new WebSocket(`${this.url}?token=${this.token}`);
    
    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.startHeartbeat();
      this.emit('connection.established', {});
    };
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.emit(data.type, data);
    };
    
    this.ws.onclose = (event) => {
      this.stopHeartbeat();
      if (event.code !== 1000) {
        this.reconnect();
      }
    };
    
    this.ws.onerror = () => {
      this.emit('error', { message: 'WebSocket error' });
    };
  }

  private reconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.emit('error', { message: 'Max reconnect attempts reached' });
      return;
    }
    
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;
    
    setTimeout(() => this.connect(), delay);
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = window.setInterval(() => {
      this.send({ type: 'ping' });
    }, 20000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  on(eventType: string, handler: EventHandler): void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set());
    }
    this.handlers.get(eventType)!.add(handler);
  }

  off(eventType: string, handler: EventHandler): void {
    this.handlers.get(eventType)?.delete(handler);
  }

  private emit(eventType: string, data: any): void {
    this.handlers.get(eventType)?.forEach(handler => handler(data));
    this.handlers.get('*')?.forEach(handler => handler({ type: eventType, ...data }));
  }

  send(data: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  disconnect(): void {
    this.stopHeartbeat();
    this.ws?.close(1000);
    this.ws = null;
  }
}
```

---

## 8. SpiceDB Integration Design

### 8.1 Permission Client

```python
# File: somaAgent01/ui/backend/permissions/client.py

from typing import Optional
from authzed.api.v1 import Client, CheckPermissionRequest, CheckPermissionResponse
from authzed.api.v1 import ObjectReference, SubjectReference
import grpc

class SpiceDBClient:
    """SpiceDB client for permission checks."""
    
    def __init__(self, endpoint: str, token: str):
        self.endpoint = endpoint
        self.token = token
        self._client: Optional[Client] = None
    
    def connect(self) -> None:
        credentials = grpc.ssl_channel_credentials()
        self._client = Client(
            self.endpoint,
            credentials,
            options=[("authorization", f"Bearer {self.token}")]
        )
    
    async def check_permission(
        self,
        resource_type: str,
        resource_id: str,
        permission: str,
        subject_type: str,
        subject_id: str
    ) -> bool:
        """Check if subject has permission on resource."""
        request = CheckPermissionRequest(
            resource=ObjectReference(
                object_type=resource_type,
                object_id=resource_id
            ),
            permission=permission,
            subject=SubjectReference(
                object=ObjectReference(
                    object_type=subject_type,
                    object_id=subject_id
                )
            )
        )
        
        response = await self._client.CheckPermission(request)
        return response.permissionship == CheckPermissionResponse.PERMISSIONSHIP_HAS_PERMISSION
```

### 5.4 Voice Configuration Models

```python
# File: somaAgent01/ui/backend/core/models/voice.py

from django.db import models
import uuid

class VoiceProvider(models.TextChoices):
    DISABLED = 'disabled', 'Disabled'
    LOCAL = 'local', 'Local (Whisper/Kokoro)'
    AGENTVOICEBOX = 'agentvoicebox', 'AgentVoiceBox'


class VoiceConfig(models.Model):
    """Voice configuration per tenant."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField('Tenant', on_delete=models.CASCADE, related_name='voice_config')
    enabled = models.BooleanField(default=False)
    provider = models.CharField(max_length=32, choices=VoiceProvider.choices, default='disabled')
    
    # Local Voice Settings
    stt_engine = models.CharField(max_length=32, default='whisper')
    stt_model_size = models.CharField(max_length=16, default='base')
    tts_engine = models.CharField(max_length=32, default='kokoro')
    tts_voice = models.CharField(max_length=64, default='am_onyx')
    tts_speed = models.FloatField(default=1.0)
    vad_threshold = models.FloatField(default=0.5)
    language = models.CharField(max_length=16, default='en-US')
    
    # AgentVoiceBox Settings
    agentvoicebox_url = models.URLField(null=True, blank=True)
    agentvoicebox_ws_url = models.URLField(null=True, blank=True)
    agentvoicebox_token = models.CharField(max_length=256, null=True, blank=True)
    agentvoicebox_model = models.CharField(max_length=64, default='ovos-voice-1')
    
    # Audio Settings
    audio_input_device = models.IntegerField(default=0)
    audio_output_device = models.IntegerField(default=0)
    sample_rate = models.IntegerField(default=24000)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'eog_voice_config'


class FeatureFlag(models.Model):
    """Feature flags per tenant."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='feature_flags_entries')
    name = models.CharField(max_length=64)
    enabled = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'eog_feature_flags'
        unique_together = ['tenant', 'name']


class AuditLog(models.Model):
    """Audit trail for all actions."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=64)
    resource_type = models.CharField(max_length=64)
    resource_id = models.CharField(max_length=128, null=True, blank=True)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'eog_audit_logs'
        indexes = [
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action']),
        ]
```

---

## 6. API Endpoint Schemas

### 6.1 Authentication Endpoints

```python
# File: somaAgent01/ui/backend/api/endpoints/auth.py

from ninja import Router, Schema
from typing import Optional
from datetime import datetime

router = Router()

class LoginRequest(Schema):
    username: str
    password: str
    tenant_id: Optional[str] = None

class LoginResponse(Schema):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: "UserResponse"

class UserResponse(Schema):
    id: str
    email: str
    username: str
    display_name: str
    avatar_url: Optional[str]
    roles: list[str]
    tenant_id: str
    last_mode: str

class RefreshRequest(Schema):
    refresh_token: str

@router.post("/login", response=LoginResponse)
async def login(request, payload: LoginRequest):
    """Authenticate user and return tokens."""
    pass

@router.post("/refresh", response=LoginResponse)
async def refresh(request, payload: RefreshRequest):
    """Refresh access token."""
    pass

@router.post("/logout")
async def logout(request):
    """Invalidate tokens."""
    pass

@router.get("/me", response=UserResponse)
async def get_current_user(request):
    """Get current authenticated user."""
    pass
```


### 8.2 Permission Decorator

```python
# File: somaAgent01/ui/backend/permissions/decorators.py

from functools import wraps
from ninja import Router
from django.http import HttpRequest
from .client import spicedb_client

def require_permission(resource_type: str, permission: str):
    """Decorator to require SpiceDB permission check."""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: HttpRequest, *args, **kwargs):
            user = request.auth
            resource_id = kwargs.get('id') or kwargs.get('resource_id')
            
            has_permission = await spicedb_client.check_permission(
                resource_type=resource_type,
                resource_id=str(resource_id),
                permission=permission,
                subject_type="user",
                subject_id=str(user.id)
            )
            
            if not has_permission:
                return {"error": "Permission denied"}, 403
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

# Usage example:
# @router.get("/settings/{id}")
# @require_permission("setting_section", "view")
# async def get_settings(request, id: str):
#     ...
```

---

## 9. Database Models

### 9.1 Django Models

```python
# File: somaAgent01/ui/backend/core/models/tenant.py

from django.db import models
import uuid

class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'eog_tenants'

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    email = models.EmailField()
    display_name = models.CharField(max_length=255)
    current_mode = models.CharField(max_length=10, default='STD')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'eog_users'
        unique_together = ['tenant', 'email']

class Settings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    tab = models.CharField(max_length=50)
    data = models.JSONField(default=dict)
    version = models.IntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    
    class Meta:
        db_table = 'eog_settings'
        unique_together = ['tenant', 'tab']

class Theme(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=50)
    author = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    variables = models.JSONField()
    is_default = models.BooleanField(default=False)
    downloads = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'eog_themes'

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=255)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'eog_audit_logs'
        indexes = [
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action']),
        ]
```


---

## 10. Deployment Architecture

### 10.1 Docker Compose (Development)

```yaml
# File: somaAgent01/ui/docker-compose.yml

version: '3.8'

services:
  eog-backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8020:8020"
    environment:
      - DATABASE_URL=postgresql://***REMOVED***@postgres:5432/eog
      - REDIS_URL=redis://redis:6379/0
      - SPICEDB_ENDPOINT=spicedb:50051
      - SPICEDB_TOKEN=${SPICEDB_TOKEN}
    depends_on:
      - postgres
      - redis
      - spicedb

  eog-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - API_URL=http://eog-backend:8020

  postgres:
    image: postgres:16
    environment:
      - POSTGRES_DB=eog
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  spicedb:
    image: authzed/spicedb:latest
    command: serve
    environment:
      - SPICEDB_GRPC_PRESHARED_KEY=${SPICEDB_TOKEN}
      - SPICEDB_DATASTORE_ENGINE=postgres
      - SPICEDB_DATASTORE_CONN_URI=postgresql://***REMOVED***@postgres:5432/spicedb
    ports:
      - "50051:50051"
    depends_on:
      - postgres

volumes:
  postgres_data:
  redis_data:
```

### 10.2 Kubernetes Deployment (Production)

```yaml
# File: somaAgent01/ui/k8s/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: eog-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: eog-backend
  template:
    metadata:
      labels:
        app: eog-backend
    spec:
      containers:
        - name: eog-backend
          image: somaagent/eog-backend:latest
          ports:
            - containerPort: 8020
          resources:
            requests:
              memory: "512Mi"
              cpu: "500m"
            limits:
              memory: "2Gi"
              cpu: "2000m"
          livenessProbe:
            httpGet:
              path: /api/v2/health
              port: 8020
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /api/v2/health
              port: 8020
            initialDelaySeconds: 5
            periodSeconds: 5
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: eog-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: eog-backend
  minReplicas: 3
  maxReplicas: 100
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

---

## 11. Observability Design

### 11.1 Prometheus Metrics

```python
# File: somaAgent01/ui/backend/observability/metrics.py

from prometheus_client import Counter, Histogram, Gauge

# Request metrics
REQUEST_COUNT = Counter(
    'eog_request_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'eog_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# WebSocket metrics
WS_CONNECTIONS = Gauge(
    'eog_websocket_connections',
    'Active WebSocket connections',
    ['tenant_id']
)

# Permission metrics
PERMISSION_CHECKS = Counter(
    'eog_permission_checks_total',
    'Total permission checks',
    ['resource_type', 'permission', 'result']
)

PERMISSION_DURATION = Histogram(
    'eog_permission_check_duration_seconds',
    'Permission check duration',
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1]
)

# Theme metrics
THEME_LOADS = Counter(
    'eog_theme_loads_total',
    'Total theme loads',
    ['theme_id']
)

# Mode metrics
MODE_TRANSITIONS = Counter(
    'eog_mode_transitions_total',
    'Total mode transitions',
    ['from_mode', 'to_mode']
)

# Voice metrics
VOICE_SESSIONS = Counter(
    'eog_voice_sessions_total',
    'Total voice sessions',
    ['provider']
)

VOICE_LATENCY = Histogram(
    'eog_voice_latency_seconds',
    'Voice processing latency',
    ['operation'],  # transcribe, synthesize
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)
```

---

## 12. Security Design

### 12.1 Authentication Middleware

```python
# File: somaAgent01/ui/backend/api/middleware/auth.py

from ninja.security import HttpBearer
from django.http import HttpRequest
import jwt
from datetime import datetime

class JWTAuth(HttpBearer):
    def authenticate(self, request: HttpRequest, token: str):
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=["HS256"]
            )
            
            # Check expiration
            if datetime.utcnow().timestamp() > payload.get("exp", 0):
                return None
            
            # Get user
            user = User.objects.get(id=payload["sub"])
            request.tenant_id = payload.get("tenant_id")
            
            return user
        except (jwt.InvalidTokenError, User.DoesNotExist):
            return None
```

---

**Document Status:** COMPLETE

**Implements Requirements:**
- REQ-1 through REQ-25 from requirements.md
- All SRS sections 1-13

**Next Steps:**
1. Create tasks.md with implementation plan
2. Begin Phase 1 implementation (Django Ninja parallel build)


---

## 13. Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Theme Validation Completeness

*For any* theme JSON object submitted to the Theme_System, the validation function SHALL:
- Verify the presence of all 26 required CSS custom property variables
- Reject any theme containing `url()` in CSS values (XSS prevention)
- Validate WCAG AA contrast ratio (≥4.5:1) between text and background colors
- Reject themes loaded via HTTP (require HTTPS only)

**Validates: Requirements 4.1, 4.3, 4.4, 4.6, 4.8, 4.10**

---

### Property 2: Permission Enforcement Consistency

*For any* user action request and any resource, the Permission_System SHALL:
- Return the same permission decision for identical (user, resource, action) tuples within the cache TTL (60s)
- Deny access when SpiceDB is unavailable (fail-closed)
- Enforce tenant isolation such that users cannot access resources belonging to other tenants
- Propagate role changes to all cached decisions within 5 seconds

**Validates: Requirements 3.4, 3.5, 3.6, 3.7, 3.9, 8.5, 8.6, 11.4, 11.9**

---

### Property 3: Real-time Event Delivery

*For any* server-side event (mode.changed, settings.changed, theme.changed, voice.*), the Realtime_System SHALL:
- Deliver the event to all subscribed clients within 100ms
- Maintain heartbeat at 20-second intervals
- Reconnect with exponential backoff when connection drops
- Replay missed events upon client reconnection
- Authenticate all WebSocket connections via Bearer token

**Validates: Requirements 10.2, 10.4, 10.5, 10.6, 10.8, 10.10**

---

### Property 4: Settings Persistence Round-Trip

*For any* valid settings object, storing then retrieving the settings SHALL produce an equivalent object, where:
- Settings are persisted to PostgreSQL immediately upon modification
- API keys are stored in Vault (not PostgreSQL)
- Optimistic locking via version field prevents concurrent edit conflicts
- Settings changes trigger agent config reload

**Validates: Requirements 9.2, 9.3, 9.6, 9.11**

---

### Property 5: Mode State Consistency

*For any* mode transition request, the Mode_Manager SHALL:
- Verify user has permission for target mode via SpiceDB before transition
- Emit mode.changed WebSocket event after successful transition
- Log all mode transitions to audit trail
- Persist mode preference per user in PostgreSQL
- Restore last permitted mode when session starts

**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.8**

---

### Property 6: Tenant Data Isolation

*For any* database query and any tenant, the Multi_Tenancy system SHALL:
- Filter all results by tenant_id extracted from X-Tenant-Id header
- Prevent cross-tenant data access except for SYSADMIN role
- Log all cross-tenant access attempts to audit trail
- Cascade delete all tenant data when tenant is deleted
- Provision default roles and settings when tenant is created

**Validates: Requirements 11.1, 11.2, 11.3, 11.5, 11.6, 11.7, 11.8, 11.10**

---

### Property 7: Security Controls Enforcement

*For any* API request, the API_Security layer SHALL:
- Require Bearer token authentication (return 401 if missing/invalid)
- Enforce rate limiting (return 429 with Retry-After when exceeded)
- Validate all inputs against JSON Schema (return 400 for invalid)
- Reject SQL injection attempts (return 400)
- Sanitize and reject XSS payloads
- Set CSP headers on all responses
- Log all authentication failures to audit trail

**Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9**

---

### Property 8: Voice Provider Selection Consistency

*For any* voice provider selection (local, agentvoicebox, disabled), the System SHALL:
- Use Local_Voice for STT/TTS when provider is "local"
- Use AgentVoiceBox for full speech-on-speech when provider is "agentvoicebox"
- Hide all voice UI elements when provider is "disabled"
- Show provider-specific configuration fields dynamically
- Validate new configuration when provider changes
- Emit settings.changed event when voice provider changes

**Validates: Requirements 7.2, 7.3, 7.4, 7.5, 7.6, 7.10**

---

### Property 9: Component Render Performance

*For any* Lit Web Component in the UI_Layer, rendering SHALL:
- Complete within 16ms (60fps) for all component state changes
- Apply theme variable changes within 50ms
- Use CSS Custom Properties for all themeable values
- Maintain Shadow DOM encapsulation

**Validates: Requirements 1.2, 1.4, 1.7, 1.10**

---

### Property 10: API Response Time SLA

*For any* API request under normal load, the Backend SHALL:
- Respond within 50ms (p95)
- Complete permission checks within 10ms (p95)
- Use Pydantic schemas for all request/response validation

**Validates: Requirements 2.3, 2.10, 3.2**

---

## 14. Error Handling

### 14.1 Error Categories

| Category | HTTP Status | Handling |
|----------|-------------|----------|
| Authentication | 401 | Redirect to login, clear token |
| Authorization | 403 | Show permission denied toast |
| Validation | 400 | Show field-level errors |
| Rate Limit | 429 | Show retry countdown |
| Server Error | 500 | Show generic error, log details |
| Network | 0 | Show offline indicator, retry |

### 14.2 Error Response Schema

```python
class ErrorResponse(Schema):
    error: str           # Error code (e.g., "PERMISSION_DENIED")
    message: str         # Human-readable message
    details: dict = {}   # Additional context
    trace_id: str        # Request trace ID for debugging
```

### 14.3 Frontend Error Handling

```typescript
// Global error handler
window.addEventListener('unhandledrejection', (event) => {
  const error = event.reason;
  if (error instanceof ApiError) {
    switch (error.status) {
      case 401:
        authStore.logout();
        router.navigate('/login');
        break;
      case 403:
        toastStore.show({ type: 'error', message: 'Permission denied' });
        break;
      case 429:
        toastStore.show({ type: 'warning', message: `Rate limited. Retry in ${error.retryAfter}s` });
        break;
      default:
        toastStore.show({ type: 'error', message: error.message });
    }
  }
});
```

---

## 15. Testing Strategy

### 15.1 Dual Testing Approach

The Eye of God UIX uses both unit tests and property-based tests:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs using Hypothesis (Python) and fast-check (TypeScript)

### 15.2 Property-Based Testing Configuration

**Backend (Python):**
```python
# pytest.ini
[pytest]
addopts = --hypothesis-show-statistics
hypothesis_profile = ci

# conftest.py
from hypothesis import settings, Verbosity

settings.register_profile("ci", max_examples=100, verbosity=Verbosity.verbose)
settings.register_profile("dev", max_examples=10)
```

**Frontend (TypeScript):**
```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    include: ['**/*.property.test.ts'],
    testTimeout: 30000, // Property tests may take longer
  },
});
```

### 15.3 Test Organization

```
ui/
├── backend/
│   └── tests/
│       ├── unit/
│       │   ├── test_auth.py
│       │   ├── test_settings.py
│       │   └── test_themes.py
│       └── property/
│           ├── test_theme_validation.py      # Property 1
│           ├── test_permission_enforcement.py # Property 2
│           ├── test_tenant_isolation.py      # Property 6
│           └── test_security_controls.py     # Property 7
│
├── frontend/
│   └── src/
│       └── tests/
│           ├── unit/
│           │   ├── eog-button.test.ts
│           │   ├── eog-input.test.ts
│           │   └── auth-store.test.ts
│           └── property/
│               ├── theme-validation.property.test.ts  # Property 1
│               ├── event-delivery.property.test.ts    # Property 3
│               ├── voice-provider.property.test.ts    # Property 8
│               └── render-performance.property.test.ts # Property 9
```

### 15.4 Property Test Examples

**Property 1: Theme Validation (Python)**
```python
# Feature: eye-of-god-uix, Property 1: Theme Validation Completeness
# Validates: Requirements 4.1, 4.3, 4.4, 4.6, 4.8, 4.10

from hypothesis import given, strategies as st
from api.schemas.themes import Theme, validate_theme

@given(st.builds(Theme, variables=st.dictionaries(
    st.text(min_size=1, max_size=32),
    st.text(min_size=1, max_size=64)
)))
def test_theme_validation_rejects_incomplete_themes(theme):
    """For any theme missing required variables, validation SHALL fail."""
    required_vars = ['bg-void', 'text-main', ...]  # 26 required
    if not all(v in theme.variables for v in required_vars):
        result = validate_theme(theme)
        assert not result.valid
        assert 'Missing required variables' in result.errors
```

**Property 6: Tenant Isolation (Python)**
```python
# Feature: eye-of-god-uix, Property 6: Tenant Data Isolation
# Validates: Requirements 11.1, 11.2, 11.3, 11.5, 11.6, 11.7, 11.8, 11.10

from hypothesis import given, strategies as st

@given(
    tenant_a=st.uuids(),
    tenant_b=st.uuids(),
    resource_id=st.uuids()
)
def test_tenant_isolation_prevents_cross_tenant_access(tenant_a, tenant_b, resource_id):
    """For any two different tenants, user from tenant_a SHALL NOT access tenant_b resources."""
    if tenant_a != tenant_b:
        user = create_user(tenant_id=tenant_a)
        resource = create_resource(tenant_id=tenant_b, id=resource_id)
        
        with pytest.raises(PermissionDenied):
            access_resource(user, resource)
```

**Property 9: Component Render Performance (TypeScript)**
```typescript
// Feature: eye-of-god-uix, Property 9: Component Render Performance
// Validates: Requirements 1.2, 1.4, 1.7, 1.10

import { fc } from 'fast-check';
import { EogButton } from '../components/eog-button';

fc.assert(
  fc.property(
    fc.record({
      variant: fc.constantFrom('default', 'primary', 'danger'),
      disabled: fc.boolean(),
      loading: fc.boolean(),
    }),
    async (props) => {
      const el = document.createElement('eog-button') as EogButton;
      Object.assign(el, props);
      document.body.appendChild(el);
      
      const start = performance.now();
      await el.updateComplete;
      const duration = performance.now() - start;
      
      // Render must complete within 16ms (60fps)
      expect(duration).toBeLessThan(16);
      
      document.body.removeChild(el);
    }
  ),
  { numRuns: 100 }
);
```

---

**Document Status:** COMPLETE

**Implements Requirements:**
- REQ-1 through REQ-25 from requirements.md
- All SRS sections 1-13

**Correctness Properties:**
- 10 properties covering all testable acceptance criteria
- Property-based testing with Hypothesis (Python) and fast-check (TypeScript)
- Minimum 100 iterations per property test

# Eye of God UIX — Requirements Document

## Document Control

| Field | Value |
|-------|-------|
| **Document ID** | SA01-EOG-REQ-2025-12 |
| **Version** | 3.0 |
| **Date** | 2025-12-21 |
| **Status** | CANONICAL |
| **Classification** | ENTERPRISE |
| **Derived From** | SA01-EOG-SRS-2025-12 |

---

## 1. Introduction

This document defines the EARS-format requirements for the **Eye of God (EOG)** unified interface architecture. All requirements are derived from the Software Requirements Specification (SRS.md).

**Key Architecture Decisions:**
- **UI Layer**: Lit 3.x Web Components (MILLIONS of concurrent users)
- **API Layer**: Django Ninja (ALL projects - SomaAgent01, SomaBrain, etc.)
- **MVC Layer**: Django 5.x with PostgreSQL
- **Permissions**: SpiceDB (Google Zanzibar - 1M+ checks/second)
- **Theming**: AgentSkin (REQUIRED - 26+ CSS variables)
- **Voice**: Dual-mode (Local STT/TTS OR AgentVoiceBox for speech-on-speech)

---

## 2. Glossary

| Term | Definition |
|------|------------|
| **Agent_Mode** | Operational state: STD, TRN, ADM, DEV, RO, DGR |
| **AgentSkin** | Theme system using CSS Custom Properties (26+ variables) |
| **AgentVoiceBox** | External voice service with full speech-on-speech capability |
| **Django_Ninja** | Fast async API framework for Django with OpenAPI 3.1 |
| **Kokoro** | Local TTS engine (82M-200M ONNX models, CPU/GPU) |
| **Lit** | Google's Web Components library with reactive properties |
| **Local_Voice** | On-device STT (Whisper) + TTS (Kokoro), NO speech-on-speech |
| **SpiceDB** | Google Zanzibar-based permission system for scale |
| **Whisper** | Local STT engine (OpenAI Whisper, CPU/GPU detection) |

---

## 3. Requirements

### Requirement 1: UI Layer Architecture (Lit Web Components)

**User Story:** As a developer, I want a modular, reactive UI built with Lit Web Components supporting millions of concurrent users, so that I can create fast, encapsulated, and themeable interfaces at scale.

#### Acceptance Criteria

1. THE UI_Layer SHALL use Lit 3.x Web Components with Shadow DOM encapsulation
2. WHEN a component renders THEN the UI_Layer SHALL complete rendering within 16ms (60fps)
3. THE UI_Layer SHALL expose reactive properties via Lit's `@property` decorator
4. WHEN theme variables change THEN the UI_Layer SHALL update all components within 50ms
5. THE UI_Layer SHALL lazy-load non-critical components via dynamic imports
6. WHEN the application loads THEN the UI_Layer SHALL achieve First Contentful Paint < 1.5s
7. THE UI_Layer SHALL use CSS Custom Properties for all themeable values
8. WHEN offline THEN the UI_Layer SHALL serve cached assets via Service Worker
9. THE UI_Layer SHALL support 1,000,000+ concurrent WebSocket connections
10. THE UI_Layer SHALL render at 60fps during all user interactions

---

### Requirement 2: Django + Django Ninja Backend (ALL PROJECTS)

**User Story:** As a backend developer, I want a unified Django + Django Ninja architecture across all projects (SomaAgent01, SomaBrain, etc.), so that I can build scalable, maintainable APIs with consistent patterns.

#### Acceptance Criteria

1. THE Backend SHALL use Django 5.x with async ORM support for ALL projects
2. THE Backend SHALL expose all REST APIs via Django Ninja with OpenAPI 3.1 schema
3. WHEN an API request arrives THEN the Backend SHALL respond within 50ms (p95)
4. THE Backend SHALL use Django's migration system for all schema changes
5. WHEN database queries execute THEN the Backend SHALL use connection pooling (pgbouncer)
6. THE Backend SHALL implement CQRS pattern for read-heavy endpoints
7. WHEN WebSocket connections are needed THEN the Backend SHALL use Django Channels 4.x
8. THE Backend SHALL expose Django Admin for superuser operations only
9. THE Backend SHALL handle 100,000+ requests/second per node
10. THE Backend SHALL use Pydantic schemas for all request/response validation

---

### Requirement 3: Permission System (SpiceDB / Google Zanzibar)

**User Story:** As a security architect, I want a globally consistent, high-performance permission system supporting millions of checks per second, so that I can enforce access control at enterprise scale.

#### Acceptance Criteria

1. THE Permission_System SHALL deploy SpiceDB as the permission authority
2. WHEN a permission check executes THEN the Permission_System SHALL respond within 10ms (p95)
3. THE Permission_System SHALL support 1,000,000+ permission checks per second
4. WHEN SpiceDB is unavailable THEN the Permission_System SHALL deny all requests (fail-closed)
5. THE Permission_System SHALL cache permission decisions in Redis with TTL 60s
6. WHEN a role changes THEN the Permission_System SHALL propagate changes within 5 seconds
7. THE Permission_System SHALL support hierarchical role inheritance
8. THE Permission_System SHALL provide default roles: SysAdmin, Admin, Developer, Trainer, User, Viewer
9. WHEN a user requests an action THEN the Permission_System SHALL verify tenant isolation

---

### Requirement 4: AgentSkin Theme System (REQUIRED)

**User Story:** As a user, I want to customize the visual appearance using the AgentSkin theme system, so that I can personalize my workspace with validated, secure themes.

#### Acceptance Criteria

1. THE Theme_System SHALL use CSS Custom Properties for all themeable values (26 variables minimum)
2. WHEN theme is applied THEN the Theme_System SHALL inject variables within 50ms
3. THE Theme_System SHALL support theme JSON format with name, version, author, variables
4. WHEN theme file is dropped THEN the Theme_System SHALL validate against JSON Schema
5. THE Theme_System SHALL persist active theme to localStorage
6. WHEN theme contains `url()` in CSS values THEN the Theme_System SHALL reject (XSS prevention)
7. THE Theme_System SHALL provide default themes: Default Light, Midnight Dark, High Contrast
8. THE Theme_System SHALL support remote theme loading via HTTPS only
9. WHEN theme is previewed THEN the Theme_System SHALL show split-screen comparison
10. THE Theme_System SHALL validate WCAG AA contrast ratios (4.5:1 minimum)
11. THE Theme_System SHALL enforce rate limiting (10 uploads/hour/user)

---

### Requirement 5: Local Voice System (STT + TTS)

**User Story:** As a user, I want to use local voice capabilities (Whisper STT + Kokoro TTS) running on my device, so that I can have voice input/output without external dependencies.

#### Acceptance Criteria

1. THE Local_Voice SHALL provide STT via Whisper (CPU or GPU auto-detection)
2. THE Local_Voice SHALL provide TTS via Kokoro (CPU or GPU auto-detection)
3. THE Local_Voice SHALL NOT support real-time speech-on-speech (use AgentVoiceBox for that)
4. WHEN GPU is available THEN the Local_Voice SHALL use CUDA-optimized models
5. WHEN GPU is unavailable THEN the Local_Voice SHALL fallback to CPU models
6. THE Local_Voice SHALL support Whisper model sizes: tiny, base, small, medium, large
7. THE Local_Voice SHALL support Kokoro model sizes: 82M, 200M
8. WHEN voice is enabled THEN the Local_Voice SHALL preload models at startup
9. THE Local_Voice SHALL support 15+ languages via Kokoro TTS
10. THE Local_Voice SHALL detect hardware architecture at Docker build time

---

### Requirement 6: AgentVoiceBox Integration (Speech-on-Speech)

**User Story:** As a user, I want full real-time speech-on-speech capability via AgentVoiceBox, so that I can have natural voice conversations with the agent.

#### Acceptance Criteria

1. THE AgentVoiceBox SHALL provide full real-time speech-on-speech capability
2. THE AgentVoiceBox SHALL connect via WebSocket to /v1/realtime endpoint
3. THE AgentVoiceBox SHALL support OpenAI Realtime API protocol compatibility
4. THE AgentVoiceBox SHALL support bidirectional audio streaming
5. WHEN AgentVoiceBox is active THEN the System SHALL achieve latency < 150ms end-to-end
6. THE AgentVoiceBox SHALL support turn detection and interruption handling
7. THE AgentVoiceBox SHALL support dual VAD (WebRTC + Silero)
8. THE AgentVoiceBox SHALL support noise reduction and AGC
9. WHEN AgentVoiceBox is local THEN the System SHALL connect to localhost
10. WHEN AgentVoiceBox is remote THEN the System SHALL connect via configured URL
11. THE AgentVoiceBox SHALL support 1000+ concurrent voice sessions per server

---

### Requirement 7: Voice Provider Selection

**User Story:** As a user, I want to choose between Local Voice and AgentVoiceBox in Settings, so that I can select the voice capability that fits my needs.

#### Acceptance Criteria

1. THE Settings SHALL allow user to select voice provider: local, agentvoicebox, or disabled
2. WHEN provider is "local" THEN the System SHALL use Local_Voice for STT/TTS only
3. WHEN provider is "agentvoicebox" THEN the System SHALL use AgentVoiceBox for full speech-on-speech
4. WHEN provider is "disabled" THEN the System SHALL hide all voice UI elements
5. THE Settings SHALL show provider-specific configuration fields dynamically
6. WHEN provider changes THEN the System SHALL validate new configuration
7. THE Settings SHALL provide "Test Connection" button for AgentVoiceBox
8. WHEN test connection succeeds THEN the Settings SHALL show green checkmark
9. THE Settings SHALL include Voice/Speech section in Connectivity tab
10. WHEN voice provider changes THEN the System SHALL emit settings.changed event

---

### Requirement 8: Mode State Management

**User Story:** As a user, I want to switch between agent modes (STD, TRN, ADM, DEV, RO, DGR) based on my permissions, so that I can access appropriate features for my role.

#### Acceptance Criteria

1. THE Mode_Manager SHALL maintain current mode state per session
2. WHEN mode changes THEN the Mode_Manager SHALL emit `mode.changed` event via WebSocket
3. THE Mode_Manager SHALL persist mode preference per user in PostgreSQL
4. WHEN session starts THEN the Mode_Manager SHALL restore last mode if permitted
5. WHEN user requests mode change THEN the Mode_Manager SHALL verify permissions via SpiceDB
6. IF user lacks permission for target mode THEN the Mode_Manager SHALL reject with HTTP 403
7. WHEN transitioning to DEGRADED mode THEN the Mode_Manager SHALL NOT require user action
8. THE Mode_Manager SHALL log all mode transitions to audit trail
9. THE Mode_Manager SHALL support modes: STD, TRN, ADM, DEV, RO, DGR
10. WHEN mode is DEGRADED THEN the Mode_Manager SHALL disable non-essential features

---

### Requirement 9: Settings Management

**User Story:** As a user, I want to configure agent settings through a tabbed interface with proper validation and persistence, so that I can customize the agent behavior.

#### Acceptance Criteria

1. THE Settings_Manager SHALL organize settings into tabs: Agent, External, Connectivity, System
2. WHEN settings are modified THEN the Settings_Manager SHALL persist to PostgreSQL immediately
3. THE Settings_Manager SHALL validate all inputs against JSON Schema before saving
4. WHEN sensitive fields are displayed THEN the Settings_Manager SHALL mask values with asterisks
5. THE Settings_Manager SHALL support field types: text, password, select, toggle, slider, number, json, file
6. WHEN API keys are saved THEN the Settings_Manager SHALL store in Vault (not PostgreSQL)
7. THE Settings_Manager SHALL emit `settings.changed` event after successful save
8. WHEN settings change THEN the Settings_Manager SHALL trigger agent config reload
9. THE Settings_Manager SHALL include Voice/Speech section in Connectivity tab
10. WHEN voice provider changes THEN the Settings_Manager SHALL show provider-specific fields
11. THE Settings_Manager SHALL support optimistic locking via version field
12. WHEN concurrent edit detected THEN the Settings_Manager SHALL show conflict resolution UI

---

### Requirement 10: Real-Time Communication

**User Story:** As a user, I want real-time updates via WebSocket for mode changes, settings updates, and voice events, so that I can see changes immediately without refreshing.

#### Acceptance Criteria

1. THE Realtime_System SHALL use WebSocket for bidirectional communication
2. WHEN server event occurs THEN the Realtime_System SHALL deliver to client within 100ms
3. THE Realtime_System SHALL support SSE fallback when WebSocket unavailable
4. WHEN connection drops THEN the Realtime_System SHALL reconnect with exponential backoff
5. THE Realtime_System SHALL send heartbeat every 20 seconds
6. WHEN client reconnects THEN the Realtime_System SHALL replay missed events
7. THE Realtime_System SHALL support event types: mode.changed, settings.changed, theme.changed, voice.*
8. THE Realtime_System SHALL authenticate WebSocket connections via token
9. THE Realtime_System SHALL support 10,000 concurrent connections per node
10. WHEN WebSocket fails THEN the Realtime_System SHALL fallback to SSE automatically

---

### Requirement 11: Multi-Tenancy

**User Story:** As a platform operator, I want complete tenant isolation for data, settings, and permissions, so that I can serve multiple organizations securely.

#### Acceptance Criteria

1. THE Multi_Tenancy SHALL isolate all data by tenant_id
2. WHEN request arrives THEN the Multi_Tenancy SHALL extract tenant from X-Tenant-Id header
3. THE Multi_Tenancy SHALL enforce tenant isolation in all database queries
4. WHEN user accesses resource THEN the Multi_Tenancy SHALL verify tenant membership via SpiceDB
5. THE Multi_Tenancy SHALL support tenant-specific themes and settings
6. WHEN tenant is created THEN the Multi_Tenancy SHALL provision default roles and settings
7. THE Multi_Tenancy SHALL support tenant hierarchy (parent/child tenants)
8. WHEN tenant is deleted THEN the Multi_Tenancy SHALL cascade delete all tenant data
9. THE Multi_Tenancy SHALL support cross-tenant queries for SYSADMIN only
10. THE Multi_Tenancy SHALL log all cross-tenant access to audit trail

---

### Requirement 12: Security

**User Story:** As a security architect, I want comprehensive security controls including authentication, authorization, input validation, and audit logging, so that I can protect the system from attacks.

#### Acceptance Criteria

1. THE API_Security SHALL require Bearer token authentication for all endpoints
2. WHEN request lacks valid token THEN the API_Security SHALL return HTTP 401
3. THE API_Security SHALL enforce rate limiting (120 requests/minute default)
4. WHEN rate limit exceeded THEN the API_Security SHALL return HTTP 429 with Retry-After
5. THE API_Security SHALL validate all inputs against JSON Schema
6. WHEN SQL injection attempted THEN the API_Security SHALL reject with HTTP 400
7. THE API_Security SHALL set CSP headers: default-src 'self'; style-src 'self' 'unsafe-inline'
8. THE API_Security SHALL log all authentication failures to audit trail
9. WHEN XSS payload detected THEN the API_Security SHALL sanitize and reject
10. THE System SHALL store all secrets in Vault (not PostgreSQL)
11. THE API_Security SHALL enforce HTTPS for all external connections
12. THE API_Security SHALL support JWT token refresh without re-authentication

---

### Requirement 13: Observability

**User Story:** As an operations engineer, I want comprehensive metrics, tracing, and logging, so that I can monitor system health and troubleshoot issues.

#### Acceptance Criteria

1. THE Observability SHALL expose Prometheus metrics on /metrics endpoint
2. THE Observability SHALL track: request_count, request_duration, error_rate, active_connections
3. WHEN error occurs THEN the Observability SHALL increment error counter with labels
4. THE Observability SHALL support OpenTelemetry tracing with trace_id propagation
5. THE Observability SHALL log structured JSON to stdout
6. WHEN latency exceeds SLO THEN the Observability SHALL emit alert
7. THE Observability SHALL track theme_loads_total, permission_checks_total, mode_transitions_total
8. THE Observability SHALL provide Grafana dashboard templates
9. THE Observability SHALL track voice_sessions_total, voice_latency_seconds
10. THE Observability SHALL support distributed tracing across all services

---

### Requirement 14: Performance (MILLIONS OF USERS)

**User Story:** As a platform architect, I want the system to support millions of concurrent users with sub-second response times, so that I can serve enterprise-scale deployments.

#### Acceptance Criteria

1. THE System SHALL support 1,000,000+ concurrent WebSocket connections
2. THE System SHALL achieve First Contentful Paint < 1.5 seconds
3. THE System SHALL achieve Time to Interactive < 3 seconds
4. WHEN theme switches THEN the System SHALL complete transition < 300ms
5. THE API_Layer SHALL achieve response time < 50ms (p95)
6. THE Permission_System SHALL achieve check time < 10ms (p95)
7. THE System SHALL support 10,000 concurrent WebSocket connections per node
8. WHEN under load THEN the System SHALL maintain 99.9% availability
9. THE System SHALL achieve Lighthouse score > 90 for all categories
10. THE Django_Ninja_API SHALL handle 100,000+ requests/second per node
11. THE Lit_UI SHALL render 60fps during all interactions
12. THE System SHALL support horizontal scaling via Kubernetes

---

### Requirement 15: Accessibility

**User Story:** As a user with disabilities, I want the interface to be fully accessible via keyboard, screen readers, and high contrast modes, so that I can use the system effectively.

#### Acceptance Criteria

1. THE Accessibility SHALL comply with WCAG 2.1 AA standards
2. THE Accessibility SHALL support keyboard navigation for all interactive elements
3. WHEN focus changes THEN the Accessibility SHALL show visible focus indicator
4. THE Accessibility SHALL provide ARIA labels for all controls
5. THE Accessibility SHALL support screen readers (NVDA, VoiceOver, JAWS)
6. WHEN color is used for meaning THEN the Accessibility SHALL provide alternative indicator
7. THE Accessibility SHALL support reduced motion preference
8. THE Accessibility SHALL maintain contrast ratio >= 4.5:1 for all text
9. THE Accessibility SHALL provide skip navigation links
10. THE Accessibility SHALL support text scaling up to 200%

---

### Requirement 16: Cognitive Panel

**User Story:** As a trainer, I want to view and adjust cognitive parameters (neuromodulators, adaptation weights, learning rate), so that I can fine-tune agent behavior.

#### Acceptance Criteria

1. THE Cognitive_Panel SHALL display current neuromodulator levels (dopamine, serotonin, noradrenaline, acetylcholine)
2. WHEN user has TRN or ADM mode THEN the Cognitive_Panel SHALL allow editing neuromodulators
3. THE Cognitive_Panel SHALL display adaptation weights (alpha, beta, gamma, tau)
4. THE Cognitive_Panel SHALL display learning rate with slider control
5. WHEN cognitive parameters change THEN the Cognitive_Panel SHALL call SomaBrain API
6. THE Cognitive_Panel SHALL display cognitive load indicator
7. WHEN cognitive load > 0.8 THEN the Cognitive_Panel SHALL show sleep cycle recommendation
8. THE Cognitive_Panel SHALL provide "Trigger Sleep Cycle" button for TRN/ADM modes
9. THE Cognitive_Panel SHALL display real-time parameter updates via WebSocket
10. THE Cognitive_Panel SHALL validate parameter ranges before submission

---

### Requirement 17: Memory Browser

**User Story:** As a user, I want to browse, search, and manage agent memories, so that I can understand what the agent knows and curate its knowledge.

#### Acceptance Criteria

1. THE Memory_Browser SHALL display memories in paginated list view
2. THE Memory_Browser SHALL support semantic search via query input
3. WHEN memory is selected THEN the Memory_Browser SHALL show full payload details
4. THE Memory_Browser SHALL display memory metadata (timestamp, type, score)
5. WHEN user has ADM mode THEN the Memory_Browser SHALL allow memory deletion
6. WHEN user has ADM mode THEN the Memory_Browser SHALL allow memory export (JSON)
7. THE Memory_Browser SHALL support filtering by memory type (episodic, semantic)
8. THE Memory_Browser SHALL support filtering by date range
9. THE Memory_Browser SHALL display memory count and storage usage
10. THE Memory_Browser SHALL call SomaBrain /recall endpoint for search

---

### Requirement 18: Audit Log Viewer

**User Story:** As an administrator, I want to view audit logs of all system actions, so that I can track user activity and investigate incidents.

#### Acceptance Criteria

1. THE Audit_Viewer SHALL display audit logs in paginated table view
2. THE Audit_Viewer SHALL support filtering by user, action, resource, timestamp
3. THE Audit_Viewer SHALL display: timestamp, user, action, resource, result, details
4. WHEN audit entry is selected THEN the Audit_Viewer SHALL show full JSON payload
5. THE Audit_Viewer SHALL support export to CSV/JSON
6. THE Audit_Viewer SHALL require ADM or SYSADMIN mode
7. THE Audit_Viewer SHALL support real-time streaming of new entries
8. THE Audit_Viewer SHALL retain logs for configurable period (default 90 days)
9. THE Audit_Viewer SHALL support search across all fields
10. THE Audit_Viewer SHALL display log volume metrics

---

### Requirement 19: Tool Catalog

**User Story:** As a user, I want to browse available tools and their permissions, so that I can understand what capabilities the agent has.

#### Acceptance Criteria

1. THE Tool_Catalog SHALL display all available tools in card grid view
2. THE Tool_Catalog SHALL show tool name, description, category, required mode
3. WHEN tool is selected THEN the Tool_Catalog SHALL show full documentation
4. THE Tool_Catalog SHALL indicate which tools are available in current mode
5. THE Tool_Catalog SHALL support filtering by category
6. THE Tool_Catalog SHALL support search by name/description
7. WHEN user has DEV mode THEN the Tool_Catalog SHALL show tool configuration
8. THE Tool_Catalog SHALL display tool usage statistics
9. THE Tool_Catalog SHALL group tools by category: execution, memory, communication, browser
10. THE Tool_Catalog SHALL show tool dependencies and requirements

---

### Requirement 20: Desktop Application (Tauri)

**User Story:** As a user, I want a native desktop application with system tray integration, so that I can access the agent without a browser.

#### Acceptance Criteria

1. THE Desktop_App SHALL use Tauri 2.0 with shared Lit components
2. THE Desktop_App SHALL support Windows, macOS, and Linux
3. THE Desktop_App SHALL provide system tray icon with quick actions
4. THE Desktop_App SHALL support global hotkey for activation
5. THE Desktop_App SHALL support native notifications
6. THE Desktop_App SHALL support offline mode with cached data
7. THE Desktop_App SHALL auto-update via Tauri updater
8. THE Desktop_App SHALL support deep linking (soma://...)
9. THE Desktop_App SHALL share authentication with web version
10. THE Desktop_App SHALL support local voice (Whisper/Kokoro) natively

---

### Requirement 21: CLI Dashboard (Ratatui)

**User Story:** As a developer, I want a terminal-based dashboard for monitoring and quick interactions, so that I can work without leaving the terminal.

#### Acceptance Criteria

1. THE CLI_Dashboard SHALL use Rust + Ratatui for terminal UI
2. THE CLI_Dashboard SHALL display agent status, mode, and health
3. THE CLI_Dashboard SHALL support quick chat input
4. THE CLI_Dashboard SHALL display streaming responses
5. THE CLI_Dashboard SHALL support keyboard shortcuts for common actions
6. THE CLI_Dashboard SHALL display memory usage and cognitive load
7. THE CLI_Dashboard SHALL support mode switching via keyboard
8. THE CLI_Dashboard SHALL connect via same API as web/desktop
9. THE CLI_Dashboard SHALL support configuration via TOML file
10. THE CLI_Dashboard SHALL support piping input/output for scripting

---

### Requirement 22: Django Migration (SomaAgent01)

**User Story:** As a developer, I want SomaAgent01 to migrate from FastAPI to Django Ninja while maintaining backward compatibility, so that I can benefit from Django's ecosystem.

#### Acceptance Criteria

1. THE Migration SHALL run Django Ninja parallel to FastAPI during transition
2. THE Django_Ninja_API SHALL be available at /api/v2/*
3. THE FastAPI SHALL remain at /v1/* during 6-month transition period
4. THE Django_Ninja SHALL achieve feature parity with FastAPI
5. THE Migration SHALL use nginx for traffic routing between versions
6. WHEN feature parity achieved THEN the Migration SHALL begin traffic migration
7. THE Migration SHALL support rollback to FastAPI if issues detected
8. THE Migration SHALL maintain all existing integrations
9. THE Django_Ninja SHALL use same authentication tokens as FastAPI
10. THE Migration SHALL complete within 6-month overlap period

---

### Requirement 23: Django Migration (SomaBrain)

**User Story:** As a developer, I want SomaBrain to migrate from FastAPI to Django Ninja, so that I can have a unified backend stack across all projects.

#### Acceptance Criteria

1. THE SomaBrain SHALL migrate from FastAPI to Django Ninja
2. THE SomaBrain SHALL expose /api/v2/remember endpoint
3. THE SomaBrain SHALL expose /api/v2/recall endpoint
4. THE SomaBrain SHALL expose /api/v2/neuromodulators endpoint
5. THE SomaBrain SHALL expose /api/v2/sleep/* endpoints
6. THE SomaBrain SHALL expose /api/v2/context/* endpoints
7. THE SomaBrain gRPC service SHALL remain for high-performance memory operations
8. THE Migration SHALL maintain backward compatibility with existing clients
9. THE Django_Ninja SHALL use same Pydantic schemas as FastAPI
10. THE Migration SHALL follow same parallel deployment strategy as SomaAgent01

---

### Requirement 24: Infrastructure (Docker/Kubernetes)

**User Story:** As a DevOps engineer, I want containerized deployment with auto-scaling and zero-downtime updates, so that I can operate the system reliably at scale.

#### Acceptance Criteria

1. THE System SHALL detect CPU/GPU architecture at Docker build time
2. THE System SHALL build appropriate Docker images for detected architecture
3. THE System SHALL support horizontal scaling via Kubernetes
4. THE System SHALL support rolling deployments with zero downtime
5. THE System SHALL support health checks for all services
6. THE System SHALL support resource limits and requests
7. THE System SHALL use PostgreSQL 16.x as primary database
8. THE System SHALL use pgbouncer for connection pooling
9. THE System SHALL use Redis 7.x for caching and sessions
10. THE System SHALL use Kafka 3.x for event streaming

---

### Requirement 25: Feature Flags

**User Story:** As an administrator, I want to enable/disable features via feature flags, so that I can control feature rollout and manage system capabilities.

#### Acceptance Criteria

1. THE Feature_Flags SHALL support flags: sse_enabled, embeddings_ingest, semantic_recall, content_masking
2. THE Feature_Flags SHALL support flags: audio_support, browser_support, code_exec, vision_support
3. THE Feature_Flags SHALL support flags: mcp_client, mcp_server, learning_context, tool_sandboxing
4. THE Feature_Flags SHALL support flags: streaming_responses, delegation, voice_local, voice_agentvoicebox
5. THE Feature_Flags SHALL support feature profiles: minimal, standard, enhanced, max
6. WHEN profile is selected THEN the Feature_Flags SHALL apply all profile flags
7. THE Feature_Flags SHALL persist to PostgreSQL per tenant
8. WHEN flag changes THEN the Feature_Flags SHALL emit settings.changed event
9. THE Feature_Flags SHALL support override at user level
10. THE Feature_Flags SHALL be editable in System tab of Settings (ADM mode only)

---

## 4. Traceability Matrix

| Requirement | SRS Section | Priority | Status |
|-------------|-------------|----------|--------|
| REQ-1: UI Layer | 8.1 | P0 | DEFINED |
| REQ-2: Django Backend | 8.2, 11 | P0 | DEFINED |
| REQ-3: SpiceDB Permissions | 8.3 | P0 | DEFINED |
| REQ-4: AgentSkin Theme | 6, 8.4 | P0 | DEFINED |
| REQ-5: Local Voice | 7, 10.1 | P1 | DEFINED |
| REQ-6: AgentVoiceBox | 7, 10.2 | P1 | DEFINED |
| REQ-7: Voice Provider Selection | 10.3 | P1 | DEFINED |
| REQ-8: Mode State Management | 3, 8.7 | P0 | DEFINED |
| REQ-9: Settings Management | 5, 8.6 | P0 | DEFINED |
| REQ-10: Real-Time Communication | 8.8 | P0 | DEFINED |
| REQ-11: Multi-Tenancy | 9.3 | P0 | DEFINED |
| REQ-12: Security | 9.2 | P0 | DEFINED |
| REQ-13: Observability | 9.5 | P1 | DEFINED |
| REQ-14: Performance | 9.1 | P0 | DEFINED |
| REQ-15: Accessibility | 9.4 | P1 | DEFINED |
| REQ-16: Cognitive Panel | 5 | P1 | DEFINED |
| REQ-17: Memory Browser | 5 | P1 | DEFINED |
| REQ-18: Audit Log Viewer | 9.5 | P2 | DEFINED |
| REQ-19: Tool Catalog | 5 | P2 | DEFINED |
| REQ-20: Desktop (Tauri) | 1.2 | P2 | DEFINED |
| REQ-21: CLI (Ratatui) | 1.2 | P2 | DEFINED |
| REQ-22: Django Migration (SA01) | 11.2 | P0 | DEFINED |
| REQ-23: Django Migration (SomaBrain) | 11.3 | P1 | DEFINED |
| REQ-24: Infrastructure | 12 | P0 | DEFINED |
| REQ-25: Feature Flags | 5.3 | P1 | DEFINED |

---

## 5. Document Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | | | |
| Tech Lead | | | |
| Security Lead | | | |
| QA Lead | | | |

---

**Document Status:** COMPLETE - Ready for Review

**Next Steps:**
1. Review requirements with stakeholders
2. Complete design.md with detailed architecture
3. Create tasks.md with implementation plan
# Eye of God SAAS Admin — Software Requirements Specification

## Document Control

| Field | Value |
|-------|-------|
| **Document ID** | SA01-SAAS-SRS-2025-12 |
| **Version** | 1.0 |
| **Date** | 2025-12-22 |
| **Status** | DRAFT |
| **Classification** | CANONICAL |

---

## 1. Executive Summary

The Eye of God SAAS Admin UI provides enterprise-level administration for multi-tenant SomaAgent deployments. It enables SAAS operators to manage **Tenants**, enforce **Quotas**, configure **Subscriptions**, and delegate administration to tenant-level and agent-level users.

**Key Capabilities:**
- Tenant lifecycle management (create, suspend, delete)
- Subscription tiers with quota enforcement
- Hierarchical permission model (SAAS → Tenant → Agent)
- Agent deployment limits and resource allocation
- Billing integration and usage tracking

---

## 2. Permission Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SAAS PLATFORM LEVEL                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ SAAS Super Admin (God Mode)                                          │   │
│  │  • Create/Delete Tenants                                             │   │
│  │  • Set Subscription Tiers                                            │   │
│  │  • View All Usage/Billing                                            │   │
│  │  • Platform-wide Feature Flags                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TENANT LEVEL (e.g., SomaTechDev)                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Tenant SysAdmin                                                      │   │
│  │  • Manage Tenant Users                                               │   │
│  │  • Create/Configure Agents (within quota)                            │   │
│  │  • View Tenant Billing                                               │   │
│  │  • Tenant-wide Settings                                              │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ Tenant Admin                                                         │   │
│  │  • Manage Agent Admins                                               │   │
│  │  • Configure Agent Defaults                                          │   │
│  │  • View Audit Logs                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AGENT LEVEL (e.g., SomaAgent01)                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Agent Owner         • Full control of this specific agent           │   │
│  │ Agent Admin         • Manage agent settings, models, tools          │   │
│  │ Agent Developer     • DEV mode access, debugging                    │   │
│  │ Agent Trainer       • TRN mode, cognitive parameter tuning          │   │
│  │ Agent User          • Standard interaction (STD mode)               │   │
│  │ Agent Viewer        • Read-only access (RO mode)                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. SpiceDB Permission Schema Extension

```zed
// SAAS Platform Level
definition platform {}

definition saas_admin {
    relation platform: platform
    
    permission manage_tenants = platform
    permission view_billing = platform
    permission configure_platform = platform
}

// Tenant Level (extended)
definition tenant {
    relation sysadmin: user          // Tenant owner/super admin
    relation admin: user             // Tenant administrators
    relation developer: user         // Developers with DEV access
    relation trainer: user           // Trainers with TRN access
    relation member: user            // Regular users
    relation viewer: user            // Read-only users
    
    // Subscription limits
    relation subscription: subscription_tier
    
    // Computed permissions
    permission manage = sysadmin
    permission administrate = sysadmin + admin
    permission develop = sysadmin + admin + developer
    permission train = sysadmin + admin + trainer
    permission use = sysadmin + admin + developer + trainer + member
    permission view = sysadmin + admin + developer + trainer + member + viewer
    
    // Agent management
    permission create_agent = sysadmin + admin
    permission delete_agent = sysadmin
}

// Subscription Tier (NEW)
definition subscription_tier {
    relation owner: tenant
    
    // Limits stored as relation metadata
    // max_agents: int
    // max_users: int
    // max_tokens_per_month: int
    // max_storage_gb: int
}

// Agent Level (NEW)
definition agent {
    relation tenant: tenant
    relation owner: user              // Agent owner (full control)
    relation admin: user              // Agent admins
    relation developer: user          // Agent developers
    relation trainer: user            // Agent trainers
    relation user: user               // Agent users
    relation viewer: user             // Agent viewers
    
    // Mode permissions
    permission activate_adm = owner + admin
    permission activate_dev = owner + admin + developer
    permission activate_trn = owner + admin + trainer
    permission activate_std = owner + admin + developer + trainer + user
    permission activate_ro = owner + admin + developer + trainer + user + viewer
    
    // Agent configuration
    permission configure = owner + admin
    permission view_settings = owner + admin + developer + trainer
}
```

---

## 4. UI Views Specification

### 4.1 SAAS Super Admin Dashboard

**Route:** `/saas/dashboard`  
**Permission:** `saas_admin->manage_tenants`

**Features:**
- Platform overview (total tenants, users, agents)
- Revenue/billing summary
- System health metrics
- Feature flag management

---

### 4.2 Tenant Management

**Route:** `/saas/tenants`  
**Permission:** `saas_admin->manage_tenants`

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Tenant unique identifier |
| `name` | string | Organization name |
| `slug` | string | URL-safe identifier |
| `subscription_tier` | enum | free/starter/team/enterprise |
| `status` | enum | active/suspended/pending |
| `created_at` | datetime | Creation timestamp |
| `owner_email` | string | Primary contact |

**Actions:**
- Create Tenant (modal form)
- Edit Tenant Settings
- Suspend/Reactivate Tenant
- Delete Tenant (with confirmation)
- Impersonate Tenant (for support)

---

### 4.3 Subscription Tiers

**Route:** `/saas/subscriptions`  
**Permission:** `saas_admin->configure_platform`

| Tier | Max Agents | Max Users | Tokens/Month | Storage | Price |
|------|------------|-----------|--------------|---------|-------|
| **Free** | 1 | 3 | 100K | 1 GB | $0 |
| **Starter** | 3 | 10 | 1M | 10 GB | $49/mo |
| **Team** | 10 | 50 | 10M | 100 GB | $199/mo |
| **Enterprise** | Unlimited | Unlimited | Custom | Custom | Custom |

**Actions:**
- Edit tier limits
- Create custom tiers
- Assign tier to tenant

---

### 4.3.1 Subscription Tier Builder (Full-Screen Composer)

**Route:** `/saas/subscriptions/builder`  
**Permission:** `saas_admin->configure_platform`

#### Overview

A **full-screen, drag-and-drop tier composition system** that enables SAAS admins to create and configure subscription tiers by dragging features from a catalog and customizing limits. All modals are **full-screen experiences** (100% viewport) for maximum configuration space.

#### Wireframe - Tier Builder

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  ← Back to Tiers                          TIER BUILDER                    [Save Draft]  │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌────────────────────────────────────────────────────────────┐  ┌────────────────────┐ │
│  │                                                            │  │  FEATURE CATALOG   │ │
│  │   TIER INFO                                                │  │  ────────────────  │ │
│  │   ─────────────────────────────────────────                │  │                    │ │
│  │   Name: [Professional_____________]                         │  │  Search features...│ │
│  │   Slug: [professional] (auto)                              │  │                    │ │
│  │   Description: [For growing teams with advanced needs___]  │  │  CORE              │ │
│  │                                                            │  │  ┌──────────────┐  │ │
│  │   Price: [$__299__]  Billing: [Monthly ▼]                  │  │  │  ◉ VOICE     │  │ │
│  │   ☐ Custom pricing  ☐ Usage-based add-on                   │  │  │  TTS & STT   │  │ │
│  │                                                            │  │  └──────────────┘  │ │
│  │   ─────────────────────────────────────────                │  │  ┌──────────────┐  │ │
│  │   ASSIGNED FEATURES (drop here)                            │  │  │  ◉ MEMORY    │  │ │
│  │                                                            │  │  │  SomaBrain   │  │ │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │  │  └──────────────┘  │ │
│  │   │   VOICE     │  │   MEMORY    │  │    MCP      │       │  │  ┌──────────────┐  │ │
│  │   │  ●●●●●      │  │  ●●●●○      │  │  ●●●○○      │       │  │  │  ◉ MCP       │  │ │
│  │   │  1000 min   │  │  100K items │  │  5 servers  │       │  │  │  Connections │  │ │
│  │   │  [Configure]│  │  [Configure]│  │  [Configure]│       │  │  └──────────────┘  │ │
│  │   └─────────────┘  └─────────────┘  └─────────────┘       │  │                    │ │
│  │                                                            │  │  AI CAPABILITIES   │ │
│  │   ┌─────────────┐  ┌─────────────┐                        │  │  ┌──────────────┐  │ │
│  │   │   VISION    │  │   MODELS    │   [+ Drop more]         │  │  │  ◉ VISION    │  │ │
│  │   │  ●●●○○      │  │  ●●●●●      │                        │  │  │  Image AI    │  │ │
│  │   │  100 img/d  │  │  All models │                        │  │  └──────────────┘  │ │
│  │   │  [Configure]│  │  [Configure]│                        │  │  ┌──────────────┐  │ │
│  │   └─────────────┘  └─────────────┘                        │  │  │  ◉ MODELS    │  │ │
│  │                                                            │  │  │  LLM Access  │  │ │
│  │   ─────────────────────────────────────────                │  │  └──────────────┘  │ │
│  │   BASE LIMITS                                              │  │                    │ │
│  │   Agents: [__20__]  Users: [__100__]  Storage: [__500 GB]  │  │  AUTOMATION        │ │
│  │                                                            │  │  ┌──────────────┐  │ │
│  │                                                            │  │  │  ◉ BROWSER   │  │ │
│  │                                                            │  │  │  Automation  │  │ │
│  │                                                            │  │  └──────────────┘  │ │
│  │                                                            │  │  ┌──────────────┐  │ │
│  │                                                            │  │  │  ◉ CODE EXEC │  │ │
│  │                                                            │  │  │  Sandbox     │  │ │
│  │                                                            │  │  └──────────────┘  │ │
│  │                                                            │  │  ┌──────────────┐  │ │
│  │                                                            │  │  │  ◉ TOOLS     │  │ │
│  │                                                            │  │  │  Extensions  │  │ │
│  │                                                            │  │  └──────────────┘  │ │
│  │                                                            │  │                    │ │
│  └────────────────────────────────────────────────────────────┘  └────────────────────┘ │
│                                                                                          │
│                                             [Cancel]  [Preview Tier]  [Publish Tier]     │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Feature Settings Modal - Full-Screen (Example: VOICE)

When user clicks **[Configure]** on a feature card → **FULL SCREEN** modal opens:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  ← Back to Tier Builder              VOICE CONFIGURATION                  Professional  │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   ┌─────────────────────────────────────────┐   ┌─────────────────────────────────────┐ │
│   │  USAGE LIMITS                           │   │  LIVE PREVIEW                       │ │
│   │  ─────────────────────────────────      │   │  ─────────────────────────────────  │ │
│   │                                         │   │                                     │ │
│   │  Monthly Voice Minutes                  │   │   ┌───────────────────────────┐    │ │
│   │  ┌─────────────────────────────────┐   │   │   │  Voice Assistant Active   │    │ │
│   │  │  1000                           │   │   │   │  ─────────────────────    │    │ │
│   │  └─────────────────────────────────┘   │   │   │  "Hello, how can I help   │    │ │
│   │  ○ Unlimited  ● Limited  ○ Disabled     │   │   │   you today?"             │    │ │
│   │                                         │   │   │                           │    │ │
│   │  Concurrent Calls                       │   │   │   [Play Sample]           │    │ │
│   │  ┌─────────────────────────────────┐   │   │   │                           │    │ │
│   │  │  5                              │   │   │   └───────────────────────────┘    │ │
│   │  └─────────────────────────────────┘   │   │                                     │ │
│   │                                         │   │   Estimated Cost: ~$50/mo          │ │
│   │  Max Recording Length (minutes)         │   │   Based on avg usage               │ │
│   │  ┌─────────────────────────────────┐   │   │                                     │ │
│   │  │  30                             │   │   └─────────────────────────────────────┘ │
│   │  └─────────────────────────────────┘   │                                          │
│   │                                         │   ┌─────────────────────────────────────┐ │
│   └─────────────────────────────────────────┘   │  ENFORCEMENT POLICY                 │ │
│                                                  │  ─────────────────────────────────  │ │
│   ┌─────────────────────────────────────────┐   │                                     │ │
│   │  TTS PROVIDERS (Text-to-Speech)         │   │  Backend: AgentVoiceBox             │ │
│   │  ─────────────────────────────────      │   │  Metric: lago.voice_minutes         │ │
│   │                                         │   │  Policy: spicedb.voice_quota        │ │
│   │  ☑ Local TTS (Free, basic quality)      │   │                                     │ │
│   │  ☑ ElevenLabs (Premium voices)          │   │  [View Policy Definition]           │ │
│   │  ☑ OpenAI TTS (Natural voices)          │   │                                     │ │
│   │  ☐ Azure Cognitive (Enterprise)         │   │  When limit exceeded:               │ │
│   │  ☐ Google Cloud TTS (Wavenet)           │   │  ○ Block  ● Soft limit  ○ Alert     │ │
│   │                                         │   │                                     │ │
│   └─────────────────────────────────────────┘   └─────────────────────────────────────┘ │
│                                                                                          │
│   ┌─────────────────────────────────────────┐   ┌─────────────────────────────────────┐ │
│   │  STT PROVIDERS (Speech-to-Text)         │   │  VOICE CLONING                      │ │
│   │  ─────────────────────────────────      │   │  ─────────────────────────────────  │ │
│   │                                         │   │                                     │ │
│   │  ☑ OpenAI Whisper (Most accurate)       │   │  ● Disabled  ○ Enabled              │ │
│   │  ☑ Local Whisper (Offline capable)      │   │                                     │ │
│   │  ☐ Google Speech (Streaming)            │   │  Max Custom Voices: [___3___]       │ │
│   │  ☐ Azure Speech (Real-time)             │   │                                     │ │
│   │                                         │   │  Cloning Method:                    │ │
│   └─────────────────────────────────────────┘   │  [ElevenLabs Instant Clone ▼]       │ │
│                                                  │                                     │ │
│   ┌─────────────────────────────────────────┐   └─────────────────────────────────────┘ │
│   │  QUALITY SETTINGS                       │                                          │
│   │  ─────────────────────────────────      │                                          │ │
│   │                                         │                                          │ │
│   │  Output Quality:                        │                                          │ │
│   │  ○ Standard (fastest, 22kHz)            │                                          │ │
│   │  ● High (balanced, 44kHz)               │                                          │ │
│   │  ○ Ultra (slowest, 48kHz lossless)      │                                          │ │
│   │                                         │                                          │ │
│   └─────────────────────────────────────────┘                                          │
│                                                                                          │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                [Cancel]                    [Apply to Tier]               │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Feature Settings Modals (All Full-Screen)

| Feature | Modal Contents | Backend Integration |
|---------|----------------|---------------------|
| **VOICE** | Limits, TTS/STT Providers, Quality, Cloning | `AgentVoiceBox`, Lago `voice_minutes` |
| **MEMORY** | Entries limit, Retention, Embedding model, Capabilities | `SomaBrain`, PostgreSQL |
| **MCP** | Client/Server toggle, Max connections, Allowed servers list | MCP Registry, SpiceDB |
| **VISION** | Images/day, Providers (OpenAI, Anthropic, Google), Resolution | Lago `vision_requests` |
| **MODELS** | Model catalog with tier access toggle per model | `saas.models` table |
| **BROWSER** | Sessions, Timeout, Allowed domains, Sandbox level | Browser Automation Service |
| **CODE EXEC** | Languages, Memory limit, CPU time, Allowed packages | Code Sandbox Service |
| **TOOLS** | Tool catalog with enable/disable per tool | `saas.tools` table |
| **DELEGATION** | Max delegate agents, Inter-agent communication | Agent Orchestrator |

#### API Endpoints (Tier Builder)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v2/saas/tiers` | GET | List all subscription tiers |
| `/api/v2/saas/tiers` | POST | Create new tier |
| `/api/v2/saas/tiers/{id}` | GET | Get tier with all feature configs |
| `/api/v2/saas/tiers/{id}` | PUT | Update tier |
| `/api/v2/saas/tiers/{id}` | DELETE | Delete tier |
| `/api/v2/saas/tiers/{id}/features` | GET | Get features assigned to tier |
| `/api/v2/saas/tiers/{id}/features/{feature}` | PUT | Update feature config for tier |
| `/api/v2/saas/features/catalog` | GET | List all available features |
| `/api/v2/saas/features/{feature}/schema` | GET | Get schema for feature settings |
| `/api/v2/saas/features/{feature}/defaults` | GET | Get default settings |
| `/api/v2/saas/features/{feature}/providers` | GET | List available providers |

#### Database Schema (Tier Builder Extension)

```sql
-- Feature Catalog
CREATE TABLE saas_features (
    id VARCHAR(50) PRIMARY KEY,  -- 'voice', 'memory', 'mcp', etc.
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    icon VARCHAR(50),
    settings_schema JSONB,  -- JSON Schema for settings
    default_settings JSONB,
    is_active BOOLEAN DEFAULT TRUE
);

-- Tier-Feature Assignments
CREATE TABLE saas_tier_features (
    tier_id UUID REFERENCES subscription_tiers(id),
    feature_id VARCHAR(50) REFERENCES saas_features(id),
    is_enabled BOOLEAN DEFAULT TRUE,
    settings JSONB,  -- Override settings for this tier
    PRIMARY KEY (tier_id, feature_id)
);

-- Feature Providers
CREATE TABLE saas_feature_providers (
    id VARCHAR(50) PRIMARY KEY,
    feature_id VARCHAR(50) REFERENCES saas_features(id),
    name VARCHAR(100) NOT NULL,
    config_schema JSONB,
    is_active BOOLEAN DEFAULT TRUE
);
```

---

### 4.4 Tenant Users (within Tenant Admin)

**Route:** `/admin/users`  
**Permission:** `tenant->administrate`

**User Roles:**
- `sysadmin` - Tenant owner, full control
- `admin` - Administrative access
- `developer` - DEV mode access
- `trainer` - TRN mode access
- `member` - Standard access
- `viewer` - Read-only access

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | User identifier |
| `email` | string | Email address |
| `name` | string | Display name |
| `role` | enum | User role within tenant |
| `status` | enum | active/invited/suspended |
| `last_active` | datetime | Last activity |

---

### 4.5 Agent Management

**Route:** `/admin/agents`  
**Permission:** `tenant->create_agent`

**Agent Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Agent identifier |
| `name` | string | Agent name |
| `slug` | string | URL-safe identifier |
| `status` | enum | running/stopped/error |
| `owner_id` | UUID | Agent owner user |
| `chat_model` | string | Primary LLM model |
| `memory_enabled` | bool | SomaBrain integration |
| `voice_enabled` | bool | AgentVoiceBox integration |
| `created_at` | datetime | Creation timestamp |

**Actions:**
- Create Agent (within tenant quota)
- Configure Agent Settings
- Start/Stop Agent
- Delete Agent
- Transfer Ownership

**Quota Enforcement:**
```
if tenant.agent_count >= tenant.subscription.max_agents:
    raise QuotaExceededError("Agent limit reached for subscription tier")
```

---

### 4.6 Agent-Level User Management

**Route:** `/agent/{agent_id}/users`  
**Permission:** `agent->configure`

**Agent Roles:**
- `owner` - Full control (single user)
- `admin` - Agent configuration
- `developer` - DEV mode access
- `trainer` - TRN mode access
- `user` - Standard interaction
- `viewer` - Read-only

---

## 5. API Endpoints

### 5.1 SAAS Admin APIs

```
# Tenant Management
GET    /api/v2/saas/tenants                  # List tenants
POST   /api/v2/saas/tenants                  # Create tenant
GET    /api/v2/saas/tenants/{id}             # Get tenant
PUT    /api/v2/saas/tenants/{id}             # Update tenant
DELETE /api/v2/saas/tenants/{id}             # Delete tenant
POST   /api/v2/saas/tenants/{id}/suspend     # Suspend tenant
POST   /api/v2/saas/tenants/{id}/activate    # Activate tenant

# Subscription Management
GET    /api/v2/saas/subscriptions            # List tiers
POST   /api/v2/saas/subscriptions            # Create tier
PUT    /api/v2/saas/tenants/{id}/subscription # Assign tier

# Usage & Billing
GET    /api/v2/saas/usage                    # Platform usage
GET    /api/v2/saas/tenants/{id}/usage       # Tenant usage
GET    /api/v2/saas/billing                  # Billing summary
```

### 5.2 Tenant Admin APIs

```
# User Management
GET    /api/v2/admin/users                   # List tenant users
POST   /api/v2/admin/users                   # Invite user
PUT    /api/v2/admin/users/{id}              # Update user
DELETE /api/v2/admin/users/{id}              # Remove user
PUT    /api/v2/admin/users/{id}/role         # Change role

# Agent Management
GET    /api/v2/admin/agents                  # List agents
POST   /api/v2/admin/agents                  # Create agent
GET    /api/v2/admin/agents/{id}             # Get agent
PUT    /api/v2/admin/agents/{id}             # Update agent
DELETE /api/v2/admin/agents/{id}             # Delete agent
POST   /api/v2/admin/agents/{id}/start       # Start agent
POST   /api/v2/admin/agents/{id}/stop        # Stop agent
```

### 5.3 Agent Admin APIs

```
# Agent Users
GET    /api/v2/agents/{id}/users             # List agent users
POST   /api/v2/agents/{id}/users             # Add user to agent
PUT    /api/v2/agents/{id}/users/{uid}/role  # Change agent role
DELETE /api/v2/agents/{id}/users/{uid}       # Remove from agent
```

---

## 6. UI Components Required

| Component | Path | Description |
|-----------|------|-------------|
| `eog-tenant-list` | `/saas/tenants` | Tenant grid with filters |
| `eog-tenant-form` | Modal | Create/edit tenant form |
| `eog-subscription-manager` | `/saas/subscriptions` | Tier configuration |
| `eog-quota-display` | Sidebar | Quota usage indicators |
| `eog-user-table` | `/admin/users` | User management table |
| `eog-role-selector` | Form | Role dropdown with descriptions |
| `eog-agent-grid` | `/admin/agents` | Agent cards with status |
| `eog-agent-form` | Modal | Create/configure agent |
| `eog-usage-chart` | Dashboard | Usage over time charts |

---

## 7. Database Schema

```sql
-- Subscription Tiers  
CREATE TABLE subscription_tiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(64) NOT NULL,
    slug VARCHAR(64) UNIQUE NOT NULL,
    max_agents INT NOT NULL DEFAULT 1,
    max_users INT NOT NULL DEFAULT 3,
    max_tokens_per_month BIGINT NOT NULL DEFAULT 100000,
    max_storage_bytes BIGINT NOT NULL DEFAULT 1073741824,
    price_cents INT NOT NULL DEFAULT 0,
    billing_interval VARCHAR(16) DEFAULT 'monthly',
    is_custom BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tenants
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(64) UNIQUE NOT NULL,
    subscription_tier_id UUID REFERENCES subscription_tiers(id),
    status VARCHAR(32) DEFAULT 'pending',
    owner_user_id UUID REFERENCES users(id),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    suspended_at TIMESTAMPTZ
);

-- Tenant Users (junction)
CREATE TABLE tenant_users (
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(32) NOT NULL,
    invited_at TIMESTAMPTZ DEFAULT NOW(),
    accepted_at TIMESTAMPTZ,
    PRIMARY KEY (tenant_id, user_id)
);

-- Agents
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(64) NOT NULL,
    status VARCHAR(32) DEFAULT 'stopped',
    owner_user_id UUID REFERENCES users(id),
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, slug)
);

-- Agent Users (junction)
CREATE TABLE agent_users (
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(32) NOT NULL,
    PRIMARY KEY (agent_id, user_id)
);

-- Usage Tracking
CREATE TABLE usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    agent_id UUID REFERENCES agents(id),
    user_id UUID REFERENCES users(id),
    metric_type VARCHAR(64) NOT NULL,
    value BIGINT NOT NULL,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 8. Implementation Priority

| Phase | Feature | Priority |
|-------|---------|----------|
| 1 | Tenant CRUD | HIGH |
| 1 | Subscription Tiers | HIGH |
| 1 | Tenant User Management | HIGH |
| 2 | Agent Quota Enforcement | HIGH |
| 2 | Agent CRUD | HIGH |
| 2 | Agent User Management | MEDIUM |
| 3 | Usage Tracking | MEDIUM |
| 3 | Billing Integration | MEDIUM |
| 4 | Platform Analytics | LOW |
| 4 | Custom Tier Builder | LOW |

---

## 9. Complete CRUD UI Screens

### 9.1 Models Catalog (CRUD)

**Route:** `/platform/models`  
**Permission:** `platform->configure_platform`

#### Wireframe - Models List

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │ Model Catalog                               [+ Add Model]     │
│            │─────────────────────────────────────────────────────────────────│
│            │ 🔍 Search...     [Provider ▼] [Type ▼] [Status ▼]              │
│            │                                                                 │
│            │ CHAT MODELS                                                     │
│            │ ┌───────────────────────────────────────────────────────────┐ │
│            │ │ Model          Provider  Context  Vision  Status  Actions │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │ gpt-4o         OpenAI    128K     ✓       🟢      [···]  │ │
│            │ │ gpt-4o-mini    OpenAI    128K     ✓       🟢      [···]  │ │
│            │ │ claude-3-opus  Anthropic 200K     ✓       🟢      [···]  │ │
│            │ │ claude-3-sonn  Anthropic 200K     ✓       🟢      [···]  │ │
│            │ │ gemini-pro     Google    2M       ✓       🟢      [···]  │ │
│            │ └───────────────────────────────────────────────────────────┘ │
│            │                                                                 │
│            │ EMBEDDING MODELS                                                │
│            │ ┌───────────────────────────────────────────────────────────┐ │
│            │ │ Model              Provider  Dims   Status  Actions       │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │ text-embed-3-sm    OpenAI    1536   🟢      [···]         │ │
│            │ │ text-embed-3-lg    OpenAI    3072   🟢      [···]         │ │
│            │ └───────────────────────────────────────────────────────────┘ │
└────────────┴─────────────────────────────────────────────────────────────────┘
```

#### Model CRUD Operations

| Operation | Button | Modal Fields | API |
|-----------|--------|--------------|-----|
| **Create** | `+ Add Model` | Provider, Model ID, Type, Context Length, Has Vision, Rate Limits | `POST /api/v2/saas/models` |
| **Read** | Row click | Full model details panel | `GET /api/v2/saas/models/{id}` |
| **Update** | `[···] → Edit` | All editable fields | `PUT /api/v2/saas/models/{id}` |
| **Delete** | `[···] → Delete` | Confirmation modal | `DELETE /api/v2/saas/models/{id}` |
| **Toggle** | `[···] → Enable/Disable` | None | `PATCH /api/v2/saas/models/{id}/status` |

#### Add Model Modal

```
┌─────────────────────────────────────────────────────────┐
│  Add Model to Catalog                                ✕  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Provider *                                             │
│  ┌─────────────────────────────────────────────────┐   │
│  │ OpenAI                                      ▼   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Model ID *                                             │
│  ┌─────────────────────────────────────────────────┐   │
│  │ gpt-4o-2024-11-20                               │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Display Name *                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ GPT-4o (Nov 2024)                               │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Type *                                                 │
│  ○ Chat Model  ○ Embedding Model  ○ Utility Model      │
│                                                         │
│  Context Window *          Max Output Tokens            │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │ 128000           │      │ 16384            │        │
│  └──────────────────┘      └──────────────────┘        │
│                                                         │
│  Capabilities                                           │
│  ☑ Vision (Image Input)                                │
│  ☑ Function Calling                                    │
│  ☐ JSON Mode                                           │
│                                                         │
│  Rate Limits                                            │
│  RPM (Requests/Min) *      TPM (Tokens/Min)            │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │ 500              │      │ 30000            │        │
│  └──────────────────┘      └──────────────────┘        │
│                                                         │
│  Tier Availability                                      │
│  ☑ Enterprise  ☑ Team  ☐ Starter  ☐ Free              │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  [Cancel]                              [Add Model]      │
└─────────────────────────────────────────────────────────┘
```

---

### 9.2 Roles & Permissions Catalog (CRUD)

**Route:** `/platform/roles`  
**Permission:** `platform->configure_platform`

#### Wireframe - Roles List

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │ Roles & Permissions                        [+ Create Role]    │
│            │─────────────────────────────────────────────────────────────────│
│            │ [Platform Roles] [Tenant Roles] [Agent Roles]                  │
│            │                                                                 │
│            │ PLATFORM ROLES (SAAS Admin only)                               │
│            │ ┌───────────────────────────────────────────────────────────┐ │
│            │ │ Role               Users   Permissions        Actions     │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │ 👑 saas_superadmin 2       ALL (45)            [View]     │ │
│            │ │ 🛡️ saas_support    5       12 permissions      [Edit]     │ │
│            │ │ 📊 saas_billing    3       8 permissions       [Edit]     │ │
│            │ └───────────────────────────────────────────────────────────┘ │
│            │                                                                 │
│            │ TENANT ROLES (Template for all tenants)                        │
│            │ ┌───────────────────────────────────────────────────────────┐ │
│            │ │ Role          Modes    Permissions          Actions       │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │ 👑 sysadmin   ALL      Full tenant control   [🔒 System] │ │
│            │ │ 🛡️ admin      ADM,STD  User/agent mgmt       [Edit]      │ │
│            │ │ 👨‍💻 developer  DEV,STD  Dev tools, debug      [Edit]      │ │
│            │ │ 🎓 trainer    TRN,STD  Cognitive params      [Edit]      │ │
│            │ │ 👤 member     STD      Chat, memory, tools   [Edit]      │ │
│            │ │ 👁️ viewer     RO       Read-only access      [Edit]      │ │
│            │ └───────────────────────────────────────────────────────────┘ │
└────────────┴─────────────────────────────────────────────────────────────────┘
```

#### Role Edit Modal - Permission Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Edit Role: Developer                                                    ✕  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Role Name *              Role Code (read-only)                             │
│  ┌──────────────────┐     ┌──────────────────┐                             │
│  │ Developer        │     │ developer   [🔒] │                             │
│  └──────────────────┘     └──────────────────┘                             │
│                                                                             │
│  Agent Modes Allowed                                                        │
│  ☑ STD (Standard)  ☑ DEV (Developer)  ☐ TRN  ☐ ADM  ☐ RO                  │
│                                                                             │
│  PERMISSION MATRIX                                            [Select All] │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ CHAT & MEMORY                                                       │   │
│  │ ────────────────────────────────────────────────────────────────── │   │
│  │ ☑ chat:send              Send chat messages                        │   │
│  │ ☑ chat:view_history      View conversation history                 │   │
│  │ ☑ memory:read            Read from SomaBrain                       │   │
│  │ ☑ memory:write           Write to SomaBrain                        │   │
│  │ ☐ memory:delete          Delete memories                           │   │
│  │ ☐ memory:export          Export memory data                        │   │
│  │                                                                     │   │
│  │ TOOLS                                                               │   │
│  │ ────────────────────────────────────────────────────────────────── │   │
│  │ ☑ tools:execute          Execute approved tools                    │   │
│  │ ☑ tools:code_exec        Execute code snippets                     │   │
│  │ ☑ tools:browser          Use browser agent                         │   │
│  │ ☑ tools:debug            Access debug tools                        │   │
│  │ ☐ tools:configure        Configure tool settings                   │   │
│  │                                                                     │   │
│  │ SETTINGS                                                            │   │
│  │ ────────────────────────────────────────────────────────────────── │   │
│  │ ☑ settings:view          View settings (read-only)                 │   │
│  │ ☐ settings:edit          Edit settings                             │   │
│  │ ☐ settings:api_keys      Manage API keys                           │   │
│  │                                                                     │   │
│  │ ADMIN (disabled for non-admin roles)                               │   │
│  │ ────────────────────────────────────────────────────────────────── │   │
│  │ ☐ admin:users            Manage tenant users        [🔒 ADM only] │   │
│  │ ☐ admin:agents           Manage agents              [🔒 ADM only] │   │
│  │ ☐ admin:billing          View/manage billing        [🔒 ADM only] │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  [Cancel]                                              [Save Changes]       │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Complete Permission List

| Category | Permission | Description | Default Roles |
|----------|------------|-------------|---------------|
| **Chat** | `chat:send` | Send messages | ALL except RO |
| | `chat:view_history` | View history | ALL |
| | `chat:export` | Export conversations | admin+ |
| **Memory** | `memory:read` | Read SomaBrain | ALL |
| | `memory:write` | Write to memory | ALL except RO |
| | `memory:delete` | Delete memories | sysadmin, admin |
| | `memory:export` | Export memory | sysadmin |
| **Tools** | `tools:execute` | Run tools | ALL except RO |
| | `tools:code_exec` | Execute code | member+ |
| | `tools:browser` | Browser agent | member+ |
| | `tools:debug` | Debug mode | developer+ |
| | `tools:configure` | Configure tools | admin+ |
| **Voice** | `voice:input` | Voice input | ALL except RO |
| | `voice:output` | Voice output | ALL |
| | `voice:configure` | Voice settings | admin+ |
| **Settings** | `settings:view` | View settings | ALL |
| | `settings:edit` | Edit settings | admin+ |
| | `settings:api_keys` | Manage API keys | sysadmin |
| | `settings:models` | Configure models | admin+ |
| **Admin** | `admin:users` | User management | admin+ |
| | `admin:agents` | Agent management | admin+ |
| | `admin:billing` | Billing access | sysadmin |
| | `admin:audit` | View audit log | admin+ |
| **Cognitive** | `cognitive:view` | View params | trainer+ |
| | `cognitive:edit` | Edit params | trainer, sysadmin |
| | `cognitive:reset` | Reset adaptation | sysadmin |

---

### 9.3 Feature Flags Management (CRUD)

**Route:** `/platform/flags`  
**Permission:** `platform->configure_platform`

#### Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │ Feature Flags                              [+ Create Flag]    │
│            │─────────────────────────────────────────────────────────────────│
│            │ [Global] [Per-Tier] [Per-Tenant]                               │
│            │                                                                 │
│            │ GLOBAL FEATURE FLAGS                                           │
│            │ ┌───────────────────────────────────────────────────────────┐ │
│            │ │ Flag                    Description          Status       │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │ sse_enabled             SSE streaming         🟢 ON [···] │ │
│            │ │ embeddings_ingest       Embedding pipeline    🟢 ON [···] │ │
│            │ │ semantic_recall         SomaBrain recall      🟢 ON [···] │ │
│            │ │ audio_support           Voice subsystem       🟡 OFF[···] │ │
│            │ │ browser_support         Browser agent         🟢 ON [···] │ │
│            │ │ code_exec               Code execution        🟢 ON [···] │ │
│            │ │ vision_support          Image analysis        🟢 ON [···] │ │
│            │ │ mcp_client              MCP connections       🟢 ON [···] │ │
│            │ │ mcp_server              MCP server mode       🟡 OFF[···] │ │
│            │ │ voice_local             Local Whisper/Kokoro  🟢 ON [···] │ │
│            │ │ voice_agentvoicebox     AgentVoiceBox         🟡 OFF[···] │ │
│            │ │ delegation              Agent delegation      🟢 ON [···] │ │
│            │ └───────────────────────────────────────────────────────────┘ │
│            │                                                                 │
│            │ PER-TIER OVERRIDES                                             │
│            │ ┌───────────────────────────────────────────────────────────┐ │
│            │ │ Tier        Overrides                     Actions         │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │ Free        audio_support=OFF, browser=OFF [Configure]    │ │
│            │ │ Starter     mcp_server=OFF                 [Configure]    │ │
│            │ │ Team        (inherits global)              [Configure]    │ │
│            │ │ Enterprise  (all enabled)                  [Configure]    │ │
│            │ └───────────────────────────────────────────────────────────┘ │
└────────────┴─────────────────────────────────────────────────────────────────┘
```

---

### 9.4 API Keys Management (CRUD)

**Route:** `/platform/api-keys`  
**Permission:** `platform->configure_platform`

#### Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │ Platform API Keys                          [+ Add Key]        │
│            │─────────────────────────────────────────────────────────────────│
│            │ ⚠️ These are platform-wide API keys. Tenant keys are separate.│
│            │                                                                 │
│            │ LLM PROVIDERS                                                   │
│            │ ┌───────────────────────────────────────────────────────────┐ │
│            │ │ Provider       Key                      Status   Actions  │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │ 🟢 OpenAI      sk-proj-****...8x9K      Valid    [···]    │ │
│            │ │ 🟢 Anthropic   sk-ant-****...JKL2       Valid    [···]    │ │
│            │ │ 🟢 Google      AIzaSy****...mnop        Valid    [···]    │ │
│            │ │ 🟡 Groq        gsk_****...qrst          Exp.5d   [···]    │ │
│            │ │ ⚪ Mistral     (not configured)         —        [Add]    │ │
│            │ └───────────────────────────────────────────────────────────┘ │
│            │                                                                 │
│            │ SERVICES                                                        │
│            │ ┌───────────────────────────────────────────────────────────┐ │
│            │ │ Service        Key                      Status   Actions  │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │ 🟢 Serper      ****...xyz               Valid    [···]    │ │
│            │ │ 🟢 Lago        lago_****...abc          Valid    [···]    │ │
│            │ │ ⚪ Stripe      (not configured)         —        [Add]    │ │
│            │ └───────────────────────────────────────────────────────────┘ │
│            │                                                                 │
└────────────┴─────────────────────────────────────────────────────────────────┘
```

---

## 10. Shared Component Catalog

### 10.1 Reusable Components (AgentSkin Pattern)

All components follow the `saas-*` naming convention and are built with Lit 3.x.

| Component | Path | Usage | Props |
|-----------|------|-------|-------|
| `saas-data-table` | `components/data-table.ts` | All list views | `columns`, `data`, `sortable`, `filterable` |
| `saas-modal` | `components/modal.ts` | All CRUD modals | `title`, `open`, `size` |
| `saas-form-field` | `components/form-field.ts` | All form inputs | `label`, `type`, `required`, `error` |
| `saas-select` | `components/select.ts` | All dropdowns | `options`, `value`, `searchable` |
| `saas-toggle` | `components/toggle.ts` | Feature flags, settings | `checked`, `disabled`, `label` |
| `saas-stat-card` | `components/stat-card.ts` | Dashboard metrics | `title`, `value`, `trend`, `icon` |
| `saas-quota-bar` | `components/quota-bar.ts` | Usage indicators | `used`, `max`, `label` |
| `saas-status-badge` | `components/status-badge.ts` | Status indicators | `status`, `size` |
| `saas-action-menu` | `components/action-menu.ts` | Row actions | `items` |
| `saas-confirm-dialog` | `components/confirm-dialog.ts` | Dangerous actions | `title`, `message`, `confirmText` |
| `saas-toast` | `components/toast.ts` | Notifications | `message`, `type`, `duration` |
| `saas-sidebar` | `components/sidebar.ts` | Navigation | `items`, `activeRoute` |
| `saas-header` | `components/header.ts` | Top bar | `user`, `tenant` |

### 10.2 Voice Settings Component (Shared)

**Component:** `saas-voice-settings`  
**Used by:** Agent Settings, Tenant Settings, Platform Settings

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Voice & Speech Settings                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Voice Provider *                                                           │
│  ○ Local Voice (Whisper + Kokoro)                                          │
│    On-device processing, full privacy, ~300ms latency                       │
│                                                                             │
│  ○ AgentVoiceBox (External Service)                                        │
│    Cloud processing, lower latency (~150ms), requires network               │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  [IF Local Selected]                                                        │
│                                                                             │
│  STT Engine               STT Model Size                                    │
│  ┌──────────────────┐     ┌──────────────────┐                             │
│  │ Whisper      ▼   │     │ base         ▼   │                             │
│  └──────────────────┘     └──────────────────┘                             │
│  Models: tiny (39M), base (74M), small (244M), medium (769M), large (1.5G) │
│                                                                             │
│  TTS Engine               TTS Voice                                         │
│  ┌──────────────────┐     ┌──────────────────┐                             │
│  │ Kokoro       ▼   │     │ am_onyx      ▼   │                             │
│  └──────────────────┘     └──────────────────┘                             │
│                                                                             │
│  TTS Speed                                                                  │
│  Slow ─────────●───────── Fast                                             │
│       0.5x     1.0x       2.0x                                              │
│                                                                             │
│  VAD Threshold (Voice Activity Detection)                                   │
│  Less Sensitive ──────●────── More Sensitive                                │
│                  0.5                                                        │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  [IF AgentVoiceBox Selected]                                                │
│                                                                             │
│  AgentVoiceBox Server URL *                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ https://voice.mycompany.com                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  API Token *                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ••••••••••••••••••••••••                                [Show] [Test]│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  Audio Devices                                                              │
│                                                                             │
│  Input Device (Microphone)                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Built-in Microphone (Default)                                   ▼   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Output Device (Speaker)                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Built-in Speakers (Default)                                     ▼   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  [Test Microphone]  [Test Speaker]                                          │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  [Reset to Defaults]                                   [Save Settings]      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 10.3 Catalog Manager Abstraction (Universal Dual-Panel Pattern)

A **universal reusable component** for all complex admin catalog management. This abstraction enables drag-and-drop composition with full-screen configuration modals.

#### Pattern Overview

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                         CATALOG MANAGER (Base Component)                              │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│   LEFT PANEL (Source)                           RIGHT PANEL (Target/Config)           │
│   ┌───────────────────────────┐                ┌────────────────────────────────┐    │
│   │  AVAILABLE ITEMS          │                │  ASSIGNED / CONFIGURED          │    │
│   │  ─────────────────────    │                │  ─────────────────────────      │    │
│   │                           │                │                                 │    │
│   │  [Search...]              │   DRAG →→→    │  [Drop zone / Configuration]    │    │
│   │                           │                │                                 │    │
│   │  ┌─────────────────────┐  │                │                                 │    │
│   │  │  Draggable Card 1   │──┼────────────→   │                                 │    │
│   │  └─────────────────────┘  │                │                                 │    │
│   │  ┌─────────────────────┐  │                │  Click item → Opens Full-Screen │    │
│   │  │  Draggable Card 2   │  │                │  Configuration Modal            │    │
│   │  └─────────────────────┘  │                │                                 │    │
│   │  ┌─────────────────────┐  │                │                                 │    │
│   │  │  Draggable Card 3   │  │                │                                 │    │
│   │  └─────────────────────┘  │                │                                 │    │
│   │                           │                │                                 │    │
│   │  Categories/Filters       │                │                                 │    │
│   │  ─────────────────────    │                │                                 │    │
│   │  ○ All  ● Core  ○ AI      │                └────────────────────────────────┘    │
│   │                           │                                                       │
│   └───────────────────────────┘                                                       │
│                                                                                       │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

#### Component Architecture

| Component | Type | Description |
|-----------|------|-------------|
| `<catalog-manager>` | Full-screen page | Master orchestrator |
| `<catalog-panel>` | Sidebar panel | Left: Searchable, filterable, draggable items |
| `<catalog-item>` | Draggable card | Draggable feature/item card |
| `<target-panel>` | Drop zone | Right: Drop target + assigned items |
| `<assigned-item>` | Clickable card | Opens full-screen modal on click |
| `<fullscreen-config-modal>` | Full-screen modal | 100% viewport configuration |

#### Use Cases (Same Abstraction, Different Data)

| Use Case | Left Panel (Catalog) | Right Panel (Target) | Full-Screen Modal |
|----------|---------------------|---------------------|-------------------|
| **Tier Builder** | Features (Voice, Memory, MCP...) | Tier composition canvas | Feature settings |
| **Agent Config** | Tools, Models, Features | Agent capabilities | Tool/Model settings |
| **Role Editor** | Permissions catalog | Role permission set | Permission rules |
| **MCP Manager** | Available MCP servers | Connected servers | Server config |
| **Model Catalog** | All LLM models | Enabled for tenant | Model settings & limits |
| **Tool Registry** | All available tools | Active tools | Tool configuration |
| **Webhook Manager** | Event types | Active webhooks | Webhook config |
| **Theme Builder** | UI components | Theme preview | Component styling |

#### Component Usage Examples

**Tier Builder:**
```html
<catalog-manager
  catalog-source="/api/v2/saas/features/catalog"
  target-source="/api/v2/saas/tiers/{tierId}/features"
  modal-component="feature-settings-modal"
  mode="compose"
></catalog-manager>
```

**Agent Tool Configuration:**
```html
<catalog-manager
  catalog-source="/api/v2/tools/registry"
  target-source="/api/v2/agents/{agentId}/tools"
  modal-component="tool-settings-modal"
  mode="assign"
></catalog-manager>
```

**Role Permission Editor:**
```html
<catalog-manager
  catalog-source="/api/v2/permissions/catalog"
  target-source="/api/v2/roles/{roleId}/permissions"
  modal-component="permission-rules-modal"
  mode="assign"
></catalog-manager>
```

#### Props

| Prop | Type | Description |
|------|------|-------------|
| `catalog-source` | string | API endpoint for catalog items |
| `target-source` | string | API endpoint for assigned items |
| `modal-component` | string | Custom element name for config modal |
| `mode` | 'compose' \| 'assign' | Composition vs assignment mode |
| `searchable` | boolean | Enable search in catalog |
| `filterable` | boolean | Enable category filters |
| `max-items` | number | Maximum assignable items |

---

## 11. Element-Level Permissions

### 11.1 UI Element Visibility by Role

| Element | saas_admin | sysadmin | admin | developer | trainer | member | viewer |
|---------|------------|----------|-------|-----------|---------|--------|--------|
| **Sidebar - Platform** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Sidebar - Admin** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Sidebar - Billing** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Dashboard - MRR** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Dashboard - Agents** | ✅ | ✅ | ✅ | ✅ | ✅ | 👁️ | 👁️ |
| **Users - Invite** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Users - Delete** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Agents - Create** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Agents - Delete** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Settings - API Keys** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Settings - Models** | ✅ | ✅ | ✅ | 👁️ | 👁️ | 👁️ | 👁️ |
| **Cognitive Panel** | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Voice Configure** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Chat Send** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Memory Delete** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

Legend: ✅ Full Access | 👁️ View Only | ❌ Hidden

### 11.2 SpiceDB Check Pattern

```typescript
// Frontend: Check permission before rendering
async function canRender(element: string, resource: string): Promise<boolean> {
  const result = await permStore.check({
    subject: `user:${currentUser.id}`,
    resource: resource,
    permission: elementPermissionMap[element]
  });
  return result.allowed;
}

// Usage in Lit component
render() {
  return html`
    ${this.canDelete ? html`<button @click=${this.handleDelete}>Delete</button>` : nothing}
  `;
}
```

---

## 12. Dashboard Specifications by Role

### 12.1 SAAS Super Admin Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Platform Overview                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │   124    │ │  4,502   │ │ $24.5K   │ │  99.9%   │ │    2     │         │
│  │ Tenants  │ │ Agents   │ │   MRR    │ │ Uptime   │ │ 🔴Alerts │         │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
│                                                                             │
│  Revenue Trend        │  Tenant Distribution  │  System Health             │
│  ┌────────────────────┤  ┌────────────────────┤  ┌─────────────────────    │
│  │ 📈 Chart           │  │ 🥧 Pie by Tier     │  │ API: 🟢 45ms            │
│  └────────────────────┤  └────────────────────┤  │ DB:  🟢 12ms            │
│                       │                       │  │ Redis: 🟢 2ms           │
│                       │                       │  │ LLM: 🟢 350ms           │
│                       │                       │  └─────────────────────    │
│                                                                             │
│  Recent Activity        │  Top Tenants by Usage                             │
│  ┌──────────────────────┤  ┌──────────────────────────────────────────     │
│  │ Acme: tenant.create  │  │ 1. Acme Corp      4.2M tokens                  │
│  │ Globex: quota.warn   │  │ 2. TechStart      3.8M tokens                  │
│  │ ...                  │  │ 3. Globex Inc     2.1M tokens                  │
│  └──────────────────────┤  └──────────────────────────────────────────     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 12.2 Tenant SysAdmin Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Acme Corporation — Dashboard                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │   5/10   │ │  12/50   │ │  4.2M    │ │  45GB    │ │  $199    │         │
│  │ Agents   │ │ Users    │ │ Tokens   │ │ Storage  │ │ /month   │         │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
│                                                                             │
│  Your Agents                                   User Activity               │
│  ┌────────────────────────────────────────┐   ┌────────────────────────   │
│  │ 🤖 Support-AI    🟢 Running  [Manage] │   │ Jane: 234 messages       │
│  │ 🤖 Sales-Bot     🟡 Stopped  [Start]  │   │ Bob: 156 messages        │
│  │ 🤖 Research-AI   🟢 Running  [Manage] │   │ Alice: 89 messages       │
│  └────────────────────────────────────────┘   └────────────────────────   │
│                                                                             │
│  Token Usage This Month    │  Quick Actions                                │
│  ┌─────────────────────────┤  ┌──────────────────────────────────────     │
│  │ 📊 4.2M / 10M (42%)     │  │ [+ Invite User] [+ Create Agent]          │
│  │ ████████░░░░░░░░░░░░   │  │ [📋 View Audit] [⚙️ Settings]              │
│  └─────────────────────────┤  └──────────────────────────────────────     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 12.3 Developer Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Developer Dashboard                                        [Mode: DEV]     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  My Agents                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │ 🤖 Support-AI (developer access)                                      ││
│  │    Sessions: 45 today │ Errors: 2 │ Avg Latency: 320ms                ││
│  │    [Open Chat] [View Logs] [Debug Mode]                               ││
│  └────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│  Debug Console           │  Recent Errors                                  │
│  ┌───────────────────────┤  ┌──────────────────────────────────────────   │
│  │ > Tool execution logs │  │ ⚠️ 14:32 - Tool timeout (browser)          │
│  │ > API request/response│  │ ❌ 14:28 - LLM rate limit hit              │
│  │ > Memory operations   │  │ ⚠️ 14:15 - Memory write slow (>500ms)      │
│  └───────────────────────┤  └──────────────────────────────────────────   │
│                                                                             │
│  MCP Connections         │  Module SDK                                     │
│  ┌───────────────────────┤  ┌──────────────────────────────────────────   │
│  │ 🟢 filesystem         │  │ [📖 Documentation] [🧪 Playground]          │
│  │ 🟢 database           │  │ [📦 Component Library]                      │
│  │ 🟡 browser (unstable) │  │                                             │
│  └───────────────────────┤  └──────────────────────────────────────────   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 12.4 Trainer Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Trainer Dashboard                                          [Mode: TRN]     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Cognitive Status — Support-AI                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │ ┌──────────────────────────────────────────────────────────────────┐ ││
│  │ │ NEUROMODULATOR LEVELS                                            │ ││
│  │ │                                                                  │ ││
│  │ │ Dopamine    ████████████░░░░░░░░░░░░░░░░░░  0.72  [Adjust]       │ ││
│  │ │ Serotonin   ██████████████░░░░░░░░░░░░░░░░  0.65  [Adjust]       │ ││
│  │ │ Norepineph  █████████░░░░░░░░░░░░░░░░░░░░░  0.48  [Adjust]       │ ││
│  │ │ Acetylchol  ██████████████████░░░░░░░░░░░░  0.81  [Adjust]       │ ││
│  │ └──────────────────────────────────────────────────────────────────┘ ││
│  └────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│  Adaptation Status       │  Training Actions                               │
│  ┌───────────────────────┤  ┌──────────────────────────────────────────   │
│  │ Learning Rate: 0.001  │  │ [🔄 Trigger Sleep Cycle]                    │
│  │ Adapt. Weights: 1.2   │  │ [🧹 Reset Adaptation]                       │
│  │ Last Consolidation:   │  │ [📊 Export Training Data]                   │
│  │   2 hours ago         │  │ [📈 View Learning Curves]                   │
│  └───────────────────────┤  └──────────────────────────────────────────   │
│                                                                             │
│  Training Sessions       │  Cognitive Metrics                              │
│  ┌───────────────────────┤  ┌──────────────────────────────────────────   │
│  │ Today: 45 interactions│  │ Confidence: 0.87 avg                        │
│  │ Corrections: 3        │  │ Response Quality: 4.2/5                     │
│  │ Positive: 89%         │  │ Hallucination Rate: 2.1%                    │
│  └───────────────────────┤  └──────────────────────────────────────────   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 12.5 Standard User Dashboard (Chat)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 💬 AI Chat                                             [+ New Chat]        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Recent Conversations                │  Chat Area                          │
│  ┌───────────────────────────────────┤  ┌──────────────────────────────    │
│  │ 📝 Server config help      Today  │  │                              │    │
│  │ 📝 Database optimization   Today  │  │  Welcome! How can I help?   │    │
│  │ 📝 Code review request     Yest.  │  │                              │    │
│  │ 📝 API documentation       Yest.  │  │                              │    │
│  │ ...                               │  │                              │    │
│  └───────────────────────────────────┤  │                              │    │
│                                      │  │                              │    │
│  Quick Actions                       │  │                              │    │
│  ┌───────────────────────────────────┤  │                              │    │
│  │ [🧠 Memory] [🔧 Tools]            │  │                              │    │
│  │ [⚙️ Settings] [🎨 Themes]         │  │                              │    │
│  └───────────────────────────────────┤  └──────────────────────────────    │
│                                      │                                     │
│                                      │  ┌────────────────────────────────┐│
│                                      │  │ + │ Write message...   🎤 │ ▲ │││
│                                      │  └────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

**Document Status:** CANONICAL — Complete with CRUD, Permissions, Dashboards  
**Revision:** 2.0 (2025-12-22)
# Eye of God SAAS Platform — Software Requirements Specification

## IEEE 830 / ISO/IEC/IEEE 29148:2018 Compliant

---

## Document Control

| Field | Value |
|-------|-------|
| **Document ID** | SA01-SAAS-PLATFORM-SRS-2025-12 |
| **Version** | 2.0 |
| **Date** | 2025-12-22 |
| **Status** | CANONICAL |
| **Classification** | Internal |
| **Author** | SomaAgent Development Team |
| **Approvers** | Technical Lead, Product Owner |

### Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-21 | Dev Team | Initial SAAS Admin SRS |
| 2.0 | 2025-12-22 | Dev Team | Full platform SRS with auth flows, mode selection, infrastructure |

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) defines the complete requirements for the **Eye of God SAAS Platform** — a multi-tenant enterprise AI agent management system. It covers:

- Multi-tenant architecture
- Authentication and authorization flows
- God Mode (SAAS Admin) capabilities
- Tenant isolation and quota management
- Infrastructure requirements
- UI/UX specifications

### 1.2 Scope

**System Name:** Eye of God SAAS Platform

**Product Features:**
- Multi-tenant AI agent deployment platform
- Hierarchical permission system (Platform → Tenant → Agent)
- Real-time voice interaction (AgentVoiceBox integration)
- Fractal memory system (SomaBrain integration)
- Enterprise billing and quota management

**Out of Scope:**
- Mobile native applications (future phase)
- On-premise deployment (cloud-only for V1)

### 1.3 Definitions and Acronyms

| Term | Definition |
|------|------------|
| **God Mode** | SAAS Super Administrator access level with platform-wide visibility |
| **Tenant** | Enterprise customer organization with isolated resources |
| **Agent** | AI assistant instance deployed within a tenant |
| **SpiceDB** | Google Zanzibar-based authorization system |
| **MRR** | Monthly Recurring Revenue |

### 1.4 References

| Document | ID |
|----------|-----|
| UI Architecture | SA01-EOG-UI-ARCH-2025-12 |
| Design Document | SA01-EOG-DES-2025-12 |
| SAAS Admin SRS | SA01-SAAS-SRS-2025-12 |

---

## 2. Overall Description

### 2.1 Product Perspective

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EYE OF GOD SAAS PLATFORM                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         PRESENTATION LAYER                              │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │ │
│  │  │  Web UI      │  │  Desktop     │  │  CLI         │                  │ │
│  │  │  (Lit 3.x)   │  │  (Tauri)     │  │  (Ratatui)   │                  │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                           HTTPS/WSS (Connection Pool)                        │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                          API GATEWAY LAYER                              │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐  │ │
│  │  │              Django Ninja API (Port 8020)                         │  │ │
│  │  │  /api/v2/saas/*     Platform Administration                       │  │ │
│  │  │  /api/v2/auth/*     Authentication & Sessions                     │  │ │
│  │  │  /api/v2/admin/*    Tenant Administration                         │  │ │
│  │  │  /api/v2/agents/*   Agent Management                              │  │ │
│  │  │  /api/v2/chat/*     Conversation                                  │  │ │
│  │  │  /ws/v2/*           Real-time WebSocket                           │  │ │
│  │  └──────────────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                       AUTHORIZATION LAYER                               │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐  │ │
│  │  │                    SpiceDB (Port 50051)                           │  │ │
│  │  │  Platform → Tenant → Agent → User Permission Graph                │  │ │
│  │  └──────────────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                          DATA LAYER                                     │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │ │
│  │  │  PostgreSQL  │  │  Redis       │  │  Kafka       │                  │ │
│  │  │  (Primary)   │  │  (Cache/WS)  │  │  (Events)    │                  │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      INTEGRATION LAYER                                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │ │
│  │  │  SomaBrain   │  │AgentVoiceBox │  │  LLM APIs    │                  │ │
│  │  │  (Memory)    │  │  (Voice)     │  │  (OpenAI/+)  │                  │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 User Classes and Characteristics

| User Class | Description | Access Level |
|------------|-------------|--------------|
| **SAAS Super Admin** | Platform operators (God Mode) | Full platform access |
| **Tenant SysAdmin** | Organization owners | Full tenant access |
| **Tenant Admin** | Organization administrators | Tenant management |
| **Agent Admin** | Agent-level administrators | Agent configuration |
| **Developer** | Technical users | DEV mode access |
| **Trainer** | AI trainers | TRN mode access |
| **User** | Standard users | STD mode access |
| **Viewer** | Read-only users | RO mode access |

### 2.3 Operating Environment

| Component | Specification |
|-----------|---------------|
| **Cloud Provider** | AWS/GCP/Azure (Kubernetes) |
| **Container Runtime** | Docker + K8s |
| **Database** | PostgreSQL 15+ |
| **Cache** | Redis 7+ |
| **Message Queue** | Kafka 3+ |
| **Auth Service** | SpiceDB (Zanzibar) |
| **Billing Service** | Lago (Open Source) |

### 2.4 Infrastructure Stack (Complete)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INFRASTRUCTURE LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      CORE SERVICES                                   │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │    │
│  │  │  Django API  │  │  SomaBrain   │  │AgentVoiceBox │               │    │
│  │  │  (Port 8020) │  │  (Port 8030) │  │  (Port 8035) │               │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    PLATFORM SERVICES (Always Present)                │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │    │
│  │  │   SpiceDB    │  │    Lago      │  │   Keycloak   │               │    │
│  │  │  (Auth/RBAC) │  │  (Billing)   │  │   (SSO)      │               │    │
│  │  │  Port 50051  │  │  Port 3000   │  │  Port 8080   │               │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      DATA SERVICES                                   │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │    │
│  │  │  PostgreSQL  │  │    Redis     │  │    Kafka     │               │    │
│  │  │  (Primary)   │  │  (Cache/WS)  │  │  (Events)    │               │    │
│  │  │  Port 5432   │  │  Port 6379   │  │  Port 9092   │               │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    EXTERNAL INTEGRATIONS                             │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │    │
│  │  │  LLM APIs    │  │   Stripe     │  │   SendGrid   │               │    │
│  │  │  (OpenAI/+)  │  │  (Payments)  │  │  (Email)     │               │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2.5 Lago Billing System Integration

### 2.5.1 Lago Overview

Lago is an open-source usage-based billing platform that handles:
- Usage event ingestion
- Metrics aggregation  
- Pricing and packaging
- Invoicing
- Payment collection

**Reference:** https://www.getlago.com/

### 2.5.2 Lago 5-Step Billing Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        LAGO BILLING WORKFLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. USAGE INGESTION                                                          │
│     └── Agent sends events: tokens_used, api_calls, storage_bytes           │
│                                                                              │
│  2. METRICS AGGREGATION                                                      │
│     └── Lago aggregates: COUNT, SUM, MAX, LATEST, WEIGHTED_SUM              │
│                                                                              │
│  3. PRICING & PACKAGING                                                      │
│     └── Plans: Free, Starter, Team, Enterprise (with overages)              │
│                                                                              │
│  4. INVOICING                                                                │
│     └── Automatic invoice generation at billing period end                  │
│                                                                              │
│  5. PAYMENTS                                                                 │
│     └── Integration with Stripe, PayPal, or manual collection               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.5.3 Billable Metrics for SomaAgent

| Metric Code | Type | Description | Unit |
|-------------|------|-------------|------|
| `tokens_input` | SUM | LLM input tokens | tokens |
| `tokens_output` | SUM | LLM output tokens | tokens |
| `api_calls` | COUNT | API requests made | calls |
| `storage_bytes` | LATEST | Storage used | bytes |
| `voice_minutes` | SUM | Voice processing time | minutes |
| `agents_active` | MAX | Peak active agents | agents |
| `users_active` | MAX | Peak active users | users |
| `memories_stored` | COUNT | Memory writes | memories |

### 2.5.4 Lago API Integration

| Lago Entity | Eye of God Mapping | Description |
|-------------|-------------------|-------------|
| Customer | Tenant | One Lago customer per tenant |
| Subscription | Tenant.subscription | Active plan subscription |
| Plan | Subscription Tier | Free/Starter/Team/Enterprise |
| Billable Metric | Usage Metrics | Token/API/Storage tracking |
| Invoice | Billing → Invoices | Monthly billing documents |
| Wallet | Prepaid Credits | Token pre-purchase |
| Coupon | Discounts | Promotional pricing |

### 2.5.5 Eye of God ↔ Lago Flow

```
┌──────────────────────┐         ┌──────────────────────┐
│    Eye of God UI     │         │        Lago          │
│   (Billing Admin)    │         │   (Billing Engine)   │
├──────────────────────┤         ├──────────────────────┤
│                      │         │                      │
│  Create Tenant ──────┼────────▶│  Create Customer     │
│                      │         │                      │
│  Assign Plan ────────┼────────▶│  Create Subscription │
│                      │         │                      │
│  View Usage ◀────────┼─────────│  Return Metrics      │
│                      │         │                      │
│  View Invoices ◀─────┼─────────│  Return Invoices     │
│                      │         │                      │
│  Apply Coupon ───────┼────────▶│  Apply Coupon        │
│                      │         │                      │
│  Add Credits ────────┼────────▶│  Top-up Wallet       │
│                      │         │                      │
└──────────────────────┘         └──────────────────────┘
         │                                 │
         │                                 │
         ▼                                 ▼
┌──────────────────────┐         ┌──────────────────────┐
│    SomaAgent Core    │         │   Payment Provider   │
│   (Usage Events)     │         │     (Stripe)         │
├──────────────────────┤         ├──────────────────────┤
│                      │         │                      │
│  Chat Request ───────┼────────▶│  Lago sends events   │
│  Voice Call ─────────┼────────▶│  to Stripe for       │
│  Memory Write ───────┼────────▶│  payment collection  │
│                      │         │                      │
└──────────────────────┘         └──────────────────────┘
```

### 2.5.6 Lago UI in Eye of God

| View | Lago API Used | Description |
|------|---------------|-------------|
| Billing Dashboard | GET /analytics | Revenue charts, MRR |
| Tenant Billing | GET /customers/{id} | Tenant subscription & usage |
| Invoices | GET /invoices | Invoice list with download |
| Plans | GET /plans | Plan configuration |
| Usage | GET /billable_metrics | Real-time usage tracking |
| Wallets | GET /wallets | Prepaid credit balances |
| Coupons | GET/POST /coupons | Discount management |

---

### 2.6 Design Constraints

| Constraint | Rationale |
|------------|-----------|
| Multi-tenancy isolation | Enterprise security requirement |
| WebSocket for real-time | Voice latency requirements |
| SpiceDB for auth | Google Zanzibar model for scale |
| Lit 3.x for UI | Web Components for reusability |

---

## 3. System Features

### 3.1 Authentication System

#### 3.1.1 Login Flow

**FR-AUTH-001:** System shall provide email/password authentication  
**FR-AUTH-002:** System shall support OAuth2 providers (Google, GitHub, Microsoft)  
**FR-AUTH-003:** System shall issue JWT tokens with 24h expiration  
**FR-AUTH-004:** System shall support token refresh mechanism  

#### 3.1.2 Mode Selection Flow (God Mode Users)

**FR-AUTH-010:** After login, SAAS admins shall see mode selection screen  
**FR-AUTH-011:** Mode selection shall offer two options:
  - Platform Mode (God View)
  - Tenant Entry (Select tenant to impersonate)

**FR-AUTH-012:** Tenant Entry shall allow role selection (SysAdmin/Admin/User)  
**FR-AUTH-013:** Regular users shall bypass mode selection, entering their tenant directly  

```
Login Flow Diagram:

[Login Page] 
    │
    ▼
[Authenticate]
    │
    ├── IF role == SAAS_ADMIN
    │       │
    │       ▼
    │   [Mode Selection Screen]
    │       ├── Platform Mode → [Platform Dashboard]
    │       └── Enter Tenant → [Select Tenant] → [Tenant UI]
    │
    └── ELSE
            │
            ▼
        [Tenant UI] (User's assigned tenant)
```

#### 3.1.3 Session Management

**FR-AUTH-020:** Session shall store: user_id, tenant_id, entry_mode, role  
**FR-AUTH-021:** Session shall support runtime tenant switching (God users only)  
**FR-AUTH-022:** Session shall create audit log on tenant entry  

### 3.2 Multi-Tenancy System

#### 3.2.1 Tenant Isolation

**FR-TENANT-001:** Each tenant shall have isolated database schema/partition  
**FR-TENANT-002:** API requests shall require X-Tenant-ID header (except platform APIs)  
**FR-TENANT-003:** WebSocket connections shall be tenant-scoped  
**FR-TENANT-004:** File storage shall be tenant-isolated (S3 buckets/prefixes)  

#### 3.2.2 Tenant Lifecycle

**FR-TENANT-010:** SAAS admin shall create tenants with:
  - Name, slug, owner email, subscription tier

**FR-TENANT-011:** Tenants shall have states: pending, active, suspended, deleted  
**FR-TENANT-012:** Suspended tenants shall have read-only access  
**FR-TENANT-013:** Deleted tenants shall have 30-day recovery window  

### 3.3 Subscription & Quota System

#### 3.3.1 Subscription Tiers

**FR-SUB-001:** System shall support tiered subscriptions:

| Tier | Max Agents | Max Users | Tokens/Month | Storage | Price |
|------|------------|-----------|--------------|---------|-------|
| Free | 1 | 3 | 100K | 1 GB | $0 |
| Starter | 3 | 10 | 1M | 10 GB | $49/mo |
| Team | 10 | 50 | 10M | 100 GB | $199/mo |
| Enterprise | Unlimited | Unlimited | Custom | Custom | Custom |

**FR-SUB-002:** System shall enforce quota limits before resource creation  
**FR-SUB-003:** System shall send alerts at 80% and 100% quota usage  

### 3.4 Permission System (SpiceDB)

#### 3.4.1 Permission Schema

**FR-PERM-001:** Permissions shall follow hierarchy:
```
platform → tenant → agent → resource
```

**FR-PERM-002:** Permission checks shall occur at:
  - API Gateway (route-level)
  - Service Layer (action-level)
  - UI (component-level visibility)

#### 3.4.2 SpiceDB Relations

```zed
definition platform {}

definition saas_admin {
    relation platform: platform
    permission manage_tenants = platform
    permission view_billing = platform
    permission configure_platform = platform
}

definition tenant {
    relation sysadmin: user
    relation admin: user
    relation developer: user
    relation trainer: user
    relation member: user
    relation viewer: user
    relation subscription: subscription_tier
    
    permission manage = sysadmin
    permission administrate = sysadmin + admin
    permission develop = administrate + developer
    permission train = administrate + trainer
    permission use = develop + train + member
    permission view = use + viewer
}

definition agent {
    relation tenant: tenant
    relation owner: user
    relation admin: user
    relation developer: user
    relation trainer: user
    relation user: user
    relation viewer: user
    
    permission configure = owner + admin
    permission activate_dev = configure + developer
    permission activate_trn = configure + trainer
    permission interact = activate_dev + activate_trn + user
    permission observe = interact + viewer
}
```

### 3.5 UI System

#### 3.5.1 Platform UI (God Mode)

**FR-UI-001:** Platform Dashboard shall display:
  - Total tenants, agents, users
  - MRR and billing metrics
  - System health status
  - Recent activity feed

**FR-UI-002:** Tenants view shall display:
  - Tenant list with search/filter
  - Quota usage per tenant
  - Actions: Create, Enter, Suspend, Delete

**FR-UI-003:** Billing view shall display:
  - Revenue charts
  - Subscription breakdown
  - Invoice history

#### 3.5.2 Tenant UI (All Roles)

**FR-UI-010:** Same UI components for all roles  
**FR-UI-011:** Components shall hide based on permissions  
**FR-UI-012:** Actions shall disable based on permissions  

#### 3.5.3 Tenant Switcher

**FR-UI-020:** Header shall include tenant switcher (God users only)  
**FR-UI-021:** Switcher shall show: Platform option + tenant list  
**FR-UI-022:** Switching shall preserve current view when possible  

---

## 4. External Interface Requirements

### 4.1 User Interfaces

| Screen | Route | Description |
|--------|-------|-------------|
| Login | `/login` | Email/password auth |
| Mode Selection | `/select-mode` | God user mode selection |
| Platform Dashboard | `/platform` | SAAS admin dashboard |
| Tenants | `/platform/tenants` | Tenant management |
| Billing | `/platform/billing` | Revenue & invoices |
| Chat | `/chat` | Agent conversation |
| Memory | `/memory` | SomaBrain browser |
| Settings | `/settings` | User/agent settings |

### 4.2 API Interfaces

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v2/auth/login` | POST | User authentication |
| `/api/v2/auth/mode-select` | POST | Set entry mode (God users) |
| `/api/v2/saas/tenants` | GET/POST | Tenant CRUD |
| `/api/v2/saas/tenants/{id}/enter` | POST | Enter tenant (impersonate) |
| `/api/v2/admin/users` | GET/POST | Tenant user management |
| `/api/v2/agents` | GET/POST | Agent CRUD |

### 4.3 Hardware Interfaces

N/A (Cloud-native, no hardware dependencies)

### 4.4 Software Interfaces

| System | Interface | Purpose |
|--------|-----------|---------|
| SomaBrain | REST/gRPC | Fractal memory |
| AgentVoiceBox | WebSocket | Real-time voice |
| OpenAI/Anthropic | REST | LLM completions |
| Stripe/Paddle | REST | Billing integration |
| SpiceDB | gRPC | Authorization |

---

## 5. Non-Functional Requirements

### 5.1 Performance

| Metric | Requirement |
|--------|-------------|
| API Latency (p95) | < 200ms |
| Page Load | < 2s |
| WebSocket Latency | < 50ms |
| Voice Round-trip | < 500ms |
| Concurrent Users | 10,000+ per tenant |

### 5.2 Security

| Requirement | Implementation |
|-------------|----------------|
| Encryption at Rest | AES-256 |
| Encryption in Transit | TLS 1.3 |
| Password Storage | bcrypt (cost 12) |
| Session Tokens | JWT (RS256) |
| API Auth | Bearer tokens |
| RBAC | SpiceDB (Zanzibar) |

### 5.3 Scalability

| Component | Strategy |
|-----------|----------|
| API | Horizontal pod scaling (K8s HPA) |
| Database | Read replicas, sharding |
| Cache | Redis Cluster |
| WebSocket | Sticky sessions + Redis Pub/Sub |

### 5.4 Availability

| Metric | Target |
|--------|--------|
| Uptime | 99.9% |
| RTO | 1 hour |
| RPO | 15 minutes |

---

## 6. Implementation Priority

| Phase | Features | Timeline |
|-------|----------|----------|
| **Phase 1** | Login, Auth, Tenant CRUD, Basic UI | Week 1-2 |
| **Phase 2** | Mode Selection, Quota Enforcement, Agent CRUD | Week 3-4 |
| **Phase 3** | Billing Integration, Usage Tracking | Week 5-6 |
| **Phase 4** | Voice Integration, Memory Integration | Week 7-8 |
| **Phase 5** | Analytics, Advanced Admin | Week 9-10 |

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| Eye of God | The admin console UI for SomaAgent |
| God Mode | SAAS Super Admin access level |
| SomaBrain | Fractal memory system |
| AgentVoiceBox | Real-time voice processing system |
| SpiceDB | Zanzibar-based authorization database |
| Tenant | An enterprise customer organization |

---

**Document Status:** CANONICAL — Ready for Implementation
# SAAS Sys Admin — Complete UI SRS

**Document ID:** SA01-SAAS-SYSADMIN-UI-SRS-2025-12  
**Version:** 1.0  
**Date:** 2025-12-22  
**Status:** CANONICAL  
**Classification:** ENTERPRISE  
**Compliance:** ISO/IEC/IEEE 29148:2018

---

## Document Control

| Field | Value |
|-------|-------|
| Persona | SAAS System Administrator (God Mode) |
| Role Code | `saas_superadmin` |
| SpiceDB Permissions | `platform->manage_tenants`, `platform->view_billing`, `platform->configure_platform` |

---

## 1. Persona Definition

### 1.1 Who is the SAAS Sys Admin?

The **SAAS System Administrator** (also called "God Mode" user) is a super-administrator with complete control over the entire SomaAgent platform. They:

- Manage ALL tenants (create, suspend, delete)
- Configure subscription tiers and quotas
- View platform-wide billing and revenue
- Access any tenant as impersonator for support
- Configure platform-wide feature flags
- Monitor system health across all tenants

### 1.2 NOT Covered by This Document

- Tenant-level administration → See `TENANT_ADMIN_UI_SRS.md`
- Agent-level user management → See `AGENT_USER_UI_SRS.md`
- Regular user interactions → See `STANDARD_USER_UI_SRS.md`

---

## 2. Complete User Journey

### 2.1 User Flow Diagram

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                         SAAS SYS ADMIN COMPLETE JOURNEY                         │
└────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────┐
    │   START     │
    └──────┬──────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                          AUTHENTICATION PHASE                            │
    │                                                                          │
    │  ┌────────────────┐     ┌────────────────┐     ┌────────────────┐       │
    │  │   /login       │ ──▶ │ /auth/callback │ ──▶ │ Token Stored   │       │
    │  │  (Email/OAuth) │     │ (Google/SSO)   │     │ (localStorage) │       │
    │  └────────────────┘     └────────────────┘     └────────┬───────┘       │
    └─────────────────────────────────────────────────────────┬───────────────┘
                                                              │
                                                              ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                          ROLE DETECTION PHASE                            │
    │                                                                          │
    │  Backend checks SpiceDB: lookup('user:123', 'platform', 'manage_tenants')│
    │                                                                          │
    │      ┌─────────────────┐                                                │
    │      │ is_saas_admin?  │                                                │
    │      └────────┬────────┘                                                │
    │               │                                                          │
    │       ┌───────┴───────┐                                                  │
    │       │               │                                                  │
    │    YES│            NO │                                                  │
    │       ▼               ▼                                                  │
    │  ┌─────────┐    ┌─────────────┐                                         │
    │  │/mode-   │    │ /dashboard  │ (regular user)                          │
    │  │ select  │    │ or /chat    │                                         │
    │  └────┬────┘    └─────────────┘                                         │
    └───────┼─────────────────────────────────────────────────────────────────┘
            │
            ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                          MODE SELECTION PHASE                            │
    │                                                                          │
    │     ┌────────────────────────────────────────────────────────┐          │
    │     │               /mode-select                              │          │
    │     │                                                         │          │
    │     │   ┌─────────────────┐      ┌─────────────────┐         │          │
    │     │   │ ⚡ GOD MODE     │      │ 🏢 TENANT VIEW  │         │          │
    │     │   │ Platform Admin  │      │ Enter as User   │         │          │
    │     │   │ • 124 Tenants   │      │ • Last: Acme    │         │          │
    │     │   │ • 4502 Agents   │      │ • Role: Owner   │         │          │
    │     │   │ • 99.9% Uptime  │      │ • 5 Agents      │         │          │
    │     │   └────────┬────────┘      └────────┬────────┘         │          │
    │     └────────────┼───────────────────────┼──────────────────┘          │
    │                  │                       │                              │
    │            CLICK │                 CLICK │                              │
    │                  ▼                       ▼                              │
    │         ┌────────────────┐      ┌────────────────┐                     │
    │         │ /platform      │      │ /tenant-select │                     │
    │         │ (God Dashboard)│      │ (Pick Tenant)  │                     │
    │         └────────────────┘      └────────────────┘                     │
    └─────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                          PLATFORM ADMIN PHASE                            │
    │                                                                          │
    │  ┌──────────────────────────────────────────────────────────────────┐   │
    │  │                     SIDEBAR NAVIGATION                            │   │
    │  │                                                                   │   │
    │  │  PLATFORM                                                         │   │
    │  │  📊 Dashboard ──────────────────▶ /platform                       │   │
    │  │  🏢 Tenants ────────────────────▶ /platform/tenants               │   │
    │  │  💳 Billing ────────────────────▶ /platform/billing               │   │
    │  │  📦 Subscriptions ──────────────▶ /platform/subscriptions         │   │
    │  │  🚩 Feature Flags ──────────────▶ /platform/flags                 │   │
    │  │                                                                   │   │
    │  │  SYSTEM                                                           │   │
    │  │  ⚙️ Settings ───────────────────▶ /settings                       │   │
    │  │  📋 Audit Log ──────────────────▶ /platform/audit                 │   │
    │  │  🔐 Security ───────────────────▶ /platform/security              │   │
    │  │                                                                   │   │
    │  └──────────────────────────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Screen 1: Login

### 3.1 Route & Component

| Property | Value |
|----------|-------|
| Route | `/login` |
| Component | `saas-login.ts` |
| Permission | Public |

### 3.2 Wireframe

```
┌─────────────────────────────────────────────────────────────────┐
│                          (Page: #f5f5f5)                        │
│                                                                 │
│                    ┌─────────────────────────┐                  │
│                    │     (Card: #ffffff)     │                  │
│                    │                         │                  │
│                    │  ┌───┐                  │                  │
│                    │  │▓▓▓│ SomaAgent        │                  │
│                    │  │▓▓▓│ SaaS Admin       │                  │
│                    │  └───┘                  │                  │
│                    │                         │                  │
│                    │  Sign in to your        │                  │
│                    │  account                │                  │
│                    │                         │                  │
│                    │  ┌─────────────────────┐│                  │
│                    │  │ 🔵 Continue with    ││                  │
│                    │  │    Google           ││                  │
│                    │  └─────────────────────┘│                  │
│                    │                         │                  │
│                    │  ┌─────────────────────┐│                  │
│                    │  │ 🏢 Enterprise SSO   ││                  │
│                    │  │    (Keycloak)       ││                  │
│                    │  └─────────────────────┘│                  │
│                    │                         │                  │
│                    │  ──────── or ────────   │                  │
│                    │                         │                  │
│                    │  Email *                │                  │
│                    │  ┌─────────────────────┐│                  │
│                    │  │ admin@platform.io   ││                  │
│                    │  └─────────────────────┘│                  │
│                    │                         │                  │
│                    │  Password *  [Forgot?]  │                  │
│                    │  ┌─────────────────────┐│                  │
│                    │  │ ••••••••••••        ││                  │
│                    │  └─────────────────────┘│                  │
│                    │                         │                  │
│                    │  ┌─────────────────────┐│                  │
│                    │  │ ▓▓▓  Sign in  ▓▓▓   ││ (black btn)     │
│                    │  └─────────────────────┘│                  │
│                    │                         │                  │
│                    │  Don't have an account? │                  │
│                    │  [Contact Sales]        │                  │
│                    │                         │                  │
│                    └─────────────────────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 User Actions

| Action | Element | Validation | API Call | Next Screen |
|--------|---------|------------|----------|-------------|
| Click "Continue with Google" | OAuth Button | None | `GoogleAuthService.getAuthUrl()` | Redirect to Google |
| Click "Enterprise SSO" | OAuth Button | None | `KeycloakService.getAuthUrl()` | Redirect to Keycloak |
| Submit Email/Password | Form | Email format, Password min 8 | `POST /api/v2/auth/login` | `/mode-select` or error |
| Click "Forgot?" | Link | None | None | `/forgot-password` |

### 3.4 Sequence Diagram

```mermaid
sequenceDiagram
    actor Admin as SAAS Admin
    participant Login as saas-login
    participant API as /api/v2/auth/login
    participant SpiceDB
    participant DB as PostgreSQL

    Admin->>Login: Enter credentials
    Admin->>Login: Click "Sign in"
    Login->>Login: Validate (email format, password >= 8)
    
    alt Validation Fails
        Login-->>Admin: Show inline error (red border)
    end
    
    Login->>API: POST {email, password}
    API->>DB: SELECT * FROM users WHERE email = ?
    
    alt User Not Found
        API-->>Login: 401 {error: "Invalid credentials"}
        Login-->>Admin: Show error banner
    end
    
    API->>API: bcrypt.compare(password, user.password_hash)
    
    alt Password Wrong
        API-->>Login: 401 {error: "Invalid credentials"}
        Login-->>Admin: Show error banner
    end
    
    API->>SpiceDB: lookup('user:' + user.id, 'platform', 'manage_tenants')
    SpiceDB-->>API: {allowed: true, roles: ['saas_superadmin']}
    
    API->>DB: INSERT INTO sessions (user_id, token, expires_at)
    API-->>Login: 200 {token, user: {..., is_saas_admin: true}, redirect_path: '/mode-select'}
    
    Login->>Login: localStorage.setItem('saas_auth_token', token)
    Login->>Login: localStorage.setItem('saas_user', JSON.stringify(user))
    Login->>Login: Router.go('/mode-select')
```

### 3.5 State Diagram

```mermaid
stateDiagram-v2
    [*] --> Idle: Component loaded
    
    Idle --> Validating: Submit clicked
    Validating --> Idle: Validation failed
    Validating --> Loading: Validation passed
    
    Loading --> Error: API error
    Loading --> Success: API success
    
    Error --> Idle: User fixes input
    
    Success --> Storing: Store token
    Storing --> Redirecting: Token stored
    Redirecting --> [*]: Navigate to /mode-select
```

---

## 4. Screen 2: Mode Selection

### 4.1 Route & Component

| Property | Value |
|----------|-------|
| Route | `/mode-select` |
| Component | `saas-mode-selection.ts` |
| Permission | `saas_admin` (must be SAAS admin to see this screen) |

### 4.2 Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          (Page: Dark gradient #0f172a)                       │
│                                                                              │
│                          Select Interface Mode                               │
│                          Access your specialized workspace                   │
│                                                                              │
│   ┌────────────────────────────────────┐  ┌─────────────────────────────────┐│
│   │  ⚡ God Mode                       │  │  🏢 Tenant Viewer               ││
│   │     [SUPER ADMIN]                  │  │     [STANDARD VIEW]             ││
│   ├────────────────────────────────────┤  ├─────────────────────────────────┤│
│   │                                    │  │                                 ││
│   │  Full infrastructure control,     │  │  Focused workspace for agent   ││
│   │  multi-tenant oversight, and      │  │  management, conversation      ││
│   │  system-wide configuration.       │  │  flows, and memory.            ││
│   │                                    │  │                                 ││
│   ├────────────────────────────────────┤  ├─────────────────────────────────┤│
│   │  ┌──────────┐  ┌──────────┐       │  │  ┌──────────┐  ┌──────────┐    ││
│   │  │   124    │  │  4,502   │       │  │  │ Acme Corp│  │  Owner   │    ││
│   │  │ Tenants  │  │  Agents  │       │  │  │Last View │  │ Role     │    ││
│   │  └──────────┘  └──────────┘       │  │  └──────────┘  └──────────┘    ││
│   │  ┌──────────┐  ┌──────────┐       │  │  ┌──────────┐  ┌──────────┐    ││
│   │  │  99.9%   │  │    2     │       │  │  │    5     │  │   12     │    ││
│   │  │🟢Uptime  │  │🟡Alerts  │       │  │  │ Agents   │  │ Events   │    ││
│   │  └──────────┘  └──────────┘       │  │  └──────────┘  └──────────┘    ││
│   ├────────────────────────────────────┤  ├─────────────────────────────────┤│
│   │ Access: Tier 0 (Root)              │  │ Context: Single Tenant           ││
│   │              Configure System →    │  │              Enter Workspace →  ││
│   └────────────────────────────────────┘  └─────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 User Actions

| Action | Element | API Call | Next Screen |
|--------|---------|----------|-------------|
| Click "God Mode" card | Card | None | Show confirmation modal |
| Confirm God Mode | Modal button | `POST /api/v2/session/mode` | `/platform` |
| Click "Tenant Viewer" card | Card | None | Show tenant picker modal |
| Select tenant → Confirm | Modal | `POST /api/v2/session/tenant` | `/dashboard` |

### 4.4 Sequence Diagram - Enter God Mode

```mermaid
sequenceDiagram
    actor Admin as SAAS Admin
    participant ModeSelect as saas-mode-selection
    participant API as /api/v2
    participant Session as SessionStorage

    Admin->>ModeSelect: Page loads
    ModeSelect->>API: GET /saas/stats
    API-->>ModeSelect: {tenants: 124, agents: 4502, uptime: '99.9%', alerts: 2}
    ModeSelect->>ModeSelect: Display stats in cards
    
    Admin->>ModeSelect: Click "God Mode" card
    ModeSelect->>ModeSelect: Show confirmation modal
    
    Note over ModeSelect: Modal shows:<br/>- Session ID<br/>- Gateway Region<br/>- Latency<br/>- Warning about audit logging
    
    Admin->>ModeSelect: Click "Initialize & Enter"
    ModeSelect->>Session: setItem('saas_mode', 'platform')
    ModeSelect->>API: POST /session/mode {mode: 'platform'}
    API-->>ModeSelect: 200 OK
    ModeSelect->>ModeSelect: Router.go('/platform')
```

---

## 5. Screen 3: Platform Dashboard

### 5.1 Route & Component

| Property | Value |
|----------|-------|
| Route | `/platform` |
| Component | `saas-platform-dashboard.ts` |
| Permission | `platform->manage_tenants` |

### 5.2 Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ┌────────────┐ │ Platform Dashboard                         [Brian F. ▼]   │
│ │ SomaAgent  │ │────────────────────────────────────────────────────────────│
│ │            │ │                                                            │
│ │ PLATFORM   │ │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│ │ 📊Dashboard│◀│ │   124    │ │  4,502   │ │ $24.5K   │ │  99.9%   │       │
│ │ 🏢Tenants  │ │ │ Tenants  │ │ Agents   │ │   MRR    │ │ Uptime   │       │
│ │ 💳Billing  │ │ │  ↑12%    │ │  ↑8%     │ │  ↑15%    │ │  ✓       │       │
│ │ 📦Subs     │ │ └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│ │            │ │                                                            │
│ │ SYSTEM     │ │ Revenue Trend                               [Last 12 mo ▼]│
│ │ ⚙️Settings │ │ ┌────────────────────────────────────────────────────────┐│
│ │ 📋Audit    │ │ │  $30K ─                                    ▄▄          ││
│ │ 🔐Security │ │ │  $25K ─                               ▄▄▄ ██          ││
│ │            │ │ │  $20K ─                          ▄▄▄ ███ ██          ││
│ │            │ │ │  $15K ─                     ▄▄▄ ███ ███ ██          ││
│ │            │ │ │  $10K ─                ▄▄▄ ███ ███ ███ ██          ││
│ │            │ │ │   $5K ─           ▄▄▄ ███ ███ ███ ███ ██          ││
│ │            │ │ │    $0 ─ Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec ││
│ │            │ │ └────────────────────────────────────────────────────────┘│
│ │            │ │                                                            │
│ │            │ │ Recent Activity                                [View All →]│
│ │ ─────────  │ │ ┌────────────────────────────────────────────────────────┐│
│ │ [Avatar]   │ │ │ 🟢 Acme Corp      New tenant created        2 min ago  ││
│ │ Platform   │ │ │ 🟡 Globex Inc     Quota warning: 80% agents 15 min ago ││
│ │ Admin      │ │ │ 🔵 TechStart      Agent "Support-AI" deployed 1 hr ago││
│ │            │ │ │ 🟢 DataFlow       Upgraded: Team → Enterprise 2 hr ago ││
│ └────────────┘ │ └────────────────────────────────────────────────────────┘│
└────────────────┴────────────────────────────────────────────────────────────┘
```

### 5.3 Components Breakdown

| Component | Data Source | Refresh Rate |
|-----------|-------------|--------------|
| Stat Cards (4x) | `GET /api/v2/saas/stats` | 60 seconds |
| Revenue Chart | `GET /api/v2/saas/billing/revenue` | On load |
| Activity Feed | `GET /api/v2/saas/activity` | WebSocket real-time |
| Health Status | `GET /api/v2/saas/health` | 30 seconds |

### 5.4 API Endpoints

| Endpoint | Method | Response |
|----------|--------|----------|
| `/api/v2/saas/stats` | GET | `{tenants: int, agents: int, mrr: float, uptime: str}` |
| `/api/v2/saas/billing/revenue` | GET | `{months: [{month: str, revenue: float}]}` |
| `/api/v2/saas/activity` | GET | `{items: [{id, type, tenant, message, timestamp}]}` |
| `/api/v2/saas/health` | GET | `{status: 'healthy'|'degraded', services: [...]}` |

---

## 6. Screen 4: Tenant Management

### 6.1 Route & Component

| Property | Value |
|----------|-------|
| Route | `/platform/tenants` |
| Component | `saas-tenants.ts` |
| Permission | `platform->manage_tenants` |

### 6.2 Wireframe - List View

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │ Tenants                                    [+ Create Tenant]   │
│            │─────────────────────────────────────────────────────────────────│
│            │                                                                 │
│            │ 🔍 Search tenants...        [Status ▼] [Tier ▼] [Sort: Name ▼] │
│            │                                                                 │
│            │ ┌───────────────────────────────────────────────────────────┐  │
│            │ │                                                           │  │
│            │ │  Organization    Status    Tier        Agents   Created   │  │
│            │ │ ─────────────────────────────────────────────────────────│  │
│            │ │  Acme Corp       🟢Active  Enterprise  45/∞     Dec 1     │  │
│            │ │  [acme-corp]                                      [···]   │  │
│            │ │ ─────────────────────────────────────────────────────────│  │
│            │ │  Globex Inc      🟢Active  Team        12/50    Nov 15    │  │
│            │ │  [globex-inc]                                     [···]   │  │
│            │ │ ─────────────────────────────────────────────────────────│  │
│            │ │  TechStart       🟡Pending Starter     3/10     Dec 20    │  │
│            │ │  [techstart]                                      [···]   │  │
│            │ │ ─────────────────────────────────────────────────────────│  │
│            │ │  DataFlow        🔴Suspend Free        1/3      Oct 5     │  │
│            │ │  [dataflow]                                       [···]   │  │
│            │ │                                                           │  │
│            │ └───────────────────────────────────────────────────────────┘  │
│            │                                                                 │
│            │ Showing 1-4 of 124 tenants            [← 1  2  3 ... 32 →]     │
│            │                                                                 │
└────────────┴─────────────────────────────────────────────────────────────────┘
```

### 6.3 Row Actions Menu [···]

```
┌─────────────────────────┐
│ 👁️  View Details        │
│ ✏️  Edit Tenant         │
│ ➡️  Enter as Admin      │
│ ───────────────────────│
│ ⏸️  Suspend             │
│ ▶️  Activate            │
│ ───────────────────────│
│ 🗑️  Delete              │
└─────────────────────────┘
```

### 6.4 Create Tenant Modal

```
┌─────────────────────────────────────────────────────────┐
│  Create New Tenant                                   ✕  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Organization Name *                                    │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Acme Corporation                                │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Slug (URL identifier) *                                │
│  ┌─────────────────────────────────────────────────┐   │
│  │ acme-corp                                       │   │
│  └─────────────────────────────────────────────────┘   │
│  URL: https://app.somaagent.io/tenant/acme-corp         │
│                                                         │
│  Owner Email *                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ admin@acme.com                                  │   │
│  └─────────────────────────────────────────────────┘   │
│  An invitation will be sent to this email              │
│                                                         │
│  Subscription Tier *                                    │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Team ($199/mo)                              ▼   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Tier Details:                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ • Up to 10 agents                               │   │
│  │ • Up to 50 users                                │   │
│  │ • 10M tokens/month                              │   │
│  │ • 100 GB storage                                │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  [Cancel]                                  [Create] █   │
└─────────────────────────────────────────────────────────┘
```

### 6.5 Sequence Diagram - Create Tenant

```mermaid
sequenceDiagram
    actor Admin as SAAS Admin
    participant UI as saas-tenants
    participant API as /api/v2/saas/tenants
    participant SpiceDB
    participant Lago as Lago Billing
    participant Email as EmailService
    participant DB as PostgreSQL

    Admin->>UI: Click "+ Create Tenant"
    UI->>UI: Show modal
    
    Admin->>UI: Fill form (name, slug, email, tier)
    Admin->>UI: Click "Create"
    
    UI->>UI: Validate form
    UI->>API: POST {name, slug, owner_email, tier_id}
    
    API->>DB: SELECT 1 FROM tenants WHERE slug = ?
    
    alt Slug exists
        API-->>UI: 409 {error: "Slug already taken"}
        UI-->>Admin: Show error "This slug is already in use"
    end
    
    API->>DB: BEGIN TRANSACTION
    API->>DB: INSERT INTO tenants (name, slug, tier_id, status)
    API->>DB: INSERT INTO users (email, tenant_id, role='sysadmin', status='invited')
    API->>SpiceDB: write('tenant:' + tenant_id, 'sysadmin', 'user:' + user_id)
    API->>Lago: POST /customers {external_id, name, email}
    API->>Lago: POST /subscriptions {customer_id, plan_code: tier.code}
    API->>Email: SendInvitation(email, tenant, token)
    API->>DB: COMMIT
    
    API-->>UI: 201 {tenant: {...}}
    UI->>UI: Close modal
    UI->>UI: Add tenant to list (optimistic)
    UI-->>Admin: Show success toast "Tenant created"
```

### 6.6 Tenant Detail Panel

When clicking "View Details" or a row:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ← Back to Tenants                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │                                                                        │ │
│ │  🏢 Acme Corporation                               🟢 Active           │ │
│ │     acme-corp                                                          │ │
│ │                                                                        │ │
│ │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │ │
│ │  │    45    │ │    8     │ │  4.2M    │ │  32 GB   │ │  $499    │    │ │
│ │  │ Agents   │ │ Users    │ │ Tokens   │ │ Storage  │ │ MRR      │    │ │
│ │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘    │ │
│ │                                                                        │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ [Overview] [Users] [Agents] [Billing] [Settings] [Audit]                    │
│                                                                             │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ Subscription: Enterprise ($499/mo)                                     │ │
│ │ Owner: admin@acme.com                                                  │ │
│ │ Created: December 1, 2024                                              │ │
│ │ Last Activity: 2 minutes ago                                           │ │
│ │                                                                        │ │
│ │ Quota Usage:                                                           │ │
│ │ Agents:  45/∞ ████████████████████████░░░░░░░░░░                      │ │
│ │ Users:   8/∞  ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░                       │ │
│ │ Tokens:  4.2M/10M ████████████████░░░░░░░░░░░░░░                       │ │
│ │ Storage: 32GB/100GB ████████████░░░░░░░░░░░░░░░░                       │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ [Edit Settings]  [Suspend Tenant]  [Enter as Admin]  [Delete]               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Screen 5: Billing Dashboard

### 7.1 Route & Component

| Property | Value |
|----------|-------|
| Route | `/platform/billing` |
| Component | `saas-billing.ts` |
| Permission | `platform->view_billing` |

### 7.2 Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │ Billing & Revenue                              [This Year ▼]  │
│            │─────────────────────────────────────────────────────────────────│
│            │                                                                 │
│            │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│            │ │  $24.5K  │ │  $281    │ │    87    │ │   2.3%   │           │
│            │ │   MRR    │ │   ARPU   │ │ Paying   │ │  Churn   │           │
│            │ │  ↑ 12%   │ │  ↑ 5%    │ │  ↑ 8     │ │  ↓ 0.5%  │           │
│            │ └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│            │                                                                 │
│            │ Revenue by Tier                    Tenant Distribution         │
│            │ ┌─────────────────────────┐       ┌─────────────────────────┐ │
│            │ │                         │       │        🟢12%            │ │
│            │ │ Enterprise ██████ $12.4K│       │      ████               │ │
│            │ │ Team       ████   $7.9K │       │    ████ 🔵32%           │ │
│            │ │ Starter    ██     $3.7K │       │  ██████                 │ │
│            │ │ Free       ░      $0    │       │ ████████ 🟡45%          │ │
│            │ │                         │       │ ██████████              │ │
│            │ └─────────────────────────┘       │ 🔘11% Free              │ │
│            │                                    └─────────────────────────┘ │
│            │                                                                 │
│            │ Recent Invoices                               [View All →]     │
│            │ ┌───────────────────────────────────────────────────────────┐ │
│            │ │ Invoice       Tenant       Amount   Status    Due         │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │ INV-2024-142  Acme Corp    $499     🟢 Paid   Dec 1       │ │
│            │ │ INV-2024-141  Globex Inc   $199     🟢 Paid   Dec 1       │ │
│            │ │ INV-2024-140  TechStart    $49      🟡 Pending Dec 1      │ │
│            │ │ INV-2024-139  NewCo        $199     🔴 Overdue Nov 15     │ │
│            │ └───────────────────────────────────────────────────────────┘ │
│            │                                                                 │
└────────────┴─────────────────────────────────────────────────────────────────┘
```

### 7.3 Lago Integration

| Metric | Lago API | Endpoint |
|--------|----------|----------|
| MRR | `/analytics/mrr` | `GET /api/v2/saas/billing/mrr` |
| ARPU | Calculated | MRR / paying_customers |
| Churn | `/analytics/invoice_collection` | `GET /api/v2/saas/billing/churn` |
| Invoices | `/invoices` | `GET /api/v2/saas/billing/invoices` |

---

## 8. Screen 6: Subscription Tiers

### 8.1 Route & Component

| Property | Value |
|----------|-------|
| Route | `/platform/subscriptions` |
| Component | `saas-subscriptions.ts` |
| Permission | `platform->configure_platform` |

### 8.2 Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │ Subscription Tiers                          [+ Create Tier]   │
│            │─────────────────────────────────────────────────────────────────│
│            │                                                                 │
│            │ ┌─────────────────────────────────────────────────────────────┐│
│            │ │                                                             ││
│            │ │  Tier         Agents  Users   Tokens    Storage   Price     ││
│            │ │ ─────────────────────────────────────────────────────────── ││
│            │ │  🔘 Free      1       3       100K      1 GB      $0        ││
│            │ │     14 tenants                                     [Edit]   ││
│            │ │ ─────────────────────────────────────────────────────────── ││
│            │ │  🟡 Starter   3       10      1M        10 GB     $49/mo    ││
│            │ │     56 tenants                                     [Edit]   ││
│            │ │ ─────────────────────────────────────────────────────────── ││
│            │ │  🔵 Team      10      50      10M       100 GB    $199/mo   ││
│            │ │     42 tenants                                     [Edit]   ││
│            │ │ ─────────────────────────────────────────────────────────── ││
│            │ │  🟢 Enterprise ∞      ∞       Custom    Custom    Custom    ││
│            │ │     12 tenants                                     [Edit]   ││
│            │ │                                                             ││
│            │ └─────────────────────────────────────────────────────────────┘│
│            │                                                                 │
└────────────┴─────────────────────────────────────────────────────────────────┘
```

### 8.3 Edit Tier Modal

```
┌─────────────────────────────────────────────────────────┐
│  Edit Tier: Team                                     ✕  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Tier Name *                                            │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Team                                            │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Quotas                                                 │
│                                                         │
│  Max Agents *           Max Users *                     │
│  ┌──────────────┐       ┌──────────────┐               │
│  │ 10           │       │ 50           │               │
│  └──────────────┘       └──────────────┘               │
│                                                         │
│  Tokens/Month *         Storage (GB) *                  │
│  ┌──────────────┐       ┌──────────────┐               │
│  │ 10000000     │       │ 100          │               │
│  └──────────────┘       └──────────────┘               │
│                                                         │
│  Pricing                                                │
│                                                         │
│  Monthly Price (USD) *                                  │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 199                                             │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ⚠️ Changes will affect new subscriptions only.         │
│     Existing tenants keep their current limits.         │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  [Cancel]                              [Save Changes]   │
└─────────────────────────────────────────────────────────┘
```

---

## 9. Screen 7: Platform Audit Log

### 9.1 Route & Component

| Property | Value |
|----------|-------|
| Route | `/platform/audit` |
| Component | `saas-audit.ts` |
| Permission | `platform->manage_tenants` |

### 9.2 Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │ Platform Audit Log                             [Export CSV]   │
│            │─────────────────────────────────────────────────────────────────│
│            │                                                                 │
│            │ 🔍 Search actions...  [Action ▼] [Actor ▼] [Date Range ▼]     │
│            │                                                                 │
│            │ ┌───────────────────────────────────────────────────────────┐ │
│            │ │                                                           │ │
│            │ │  Timestamp         Actor         Action         Target    │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │  Dec 22, 14:32:01  admin@plat    tenant.create   Acme     │ │
│            │ │  Dec 22, 14:30:45  admin@plat    user.invite     john@acm │ │
│            │ │  Dec 22, 14:15:22  system        quota.warning   Globex   │ │
│            │ │  Dec 22, 13:55:10  admin@plat    tier.update     Team     │ │
│            │ │  Dec 22, 12:30:00  support@plat  tenant.imperson TechStar │ │
│            │ │  Dec 22, 11:00:00  admin@plat    tenant.suspend  DataFlow │ │
│            │ │                                                           │ │
│            │ └───────────────────────────────────────────────────────────┘ │
│            │                                                                 │
│            │ Showing 1-6 of 1,242 events          [← 1  2  3 ... 208 →]    │
│            │                                                                 │
└────────────┴─────────────────────────────────────────────────────────────────┘
```

---

## 10. Summary: All SAAS Admin Screens

| # | Screen | Route | Component | Status |
|---|--------|-------|-----------|--------|
| 1 | Login | `/login` | `saas-login.ts` | ✅ Exists |
| 2 | Mode Selection | `/mode-select` | `saas-mode-selection.ts` | ✅ Exists |
| 3 | Platform Dashboard | `/platform` | `saas-platform-dashboard.ts` | ✅ Exists |
| 4 | Tenant Management | `/platform/tenants` | `saas-tenants.ts` | ✅ Exists |
| 5 | Tenant Detail | `/platform/tenants/:id` | `saas-tenant-detail.ts` | ❌ Create |
| 6 | Billing Dashboard | `/platform/billing` | `saas-billing.ts` | ❌ Create |
| 7 | Subscription Tiers | `/platform/subscriptions` | `saas-subscriptions.ts` | ❌ Create |
| 8 | Platform Audit Log | `/platform/audit` | `saas-audit.ts` | ❌ Create |
| 9 | Platform Settings | `/platform/settings` | `saas-platform-settings.ts` | ❌ Create |

---

**Document Status:** CANONICAL — Ready for Implementation  
**Next Document:** `TENANT_ADMIN_UI_SRS.md` (Tenant-level administration)
# Eye of God UIX — Software Requirements Specification (SRS)

## Document Control

| Field | Value |
|-------|-------|
| **Document ID** | SA01-EOG-SRS-2025-12 |
| **Version** | 1.0 |
| **Date** | 2025-12-21 |
| **Status** | CANONICAL |
| **Classification** | ENTERPRISE |
| **Supersedes** | SA01-EOG-REQ-2025-12 (merged) |

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) defines the complete requirements for the **Eye of God (EOG)** unified interface architecture for SomaAgent01. This document serves as the single source of truth for all UI/UX, API, permissions, settings, voice integration, and theming requirements.

### 1.2 Scope

EOG encompasses:
- **UI Layer**: Lit 3.x Web Components with Shadow DOM
- **API Layer**: Django Ninja async REST/WebSocket
- **MVC Layer**: Django 5.x with PostgreSQL
- **Permissions**: SpiceDB (Google Zanzibar model)
- **Theming**: AgentSkin system (REQUIRED)
- **Voice**: Dual-mode (Local Whisper/Kokoro OR AgentVoiceBox)
- **Desktop**: Tauri 2.0 with shared Lit components
- **CLI**: Rust + Ratatui terminal dashboard

### 1.3 Design Principles

1. **Strict Layer Separation** - UI knows NOTHING about Django internals
2. **API-First** - All communication via Django Ninja REST/WebSocket
3. **Permission-First** - Every action checked via SpiceDB before execution
4. **Scale-First** - Architecture supports 1M+ concurrent users
5. **Offline-First** - Service Worker caching, optimistic updates
6. **Voice-Agnostic** - User chooses Local or AgentVoiceBox provider

---

## 2. Glossary

| Term | Definition |
|------|------------|
| **Agent_Mode** | Operational state determining available features (STD/TRN/ADM/DEV/RO/DGR) |
| **AgentSkin** | Theme system using CSS Custom Properties (26+ variables) |
| **AgentVoiceBox** | External voice service (OpenAI-compatible API, Kokoro TTS, Faster-Whisper STT) |
| **Django_Ninja** | Fast async API framework for Django with OpenAPI 3.1 |
| **Kokoro** | Local TTS engine (82M-200M ONNX models) |
| **Lit** | Google's Web Components library with reactive properties |
| **Local_Voice** | On-device STT/TTS using Whisper + Kokoro |
| **Module** | Self-contained Lit Web Component with defined permissions |
| **Permission** | Authorization to perform a specific action on a resource |
| **Persona** | Agent personality/behavior configuration within a tenant |
| **Profile** | Custom role configuration created by system administrators |
| **Role** | Named collection of permissions assignable to users |
| **Shadow_DOM** | Encapsulated DOM tree for component isolation |
| **Skin** | Visual theme configuration (CSS variables, metadata) |
| **SpiceDB** | Google Zanzibar-based permission system for scale |
| **Tauri** | Rust-based desktop application framework |
| **Tenant** | Isolated organizational unit with separate data and config |
| **Whisper** | Local STT engine (OpenAI Whisper, various model sizes) |

---

## 3. Agent Modes

### 3.1 Mode Definitions

| Mode | Code | Description | Use Case |
|------|------|-------------|----------|
| **STANDARD** | `STD` | Normal operation with user-level access | Regular users |
| **TRAINING** | `TRN` | Learning mode with cognitive parameter access | Model fine-tuning |
| **ADMIN** | `ADM` | Full system control and configuration | System administrators |
| **DEVELOPER** | `DEV` | Module SDK access and debugging tools | UI/Module developers |
| **READONLY** | `RO` | View-only access for auditing | Auditors, observers |
| **DEGRADED** | `DGR` | Limited functionality during service issues | Automatic failover |

### 3.2 Mode Transition Rules

- Users can only transition to modes they have permission for
- DEGRADED mode is system-triggered (no user action required)
- Mode changes emit `mode.changed` WebSocket event
- All mode transitions are logged to audit trail

---

## 4. Complete Permission Matrix

### 4.1 Role Hierarchy (SpiceDB Schema)

```
SYSADMIN (Platform Owner)
    └── ADMIN (Tenant Administrator)
            ├── DEVELOPER (Module/UI Developer)
            ├── TRAINER (Cognitive Parameter Access)
            └── USER (Standard Operations)
                    └── VIEWER (Read-Only Access)
```

### 4.2 Feature Permissions by Mode

| Feature | STD | TRN | ADM | DEV | RO | SYSADMIN |
|---------|-----|-----|-----|-----|-----|----------|
| Chat/Conversation | ✅ | ✅ | ✅ | ✅ | 👁️ | ✅ |
| Memory Read | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Memory Write | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Memory Delete | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| Memory Export | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| Tool Execution | ✅ | ⚠️ | ✅ | ✅ | ❌ | ✅ |
| Browser Agent | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| Code Execution | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| Settings View | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Settings Edit | ❌ | ⚠️ | ✅ | ⚠️ | ❌ | ✅ |
| API Keys View | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| API Keys Edit | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| Voice Settings | ✅ | ✅ | ✅ | ✅ | 👁️ | ✅ |
| Theme Apply | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Theme Upload | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |

Legend: ✅ Full Access | ⚠️ Limited | 👁️ View Only | ❌ No Access

### 4.3 Cognitive Parameters by Mode

| Parameter | STD | TRN | ADM | DEV | RO | SYSADMIN |
|-----------|-----|-----|-----|-----|-----|----------|
| Neuromodulators View | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Neuromodulators Edit | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Adaptation Weights | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Learning Rate | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Sleep Cycle Trigger | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |

### 4.4 Settings Sections by Mode

| Settings Section | STD | TRN | ADM | DEV | RO | SYSADMIN |
|------------------|-----|-----|-----|-----|-----|----------|
| Agent Tab - Models | 👁️ | 👁️ | ✅ | 👁️ | 👁️ | ✅ |
| Agent Tab - Memory | 👁️ | ✅ | ✅ | 👁️ | 👁️ | ✅ |
| External Tab - API Keys | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| External Tab - MCP | 👁️ | 👁️ | ✅ | ✅ | 👁️ | ✅ |
| Connectivity Tab - Proxy | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| Connectivity Tab - Voice | ✅ | ✅ | ✅ | ✅ | 👁️ | ✅ |
| System Tab - Auth | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| System Tab - Backup | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| System Tab - Features | 👁️ | 👁️ | ✅ | 👁️ | 👁️ | ✅ |

### 4.5 Tool Permissions by Mode

| Tool Category | STD | TRN | ADM | DEV | RO | SYSADMIN |
|---------------|-----|-----|-----|-----|-----|----------|
| code_execution | ✅ | ⚠️ | ✅ | ✅ | ❌ | ✅ |
| browser_agent | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| memory_save | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| memory_load | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| memory_delete | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| search_engine | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| voice_input | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| voice_output | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| scheduler | ✅ | ❌ | ✅ | ✅ | 👁️ | ✅ |

---

## 5. Complete Settings Architecture

### 5.1 Settings Tab Structure

```
Settings
├── Agent Tab
│   ├── Chat Model (provider, model, context_length, RPM, TPM, vision)
│   ├── Utility Model (provider, model, context_length, RPM, TPM)
│   ├── Browser Model (provider, model, headers, rate_limit)
│   ├── Embedding Model (provider, model, dimensions)
│   └── Memory/SomaBrain (recall_enabled, interval, max_memories, threshold)
│
├── External Tab
│   ├── API Keys (OpenAI, Anthropic, Google, Groq, Mistral)
│   ├── MCP Client (servers JSON, init_timeout, tool_timeout)
│   ├── MCP Server (enabled, endpoint, token)
│   ├── A2A Server (enabled, endpoint, token)
│   └── Tunnel (enabled, URL, auth_token)
│
├── Connectivity Tab
│   ├── Proxy (HTTP/HTTPS proxy configuration)
│   ├── SSE (retry_interval, request_timeout)
│   ├── Voice/Speech (provider, language, voice, VAD_threshold) ← NEW
│   └── Health (poll_interval, degradation_threshold, alerts)
│
└── System Tab
    ├── Authentication (username, password, root_password)
    ├── Backup/Restore (auto_backup, location, restore_file)
    ├── Developer (shell_interface, RFC_host, RFC_port, debug_mode)
    ├── Feature Flags (profile selector + individual toggles)
    ├── Secrets (opaque JSON blob → Vault)
    └── Agent Config (profile, knowledge_dirs, memory_subdir)
```

### 5.2 Voice/Speech Settings (NEW - REQUIRED)

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `voice_provider` | select | `local` | Voice provider: `local` or `agentvoicebox` |
| `voice_enabled` | toggle | `false` | Master switch for voice subsystem |
| `stt_engine` | select | `whisper` | STT engine: `whisper`, `faster-whisper` |
| `stt_model_size` | select | `base` | Whisper model: `tiny`, `base`, `small`, `medium`, `large` |
| `tts_engine` | select | `kokoro` | TTS engine: `kokoro`, `browser`, `openai` |
| `tts_voice` | select | `am_onyx` | Kokoro voice ID |
| `tts_speed` | slider | `1.0` | TTS speed multiplier (0.5-2.0) |
| `vad_threshold` | slider | `0.5` | Voice Activity Detection threshold |
| `language` | select | `en-US` | Speech language code |
| `agentvoicebox_url` | text | `` | AgentVoiceBox server URL (if provider=agentvoicebox) |
| `agentvoicebox_token` | password | `` | AgentVoiceBox API token |
| `audio_input_device` | select | `0` | Microphone device index |
| `audio_output_device` | select | `0` | Speaker device index |
| `audio_sample_rate` | select | `24000` | Audio sample rate (Hz) |

### 5.3 Feature Flags (Complete List)

| Flag | Default | Description |
|------|---------|-------------|
| `sse_enabled` | `true` | Server-Sent Events for streaming |
| `embeddings_ingest` | `true` | Embedding ingestion pipeline |
| `semantic_recall` | `true` | Semantic memory recall |
| `content_masking` | `true` | Sensitive content masking |
| `audio_support` | `false` | Voice/audio subsystem |
| `browser_support` | `true` | Browser agent capability |
| `code_exec` | `true` | Code execution tool |
| `vision_support` | `true` | Vision/image analysis |
| `mcp_client` | `true` | MCP client connections |
| `mcp_server` | `false` | MCP server mode |
| `learning_context` | `true` | Learning context tracking |
| `tool_sandboxing` | `true` | Tool execution sandboxing |
| `streaming_responses` | `true` | Streaming LLM responses |
| `delegation` | `true` | Agent delegation/subordinates |
| `voice_local` | `true` | Local voice (Whisper/Kokoro) |
| `voice_agentvoicebox` | `false` | AgentVoiceBox integration |

### 5.4 Feature Profiles

| Profile | Description | Enabled Flags |
|---------|-------------|---------------|
| `minimal` | Bare minimum | sse, semantic_recall |
| `standard` | Default experience | minimal + browser, code_exec, vision |
| `enhanced` | Full features | standard + audio, mcp_client, delegation |
| `max` | Everything enabled | All flags enabled |

---

## 6. AgentSkin Theme System (REQUIRED)

### 6.1 Theme JSON Schema

```json
{
  "$schema": "https://somaagent.io/schemas/agentskin-v1.json",
  "name": "Theme Name",
  "version": "1.0.0",
  "author": "Author Name",
  "description": "Theme description",
  "category": "Professional|Creative|Developer|Gaming|Accessibility",
  "tags": ["dark", "minimal", "high-contrast"],
  "variables": {
    "bg-void": "#0f172a",
    "glass-surface": "rgba(30, 41, 59, 0.85)",
    "glass-border": "rgba(255, 255, 255, 0.05)",
    "text-main": "#e2e8f0",
    "text-dim": "#64748b",
    "accent-primary": "#3b82f6",
    "accent-secondary": "#8b5cf6",
    "accent-success": "#22c55e",
    "accent-warning": "#f59e0b",
    "accent-danger": "#ef4444",
    "shadow-soft": "0 10px 40px -10px rgba(0, 0, 0, 0.5)",
    "radius-sm": "4px",
    "radius-md": "8px",
    "radius-lg": "16px",
    "radius-full": "9999px",
    "spacing-xs": "4px",
    "spacing-sm": "8px",
    "spacing-md": "16px",
    "spacing-lg": "24px",
    "spacing-xl": "32px",
    "font-sans": "'Space Grotesk', sans-serif",
    "font-mono": "'JetBrains Mono', monospace",
    "text-xs": "10px",
    "text-sm": "12px",
    "text-base": "14px",
    "text-lg": "16px",
    "text-xl": "20px"
  }
}
```

### 6.2 Required CSS Custom Properties (26 minimum)

| Property | Purpose | Example |
|----------|---------|---------|
| `--eog-bg-void` | Background color | `#0f172a` |
| `--eog-glass-surface` | Glass panel background | `rgba(30, 41, 59, 0.85)` |
| `--eog-glass-border` | Glass panel border | `rgba(255, 255, 255, 0.05)` |
| `--eog-text-main` | Primary text color | `#e2e8f0` |
| `--eog-text-dim` | Secondary text color | `#64748b` |
| `--eog-accent-primary` | Primary accent | `#3b82f6` |
| `--eog-accent-secondary` | Secondary accent | `#8b5cf6` |
| `--eog-accent-success` | Success state | `#22c55e` |
| `--eog-accent-warning` | Warning state | `#f59e0b` |
| `--eog-accent-danger` | Danger/error state | `#ef4444` |
| `--eog-shadow-soft` | Soft shadow | `0 10px 40px...` |
| `--eog-radius-sm` | Small border radius | `4px` |
| `--eog-radius-md` | Medium border radius | `8px` |
| `--eog-radius-lg` | Large border radius | `16px` |
| `--eog-radius-full` | Full/pill radius | `9999px` |
| `--eog-spacing-xs` | Extra small spacing | `4px` |
| `--eog-spacing-sm` | Small spacing | `8px` |
| `--eog-spacing-md` | Medium spacing | `16px` |
| `--eog-spacing-lg` | Large spacing | `24px` |
| `--eog-spacing-xl` | Extra large spacing | `32px` |
| `--eog-font-sans` | Sans-serif font | `'Space Grotesk'` |
| `--eog-font-mono` | Monospace font | `'JetBrains Mono'` |
| `--eog-text-xs` | Extra small text | `10px` |
| `--eog-text-sm` | Small text | `12px` |
| `--eog-text-base` | Base text | `14px` |
| `--eog-text-lg` | Large text | `16px` |

### 6.3 Default Themes (REQUIRED)

1. **Default Light** - Clean, professional light theme
2. **Midnight Dark** - Dark theme with blue accents (current glassmorphism)
3. **High Contrast** - WCAG AAA compliant accessibility theme

### 6.4 Theme Security Rules

- NO `url()` in CSS values (XSS prevention)
- HTTPS-only for remote theme loading
- JSON Schema validation required
- WCAG AA contrast ratio validation (4.5:1 minimum)
- Rate limiting: 10 uploads/hour/user

---

## 7. Voice/Speech Integration Architecture

### 7.1 Dual-Mode Voice System

The agent supports TWO voice providers, selectable via Settings:

```
┌─────────────────────────────────────────────────────────────────┐
│                    VOICE PROVIDER SELECTION                      │
│                                                                  │
│   ┌─────────────────────┐    ┌─────────────────────────────┐   │
│   │   LOCAL VOICE       │    │   AGENTVOICEBOX             │   │
│   │   (On-Device)       │    │   (External Service)        │   │
│   ├─────────────────────┤    ├─────────────────────────────┤   │
│   │ STT: Whisper        │    │ STT: Faster-Whisper         │   │
│   │ TTS: Kokoro         │    │ TTS: Kokoro/phoonnx         │   │
│   │ VAD: WebRTC         │    │ VAD: WebRTC + Silero        │   │
│   │ Latency: ~300ms     │    │ Latency: ~150ms             │   │
│   │ Privacy: Full       │    │ Privacy: Network            │   │
│   │ Cost: $0            │    │ Cost: $0 (self-hosted)      │   │
│   └─────────────────────┘    └─────────────────────────────┘   │
│                                                                  │
│   User selects via: Settings → Connectivity → Voice/Speech      │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Local Voice Architecture (Whisper + Kokoro)

```
┌─────────────────────────────────────────────────────────────────┐
│                    LOCAL VOICE PIPELINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Microphone → AudioCapture → VAD → Whisper STT → Text          │
│                                                                  │
│   Text → Agent Processing → Response Text                        │
│                                                                  │
│   Response Text → Kokoro TTS → Audio → Speaker                  │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  Components:                                                     │
│  - AudioCapture (src/voice/audio_capture.py)                    │
│  - VoiceAdapter (src/voice/voice_adapter.py)                    │
│  - LocalClient (src/voice/local_client.py)                      │
│  - Speaker (src/voice/speaker.py)                               │
│  - Whisper (python/helpers/whisper.py)                          │
│  - Kokoro (python/helpers/kokoro_tts.py)                        │
└─────────────────────────────────────────────────────────────────┘
```

### 7.3 AgentVoiceBox Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 AGENTVOICEBOX INTEGRATION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   SomaAgent01                    AgentVoiceBox Server            │
│   ┌──────────────┐              ┌──────────────────────┐        │
│   │ VoiceAdapter │──WebSocket──▶│ /v1/realtime         │        │
│   │              │◀─────────────│ (OpenAI-compatible)  │        │
│   └──────────────┘              └──────────────────────┘        │
│                                          │                       │
│                                          ▼                       │
│                                 ┌──────────────────────┐        │
│                                 │ Speech Pipeline      │        │
│                                 │ - Faster-Whisper STT │        │
│                                 │ - Kokoro/phoonnx TTS │        │
│                                 │ - Dual VAD           │        │
│                                 │ - Noise Reduction    │        │
│                                 └──────────────────────┘        │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  AgentVoiceBox Endpoints:                                        │
│  - WS /v1/realtime (bidirectional audio streaming)              │
│  - POST /v1/audio/speech (TTS)                                  │
│  - POST /v1/audio/transcriptions (STT)                          │
│  - GET /v1/models (available models)                            │
│  - GET /health (health check)                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 7.4 Voice Configuration Models

```python
# Local Voice Config
class LocalVoiceConfig:
    stt_engine: str = "whisper"           # whisper, faster-whisper
    stt_model_size: str = "base"          # tiny, base, small, medium, large
    tts_engine: str = "kokoro"            # kokoro, browser
    tts_voice: str = "am_onyx"            # Kokoro voice ID
    tts_speed: float = 1.0                # 0.5-2.0
    vad_threshold: float = 0.5            # 0.0-1.0
    language: str = "en-US"

# AgentVoiceBox Config
class AgentVoiceBoxConfig:
    base_url: str = ""                    # http://localhost:60200
    ws_url: str = ""                      # ws://localhost:60200/v1/realtime
    api_token: str = ""                   # Bearer token
    model: str = "ovos-voice-1"           # Model name
    voice: str = "default"                # Voice ID
    turn_detection: bool = True           # Server-side VAD
    input_audio_format: str = "pcm16"     # Audio format
    output_audio_format: str = "pcm16"

# Master Voice Config
class VoiceConfig:
    enabled: bool = False                 # Master switch
    provider: str = "local"               # local, agentvoicebox
    local: LocalVoiceConfig
    agentvoicebox: AgentVoiceBoxConfig
    audio_input_device: int = 0
    audio_output_device: int = 0
    sample_rate: int = 24000
```

### 7.5 Voice Provider Selection Logic

```python
def get_voice_provider(config: VoiceConfig):
    if not config.enabled:
        raise VoiceDisabledError("Voice subsystem is disabled")
    
    if config.provider == "local":
        return LocalVoiceProvider(config.local)
    elif config.provider == "agentvoicebox":
        return AgentVoiceBoxProvider(config.agentvoicebox)
    else:
        raise ProviderNotSupportedError(config.provider)
```

### 7.6 Voice Events (WebSocket)

| Event | Direction | Description |
|-------|-----------|-------------|
| `voice.started` | Server→Client | Voice session started |
| `voice.speech_started` | Server→Client | User started speaking |
| `voice.speech_stopped` | Server→Client | User stopped speaking |
| `voice.transcription` | Server→Client | STT result |
| `voice.response_started` | Server→Client | Agent started responding |
| `voice.audio_delta` | Server→Client | Audio chunk (base64) |
| `voice.response_done` | Server→Client | Agent finished responding |
| `voice.error` | Server→Client | Voice error occurred |
| `voice.input_audio` | Client→Server | Audio input (base64) |
| `voice.cancel` | Client→Server | Cancel current response |

---

## 8. Functional Requirements

### 8.1 UI Layer Requirements (Lit Web Components)

| ID | Requirement |
|----|-------------|
| REQ-UI-001 | THE UI_Layer SHALL use Lit 3.x Web Components with Shadow DOM encapsulation |
| REQ-UI-002 | WHEN a component renders THEN the UI_Layer SHALL complete rendering within 16ms (60fps) |
| REQ-UI-003 | THE UI_Layer SHALL expose reactive properties via Lit's `@property` decorator |
| REQ-UI-004 | WHEN theme variables change THEN the UI_Layer SHALL update all components within 50ms |
| REQ-UI-005 | THE UI_Layer SHALL lazy-load non-critical components via dynamic imports |
| REQ-UI-006 | WHEN the application loads THEN the UI_Layer SHALL achieve First Contentful Paint < 1.5s |
| REQ-UI-007 | THE UI_Layer SHALL use CSS Custom Properties for all themeable values |
| REQ-UI-008 | WHEN offline THEN the UI_Layer SHALL serve cached assets via Service Worker |

### 8.2 MVC Layer Requirements (Django + Django Ninja)

| ID | Requirement |
|----|-------------|
| REQ-MVC-001 | THE MVC_Layer SHALL use Django 5.x with async ORM support |
| REQ-MVC-002 | THE MVC_Layer SHALL expose all APIs via Django Ninja with OpenAPI 3.1 schema |
| REQ-MVC-003 | WHEN an API request arrives THEN the MVC_Layer SHALL respond within 50ms (p95) |
| REQ-MVC-004 | THE MVC_Layer SHALL use Django's migration system for all schema changes |
| REQ-MVC-005 | WHEN database queries execute THEN the MVC_Layer SHALL use connection pooling (pgbouncer) |
| REQ-MVC-006 | THE MVC_Layer SHALL implement CQRS pattern for read-heavy endpoints |
| REQ-MVC-007 | WHEN WebSocket connections are needed THEN the MVC_Layer SHALL use Django Channels |
| REQ-MVC-008 | THE MVC_Layer SHALL expose Django Admin for superuser operations only |

### 8.3 Permission System Requirements (SpiceDB)

| ID | Requirement |
|----|-------------|
| REQ-PERM-001 | THE Permission_System SHALL deploy SpiceDB as the permission authority |
| REQ-PERM-002 | WHEN a permission check executes THEN the Permission_System SHALL respond within 10ms (p95) |
| REQ-PERM-003 | THE Permission_System SHALL support 1,000,000+ permission checks per second |
| REQ-PERM-004 | WHEN SpiceDB is unavailable THEN the Permission_System SHALL deny all requests (fail-closed) |
| REQ-PERM-005 | THE Permission_System SHALL cache permission decisions in Redis with TTL 60s |
| REQ-PERM-006 | WHEN a role changes THEN the Permission_System SHALL propagate changes within 5 seconds |
| REQ-PERM-007 | THE Permission_System SHALL support hierarchical role inheritance |
| REQ-PERM-008 | THE Permission_System SHALL provide default roles: SysAdmin, Admin, Developer, User, Viewer |
| REQ-PERM-009 | WHEN a user requests an action THEN the Permission_System SHALL verify tenant isolation |

### 8.4 AgentSkin Theme Requirements (REQUIRED)

| ID | Requirement |
|----|-------------|
| REQ-SKIN-001 | THE Theme_System SHALL use CSS Custom Properties for all themeable values (26 variables minimum) |
| REQ-SKIN-002 | WHEN theme is applied THEN the Theme_System SHALL inject variables within 50ms |
| REQ-SKIN-003 | THE Theme_System SHALL support theme JSON format with name, version, author, variables |
| REQ-SKIN-004 | WHEN theme file is dropped THEN the Theme_System SHALL validate against JSON Schema |
| REQ-SKIN-005 | THE Theme_System SHALL persist active theme to localStorage |
| REQ-SKIN-006 | WHEN theme contains `url()` in CSS values THEN the Theme_System SHALL reject (XSS prevention) |
| REQ-SKIN-007 | THE Theme_System SHALL provide default themes: Default Light, Midnight Dark, High Contrast |
| REQ-SKIN-008 | THE Theme_System SHALL support remote theme loading via HTTPS only |
| REQ-SKIN-009 | WHEN theme is previewed THEN the Theme_System SHALL show split-screen comparison |
| REQ-SKIN-010 | THE Theme_System SHALL validate WCAG AA contrast ratios (4.5:1 minimum) |

### 8.5 Voice/Speech Requirements (NEW)

| ID | Requirement |
|----|-------------|
| REQ-VOICE-001 | THE Voice_System SHALL support dual providers: Local (Whisper/Kokoro) and AgentVoiceBox |
| REQ-VOICE-002 | WHEN voice_provider is "local" THEN the Voice_System SHALL use on-device Whisper STT |
| REQ-VOICE-003 | WHEN voice_provider is "local" THEN the Voice_System SHALL use on-device Kokoro TTS |
| REQ-VOICE-004 | WHEN voice_provider is "agentvoicebox" THEN the Voice_System SHALL connect via WebSocket |
| REQ-VOICE-005 | THE Voice_System SHALL support model selection for Whisper (tiny/base/small/medium/large) |
| REQ-VOICE-006 | THE Voice_System SHALL support voice selection for Kokoro TTS |
| REQ-VOICE-007 | WHEN voice is enabled THEN the Voice_System SHALL emit voice.* WebSocket events |
| REQ-VOICE-008 | THE Voice_System SHALL support Voice Activity Detection (VAD) with configurable threshold |
| REQ-VOICE-009 | WHEN AgentVoiceBox is selected THEN the Voice_System SHALL validate connection on save |
| REQ-VOICE-010 | THE Voice_System SHALL support audio device selection (input/output) |
| REQ-VOICE-011 | THE Voice_System SHALL support sample rate configuration (8kHz-48kHz) |
| REQ-VOICE-012 | WHEN voice error occurs THEN the Voice_System SHALL emit voice.error event with details |

### 8.6 Settings Management Requirements

| ID | Requirement |
|----|-------------|
| REQ-SET-001 | THE Settings_Manager SHALL organize settings into tabs: Agent, External, Connectivity, System |
| REQ-SET-002 | WHEN settings are modified THEN the Settings_Manager SHALL persist to PostgreSQL immediately |
| REQ-SET-003 | THE Settings_Manager SHALL validate all inputs against JSON Schema before saving |
| REQ-SET-004 | WHEN sensitive fields are displayed THEN the Settings_Manager SHALL mask values with asterisks |
| REQ-SET-005 | THE Settings_Manager SHALL support field types: text, password, select, toggle, slider, number, json, file |
| REQ-SET-006 | WHEN API keys are saved THEN the Settings_Manager SHALL store in Vault (not PostgreSQL) |
| REQ-SET-007 | THE Settings_Manager SHALL emit `settings.changed` event after successful save |
| REQ-SET-008 | WHEN settings change THEN the Settings_Manager SHALL trigger agent config reload |
| REQ-SET-009 | THE Settings_Manager SHALL include Voice/Speech section in Connectivity tab |
| REQ-SET-010 | WHEN voice provider changes THEN the Settings_Manager SHALL show provider-specific fields |

### 8.7 Mode State Management Requirements

| ID | Requirement |
|----|-------------|
| REQ-MODE-001 | THE Mode_Manager SHALL maintain current mode state per session |
| REQ-MODE-002 | WHEN mode changes THEN the Mode_Manager SHALL emit `mode.changed` event via WebSocket |
| REQ-MODE-003 | THE Mode_Manager SHALL persist mode preference per user in PostgreSQL |
| REQ-MODE-004 | WHEN session starts THEN the Mode_Manager SHALL restore last mode if permitted |
| REQ-MODE-005 | WHEN user requests mode change THEN the Mode_Manager SHALL verify permissions via SpiceDB |
| REQ-MODE-006 | IF user lacks permission for target mode THEN the Mode_Manager SHALL reject with HTTP 403 |
| REQ-MODE-007 | WHEN transitioning to DEGRADED mode THEN the Mode_Manager SHALL NOT require user action |
| REQ-MODE-008 | THE Mode_Manager SHALL log all mode transitions to audit trail |

### 8.8 Real-Time Communication Requirements

| ID | Requirement |
|----|-------------|
| REQ-RT-001 | THE Realtime_System SHALL use WebSocket for bidirectional communication |
| REQ-RT-002 | WHEN server event occurs THEN the Realtime_System SHALL deliver to client within 100ms |
| REQ-RT-003 | THE Realtime_System SHALL support SSE fallback when WebSocket unavailable |
| REQ-RT-004 | WHEN connection drops THEN the Realtime_System SHALL reconnect with exponential backoff |
| REQ-RT-005 | THE Realtime_System SHALL send heartbeat every 20 seconds |
| REQ-RT-006 | WHEN client reconnects THEN the Realtime_System SHALL replay missed events |
| REQ-RT-007 | THE Realtime_System SHALL support event types: mode.changed, settings.changed, theme.changed, voice.* |
| REQ-RT-008 | THE Realtime_System SHALL authenticate WebSocket connections via token |

---

## 9. Non-Functional Requirements

### 9.1 Performance Requirements (MILLIONS OF USERS)

| ID | Requirement |
|----|-------------|
| REQ-PERF-001 | THE System SHALL support 1,000,000+ concurrent WebSocket connections |
| REQ-PERF-002 | THE System SHALL achieve First Contentful Paint < 1.5 seconds |
| REQ-PERF-003 | THE System SHALL achieve Time to Interactive < 3 seconds |
| REQ-PERF-004 | WHEN theme switches THEN the System SHALL complete transition < 300ms |
| REQ-PERF-005 | THE API_Layer SHALL achieve response time < 50ms (p95) |
| REQ-PERF-006 | THE Permission_System SHALL achieve check time < 10ms (p95) |
| REQ-PERF-007 | THE System SHALL support 10,000 concurrent WebSocket connections per node |
| REQ-PERF-008 | WHEN under load THEN the System SHALL maintain 99.9% availability |
| REQ-PERF-009 | THE System SHALL achieve Lighthouse score > 90 for all categories |
| REQ-PERF-010 | THE Django_Ninja_API SHALL handle 100,000+ requests/second per node |
| REQ-PERF-011 | THE Lit_UI SHALL render 60fps during all interactions |
| REQ-PERF-012 | THE System SHALL support horizontal scaling via Kubernetes |

### 9.2 Security Requirements

| ID | Requirement |
|----|-------------|
| REQ-SEC-001 | THE API_Security SHALL require Bearer token authentication for all endpoints |
| REQ-SEC-002 | WHEN request lacks valid token THEN the API_Security SHALL return HTTP 401 |
| REQ-SEC-003 | THE API_Security SHALL enforce rate limiting (120 requests/minute default) |
| REQ-SEC-004 | WHEN rate limit exceeded THEN the API_Security SHALL return HTTP 429 with Retry-After |
| REQ-SEC-005 | THE API_Security SHALL validate all inputs against JSON Schema |
| REQ-SEC-006 | WHEN SQL injection attempted THEN the API_Security SHALL reject with HTTP 400 |
| REQ-SEC-007 | THE API_Security SHALL set CSP headers: default-src 'self'; style-src 'self' 'unsafe-inline' |
| REQ-SEC-008 | THE API_Security SHALL log all authentication failures to audit trail |
| REQ-SEC-009 | WHEN XSS payload detected THEN the API_Security SHALL sanitize and reject |
| REQ-SEC-010 | THE System SHALL store all secrets in Vault (not PostgreSQL) |

### 9.3 Multi-Tenancy Requirements

| ID | Requirement |
|----|-------------|
| REQ-MT-001 | THE Multi_Tenancy SHALL isolate all data by tenant_id |
| REQ-MT-002 | WHEN request arrives THEN the Multi_Tenancy SHALL extract tenant from X-Tenant-Id header |
| REQ-MT-003 | THE Multi_Tenancy SHALL enforce tenant isolation in all database queries |
| REQ-MT-004 | WHEN user accesses resource THEN the Multi_Tenancy SHALL verify tenant membership via SpiceDB |
| REQ-MT-005 | THE Multi_Tenancy SHALL support tenant-specific themes and settings |
| REQ-MT-006 | WHEN tenant is created THEN the Multi_Tenancy SHALL provision default roles and settings |
| REQ-MT-007 | THE Multi_Tenancy SHALL support tenant hierarchy (parent/child tenants) |
| REQ-MT-008 | WHEN tenant is deleted THEN the Multi_Tenancy SHALL cascade delete all tenant data |

### 9.4 Accessibility Requirements

| ID | Requirement |
|----|-------------|
| REQ-A11Y-001 | THE Accessibility SHALL comply with WCAG 2.1 AA standards |
| REQ-A11Y-002 | THE Accessibility SHALL support keyboard navigation for all interactive elements |
| REQ-A11Y-003 | WHEN focus changes THEN the Accessibility SHALL show visible focus indicator |
| REQ-A11Y-004 | THE Accessibility SHALL provide ARIA labels for all controls |
| REQ-A11Y-005 | THE Accessibility SHALL support screen readers (NVDA, VoiceOver, JAWS) |
| REQ-A11Y-006 | WHEN color is used for meaning THEN the Accessibility SHALL provide alternative indicator |
| REQ-A11Y-007 | THE Accessibility SHALL support reduced motion preference |
| REQ-A11Y-008 | THE Accessibility SHALL maintain contrast ratio >= 4.5:1 for all text |

### 9.5 Observability Requirements

| ID | Requirement |
|----|-------------|
| REQ-OBS-001 | THE Observability SHALL expose Prometheus metrics on /metrics endpoint |
| REQ-OBS-002 | THE Observability SHALL track: request_count, request_duration, error_rate, active_connections |
| REQ-OBS-003 | WHEN error occurs THEN the Observability SHALL increment error counter with labels |
| REQ-OBS-004 | THE Observability SHALL support OpenTelemetry tracing with trace_id propagation |
| REQ-OBS-005 | THE Observability SHALL log structured JSON to stdout |
| REQ-OBS-006 | WHEN latency exceeds SLO THEN the Observability SHALL emit alert |
| REQ-OBS-007 | THE Observability SHALL track theme_loads_total, permission_checks_total, mode_transitions_total |
| REQ-OBS-008 | THE Observability SHALL provide Grafana dashboard templates |

---

## 10. Voice System Detailed Requirements

### 10.1 Local Voice (STT + TTS Only - NO Speech-on-Speech)

| ID | Requirement |
|----|-------------|
| REQ-LVOICE-001 | THE Local_Voice SHALL provide STT via Whisper (CPU or GPU) |
| REQ-LVOICE-002 | THE Local_Voice SHALL provide TTS via Kokoro (CPU or GPU) |
| REQ-LVOICE-003 | THE Local_Voice SHALL NOT support real-time speech-on-speech |
| REQ-LVOICE-004 | THE Local_Voice SHALL detect hardware (CPU/GPU) and select appropriate model |
| REQ-LVOICE-005 | WHEN GPU is available THEN the Local_Voice SHALL use CUDA-optimized models |
| REQ-LVOICE-006 | WHEN GPU is unavailable THEN the Local_Voice SHALL fallback to CPU models |
| REQ-LVOICE-007 | THE Local_Voice SHALL support Whisper model sizes: tiny, base, small, medium, large |
| REQ-LVOICE-008 | THE Local_Voice SHALL support Kokoro model sizes: 82M, 200M |
| REQ-LVOICE-009 | THE Local_Voice SHALL preload models at startup if enabled |
| REQ-LVOICE-010 | THE Local_Voice SHALL support 15+ languages via Kokoro |

### 10.2 AgentVoiceBox Integration (Full Speech-on-Speech)

| ID | Requirement |
|----|-------------|
| REQ-AVB-001 | THE AgentVoiceBox SHALL provide full real-time speech-on-speech capability |
| REQ-AVB-002 | THE AgentVoiceBox SHALL connect via WebSocket to /v1/realtime endpoint |
| REQ-AVB-003 | THE AgentVoiceBox SHALL support OpenAI Realtime API protocol |
| REQ-AVB-004 | THE AgentVoiceBox SHALL support bidirectional audio streaming |
| REQ-AVB-005 | THE AgentVoiceBox SHALL achieve latency < 150ms end-to-end |
| REQ-AVB-006 | THE AgentVoiceBox SHALL support turn detection and interruption handling |
| REQ-AVB-007 | THE AgentVoiceBox SHALL support dual VAD (WebRTC + Silero) |
| REQ-AVB-008 | THE AgentVoiceBox SHALL support noise reduction and AGC |
| REQ-AVB-009 | WHEN AgentVoiceBox is local THEN the System SHALL connect to localhost |
| REQ-AVB-010 | WHEN AgentVoiceBox is remote THEN the System SHALL connect via configured URL |
| REQ-AVB-011 | THE AgentVoiceBox SHALL support 1000+ concurrent voice sessions per server |

### 10.3 Voice Provider Selection

| ID | Requirement |
|----|-------------|
| REQ-VPROV-001 | THE Settings SHALL allow user to select voice provider: local, agentvoicebox, or disabled |
| REQ-VPROV-002 | WHEN provider is "local" THEN the System SHALL use Local_Voice for STT/TTS |
| REQ-VPROV-003 | WHEN provider is "agentvoicebox" THEN the System SHALL use AgentVoiceBox |
| REQ-VPROV-004 | WHEN provider is "disabled" THEN the System SHALL hide all voice UI elements |
| REQ-VPROV-005 | THE Settings SHALL show provider-specific configuration fields |
| REQ-VPROV-006 | WHEN provider changes THEN the System SHALL validate new configuration |
| REQ-VPROV-007 | THE Settings SHALL provide "Test Connection" for AgentVoiceBox |

---

## 11. Django + Django Ninja Architecture (ALL PROJECTS)

### 11.1 Unified Backend Stack

| ID | Requirement |
|----|-------------|
| REQ-DJ-001 | ALL backend services SHALL use Django 5.x as the MVC framework |
| REQ-DJ-002 | ALL REST APIs SHALL use Django Ninja with OpenAPI 3.1 schema |
| REQ-DJ-003 | ALL WebSocket connections SHALL use Django Channels 4.x |
| REQ-DJ-004 | ALL database operations SHALL use Django ORM with async support |
| REQ-DJ-005 | ALL migrations SHALL use Django's migration system |
| REQ-DJ-006 | THE Django_Admin SHALL be available for superuser operations only |

### 11.2 SomaAgent01 Django Migration

| ID | Requirement |
|----|-------------|
| REQ-SA01-DJ-001 | THE SomaAgent01 Gateway SHALL migrate from FastAPI to Django Ninja |
| REQ-SA01-DJ-002 | THE Migration SHALL be parallel (both run simultaneously during transition) |
| REQ-SA01-DJ-003 | THE Django Ninja API SHALL be available at /api/v2/* |
| REQ-SA01-DJ-004 | THE FastAPI SHALL remain at /v1/* during transition period |
| REQ-SA01-DJ-005 | THE Django Ninja SHALL achieve feature parity with FastAPI |
| REQ-SA01-DJ-006 | THE Migration SHALL complete within 6-month overlap period |

### 11.3 SomaBrain Django Migration

| ID | Requirement |
|----|-------------|
| REQ-SB-DJ-001 | THE SomaBrain API SHALL migrate from FastAPI to Django Ninja |
| REQ-SB-DJ-002 | THE SomaBrain SHALL expose /api/v2/remember endpoint |
| REQ-SB-DJ-003 | THE SomaBrain SHALL expose /api/v2/recall endpoint |
| REQ-SB-DJ-004 | THE SomaBrain SHALL expose /api/v2/neuromodulators endpoint |
| REQ-SB-DJ-005 | THE SomaBrain SHALL expose /api/v2/sleep/* endpoints |
| REQ-SB-DJ-006 | THE SomaBrain SHALL expose /api/v2/context/* endpoints |
| REQ-SB-DJ-007 | THE SomaBrain gRPC service SHALL remain for high-performance memory operations |

### 11.4 Django Ninja API Standards

| ID | Requirement |
|----|-------------|
| REQ-NINJA-001 | ALL endpoints SHALL use Pydantic schemas for request/response validation |
| REQ-NINJA-002 | ALL endpoints SHALL return JSON with consistent error format |
| REQ-NINJA-003 | ALL endpoints SHALL include OpenAPI documentation |
| REQ-NINJA-004 | ALL endpoints SHALL support async/await |
| REQ-NINJA-005 | ALL endpoints SHALL include rate limiting via middleware |
| REQ-NINJA-006 | ALL endpoints SHALL include tenant isolation via middleware |
| REQ-NINJA-007 | ALL endpoints SHALL include permission checks via SpiceDB |
| REQ-NINJA-008 | ALL endpoints SHALL include audit logging |

---

## 12. Infrastructure Requirements

### 12.1 Docker/Kubernetes

| ID | Requirement |
|----|-------------|
| REQ-INFRA-001 | THE System SHALL detect CPU/GPU architecture at build time |
| REQ-INFRA-002 | THE System SHALL build appropriate Docker images for detected architecture |
| REQ-INFRA-003 | THE System SHALL support horizontal scaling via Kubernetes |
| REQ-INFRA-004 | THE System SHALL support rolling deployments with zero downtime |
| REQ-INFRA-005 | THE System SHALL support health checks for all services |
| REQ-INFRA-006 | THE System SHALL support resource limits and requests |

### 12.2 Database

| ID | Requirement |
|----|-------------|
| REQ-DB-001 | THE System SHALL use PostgreSQL 16.x as primary database |
| REQ-DB-002 | THE System SHALL use pgbouncer for connection pooling |
| REQ-DB-003 | THE System SHALL support read replicas for scaling |
| REQ-DB-004 | THE System SHALL use Redis 7.x for caching and sessions |
| REQ-DB-005 | THE System SHALL use Milvus for vector storage (SomaBrain) |

### 12.3 Message Queue

| ID | Requirement |
|----|-------------|
| REQ-MQ-001 | THE System SHALL use Kafka 3.x for event streaming |
| REQ-MQ-002 | THE System SHALL use Celery 5.x for background tasks |
| REQ-MQ-003 | THE System SHALL support event replay for missed events |

---

## 13. Success Criteria

### 13.1 Performance Targets

- [ ] 1,000,000+ concurrent WebSocket connections
- [ ] First Contentful Paint < 1.5s
- [ ] Time to Interactive < 3s
- [ ] API response time < 50ms (p95)
- [ ] Permission check < 10ms (p95)
- [ ] Theme switch < 300ms
- [ ] 99.9% uptime SLA

### 13.2 Security Targets

- [ ] Zero XSS vulnerabilities
- [ ] Zero SQL injection vulnerabilities
- [ ] 100% tenant isolation
- [ ] Fail-closed permission model
- [ ] All secrets in Vault

### 13.3 Quality Targets

- [ ] 80% test coverage
- [ ] Lighthouse score > 90
- [ ] WCAG 2.1 AA compliance
- [ ] Zero critical bugs in production

---

**Document Status:** COMPLETE - Ready for Requirements Conversion

**Next Steps:**
1. Convert SRS to EARS-format requirements.md
2. Create design.md with detailed architecture
3. Create tasks.md with implementation plan
# Eye of God UIX — Implementation Tasks

## Document Control

| Field | Value |
|-------|-------|
| **Document ID** | SA01-EOG-TASKS-2025-12 |
| **Version** | 1.0 |
| **Date** | 2025-12-21 |
| **Status** | CANONICAL |
| **Implements** | SA01-EOG-UI-ARCH-2025-12 |

---

## Task Overview

| Phase | Tasks | Duration | Dependencies |
|-------|-------|----------|--------------|
| Phase 1: Foundation | 1-8 | 2 weeks | None |
| Phase 2: Core Features | 9-16 | 2 weeks | Phase 1 |
| Phase 3: Voice Integration | 17-22 | 2 weeks | Phase 2 |
| Phase 4: Advanced Features | 23-28 | 2 weeks | Phase 3 |
| Phase 5: Optimization | 29-34 | 2 weeks | Phase 4 |

---

## Phase 1: Foundation

### Task 1: Django Project Setup
- [ ] Create Django 5.x project structure at `somaAgent01/ui/backend/`
- [ ] Configure settings for development and production
- [ ] Set up Django Ninja API router
- [ ] Configure ASGI with Django Channels
- [ ] Add PostgreSQL connection with pgbouncer
- [ ] Add Redis connection for caching and channels

**Files:**
- `ui/backend/eog/settings/base.py`
- `ui/backend/eog/settings/development.py`
- `ui/backend/eog/settings/production.py`
- `ui/backend/eog/urls.py`
- `ui/backend/eog/asgi.py`
- `ui/backend/api/router.py`

**Acceptance Criteria:**
- Django server starts on port 8020
- `/api/v2/health` returns 200 OK
- `/api/v2/docs` shows OpenAPI documentation

---

### Task 2: SpiceDB Integration
- [ ] Deploy SpiceDB container in docker-compose
- [ ] Create permission schema (schema.zed)
- [ ] Implement SpiceDB gRPC client
- [ ] Create `@require_permission` decorator
- [ ] Add permission caching with Redis (TTL 60s)
- [ ] Implement fail-closed behavior

**Files:**
- `ui/backend/permissions/schema.zed`
- `ui/backend/permissions/client.py`
- `ui/backend/permissions/decorators.py`
- `docker-compose.yml` (SpiceDB service)

**Acceptance Criteria:**
- Permission checks complete in < 10ms (p95)
- Fail-closed when SpiceDB unavailable
- Cache invalidation on role changes

---

### Task 3: Lit Project Setup
- [ ] Initialize Lit 3.x project with Vite
- [ ] Configure TypeScript with strict mode
- [ ] Set up @vaadin/router for SPA routing
- [ ] Configure @lit/context for state management
- [ ] Add @lit-labs/signals for reactive state
- [ ] Set up Web Test Runner for testing

**Files:**
- `ui/frontend/package.json`
- `ui/frontend/vite.config.ts`
- `ui/frontend/tsconfig.json`
- `ui/frontend/web-test-runner.config.js`
- `ui/frontend/src/index.ts`

**Acceptance Criteria:**
- `bun run dev` starts dev server with HMR
- `bun run build` produces optimized bundle
- `bun run test` runs component tests

---

### Task 4: Base UI Components
- [ ] Create `eog-button` component
- [ ] Create `eog-input` component
- [ ] Create `eog-select` component
- [ ] Create `eog-toggle` component
- [ ] Create `eog-slider` component
- [ ] Create `eog-spinner` component
- [ ] Create `eog-modal` component
- [ ] Create `eog-toast` component

**Files:**
- `ui/frontend/src/components/eog-button.ts`
- `ui/frontend/src/components/eog-input.ts`
- `ui/frontend/src/components/eog-select.ts`
- `ui/frontend/src/components/eog-toggle.ts`
- `ui/frontend/src/components/eog-slider.ts`
- `ui/frontend/src/components/eog-spinner.ts`
- `ui/frontend/src/components/eog-modal.ts`
- `ui/frontend/src/components/eog-toast.ts`
- `ui/frontend/src/components/index.ts`

**Acceptance Criteria:**
- All components use CSS Custom Properties
- All components have Shadow DOM encapsulation
- All components render in < 16ms

---

### Task 5: Auth Store and Service
- [ ] Create AuthStore with Lit signals
- [ ] Implement login/logout methods
- [ ] Implement session restoration from localStorage
- [ ] Create AuthService for API calls
- [ ] Add JWT token management
- [ ] Create auth context provider

**Files:**
- `ui/frontend/src/stores/auth-store.ts`
- `ui/frontend/src/services/auth-service.ts`
- `ui/backend/api/endpoints/auth.py`
- `ui/backend/api/schemas/auth.py`

**Acceptance Criteria:**
- Login persists token to localStorage
- Session restores on page reload
- Logout clears all auth state

---

### Task 6: WebSocket Client
- [ ] Create WebSocketClient class
- [ ] Implement connection with token auth
- [ ] Add reconnection with exponential backoff
- [ ] Implement heartbeat (20s interval)
- [ ] Add event subscription system
- [ ] Handle connection state changes

**Files:**
- `ui/frontend/src/services/websocket-client.ts`
- `ui/backend/realtime/consumers.py`
- `ui/backend/realtime/routing.py`

**Acceptance Criteria:**
- Reconnects automatically on disconnect
- Heartbeat keeps connection alive
- Events dispatch to subscribers

---

### Task 7: API Client
- [ ] Create base ApiClient class
- [ ] Implement request method with retry logic
- [ ] Add timeout handling (30s default)
- [ ] Implement error handling with ApiError
- [ ] Add token injection from AuthStore
- [ ] Create typed service methods

**Files:**
- `ui/frontend/src/services/api-client.ts`

**Acceptance Criteria:**
- Retries failed requests (3 attempts)
- Throws ApiError with status code
- Injects Bearer token automatically

---

### Task 8: App Shell
- [ ] Create `eog-app` root component
- [ ] Create `eog-header` with mode selector
- [ ] Create `eog-sidebar` with navigation
- [ ] Create `eog-main` router outlet
- [ ] Create `eog-toast-container`
- [ ] Set up route configuration

**Files:**
- `ui/frontend/src/views/eog-app.ts`
- `ui/frontend/src/views/eog-header.ts`
- `ui/frontend/src/views/eog-sidebar.ts`
- `ui/frontend/src/views/eog-main.ts`
- `ui/frontend/public/index.html`

**Acceptance Criteria:**
- App shell renders with header, sidebar, main
- Routes navigate without page reload
- Sidebar collapses on mobile

---

## Phase 2: Core Features

### Task 9: Mode Store and Selector
- [ ] Create ModeStore with available modes
- [ ] Implement mode change with permission check
- [ ] Create `eog-mode-selector` component
- [ ] Add mode persistence per user
- [ ] Emit mode.changed WebSocket event
- [ ] Handle DEGRADED mode transition

**Files:**
- `ui/frontend/src/stores/mode-store.ts`
- `ui/frontend/src/components/eog-mode-selector.ts`
- `ui/backend/api/endpoints/modes.py`
- `ui/backend/api/schemas/modes.py`

**Acceptance Criteria:**
- Mode changes require permission
- Mode persists across sessions
- DEGRADED mode triggers automatically

---

### Task 10: Theme Store and AgentSkin
- [ ] Create ThemeStore with theme list
- [ ] Implement theme application via CSS variables
- [ ] Create theme validation (26 variables, no url())
- [ ] Add contrast ratio validation (WCAG AA)
- [ ] Create `eog-theme-card` component
- [ ] Implement theme preview mode

**Files:**
- `ui/frontend/src/stores/theme-store.ts`
- `ui/frontend/src/utils/theme-loader.ts`
- `ui/frontend/src/styles/agentskin-bridge.css`
- `ui/frontend/src/styles/themes/default-light.json`
- `ui/frontend/src/styles/themes/midnight-dark.json`
- `ui/frontend/src/styles/themes/high-contrast.json`

**Acceptance Criteria:**
- Theme applies in < 50ms
- Invalid themes rejected with errors
- Preview shows split-screen comparison

---

### Task 11: Settings Views
- [ ] Create `eog-settings-view` with tabs
- [ ] Create `eog-settings-agent` tab
- [ ] Create `eog-settings-external` tab
- [ ] Create `eog-settings-connectivity` tab
- [ ] Create `eog-settings-system` tab
- [ ] Implement settings persistence

**Files:**
- `ui/frontend/src/views/eog-settings-view.ts`
- `ui/frontend/src/views/eog-settings-agent.ts`
- `ui/frontend/src/views/eog-settings-external.ts`
- `ui/frontend/src/views/eog-settings-connectivity.ts`
- `ui/frontend/src/views/eog-settings-system.ts`
- `ui/backend/api/endpoints/settings.py`
- `ui/backend/api/schemas/settings.py`

**Acceptance Criteria:**
- Settings save immediately on change
- Sensitive fields masked with asterisks
- API keys stored in Vault (not PostgreSQL)

---

### Task 12: Permission Store
- [ ] Create PermissionStore with cache
- [ ] Implement permission check method
- [ ] Add cache invalidation on role change
- [ ] Create `@can` directive for templates
- [ ] Integrate with SpiceDB client
- [ ] Handle permission denied gracefully

**Files:**
- `ui/frontend/src/stores/permission-store.ts`
- `ui/frontend/src/services/permission-service.ts`
- `ui/frontend/src/utils/can-directive.ts`

**Acceptance Criteria:**
- Permission checks cached for 60s
- UI elements hidden when no permission
- Permission denied shows toast message

---

### Task 13: Chat View
- [ ] Create `eog-chat-view` layout
- [ ] Create `eog-conversation-list` sidebar
- [ ] Create `eog-chat-panel` main area
- [ ] Create `eog-message` component
- [ ] Create `eog-chat-input` with voice button
- [ ] Implement streaming response display

**Files:**
- `ui/frontend/src/views/eog-chat-view.ts`
- `ui/frontend/src/components/eog-conversation-list.ts`
- `ui/frontend/src/components/eog-chat-panel.ts`
- `ui/frontend/src/components/eog-message.ts`
- `ui/frontend/src/components/eog-chat-input.ts`
- `ui/frontend/src/stores/chat-store.ts`

**Acceptance Criteria:**
- Messages stream in real-time
- Conversation history persists
- Voice button integrated in input

---

### Task 14: Chat Backend
- [ ] Create chat endpoint `/api/v2/chat`
- [ ] Implement Kafka message publishing
- [ ] Create WebSocket consumer for responses
- [ ] Handle streaming events (delta, final)
- [ ] Add tool execution markers
- [ ] Implement conversation history

**Files:**
- `ui/backend/api/endpoints/chat.py`
- `ui/backend/api/schemas/chat.py`
- `ui/backend/realtime/consumers.py`
- `ui/backend/realtime/events.py`

**Acceptance Criteria:**
- Chat messages published to Kafka
- Responses stream via WebSocket
- Tool execution shows in UI

---

### Task 15: Themes View
- [ ] Create `eog-themes-view` gallery
- [ ] Create `eog-theme-gallery` grid
- [ ] Create `eog-theme-preview` panel
- [ ] Create `eog-theme-upload` dropzone
- [ ] Implement theme download/install
- [ ] Add theme rating system

**Files:**
- `ui/frontend/src/views/eog-themes-view.ts`
- `ui/frontend/src/components/eog-theme-gallery.ts`
- `ui/frontend/src/components/eog-theme-preview.ts`
- `ui/frontend/src/components/eog-theme-upload.ts`
- `ui/backend/api/endpoints/themes.py`
- `ui/backend/api/schemas/themes.py`

**Acceptance Criteria:**
- Themes display in responsive grid
- Upload validates JSON schema
- Rate limiting (10 uploads/hour)

---

### Task 16: Django Models
- [ ] Create Tenant model
- [ ] Create User model with tenant relation
- [ ] Create Settings model (JSON field)
- [ ] Create Theme model
- [ ] Create FeatureFlag model
- [ ] Create AuditLog model
- [ ] Run migrations

**Files:**
- `ui/backend/core/models/tenant.py`
- `ui/backend/core/models/user.py`
- `ui/backend/core/models/settings.py`
- `ui/backend/core/models/theme.py`
- `ui/backend/core/models/feature_flag.py`
- `ui/backend/core/models/audit_log.py`
- `ui/backend/core/migrations/`

**Acceptance Criteria:**
- All models have proper indexes
- Tenant isolation enforced
- Audit log captures all changes

---

## Phase 3: Voice Integration

### Task 17: Voice Store
- [ ] Create VoiceStore with provider state
- [ ] Implement provider selection (local/agentvoicebox)
- [ ] Add voice state machine (idle/listening/processing/speaking)
- [ ] Store voice configuration
- [ ] Handle voice errors
- [ ] Emit voice events to WebSocket

**Files:**
- `ui/frontend/src/stores/voice-store.ts`

**Acceptance Criteria:**
- Provider selection persists
- State transitions are atomic
- Errors surface to UI

---

### Task 18: Local Voice Service
- [ ] Implement microphone capture with Web Audio API
- [ ] Add Voice Activity Detection (WebRTC)
- [ ] Integrate with backend Whisper STT
- [ ] Integrate with backend Kokoro TTS
- [ ] Handle audio playback
- [ ] Implement push-to-talk mode

**Files:**
- `ui/frontend/src/services/voice-service.ts` (local methods)
- `ui/backend/api/endpoints/voice.py`
- `ui/backend/api/schemas/voice.py`

**Acceptance Criteria:**
- STT transcription in < 500ms
- TTS playback smooth
- VAD detects speech accurately

---

### Task 19: AgentVoiceBox Integration
- [ ] Implement WebSocket connection to AgentVoiceBox
- [ ] Handle session.update/session.created events
- [ ] Stream audio via input_audio_buffer.append
- [ ] Handle speech_started/speech_stopped events
- [ ] Process response.audio.delta for playback
- [ ] Implement turn detection handling

**Files:**
- `ui/frontend/src/services/voice-service.ts` (agentvoicebox methods)

**Acceptance Criteria:**
- Full speech-on-speech works
- Latency < 150ms end-to-end
- Interruption handling works

---

### Task 20: Voice Settings UI
- [ ] Create `eog-voice-settings` component
- [ ] Add provider selection cards
- [ ] Add local voice settings (model, voice, speed)
- [ ] Add AgentVoiceBox settings (URL, token)
- [ ] Add audio device selection
- [ ] Implement connection test button

**Files:**
- `ui/frontend/src/views/eog-voice-settings.ts`

**Acceptance Criteria:**
- Provider-specific fields show/hide
- Test connection validates settings
- Settings save immediately

---

### Task 21: Voice Button Component
- [ ] Create `eog-voice-button` component
- [ ] Implement push-to-talk interaction
- [ ] Add visual state indicators (listening/processing/speaking)
- [ ] Add pulse animation for listening
- [ ] Handle disabled state
- [ ] Add tooltip with state description

**Files:**
- `ui/frontend/src/components/eog-voice-button.ts`

**Acceptance Criteria:**
- Button shows current voice state
- Push-to-talk works on desktop/mobile
- Disabled when voice not configured

---

### Task 22: Voice Overlay
- [ ] Create `eog-voice-overlay` floating panel
- [ ] Add audio visualizer (waveform)
- [ ] Show real-time transcript
- [ ] Add voice controls (mute, cancel)
- [ ] Position overlay near voice button
- [ ] Auto-hide when idle

**Files:**
- `ui/frontend/src/components/eog-voice-overlay.ts`
- `ui/frontend/src/components/eog-voice-visualizer.ts`

**Acceptance Criteria:**
- Visualizer shows audio levels
- Transcript updates in real-time
- Overlay dismisses on idle

---

## Phase 4: Advanced Features

### Task 23: Memory View
- [ ] Create `eog-memory-view` layout
- [ ] Create `eog-memory-search` with filters
- [ ] Create `eog-memory-grid` with virtual scrolling
- [ ] Create `eog-memory-card` component
- [ ] Create `eog-memory-detail` panel
- [ ] Implement memory CRUD operations

**Files:**
- `ui/frontend/src/views/eog-memory-view.ts`
- `ui/frontend/src/components/eog-memory-search.ts`
- `ui/frontend/src/components/eog-memory-grid.ts`
- `ui/frontend/src/components/eog-memory-card.ts`
- `ui/frontend/src/components/eog-memory-detail.ts`
- `ui/frontend/src/stores/memory-store.ts`
- `ui/backend/api/endpoints/memory.py`

**Acceptance Criteria:**
- Virtual scrolling handles 10K+ items
- Search filters by type, date, content
- Delete requires ADM permission

---

### Task 24: Cognitive Panel
- [ ] Create `eog-cognitive-view` layout
- [ ] Create `eog-neuromod-panel` with gauges
- [ ] Create `eog-neuromod-gauge` component
- [ ] Create `eog-adaptation-panel` with weights
- [ ] Create `eog-sleep-panel` with controls
- [ ] Integrate with SomaBrain API

**Files:**
- `ui/frontend/src/views/eog-cognitive-view.ts`
- `ui/frontend/src/components/eog-neuromod-panel.ts`
- `ui/frontend/src/components/eog-neuromod-gauge.ts`
- `ui/frontend/src/components/eog-adaptation-panel.ts`
- `ui/frontend/src/components/eog-sleep-panel.ts`
- `ui/frontend/src/stores/cognitive-store.ts`
- `ui/backend/api/endpoints/cognitive.py`

**Acceptance Criteria:**
- Neuromodulator gauges update in real-time
- Editing requires TRN or ADM mode
- Sleep cycle triggers consolidation

---

### Task 25: Admin Dashboard
- [ ] Create `eog-admin-view` layout
- [ ] Create `eog-user-management` panel
- [ ] Create `eog-tenant-management` panel
- [ ] Create `eog-system-health` panel
- [ ] Add user CRUD operations
- [ ] Add tenant provisioning

**Files:**
- `ui/frontend/src/views/eog-admin-view.ts`
- `ui/frontend/src/components/eog-user-management.ts`
- `ui/frontend/src/components/eog-tenant-management.ts`
- `ui/frontend/src/components/eog-system-health.ts`
- `ui/backend/api/endpoints/admin.py`
- `ui/backend/api/schemas/admin.py`

**Acceptance Criteria:**
- Admin view requires ADM mode
- User creation provisions SpiceDB roles
- Health shows all service statuses

---

### Task 26: Audit Log Viewer
- [ ] Create `eog-audit-view` layout
- [ ] Create `eog-audit-filters` panel
- [ ] Create `eog-audit-table` with virtual scrolling
- [ ] Add date range filter
- [ ] Add action type filter
- [ ] Add user filter

**Files:**
- `ui/frontend/src/views/eog-audit-view.ts`
- `ui/frontend/src/components/eog-audit-filters.ts`
- `ui/frontend/src/components/eog-audit-table.ts`
- `ui/backend/api/endpoints/audit.py`

**Acceptance Criteria:**
- Audit log loads in < 1s
- Filters apply without reload
- Export to CSV available

---

### Task 27: Tool Catalog
- [ ] Create `eog-tools-view` layout
- [ ] Create `eog-tool-catalog` grid
- [ ] Create `eog-tool-card` component
- [ ] Create `eog-tool-executor` panel
- [ ] Show tool permissions by mode
- [ ] Implement tool execution

**Files:**
- `ui/frontend/src/views/eog-tools-view.ts`
- `ui/frontend/src/components/eog-tool-catalog.ts`
- `ui/frontend/src/components/eog-tool-card.ts`
- `ui/frontend/src/components/eog-tool-executor.ts`
- `ui/backend/api/endpoints/tools.py`

**Acceptance Criteria:**
- Tools show permission requirements
- Execution requires appropriate mode
- Output streams in real-time

---

### Task 28: Scheduler View
- [ ] Create `eog-scheduler-view` layout
- [ ] Create `eog-task-list` component
- [ ] Create `eog-task-form` for creation
- [ ] Support scheduled, ad-hoc, planned tasks
- [ ] Show task execution history
- [ ] Implement task CRUD

**Files:**
- `ui/frontend/src/views/eog-scheduler-view.ts`
- `ui/frontend/src/components/eog-task-list.ts`
- `ui/frontend/src/components/eog-task-form.ts`
- `ui/backend/api/endpoints/scheduler.py`

**Acceptance Criteria:**
- Cron expression builder works
- Task history shows last 10 runs
- Manual trigger available

---

## Phase 5: Optimization

### Task 29: Service Worker
- [ ] Create service worker for caching
- [ ] Cache static assets (JS, CSS, fonts)
- [ ] Cache theme JSON files
- [ ] Implement cache-first for static
- [ ] Implement network-first for API
- [ ] Add offline fallback page

**Files:**
- `ui/frontend/src/sw.ts`
- `ui/frontend/vite.config.ts` (SW plugin)

**Acceptance Criteria:**
- Static assets served from cache
- App works offline (read-only)
- Cache updates on new version

---

### Task 30: Code Splitting
- [ ] Configure manual chunks in Vite
- [ ] Split vendor libraries
- [ ] Split views by route
- [ ] Split voice module
- [ ] Analyze bundle size
- [ ] Optimize chunk loading

**Files:**
- `ui/frontend/vite.config.ts`

**Acceptance Criteria:**
- Initial bundle < 100KB
- Largest chunk < 50KB
- All views lazy-loaded

---

### Task 31: Virtual Scrolling
- [ ] Create `eog-virtual-list` component
- [ ] Implement viewport calculation
- [ ] Add overscan for smooth scrolling
- [ ] Support variable item heights
- [ ] Apply to memory grid
- [ ] Apply to audit table

**Files:**
- `ui/frontend/src/components/eog-virtual-list.ts`

**Acceptance Criteria:**
- Renders 10K items smoothly
- Memory usage constant
- Scroll position preserved

---

### Task 32: Performance Testing
- [ ] Set up k6 for load testing
- [ ] Test 10K concurrent WebSocket connections
- [ ] Test API response times under load
- [ ] Test permission check latency
- [ ] Test theme switch performance
- [ ] Document performance baselines

**Files:**
- `ui/tests/k6/websocket-load.js`
- `ui/tests/k6/api-load.js`
- `ui/tests/performance-baseline.md`

**Acceptance Criteria:**
- 10K WS connections per node
- API p95 < 50ms under load
- Permission check p95 < 10ms

---

### Task 33: Accessibility Audit
- [ ] Run axe-core automated tests
- [ ] Test keyboard navigation
- [ ] Test screen reader compatibility
- [ ] Verify focus indicators
- [ ] Verify color contrast
- [ ] Fix all WCAG AA violations

**Files:**
- `ui/frontend/src/tests/a11y.test.ts`
- `ui/docs/accessibility-report.md`

**Acceptance Criteria:**
- Zero axe-core violations
- All controls keyboard accessible
- Screen reader announces correctly

---

### Task 34: Security Audit
- [ ] Run OWASP ZAP scan
- [ ] Test XSS prevention in themes
- [ ] Test CSRF protection
- [ ] Test SQL injection prevention
- [ ] Test rate limiting
- [ ] Document security findings

**Files:**
- `ui/docs/security-report.md`

**Acceptance Criteria:**
- Zero high/critical vulnerabilities
- Theme url() blocked
- Rate limiting enforced

---

## Task Status Legend

- [ ] Not started
- [~] In progress
- [x] Complete
- [!] Blocked

---

**Document Status:** COMPLETE

**Total Tasks:** 34
**Estimated Duration:** 10 weeks
# Tenant Admin — Complete UI SRS

**Document ID:** SA01-TENANT-ADMIN-UI-SRS-2025-12  
**Version:** 1.0  
**Date:** 2025-12-22  
**Status:** CANONICAL  
**Classification:** ENTERPRISE  
**Compliance:** ISO/IEC/IEEE 29148:2018

---

## Document Control

| Field | Value |
|-------|-------|
| Persona | Tenant Administrator |
| Role Codes | `sysadmin`, `admin` |
| SpiceDB Permissions | `tenant->manage`, `tenant->administrate`, `tenant->create_agent` |

---

## 1. Persona Definition

### 1.1 Who is the Tenant Admin?

The **Tenant Administrator** manages a single tenant organization. There are TWO levels:

#### Tenant SysAdmin (Owner)
- Full control over the tenant
- Create/delete agents
- Manage all users
- View billing
- Access tenant-wide settings

#### Tenant Admin
- Manage users (except SysAdmins)
- Configure agents
- View audit logs
- Cannot delete agents

### 1.2 NOT Covered by This Document

- Platform-level administration → See `SAAS_SYSADMIN_UI_SRS.md`
- Agent-level user interactions → See `AGENT_USER_UI_SRS.md`

---

## 2. Complete User Journey

### 2.1 User Flow Diagram

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                         TENANT ADMIN COMPLETE JOURNEY                           │
└────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────┐
    │   START     │
    └──────┬──────┘
           │
           ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                          AUTHENTICATION PHASE                            │
    │                                                                          │
    │  ┌────────────────┐     ┌────────────────┐     ┌────────────────┐       │
    │  │   /login       │ ──▶ │ Check Role     │ ──▶ │ Token Stored   │       │
    │  │  (Same login)  │     │ (SpiceDB)      │     │                │       │
    │  └────────────────┘     └────────────────┘     └────────┬───────┘       │
    └─────────────────────────────────────────────────────────┬───────────────┘
                                                              │
                                                              ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                          ROLE DETECTION PHASE                            │
    │                                                                          │
    │  Backend: lookup('user:123', 'tenant:acme', 'administrate')             │
    │                                                                          │
    │      ┌─────────────────────────┐                                        │
    │      │ is_tenant_admin?         │                                        │
    │      └────────────┬────────────┘                                        │
    │                   │                                                      │
    │      YES (sysadmin or admin)                                             │
    │                   ▼                                                      │
    │          ┌────────────────┐                                              │
    │          │  /admin        │ (Tenant Dashboard)                          │
    │          └────────┬───────┘                                              │
    └───────────────────┼──────────────────────────────────────────────────────┘
                        │
                        ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                          TENANT ADMIN PHASE                              │
    │                                                                          │
    │  ┌──────────────────────────────────────────────────────────────────┐   │
    │  │                     SIDEBAR NAVIGATION                            │   │
    │  │                                                                   │   │
    │  │  DASHBOARD                                                        │   │
    │  │  📊 Overview ───────────────────▶ /admin                          │   │
    │  │                                                                   │   │
    │  │  MANAGEMENT                                                       │   │
    │  │  👥 Users ──────────────────────▶ /admin/users                    │   │
    │  │  🤖 Agents ─────────────────────▶ /admin/agents                   │   │
    │  │  🎭 Roles ──────────────────────▶ /admin/roles                    │   │
    │  │                                                                   │   │
    │  │  CONFIGURATION                                                    │   │
    │  │  ⚙️ Tenant Settings ────────────▶ /admin/settings                 │   │
    │  │  🔌 Integrations ───────────────▶ /admin/integrations             │   │
    │  │                                                                   │   │
    │  │  MONITORING                                                       │   │
    │  │  📋 Audit Log ──────────────────▶ /admin/audit                    │   │
    │  │  📈 Usage ──────────────────────▶ /admin/usage                    │   │
    │  │  💳 Billing ────────────────────▶ /admin/billing (SysAdmin only)  │   │
    │  │                                                                   │   │
    │  └──────────────────────────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Screen 1: Tenant Dashboard

### 3.1 Route & Component

| Property | Value |
|----------|-------|
| Route | `/admin` |
| Component | `saas-tenant-dashboard.ts` |
| Permission | `tenant->administrate` |

### 3.2 Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ┌────────────┐ │ Dashboard — Acme Corporation                [John D. ▼]   │
│ │ SomaAgent  │ │────────────────────────────────────────────────────────────│
│ │            │ │                                                            │
│ │ DASHBOARD  │ │ Welcome back, John                                         │
│ │ 📊Overview │◀│ Acme Corporation • Team Plan                               │
│ │            │ │                                                            │
│ │ MANAGEMENT │ │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│ │ 👥Users    │ │ │    5     │ │    12    │ │  2.1M    │ │   45%    │       │
│ │ 🤖Agents   │ │ │ Agents   │ │ Users    │ │ Tokens   │ │ Storage  │       │
│ │ 🎭Roles    │ │ │  /10     │ │  /50     │ │ /10M     │ │ /100GB   │       │
│ │            │ │ └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│ │ CONFIG     │ │                                                            │
│ │ ⚙️Settings │ │ Your Agents                                    [View All →]│
│ │ 🔌Integr.  │ │ ┌────────────────────────────────────────────────────────┐│
│ │            │ │ │ ┌──────────────────┐ ┌──────────────────┐              ││
│ │ MONITORING │ │ │ │ 🤖 Support-AI    │ │ 🤖 Sales-Bot     │              ││
│ │ 📋Audit    │ │ │ │ 🟢 Running       │ │ 🟡 Stopped       │              ││
│ │ 📈Usage    │ │ │ │ GPT-4o • Memory  │ │ Claude-3 • Voice │              ││
│ │ 💳Billing  │ │ │ │ 234 sessions     │ │ 45 sessions      │              ││
│ │            │ │ │ │ [Configure][Stop]│ │ [Configure][Start]│             ││
│ │ ─────────  │ │ │ └──────────────────┘ └──────────────────┘              ││
│ │ [Avatar]   │ │ └────────────────────────────────────────────────────────┘│
│ │ John Doe   │ │                                                            │
│ │ SysAdmin   │ │ Recent Activity                                            │
│ └────────────┘ │ ┌────────────────────────────────────────────────────────┐│
│                │ │ 🟢 Jane invited to team               15 min ago       ││
│                │ │ 🔵 Agent "Sales-Bot" stopped          1 hour ago       ││
│                │ │ 🟢 Bob changed role: User → Developer 2 hours ago      ││
│                │ └────────────────────────────────────────────────────────┘│
└────────────────┴────────────────────────────────────────────────────────────┘
```

---

## 4. Screen 2: User Management

### 4.1 Route & Component

| Property | Value |
|----------|-------|
| Route | `/admin/users` |
| Component | `saas-users.ts` |
| Permission | `tenant->administrate` |

### 4.2 Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │ Users                                       [+ Invite User]   │
│            │─────────────────────────────────────────────────────────────────│
│            │                                                                 │
│            │ Using 12 of 50 user seats (Team plan)                          │
│            │ ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░                             │
│            │                                                                 │
│            │ 🔍 Search users...              [Role ▼] [Status ▼]            │
│            │                                                                 │
│            │ ┌───────────────────────────────────────────────────────────┐ │
│            │ │                                                           │ │
│            │ │  User               Email                Role     Status  │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │  👤 John Doe        john@acme.com        SysAdmin 🟢Active│ │
│            │ │                                                    [···]  │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │  👤 Jane Smith      jane@acme.com        Admin    🟢Active│ │
│            │ │                                                    [···]  │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │  👤 Bob Wilson      bob@acme.com         Developer🟢Active│ │
│            │ │                                                    [···]  │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │  👤 Alice Chen      alice@acme.com       Trainer  🟡Invited│ │
│            │ │                                                    [···]  │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │  👤 Mike Brown      mike@acme.com        User     🟢Active│ │
│            │ │                                                    [···]  │ │
│            │ │                                                           │ │
│            │ └───────────────────────────────────────────────────────────┘ │
│            │                                                                 │
└────────────┴─────────────────────────────────────────────────────────────────┘
```

### 4.3 Invite User Modal

```
┌─────────────────────────────────────────────────────────┐
│  Invite New User                                     ✕  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Email Address *                                        │
│  ┌─────────────────────────────────────────────────┐   │
│  │ newuser@example.com                             │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Role *                                                 │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Developer                                   ▼   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 👨‍💻 DEVELOPER                                    │   │
│  │                                                 │   │
│  │ Can access:                                     │   │
│  │ ✓ DEV mode (debugging, module SDK)              │   │
│  │ ✓ STD mode (chat, memory, tools)                │   │
│  │ ✓ View settings (not edit API keys)             │   │
│  │                                                 │   │
│  │ Cannot access:                                  │   │
│  │ ✗ ADM mode (user management)                    │   │
│  │ ✗ TRN mode (cognitive parameters)               │   │
│  │ ✗ Billing or tenant settings                    │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Agent Access                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │ ☑ Support-AI (developer)                        │   │
│  │ ☑ Sales-Bot (developer)                         │   │
│  │ ☐ Internal-Agent (no access)                    │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  [Cancel]                              [Send Invite]    │
└─────────────────────────────────────────────────────────┘
```

### 4.4 Role Hierarchy

| Role | Code | Agent Modes | Can Manage Users | Can Manage Agents |
|------|------|-------------|------------------|-------------------|
| SysAdmin | `sysadmin` | ALL | Yes (all) | Create + Delete |
| Admin | `admin` | STD, ADM | Yes (except SysAdmins) | Configure |
| Developer | `developer` | STD, DEV | No | View config |
| Trainer | `trainer` | STD, TRN | No | View config |
| Member | `member` | STD | No | No |
| Viewer | `viewer` | RO | No | No |

### 4.5 Sequence Diagram - Invite User

```mermaid
sequenceDiagram
    actor Admin as Tenant Admin
    participant UI as saas-users
    participant API as /api/v2/admin/users
    participant SpiceDB
    participant Quota as QuotaService
    participant Email as EmailService
    participant DB as PostgreSQL

    Admin->>UI: Click "+ Invite User"
    UI->>UI: Show modal
    
    Admin->>UI: Fill email, role, agent access
    Admin->>UI: Click "Send Invite"
    
    UI->>API: POST {email, role, agent_ids}
    
    API->>Quota: checkQuota(tenant_id, 'users')
    Quota->>DB: SELECT COUNT(*) FROM users WHERE tenant_id
    
    alt Quota exceeded
        API-->>UI: 402 {error: "User limit reached"}
        UI-->>Admin: Show upgrade modal
    end
    
    API->>DB: Check email not already in tenant
    
    alt Email exists
        API-->>UI: 409 {error: "User already exists"}
    end
    
    API->>DB: INSERT INTO users (email, tenant_id, role, status='invited')
    API->>SpiceDB: write('tenant:' + tenant_id, role, 'user:' + user_id)
    
    loop For each agent_id
        API->>SpiceDB: write('agent:' + agent_id, role, 'user:' + user_id)
    end
    
    API->>Email: SendInvitation(email, tenant_name, inviter_name, token)
    
    API-->>UI: 201 {user: {..., status: 'invited'}}
    UI->>UI: Close modal
    UI->>UI: Add user to list
    UI-->>Admin: Toast "Invitation sent"
```

---

## 5. Screen 3: Agent Management

### 5.1 Route & Component

| Property | Value |
|----------|-------|
| Route | `/admin/agents` |
| Component | `saas-agents.ts` |
| Permission | `tenant->create_agent` |

### 5.2 Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │ Agents                                     [+ Create Agent]   │
│            │─────────────────────────────────────────────────────────────────│
│            │                                                                 │
│            │ Using 5 of 10 agents (Team plan)                               │
│            │ ██████████████████████████░░░░░░░░░░░░░░░░                     │
│            │                                                                 │
│            │ ┌────────────────────────────┐ ┌────────────────────────────┐  │
│            │ │                            │ │                            │  │
│            │ │  🤖 Support-AI             │ │  🤖 Sales-Bot              │  │
│            │ │     [support-ai]           │ │     [sales-bot]            │  │
│            │ │                            │ │                            │  │
│            │ │  Status: 🟢 Running        │ │  Status: 🟡 Stopped        │  │
│            │ │  Model:  GPT-4o            │ │  Model:  Claude-3-Sonnet   │  │
│            │ │                            │ │                            │  │
│            │ │  Features:                 │ │  Features:                 │  │
│            │ │  ✓ Memory (SomaBrain)     │ │  ✓ Memory (SomaBrain)     │  │
│            │ │  ✓ Voice (AgentVoiceBox)  │ │  ✗ Voice                   │  │
│            │ │  ✓ Browser Agent          │ │  ✗ Browser Agent          │  │
│            │ │  ✓ Code Execution         │ │  ✓ Code Execution         │  │
│            │ │                            │ │                            │  │
│            │ │  Sessions: 234 this month  │ │  Sessions: 45 this month   │  │
│            │ │  Tokens:   1.2M used       │ │  Tokens:   340K used       │  │
│            │ │                            │ │                            │  │
│            │ │  ─────────────────────────│ │  ─────────────────────────│  │
│            │ │  [Configure] [Users] [Stop]│ │  [Configure] [Users][Start]│  │
│            │ │                            │ │                            │  │
│            │ └────────────────────────────┘ └────────────────────────────┘  │
│            │                                                                 │
│            │ ┌────────────────────────────┐ ┌────────────────────────────┐  │
│            │ │  🤖 Internal-Agent         │ │  🤖 Research-AI            │  │
│            │ │     [internal-agent]       │ │     [research-ai]          │  │
│            │ │  Status: 🟢 Running        │ │  Status: 🔴 Error          │  │
│            │ │  ...                       │ │  ...                       │  │
│            │ └────────────────────────────┘ └────────────────────────────┘  │
│            │                                                                 │
└────────────┴─────────────────────────────────────────────────────────────────┘
```

### 5.3 Create Agent Modal

```
┌─────────────────────────────────────────────────────────┐
│  Create New Agent                                    ✕  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Agent Name *                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Customer Support AI                             │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Slug (URL identifier) *                                │
│  ┌─────────────────────────────────────────────────┐   │
│  │ customer-support-ai                             │   │
│  └─────────────────────────────────────────────────┘   │
│  URL: acme.somaagent.io/agent/customer-support-ai       │
│                                                         │
│  Primary Chat Model *                                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ GPT-4o (OpenAI)                             ▼   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Features                                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │ ☑ Memory Integration (SomaBrain)                │   │
│  │ ☐ Voice Integration (AgentVoiceBox)             │   │
│  │ ☑ Browser Agent                                 │   │
│  │ ☑ Code Execution                                │   │
│  │ ☐ MCP Server Mode                               │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Agent Owner *                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ john@acme.com (You)                         ▼   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  [Cancel]                              [Create Agent]   │
└─────────────────────────────────────────────────────────┘
```

### 5.4 Sequence Diagram - Create Agent

```mermaid
sequenceDiagram
    actor Admin as Tenant Admin
    participant UI as saas-agents
    participant API as /api/v2/admin/agents
    participant SpiceDB
    participant Quota as QuotaService
    participant DB as PostgreSQL

    Admin->>UI: Click "+ Create Agent"
    UI->>UI: Show modal
    
    Admin->>UI: Fill name, slug, model, features
    Admin->>UI: Click "Create Agent"
    
    UI->>API: POST {name, slug, model, features, owner_id}
    
    API->>Quota: checkQuota(tenant_id, 'agents')
    Quota->>DB: SELECT COUNT(*) FROM agents WHERE tenant_id
    Quota->>DB: SELECT max_agents FROM subscription_tiers JOIN tenants
    
    alt Quota exceeded
        API-->>UI: 402 {error: "Agent limit reached for your plan"}
        UI-->>Admin: Show upgrade modal
    end
    
    API->>DB: Check slug uniqueness within tenant
    
    alt Slug exists
        API-->>UI: 409 {error: "Agent slug already exists"}
    end
    
    API->>DB: INSERT INTO agents (name, slug, tenant_id, owner_id, config)
    API->>SpiceDB: write('agent:' + agent_id, 'owner', 'user:' + owner_id)
    API->>SpiceDB: write('agent:' + agent_id, 'tenant', 'tenant:' + tenant_id)
    
    API-->>UI: 201 {agent: {...}}
    UI->>UI: Close modal
    UI->>UI: Add agent card to grid
    UI-->>Admin: Toast "Agent created successfully"
```

---

## 6. Screen 4: Agent Configuration

### 6.1 Route & Component

| Property | Value |
|----------|-------|
| Route | `/admin/agents/:id` |
| Component | `saas-agent-config.ts` |
| Permission | `agent->configure` |

### 6.2 Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │ ← Back to Agents                                               │
│            │                                                                 │
│            │ Support-AI                                   🟢 Running         │
│            │ support-ai • Created Dec 1, 2024 • Owner: john@acme.com        │
│            │                                                                 │
│            │ [Overview] [Models] [Features] [Users] [Settings] [Logs]       │
│            │─────────────────────────────────────────────────────────────────│
│            │                                                                 │
│            │ Models Tab                                                      │
│            │                                                                 │
│            │ Chat Model *                                                    │
│            │ ┌─────────────────────────────────────────────────────────────┐│
│            │ │ Provider     │ Model           │ Context  │ Vision         ││
│            │ │ OpenAI       │ gpt-4o          │ 128K     │ ✓ Enabled      ││
│            │ └─────────────────────────────────────────────────────────────┘│
│            │ [Change Model]                                                  │
│            │                                                                 │
│            │ Utility Model                                                   │
│            │ ┌─────────────────────────────────────────────────────────────┐│
│            │ │ Provider     │ Model           │ Context  │                 ││
│            │ │ Anthropic    │ claude-3-haiku  │ 200K     │                 ││
│            │ └─────────────────────────────────────────────────────────────┘│
│            │ [Change Model]                                                  │
│            │                                                                 │
│            │ Embedding Model                                                 │
│            │ ┌─────────────────────────────────────────────────────────────┐│
│            │ │ Provider     │ Model           │ Dimensions│                ││
│            │ │ OpenAI       │ text-embed-3-sm │ 1536      │                ││
│            │ └─────────────────────────────────────────────────────────────┘│
│            │ [Change Model]                                                  │
│            │                                                                 │
└────────────┴─────────────────────────────────────────────────────────────────┘
```

### 6.3 Agent User Management Tab

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │ Support-AI › Users                          [+ Add User]      │
│            │─────────────────────────────────────────────────────────────────│
│            │                                                                 │
│            │ Agent-Level Access                                              │
│            │ Users with specific permissions for this agent only            │
│            │                                                                 │
│            │ ┌───────────────────────────────────────────────────────────┐ │
│            │ │                                                           │ │
│            │ │  User               Agent Role        Modes    Actions    │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │  👑 John Doe        Owner             ALL      [Remove]   │ │
│            │ │  ⚙️ Jane Smith      Admin             ADM,STD  [Remove]   │ │
│            │ │  👨‍💻 Bob Wilson      Developer         DEV,STD  [Remove]   │ │
│            │ │  🎓 Alice Chen      Trainer           TRN,STD  [Remove]   │ │
│            │ │  👤 Mike Brown      User              STD      [Remove]   │ │
│            │ │  👁️ Lisa Park       Viewer            RO       [Remove]   │ │
│            │ │                                                           │ │
│            │ └───────────────────────────────────────────────────────────┘ │
│            │                                                                 │
│            │ Agent Mode Legend:                                              │
│            │ ADM = Admin Mode • DEV = Developer Mode • TRN = Training Mode  │
│            │ STD = Standard Mode • RO = Read-Only Mode                      │
│            │                                                                 │
└────────────┴─────────────────────────────────────────────────────────────────┘
```

---

## 7. Screen 5: Tenant Settings

### 7.1 Route & Component

| Property | Value |
|----------|-------|
| Route | `/admin/settings` |
| Component | `saas-tenant-settings.ts` |
| Permission | `tenant->manage` (SysAdmin only) |

### 7.2 Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │ Tenant Settings                                                │
│            │─────────────────────────────────────────────────────────────────│
│            │                                                                 │
│            │ [General] [Branding] [Security] [API] [Danger Zone]             │
│            │                                                                 │
│            │ General Tab                                                     │
│            │                                                                 │
│            │ Organization Name *                                             │
│            │ ┌─────────────────────────────────────────────────────────────┐│
│            │ │ Acme Corporation                                            ││
│            │ └─────────────────────────────────────────────────────────────┘│
│            │                                                                 │
│            │ Tenant Slug (read-only)                                         │
│            │ ┌─────────────────────────────────────────────────────────────┐│
│            │ │ acme-corp                                      [disabled]   ││
│            │ └─────────────────────────────────────────────────────────────┘│
│            │                                                                 │
│            │ Primary Contact Email *                                         │
│            │ ┌─────────────────────────────────────────────────────────────┐│
│            │ │ admin@acme.com                                              ││
│            │ └─────────────────────────────────────────────────────────────┘│
│            │                                                                 │
│            │ Timezone                                                        │
│            │ ┌─────────────────────────────────────────────────────────────┐│
│            │ │ America/New_York (UTC-5)                                ▼   ││
│            │ └─────────────────────────────────────────────────────────────┘│
│            │                                                                 │
│            │ Default Agent Theme                                             │
│            │ ┌─────────────────────────────────────────────────────────────┐│
│            │ │ Midnight Dark                                           ▼   ││
│            │ └─────────────────────────────────────────────────────────────┘│
│            │                                                                 │
│            │ [Save Changes]                                                  │
│            │                                                                 │
└────────────┴─────────────────────────────────────────────────────────────────┘
```

---

## 8. Screen 6: Tenant Audit Log

### 8.1 Route & Component

| Property | Value |
|----------|-------|
| Route | `/admin/audit` |
| Component | `saas-tenant-audit.ts` |
| Permission | `tenant->administrate` |

### 8.2 Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │ Audit Log — Acme Corporation                    [Export CSV]  │
│            │─────────────────────────────────────────────────────────────────│
│            │                                                                 │
│            │ 🔍 Search...    [Action ▼] [User ▼] [Agent ▼] [Date Range ▼]   │
│            │                                                                 │
│            │ ┌───────────────────────────────────────────────────────────┐ │
│            │ │                                                           │ │
│            │ │  Time             User         Action          Resource   │ │
│            │ │ ─────────────────────────────────────────────────────────│ │
│            │ │  14:32:01        john@acme    user.invite     jane@acme   │ │
│            │ │  14:30:45        john@acme    agent.start     Support-AI  │ │
│            │ │  14:15:22        jane@acme    chat.message    Support-AI  │ │
│            │ │  13:55:10        bob@acme     mode.change     DEV→STD     │ │
│            │ │  12:30:00        john@acme    agent.config    Sales-Bot   │ │
│            │ │  11:00:00        alice@acme   memory.write    Support-AI  │ │
│            │ │                                                           │ │
│            │ └───────────────────────────────────────────────────────────┘ │
│            │                                                                 │
│            │ Showing 1-6 of 342 events            [← 1  2  3 ... 58 →]     │
│            │                                                                 │
└────────────┴─────────────────────────────────────────────────────────────────┘
```

---

## 9. Summary: All Tenant Admin Screens

| # | Screen | Route | Component | Permission |
|---|--------|-------|-----------|------------|
| 1 | Dashboard | `/admin` | `saas-tenant-dashboard.ts` | `tenant->administrate` |
| 2 | Users | `/admin/users` | `saas-users.ts` | `tenant->administrate` |
| 3 | Agents | `/admin/agents` | `saas-agents.ts` | `tenant->create_agent` |
| 4 | Agent Config | `/admin/agents/:id` | `saas-agent-config.ts` | `agent->configure` |
| 5 | Roles | `/admin/roles` | `saas-roles.ts` | `tenant->manage` |
| 6 | Settings | `/admin/settings` | `saas-tenant-settings.ts` | `tenant->manage` |
| 7 | Integrations | `/admin/integrations` | `saas-integrations.ts` | `tenant->administrate` |
| 8 | Audit Log | `/admin/audit` | `saas-tenant-audit.ts` | `tenant->administrate` |
| 9 | Usage | `/admin/usage` | `saas-usage.ts` | `tenant->administrate` |
| 10 | Billing | `/admin/billing` | `saas-tenant-billing.ts` | `tenant->manage` |

---

**Document Status:** CANONICAL — Ready for Implementation  
**Previous Document:** `SAAS_SYSADMIN_UI_SRS.md`  
**Next Document:** `AGENT_USER_UI_SRS.md` (Agent modes: STD, TRN, DEV, ADM, RO)
# Eye of God UIX — Complete UI Layer Architecture

## Document Control

| Field | Value |
|-------|-------|
| **Document ID** | SA01-EOG-UI-ARCH-2025-12 |
| **Version** | 1.0 |
| **Date** | 2025-12-21 |
| **Status** | CANONICAL |
| **Scale Target** | MILLIONS of concurrent users |

---

## 1. Architecture Overview

### 1.1 Technology Stack

| Layer | Technology | Purpose | Scale |
|-------|------------|---------|-------|
| **Components** | Lit 3.x | Web Components, Shadow DOM | Millions |
| **State** | Lit Context + Signals | Reactive state management | Per-session |
| **Routing** | @vaadin/router | Client-side SPA routing | N/A |
| **API Client** | Fetch + WebSocket | Django Ninja communication | Pooled |
| **Build** | Vite 5.x | Fast builds, HMR, tree-shaking | N/A |
| **Testing** | Web Test Runner + Playwright | Component + E2E tests | N/A |
| **Theming** | AgentSkin (CSS Custom Properties) | 26+ design tokens | Runtime |

### 1.2 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BROWSER (Lit 3.x SPA)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        EOG-APP (Root Shell)                          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │   │
│  │  │ EOG-HEADER  │  │ EOG-SIDEBAR │  │ EOG-MAIN    │  │ EOG-TOAST  │  │   │
│  │  │ (Mode/User) │  │ (Navigation)│  │ (Router)    │  │ (Notifs)   │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         VIEWS (Pages)                                │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │ EOG-CHAT │ │EOG-MEMORY│ │EOG-TOOLS │ │EOG-ADMIN │ │EOG-VOICE │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         STORES (State)                               │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │AuthStore │ │ModeStore │ │ThemeStore│ │PermStore │ │VoiceStore│  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
                                   │
                    HTTPS/WSS (Connection Pool)
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DJANGO NINJA API GATEWAY (Port 8020)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  /api/v2/*  (REST)  │  /ws/v2/*  (WebSocket)  │  /openapi.json  (Schema)   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Hierarchy

### 2.1 Complete Component Tree

```
eog-app (Root Shell)
├── eog-providers (Context Providers Wrapper)
│   ├── eog-auth-provider
│   ├── eog-mode-provider
│   ├── eog-theme-provider
│   ├── eog-permission-provider
│   └── eog-voice-provider
│
├── eog-header
│   ├── eog-logo
│   ├── eog-mode-selector
│   ├── eog-search-bar
│   ├── eog-notifications
│   └── eog-user-menu
│       ├── eog-avatar
│       └── eog-dropdown
│
├── eog-sidebar
│   ├── eog-nav-section (Chat)
│   ├── eog-nav-section (Memory)
│   ├── eog-nav-section (Tools)
│   ├── eog-nav-section (Cognitive)
│   ├── eog-nav-section (Settings)
│   └── eog-sidebar-footer
│
├── eog-main (Router Outlet)
│   ├── eog-chat-view
│   │   ├── eog-conversation-list
│   │   ├── eog-chat-panel
│   │   │   ├── eog-message-list
│   │   │   │   └── eog-message (repeated)
│   │   │   ├── eog-chat-input
│   │   │   │   ├── eog-textarea
│   │   │   │   ├── eog-voice-button
│   │   │   │   └── eog-send-button
│   │   │   └── eog-typing-indicator
│   │   └── eog-context-panel
│   │
│   ├── eog-memory-view
│   │   ├── eog-memory-search
│   │   ├── eog-memory-filters
│   │   ├── eog-memory-grid
│   │   │   └── eog-memory-card (repeated)
│   │   └── eog-memory-detail
│   │
│   ├── eog-tools-view
│   │   ├── eog-tool-catalog
│   │   │   └── eog-tool-card (repeated)
│   │   └── eog-tool-executor
│   │
│   ├── eog-cognitive-view
│   │   ├── eog-neuromod-panel
│   │   │   ├── eog-neuromod-gauge (dopamine)
│   │   │   ├── eog-neuromod-gauge (serotonin)
│   │   │   ├── eog-neuromod-gauge (noradrenaline)
│   │   │   └── eog-neuromod-gauge (acetylcholine)
│   │   ├── eog-adaptation-panel
│   │   └── eog-sleep-panel
│   │
│   ├── eog-settings-view
│   │   ├── eog-settings-tabs
│   │   ├── eog-settings-agent
│   │   ├── eog-settings-external
│   │   ├── eog-settings-connectivity
│   │   │   └── eog-voice-settings (NEW)
│   │   └── eog-settings-system
│   │
│   ├── eog-themes-view
│   │   ├── eog-theme-gallery
│   │   │   └── eog-theme-card (repeated)
│   │   ├── eog-theme-preview
│   │   └── eog-theme-upload
│   │
│   ├── eog-admin-view
│   │   ├── eog-user-management
│   │   ├── eog-tenant-management
│   │   └── eog-system-health
│   │
│   └── eog-audit-view
│       ├── eog-audit-filters
│       └── eog-audit-table
│
├── eog-voice-overlay (Floating Voice UI)
│   ├── eog-voice-visualizer
│   ├── eog-voice-transcript
│   └── eog-voice-controls
│
└── eog-toast-container
    └── eog-toast (repeated)
```

---

## 2. Component Catalog

### 2.1 Primitive Components (Design System)

| Component | Tag | Purpose | Props |
|-----------|-----|---------|-------|
| Button | `<eog-button>` | Primary action trigger | `variant`, `disabled`, `loading`, `size` |
| Input | `<eog-input>` | Text input field | `type`, `placeholder`, `value`, `error`, `disabled` |
| Select | `<eog-select>` | Dropdown selection | `options`, `value`, `placeholder`, `disabled` |
| Toggle | `<eog-toggle>` | Boolean switch | `checked`, `disabled`, `label` |
| Slider | `<eog-slider>` | Range input | `min`, `max`, `value`, `step`, `label` |
| Modal | `<eog-modal>` | Dialog overlay | `open`, `title`, `closable`, `size` |
| Toast | `<eog-toast>` | Notification popup | `type`, `message`, `duration`, `dismissable` |
| Card | `<eog-card>` | Content container | `variant`, `padding`, `elevation` |
| Tabs | `<eog-tabs>` | Tab navigation | `tabs`, `active`, `orientation` |
| Spinner | `<eog-spinner>` | Loading indicator | `size`, `color` |
| Badge | `<eog-badge>` | Status indicator | `variant`, `count`, `dot` |
| Avatar | `<eog-avatar>` | User/agent image | `src`, `name`, `size`, `status` |
| Icon | `<eog-icon>` | SVG icon wrapper | `name`, `size`, `color` |
| Tooltip | `<eog-tooltip>` | Hover information | `content`, `position`, `delay` |
| Progress | `<eog-progress>` | Progress bar | `value`, `max`, `variant`, `label` |

### 2.2 Layout Components

| Component | Tag | Purpose | Props |
|-----------|-----|---------|-------|
| App Shell | `<eog-app>` | Root application | `theme`, `mode`, `user` |
| Header | `<eog-header>` | Top navigation bar | `title`, `user`, `mode` |
| Sidebar | `<eog-sidebar>` | Side navigation | `collapsed`, `items`, `active` |
| Main | `<eog-main>` | Content area | `padding`, `scroll` |
| Panel | `<eog-panel>` | Collapsible section | `title`, `collapsed`, `icon` |
| Split | `<eog-split>` | Resizable split view | `direction`, `sizes`, `min` |
| Grid | `<eog-grid>` | CSS Grid wrapper | `columns`, `gap`, `responsive` |
| Stack | `<eog-stack>` | Flex stack layout | `direction`, `gap`, `align` |

### 2.3 View Components (Pages)

| Component | Tag | Route | Permission |
|-----------|-----|-------|------------|
| Chat | `<eog-chat>` | `/chat` | `tenant->use` |
| Memory | `<eog-memory>` | `/memory` | `tenant->view` |
| Tools | `<eog-tools>` | `/tools` | `tenant->view` |
| Settings | `<eog-settings>` | `/settings` | `tenant->view` |
| Themes | `<eog-themes>` | `/themes` | `tenant->view` |
| Voice | `<eog-voice>` | `/voice` | `tenant->use` |
| Cognitive | `<eog-cognitive>` | `/cognitive` | `tenant->train` |
| Admin | `<eog-admin>` | `/admin` | `tenant->administrate` |
| Audit | `<eog-audit>` | `/audit` | `tenant->administrate` |
| Scheduler | `<eog-scheduler>` | `/scheduler` | `tenant->use` |

### 2.2 Component Categories

| Category | Components | Purpose |
|----------|------------|---------|
| **Shell** | eog-app, eog-header, eog-sidebar, eog-main | Application structure |
| **Providers** | eog-*-provider | Context/state injection |
| **Views** | eog-*-view | Page-level containers |
| **Panels** | eog-*-panel | Feature sections |
| **Forms** | eog-input, eog-select, eog-toggle, eog-slider | User input |
| **Display** | eog-card, eog-table, eog-list, eog-badge | Data presentation |
| **Feedback** | eog-toast, eog-modal, eog-spinner, eog-skeleton | User feedback |
| **Voice** | eog-voice-*, eog-visualizer | Voice interaction |

### 2.3 Lazy Loading Strategy

```typescript
// Route-based code splitting
const routes = [
  { path: '/', component: 'eog-chat-view' },
  { path: '/memory', component: 'eog-memory-view', action: () => import('./views/eog-memory-view.js') },
  { path: '/tools', component: 'eog-tools-view', action: () => import('./views/eog-tools-view.js') },
  { path: '/cognitive', component: 'eog-cognitive-view', action: () => import('./views/eog-cognitive-view.js') },
  { path: '/settings', component: 'eog-settings-view', action: () => import('./views/eog-settings-view.js') },
  { path: '/themes', component: 'eog-themes-view', action: () => import('./views/eog-themes-view.js') },
  { path: '/admin', component: 'eog-admin-view', action: () => import('./views/eog-admin-view.js') },
  { path: '/audit', component: 'eog-audit-view', action: () => import('./views/eog-audit-view.js') },
];
```

---

## 3. State Management

### 3.1 Store Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    STORE LAYER (Lit Context)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ AuthStore   │  │ ModeStore   │  │ ThemeStore  │             │
│  │ - user      │  │ - current   │  │ - active    │             │
│  │ - token     │  │ - available │  │ - list      │             │
│  │ - tenant    │  │ - loading   │  │ - preview   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ PermStore   │  │ VoiceStore  │  │ SettingsStore│            │
│  │ - cache     │  │ - provider  │  │ - agent     │             │
│  │ - roles     │  │ - state     │  │ - external  │             │
│  │ - loading   │  │ - config    │  │ - system    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ ChatStore   │  │ MemoryStore │  │ CognitiveStore│           │
│  │ - messages  │  │ - items     │  │ - neuromod  │             │
│  │ - sessions  │  │ - filters   │  │ - adaptation│             │
│  │ - streaming │  │ - selected  │  │ - sleep     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Store Implementations

#### AuthStore

```typescript
// File: src/stores/auth-store.ts
import { createContext } from '@lit/context';
import { signal, computed } from '@lit-labs/signals';

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  roles: string[];
  tenant_id: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  tenant_id: string | null;
  loading: boolean;
  error: string | null;
}

export const authContext = createContext<AuthState>('auth-state');

class AuthStore {
  private _user = signal<User | null>(null);
  private _token = signal<string | null>(null);
  private _loading = signal(false);
  private _error = signal<string | null>(null);

  readonly isAuthenticated = computed(() => this._user.get() !== null);
  readonly tenantId = computed(() => this._user.get()?.tenant_id ?? null);

  get state(): AuthState {
    return {
      user: this._user.get(),
      token: this._token.get(),
      tenant_id: this.tenantId.get(),
      loading: this._loading.get(),
      error: this._error.get(),
    };
  }

  async login(email: string, password: string): Promise<void> {
    this._loading.set(true);
    this._error.set(null);
    try {
      const response = await fetch('/api/v2/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!response.ok) throw new Error('Login failed');
      const data = await response.json();
      this._user.set(data.user);
      this._token.set(data.token);
      localStorage.setItem('eog_token', data.token);
    } catch (e) {
      this._error.set(String(e));
    } finally {
      this._loading.set(false);
    }
  }

  logout(): void {
    this._user.set(null);
    this._token.set(null);
    localStorage.removeItem('eog_token');
  }

  async restoreSession(): Promise<void> {
    const token = localStorage.getItem('eog_token');
    if (!token) return;
    this._loading.set(true);
    try {
      const response = await fetch('/api/v2/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Session expired');
      const data = await response.json();
      this._user.set(data.user);
      this._token.set(token);
    } catch {
      localStorage.removeItem('eog_token');
    } finally {
      this._loading.set(false);
    }
  }
}

export const authStore = new AuthStore();
```

### 2.4 Feature Components

| Component | Tag | Purpose | Props |
|-----------|-----|---------|-------|
| Chat Message | `<eog-chat-message>` | Single message | `role`, `content`, `timestamp`, `status` |
| Chat Input | `<eog-chat-input>` | Message composer | `placeholder`, `disabled`, `voice` |
| Memory Card | `<eog-memory-card>` | Memory item display | `memory`, `actions` |
| Memory Search | `<eog-memory-search>` | Memory query | `query`, `filters` |
| Tool Card | `<eog-tool-card>` | Tool display | `tool`, `status`, `execute` |
| Tool Executor | `<eog-tool-executor>` | Tool execution UI | `tool`, `params`, `result` |
| Settings Form | `<eog-settings-form>` | Settings editor | `schema`, `values`, `tab` |
| Theme Preview | `<eog-theme-preview>` | Theme comparison | `theme`, `split` |
| Theme Editor | `<eog-theme-editor>` | Theme customization | `theme`, `variables` |
| Voice Indicator | `<eog-voice-indicator>` | Voice status | `state`, `level`, `provider` |
| Voice Controls | `<eog-voice-controls>` | Voice buttons | `recording`, `playing`, `muted` |
| Neuro Panel | `<eog-neuro-panel>` | Neuromodulator display | `dopamine`, `serotonin`, `noradrenaline` |
| Adaptation Panel | `<eog-adaptation-panel>` | Adaptation weights | `weights`, `history` |
| User Menu | `<eog-user-menu>` | User dropdown | `user`, `mode`, `logout` |
| Mode Selector | `<eog-mode-selector>` | Mode switcher | `current`, `available` |

---

## 3. State Management

### 3.1 Store Architecture (Lit Context)

```
┌─────────────────────────────────────────────────────────────────┐
│                     STORE HIERARCHY                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    ROOT PROVIDER                         │   │
│  │  <eog-store-provider>                                    │   │
│  │    ├── AuthStore (token, user, tenant)                   │   │
│  │    ├── ModeStore (current, available, loading)           │   │
│  │    ├── ThemeStore (active, themes, preview)              │   │
│  │    ├── PermStore (permissions, cache)                    │   │
│  │    ├── VoiceStore (provider, state, config)              │   │
│  │    ├── SettingsStore (tabs, values, dirty)               │   │
│  │    └── ChatStore (messages, streaming, session)          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Store Definitions

#### AuthStore
```typescript
interface AuthState {
  token: string | null;
  user: User | null;
  tenant: Tenant | null;
  loading: boolean;
  error: string | null;
}

interface AuthActions {
  login(credentials: Credentials): Promise<void>;
  logout(): Promise<void>;
  refresh(): Promise<void>;
  setTenant(tenantId: string): Promise<void>;
}
```

#### ModeStore
```typescript
interface ModeState {
  current: AgentMode;  // 'STD' | 'TRN' | 'ADM' | 'DEV' | 'RO' | 'DGR'
  available: AgentMode[];
  loading: boolean;
  error: string | null;
}

interface ModeActions {
  setMode(mode: AgentMode): Promise<void>;
  refresh(): Promise<void>;
}
```

#### ThemeStore
```typescript
interface ThemeState {
  active: Theme;
  themes: Theme[];
  preview: Theme | null;
  loading: boolean;
}

interface ThemeActions {
  apply(themeId: string): Promise<void>;
  preview(theme: Theme): void;
  upload(file: File): Promise<Theme>;
  reset(): void;
}
```

#### VoiceStore

```typescript
// File: src/stores/voice-store.ts
import { createContext } from '@lit/context';
import { signal, computed } from '@lit-labs/signals';

export type VoiceProvider = 'disabled' | 'local' | 'agentvoicebox';
export type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking' | 'error';

export interface VoiceConfig {
  provider: VoiceProvider;
  local: {
    stt_engine: 'whisper' | 'faster-whisper';
    stt_model_size: 'tiny' | 'base' | 'small' | 'medium' | 'large';
    tts_engine: 'kokoro' | 'browser';
    tts_voice: string;
    tts_speed: number;
    vad_threshold: number;
    language: string;
  };
  agentvoicebox: {
    base_url: string;
    ws_url: string;
    api_token: string;
    model: string;
    voice: string;
    turn_detection: boolean;
  };
  audio: {
    input_device: number;
    output_device: number;
    sample_rate: number;
  };
}

export interface VoiceStoreState {
  enabled: boolean;
  provider: VoiceProvider;
  state: VoiceState;
  config: VoiceConfig;
  transcript: string;
  error: string | null;
}

export const voiceContext = createContext<VoiceStoreState>('voice-state');

class VoiceStore {
  private _enabled = signal(false);
  private _provider = signal<VoiceProvider>('disabled');
  private _state = signal<VoiceState>('idle');
  private _transcript = signal('');
  private _error = signal<string | null>(null);
  private _config = signal<VoiceConfig>(this.defaultConfig());

  readonly isActive = computed(() => 
    this._enabled.get() && this._state.get() !== 'idle' && this._state.get() !== 'error'
  );

  readonly canUseSpeechOnSpeech = computed(() => 
    this._provider.get() === 'agentvoicebox'
  );

  get state(): VoiceStoreState {
    return {
      enabled: this._enabled.get(),
      provider: this._provider.get(),
      state: this._state.get(),
      config: this._config.get(),
      transcript: this._transcript.get(),
      error: this._error.get(),
    };
  }

  private defaultConfig(): VoiceConfig {
    return {
      provider: 'disabled',
      local: {
        stt_engine: 'whisper',
        stt_model_size: 'base',
        tts_engine: 'kokoro',
        tts_voice: 'am_onyx',
        tts_speed: 1.0,
        vad_threshold: 0.5,
        language: 'en-US',
      },
      agentvoicebox: {
        base_url: '',
        ws_url: '',
        api_token: '',
        model: 'ovos-voice-1',
        voice: 'default',
        turn_detection: true,
      },
      audio: {
        input_device: 0,
        output_device: 0,
        sample_rate: 24000,
      },
    };
  }

  setProvider(provider: VoiceProvider): void {
    this._provider.set(provider);
    this._enabled.set(provider !== 'disabled');
  }

  setState(state: VoiceState): void {
    this._state.set(state);
  }

  setTranscript(text: string): void {
    this._transcript.set(text);
  }

  updateConfig(partial: Partial<VoiceConfig>): void {
    this._config.set({ ...this._config.get(), ...partial });
  }

  setError(error: string | null): void {
    this._error.set(error);
    if (error) this._state.set('error');
  }
}

export const voiceStore = new VoiceStore();
```

#### VoiceStore
```typescript
interface VoiceState {
  enabled: boolean;
  provider: 'local' | 'agentvoicebox' | 'disabled';
  state: 'idle' | 'listening' | 'processing' | 'speaking' | 'error';
  config: VoiceConfig;
  audioLevel: number;
  error: string | null;
}

interface VoiceActions {
  setProvider(provider: string): Promise<void>;
  startListening(): Promise<void>;
  stopListening(): void;
  speak(text: string): Promise<void>;
  cancel(): void;
  testConnection(): Promise<boolean>;
}
```

#### PermStore
```typescript
interface PermState {
  permissions: Map<string, boolean>;
  loading: boolean;
  cacheExpiry: number;
}

interface PermActions {
  check(resource: string, action: string): Promise<boolean>;
  refresh(): Promise<void>;
  invalidate(): void;
}
```

---

## 4. Service Layer

### 4.1 API Client Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SERVICE LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    ApiClient (Base)                      │   │
│  │  - baseUrl: /api/v2                                      │   │
│  │  - timeout: 30000ms                                      │   │
│  │  - retries: 3                                            │   │
│  │  - interceptors: [auth, tenant, error]                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                      │
│           ┌───────────────┼───────────────┐                     │
│           ▼               ▼               ▼                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ AuthService │ │SettingsService│ │ VoiceService │             │
│  │ /auth/*     │ │ /settings/* │ │ /voice/*    │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│           │               │               │                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ ThemeService│ │ MemoryService│ │ ToolService │               │
│  │ /themes/*  │ │ /memory/*   │ │ /tools/*    │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│           │               │               │                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ CognitiveService│ │ AdminService│ │ PermService │            │
│  │ /cognitive/*│ │ /admin/*    │ │ /permissions/*│             │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 WebSocket Client

```typescript
interface WSClientConfig {
  url: string;           // /ws/v2/events
  reconnect: boolean;    // true
  maxRetries: number;    // 5
  backoff: number;       // 1000ms (exponential)
  heartbeat: number;     // 20000ms
}

interface WSClient {
  connect(): Promise<void>;
  disconnect(): void;
  send(event: WSEvent): void;
  subscribe(type: string, handler: EventHandler): Unsubscribe;
  onReconnect(handler: () => void): void;
}

// Event Types
type WSEventType = 
  | 'mode.changed'
  | 'settings.changed'
  | 'theme.changed'
  | 'voice.started'
  | 'voice.speech_started'
  | 'voice.speech_stopped'
  | 'voice.transcription'
  | 'voice.response_started'
  | 'voice.audio_delta'
  | 'voice.response_done'
  | 'voice.error'
  | 'chat.message'
  | 'chat.typing'
  | 'chat.done'
  | 'system.keepalive';
```

#### ThemeStore

```typescript
// File: src/stores/theme-store.ts
import { createContext } from '@lit/context';
import { signal } from '@lit-labs/signals';

export interface Theme {
  id: string;
  name: string;
  version: string;
  author: string;
  variables: Record<string, string>;
}

export interface ThemeState {
  active: Theme | null;
  list: Theme[];
  preview: Theme | null;
  loading: boolean;
}

export const themeContext = createContext<ThemeState>('theme-state');

class ThemeStore {
  private _active = signal<Theme | null>(null);
  private _list = signal<Theme[]>([]);
  private _preview = signal<Theme | null>(null);
  private _loading = signal(false);

  get state(): ThemeState {
    return {
      active: this._active.get(),
      list: this._list.get(),
      preview: this._preview.get(),
      loading: this._loading.get(),
    };
  }

  applyTheme(theme: Theme): void {
    const root = document.documentElement;
    Object.entries(theme.variables).forEach(([key, value]) => {
      root.style.setProperty(`--eog-${key}`, value);
    });
    this._active.set(theme);
    localStorage.setItem('eog_theme', theme.id);
  }

  previewTheme(theme: Theme | null): void {
    this._preview.set(theme);
    if (theme) {
      const root = document.documentElement;
      Object.entries(theme.variables).forEach(([key, value]) => {
        root.style.setProperty(`--eog-${key}`, value);
      });
    } else if (this._active.get()) {
      this.applyTheme(this._active.get()!);
    }
  }

  async loadThemes(): Promise<void> {
    this._loading.set(true);
    try {
      const response = await fetch('/api/v2/themes');
      const data = await response.json();
      this._list.set(data.themes);
    } finally {
      this._loading.set(false);
    }
  }

  async restoreTheme(): Promise<void> {
    const themeId = localStorage.getItem('eog_theme');
    if (!themeId) return;
    await this.loadThemes();
    const theme = this._list.get().find(t => t.id === themeId);
    if (theme) this.applyTheme(theme);
  }
}

export const themeStore = new ThemeStore();
```

---

## 4. Service Layer

### 4.1 Service Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    ApiClient (Base)                      │   │
│  │  - request<T>(method, path, options): Promise<T>        │   │
│  │  - setToken(token): void                                │   │
│  │  - retry logic, timeout, error handling                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│         ┌────────────────────┼────────────────────┐             │
│         ▼                    ▼                    ▼             │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐     │
│  │ AuthService │      │ ChatService │      │ MemoryService│    │
│  │ - login()   │      │ - send()    │      │ - recall()  │     │
│  │ - logout()  │      │ - stream()  │      │ - remember()│     │
│  │ - refresh() │      │ - history() │      │ - delete()  │     │
│  └─────────────┘      └─────────────┘      └─────────────┘     │
│                                                                  │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐     │
│  │ ThemeService│      │ SettingsService│   │ VoiceService│     │
│  │ - list()    │      │ - get()     │      │ - connect() │     │
│  │ - upload()  │      │ - update()  │      │ - disconnect()│   │
│  │ - delete()  │      │ - validate()│      │ - send()    │     │
│  └─────────────┘      └─────────────┘      └─────────────┘     │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  WebSocketClient                         │   │
│  │  - connect(url): void                                   │   │
│  │  - disconnect(): void                                   │   │
│  │  - send(event): void                                    │   │
│  │  - on(event, handler): void                             │   │
│  │  - reconnect with exponential backoff                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Routing Configuration

### 5.1 Route Definitions

```typescript
const routes: Route[] = [
  { path: '/', redirect: '/chat' },
  { path: '/chat', component: 'eog-chat', permission: 'tenant->use' },
  { path: '/chat/:sessionId', component: 'eog-chat', permission: 'tenant->use' },
  { path: '/memory', component: 'eog-memory', permission: 'tenant->view' },
  { path: '/memory/:coordinate', component: 'eog-memory', permission: 'tenant->view' },
  { path: '/tools', component: 'eog-tools', permission: 'tenant->view' },
  { path: '/tools/:toolId', component: 'eog-tool-executor', permission: 'tenant->use' },
  { path: '/settings', component: 'eog-settings', permission: 'tenant->view' },
  { path: '/settings/:tab', component: 'eog-settings', permission: 'tenant->view' },
  { path: '/themes', component: 'eog-themes', permission: 'tenant->view' },
  { path: '/themes/:themeId', component: 'eog-theme-editor', permission: 'tenant->administrate' },
  { path: '/voice', component: 'eog-voice', permission: 'tenant->use' },
  { path: '/cognitive', component: 'eog-cognitive', permission: 'tenant->train' },
  { path: '/admin', component: 'eog-admin', permission: 'tenant->administrate' },
  { path: '/admin/users', component: 'eog-admin-users', permission: 'tenant->administrate' },
  { path: '/admin/tenants', component: 'eog-admin-tenants', permission: 'tenant->manage' },
  { path: '/audit', component: 'eog-audit', permission: 'tenant->administrate' },
  { path: '/scheduler', component: 'eog-scheduler', permission: 'tenant->use' },
  { path: '/login', component: 'eog-login', public: true },
  { path: '/logout', component: 'eog-logout', public: true },
  { path: '(.*)', component: 'eog-not-found', public: true },
];
```

### 5.2 Route Guards

```typescript
async function routeGuard(context: RouterContext, commands: Commands): Promise<void> {
  const { route, params } = context;
  
  // Public routes bypass auth
  if (route.public) return;
  
  // Check authentication
  const authStore = getStore('auth');
  if (!authStore.token) {
    return commands.redirect('/login');
  }
  
  // Check permission
  if (route.permission) {
    const permStore = getStore('perm');
    const allowed = await permStore.check(route.permission);
    if (!allowed) {
      return commands.redirect('/unauthorized');
    }
  }
}
```

---

## 6. AgentSkin Theme System

### 6.1 CSS Custom Properties (26 Required)

```css
:root {
  /* Background Colors */
  --eog-bg-void: #0f172a;
  --eog-bg-surface: rgba(30, 41, 59, 0.85);
  --eog-bg-elevated: rgba(51, 65, 85, 0.9);
  
  /* Glass Effects */
  --eog-glass-surface: rgba(30, 41, 59, 0.85);
  --eog-glass-border: rgba(255, 255, 255, 0.05);
  --eog-glass-blur: blur(20px);
  
  /* Text Colors */
  --eog-text-main: #e2e8f0;
  --eog-text-dim: #64748b;
  --eog-text-accent: #3b82f6;
  
  /* Accent Colors */
  --eog-accent-primary: #3b82f6;
  --eog-accent-secondary: #8b5cf6;
  --eog-accent-success: #22c55e;
  --eog-accent-warning: #f59e0b;
  --eog-accent-danger: #ef4444;
  
  /* Shadows */
  --eog-shadow-soft: 0 10px 40px -10px rgba(0, 0, 0, 0.5);
  --eog-shadow-glow: 0 0 20px rgba(59, 130, 246, 0.3);
  
  /* Border Radius */
  --eog-radius-sm: 4px;
  --eog-radius-md: 8px;
  --eog-radius-lg: 16px;
  --eog-radius-full: 9999px;
  
  /* Spacing */
  --eog-spacing-xs: 4px;
  --eog-spacing-sm: 8px;
  --eog-spacing-md: 16px;
  --eog-spacing-lg: 24px;
  --eog-spacing-xl: 32px;
  
  /* Typography */
  --eog-font-sans: 'Space Grotesk', system-ui, sans-serif;
  --eog-font-mono: 'JetBrains Mono', monospace;
  --eog-text-xs: 10px;
  --eog-text-sm: 12px;
  --eog-text-base: 14px;
  --eog-text-lg: 16px;
  --eog-text-xl: 20px;
}
```

### 4.2 WebSocket Client Implementation

```typescript
// File: src/services/websocket-client.ts

export type WSEventType = 
  | 'mode.changed'
  | 'settings.changed'
  | 'theme.changed'
  | 'voice.started'
  | 'voice.speech_started'
  | 'voice.speech_stopped'
  | 'voice.transcription'
  | 'voice.response_started'
  | 'voice.audio_delta'
  | 'voice.response_done'
  | 'voice.error'
  | 'assistant.started'
  | 'assistant.delta'
  | 'assistant.final'
  | 'system.keepalive';

export interface WSEvent<T = unknown> {
  type: WSEventType;
  data: T;
  timestamp: number;
}

type EventHandler<T = unknown> = (event: WSEvent<T>) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private handlers = new Map<WSEventType, Set<EventHandler>>();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 1000;
  private heartbeatInterval: number | null = null;
  private url: string = '';
  private token: string = '';

  connect(url: string, token: string): void {
    this.url = url;
    this.token = token;
    this.doConnect();
  }

  private doConnect(): void {
    const wsUrl = `${this.url}?token=${encodeURIComponent(this.token)}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.startHeartbeat();
      this.emit('system.keepalive', { connected: true });
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WSEvent;
        this.dispatch(data.type, data);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    this.ws.onclose = () => {
      this.stopHeartbeat();
      this.scheduleReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  disconnect(): void {
    this.stopHeartbeat();
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnect
    this.ws?.close();
    this.ws = null;
  }

  send<T>(type: WSEventType, data: T): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, data, timestamp: Date.now() }));
    }
  }

  on<T>(type: WSEventType, handler: EventHandler<T>): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler as EventHandler);
    return () => this.handlers.get(type)?.delete(handler as EventHandler);
  }

  private dispatch(type: WSEventType, event: WSEvent): void {
    this.handlers.get(type)?.forEach(handler => handler(event));
  }

  private emit<T>(type: WSEventType, data: T): void {
    this.dispatch(type, { type, data, timestamp: Date.now() });
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = window.setInterval(() => {
      this.send('system.keepalive', { ping: true });
    }, 20000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts++;
    setTimeout(() => this.doConnect(), delay);
  }
}

export const wsClient = new WebSocketClient();
```

### 6.2 Theme JSON Schema

```json
{
  "$schema": "https://somaagent.io/schemas/agentskin-v1.json",
  "type": "object",
  "required": ["name", "version", "variables"],
  "properties": {
    "name": { "type": "string", "minLength": 1, "maxLength": 64 },
    "version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" },
    "author": { "type": "string", "maxLength": 128 },
    "description": { "type": "string", "maxLength": 512 },
    "category": { 
      "type": "string", 
      "enum": ["Professional", "Creative", "Developer", "Gaming", "Accessibility"] 
    },
    "tags": { "type": "array", "items": { "type": "string" }, "maxItems": 10 },
    "variables": {
      "type": "object",
      "required": [
        "bg-void", "glass-surface", "glass-border", "text-main", "text-dim",
        "accent-primary", "accent-secondary", "accent-success", "accent-warning", "accent-danger",
        "shadow-soft", "radius-sm", "radius-md", "radius-lg", "radius-full",
        "spacing-xs", "spacing-sm", "spacing-md", "spacing-lg", "spacing-xl",
        "font-sans", "font-mono", "text-xs", "text-sm", "text-base", "text-lg"
      ],
      "additionalProperties": { "type": "string" }
    }
  }
}
```

### 6.3 Theme Application Logic

```typescript
class ThemeManager {
  private root: HTMLElement;
  private active: Theme | null = null;
  
  constructor() {
    this.root = document.documentElement;
  }
  
  apply(theme: Theme): void {
    // Validate theme
    this.validate(theme);
    
    // Apply CSS variables
    for (const [key, value] of Object.entries(theme.variables)) {
      this.root.style.setProperty(`--eog-${key}`, value);
    }
    
    // Store in localStorage
    localStorage.setItem('eog-theme', JSON.stringify(theme));
    
    // Emit event
    this.root.dispatchEvent(new CustomEvent('theme-changed', { detail: theme }));
    
    this.active = theme;
  }
  
  validate(theme: Theme): void {
    // Check for url() in values (XSS prevention)
    for (const value of Object.values(theme.variables)) {
      if (value.includes('url(')) {
        throw new ThemeValidationError('url() not allowed in theme values');
      }
    }
    
    // Validate contrast ratios (WCAG AA)
    const contrast = this.calculateContrast(
      theme.variables['bg-void'],
      theme.variables['text-main']
    );
    if (contrast < 4.5) {
      throw new ThemeValidationError('Insufficient contrast ratio (min 4.5:1)');
    }
  }
}
```

---

## 7. Voice Integration

### 7.1 Voice Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    VOICE SUBSYSTEM                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  <eog-voice-controls>                    │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │   │
│  │  │ Record  │  │  Stop   │  │  Mute   │  │ Settings│    │   │
│  │  │ Button  │  │ Button  │  │ Toggle  │  │  Link   │    │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  <eog-voice-indicator>                   │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │  State: idle | listening | processing | speaking │    │   │
│  │  │  Level: ████████░░░░░░░░ (audio level meter)     │    │   │
│  │  │  Provider: Local | AgentVoiceBox                 │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    VoiceService                          │   │
│  │  ┌─────────────────┐  ┌─────────────────────────────┐   │   │
│  │  │ LocalProvider   │  │ AgentVoiceBoxProvider       │   │   │
│  │  │ - Whisper STT   │  │ - WebSocket /v1/realtime    │   │   │
│  │  │ - Kokoro TTS    │  │ - Bidirectional audio       │   │   │
│  │  │ - WebRTC VAD    │  │ - Turn detection            │   │   │
│  │  └─────────────────┘  └─────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Voice Service Implementation

```typescript
// File: src/services/voice-service.ts

import { voiceStore, VoiceProvider } from '../stores/voice-store';
import { wsClient } from './websocket-client';

export class VoiceService {
  private mediaStream: MediaStream | null = null;
  private audioContext: AudioContext | null = null;
  private processor: ScriptProcessorNode | null = null;
  private agentVoiceBoxWs: WebSocket | null = null;

  async initialize(provider: VoiceProvider): Promise<void> {
    if (provider === 'disabled') return;

    // Request microphone access
    this.mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        sampleRate: voiceStore.state.config.audio.sample_rate,
      },
    });

    this.audioContext = new AudioContext({
      sampleRate: voiceStore.state.config.audio.sample_rate,
    });

    if (provider === 'agentvoicebox') {
      await this.connectAgentVoiceBox();
    }

    voiceStore.setState('idle');
  }

  private async connectAgentVoiceBox(): Promise<void> {
    const config = voiceStore.state.config.agentvoicebox;
    if (!config.ws_url) throw new Error('AgentVoiceBox WebSocket URL not configured');

    return new Promise((resolve, reject) => {
      this.agentVoiceBoxWs = new WebSocket(config.ws_url);

      this.agentVoiceBoxWs.onopen = () => {
        // Send session configuration
        this.agentVoiceBoxWs!.send(JSON.stringify({
          type: 'session.update',
          session: {
            voice: config.voice,
            model: config.model,
            turn_detection: config.turn_detection ? { type: 'server_vad' } : null,
            input_audio_format: 'pcm16',
            output_audio_format: 'pcm16',
          },
        }));
        resolve();
      };

      this.agentVoiceBoxWs.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.handleAgentVoiceBoxEvent(data);
      };

      this.agentVoiceBoxWs.onerror = (error) => {
        voiceStore.setError('AgentVoiceBox connection failed');
        reject(error);
      };

      this.agentVoiceBoxWs.onclose = () => {
        voiceStore.setState('idle');
      };
    });
  }

  private handleAgentVoiceBoxEvent(event: any): void {
    switch (event.type) {
      case 'session.created':
      case 'session.updated':
        voiceStore.setState('idle');
        break;
      case 'input_audio_buffer.speech_started':
        voiceStore.setState('listening');
        wsClient.send('voice.speech_started', {});
        break;
      case 'input_audio_buffer.speech_stopped':
        voiceStore.setState('processing');
        wsClient.send('voice.speech_stopped', {});
        break;
      case 'conversation.item.created':
        if (event.item?.content?.[0]?.transcript) {
          voiceStore.setTranscript(event.item.content[0].transcript);
          wsClient.send('voice.transcription', { text: event.item.content[0].transcript });
        }
        break;
      case 'response.audio.delta':
        voiceStore.setState('speaking');
        this.playAudioDelta(event.delta);
        wsClient.send('voice.audio_delta', { delta: event.delta });
        break;
      case 'response.done':
        voiceStore.setState('idle');
        wsClient.send('voice.response_done', {});
        break;
      case 'error':
        voiceStore.setError(event.error?.message || 'Unknown error');
        wsClient.send('voice.error', { error: event.error });
        break;
    }
  }

  startListening(): void {
    if (!this.mediaStream || !this.audioContext) return;

    const source = this.audioContext.createMediaStreamSource(this.mediaStream);
    this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);

    this.processor.onaudioprocess = (event) => {
      const inputData = event.inputBuffer.getChannelData(0);
      const pcm16 = this.floatTo16BitPCM(inputData);
      const base64 = this.arrayBufferToBase64(pcm16.buffer);

      if (voiceStore.state.provider === 'agentvoicebox' && this.agentVoiceBoxWs) {
        this.agentVoiceBoxWs.send(JSON.stringify({
          type: 'input_audio_buffer.append',
          audio: base64,
        }));
      } else if (voiceStore.state.provider === 'local') {
        wsClient.send('voice.input_audio', { audio: base64 });
      }
    };

    source.connect(this.processor);
    this.processor.connect(this.audioContext.destination);
    voiceStore.setState('listening');
    wsClient.send('voice.started', {});
  }

  stopListening(): void {
    this.processor?.disconnect();
    this.processor = null;
    voiceStore.setState('idle');
  }

  private playAudioDelta(base64Audio: string): void {
    const audioData = this.base64ToArrayBuffer(base64Audio);
    const audioBuffer = this.audioContext!.createBuffer(1, audioData.byteLength / 2, 24000);
    const channelData = audioBuffer.getChannelData(0);
    const int16Array = new Int16Array(audioData);
    for (let i = 0; i < int16Array.length; i++) {
      channelData[i] = int16Array[i] / 32768;
    }
    const source = this.audioContext!.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(this.audioContext!.destination);
    source.start();
  }

  private floatTo16BitPCM(input: Float32Array): Int16Array {
    const output = new Int16Array(input.length);
    for (let i = 0; i < input.length; i++) {
      const s = Math.max(-1, Math.min(1, input[i]));
      output[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return output;
  }

  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  private base64ToArrayBuffer(base64: string): ArrayBuffer {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }

  async testConnection(): Promise<boolean> {
    const config = voiceStore.state.config.agentvoicebox;
    if (!config.base_url) return false;
    try {
      const response = await fetch(`${config.base_url}/health`);
      return response.ok;
    } catch {
      return false;
    }
  }

  dispose(): void {
    this.stopListening();
    this.agentVoiceBoxWs?.close();
    this.audioContext?.close();
    this.mediaStream?.getTracks().forEach(track => track.stop());
  }
}

export const voiceService = new VoiceService();
```

### 7.2 Voice Service Implementation

```typescript
interface VoiceProvider {
  connect(): Promise<void>;
  disconnect(): void;
  startListening(): Promise<void>;
  stopListening(): void;
  speak(text: string): Promise<void>;
  cancel(): void;
  onTranscription(handler: (text: string) => void): void;
  onAudioLevel(handler: (level: number) => void): void;
  onStateChange(handler: (state: VoiceState) => void): void;
}

class LocalVoiceProvider implements VoiceProvider {
  private audioContext: AudioContext;
  private mediaStream: MediaStream | null = null;
  private whisperWorker: Worker;
  private kokoroWorker: Worker;
  
  async startListening(): Promise<void> {
    this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    // Process audio through Whisper STT
  }
  
  async speak(text: string): Promise<void> {
    // Generate audio through Kokoro TTS
    const audio = await this.kokoroWorker.synthesize(text);
    await this.playAudio(audio);
  }
}

class AgentVoiceBoxProvider implements VoiceProvider {
  private ws: WebSocket | null = null;
  private config: AgentVoiceBoxConfig;
  
  async connect(): Promise<void> {
    this.ws = new WebSocket(this.config.wsUrl);
    this.ws.onmessage = this.handleMessage.bind(this);
    // Send session.update with configuration
  }
  
  async startListening(): Promise<void> {
    // Start sending audio chunks via WebSocket
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    // Process and send audio
  }
  
  private handleMessage(event: MessageEvent): void {
    const data = JSON.parse(event.data);
    switch (data.type) {
      case 'response.audio.delta':
        this.playAudioChunk(data.delta);
        break;
      case 'conversation.item.input_audio_transcription.completed':
        this.onTranscription?.(data.transcript);
        break;
    }
  }
}
```

---

## 8. Performance Requirements

### 8.1 Core Web Vitals Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| First Contentful Paint (FCP) | < 1.5s | Time to first content |
| Largest Contentful Paint (LCP) | < 2.5s | Time to largest element |
| First Input Delay (FID) | < 100ms | Time to interactive |
| Cumulative Layout Shift (CLS) | < 0.1 | Visual stability |
| Time to Interactive (TTI) | < 3.0s | Full interactivity |

### 8.2 Scale Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| Concurrent WebSocket connections | 1,000,000+ | Horizontal scaling, Redis pub/sub |
| API requests/second/node | 100,000+ | Django Ninja async, connection pooling |
| Permission checks/second | 1,000,000+ | SpiceDB, Redis caching |
| Theme switch latency | < 300ms | CSS Custom Properties, no reflow |
| Component render time | < 16ms | Virtual DOM, Shadow DOM isolation |

### 8.3 Bundle Size Targets

| Bundle | Target | Strategy |
|--------|--------|----------|
| Initial JS | < 100KB gzip | Code splitting, tree shaking |
| Initial CSS | < 20KB gzip | CSS Custom Properties, minimal reset |
| Per-route chunk | < 50KB gzip | Dynamic imports, lazy loading |
| Total app | < 500KB gzip | Aggressive tree shaking |

---

## 9. Accessibility (WCAG 2.1 AA)

### 9.1 Requirements

- All interactive elements keyboard accessible
- Focus indicators visible (2px solid outline)
- ARIA labels on all controls
- Color contrast ratio >= 4.5:1
- Reduced motion support (`prefers-reduced-motion`)
- Screen reader compatible (NVDA, VoiceOver, JAWS)
- Skip navigation links
- Semantic HTML structure

### 9.2 Component Accessibility Patterns

```typescript
@customElement('eog-button')
export class EogButton extends LitElement {
  @property({ type: Boolean, reflect: true }) disabled = false;
  @property({ type: String }) ariaLabel = '';
  
  render() {
    return html`
      <button
        role="button"
        aria-label=${this.ariaLabel || nothing}
        aria-disabled=${this.disabled}
        tabindex=${this.disabled ? -1 : 0}
        @keydown=${this.handleKeydown}
      >
        <slot></slot>
      </button>
    `;
  }
  
  private handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      this.click();
    }
  }
}
```

---

## 10. File Structure

```
somaAgent01/ui/frontend/
├── src/
│   ├── components/           # Primitive components
│   │   ├── eog-button.ts
│   │   ├── eog-input.ts
│   │   ├── eog-select.ts
│   │   ├── eog-toggle.ts
│   │   ├── eog-slider.ts
│   │   ├── eog-modal.ts
│   │   ├── eog-toast.ts
│   │   ├── eog-card.ts
│   │   ├── eog-tabs.ts
│   │   └── index.ts
│   ├── layout/               # Layout components
│   │   ├── eog-app.ts
│   │   ├── eog-header.ts
│   │   ├── eog-sidebar.ts
│   │   ├── eog-main.ts
│   │   └── index.ts
│   ├── views/                # Page components
│   │   ├── eog-chat.ts
│   │   ├── eog-memory.ts
│   │   ├── eog-tools.ts
│   │   ├── eog-settings.ts
│   │   ├── eog-themes.ts
│   │   ├── eog-voice.ts
│   │   ├── eog-cognitive.ts
│   │   ├── eog-admin.ts
│   │   └── index.ts
│   ├── stores/               # State management
│   │   ├── auth-store.ts
│   │   ├── mode-store.ts
│   │   ├── theme-store.ts
│   │   ├── perm-store.ts
│   │   ├── voice-store.ts
│   │   └── index.ts
│   ├── services/             # API clients
│   │   ├── api-client.ts
│   │   ├── ws-client.ts
│   │   ├── auth-service.ts
│   │   ├── voice-service.ts
│   │   └── index.ts
│   ├── styles/               # Global styles
│   │   ├── tokens.css
│   │   ├── reset.css
│   │   └── themes/
│   │       ├── default-light.json
│   │       ├── midnight-dark.json
│   │       └── high-contrast.json
│   ├── utils/                # Utilities
│   │   ├── validators.ts
│   │   ├── formatters.ts
│   │   └── constants.ts
│   ├── router.ts             # Route configuration
│   └── index.ts              # Entry point
├── public/
│   ├── index.html
│   └── favicon.ico
├── package.json
├── vite.config.ts
├── tsconfig.json
└── web-test-runner.config.js
```

---

**Document Status:** COMPLETE

**Next Steps:**
1. Complete design.md with Django models and API schemas
2. Create tasks.md with implementation plan

---

## 5. WebSocket Event System

### 5.1 Event Types and Payloads

| Event Type | Direction | Payload | Description |
|------------|-----------|---------|-------------|
| `mode.changed` | Server→Client | `{ mode: string, previous: string }` | Agent mode changed |
| `settings.changed` | Server→Client | `{ section: string, key: string, value: any }` | Settings updated |
| `theme.changed` | Server→Client | `{ theme_id: string }` | Theme changed |
| `voice.started` | Client→Server | `{}` | Voice session started |
| `voice.speech_started` | Server→Client | `{}` | User started speaking |
| `voice.speech_stopped` | Server→Client | `{}` | User stopped speaking |
| `voice.transcription` | Server→Client | `{ text: string, final: boolean }` | STT result |
| `voice.response_started` | Server→Client | `{}` | Agent started responding |
| `voice.audio_delta` | Server→Client | `{ delta: string }` | Audio chunk (base64) |
| `voice.response_done` | Server→Client | `{}` | Agent finished responding |
| `voice.error` | Server→Client | `{ error: string, code: string }` | Voice error |
| `voice.input_audio` | Client→Server | `{ audio: string }` | Audio input (base64) |
| `voice.cancel` | Client→Server | `{}` | Cancel current response |
| `assistant.started` | Server→Client | `{ session_id: string }` | Assistant started |
| `assistant.thinking.started` | Server→Client | `{}` | Reasoning started |
| `assistant.delta` | Server→Client | `{ content: string }` | Response chunk |
| `assistant.thinking.final` | Server→Client | `{ content: string }` | Reasoning complete |
| `assistant.final` | Server→Client | `{ content: string, done: boolean }` | Response complete |
| `assistant.tool.started` | Server→Client | `{ tool: string }` | Tool execution started |
| `assistant.tool.delta` | Server→Client | `{ output: string }` | Tool output chunk |
| `assistant.tool.final` | Server→Client | `{ output: string }` | Tool execution complete |
| `system.keepalive` | Bidirectional | `{ ping?: boolean }` | Heartbeat |

### 5.2 Event Flow Diagrams

#### Chat Message Flow

```
Client                    Django Ninja                    Agent
  │                           │                             │
  │──POST /api/v2/chat───────▶│                             │
  │                           │──Kafka: chat.request───────▶│
  │                           │                             │
  │◀──WS: assistant.started───│◀──Kafka: assistant.started──│
  │                           │                             │
  │◀──WS: assistant.delta─────│◀──Kafka: assistant.delta────│
  │◀──WS: assistant.delta─────│◀──Kafka: assistant.delta────│
  │◀──WS: assistant.delta─────│◀──Kafka: assistant.delta────│
  │                           │                             │
  │◀──WS: assistant.final─────│◀──Kafka: assistant.final────│
  │                           │                             │
```

#### Voice Flow (AgentVoiceBox)

```
Client                    AgentVoiceBox                   Agent
  │                           │                             │
  │──WS: session.update──────▶│                             │
  │◀──WS: session.created─────│                             │
  │                           │                             │
  │──WS: input_audio.append──▶│                             │
  │──WS: input_audio.append──▶│                             │
  │                           │                             │
  │◀──WS: speech_started──────│                             │
  │                           │                             │
  │◀──WS: speech_stopped──────│                             │
  │                           │──STT: transcription────────▶│
  │◀──WS: conversation.item───│                             │
  │                           │                             │
  │                           │◀──LLM: response─────────────│
  │◀──WS: response.audio.delta│                             │
  │◀──WS: response.audio.delta│                             │
  │◀──WS: response.done───────│                             │
  │                           │                             │
```

---

## 6. Performance Optimization

### 6.1 Scale Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| Concurrent WebSocket connections | 1,000,000+ | Connection pooling, horizontal scaling |
| First Contentful Paint | < 1.5s | Code splitting, preloading, CDN |
| Time to Interactive | < 3s | Lazy loading, service worker |
| API Response Time (p95) | < 50ms | Connection pooling, caching |
| Theme Switch | < 300ms | CSS Custom Properties (no reflow) |
| Component Render | < 16ms | Virtual scrolling, memoization |
| WebSocket Latency | < 100ms | Edge servers, sticky sessions |

### 6.2 Optimization Strategies

#### Code Splitting

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-lit': ['lit', '@lit/context', '@lit-labs/signals'],
          'vendor-router': ['@vaadin/router'],
          'views-chat': ['./src/views/eog-chat-view.ts'],
          'views-memory': ['./src/views/eog-memory-view.ts'],
          'views-settings': ['./src/views/eog-settings-view.ts'],
          'views-admin': ['./src/views/eog-admin-view.ts'],
          'voice': ['./src/services/voice-service.ts', './src/stores/voice-store.ts'],
        },
      },
    },
  },
});
```

#### Virtual Scrolling

```typescript
// For large lists (memory items, audit logs, etc.)
@customElement('eog-virtual-list')
export class EogVirtualList extends LitElement {
  @property({ type: Array }) items: unknown[] = [];
  @property({ type: Number }) itemHeight = 48;
  @property({ type: Number }) overscan = 5;

  @state() private scrollTop = 0;
  @state() private containerHeight = 0;

  private get visibleRange(): { start: number; end: number } {
    const start = Math.max(0, Math.floor(this.scrollTop / this.itemHeight) - this.overscan);
    const visibleCount = Math.ceil(this.containerHeight / this.itemHeight);
    const end = Math.min(this.items.length, start + visibleCount + this.overscan * 2);
    return { start, end };
  }

  render() {
    const { start, end } = this.visibleRange;
    const visibleItems = this.items.slice(start, end);
    const totalHeight = this.items.length * this.itemHeight;
    const offsetY = start * this.itemHeight;

    return html`
      <div class="container" @scroll=${this.handleScroll}>
        <div class="spacer" style="height: ${totalHeight}px">
          <div class="content" style="transform: translateY(${offsetY}px)">
            ${visibleItems.map((item, i) => html`
              <slot name="item" .item=${item} .index=${start + i}></slot>
            `)}
          </div>
        </div>
      </div>
    `;
  }

  private handleScroll(e: Event) {
    this.scrollTop = (e.target as HTMLElement).scrollTop;
  }
}
```

#### Service Worker Caching

```typescript
// sw.ts
const CACHE_NAME = 'eog-v1';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/assets/main.js',
  '/assets/styles.css',
  '/assets/themes/default-light.json',
  '/assets/themes/midnight-dark.json',
];

self.addEventListener('install', (event: ExtendableEvent) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
});

self.addEventListener('fetch', (event: FetchEvent) => {
  // Cache-first for static assets
  if (STATIC_ASSETS.some(asset => event.request.url.endsWith(asset))) {
    event.respondWith(
      caches.match(event.request).then(cached => cached || fetch(event.request))
    );
    return;
  }

  // Network-first for API calls
  if (event.request.url.includes('/api/')) {
    event.respondWith(
      fetch(event.request).catch(() => caches.match(event.request))
    );
  }
});
```

### 6.3 Connection Pooling for Millions of Users

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WEBSOCKET SCALING ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Clients (1M+)                                                              │
│   ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                                  │
│   │ C1  │ │ C2  │ │ C3  │ │ ... │ │ Cn  │                                  │
│   └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘                                  │
│      │       │       │       │       │                                       │
│      └───────┴───────┴───────┴───────┘                                       │
│                      │                                                        │
│                      ▼                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    LOAD BALANCER (nginx/HAProxy)                     │   │
│   │                    - Sticky sessions (IP hash)                       │   │
│   │                    - Health checks                                   │   │
│   │                    - SSL termination                                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                      │                                                        │
│      ┌───────────────┼───────────────┬───────────────┐                       │
│      ▼               ▼               ▼               ▼                       │
│   ┌──────┐       ┌──────┐       ┌──────┐       ┌──────┐                     │
│   │ WS-1 │       │ WS-2 │       │ WS-3 │       │ WS-N │                     │
│   │ 10K  │       │ 10K  │       │ 10K  │       │ 10K  │                     │
│   │ conn │       │ conn │       │ conn │       │ conn │                     │
│   └──┬───┘       └──┬───┘       └──┬───┘       └──┬───┘                     │
│      │              │              │              │                          │
│      └──────────────┴──────────────┴──────────────┘                          │
│                      │                                                        │
│                      ▼                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         REDIS PUB/SUB                                │   │
│   │                    - Cross-node event broadcast                      │   │
│   │                    - Session state sync                              │   │
│   │                    - Connection tracking                             │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Django Channels Configuration

```python
# File: eog/settings/production.py

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                {
                    "address": os.environ.get("REDIS_URL", "redis://localhost:6379"),
                    "db": 0,
                }
            ],
            "capacity": 1500,  # Max messages per channel
            "expiry": 60,      # Message expiry in seconds
        },
    },
}

# WebSocket connection limits per worker
ASGI_APPLICATION = "eog.asgi.application"
WEBSOCKET_MAX_CONNECTIONS = 10000  # Per worker process
WEBSOCKET_HEARTBEAT_INTERVAL = 20  # Seconds
WEBSOCKET_RECONNECT_DELAY = 1000   # Milliseconds
```

---

## 7. AgentSkin Theme Integration

### 7.1 CSS Custom Properties Mapping

```css
/* File: src/styles/agentskin-bridge.css */

:root {
  /* Map AgentSkin variables to EOG variables */
  --eog-bg-void: var(--bg-void, #0f172a);
  --eog-glass-surface: var(--glass-surface, rgba(30, 41, 59, 0.85));
  --eog-glass-border: var(--glass-border, rgba(255, 255, 255, 0.05));
  --eog-text-main: var(--text-main, #e2e8f0);
  --eog-text-dim: var(--text-dim, #64748b);
  --eog-accent-primary: var(--accent-primary, #3b82f6);
  --eog-accent-secondary: var(--accent-secondary, #8b5cf6);
  --eog-accent-success: var(--accent-success, #22c55e);
  --eog-accent-warning: var(--accent-warning, #f59e0b);
  --eog-accent-danger: var(--accent-danger, #ef4444);
  --eog-shadow-soft: var(--shadow-soft, 0 10px 40px -10px rgba(0, 0, 0, 0.5));
  --eog-radius-sm: var(--radius-sm, 4px);
  --eog-radius-md: var(--radius-md, 8px);
  --eog-radius-lg: var(--radius-lg, 16px);
  --eog-radius-full: var(--radius-full, 9999px);
  --eog-spacing-xs: var(--spacing-xs, 4px);
  --eog-spacing-sm: var(--spacing-sm, 8px);
  --eog-spacing-md: var(--spacing-md, 16px);
  --eog-spacing-lg: var(--spacing-lg, 24px);
  --eog-spacing-xl: var(--spacing-xl, 32px);
  --eog-font-sans: var(--font-sans, 'Space Grotesk', sans-serif);
  --eog-font-mono: var(--font-mono, 'JetBrains Mono', monospace);
  --eog-text-xs: var(--text-xs, 10px);
  --eog-text-sm: var(--text-sm, 12px);
  --eog-text-base: var(--text-base, 14px);
  --eog-text-lg: var(--text-lg, 16px);
  --eog-text-xl: var(--text-xl, 20px);
}
```

### 7.2 Theme Application Logic

```typescript
// File: src/utils/theme-loader.ts

export interface AgentSkinTheme {
  name: string;
  version: string;
  author: string;
  description?: string;
  category?: string;
  tags?: string[];
  variables: Record<string, string>;
}

const REQUIRED_VARIABLES = [
  'bg-void', 'glass-surface', 'glass-border', 'text-main', 'text-dim',
  'accent-primary', 'accent-secondary', 'accent-success', 'accent-warning', 'accent-danger',
  'shadow-soft', 'radius-sm', 'radius-md', 'radius-lg', 'radius-full',
  'spacing-xs', 'spacing-sm', 'spacing-md', 'spacing-lg', 'spacing-xl',
  'font-sans', 'font-mono', 'text-xs', 'text-sm', 'text-base', 'text-lg',
];

const URL_PATTERN = /url\s*\(/i;

export function validateTheme(theme: AgentSkinTheme): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  // Check required fields
  if (!theme.name) errors.push('Missing required field: name');
  if (!theme.version) errors.push('Missing required field: version');
  if (!theme.variables) errors.push('Missing required field: variables');

  // Check required variables (26 minimum)
  const missingVars = REQUIRED_VARIABLES.filter(v => !(v in theme.variables));
  if (missingVars.length > 0) {
    errors.push(`Missing required variables: ${missingVars.join(', ')}`);
  }

  // Security: Check for url() in values (XSS prevention)
  for (const [key, value] of Object.entries(theme.variables)) {
    if (URL_PATTERN.test(value)) {
      errors.push(`Security violation: url() not allowed in variable "${key}"`);
    }
  }

  // Validate contrast ratios (WCAG AA)
  const textMain = theme.variables['text-main'];
  const bgVoid = theme.variables['bg-void'];
  if (textMain && bgVoid) {
    const ratio = calculateContrastRatio(textMain, bgVoid);
    if (ratio < 4.5) {
      errors.push(`Contrast ratio ${ratio.toFixed(2)} below WCAG AA minimum (4.5:1)`);
    }
  }

  return { valid: errors.length === 0, errors };
}

export function applyTheme(theme: AgentSkinTheme): void {
  const root = document.documentElement;
  
  // Apply all variables with --eog- prefix
  for (const [key, value] of Object.entries(theme.variables)) {
    root.style.setProperty(`--eog-${key}`, value);
  }

  // Also set without prefix for backward compatibility
  for (const [key, value] of Object.entries(theme.variables)) {
    root.style.setProperty(`--${key}`, value);
  }

  // Dispatch theme change event
  window.dispatchEvent(new CustomEvent('eog-theme-changed', { detail: theme }));
}

function calculateContrastRatio(fg: string, bg: string): number {
  const fgLum = getLuminance(parseColor(fg));
  const bgLum = getLuminance(parseColor(bg));
  const lighter = Math.max(fgLum, bgLum);
  const darker = Math.min(fgLum, bgLum);
  return (lighter + 0.05) / (darker + 0.05);
}

function parseColor(color: string): [number, number, number] {
  // Handle hex colors
  if (color.startsWith('#')) {
    const hex = color.slice(1);
    const r = parseInt(hex.slice(0, 2), 16);
    const g = parseInt(hex.slice(2, 4), 16);
    const b = parseInt(hex.slice(4, 6), 16);
    return [r, g, b];
  }
  // Handle rgba
  const match = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  if (match) {
    return [parseInt(match[1]), parseInt(match[2]), parseInt(match[3])];
  }
  return [0, 0, 0];
}

function getLuminance([r, g, b]: [number, number, number]): number {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}
```

---

## 8. Voice UI Components

### 8.1 Voice Button Component

```typescript
// File: src/components/eog-voice-button.ts

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { consume } from '@lit/context';
import { voiceContext, VoiceStoreState } from '../stores/voice-store';
import { voiceService } from '../services/voice-service';

@customElement('eog-voice-button')
export class EogVoiceButton extends LitElement {
  static styles = css`
    :host {
      display: inline-block;
    }

    button {
      width: 48px;
      height: 48px;
      border-radius: var(--eog-radius-full);
      border: 2px solid var(--eog-glass-border);
      background: var(--eog-glass-surface);
      color: var(--eog-text-main);
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    button:hover:not(:disabled) {
      background: var(--eog-accent-primary);
      border-color: var(--eog-accent-primary);
    }

    button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    button.listening {
      background: var(--eog-accent-danger);
      border-color: var(--eog-accent-danger);
      animation: pulse 1.5s infinite;
    }

    button.processing {
      background: var(--eog-accent-warning);
      border-color: var(--eog-accent-warning);
    }

    button.speaking {
      background: var(--eog-accent-success);
      border-color: var(--eog-accent-success);
    }

    @keyframes pulse {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.1); }
    }

    .icon {
      width: 24px;
      height: 24px;
    }
  `;

  @consume({ context: voiceContext, subscribe: true })
  @property({ attribute: false })
  voiceState!: VoiceStoreState;

  @state() private isHolding = false;

  private get isDisabled(): boolean {
    return !this.voiceState.enabled || this.voiceState.provider === 'disabled';
  }

  private get buttonClass(): string {
    return this.voiceState.state;
  }

  render() {
    return html`
      <button
        class=${this.buttonClass}
        ?disabled=${this.isDisabled}
        @mousedown=${this.handleMouseDown}
        @mouseup=${this.handleMouseUp}
        @mouseleave=${this.handleMouseUp}
        @touchstart=${this.handleMouseDown}
        @touchend=${this.handleMouseUp}
        title=${this.getTooltip()}
      >
        ${this.renderIcon()}
      </button>
    `;
  }

  private renderIcon() {
    switch (this.voiceState.state) {
      case 'listening':
        return html`<svg class="icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
          <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
        </svg>`;
      case 'processing':
        return html`<eog-spinner size="sm"></eog-spinner>`;
      case 'speaking':
        return html`<svg class="icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/>
        </svg>`;
      default:
        return html`<svg class="icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
          <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
        </svg>`;
    }
  }

  private getTooltip(): string {
    if (this.isDisabled) return 'Voice disabled';
    switch (this.voiceState.state) {
      case 'listening': return 'Listening... Release to stop';
      case 'processing': return 'Processing...';
      case 'speaking': return 'Speaking...';
      default: return 'Hold to speak';
    }
  }

  private handleMouseDown(e: Event) {
    e.preventDefault();
    if (this.isDisabled) return;
    this.isHolding = true;
    voiceService.startListening();
  }

  private handleMouseUp() {
    if (!this.isHolding) return;
    this.isHolding = false;
    voiceService.stopListening();
  }
}
```

### 8.2 Voice Settings Component

```typescript
// File: src/views/eog-voice-settings.ts

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { voiceStore, VoiceProvider, VoiceConfig } from '../stores/voice-store';
import { voiceService } from '../services/voice-service';

@customElement('eog-voice-settings')
export class EogVoiceSettings extends LitElement {
  static styles = css`
    :host {
      display: block;
      padding: var(--eog-spacing-md);
    }

    .section {
      background: var(--eog-glass-surface);
      border: 1px solid var(--eog-glass-border);
      border-radius: var(--eog-radius-lg);
      padding: var(--eog-spacing-md);
      margin-bottom: var(--eog-spacing-md);
    }

    .section-title {
      font-size: var(--eog-text-lg);
      font-weight: 600;
      margin-bottom: var(--eog-spacing-sm);
      color: var(--eog-text-main);
    }

    .field {
      margin-bottom: var(--eog-spacing-sm);
    }

    .field-label {
      display: block;
      font-size: var(--eog-text-sm);
      color: var(--eog-text-dim);
      margin-bottom: var(--eog-spacing-xs);
    }

    .provider-cards {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: var(--eog-spacing-sm);
    }

    .provider-card {
      padding: var(--eog-spacing-md);
      border: 2px solid var(--eog-glass-border);
      border-radius: var(--eog-radius-md);
      cursor: pointer;
      transition: all 0.2s ease;
      text-align: center;
    }

    .provider-card:hover {
      border-color: var(--eog-accent-primary);
    }

    .provider-card.selected {
      border-color: var(--eog-accent-primary);
      background: rgba(59, 130, 246, 0.1);
    }

    .provider-icon {
      font-size: 32px;
      margin-bottom: var(--eog-spacing-xs);
    }

    .provider-name {
      font-weight: 600;
      color: var(--eog-text-main);
    }

    .provider-desc {
      font-size: var(--eog-text-xs);
      color: var(--eog-text-dim);
    }

    .test-button {
      margin-top: var(--eog-spacing-sm);
    }

    .test-result {
      margin-top: var(--eog-spacing-xs);
      font-size: var(--eog-text-sm);
    }

    .test-result.success {
      color: var(--eog-accent-success);
    }

    .test-result.error {
      color: var(--eog-accent-danger);
    }
  `;

  @state() private config: VoiceConfig = voiceStore.state.config;
  @state() private testResult: { success: boolean; message: string } | null = null;
  @state() private testing = false;

  render() {
    return html`
      <div class="section">
        <div class="section-title">Voice Provider</div>
        <div class="provider-cards">
          ${this.renderProviderCard('disabled', '🔇', 'Disabled', 'No voice features')}
          ${this.renderProviderCard('local', '🎤', 'Local', 'Whisper STT + Kokoro TTS')}
          ${this.renderProviderCard('agentvoicebox', '🗣️', 'AgentVoiceBox', 'Full speech-on-speech')}
        </div>
      </div>

      ${this.config.provider === 'local' ? this.renderLocalSettings() : ''}
      ${this.config.provider === 'agentvoicebox' ? this.renderAgentVoiceBoxSettings() : ''}
      ${this.config.provider !== 'disabled' ? this.renderAudioSettings() : ''}
    `;
  }

  private renderProviderCard(provider: VoiceProvider, icon: string, name: string, desc: string) {
    return html`
      <div
        class="provider-card ${this.config.provider === provider ? 'selected' : ''}"
        @click=${() => this.selectProvider(provider)}
      >
        <div class="provider-icon">${icon}</div>
        <div class="provider-name">${name}</div>
        <div class="provider-desc">${desc}</div>
      </div>
    `;
  }

  private renderLocalSettings() {
    return html`
      <div class="section">
        <div class="section-title">Local Voice Settings</div>
        
        <div class="field">
          <label class="field-label">STT Engine</label>
          <eog-select
            .value=${this.config.local.stt_engine}
            .options=${[
              { value: 'whisper', label: 'Whisper' },
              { value: 'faster-whisper', label: 'Faster Whisper' },
            ]}
            @change=${(e: CustomEvent) => this.updateLocal('stt_engine', e.detail.value)}
          ></eog-select>
        </div>

        <div class="field">
          <label class="field-label">STT Model Size</label>
          <eog-select
            .value=${this.config.local.stt_model_size}
            .options=${[
              { value: 'tiny', label: 'Tiny (fastest)' },
              { value: 'base', label: 'Base (balanced)' },
              { value: 'small', label: 'Small' },
              { value: 'medium', label: 'Medium' },
              { value: 'large', label: 'Large (most accurate)' },
            ]}
            @change=${(e: CustomEvent) => this.updateLocal('stt_model_size', e.detail.value)}
          ></eog-select>
        </div>

        <div class="field">
          <label class="field-label">TTS Engine</label>
          <eog-select
            .value=${this.config.local.tts_engine}
            .options=${[
              { value: 'kokoro', label: 'Kokoro (recommended)' },
              { value: 'browser', label: 'Browser TTS' },
            ]}
            @change=${(e: CustomEvent) => this.updateLocal('tts_engine', e.detail.value)}
          ></eog-select>
        </div>

        <div class="field">
          <label class="field-label">TTS Voice</label>
          <eog-input
            .value=${this.config.local.tts_voice}
            @change=${(e: CustomEvent) => this.updateLocal('tts_voice', e.detail.value)}
          ></eog-input>
        </div>

        <div class="field">
          <label class="field-label">TTS Speed: ${this.config.local.tts_speed.toFixed(1)}x</label>
          <eog-slider
            .value=${this.config.local.tts_speed}
            .min=${0.5}
            .max=${2.0}
            .step=${0.1}
            @change=${(e: CustomEvent) => this.updateLocal('tts_speed', e.detail.value)}
          ></eog-slider>
        </div>

        <div class="field">
          <label class="field-label">VAD Threshold: ${this.config.local.vad_threshold.toFixed(2)}</label>
          <eog-slider
            .value=${this.config.local.vad_threshold}
            .min=${0.0}
            .max=${1.0}
            .step=${0.05}
            @change=${(e: CustomEvent) => this.updateLocal('vad_threshold', e.detail.value)}
          ></eog-slider>
        </div>

        <div class="field">
          <label class="field-label">Language</label>
          <eog-select
            .value=${this.config.local.language}
            .options=${[
              { value: 'en-US', label: 'English (US)' },
              { value: 'en-GB', label: 'English (UK)' },
              { value: 'es-ES', label: 'Spanish' },
              { value: 'fr-FR', label: 'French' },
              { value: 'de-DE', label: 'German' },
              { value: 'ja-JP', label: 'Japanese' },
              { value: 'zh-CN', label: 'Chinese (Simplified)' },
            ]}
            @change=${(e: CustomEvent) => this.updateLocal('language', e.detail.value)}
          ></eog-select>
        </div>
      </div>
    `;
  }

  private renderAgentVoiceBoxSettings() {
    return html`
      <div class="section">
        <div class="section-title">AgentVoiceBox Settings</div>
        
        <div class="field">
          <label class="field-label">Server URL</label>
          <eog-input
            .value=${this.config.agentvoicebox.base_url}
            placeholder="http://localhost:8000"
            @change=${(e: CustomEvent) => this.updateAVB('base_url', e.detail.value)}
          ></eog-input>
        </div>

        <div class="field">
          <label class="field-label">WebSocket URL</label>
          <eog-input
            .value=${this.config.agentvoicebox.ws_url}
            placeholder="ws://localhost:8001/v1/realtime"
            @change=${(e: CustomEvent) => this.updateAVB('ws_url', e.detail.value)}
          ></eog-input>
        </div>

        <div class="field">
          <label class="field-label">API Token</label>
          <eog-input
            type="password"
            .value=${this.config.agentvoicebox.api_token}
            @change=${(e: CustomEvent) => this.updateAVB('api_token', e.detail.value)}
          ></eog-input>
        </div>

        <div class="field">
          <label class="field-label">Model</label>
          <eog-input
            .value=${this.config.agentvoicebox.model}
            @change=${(e: CustomEvent) => this.updateAVB('model', e.detail.value)}
          ></eog-input>
        </div>

        <div class="field">
          <label class="field-label">Voice</label>
          <eog-input
            .value=${this.config.agentvoicebox.voice}
            @change=${(e: CustomEvent) => this.updateAVB('voice', e.detail.value)}
          ></eog-input>
        </div>

        <div class="field">
          <eog-toggle
            .checked=${this.config.agentvoicebox.turn_detection}
            @change=${(e: CustomEvent) => this.updateAVB('turn_detection', e.detail.checked)}
          >Server-side Turn Detection</eog-toggle>
        </div>

        <eog-button
          class="test-button"
          variant="primary"
          ?loading=${this.testing}
          @eog-click=${this.testConnection}
        >Test Connection</eog-button>

        ${this.testResult ? html`
          <div class="test-result ${this.testResult.success ? 'success' : 'error'}">
            ${this.testResult.message}
          </div>
        ` : ''}
      </div>
    `;
  }

  private renderAudioSettings() {
    return html`
      <div class="section">
        <div class="section-title">Audio Settings</div>
        
        <div class="field">
          <label class="field-label">Input Device</label>
          <eog-select
            .value=${String(this.config.audio.input_device)}
            .options=${[{ value: '0', label: 'Default Microphone' }]}
            @change=${(e: CustomEvent) => this.updateAudio('input_device', parseInt(e.detail.value))}
          ></eog-select>
        </div>

        <div class="field">
          <label class="field-label">Output Device</label>
          <eog-select
            .value=${String(this.config.audio.output_device)}
            .options=${[{ value: '0', label: 'Default Speaker' }]}
            @change=${(e: CustomEvent) => this.updateAudio('output_device', parseInt(e.detail.value))}
          ></eog-select>
        </div>

        <div class="field">
          <label class="field-label">Sample Rate</label>
          <eog-select
            .value=${String(this.config.audio.sample_rate)}
            .options=${[
              { value: '16000', label: '16 kHz' },
              { value: '24000', label: '24 kHz (recommended)' },
              { value: '44100', label: '44.1 kHz' },
              { value: '48000', label: '48 kHz' },
            ]}
            @change=${(e: CustomEvent) => this.updateAudio('sample_rate', parseInt(e.detail.value))}
          ></eog-select>
        </div>
      </div>
    `;
  }

  private selectProvider(provider: VoiceProvider) {
    this.config = { ...this.config, provider };
    voiceStore.setProvider(provider);
    this.saveConfig();
  }

  private updateLocal(key: string, value: any) {
    this.config = {
      ...this.config,
      local: { ...this.config.local, [key]: value },
    };
    this.saveConfig();
  }

  private updateAVB(key: string, value: any) {
    this.config = {
      ...this.config,
      agentvoicebox: { ...this.config.agentvoicebox, [key]: value },
    };
    this.saveConfig();
  }

  private updateAudio(key: string, value: any) {
    this.config = {
      ...this.config,
      audio: { ...this.config.audio, [key]: value },
    };
    this.saveConfig();
  }

  private async saveConfig() {
    voiceStore.updateConfig(this.config);
    await fetch('/api/v2/settings/voice', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(this.config),
    });
  }

  private async testConnection() {
    this.testing = true;
    this.testResult = null;
    try {
      const success = await voiceService.testConnection();
      this.testResult = {
        success,
        message: success ? '✓ Connection successful' : '✗ Connection failed',
      };
    } catch (e) {
      this.testResult = { success: false, message: `✗ Error: ${e}` };
    } finally {
      this.testing = false;
    }
  }
}
```

---

## 9. File Structure Summary

```
somaAgent01/ui/
├── backend/                          # Django + Django Ninja
│   ├── eog/                          # Django project
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   ├── api/                          # Django Ninja API
│   │   ├── router.py
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   ├── settings.py
│   │   │   ├── themes.py
│   │   │   ├── modes.py
│   │   │   ├── memory.py
│   │   │   ├── voice.py
│   │   │   └── tools.py
│   │   ├── endpoints/
│   │   │   ├── auth.py
│   │   │   ├── settings.py
│   │   │   ├── themes.py
│   │   │   ├── modes.py
│   │   │   ├── memory.py
│   │   │   ├── voice.py
│   │   │   ├── tools.py
│   │   │   ├── cognitive.py
│   │   │   └── admin.py
│   │   └── middleware/
│   │       ├── tenant.py
│   │       ├── permission.py
│   │       └── audit.py
│   ├── core/                         # Django models
│   │   ├── models/
│   │   │   ├── tenant.py
│   │   │   ├── user.py
│   │   │   ├── settings.py
│   │   │   ├── theme.py
│   │   │   └── audit_log.py
│   │   └── migrations/
│   ├── permissions/                  # SpiceDB
│   │   ├── client.py
│   │   ├── schema.zed
│   │   └── decorators.py
│   ├── realtime/                     # Django Channels
│   │   ├── consumers.py
│   │   ├── routing.py
│   │   └── events.py
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/                         # Lit Web Components
│   ├── src/
│   │   ├── components/               # Reusable components
│   │   │   ├── eog-button.ts
│   │   │   ├── eog-input.ts
│   │   │   ├── eog-select.ts
│   │   │   ├── eog-toggle.ts
│   │   │   ├── eog-slider.ts
│   │   │   ├── eog-modal.ts
│   │   │   ├── eog-toast.ts
│   │   │   ├── eog-card.ts
│   │   │   ├── eog-tabs.ts
│   │   │   ├── eog-spinner.ts
│   │   │   ├── eog-voice-button.ts
│   │   │   └── index.ts
│   │   ├── views/                    # Page components
│   │   │   ├── eog-app.ts
│   │   │   ├── eog-chat-view.ts
│   │   │   ├── eog-settings-view.ts
│   │   │   ├── eog-voice-settings.ts
│   │   │   ├── eog-themes-view.ts
│   │   │   ├── eog-memory-view.ts
│   │   │   ├── eog-tools-view.ts
│   │   │   ├── eog-cognitive-view.ts
│   │   │   ├── eog-admin-view.ts
│   │   │   └── eog-audit-view.ts
│   │   ├── stores/                   # State management
│   │   │   ├── auth-store.ts
│   │   │   ├── mode-store.ts
│   │   │   ├── theme-store.ts
│   │   │   ├── permission-store.ts
│   │   │   ├── voice-store.ts
│   │   │   ├── settings-store.ts
│   │   │   ├── chat-store.ts
│   │   │   └── memory-store.ts
│   │   ├── services/                 # API clients
│   │   │   ├── api-client.ts
│   │   │   ├── websocket-client.ts
│   │   │   ├── auth-service.ts
│   │   │   ├── settings-service.ts
│   │   │   ├── theme-service.ts
│   │   │   ├── voice-service.ts
│   │   │   └── permission-service.ts
│   │   ├── styles/                   # Global styles
│   │   │   ├── tokens.css
│   │   │   ├── reset.css
│   │   │   ├── agentskin-bridge.css
│   │   │   └── themes/
│   │   │       ├── default-light.json
│   │   │       ├── midnight-dark.json
│   │   │       └── high-contrast.json
│   │   ├── utils/                    # Utilities
│   │   │   ├── validators.ts
│   │   │   ├── formatters.ts
│   │   │   ├── theme-loader.ts
│   │   │   └── constants.ts
│   │   ├── index.ts
│   │   └── sw.ts                     # Service Worker
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── web-test-runner.config.js
│
└── docker/
    ├── Dockerfile.backend
    ├── Dockerfile.frontend
    └── docker-compose.yml
```

---

## 10. Implementation Checklist

### Phase 1: Foundation (Week 1-2)
- [ ] Django project setup with Django Ninja
- [ ] SpiceDB schema and client
- [ ] Lit project setup with Vite
- [ ] Base components (button, input, select, toggle)
- [ ] Auth store and service
- [ ] WebSocket client

### Phase 2: Core Features (Week 3-4)
- [ ] Mode store and selector
- [ ] Theme store and AgentSkin integration
- [ ] Settings views (all tabs)
- [ ] Permission store and decorators
- [ ] Chat view with streaming

### Phase 3: Voice Integration (Week 5-6)
- [ ] Voice store implementation
- [ ] Local voice service (Whisper + Kokoro)
- [ ] AgentVoiceBox integration
- [ ] Voice settings UI
- [ ] Voice button and overlay

### Phase 4: Advanced Features (Week 7-8)
- [ ] Memory view with virtual scrolling
- [ ] Cognitive panel (neuromodulators)
- [ ] Admin dashboard
- [ ] Audit log viewer
- [ ] Tool catalog

### Phase 5: Optimization (Week 9-10)
- [ ] Service worker caching
- [ ] Code splitting optimization
- [ ] Performance testing (1M connections)
- [ ] Accessibility audit (WCAG AA)
- [ ] Security audit

---

**Document Status:** COMPLETE

**Next Steps:**
1. Create `tasks.md` with detailed implementation tasks
2. Begin Phase 1 implementation
3. Set up CI/CD pipeline for parallel build
# SomaAgent SaaS — UI Screens SRS

**Document ID:** SA01-UI-SCREENS-SRS-2025-12  
**Version:** 1.0  
**Date:** 2025-12-22  
**Status:** CANONICAL  
**Classification:** ENTERPRISE  
**Compliance:** ISO/IEC/IEEE 29148:2018

---

## Document Control

| Field | Value |
|-------|-------|
| Author | SomaAgent Development Team |
| Approvers | Technical Lead, Product Owner |
| Supersedes | SA01-EOG-UI-ARCH-2025-12 (partial) |

---

## 1. Introduction

### 1.1 Purpose

This document specifies EVERY screen in the SomaAgent SaaS platform with:
- Detailed wireframes and component breakdown
- UML sequence diagrams for user interactions
- State diagrams for complex flows
- API endpoints consumed
- Validation rules
- Accessibility requirements

### 1.2 Scope

**Screens Covered:**
1. Authentication (Login, Register, Forgot Password, Auth Callback)
2. Mode Selection (God Mode users)
3. Platform Admin (Dashboard, Tenants, Billing, Subscriptions)
4. Tenant Admin (Users, Agents, Roles)
5. Core App (Chat, Memory, Tools, Cognitive, Settings)
6. Audit & Security (Audit Log, Security Settings)

---

## 2. Global Navigation

### 2.1 Sidebar Navigation

```
┌────────────────────────────────────────┐
│  [Logo] SomaAgent                      │
│  ◄ ►  (collapse toggle)               │
├────────────────────────────────────────┤
│  STD  TRN  ADM  DEV  RO  (mode tabs)  │
├────────────────────────────────────────┤
│  🔍 Search...                          │
├────────────────────────────────────────┤
│  CORE                                  │
│  💬 Chat                               │
│  📄 Documents              [12]        │
│  🧠 Memory                 [1.2K]      │
├────────────────────────────────────────┤
│  TOOLS                                 │
│  🔧 Tool Catalog           [24]        │
│  🔌 MCP Servers                        │
│  🧬 Cognitive                          │
├────────────────────────────────────────┤
│  PLATFORM                              │
│  📊 Dashboard                          │
│  🏢 Tenants                [5]         │
│  💳 Billing                            │
├────────────────────────────────────────┤
│  ADMIN                                 │
│  👥 Users                  [8]         │
│  🎭 Roles                              │
│  🖥️ Servers                            │
│  📦 Models                             │
├────────────────────────────────────────┤
│  SYSTEM                                │
│  ⚙️ Settings                           │
│  🎨 Themes                             │
│  📋 Audit Log                          │
├────────────────────────────────────────┤
│  [Avatar] SomaAgent                    │
│  Admin • Online                        │
└────────────────────────────────────────┘
```

### 2.2 Top Header

```
┌────────────────────────────────────────────────────────────────────┐
│  🔍 Search                      ⌘ K  │  ❓ Help Center  │ [Avatar] │
└────────────────────────────────────────────────────────────────────┘
```

---

## 3. Authentication Screens

### 3.1 Login Screen

**Route:** `/login`  
**Component:** `saas-login.ts`  
**Permission:** Public

#### 3.1.1 Wireframe

```
┌─────────────────────────────────────────────────────────────────┐
│                          (Page: #f5f5f5)                        │
│                                                                 │
│                    ┌─────────────────────────┐                  │
│                    │     (Card: #ffffff)     │                  │
│                    │                         │                  │
│                    │  ┌───┐ SomaAgent SaaS   │                  │
│                    │  │█▀█│  Admin           │                  │
│                    │  └───┘                  │                  │
│                    │                         │                  │
│                    │  Sign in                │                  │
│                    │  Don't have account?   │                  │
│                    │  [Get started]          │                  │
│                    │                         │                  │
│                    │  ┌─────────────────────┐│                  │
│                    │  │ 🔵 Continue with    ││                  │
│                    │  │    Google           ││                  │
│                    │  └─────────────────────┘│                  │
│                    │                         │                  │
│                    │  ┌─────────────────────┐│                  │
│                    │  │ 🔒 Enterprise SSO   ││                  │
│                    │  └─────────────────────┘│                  │
│                    │                         │                  │
│                    │  ──────── or ────────   │                  │
│                    │                         │                  │
│                    │  Email                  │                  │
│                    │  ┌─────────────────────┐│                  │
│                    │  │ name@company.com    ││                  │
│                    │  └─────────────────────┘│                  │
│                    │                         │                  │
│                    │  Password      [Forgot?]│                  │
│                    │  ┌─────────────────────┐│                  │
│                    │  │ ••••••••            ││                  │
│                    │  └─────────────────────┘│                  │
│                    │                         │                  │
│                    │  ☐ Remember me          │                  │
│                    │                         │                  │
│                    │  ┌─────────────────────┐│                  │
│                    │  │      Sign in        ││ (black btn)     │
│                    │  └─────────────────────┘│                  │
│                    │                         │                  │
│                    │  ─────────────────────  │                  │
│                    │  Powered by SomaTech   │                  │
│                    │                         │                  │
│                    └─────────────────────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.1.2 Component Breakdown

| Element | Type | CSS Class | Behavior |
|---------|------|-----------|----------|
| Brand Logo | `<div>` | `.brand-icon` | 40x40px black box with grid icon |
| Brand Name | `<span>` | `.brand-name` | 18px semibold text |
| Title | `<h2>` | `.form-title` | 22px semibold "Sign in" |
| Subtitle | `<p>` | `.form-subtitle` | 14px with link to register |
| Google Button | `<button>` | `.oauth-btn` | Opens Google OAuth popup |
| SSO Button | `<button>` | `.oauth-btn` | Opens Keycloak SSO |
| Divider | `<div>` | `.divider` | "or" with lines |
| Email Input | `<input type="email">` | `.form-input` | Required, autocomplete="email" |
| Password Input | `<input type="password">` | `.form-input` | Required, min 8 chars |
| Remember Checkbox | `<input type="checkbox">` | `.remember-row` | Stores preference |
| Submit Button | `<button type="submit">` | `.submit-btn` | Black, loading state |
| Error Message | `<div>` | `.error-message` | Red background, 1px border |

#### 3.1.3 Sequence Diagram - Email Login

```mermaid
sequenceDiagram
    actor User
    participant Login as saas-login
    participant AuthStore
    participant API as /api/v2/auth/login
    participant SpiceDB
    participant DB as PostgreSQL

    User->>Login: Enter email + password
    User->>Login: Click "Sign in"
    Login->>Login: Validate form (email format, password length)
    alt Validation fails
        Login-->>User: Show inline error
    end
    Login->>AuthStore: login(email, password)
    AuthStore->>API: POST {email, password}
    API->>DB: SELECT user WHERE email
    alt User not found
        API-->>AuthStore: 401 Invalid credentials
        AuthStore-->>Login: error
        Login-->>User: Show error message
    end
    API->>API: bcrypt.compare(password, hash)
    alt Password invalid
        API-->>AuthStore: 401 Invalid credentials
    end
    API->>SpiceDB: Check user roles
    SpiceDB-->>API: roles[]
    API->>DB: INSERT session
    API-->>AuthStore: {token, user, redirect_path}
    AuthStore->>AuthStore: Store token in localStorage
    AuthStore-->>Login: success
    alt user.is_saas_admin
        Login->>Login: Router.go('/mode-select')
    else tenant_admin
        Login->>Login: Router.go('/admin')
    else regular_user
        Login->>Login: Router.go('/chat')
    end
```

#### 3.1.4 Sequence Diagram - Google OAuth

```mermaid
sequenceDiagram
    actor User
    participant Login as saas-login
    participant GoogleAuth as GoogleAuthService
    participant Google as accounts.google.com
    participant Callback as saas-auth-callback
    participant API as /api/v2/auth/google/callback
    participant DB as PostgreSQL

    User->>Login: Click "Continue with Google"
    Login->>GoogleAuth: getAuthUrl()
    GoogleAuth->>GoogleAuth: Generate state + nonce
    GoogleAuth->>GoogleAuth: Store in sessionStorage
    GoogleAuth-->>Login: https://accounts.google.com/o/oauth2/v2/auth?...
    Login->>Google: window.location.href = authUrl
    Note over Google: User authenticates with Google
    Google-->>Callback: Redirect to /auth/callback?code=xxx&state=yyy
    Callback->>GoogleAuth: parseCallback(url)
    Callback->>GoogleAuth: verifyState(state)
    alt State mismatch
        Callback-->>User: "Security error - possible CSRF"
    end
    Callback->>API: POST {code, redirect_uri}
    API->>Google: Exchange code for tokens
    Google-->>API: {access_token, id_token, refresh_token}
    API->>Google: GET /userinfo
    Google-->>API: {email, name, picture}
    API->>DB: UPSERT user WHERE email
    API->>DB: INSERT session
    API-->>Callback: {access_token, user, redirect_path}
    Callback->>Callback: localStorage.setItem('saas_auth_token', token)
    Callback->>Callback: Router.go(redirect_path)
```

#### 3.1.5 State Diagram - Login Form

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Validating: Submit clicked
    Validating --> Error: Validation failed
    Error --> Idle: User fixes input
    Validating --> Loading: Validation passed
    Loading --> Success: API returns 200
    Loading --> Error: API returns 4xx/5xx
    Success --> Redirecting: Store token
    Redirecting --> [*]: Navigate to app
```

#### 3.1.6 API Endpoints

| Endpoint | Method | Request | Response |
|----------|--------|---------|----------|
| `/api/v2/auth/login` | POST | `{email, password}` | `{token, user, redirect_path}` |
| `/api/v2/auth/google/callback` | POST | `{code, redirect_uri}` | `{token, user, redirect_path}` |

#### 3.1.7 Validation Rules

| Field | Rules |
|-------|-------|
| Email | Required, valid email format |
| Password | Required, min 8 chars |

#### 3.1.8 Accessibility

- All inputs have associated labels
- Focus order: Google → SSO → Email → Password → Remember → Submit
- Error messages linked with `aria-describedby`
- Submit button shows loading state with `aria-busy`

---

### 3.2 Register Screen

**Route:** `/register`  
**Component:** `saas-register.ts`  
**Permission:** Public

#### 3.2.1 Wireframe

```
┌─────────────────────────────────────────────────────────────────┐
│                          (Page: #f5f5f5)                        │
│                                                                 │
│                    ┌─────────────────────────┐                  │
│                    │     (Card: #ffffff)     │                  │
│                    │                         │                  │
│                    │  ┌───┐ SomaAgent SaaS   │                  │
│                    │  │█▀█│  Admin           │                  │
│                    │  └───┘                  │                  │
│                    │                         │                  │
│                    │  Create account         │                  │
│                    │  Already have account? │                  │
│                    │  [Sign in]              │                  │
│                    │                         │                  │
│                    │  ┌─────────────────────┐│                  │
│                    │  │ 🔵 Continue with    ││                  │
│                    │  │    Google           ││                  │
│                    │  └─────────────────────┘│                  │
│                    │                         │                  │
│                    │  ──────── or ────────   │                  │
│                    │                         │                  │
│                    │  Full Name              │                  │
│                    │  ┌─────────────────────┐│                  │
│                    │  │ John Doe            ││                  │
│                    │  └─────────────────────┘│                  │
│                    │                         │                  │
│                    │  Work Email             │                  │
│                    │  ┌─────────────────────┐│                  │
│                    │  │ name@company.com    ││                  │
│                    │  └─────────────────────┘│                  │
│                    │                         │                  │
│                    │  Password               │                  │
│                    │  ┌─────────────────────┐│                  │
│                    │  │ ••••••••            ││                  │
│                    │  └─────────────────────┘│                  │
│                    │  (min 8 chars)          │                  │
│                    │                         │                  │
│                    │  ☐ I agree to Terms    │                  │
│                    │    and Privacy Policy   │                  │
│                    │                         │                  │
│                    │  ┌─────────────────────┐│                  │
│                    │  │   Create account    ││                  │
│                    │  └─────────────────────┘│                  │
│                    │                         │                  │
│                    └─────────────────────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.2.2 Component Breakdown

| Element | Type | Validation |
|---------|------|------------|
| Full Name | `<input type="text">` | Required, min 2 chars |
| Work Email | `<input type="email">` | Required, valid email, unique |
| Password | `<input type="password">` | Required, min 8 chars, 1 uppercase, 1 number |
| Terms Checkbox | `<input type="checkbox">` | Required to be checked |
| Submit Button | `<button type="submit">` | Disabled until terms checked |

#### 3.2.3 Sequence Diagram - Registration

```mermaid
sequenceDiagram
    actor User
    participant Register as saas-register
    participant API as /api/v2/auth/register
    participant DB as PostgreSQL
    participant Email as EmailService

    User->>Register: Fill form + submit
    Register->>Register: Validate all fields
    Register->>API: POST {name, email, password}
    API->>DB: Check email uniqueness
    alt Email exists
        API-->>Register: 409 Email already registered
        Register-->>User: Show error
    end
    API->>API: bcrypt.hash(password)
    API->>DB: INSERT user (pending verification)
    API->>Email: Send verification email
    API-->>Register: 201 Created
    Register-->>User: Show "Check your email"
```

#### 3.2.4 API Endpoints

| Endpoint | Method | Request | Response |
|----------|--------|---------|----------|
| `/api/v2/auth/register` | POST | `{name, email, password}` | `{message: "Verification email sent"}` |
| `/api/v2/auth/verify-email` | POST | `{token}` | `{token, user}` |

---

### 3.3 Forgot Password Screen

**Route:** `/forgot-password`  
**Component:** `saas-forgot-password.ts`  
**Permission:** Public

#### 3.3.1 Wireframe

```
┌─────────────────────────────────────────────────────────────────┐
│                          (Page: #f5f5f5)                        │
│                                                                 │
│                    ┌─────────────────────────┐                  │
│                    │     (Card: #ffffff)     │                  │
│                    │                         │                  │
│                    │  ┌───┐ SomaAgent SaaS   │                  │
│                    │  │█▀█│  Admin           │                  │
│                    │  └───┘                  │                  │
│                    │                         │                  │
│                    │  Reset password         │                  │
│                    │  Enter your email and   │                  │
│                    │  we'll send reset link  │                  │
│                    │                         │                  │
│                    │  Email                  │                  │
│                    │  ┌─────────────────────┐│                  │
│                    │  │ name@company.com    ││                  │
│                    │  └─────────────────────┘│                  │
│                    │                         │                  │
│                    │  ┌─────────────────────┐│                  │
│                    │  │   Send reset link   ││                  │
│                    │  └─────────────────────┘│                  │
│                    │                         │                  │
│                    │  ← Back to login        │                  │
│                    │                         │                  │
│                    └─────────────────────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.3.2 Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant ForgotPW as saas-forgot-password
    participant API as /api/v2/auth/forgot-password
    participant DB as PostgreSQL
    participant Email as EmailService

    User->>ForgotPW: Enter email + submit
    ForgotPW->>API: POST {email}
    API->>DB: Find user by email
    Note over API: Always return success (security)
    API->>Email: Send reset email (if user exists)
    API-->>ForgotPW: 200 OK
    ForgotPW-->>User: "Check your email"
```

---

### 3.4 Auth Callback Screen

**Route:** `/auth/callback`  
**Component:** `saas-auth-callback.ts`  
**Permission:** Public

#### 3.4.1 Wireframe

```
┌─────────────────────────────────────────────────────────────────┐
│                          (Page: #f5f5f5)                        │
│                                                                 │
│                                                                 │
│                         ┌──────────┐                            │
│                         │  ◠◡◠    │ (spinning)                 │
│                         └──────────┘                            │
│                                                                 │
│                   Processing authentication...                   │
│                   Please wait while we complete                 │
│                   your sign-in                                  │
│                                                                 │
│   [Error state:]                                                │
│                         Authentication Failed                    │
│                   ┌─────────────────────────┐                   │
│                   │ Invalid state parameter │                   │
│                   └─────────────────────────┘                   │
│                   [Return to Login]                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.4.2 State Diagram

```mermaid
stateDiagram-v2
    [*] --> Detecting: Page loads
    Detecting --> ProcessingGoogle: Google state found
    Detecting --> ProcessingKeycloak: Keycloak state found
    Detecting --> Error: No state found
    
    ProcessingGoogle --> ExchangingCode: State valid
    ProcessingGoogle --> Error: State mismatch
    
    ProcessingKeycloak --> ExchangingCode: State valid
    ProcessingKeycloak --> Error: State mismatch
    
    ExchangingCode --> StoringToken: Code exchange success
    ExchangingCode --> Error: Code exchange failed
    
    StoringToken --> Redirecting: Token stored
    Redirecting --> [*]: Navigate to app
    
    Error --> [*]: User clicks retry
```

---

## 4. Mode Selection Screen

**Route:** `/mode-select`  
**Component:** `saas-mode-selection.ts`  
**Permission:** `saas_admin` only

### 4.1 Wireframe

```
┌─────────────────────────────────────────────────────────────────┐
│                   (Page: Dark #0f172a gradient)                 │
│                                                                 │
│                   Select Interface Mode                         │
│                   Access your specialized workspace             │
│                                                                 │
│   ┌─────────────────────────────┐  ┌─────────────────────────── │
│   │  ⚡ God Mode                │  │  🏢 Tenant Viewer          │
│   │     [SUPER ADMIN]           │  │     [STANDARD VIEW]        │
│   ├─────────────────────────────┤  ├─────────────────────────── │
│   │  Full infrastructure        │  │  Focused workspace for     │
│   │  control, multi-tenant      │  │  agent management and      │
│   │  oversight, and system-     │  │  conversation flows.       │
│   │  wide configuration.        │  │                            │
│   ├─────────────────────────────┤  ├─────────────────────────── │
│   │  Tenants    │  Agents       │  │  Last Viewed │  Role       │
│   │  124        │  4502         │  │  Acme Corp   │  Owner      │
│   │  Uptime     │  Alerts       │  │  Agents      │  Events     │
│   │  99.9%      │  2            │  │  5           │  12         │
│   ├─────────────────────────────┤  ├─────────────────────────── │
│   │  Access: Tier 0 (Root)      │  │  Context: Single Tenant    │
│   │          Configure System → │  │          Enter Workspace → │
│   └─────────────────────────────┘  └─────────────────────────── │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant ModeSelect as saas-mode-selection
    participant API as /api/v2/saas/stats
    participant Session as SessionService

    User->>ModeSelect: Page loads
    ModeSelect->>API: GET platform stats
    API-->>ModeSelect: {tenants, agents, health, alerts}
    ModeSelect->>ModeSelect: Display stats in cards
    
    User->>ModeSelect: Click "God Mode"
    ModeSelect->>ModeSelect: Show confirmation modal
    User->>ModeSelect: Confirm
    ModeSelect->>Session: setEntryMode('platform')
    ModeSelect->>ModeSelect: Router.go('/platform')
    
    Note over User,ModeSelect: OR
    
    User->>ModeSelect: Click "Tenant Viewer"
    ModeSelect->>ModeSelect: Show tenant picker modal
    User->>ModeSelect: Select tenant
    ModeSelect->>Session: setEntryMode('tenant', tenantId)
    ModeSelect->>ModeSelect: Router.go('/dashboard')
```

---

## 5. Platform Admin Screens (God Mode)

### 5.1 Platform Dashboard

**Route:** `/platform`  
**Component:** `saas-platform-dashboard.ts`  
**Permission:** `saas_admin`

#### 5.1.1 Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │  Platform Dashboard                          [Brian F. ▼]     │
│            │─────────────────────────────────────────────────────────────────│
│ CORE       │                                                                 │
│ 💬 Chat    │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│ 📄 Docs    │  │  124    │  │  4,502  │  │ $24.5K  │  │  99.9%  │           │
│ 🧠 Memory  │  │ Tenants │  │ Agents  │  │   MRR   │  │ Uptime  │           │
│            │  └─────────┘  └─────────┘  └─────────┘  └─────────┘           │
│ PLATFORM   │                                                                 │
│ 📊 Dashboard│  Revenue Overview                              [This Month ▼] │
│ 🏢 Tenants │  ┌─────────────────────────────────────────────────────────┐   │
│ 💳 Billing │  │                    📈 Revenue Chart                     │   │
│            │  │     $30K ─────────────────────────┐                     │   │
│ ADMIN      │  │     $20K ───────────────┐        │                     │   │
│ 👥 Users   │  │     $10K ─────┐         │        │                     │   │
│ 🎭 Roles   │  │           Jan  Feb  Mar  Apr  May                       │   │
│            │  └─────────────────────────────────────────────────────────┘   │
│ SYSTEM     │                                                                 │
│ ⚙️ Settings │  Recent Activity                                               │
│ 📋 Audit   │  ┌─────────────────────────────────────────────────────────┐   │
│            │  │ 🟢 Acme Corp        New tenant created      2 min ago   │   │
│ [Avatar]   │  │ 🟡 Globex Inc       Quota warning 80%       15 min ago  │   │
│ SomaAgent  │  │ 🔵 TechStart        Agent deployed          1 hour ago  │   │
│ Admin      │  │ 🟢 DataFlow         Subscription upgraded   2 hours ago │   │
│            │  └─────────────────────────────────────────────────────────┘   │
└─────────────┴───────────────────────────────────────────────────────────────┘
```

#### 5.1.2 Component Breakdown

| Section | Component | Data Source |
|---------|-----------|-------------|
| Stat Cards | `saas-stat-card` × 4 | `GET /api/v2/saas/stats` |
| Revenue Chart | `saas-revenue-chart` | `GET /api/v2/saas/billing/revenue` |
| Activity Feed | `saas-activity-feed` | `GET /api/v2/saas/activity` |
| Health Status | `saas-health-card` | `GET /api/v2/saas/health` |

#### 5.1.3 API Endpoints

| Endpoint | Response |
|----------|----------|
| `GET /api/v2/saas/stats` | `{tenants, agents, mrr, uptime}` |
| `GET /api/v2/saas/billing/revenue` | `{monthly: [{month, revenue}]}` |
| `GET /api/v2/saas/activity` | `{items: [{id, type, tenant, message, time}]}` |

---

### 5.2 Tenant Management

**Route:** `/platform/tenants`  
**Component:** `saas-tenants.ts`  
**Permission:** `saas_admin->manage_tenants`

#### 5.2.1 Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │  Tenants                                  [+ Create Tenant]    │
│            │─────────────────────────────────────────────────────────────────│
│            │  🔍 Search tenants...          [Status ▼] [Tier ▼] [Sort ▼]    │
│            │                                                                 │
│            │  ┌───────────────────────────────────────────────────────────┐ │
│            │  │ Name          │ Status  │ Tier      │ Agents │ Created    │ │
│            │  ├───────────────────────────────────────────────────────────┤ │
│            │  │ Acme Corp     │ 🟢 Active│ Enterprise│ 45     │ Dec 1, 24  │ │
│            │  │ Globex Inc    │ 🟢 Active│ Team      │ 12     │ Nov 15, 24 │ │
│            │  │ TechStart     │ 🟡 Pend. │ Starter   │ 3      │ Dec 20, 24 │ │
│            │  │ DataFlow      │ 🔴 Susp. │ Free      │ 1      │ Oct 5, 24  │ │
│            │  └───────────────────────────────────────────────────────────┘ │
│            │                                                                 │
│            │  Showing 1-4 of 124 tenants              [← 1 2 3 ... 32 →]   │
│            │                                                                 │
└─────────────┴───────────────────────────────────────────────────────────────┘
```

#### 5.2.2 Row Actions

| Action | Icon | Permission | Behavior |
|--------|------|------------|----------|
| View Details | 👁️ | `view` | Opens tenant detail panel |
| Edit | ✏️ | `manage_tenants` | Opens edit modal |
| Enter Tenant | ➡️ | `manage_tenants` | Impersonate as tenant admin |
| Suspend | ⏸️ | `manage_tenants` | Sets status to suspended |
| Delete | 🗑️ | `manage_tenants` | Soft delete with confirmation |

#### 5.2.3 Create Tenant Modal

```
┌────────────────────────────────────────────┐
│  Create Tenant                         ✕   │
├────────────────────────────────────────────┤
│                                            │
│  Organization Name *                       │
│  ┌────────────────────────────────────┐   │
│  │ Acme Corporation                   │   │
│  └────────────────────────────────────┘   │
│                                            │
│  Slug (URL identifier) *                   │
│  ┌────────────────────────────────────┐   │
│  │ acme-corp                          │   │
│  └────────────────────────────────────┘   │
│  Will be: app.somaagent.io/acme-corp       │
│                                            │
│  Owner Email *                             │
│  ┌────────────────────────────────────┐   │
│  │ admin@acme.com                     │   │
│  └────────────────────────────────────┘   │
│                                            │
│  Subscription Tier                         │
│  ┌────────────────────────────────────┐   │
│  │ Starter ($49/mo)              ▼   │   │
│  └────────────────────────────────────┘   │
│                                            │
├────────────────────────────────────────────┤
│  [Cancel]                    [Create]      │
└────────────────────────────────────────────┘
```

#### 5.2.4 Sequence Diagram - Create Tenant

```mermaid
sequenceDiagram
    actor Admin
    participant UI as saas-tenants
    participant API as /api/v2/saas/tenants
    participant SpiceDB
    participant Lago as Lago Billing
    participant DB as PostgreSQL

    Admin->>UI: Click "Create Tenant"
    UI->>UI: Show modal
    Admin->>UI: Fill form + submit
    UI->>API: POST {name, slug, owner_email, tier}
    API->>DB: Check slug uniqueness
    alt Slug exists
        API-->>UI: 409 Slug already taken
    end
    API->>DB: INSERT tenant
    API->>SpiceDB: Create tenant relations
    API->>Lago: Create Lago customer
    API->>Lago: Create subscription
    API-->>UI: 201 Created {tenant}
    UI->>UI: Add to list, close modal
```

---

### 5.3 Billing Dashboard

**Route:** `/platform/billing`  
**Component:** `saas-billing.ts`  
**Permission:** `saas_admin->view_billing`

#### 5.3.1 Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │  Billing & Revenue                              [This Year ▼] │
│            │─────────────────────────────────────────────────────────────────│
│            │                                                                 │
│            │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│            │  │ $24.5K  │  │  $2.1K  │  │   87    │  │   12    │           │
│            │  │   MRR   │  │  ARPU   │  │ Paying  │  │  Churn  │           │
│            │  │ ↑ 12%   │  │ ↑ 5%    │  │ ↑ 8     │  │ ↓ 3     │           │
│            │  └─────────┘  └─────────┘  └─────────┘  └─────────┘           │
│            │                                                                 │
│            │  Revenue by Tier                    Subscription Distribution   │
│            │  ┌────────────────────────┐        ┌────────────────────────┐ │
│            │  │ Enterprise ████████ 45%│        │    🟢 Enterprise 45%   │ │
│            │  │ Team       █████   32% │        │    🔵 Team 32%         │ │
│            │  │ Starter    ███     18% │        │    🟡 Starter 18%      │ │
│            │  │ Free       █       5%  │        │    ⚪ Free 5%          │ │
│            │  └────────────────────────┘        └────────────────────────┘ │
│            │                                                                 │
│            │  Recent Invoices                                [View All →]   │
│            │  ┌───────────────────────────────────────────────────────────┐ │
│            │  │ Invoice     │ Tenant      │ Amount  │ Status  │ Date      │ │
│            │  │ INV-2024-12 │ Acme Corp   │ $499    │ 🟢 Paid │ Dec 1     │ │
│            │  │ INV-2024-11 │ Globex      │ $199    │ 🟢 Paid │ Dec 1     │ │
│            │  │ INV-2024-10 │ TechStart   │ $49     │ 🟡 Pend │ Dec 1     │ │
│            │  └───────────────────────────────────────────────────────────┘ │
└─────────────┴───────────────────────────────────────────────────────────────┘
```

#### 5.3.2 API Endpoints (Lago Integration)

| Endpoint | Lago API | Purpose |
|----------|----------|---------|
| `GET /api/v2/saas/billing/metrics` | `GET /analytics` | MRR, ARPU, churn |
| `GET /api/v2/saas/billing/revenue` | `GET /analytics/mrr` | Revenue by tier |
| `GET /api/v2/saas/billing/invoices` | `GET /invoices` | Invoice list |
| `GET /api/v2/saas/billing/subscriptions` | `GET /subscriptions` | Subscription breakdown |

---

## 6. Tenant Admin Screens

### 6.1 User Management

**Route:** `/admin/users`  
**Component:** `saas-users.ts`  
**Permission:** `tenant->administrate`

#### 6.1.1 Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │  Users                                     [+ Invite User]     │
│            │─────────────────────────────────────────────────────────────────│
│            │  🔍 Search users...                    [Role ▼] [Status ▼]     │
│            │                                                                 │
│            │  ┌───────────────────────────────────────────────────────────┐ │
│            │  │ User              │ Email              │ Role     │Status │ │
│            │  ├───────────────────────────────────────────────────────────┤ │
│            │  │ 👤 John Smith     │ john@acme.com      │ SysAdmin │🟢 Active│ │
│            │  │ 👤 Jane Doe       │ jane@acme.com      │ Admin    │🟢 Active│ │
│            │  │ 👤 Bob Wilson     │ bob@acme.com       │ Developer│🟢 Active│ │
│            │  │ 👤 Alice Chen     │ alice@acme.com     │ Trainer  │🟡 Pending│ │
│            │  │ 👤 Mike Brown     │ mike@acme.com      │ User     │🟢 Active│ │
│            │  └───────────────────────────────────────────────────────────┘ │
│            │                                                                 │
└─────────────┴───────────────────────────────────────────────────────────────┘
```

#### 6.1.2 Invite User Modal

```
┌────────────────────────────────────────────┐
│  Invite User                           ✕   │
├────────────────────────────────────────────┤
│                                            │
│  Email Address *                           │
│  ┌────────────────────────────────────┐   │
│  │ user@example.com                   │   │
│  └────────────────────────────────────┘   │
│                                            │
│  Role *                                    │
│  ┌────────────────────────────────────┐   │
│  │ Developer                     ▼   │   │
│  └────────────────────────────────────┘   │
│                                            │
│  Role Description                          │
│  ┌────────────────────────────────────┐   │
│  │ Can access DEV mode, debug tools,  │   │
│  │ and develop modules/integrations.  │   │
│  └────────────────────────────────────┘   │
│                                            │
├────────────────────────────────────────────┤
│  [Cancel]               [Send Invite]      │
└────────────────────────────────────────────┘
```

#### 6.1.3 Role Definitions

| Role | Code | Permissions |
|------|------|-------------|
| SysAdmin | `sysadmin` | Full tenant control, delete agents, billing access |
| Admin | `admin` | Manage users, configure agents, view audit |
| Developer | `developer` | DEV mode, debugging, module SDK |
| Trainer | `trainer` | TRN mode, cognitive parameters |
| User | `member` | STD mode, chat, memory, tools |
| Viewer | `viewer` | RO mode, read-only access |

---

### 6.2 Agent Management

**Route:** `/admin/agents`  
**Component:** `saas-agents.ts`  
**Permission:** `tenant->create_agent`

#### 6.2.1 Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │  Agents                                    [+ Create Agent]    │
│            │─────────────────────────────────────────────────────────────────│
│            │  Using 5 of 10 agents (Team plan)                              │
│            │  ████████░░░░░░░░░░░░                                          │
│            │                                                                 │
│            │  ┌─────────────────────┐  ┌─────────────────────┐              │
│            │  │ SomaAgent-Prod      │  │ SomaAgent-Dev       │              │
│            │  │ 🟢 Running          │  │ 🟡 Stopped          │              │
│            │  │ Chat: GPT-4o        │  │ Chat: Claude-3      │              │
│            │  │ Memory: ✓ Enabled   │  │ Memory: ✓ Enabled   │              │
│            │  │ Voice: ✓ Enabled    │  │ Voice: ✗ Disabled   │              │
│            │  │ Sessions: 1.2K      │  │ Sessions: 45        │              │
│            │  ├─────────────────────┤  ├─────────────────────┤              │
│            │  │ [Configure] [Stop]  │  │ [Configure] [Start] │              │
│            │  └─────────────────────┘  └─────────────────────┘              │
│            │                                                                 │
└─────────────┴───────────────────────────────────────────────────────────────┘
```

#### 6.2.2 Quota Enforcement

```mermaid
sequenceDiagram
    actor Admin as Tenant Admin
    participant UI as saas-agents
    participant API as /api/v2/admin/agents
    participant Quota as QuotaService
    participant DB as PostgreSQL

    Admin->>UI: Click "Create Agent"
    UI->>API: POST {name, slug, config}
    API->>Quota: checkQuota(tenant_id, 'agents')
    Quota->>DB: SELECT COUNT(*) FROM agents WHERE tenant_id
    Quota->>DB: SELECT max_agents FROM subscription_tiers
    alt quota_used >= max_agents
        Quota-->>API: QuotaExceededError
        API-->>UI: 402 Quota exceeded
        UI-->>Admin: Show upgrade modal
    end
    API->>DB: INSERT agent
    API-->>UI: 201 Created
```

---

## 7. Core App Screens

### 7.1 Chat View

**Route:** `/chat`  
**Component:** `saas-chat.ts`  
**Permission:** `tenant->use`

#### 7.1.1 Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │  💬 AI Chat                                  [+ New Chat]      │
│            │─────────────────────────────────────────────────────────────────│
│            │                                                                 │
│            │                            You  2 min ago                       │
│            │                     ┌────────────────────────────┐              │
│            │                     │ 🎵 ▶ ●●●|||●●●||●●● 0:23 │              │
│            │                     └────────────────────────────┘              │
│            │                                                                 │
│            │   Eye of God  1 min ago                                         │
│            │   ┌────────────────────────────────────────────────────────┐   │
│            │   │ 🎵 ▶ ●●●|||●●●|||●●●||● 0:45                          │   │
│            │   └────────────────────────────────────────────────────────┘   │
│            │   Generating transcript...                                      │
│            │                                                                 │
│            │                            You  30 sec ago                      │
│            │                     ┌────────────────────────────┐              │
│            │                     │ What's the current status  │              │
│            │                     │ of the server configuration?│              │
│            │                     └────────────────────────────┘              │
│            │                                                                 │
│            │   Eye of God  Just now                                          │
│            │   ┌────────────────────────────────────────────────────────┐   │
│            │   │ ● ● ●                                                  │   │
│            │   └────────────────────────────────────────────────────────┘   │
│            │                                                                 │
│            │─────────────────────────────────────────────────────────────────│
│            │  🔍 Find in...  ▼                                               │
│            │  ┌───────────────────────────────────────────────────────────┐ │
│            │  │ + │ Write message...                       │ 🎤 │ ▲ │    │ │
│            │  └───────────────────────────────────────────────────────────┘ │
│            │  AI can make mistakes. Check important info.                   │
└─────────────┴───────────────────────────────────────────────────────────────┘
```

#### 7.1.2 Chat Input Component

```
┌─────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Write message...                                        │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  [ + ]  [ ⚙ Tools ]  [ ✏ Normal ]           [ 🎤 Voice ]  [ ▲ ]│
│                                                                 │
│  Tools Menu:                                                    │
│  ┌─────────────────────────┐                                   │
│  │ 🖼️ Create an image      │                                   │
│  │ 🌐 Search the web       │                                   │
│  │ {·} Write code          │                                   │
│  │ 🔬 Run deep research    │                                   │
│  │ 🧠 Think longer         │                                   │
│  └─────────────────────────┘                                   │
└─────────────────────────────────────────────────────────────────┘
```

#### 7.1.3 Sequence Diagram - Send Message

```mermaid
sequenceDiagram
    actor User
    participant Chat as saas-chat
    participant WS as WebSocket
    participant API as /api/v2/chat/send
    participant LLM as LLMService
    participant Brain as SomaBrain

    User->>Chat: Type message + submit
    Chat->>Chat: Add optimistic message
    Chat->>WS: send({type: 'chat.message', content})
    WS->>API: Route to handler
    API->>Brain: recall(context)
    Brain-->>API: relevant_memories[]
    API->>LLM: complete({messages, context})
    
    loop Streaming response
        LLM-->>WS: {type: 'chat.delta', content}
        WS-->>Chat: Display streaming text
    end
    
    LLM-->>API: full_response
    API->>Brain: remember(exchange)
    WS-->>Chat: {type: 'chat.done'}
```

---

## 8. Settings Screen

**Route:** `/settings`  
**Component:** `saas-settings.ts`  
**Permission:** `tenant->view` (edit requires higher)

### 8.1 Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Sidebar]  │  Account Settings                                              │
│            │─────────────────────────────────────────────────────────────────│
│            │  GENERAL SETTINGS         │  My Profile                        │
│            │  📱 Apps                   │                                    │
│            │  👤 Account        ◄       │  [Avatar] [+ Change] [Remove]     │
│            │  🔔 Notification           │  We support PNGs, JPEGs and GIFs  │
│            │  🌐 Language & Region      │                                    │
│            │                            │  First Name           Last Name   │
│            │  WORKSPACE SETTINGS        │  ┌────────────┐      ┌──────────┐│
│            │  ⚙ General                 │  │ Brian      │      │Frederiksen││
│            │  👥 Members                │  └────────────┘      └──────────┘│
│            │  💳 Billing                │                                    │
│            │                            │  Account Security                  │
│            │                            │                                    │
│            │                            │  Email                             │
│            │                            │  ┌──────────────────────────────┐ │
│            │                            │  │ brian@example.com  [disabled]│ │
│            │                            │  └──────────────────────────────┘ │
│            │                            │                    [Change email] │
│            │                            │                                    │
│            │                            │  Password                          │
│            │                            │  ┌──────────────────────────────┐ │
│            │                            │  │ ••••••••••        [disabled]│ │
│            │                            │  └──────────────────────────────┘ │
│            │                            │               [Change password]   │
│            │                            │                                    │
│            │                            │  2-Step Verification         [ON] │
│            │                            │  Add additional security...       │
│            │                            │                                    │
│            │                            │  Support Access                    │
│            │                            │  Support access          [ON]     │
│            │                            │  Granted until Aug 31, 9:40 PM    │
│            │                            │                                    │
│            │                            │  Log out of all devices           │
│            │                            │  Log out of all other sessions    │
│            │                            │                        [Log out]  │
│            │                            │                                    │
│            │                            │  Delete my account                 │
│            │                            │  Permanently delete account        │
│            │                            │               [Delete Account]    │
└─────────────┴───────────────────────────────────────────────────────────────┘
```

### 8.2 Settings Tabs Structure

| Tab | Sections | Permission |
|-----|----------|------------|
| Apps | Connected apps, OAuth tokens | `tenant->view` |
| Account | Profile, Security, Devices | `tenant->view` |
| Notification | Email, Push, In-app | `tenant->view` |
| Language | Locale, Timezone | `tenant->view` |
| General | Workspace name, logo | `tenant->administrate` |
| Members | User list, invites | `tenant->administrate` |
| Billing | Subscription, invoices | `tenant->administrate` |

---

## 9. Summary - All Screens

| # | Screen | Route | Component | Status |
|---|--------|-------|-----------|--------|
| 1 | Login | `/login` | `saas-login.ts` | ✅ Exists |
| 2 | Register | `/register` | `saas-register.ts` | ❌ Needs creation |
| 3 | Forgot Password | `/forgot-password` | `saas-forgot-password.ts` | ❌ Needs creation |
| 4 | Auth Callback | `/auth/callback` | `saas-auth-callback.ts` | ✅ Exists |
| 5 | Mode Selection | `/mode-select` | `saas-mode-selection.ts` | ✅ Exists |
| 6 | Platform Dashboard | `/platform` | `saas-platform-dashboard.ts` | ✅ Exists |
| 7 | Tenants | `/platform/tenants` | `saas-tenants.ts` | ✅ Exists |
| 8 | Billing | `/platform/billing` | `saas-billing.ts` | ❌ Needs creation |
| 9 | Subscriptions | `/platform/subscriptions` | `saas-subscriptions.ts` | ❌ Needs creation |
| 10 | Users | `/admin/users` | `saas-users.ts` | ❌ Needs creation |
| 11 | Agents | `/admin/agents` | `saas-agents.ts` | ❌ Needs creation |
| 12 | Chat | `/chat` | `saas-chat.ts` | ✅ Exists |
| 13 | Memory | `/memory` | `saas-memory.ts` | ✅ Exists |
| 14 | Tools | `/tools` | `saas-tools.ts` | ✅ Exists |
| 15 | Cognitive | `/cognitive` | `saas-cognitive.ts` | ✅ Exists |
| 16 | Settings | `/settings` | `saas-settings.ts` | ✅ Exists |
| 17 | Themes | `/themes` | `saas-themes.ts` | ✅ Exists |
| 18 | Audit Log | `/audit` | `saas-audit.ts` | ❌ Needs creation |

---

**Document Status:** CANONICAL — Ready for Implementation
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
