---
title: SomaAgent01 Technical Manual
slug: technical-manual
version: 1.0.0
last-reviewed: 2025-10-15
audience: platform-engineers, architects
owner: platform-architecture
reviewers:
  - infra
  - security
links:
  - label: Architecture Overview
    url: ./architecture.md
  - label: Deployment Blueprint
    url: ./infrastructure.md
  - label: Security Baseline
    url: ./security.md
---

# SomaAgent01 Technical Manual

This manual is the authoritative source on how SomaAgent01 is architected, deployed, and integrated with the wider Soma platform. It consolidates diagrams, configuration schemas, and operational decision records.

## Sections

- [Architecture](./architecture.md): canonical diagrams, service topology, and rationale.
- [Infrastructure & Deployments](./infrastructure.md): Docker Compose and Helm blueprints.
- [Integrations](./integrations.md): External systems, APIs, and data contracts.
- [Security & Compliance](./security.md): AuthN/Z, secrets, and audit posture.
- [Data Flows](./data-flow.md): Streaming and persistence pipelines.

Refer to the [Development Manual](../development-manual/index.md) for engineering workflows, and to the [Onboarding Manual](../onboarding-manual/index.md) for role-based enablement.
