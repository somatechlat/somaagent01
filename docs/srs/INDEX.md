# SRS Document Index

**Project:** SomaAgent01 SaaS Platform  
**Last Updated:** 2025-12-24

---

## Directory Structure

```
docs/
├── README.md                      # Documentation entry point
├── deployment/                    # Deployment guides (infra + software modes)
│   ├── DEPLOYMENT.md
│   └── SOFTWARE_DEPLOYMENT_MODES.md
├── development/                   # Contributor and engineering rules
│   ├── CONTRIBUTING.md
│   └── VIBE_CODING_RULES.md
├── design/                        # Design documents and inventories
│   └── INVENTORY.md
├── ui/                            # UI requirements and styling
│   ├── requirements-ui.md
│   └── UI_STYLE_GUIDE_EXTENSION.md
├── onboarding/                    # Agent onboarding
│   └── ONBOARDING_AGENT.md
├── governance/                    # Governance and violations
│   ├── steering/
│   └── violations/
│       ├── VIOLATIONS.md
│       ├── VIOLATIONS_LOG.md
│       └── VIOLATIONSLOG.md
├── tasks/                         # Implementation tasks
│   ├── AGENT_TASKS.md
│   ├── TASKS-PHASE1-FOUNDATION.md
│   ├── TASKS-PHASE2-AUTH.md
│   ├── TASKS-PHASE3-ADMIN.md
│   └── TASKS-PHASE4-AGENT.md
├── legacy/                        # Legacy canonical docs (reference)
│   ├── CANONICAL_REQUIREMENTS.md
│   ├── CANONICAL_DESIGN.md
│   ├── CANONICAL_RESILIENCE_SRS.md
│   ├── CANONICAL_USER_JOURNEYS_SRS.md
│   └── CANONICAL_SAAS_DESIGN.md
├── srs/                           # Software Requirements Specifications
│   ├── INDEX.md                   # This file
│   ├── SRS-SAAS-ADMIN.md          # 🔴 SAAS Platform Admin (God Mode)
│   ├── SRS-TENANT-ADMIN.md        # 🟠🟡 Tenant Administration
│   ├── SRS-AGENT-USER.md          # ⚪🔵🟣⚫ Agent User Interface
│   ├── SRS-ERROR-HANDLING.md      # Error handling & edge cases
│   ├── SRS-AUTHENTICATION.md      # Auth & authorization
│   └── SRS-DEPLOYMENT-MODES.md    # Deployment targets & resource baselines
└── specs/                         # Feature specs
```

---

## SRS Documents

### By Role

| Role | Document | Screens | Priority |
|------|----------|---------|----------|
| 🔴 SAAS SysAdmin | [SRS-SAAS-ADMIN.md](./SRS-SAAS-ADMIN.md) | 11 | P0 |
| 🟠 Tenant SysAdmin | [SRS-TENANT-ADMIN.md](./SRS-TENANT-ADMIN.md) | 15 | P0 |
| 🟡 Tenant Admin | [SRS-TENANT-ADMIN.md](./SRS-TENANT-ADMIN.md) | 7 | P0 |
| 🟢 Agent Owner | [SRS-AGENT-USER.md](./SRS-AGENT-USER.md) | 11 | P1 |
| 🔵 Developer (DEV) | [SRS-AGENT-USER.md](./SRS-AGENT-USER.md) | 7 | P2 |
| 🟣 Trainer (TRN) | [SRS-AGENT-USER.md](./SRS-AGENT-USER.md) | 7 | P2 |
| ⚪ User (STD) | [SRS-AGENT-USER.md](./SRS-AGENT-USER.md) | 7 | P1 |
| ⚫ Viewer (RO) | [SRS-AGENT-USER.md](./SRS-AGENT-USER.md) | 3 | P3 |
| ⛔ Degraded (DGR) | [SRS-AGENT-USER.md](./SRS-AGENT-USER.md) | 2 | P1 |

### By Category

| Category | Document | Description |
|----------|----------|-------------|
| Error Handling | [SRS-ERROR-HANDLING.md](./SRS-ERROR-HANDLING.md) | All errors, edge cases, recovery |
| Authentication | [SRS-AUTHENTICATION.md](./SRS-AUTHENTICATION.md) | Login, MFA, permissions, tokens |
| Deployment | [SRS-DEPLOYMENT-MODES.md](./SRS-DEPLOYMENT-MODES.md) | Deployment targets & infra baselines |

---

## Quick Reference

### Total Screen Count

| Role Level | Unique Screens |
|------------|----------------|
| Platform Admin | 11 |
| Tenant Admin | 15 |
| Agent Config | 11 |
| Agent User | 7 |
| Developer Mode | 6 |
| Training Mode | 6 |
| **TOTAL UNIQUE** | **~56** |

### API Endpoint Count

| Category | Endpoints |
|----------|-----------|
| SAAS Platform | 13 |
| Tenant Admin | 16 |
| Agent Config | 10 |
| Chat | 6 |
| Memory | 7 |
| Cognitive | 6 |
| Voice | 6 |
| Auth | 8 |
| **TOTAL** | **~72** |

### SpiceDB Permissions

| Level | Permissions |
|-------|-------------|
| Platform | 5 |
| Tenant | 7 |
| Agent | 6 |
| **TOTAL** | **18** |

---

## Dependencies

### Infrastructure
- PostgreSQL 15+
- Redis 7+
- Kafka
- Temporal
- Milvus

### Services
- Keycloak (Auth)
- SpiceDB (Permissions)
- SomaBrain (Memory)
- Lago (Billing)
- Vault (Secrets)

### Frontend
- Lit 3.x
- somastack-tokens.css

### Backend
- Django 5.x
- Django Ninja
- Django Channels

---

## Development Order

### Phase 1: Foundation
1. Database schema (Django models)
2. SpiceDB schema
3. Keycloak realm config
4. Base Lit components

### Phase 2: Authentication
1. Login/logout
2. OAuth providers
3. MFA
4. Session management

### Phase 3: Admin Interfaces
1. SAAS Dashboard
2. Tenant management
3. User management
4. Agent management

### Phase 4: Agent Interfaces
1. Chat view
2. Memory browser
3. Settings
4. Voice integration

### Phase 5: Advanced Features
1. DEV mode
2. TRN mode
3. Degradation handling
4. Analytics
