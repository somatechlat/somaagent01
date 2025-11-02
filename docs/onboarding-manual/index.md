# Onboarding Manual

**Standards**: ISO 21500§7

## Welcome

This manual helps new team members get started with SomaAgent01 development.

## Day 1: Environment Setup

### 1. Access

- GitHub repository access
- Slack/Discord channel invitation
- Development machine setup

### 2. Clone Repository

```bash
git clone https://github.com/somatechlat/somaagent01.git
cd somaagent01
```

### 3. Install Dependencies

```bash
# Python 3.11+
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Docker
# Install from https://docs.docker.com/get-docker/
```

### 4. Start Development Stack

```bash
# Infrastructure only
make deps-up

# Services (local Python)
make stack-up

# UI
make ui
```

### 5. Verify Setup

```bash
# Check health
curl http://localhost:20016/v1/health

# Check UI
open http://127.0.0.1:3000
```

## Week 1: Codebase Familiarization

### Architecture Review

1. Read [Technical Manual](../technical-manual/index.md)
2. Review [Architecture Diagram](../technical-manual/architecture.md)
3. Understand Kafka topics and data flow

### Code Walkthrough

1. **Gateway** (`services/gateway/main.py`): HTTP API, authentication
2. **Conversation Worker** (`services/conversation_worker/main.py`): Message processing
3. **Common Libraries** (`services/common/`): Shared utilities

### First Contribution

1. Pick a "good first issue" from GitHub
2. Create feature branch: `git checkout -b feature/your-name-issue-123`
3. Make changes, add tests
4. Submit PR following [Contribution Workflow](../development-manual/contribution-workflow.md)

## Month 1: Domain Expertise

### Key Concepts

- **Event-Driven Architecture**: Kafka topics, consumers, producers
- **Outbox Pattern**: Transactional message delivery
- **Memory System**: SomaBrain HTTP API, WAL replication
- **Multi-Tenancy**: Tenant isolation, policies

### Recommended Reading

- [Designing Data-Intensive Applications](https://dataintensive.net/) (Chapters 1-3, 11)
- [Building Microservices](https://www.oreilly.com/library/view/building-microservices-2nd/9781492034018/) (Chapters 1-4)

## Resources

- **Documentation**: `/docs`
- **Runbooks**: `/docs/development-manual/runbooks.md`
- **Team Contacts**: `/docs/onboarding-manual/team-contacts.md`
- **FAQ**: `/docs/onboarding-manual/faq.md`

## Getting Help

- **Slack**: #somaagent01-dev
- **GitHub Discussions**: https://github.com/somatechlat/somaagent01/discussions
- **Office Hours**: Tuesdays 2-3pm UTC

## Standards Compliance

- **ISO 21500§7**: Resource management and team development
