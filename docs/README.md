# SomaAgent01 Documentation

**Version**: 1.0.0  
**Last Updated**: 2025-01-24  
**Standards Compliance**: ISO/IEC 12207, ISO/IEC 42010, ISO 21500, ISO/IEC 27001

## Documentation Structure

This documentation follows ISO/IEC standards for software lifecycle processes and architecture description.

### Manuals

| Manual | Purpose | ISO/IEC Mapping |
|--------|---------|-----------------|
| [User Manual](./user-manual/index.md) | Installation, usage, troubleshooting | ISO 21500§4.2 |
| [Technical Manual](./technical-manual/index.md) | Architecture, deployment, security | ISO 12207§6, ISO 42010 |
| [Development Manual](./development-manual/index.md) | Coding standards, CI/CD, testing | ISO 29148, IEEE 1016 |
| [Onboarding Manual](./onboarding-manual/index.md) | Team setup, contribution workflow | ISO 21500§7 |

### Quick Links

#### User Documentation
- [Installation Guide](./user-manual/installation.md)
- [Quick Start Tutorial](./user-manual/quick-start-tutorial.md)
- [Features Overview](./user-manual/features.md)
- [FAQ](./user-manual/faq.md)
- [Troubleshooting](./user-manual/troubleshooting.md)

#### Technical Documentation
- [Architecture Overview](./technical-manual/architecture.md)
- [Deployment Guide](./technical-manual/deployment.md)
- [Monitoring & Observability](./technical-manual/monitoring.md)
- [Security Controls](./technical-manual/security.md)

#### Development Documentation
- [Local Setup](./development-manual/local-setup.md)
- [Coding Standards](./development-manual/coding-standards.md)
- [Testing Guidelines](./development-manual/testing-guidelines.md)
- [API Reference](./development-manual/api-reference.md)
- [Contribution Workflow](./development-manual/contribution-workflow.md)

## Project Overview

SomaAgent01 is a microservices-based conversational AI platform built on:

- **Gateway**: FastAPI HTTP/WebSocket gateway (port 20016)
- **Conversation Worker**: Kafka consumer processing user messages
- **Tool Executor**: Executes tools requested by conversations
- **Memory Services**: Replication and synchronization with SomaBrain
- **Infrastructure**: Kafka, Redis, PostgreSQL, OPA

## Standards Compliance

This project adheres to:

- **ISO/IEC 12207**: Software lifecycle processes
- **ISO/IEC 42010**: Architecture description
- **ISO/IEC 29148**: Requirements engineering
- **ISO 21500**: Project management
- **ISO/IEC 27001**: Information security management

## Metadata

```json
{
  "title": "SomaAgent01 Documentation",
  "project": "SomaAgent01",
  "version": "1.0.0",
  "last_updated": "2025-01-24",
  "owner": "Documentation Team",
  "standards": [
    "ISO/IEC 12207",
    "ISO/IEC 15288",
    "ISO/IEC 29148",
    "ISO/IEC 42010",
    "ISO 21500",
    "ISO/IEC 27001"
  ]
}
```
