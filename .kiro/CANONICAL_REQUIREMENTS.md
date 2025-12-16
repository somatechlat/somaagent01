# Canonical Requirements Specification

## 1. Introduction
This document serves as the **Single Source of Truth** for all requirements of the SomaAgent01 project. It consolidates previous fragmented specifications (Canonical Architecture, WebUI Redesign, Security/OPA, etc.) into one unified standard.

**Project Goals:**
1.  **Clean Architecture:** strict separation of concerns (Domain, Application, Infrastructure, Presentation).
2.  **Security-First:** Zero Trust principles, OPA policies, ClamAV scanning, and secure uploads.
3.  **Modern Web UI:** AI-native, responsive, accessible interface with real-time capabilities.
4.  **VIBE Compliance:** 100% adherence to Verification, Implementation, Behavior, Execution coding rules.

---

## 2. Core Architecture Requirements

### 2.1. Structural Integrity & Design Patterns
*   **REQ-ARC-001 (Clean Architecture):** The system MUST be organized into concentric layers:
    *   **Domain:** Entities, Value Objects, Repository Interfaces (Ports). No external dependencies.
    *   **Application:** Use Cases, Service Interfaces. Depends only on Domain.
    *   **Infrastructure:** Adapters (DB, API Clients, File System). Depends on Application/Domain.
    *   **Presentation:** Web Controllers, CLI. Depends on Application.
*   **REQ-ARC-002 (Module Decomposition):** Monolithic modules (ConversationWorker, Agent, ToolExecutor) MUST be decomposed into smaller, single-purpose components (< 300 lines per file).
*   **REQ-ARC-003 (Configuration):** All configuration MUST be accessed via the `src.core.config.cfg.ConfigFacade` singleton. Direct `os.environ` access is PROHIBITED in business logic.
*   **REQ-ARC-004 (Dependency Injection):** Dependencies MUST be injected into Use Cases and Services (e.g., passing Repository implementations to Use Cases).

### 2.2. Legacy & Cleanup
*   **REQ-CLN-001 (Import Cleanup):** All imports of the deleted `persist_chat` module MUST be removed.
*   **REQ-CLN-002 (Legacy Proxies):** Backward compatibility wrappers MUST be provided for legacy code (e.g., `fetchApi`, `settingsModalProxy`) until full refactor is complete.

---

## 3. Security Requirements

### 3.1. Authorization & Policy (OPA)
*   **REQ-SEC-001 (Policy Enforcement):** All agent tool executions MUST be authorized by Open Policy Agent (OPA).
*   **REQ-SEC-002 (Fail-Closed):** If OPA is unavailable, the system MUST deny the action (Fail-Closed).
*   **REQ-SEC-003 (Access Control):** Policies MUST restrict tools based on `tenant_id` and `persona_id`.

### 3.2. Secure File Uploads
*   **REQ-SEC-004 (TUS Protocol):** Large file uploads MUST use the TUS protocol for resumability.
*   **REQ-SEC-005 (Malware Scanning):** All uploads MUST be scanned by ClamAV.
    *   Files awaiting scan are `SCAN_PENDING`.
    *   Infected files are `QUARANTINED` and inaccessible.
    *   Clean files are `AVAILABLE`.
*   **REQ-SEC-006 (Rate Limiting):** Upload endpoints MUST be rate-limited using `slowapi` (Redis-backed) to prevent DoS.

---

## 4. Web UI Requirements

### 4.1. General UX & Design System
*   **REQ-UI-001 (Design System):** The UI MUST use the new "Neon/Glassmorphism" design system (tokens for colors, typography, spacing).
*   **REQ-UI-002 (Responsive):** Interfaces MUST be fully responsive (Mobile, Tablet, Desktop) with collapsible navigation.
*   **REQ-UI-003 (Accessibility):** The application MUST utilize semantic HTML and pass `axe-core` accessibility scans.

### 4.2. Chat Interface
*   **REQ-UI-004 (Real-time Streaming):** Chat usage MUST support Server-Sent Events (SSE) for token-by-token streaming of assistant responses.
*   **REQ-UI-005 (Session Management):** Users MUST be able to Create, Load, Rename, and Delete chat sessions.
*   **REQ-UI-006 (Attachments):** The chat input MUST support Drag & Drop file uploads (integrated with TUS).

### 4.3. Feature Modules
*   **REQ-UI-007 (Settings):** A comprehensive Settings modal MUST allow configuration of Agent parameters and API keys.
*   **REQ-UI-008 (Memory Dashboard):** A visual interface MUST display memory graph nodes/edges and allow semantic search (connecting to `GET /v1/memory`).
*   **REQ-UI-009 (Scheduler):** A dashboard MUST allow listing, creating, and deleting scheduled tasks (`/v1/scheduler`).
*   **REQ-UI-010 (Capsule Marketplace):** A registry browser MUST allow viewing and installing Agent Capsules.

---

## 5. System Quality & Verification

### 5.1. Testing (VIBE)
*   **REQ-TST-001 (Backend Testing):** All critical paths (Payment, Auth, Data Loss risk) MUST have Property-Based Tests (Hypothesis).
*   **REQ-TST-002 (Frontend Testing):** All UI features MUST have Playwright E2E tests.
*   **REQ-TST-003 (No Mocks):** Integration tests MUST run against real containerized services (Redis, Chroma, OPA), not mocks.

### 5.2. Observability / Health
*   **REQ-OBS-001 (Degradation):** A `DegradationMonitor` MUST track service health (Redis, SomaBrain) and reduce context window size if degraded.
*   **REQ-OBS-002 (Metrics):** Prometheus metrics MUST be exposed for Request Latency, Error Rates, OPA Decisions, and ClamAV Scan Duration.
