# SRS-LAGO-BILLING — Usage Metering & Billing (WITHDRAWN)

> ## THIS SPECIFICATION IS WITHDRAWN
>
> **Status: WITHDRAWN / NOT IMPLEMENTED — do not use as a requirement source.**
>
> The external billing platform integration specified by this document **does not
> exist in this system**. It was never implemented in the shipped codebase, and
> all remaining artefacts of it have been removed. Nothing in SomaAgent01 calls an
> external billing service, emits usage events to one, or resolves customer,
> subscription, plan, invoice or wallet state from one.
>
> Usage metering that *is* real lives in the Django-native budget system — see
> [SOMA-SRS-BUDGET-001.md](./SOMA-SRS-BUDGET-001.md) and `admin/core/budget/`.
> That system records usage in Django cache and enforces limits locally. It has
> no external billing dependency.
>
> This file is retained **only** as a document-control tombstone so the ISO
> register stays complete. Every requirement, interface, and traceability row
> that used to live here has been struck. If you are looking for billing,
> invoicing or payment behaviour: **this system has none.**

---

## Document Control

| Field | Value |
|-------|-------|
| Document Title | SRS-LAGO-BILLING — Usage Metering & Billing |
| Document Identifier | SOMA-SRS-LAGOBILLING-001 |
| Version | 1.0.0 |
| Status | **WITHDRAWN** |
| Superseded By | SOMA-SRS-BUDGET-001 (usage metering and enforcement) |
| Withdrawn On | 2026-09-28 |

## 1. Why This Document Was Withdrawn

This specification described an integration between SomaAgent01 and an external
usage-based billing platform. It specified customer and subscription lifecycle
mirroring, usage-event emission, invoice retrieval, webhook ingestion, wallets
and coupons.

None of that was ever built. The codebase contains:

- no billing client module,
- no webhook receiver for billing lifecycle events,
- no `lago_*` fields on any live model (they were dropped by
  `admin/aaas/migrations/0005_drop_lago_fields.py`),
- no billable-metric mapping on the budget metric registry,
- no settings for an external billing URL or API key,
- no tests against an external billing service.

Publishing a requirement document for a feature that does not exist is itself a
defect: it misleads implementers, auditors and integrators. The document is
withdrawn so that the specification set describes only the system as built.

## 2. What Actually Exists

| Concern | This system's actual implementation |
|---------|-------------------------------------|
| Usage metering | `admin/core/budget/limits.py` counters in Django cache |
| Limit enforcement | `admin/core/budget/gate.py` `@budget_gate` decorator |
| Metric definitions | `admin/core/budget/registry.py` `METRIC_REGISTRY` |
| Plan limits | `admin/core/budget/limits.py` `PLAN_LIMITS` |
| Invoices | **None.** No invoice source exists; invoice views report empty. |
| Payment methods | **None.** |
| Subscriptions | Tier selection only (`admin/aaas/models/tiers.py`); no external subscription record. |
| Webhooks (billing) | **None.** |

## 3. Requirements

**None.** All previously listed requirements (REQ-LGO-001 … REQ-LGO-017) were
withdrawn with this document. They were never implemented and must not be
traced, tested or scheduled.

## 4. External Interfaces

**None.** This system exposes no interface to an external billing service and
consumes none.

---

**Do not reinstate this document.** If external billing is ever required again,
write a new specification against the code that actually exists at that time.
