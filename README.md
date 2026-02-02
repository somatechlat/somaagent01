# 🧠 SomaAgent01 - Enterprise Multi-Agent Cognitive Platform

> **Production-ready enterprise AI agent orchestration system built on Django 5.0**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-Proprietary-yellow.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

---

## 📋 Executive Summary

**SomaAgent01** is an enterprise-grade **Multi-Agent Cognitive Platform** built on **Django 5.0 + Django Ninja**. It's a complete **AAAS (Agent-As-A-Service)** platform for orchestrating AI agents with:

### 🏛️ Enterprise Features
- Multi-tenant architecture with **strict data isolation**
- **Keycloak-based authentication** (OIDC)
- **SpiceDB-based fine-grained authorization** (Zanzibar-style)
- Real-time chat via **WebSocket/SSE**
- Integration with **SomaBrain** (cognitive runtime) and **SomaFractalMemory** (memory storage)
- Full observability stack (**Prometheus, Grafana, Kafka audit logging**)
- **Open-source-only** dependencies across the stack

### 🤖 Agent Intelligence
- Advanced **neuro-biological simulation** with real neuromodulation
- **Confidence scoring** with statistical quality assurance
- **Multi-modal processing** (text + vision)
- **A2A protocol** (Agent-to-Agent communication)
- **Recursive learning loops** with adaptation states

---

## 🏗️ Architecture Overview

| Layer | Technology | Enterprise Notes |
|-------|------------|-----------------|
| **API Framework** | Django 5.0 + Django Ninja | 100% Django - **NO FastAPI** (VIBE Rule 8) |
| **ORM** | Django ORM | **NO SQLAlchemy** |
| **Authentication** | Keycloak | OIDC-compliant |
| **Authorization** | SpiceDB | Zanzibar-style fine-grained |
| **Database** | PostgreSQL (Primary) + Vector Store | Multi-tenant |
| **Message Broker** | Kafka + Redis | Event-driven architecture |
| **Monitoring** | Prometheus + Grafana + APM | Production observability |
| **Memory System** | SomaFractalMemory + SomaBrain | Cognitive memory |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Keycloak instance

### 1️⃣ Environment Setup
```bash
# Clone repository
git clone https://github.com/somatechlat/somaagent01.git
cd somaagent01

# Install Poetry dependencies
poetry install

# Copy environment template
cp .env.example .env
# Edit .env with your configuration
```

### 2️⃣ Configuration
Set required environment variables:
```bash
# Core Services
DJANGO_SECRET_KEY="your-secret-key"
DATABASE_URL="postgres://user:pass@localhost:5432/somaagent01"
REDIS_URL="redis://localhost:6379"

# Authentication
KEYCLOAK_URL="https://your-keycloak-instance"
KEYCLOAK_REALM="soma-agent"
KEYCLOAK_CLIENT_ID="soma-agent-client"

# SomaBrain Integration
SA01_SOMA_BASE_URL="http://localhost:9696"
SA01_CAPSULE_REGISTRY_URL="http://localhost:8085"

# Observability
PROMETHEUS_METRICS_PORT=9090
GRAFANA_URL="http://localhost:3000"
```

### 3️⃣ Database Setup
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load fixtures (optional)
python manage.py loaddata services/fixtures/initial_data.json
```

### 4️⃣ Start Development Server
```bash
# Development mode with hot reload
make dev

# OR manual start
python manage.py runserver 0.0.0.0:8000
```

---

## 🔧 Development Workflow

### Build & Deploy
```bash
# Build all images
make build

# Start full stack
make up

# Run tests
make test

# Stop all services
make down

# Clean environment
make clean
```

### Code Quality
```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
pyright
```

---

## 🧠 Agent Cognitive Features

### Neurological Simulation System
```python
# Physiological neuromodulation ranges
NEUROMOD_CLAMP_RANGES = {
    "dopamine": (0.0, 0.8),
    "serotonin": (0.0, 1.0),
    "noradrenaline": (0.0, 0.1),
    "acetylcholine": (0.0, 0.5),
}
```

### Adaptive Cognitive Parameters
- **Exploration Factor**: `0.3 + (dopamine × 0.7)`
- **Creativity Boost**: Triggered when dopamine > 0.6
- **Patience Factor**: `0.3 + (serotonin × 0.7)`
- **Memory Consolidation**: Every 100 iterations
- **Learning Updates**: Every 25 iterations

---

## 🛠️ Agent Capabilities

### Core Tool Arsenal
- **Code Execution**: Python, Node.js, Terminal commands
- **File Operations**: Read/Write, Document processing
- **Web Intelligence**: HTTP requests, Web scraping
- **Document Processing**: PDF text extraction, OCR for images
- **Canvas Workspace**: Visual reasoning environment
- **Multi-modal Processing**: Text + Vision capabilities

### Specialized Features
- **Confidence Scoring**: Statistical quality assurance
- **Circuit Breaker Protection**: Resilient operations
- **Rate Limiting**: API protection
- **Health Monitoring**: Real-time status tracking
- **Degradation Management**: Graceful service degradation

---

## 📊 Metrics & Observability

### Key Metrics
- Agent operation counts and durations
- LLM response confidence scores
- Memory access patterns
- Circuit breaker states
- Service health indicators

### Dashboards
- **Grafana Integration**: Real-time monitoring
- **Prometheus Metrics**: Production scraping
- **Audit Logging**: Kafka-based audit trail
- **Performance Analytics**: Response time tracking

---

## 🔐 Security Architecture

### Multi-Tenancy
- **Strict Data Isolation**: Tenant separation
- **SpiceDB Authorization**: Fine-grained policies
- **Keycloak Authentication**: SSO integration
- **Role-Based Access**: Granular permissions

### Compliance
- **Audit Trail**: Complete action history
- **Data Masking**: Privacy protection
- **Secret Management**: Vault integration
- **Encryption**: End-to-end data protection

---

## 📁 Project Structure

```
somaagent01/
├── admin/                    # Django admin modules
│   ├── agents/              # Agent management
│   ├── authentication/      # Auth services
│   ├── capabilities/        # Capability registry
│   ├── core/               # Core models & utilities
│   └── [other modules]       # Feature modules
├── services/                 # Service implementations
│   ├── gateway/             # API gateway
│   ├── tool_executor/       # Tool execution engine
│   ├── soma_client/         # SomaBrain integration
│   └── [other services]     # Enterprise services
├── webui/                   # React frontend
├── schemas/                 # API schemas
└── infra/                   # Infrastructure

# Key configuration files
├── pyproject.toml           # Poetry configuration
├── requirements.txt         # Python dependencies
├── manage.py               # Django management
├── Makefile               # Build automation
└── docker-compose.yml     # Container orchestration
```

---

## 🔌 A2A Protocol Integration

### Agent-to-Agent Communication
- **Protocol**: fasta2a v0.2+ implementation
- **Context Preservation**: Cross-conversation continuity
- **Reset Capability**: Clean state management
- **Specialized Subordinates**: Profile-based agents

### Integration Capabilities
- **Subordinate Agent Spawning**: Task-specific agents
- **Task Delegation**: Distributed processing
- **Context Sharing**: Inter-agent information
- **Failure Recovery**: Robust error handling

---

## 🧪 Testing

### Test Structure
```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run performance tests
pytest tests/performance/

# Run all tests
make test
```

### Test Coverage
- **Unit Tests**: ~80% coverage required
- **Integration Tests**: Service integration
- **Performance Tests**: Load & stress testing
- **Security Tests**: Audit & compliance

---

## 📈 Performance Characteristics

### Scaling Properties
- **Horizontal Scaling**: Stateless service deployment
- **Connection Pooling**: Database optimization
- **Caching Layers**: Redis & embedding cache
- **Load Balancing**: Multi-instance deployment

### Resource Requirements
- **Memory**: 2GB minimum, 4GB recommended
- **CPU**: 2 cores minimum, 4 cores recommended
- **Storage**: 100GB+ for persistent storage
- **Network**: High bandwidth for API calls

---

## 🤝 Contributing

### Development Guidelines
- **Code Standards**: Follow PSR-12 & Django best practices
- **Type Hints**: Required for new code
- **Testing**: Minimum 80% coverage for features
- **Documentation**: Comprehensive docstrings

### Pull Request Process
1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📞 Support

- **Documentation**: [Developer Docs](https://docs.somatech.com)
- **Issue Tracker**: [GitHub Issues](https://github.com/somatechlat/somaagent01/issues)
- **Discussions**: [GitHub Discussions](https://github.com/somatechlat/somaagent01/discussions)
- **Email**: team@somatech.com

---

## 📄 License

This project is **proprietary software** licensed by SomaTech LAT.
See [LICENSE](LICENSE) file for details.

---

## 🎯 Version History

| Version | Date | Key Features |
|---------|------|--------------|
| 1.0.0 | 2025-12-30 | Initial production release |

---

**🌟 Star** and **⭐ Watch** this repository for updates!

**Built with ❤️ by the SomaTech Team**
