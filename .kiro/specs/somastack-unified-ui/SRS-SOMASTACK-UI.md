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
