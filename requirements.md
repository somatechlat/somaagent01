# SomaAgent01 — Requirements Specification

**Document ID:** SA01-SRS-2025-12  
**Version:** 3.0  
**Date:** 2025-12-16  
**Status:** VERIFIED + MULTIMODAL EXTENSION PLANNED  
**Compliance:** ISO/IEC/IEEE 29148:2018

---

## Overview

This document defines the complete functional and non-functional requirements for SomaAgent01, an enterprise-grade AI agent framework with multimodal capabilities.

**Full Specification:** See [`docs/SRS.md`](docs/SRS.md) for complete 1600+ line requirements document.

---

## System Scope

SomaAgent01 is a distributed microservices system comprising:

- **Gateway Service** (FastAPI, port 8010) - HTTP routing, auth, rate limiting
- **Conversation Worker** (Kafka consumer) - Message processing, orchestration
- **Tool Executor** (sandboxed execution) - Tool dispatch, policy enforcement
- **SomaBrain Integration** (port 9696) - Cognitive memory, neuromodulation
- **Celery Task System** (Redis) - Async task processing
- **Multimodal Extension** (planned) - Image/video generation, SRS composition

---

## Core Functional Requirements

### FR-001: Gateway Service
- **FR-001.1** FastAPI HTTP gateway with async support
- **FR-001.2** Session management (`/v1/sessions/*`)
- **FR-001.3** LLM invocation (`/v1/llm/invoke`, stream and non-stream)
- **FR-001.4** File upload processing (`/v1/uploads`)
- **FR-001.5** Admin endpoints (`/v1/admin/*` for audit, DLQ, requeue)
- **FR-001.6** Health checks (`/v1/health`)

### FR-002: Authentication & Authorization
- **FR-002.1** Bearer token / API key authentication
- **FR-002.2** Rate limiting per tenant
- **FR-002.3** OPA policy enforcement for all actions
- **FR-002.4** Service-to-service mTLS

### FR-003: Conversation Processing
- **FR-003.1** Message analysis (intent, sentiment, tags)
- **FR-003.2** Context building for LLM invocation
- **FR-003.3** Response generation with streaming support
- **FR-003.4** Memory storage to SomaBrain
- **FR-003.5** Clean Architecture use cases (ProcessMessage, GenerateResponse, StoreMemory, BuildContext)

### FR-004: Tool Execution
- **FR-004.1** Sandboxed tool execution
- **FR-004.2** Policy-based tool authorization
- **FR-004.3** Result publishing to Kafka
- **FR-004.4** Audit logging for all tool executions
- **FR-004.5** Memory capture (policy-gated)

### FR-005: SomaBrain Integration
- **FR-005.1** Memory storage (`/remember`)
- **FR-005.2** Memory recall (`/recall`)
- **FR-005.3** Neuromodulation state management
- **FR-005.4** Adaptation weights retrieval
- **FR-005.5** Sleep cycle triggering
- **FR-005.6** Persona management
- **FR-005.7** Feedback submission

### FR-006: Degraded Mode
- **FR-006.1** Component health monitoring (somabrain, database, kafka, redis, gateway, auth, tool_executor)
- **FR-006.2** Degradation levels (NONE, MINOR, MODERATE, SEVERE, CRITICAL)
- **FR-006.3** Circuit breaker integration
- **FR-006.4** Automatic fallback on component failure

### FR-007: Data Storage
- **FR-007.1** PostgreSQL tables: session_envelopes, session_events, dlq_messages, attachments, audit_events, outbox, memory_write_outbox
- **FR-007.2** Redis caching: sessions, policy requeue, deduplication, rate limiting
- **FR-007.3** Kafka topics: conversation.inbound/outbound, tool.requests/results, audit.events, dlq.events, memory.wal

---

## Multimodal Extension Requirements (Section 16)

**Feature Flag:** `SA01_ENABLE_multimodal_capabilities` (default: false)

### FR-MMX-001: Multimodal Job Planning
- **FR-MMX-001.1** Accept user requests for multimodal deliverables (images, diagrams, screenshots, videos)
- **FR-MMX-001.2** Extract plan from LLM as Task DSL JSON
- **FR-MMX-001.3** Compile plan to executable DAG with dependencies

### FR-MMX-010: Capability Registry
- **FR-MMX-010.1** Maintain registry of tools with modality metadata
- **FR-MMX-010.2** Maintain registry of models by provider with cost/latency/quality priors
- **FR-MMX-010.3** Preserve existing provider cards/settings UX

### FR-MMX-020: Tool + Model Selection
- **FR-MMX-020.1** Select tool/model based on user defaults, policy, capability fit, SomaBrain outcomes
- **FR-MMX-020.2** Support dynamic selection using SomaBrain ranking
- **FR-MMX-020.3** Produce explainable selection record with rationale and fallback ladder

### FR-MMX-030: Degradation & Fallback
- **FR-MMX-030.1** Implement deterministic fallback ladder per modality (image/video/diagram)
- **FR-MMX-030.2** Record all degradation events with reasons and traces

### FR-MMX-040: Asset Pipeline & Provenance
- **FR-MMX-040.1** Store generated assets with unique ID and metadata (request_id, tool, model, provider, prompts, timestamps, cost, hashes)
- **FR-MMX-040.2** Support embedding or linking assets into SRS outputs
- **FR-MMX-040.3** Support asset versioning (regenerate creates new version)

### FR-MMX-050: SRS Composition
- **FR-MMX-050.1** Generate ISO 29148-style SRS documentation with figures/diagrams/screenshots
- **FR-MMX-050.2** Produce deliverable package (SRS document + asset bundle + provenance summary)

---

## Non-Functional Requirements

### NFR-001: Reliability
- **NFR-001.1** Per-asset success probability target (configurable) via fallback ladders
- **NFR-001.2** Partial progress resumption (Temporal integration)

### NFR-002: Performance
- **NFR-002.1** Time budgets per task and per request
- **NFR-002.2** Concurrency controls for asset generation
- **NFR-002.3** P95 latency targets:
  - Capability discovery: 50ms
  - Policy routing: 100ms
  - Portfolio ranking: 200ms
  - Image generation (DALL-E): 15s
  - Diagram rendering (Mermaid): 2s
  - Quality evaluation: 5s
  - SRS composition (5 assets): 3s

### NFR-003: Security & Governance
- **NFR-003.1** OPA policies for tool/model invocation (allowed providers, data handling)
- **NFR-003.2** Redact sensitive inputs in provenance records per policy
- **NFR-003.3** Asset storage access control aligned to tenant model
- **NFR-003.4** TLS 1.3 only, mTLS, JWS request signing
- **NFR-003.5** Capsule supply chain security (SHA-256, cosign/sigstore)

### NFR-004: Observability
- **NFR-004.1** Structured events and metrics (selection decisions, latency, cost, fallback counts, quality feedback)
- **NFR-004.2** OpenTelemetry distributed tracing
- **NFR-004.3** Prometheus metrics for all components

### NFR-005: VIBE Compliance
- **NFR-005.1** Zero TODO/stub/placeholder keywords in production code
- **NFR-005.2** All implementations real (no mocks in production)
- **NFR-005.3** Repository pattern for all data access
- **NFR-005.4** Use Case isolation with dependency injection
- **NFR-005.5** All files within tracked size baselines

---

## Acceptance Criteria

### Base System
- [x] All 7 PostgreSQL tables created with proper constraints and indexes
- [x] All Kafka topics configured with proper partitioning
- [x] All 4 Use Cases implemented with Clean Architecture
- [x] All security hardening measures in place (TLS 1.3, mTLS, JWS signing)
- [x] All observability instrumentation (Prometheus + OpenTelemetry)

### Multimodal Extension (Planned)
- [ ] All 5 multimodal database tables created with migrations
- [ ] CapabilityRegistry discovers tools by modality and constraints
- [ ] PolicyGraphRouter routes with fallback ladders (chaos-tested)
- [ ] AssetStore creates/retrieves assets from S3 or PostgreSQL
- [ ] Provenance recorded for every generated asset
- [ ] At least 3 provider adapters implemented (OpenAI DALL-E, Stability, Mermaid)
- [ ] Quality Critic evaluates image quality with vision model
- [ ] Portfolio Ranker queries SomaBrain outcomes (shadow mode functional)
- [ ] SRSComposer generates markdown with embedded images
- [ ] All API endpoints functional and tested
- [ ] OPA policies enforce modality permissions
- [ ] Unit tests: 90%+ coverage for new modules
- [ ] E2E golden test: "Generate SRS with diagrams" succeeds
- [ ] Chaos test: circuit breaker prevents cascade failures
- [ ] Zero VIBE violations

---

## Related Documents

- **Full SRS:** [`docs/SRS.md`](docs/SRS.md) - Complete 1600+ line specification
- **Design:** [`design.md`](design.md) - Detailed architectural design
- **Tasks:** [`TASKS.md`](TASKS.md) - 250+ implementation tasks
- **VIBE Rules:** [`VIBE_CODING_RULES.md`](VIBE_CODING_RULES.md) - Coding standards

---

**Last Updated:** 2025-12-16  
**Maintained By:** Development Team
