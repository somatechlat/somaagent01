# SRS-LAGO-BILLING — Usage Metering & Billing

| Field | Value |
|-------|-------|
| **System** | SomaAgent01 |
| **Document ID** | SRS-LAGO-BILLING-2026-01-16 |
| **Version** | 1.0 |
| **Date** | 2026-01-16 |
| **Status** | FINAL |
| **Author** | Platform Engineering |
| **Owner** | Platform Team |

---

## Table of Contents

1. [Introduction](#1-introduction)
   1.1 [Purpose](#11-purpose)
   1.2 [Scope](#12-scope)
   1.3 [Definitions](#13-definitions)
   1.4 [References](#14-references)
2. [Product Description](#2-product-description)
   2.1 [Product Perspective](#21-product-perspective)
   2.2 [Product Functions](#22-product-functions)
   2.3 [User Characteristics](#23-user-characteristics)
   2.4 [Constraints](#24-constraints)
   2.5 [Assumptions and Dependencies](#25-assumptions-and-dependencies)
3. [Specific Requirements](#3-specific-requirements)
   3.1 [Functional Requirements](#31-functional-requirements)
   3.2 [Non-Functional Requirements](#32-non-functional-requirements)
   3.3 [External Interface Requirements](#33-external-interface-requirements)
   3.4 [Design Constraints](#34-design-constraints)
4. [Traceability](#4-traceability)
5. [Revision History](#5-revision-history)

---

## 1. Introduction

### 1.1 Purpose

This document specifies the integration between SomaAgent01 and the Lago usage-based billing platform. It covers tenant lifecycle management, usage metering, invoice retrieval, webhook handling, and prepaid credit support.

### 1.2 Scope

**In scope:**
- Lago customer and subscription management
- Usage event submission (single and batch)
- Invoice listing and retrieval
- Webhook consumption for subscription and invoice events
- Wallet (prepaid credits) and coupon support
- Non-blocking retry mechanism for failed events

**Out of scope:**
- Budget enforcement and limit checking (see [SRS-BUDGET-SYSTEM.md](./SRS-BUDGET-SYSTEM.md))
- Lago internal plan configuration UI
- SomaAgent01 chat execution logic

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **Lago** | External open-source usage-based billing platform (getlago.com). |
| **Customer** | A tenant represented as a Lago customer record. |
| **Subscription** | A plan assignment linking a customer to billing terms. |
| **Billable Metric** | A measurable resource defined in Lago (e.g., tokens, api_calls). |
| **Event** | A usage record sent to Lago containing a metric code, timestamp, and properties. |
| **Wallet** | A prepaid credit balance attached to a Lago customer. |
| **Webhook** | An HTTP callback posted by Lago to SomaAgent01 for lifecycle events. |

### 1.4 References

| ID | Document | Version | Location |
|----|----------|---------|----------|
| REF-001 | SRS-BUDGET-SYSTEM | 1.0 | `docs/srs/SRS-BUDGET-SYSTEM.md` |
| REF-002 | Lago API Reference | Latest | https://getlago.com/docs/api-reference |
| REF-003 | Docker Compose Lago | 1.0 | `docker-compose.lago.yml` |

---

## 2. Product Description

### 2.1 Product Perspective

Lago operates as an independent Docker deployment external to the SomaAgent01 cluster. SomaAgent01 communicates with Lago via its REST API over HTTPS. Lago is explicitly excluded from internal infrastructure health checks. Usage events are emitted from Phase 12 (Observability) of the chat flow.

### 2.2 Product Functions

| ID | Function | Description |
|----|----------|-------------|
| FUNC-001 | Customer Onboarding | Create a Lago customer record when a tenant is provisioned. |
| FUNC-002 | Plan Subscription | Assign a Lago plan to a customer upon tier selection. |
| FUNC-003 | Usage Metering | Send billable usage events after each resource-consuming operation. |
| FUNC-004 | Batch Metering | Submit up to 100 usage events in a single batch request. |
| FUNC-005 | Invoice Retrieval | List and download finalized invoices for a tenant. |
| FUNC-006 | Webhook Handling | Receive and process Lago webhooks for subscription and invoice lifecycle. |
| FUNC-007 | Prepaid Credits | Manage wallet top-ups and react to depletion alerts. |

### 2.3 User Characteristics

| User Type | Role | Technical Level | Access |
|-----------|------|-----------------|--------|
| Tenant Admin | View invoices, manage payment methods | Intermediate | Lago Customer Portal |
| Platform Operator | Configure plans, monitor webhooks | Advanced | Lago Admin Dashboard |
| End User | Subject to billing metering | Basic | None (transparent) |

### 2.4 Constraints

| ID | Constraint | Description |
|----|------------|-------------|
| CON-001 | Independent Deployment | Lago container is not included in SomaAgent01 health checks. |
| CON-002 | Non-Blocking | Lago API failures must not block chat or tool operations. |
| CON-003 | Idempotency | Every usage event must include a unique `transaction_id`. |
| CON-004 | Settings-Based Secrets | `LAGO_API_KEY` must be configured via Django settings, not environment variables. |

### 2.5 Assumptions and Dependencies

| ID | Assumption / Dependency | Impact if Invalid |
|----|------------------------|-------------------|
| AD-001 | Lago container is reachable at `LAGO_API_URL` from SomaAgent01. | Billing events cannot be delivered; retry queue fills. |
| AD-002 | Kafka or equivalent message queue is available for retry/DLQ. | Failed events are lost without manual reconciliation. |
| AD-003 | Webhook endpoint `/webhooks/lago` is exposed to Lago container. | Subscription lifecycle events are not processed. |

---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 Customer & Subscription Management

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-LGO-001 | The system shall create a Lago customer (`POST /api/v1/customers`) when a new tenant is onboarded, using `tenant_id` as the external customer ID. | Must | Test | Draft |
| REQ-LGO-002 | The system shall assign a Lago subscription (`POST /api/v1/subscriptions`) when a tenant selects a plan tier. | Must | Test | Draft |
| REQ-LGO-003 | The system shall support retrieving a customer's portal URL for self-service billing management. | Should | Test | Draft |

#### 3.1.2 Usage Metering

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-LGO-004 | The system shall send a usage event (`POST /api/v1/events`) after each billable operation, including `transaction_id`, `customer_external_id`, `code`, and `properties`. | Must | Test | Draft |
| REQ-LGO-005 | The system shall support batch event submission (`POST /api/v1/events/batch`) with a maximum of 100 events per request. | Must | Test | Draft |
| REQ-LGO-006 | The `transaction_id` shall be unique per event to ensure idempotency on Lago side. | Must | Test | Draft |

**Billable Metrics**

| Metric Code | Aggregation | Field | Description |
|-------------|-------------|-------|-------------|
| `tokens` | SUM | `total_tokens` | LLM tokens consumed |
| `input_tokens` | SUM | `count` | Input tokens only |
| `output_tokens` | SUM | `count` | Output tokens only |
| `api_calls` | COUNT | - | API requests |
| `tool_calls` | COUNT | - | Tool executions |
| `voice_minutes` | SUM | `minutes` | STT/TTS audio |
| `image_generations` | COUNT | - | DALL-E images |
| `storage_gb` | MAX | `gb` | File storage |
| `memory_tokens` | SUM | `tokens` | SomaBrain storage |
| `vector_ops` | COUNT | - | Vector operations |
| `learning_credits` | COUNT | - | Brain learn cycles |

**Rationale:** Granular metrics enable accurate graduated and usage-based pricing.

**Dependencies:** REQ-LGO-004 depends on REQ-LGO-001 (customer exists).

#### 3.1.3 Invoicing

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-LGO-007 | The system shall list invoices (`GET /api/v1/invoices`) for a tenant. | Must | Test | Draft |
| REQ-LGO-008 | The system shall support downloading a finalized invoice PDF (`POST /api/v1/invoices/{id}/download`). | Should | Test | Draft |

#### 3.1.4 Webhooks

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-LGO-009 | The system shall expose `POST /webhooks/lago` to receive Lago webhook events. | Must | Test | Draft |
| REQ-LGO-010 | On `subscription.started`, the system shall activate the tenant's features and cache the plan code. | Must | Test | Draft |
| REQ-LGO-011 | On `subscription.terminated`, the system shall deactivate the tenant's features. | Must | Test | Draft |
| REQ-LGO-012 | On `invoice.finalized`, the system shall notify the tenant and log for audit. | Must | Test | Draft |
| REQ-LGO-013 | On `wallet.depleted`, the system shall notify the tenant and optionally restrict usage. | Should | Test | Draft |

**Webhook Event Types Handled**

| Event Type | Description | SOMA Action |
|------------|-------------|-------------|
| `subscription.started` | Subscription activated | Activate tenant features, cache plan |
| `subscription.terminated` | Subscription ended | Disable tenant features |
| `subscription.upgraded` | Plan upgraded | Update AgentIQ limits |
| `subscription.downgraded` | Plan downgraded | Update AgentIQ limits |
| `invoice.created` | Invoice generated | Log for audit |
| `invoice.finalized` | Invoice ready | Notify tenant |
| `invoice.payment_status_updated` | Payment processed | Update payment status |
| `wallet.depleted` | Prepaid credits exhausted | Notify + restrict |

#### 3.1.5 Prepaid Credits & Coupons

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-LGO-014 | The system shall support wallet creation and top-up (`POST /api/v1/wallets`, `POST /api/v1/wallets/{id}/top_up`). | Should | Test | Draft |
| REQ-LGO-015 | The system shall support applying coupons to tenants (`POST /api/v1/applied_coupons`). | Should | Test | Draft |

#### 3.1.6 Failure Handling

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-LGO-016 | Lago API failures during event submission shall be caught, logged, and queued for retry without failing the primary operation. | Must | Test | Draft |
| REQ-LGO-017 | After maximum retries, failed events shall be routed to a dead-letter queue (DLQ) for manual reconciliation. | Must | Test | Draft |

---

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-LGO-PERF-001 | Event submission latency (excluding network) | < 5 ms | Load test |
| NFR-LGO-PERF-002 | Webhook response latency | < 100 ms | Load test |

#### 3.2.2 Security

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-LGO-SEC-001 | `LAGO_API_KEY` stored in Django settings (not env vars) | 100% | Inspection |
| NFR-LGO-SEC-002 | Webhook endpoint validates Lago signature using `LAGO_WEBHOOK_SECRET` | 100% | Test |

#### 3.2.3 Reliability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-LGO-REL-001 | Event delivery retries before DLQ | >= 3 | Test |
| NFR-LGO-REL-002 | System functions when Lago is unreachable | Degraded (queueing only) | Fault injection |

#### 3.2.4 Scalability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-LGO-SCL-001 | Batch endpoint capacity | 100 events/request | Test |
| NFR-LGO-SCL-002 | Concurrent webhook throughput | 100 req/sec | Load test |

#### 3.2.5 Maintainability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-LGO-MNT-001 | Lago client code isolated in a single module | Yes | Inspection |

---

### 3.3 External Interface Requirements

#### 3.3.1 User Interfaces

Tenant administrators access billing information via the Lago Customer Portal URL returned by the API. No dedicated SomaAgent01 billing UI is required.

#### 3.3.2 Software Interfaces

| Interface | Protocol | Format | Authentication |
|-----------|----------|--------|----------------|
| Lago REST API | HTTPS | JSON | Bearer token (`LAGO_API_KEY`) |
| Lago Webhooks | HTTPS | JSON | HMAC signature (`LAGO_WEBHOOK_SECRET`) |
| Kafka / MQ | TCP | Binary/JSON | SASL/SSL |

**Lago API Categories Used**

| Category | Endpoints |
|----------|-----------|
| Customers | `POST /api/v1/customers`, `GET /api/v1/customers/{id}` |
| Subscriptions | `POST /api/v1/subscriptions`, `GET /api/v1/subscriptions` |
| Events | `POST /api/v1/events`, `POST /api/v1/events/batch` |
| Plans | `GET /api/v1/plans` |
| Invoices | `GET /api/v1/invoices`, `POST /api/v1/invoices/{id}/download` |
| Wallets | `POST /api/v1/wallets`, `POST /api/v1/wallets/{id}/top_up` |
| Webhooks | `POST /api/v1/webhook_endpoints` |

#### 3.3.3 Hardware Interfaces

None.

---

### 3.4 Design Constraints

| ID | Constraint | Source |
|----|------------|--------|
| DC-LGO-001 | Lago runs as an independent Docker container, not included in SomaAgent01 health checks. | REF-003 |
| DC-LGO-002 | All Lago API calls must use the base URL configured in Django settings (`LAGO_API_URL`). | Architecture decision |
| DC-LGO-003 | Plan provisioning is performed in Lago, not in SomaAgent01 code. | Lago design |

---

## 4. Traceability

### 4.1 Requirements Traceability Matrix

| REQ ID | Description | Source | Design | Implementation | Test |
|--------|-------------|--------|--------|----------------|------|
| REQ-LGO-001 | Create Lago customer | Product backlog | `lago_client.py` | `admin/billing/lago_client.py` | `tests/integration/test_lago_customer.py` |
| REQ-LGO-002 | Assign subscription | Product backlog | `lago_client.py` | `admin/billing/lago_client.py` | `tests/integration/test_lago_subscription.py` |
| REQ-LGO-003 | Customer portal URL | Product backlog | `lago_client.py` | `admin/billing/lago_client.py` | `tests/integration/test_lago_customer.py` |
| REQ-LGO-004 | Send usage event | Product backlog | `lago_client.py` | `admin/billing/lago_client.py` | `tests/integration/test_lago_events.py` |
| REQ-LGO-005 | Batch events | Product backlog | `lago_client.py` | `admin/billing/lago_client.py` | `tests/integration/test_lago_events.py` |
| REQ-LGO-006 | Idempotency | Product backlog | Event schema | `admin/billing/lago_client.py` | `tests/integration/test_lago_events.py` |
| REQ-LGO-007 | List invoices | Product backlog | `lago_client.py` | `admin/billing/lago_client.py` | `tests/integration/test_lago_invoices.py` |
| REQ-LGO-008 | Download invoice PDF | Product backlog | `lago_client.py` | `admin/billing/lago_client.py` | `tests/integration/test_lago_invoices.py` |
| REQ-LGO-009 | Webhook endpoint | Product backlog | `webhooks.py` | `admin/billing/webhooks.py` | `tests/api/test_lago_webhooks.py` |
| REQ-LGO-010 | Handle subscription.started | Product backlog | `webhooks.py` | `admin/billing/webhooks.py` | `tests/api/test_lago_webhooks.py` |
| REQ-LGO-011 | Handle subscription.terminated | Product backlog | `webhooks.py` | `admin/billing/webhooks.py` | `tests/api/test_lago_webhooks.py` |
| REQ-LGO-012 | Handle invoice.finalized | Product backlog | `webhooks.py` | `admin/billing/webhooks.py` | `tests/api/test_lago_webhooks.py` |
| REQ-LGO-013 | Handle wallet.depleted | Product backlog | `webhooks.py` | `admin/billing/webhooks.py` | `tests/api/test_lago_webhooks.py` |
| REQ-LGO-014 | Wallet top-up | Product backlog | `lago_client.py` | `admin/billing/lago_client.py` | `tests/integration/test_lago_wallets.py` |
| REQ-LGO-015 | Apply coupons | Product backlog | `lago_client.py` | `admin/billing/lago_client.py` | `tests/integration/test_lago_coupons.py` |
| REQ-LGO-016 | Non-blocking failure handling | Product backlog | Retry module | `admin/billing/retry.py` | `tests/unit/test_lago_retry.py` |
| REQ-LGO-017 | Dead-letter queue | Product backlog | Kafka config | `infra/kafka/topics.yml` | `tests/unit/test_lago_dlq.py` |

### 4.2 Requirement to Test Case Mapping

| REQ ID | Test Case ID | Test Method | Expected Result |
|--------|--------------|-------------|-----------------|
| REQ-LGO-001 | TC-LGO-001 | Integration test | Customer created in Lago with matching external ID. |
| REQ-LGO-002 | TC-LGO-002 | Integration test | Subscription active for selected plan. |
| REQ-LGO-004 | TC-LGO-004 | Integration test | Event accepted by Lago with 201 response. |
| REQ-LGO-005 | TC-LGO-005 | Integration test | Batch of 100 events accepted without error. |
| REQ-LGO-006 | TC-LGO-006 | Integration test | Duplicate event rejected/ignored by Lago. |
| REQ-LGO-009 | TC-LGO-009 | API test | Webhook endpoint returns 200 and processes event. |
| REQ-LGO-010 | TC-LGO-010 | API test | Tenant plan cached and features activated. |
| REQ-LGO-016 | TC-LGO-016 | Fault injection | Chat operation succeeds despite Lago 500 error. |
| REQ-LGO-017 | TC-LGO-017 | Fault injection | Failed event appears in DLQ after retries exhausted. |

---

## 5. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-16 | Platform Engineering | Initial ISO/IEC/IEEE 29148 conformant version. Refactored from ad-hoc SRS. |

---

*Document conforms to ISO/IEC/IEEE 29148:2018 — Systems and Software Engineering — Life Cycle Processes — Requirements Engineering.*
