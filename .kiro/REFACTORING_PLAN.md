# SomaStack Workspace Refactoring Plan

**Document ID:** SOMA-REFACTOR-PLAN-2025-12  
**Version:** 1.0  
**Date:** 2025-12-22  
**Status:** PLAN - Awaiting Approval

---

## Executive Summary

This document outlines a comprehensive refactoring plan to standardize all 4 SomaStack repositories following Django project best practices. The goal is to create a unified, clean, and maintainable folder structure across:

1. **somaAgent01** - AI Agent Framework
2. **somabrain** - Cognitive Processing Service
3. **somafractalmemory** - Memory System Service
4. **agentVoiceBox** - Voice Agent Platform

---

## Current State Analysis

### Critical Issues Identified

| Repo | Issue | Severity |
|------|-------|----------|
| somaAgent01 | Duplicate infra folders (`infra/` + `infrastructure/`) | HIGH |
| somaAgent01 | 1000+ log files in `logs/` | HIGH |
| somaAgent01 | Scattered configs (`conf/`, `redis-conf/`, `lago_deploy/`) | HIGH |
| somaAgent01 | Root clutter (models.py, agent.py, initialize.py, preload.py) | MEDIUM |
| somaAgent01 | Empty folders (`knowledge/`, `memory/`, `tmp/`, `redis-conf/`, `postgres-backups/`) | LOW |
| somabrain | Root clutter (arc_cache.py, add_missing_pass.py, apply_vibe_fixes.py) | MEDIUM |
| somabrain | Scattered configs (alertmanager.yml, alerts.yml at root) | MEDIUM |
| somafractalmemory | `site/` folder (generated docs) in repo | LOW |
| agentVoiceBox | Mixed Next.js + Python structure | MEDIUM |
| ALL | Alpine.js webui files need deletion | HIGH |

---

## Target Django-Style Structure

### Standard Layout (Per Repo)

```
{repo_name}/
├── .github/                    # GitHub workflows, CI/CD
├── .kiro/                      # Kiro specs and steering
│   ├── specs/
│   └── steering/
├── config/                     # All configuration files
│   ├── settings/               # Environment-specific settings
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── testing.py
│   ├── docker/                 # Docker configs
│   ├── k8s/                    # Kubernetes manifests
│   └── observability/          # Prometheus, Grafana, alerts
├── docs/                       # Documentation (MkDocs)
│   ├── development-manual/
│   ├── technical-manual/
│   ├── user-manual/
│   └── api/                    # OpenAPI specs
├── infra/                      # Infrastructure as Code
│   ├── helm/                   # Helm charts
│   ├── terraform/              # Terraform (if applicable)
│   ├── kafka/                  # Kafka configs
│   ├── postgres/               # DB init scripts
│   └── redis/                  # Redis configs
├── scripts/                    # Utility scripts
│   ├── ci/                     # CI/CD scripts
│   ├── dev/                    # Development helpers
│   └── ops/                    # Operations scripts
├── src/                        # Main source code
│   └── {package_name}/         # Python package
│       ├── __init__.py
│       ├── api/                # API routers/endpoints
│       ├── core/               # Core domain logic
│       ├── models/             # Data models
│       ├── services/           # Business logic services
│       └── utils/              # Utilities
├── tests/                      # Test suites
│   ├── unit/
│   ├── integration/
│   ├── property/               # Property-based tests
│   └── e2e/                    # End-to-end tests
├── webui/                      # Frontend (Lit Web Components)
│   ├── components/             # Lit components
│   ├── controllers/            # Lit controllers
│   ├── design-system/          # CSS tokens, styles
│   └── static/                 # Static assets
├── migrations/                 # Alembic migrations
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── pyproject.toml
├── pytest.ini
└── README.md
```

---

## Phase 1: somaAgent01 Refactoring

### 1.1 Infrastructure Consolidation

**Current State:**
```
somaAgent01/
├── infra/                      # Partial infra
│   ├── helm/
│   ├── k8s/
│   ├── kafka/
│   ├── memory/
│   ├── observability/
│   ├── postgres/
│   ├── sql/
│   └── temporal/
├── infrastructure/             # DUPLICATE - grafana, postgres, prometheus
├── lago_deploy/                # Billing infra - SCATTERED
├── conf/                       # agentiq.yaml - SCATTERED
├── redis-conf/                 # EMPTY
├── postgres-backups/           # EMPTY
└── observability/              # Python observability code - WRONG LOCATION
```

**Target State:**
```
somaAgent01/
├── infra/                      # ALL infrastructure
│   ├── helm/
│   ├── k8s/
│   ├── kafka/
│   ├── postgres/
│   ├── redis/
│   ├── temporal/
│   ├── lago/                   # Moved from lago_deploy/
│   └── observability/          # Grafana, Prometheus configs
├── config/                     # All configs
│   ├── agentiq.yaml            # Moved from conf/
│   └── settings/
└── src/
    └── observability/          # Python observability code
```

**Migration Commands:**
```bash
# Merge infrastructure/ into infra/
mv infrastructure/grafana infra/
mv infrastructure/prometheus infra/observability/
rm -rf infrastructure/

# Move lago_deploy to infra/lago
mv lago_deploy infra/lago

# Move conf/ contents to config/
mv conf/agentiq.yaml config/
rm -rf conf/

# Delete empty folders
rm -rf redis-conf postgres-backups knowledge memory tmp
```

### 1.2 Logs Cleanup

**Action:** Delete all log files (1000+ files)
```bash
rm -rf logs/*.html
# Add logs/ to .gitignore
echo "logs/*.html" >> .gitignore
```

### 1.3 Root File Reorganization

**Current Root Files to Move:**
| File | Target Location |
|------|-----------------|
| `models.py` | `src/core/models.py` |
| `agent.py` | `src/agent/main.py` |
| `initialize.py` | `scripts/dev/initialize.py` |
| `preload.py` | `scripts/dev/preload.py` |
| `sitecustomize.py` | Keep at root (Python requirement) |

### 1.4 Source Code Reorganization

**Current State:**
```
somaAgent01/
├── python/                     # Agent runtime
│   ├── extensions/
│   ├── helpers/
│   ├── integrations/
│   ├── somaagent/
│   └── tools/
├── src/                        # Core domain
│   ├── core/
│   └── voice/
├── services/                   # Microservices
│   ├── gateway/
│   ├── conversation_worker/
│   └── ...
├── integrations/               # DUPLICATE of python/integrations
└── orchestrator/               # Service orchestration
```

**Target State:**
```
somaAgent01/
├── src/
│   ├── agent/                  # Merged from python/somaagent
│   │   ├── extensions/
│   │   ├── helpers/
│   │   ├── integrations/
│   │   └── tools/
│   ├── core/                   # Keep existing
│   ├── voice/                  # Keep existing
│   └── orchestrator/           # Moved from root
└── services/                   # Keep microservices separate
    ├── gateway/
    ├── conversation_worker/
    └── ...
```

---

## Phase 2: somabrain Refactoring

### 2.1 Root Cleanup

**Files to Move:**
| File | Target Location |
|------|-----------------|
| `arc_cache.py` | `somabrain/cache/arc_cache.py` |
| `add_missing_pass.py` | `scripts/dev/add_missing_pass.py` |
| `apply_vibe_fixes.py` | `scripts/dev/apply_vibe_fixes.py` |
| `alertmanager.yml` | `config/observability/alertmanager.yml` |
| `alerts.yml` | `config/observability/alerts.yml` |
| `config.yaml` | `config/settings/config.yaml` |
| `audit_log.jsonl` | DELETE (runtime artifact) |

### 2.2 Config Consolidation

**Current State:**
```
somabrain/
├── config/                     # Feature flags, logging
├── ops/                        # OPA, prometheus, supervisor
├── infra/                      # Helm, k8s, kafka, observability
└── (root files)                # alertmanager.yml, alerts.yml
```

**Target State:**
```
somabrain/
├── config/
│   ├── settings/               # All YAML configs
│   ├── observability/          # Alerts, alertmanager
│   └── feature_flags.py
└── infra/
    ├── helm/
    ├── k8s/
    ├── kafka/
    ├── opa/                    # Moved from ops/
    └── observability/          # Prometheus, Grafana
```

---

## Phase 3: somafractalmemory Refactoring

### 3.1 Structure Cleanup

**Current State:**
```
somafractalmemory/
├── alembic/                    # Migrations
├── common/                     # Shared utilities
├── somafractalmemory/          # Main package
├── site/                       # Generated docs - DELETE
└── helm/                       # Should be in infra/
```

**Target State:**
```
somafractalmemory/
├── migrations/                 # Renamed from alembic/
├── src/
│   └── somafractalmemory/      # Main package
├── common/                     # Keep shared utilities
├── infra/
│   └── helm/                   # Moved from root
└── tests/
```

### 3.2 Delete Generated Files

```bash
rm -rf site/                    # Generated MkDocs output
```

---

## Phase 4: agentVoiceBox Refactoring

### 4.1 Separate Python and Next.js

**Current State (Mixed):**
```
agentVoiceBox/
├── src/                        # Next.js app
├── ovos-voice-agent/           # Python backend
│   └── AgentVoiceBoxEngine/    # Enterprise platform
├── ovos_voice_agent/           # Python package stub
├── _posts/                     # Blog posts
└── webui/                      # Alpine.js UI - DELETE
```

**Target State:**
```
agentVoiceBox/
├── frontend/                   # Next.js app (renamed from src/)
│   ├── app/
│   ├── components/
│   └── lib/
├── backend/                    # Python backend (renamed from ovos-voice-agent/)
│   ├── src/
│   │   └── agentvoicebox/
│   ├── tests/
│   └── config/
├── blog/                       # Blog content (renamed from _posts/)
└── docs/
```

---

## Phase 5: Alpine.js Removal (ALL REPOS)

### Files to Delete

| Repo | File | Action |
|------|------|--------|
| agentVoiceBox | `webui/index.html` | DELETE |
| somabrain | `webui/index.html` | DELETE |
| somafractalmemory | `webui/index.html` | DELETE |
| somaAgent01 | Various Alpine templates | REPLACE with Lit |

### Spec Updates Required

| File | Changes |
|------|---------|
| `somaAgent01/.kiro/specs/agentskin-uix/tasks.md` | Replace Alpine → Lit |
| `somaAgent01/.kiro/specs/agentskin-uix/requirements.md` | Replace Alpine → Lit |
| `somaAgent01/.kiro/CANONICAL_REQUIREMENTS.md` | Update Section 15.2 |

---

## Phase 6: Standardize Test Structure (ALL REPOS)

### Target Test Layout

```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures
├── unit/                       # Unit tests
│   ├── __init__.py
│   ├── test_models.py
│   └── test_services.py
├── integration/                # Integration tests
│   ├── __init__.py
│   └── test_api.py
├── property/                   # Property-based tests (Hypothesis)
│   ├── __init__.py
│   └── test_properties.py
├── e2e/                        # End-to-end tests (Playwright)
│   ├── __init__.py
│   └── test_flows.py
└── fixtures/                   # Test data
    └── sample_data.json
```

---

## Execution Order

### Week 1: Critical Cleanup
1. Delete all log files in somaAgent01
2. Delete Alpine.js webui files in all repos
3. Delete empty folders
4. Update .gitignore files

### Week 2: Infrastructure Consolidation
1. Merge somaAgent01 `infrastructure/` into `infra/`
2. Move `lago_deploy/` to `infra/lago/`
3. Consolidate config files

### Week 3: Source Reorganization
1. Reorganize somaAgent01 source structure
2. Move root Python files to proper locations
3. Update imports throughout codebase

### Week 4: Other Repos
1. Refactor somabrain structure
2. Refactor somafractalmemory structure
3. Refactor agentVoiceBox structure

### Week 5: Spec Updates
1. Update all Alpine.js references to Lit Web Components
2. Update CANONICAL_REQUIREMENTS.md
3. Update all task files

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Import breakage | Run full test suite after each phase |
| Docker build failures | Update Dockerfile paths incrementally |
| CI/CD pipeline breaks | Update GitHub workflows in parallel |
| Lost configuration | Backup all configs before moving |

---

## Validation Checklist

- [ ] All tests pass after each phase
- [ ] Docker builds succeed
- [ ] CI/CD pipelines green
- [ ] No broken imports
- [ ] Documentation updated
- [ ] .gitignore updated
- [ ] README files updated

---

## Approval Required

This plan requires explicit approval before execution.

**Questions for Review:**
1. Confirm the target folder structure is acceptable
2. Confirm log file deletion is approved
3. Confirm Alpine.js removal is approved
4. Any additional folders to consolidate?

---

**Last Updated:** 2025-12-22  
**Author:** Kiro AI Assistant
