# Canonical Project Roadmap

This document outlines the **Master Roadmap** for SomaAgent01. It supersedes all previous task lists.

## Phase 1: System Hardening & Architecture Fixes

### 1.1. Refactoring & Cleanup
- [ ] **[Refactor]** Move `degradation_monitor.py` to `services/common/`.
- [ ] **[Wire]** Integrate `DegradationMonitor` into `ConversationWorker`.
- [ ] **[Cleanup]** Remove `persist_chat` imports globally.
- [ ] **[Config]** Consolidate all config usage to `src.core.config.cfg`.

### 1.2. Security Implementation
- [ ] **[Dep]** Add `slowapi` to implementation dependencies.
- [ ] **[RateLimit]** Implement Redis-backed limits on Upload endpoints.
- [ ] **[OPA]** Implement `OPAPolicyAdapter` and enforce checks in `ToolExecutor`.
- [ ] **[ClamAV]** Enforce ClamAV scanning on all file uploads (Quarantine flow).
- [ ] **[TUS]** Finalize TUS Protocol (HEAD, DELETE, Expiry Cleaning).

## Phase 2: WebUI - Testing & Stability

### 2.1. End-to-End Testing (Playwright)
- [ ] **[Test]** `test_navigation.py`: Sidebar, Responsive Breakpoints.
- [ ] **[Test]** `test_chat.py`: Send/Receive, Streaming, Stop Generation.
- [ ] **[Test]** `test_settings.py`: Persistence, API Key toggles.
- [ ] **[Test]** `test_uploads.py`: TUS simulation, Drag & Drop.
- [ ] **[Test]** `test_sessions.py`: Create, Rename, Delete flows.
- [ ] **[Test]** `test_a11y.py`: Axe-core scans on critical pages.

## Phase 3: WebUI - Capsule Marketplace

### 3.1. Marketplace Backend
- [ ] **[API]** `GET /v1/capsules/registry` (List Public).
- [ ] **[API]** `POST /v1/capsules/install/{id}`.

### 3.2. Marketplace Frontend
- [ ] **[UI]** Build `features/capsules/store.js`.
- [ ] **[UI]** Create Registry Grid Layout & Card Components.
- [ ] **[UI]** Implement Install/Update flows with progress indication.

## Phase 4: WebUI - Integration & Visualization

### 4.1. Project Manager Integration
- [ ] **[Core]** Define `ProjectProvider` interface.
- [ ] **[Adapter]** Implement Plane/Jira adapters.
- [ ] **[UI]** Add Provider Switching to Settings.

### 4.2. Canvas Visualization
- [ ] **[Engine]** Create `core/canvas/renderer.js` (OffscreenCanvas).
- [ ] **[Perf]** Implement Point Decimation (>10k nodes).
- [ ] **[Runtime]** Pyodide Integration for in-browser client code execution.

## Phase 5: Memory & Intelligence

### 5.1. Memory Dashboard
- [ ] **[Connect]** Wire `memory.store.js` to real `GET /v1/memory` endpoints.
- [ ] **[Vis]** Render Force-Directed Graph of memory nodes.
- [ ] **[Realtime]** Subscribe to `memory.created` events for live updates.
