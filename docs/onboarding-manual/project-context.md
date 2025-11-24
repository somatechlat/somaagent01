# Project Context

## What is SomaAgent01?

SomaAgent01 is a production-grade agentic AI platform built on the Agent Zero framework, designed for real-time data propagation and intelligent conversation management.

## Project Vision

**Mission**: Build a reliable, scalable, and observable agentic platform that grows and learns with its users.

**Core Principles**:
- Real data, real servers, real everything (no mocks)
- Complete transparency and observability
- Production-grade reliability
- Security by default

## Key Differentiators

### 1. Real Integration
- No mock implementations
- Real LLM providers
- Real memory persistence (SomaBrain)
- Real policy enforcement (OPA)

### 2. Observability First
- Comprehensive metrics (Prometheus)
- Distributed tracing (OpenTelemetry)
- Structured logging
- Real-time health monitoring

### 3. Event-Driven Architecture
- Kafka for event streaming
- SSE for real-time updates
- Durable message persistence
- At-least-once delivery guarantees

## Architecture Overview

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTP/SSE
┌──────▼──────────────┐
│   Gateway (21016)   │
│  - FastAPI          │
│  - /v1/* endpoints  │
│  - / static         │
└──────┬──────────────┘
       │ Kafka
┌──────▼──────────────┐
│ Conversation Worker │
│  - Message handling │
│  - Tool execution   │
│  - Memory ops       │
└──────┬──────────────┘
       │
┌──────▼──────────────┐
│   Infrastructure    │
│  - PostgreSQL       │
│  - Redis            │
│  - Kafka            │
│  - SomaBrain        │
└─────────────────────┘
```

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Event Bus**: Apache Kafka
- **Cache**: Redis
- **Database**: PostgreSQL
- **Memory**: SomaBrain

### Frontend
- **Framework**: Vanilla JavaScript (Alpine.js)
- **Styling**: Custom CSS
- **Build**: No build step (direct serving)

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Orchestration**: Kubernetes (production)
- **Monitoring**: Prometheus + Grafana
- **Tracing**: OpenTelemetry + Jaeger

## Project Structure

```
somaAgent01/
├── services/           # Microservices
│   ├── gateway/       # API gateway
│   ├── conversation_worker/
│   ├── tool_executor/
│   └── memory_*/
├── python/            # Shared Python code
│   ├── integrations/  # External service clients
│   ├── helpers/       # Utility functions
│   └── tools/         # Tool implementations
├── webui/             # Web interface
│   ├── index.html
│   ├── js/
│   └── css/
├── docs/              # Documentation
├── tests/             # Test suites
└── docker-compose.yaml
```

## Development Workflow

### Local Development
```bash
# Start everything
make dev-up

# View logs
make dev-logs

# Restart services
make dev-restart

# Clean shutdown
make dev-down
```

### Testing
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# E2E tests
pytest tests/e2e/
```

## Key Concepts

### Sessions
- Persistent conversation contexts
- Stored in PostgreSQL
- Cached in Redis
- Identified by UUID

### Messages
- User and assistant messages
- Stored durably
- Replicated to SomaBrain
- Streamed via SSE

### Tools
- Executable functions
- Registered in Tool Catalog
- Policy-gated execution
- Results tracked and logged

### Memory
- Long-term storage in SomaBrain
- Semantic search and recall
- Context building
- Learning and adaptation

## Team Structure

### Core Team
- **Platform Team**: Infrastructure and reliability
- **Backend Team**: Services and APIs
- **Frontend Team**: UI and UX
- **ML Team**: LLM integration and optimization

### Roles
- **Maintainers**: Core contributors with merge rights
- **Contributors**: Community members
- **Reviewers**: Code review specialists

## Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Discord**: Real-time chat
- **Email**: security@example.com (security issues)

## Release Cycle

### Versioning
- Semantic versioning (MAJOR.MINOR.PATCH)
- Release branches: `release/v0.x.x`
- Tags for releases

### Release Schedule
- **Minor releases**: Monthly
- **Patch releases**: As needed
- **Major releases**: Quarterly

## Success Metrics

### Technical Metrics
- Uptime: >99.9%
- P95 latency: <500ms
- Test coverage: >80%
- Zero critical security issues

### Product Metrics
- User satisfaction
- Feature adoption
- Performance improvements
- Community growth

## Learning Resources

### Essential Reading
1. [Architecture Documentation](../technical-manual/architecture.md)
2. [Development Setup](../development-manual/local-setup.md)
3. [API Reference](../development-manual/api-reference.md)
4. [Coding Standards](../development-manual/coding-standards.md)

### External Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [Agent Zero Framework](https://github.com/agent0ai/agent-zero)

## Next Steps

1. Read [Codebase Walkthrough](./codebase-walkthrough.md)
2. Complete [First Contribution](./first-contribution.md)
3. Join [Team Collaboration](./team-collaboration.md)
4. Learn [Domain Knowledge](./domain-knowledge.md)

## Questions?

Don't hesitate to ask! We're here to help you succeed.
