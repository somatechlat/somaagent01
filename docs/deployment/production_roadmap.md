# SOMA COLLECTIVE INTELLIGENCE: Production Readiness Roadmap v2.0

> **Identity**: PhD Software Developer, PhD Analyst, PhD QA Engineer, ISO Documenter, Security Auditor, Performance Engineer, UX Consultant
> 
> **Date**: 2026-01-13 | **VIBE Compliance**: v8.120.0

---

## Executive Summary

The SOMA Collective has completed a comprehensive audit of somaAgent01. This roadmap addresses the user's mandate: **ALL settings/env MUST be centralized by deployment mode** with completely isolated `infra/standalone/` and `infra/saas/` folders.

---

## 🎯 Core Mandate: Centralized Configuration by Mode

### Deployment Mode Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT MODE SELECTOR                     │
├────────────────────┬────────────────────────────────────────────┤
│ SA01_DEPLOYMENT_MODE=STANDALONE │ SA01_DEPLOYMENT_MODE=SAAS    │
├────────────────────┼────────────────────────────────────────────┤
│ infra/standalone/  │ infra/saas/                               │
│ └── docker-compose.yml │ └── docker-compose.yml               │
│ └── .env.example   │ └── .env.example                         │
│ └── Dockerfile     │ └── Dockerfile                           │
│ └── start.sh       │ └── start_saas.sh                        │
│ SELF-CONTAINED     │ UNIFIED MONOLITH                         │
│ Agent-only         │ Agent + Brain + Memory                   │
│ Port 20xxx         │ Port 63xxx                               │
└────────────────────┴────────────────────────────────────────────┘
```

### Single Source of Truth: `config/settings_registry.py`

```python
# ALL settings loaded from ONE file based on deployment mode
# VIBE Rule 100: Centralized Sovereignty

class SettingsRegistry:
    @staticmethod
    def load() -> Settings:
        mode = os.environ.get("SA01_DEPLOYMENT_MODE", "STANDALONE").upper()
        
        if mode == "SAAS":
            return SaaSSettings.from_vault()
        elif mode == "STANDALONE":
            return StandaloneSettings.from_vault()
        else:
            raise RuntimeError(f"Unknown mode: {mode}. VIBE Rule 91 violation.")
```

---

## 🔴 Phase 1: Infrastructure Isolation (Week 1)

### 1.1 Create `infra/standalone/` (NEW)

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Agent-only deployment, port 20xxx |
| `.env.example` | Standalone configuration template |
| `Dockerfile` | Single-service container |
| `start.sh` | Entrypoint script |

### 1.2 Verify `infra/saas/` Isolation

- ✅ Already exists with Unified Monolith architecture
- ✅ Uses port 63xxx namespace
- 🔴 Contains hardcoded secrets → Vault migration needed

### 1.3 Delete Legacy Scattered Config

| DELETE | Reason |
|--------|--------|
| `infra/tilt/.env` | Violates single-source Rule 100 |
| Multiple `.env` files | Consolidate to `.env.example` per infra folder |

---

## 🟠 Phase 2: Centralized Config System (Week 2)

### 2.1 Create `config/` Module

```
config/
├── __init__.py
├── settings_registry.py    # Mode dispatcher
├── standalone_settings.py  # Standalone config class
├── saas_settings.py        # SaaS config class (merge with saas/config.py)
└── vault_loader.py         # Vault integration (Rule 100)
```

### 2.2 Migrate All Scattered Settings

| Source (DELETE) | Target |
|-----------------|--------|
| `saas/config.py` | `config/saas_settings.py` |
| `services/gateway/settings.py` (env vars) | `config/settings_registry.py` |
| `admin/core/config/` | MERGE into `config/` |

### 2.3 Enforce Rule 91: Zero-Fallback

Replace ALL:
```python
# ❌ BEFORE (VIBE Violation)
os.getenv("REDIS_HOST", "localhost")

# ✅ AFTER (VIBE Compliant)
SettingsRegistry.get().redis_host  # Fails-fast if missing
```

---

## 🟡 Phase 3: Secret Consolidation (Week 3)

### 3.1 Vault-Mandatory (Rule 100/164)

| Pattern | Status | Action |
|---------|--------|--------|
| `vault_secrets.py` | ✅ Canonical | KEEP |
| `secret_manager.py` | 🔴 Redis/Fernet Legacy | DELETE |
| `unified_secret_manager.py` | 🟡 Hybrid | MERGE into vault_secrets |
| `admin/core/helpers/secrets.py` | 🟡 Dev-only | KEEP (file masking) |

### 3.2 Hardcoded Secret Purge

| File | Secret | Action |
|------|--------|--------|
| `saas/memory.py` | `dev-token-*` | ✅ FIXED |
| `services/gateway/settings.py` | `django-insecure-*` | Move to Vault |
| `infra/saas/docker-compose.yml` | `POSTGRES_PASSWORD: soma` | Vault ref |
| `infra/saas/docker-compose.yml` | `soma_dev_token` | Vault ref |

---

## 🟢 Phase 4: Code Consolidation (Week 4)

### 4.1 DO NOT MERGE (Complementary Pairs)

| Module 1 | Module 2 | Keep Both |
|----------|----------|-----------|
| `services/common/rate_limiter.py` | `admin/core/helpers/rate_limiter.py` | ✅ Redis vs asyncio |
| `services/common/circuit_breakers.py` | `admin/core/helpers/circuit_breaker.py` | ✅ Class vs Decorator |

### 4.2 DELETE Legacy Duplicates

| DELETE | Keep |
|--------|------|
| `services/common/secret_manager.py` | `vault_secrets.py` |
| `saas/config.py` | `config/saas_settings.py` |
| Multiple settings parsers | `config/settings_registry.py` |

### 4.3 Purge 47 TODOs

Rule 82 (Anti-Slop): Implement or remove all TODO/FIXME items.

---

## 🔵 Phase 5: Testing & Verification (Week 5-6)

### 5.1 Standalone Mode Tests

```bash
cd infra/standalone
docker compose up -d
curl http://localhost:20020/api/v1/health
# Expected: {"status": "healthy", "mode": "STANDALONE"}
```

### 5.2 SaaS Mode Tests

```bash
cd infra/saas
./build_saas.sh
docker compose up -d
curl http://localhost:63900/api/v1/health
# Expected: {"status": "healthy", "mode": "SAAS"}
```

### 5.3 10-Cycle Resiliency (Rule 122)

```bash
for i in {1..10}; do
  docker compose down && docker compose up -d
  sleep 30
  curl -sf http://localhost:63900/healthz || exit 1
done
echo "✅ 10-Cycle PASS"
```

---

## Verification Commands

```bash
# 1. No hardcoded secrets
grep -rn "dev-token\|somastack2024\|insecure" --include="*.py" --include="*.yml" .
# Target: 0 results

# 2. No localhost fallbacks
grep -rn 'localhost\|127\.0\.0\.1' --include="*.py" . | grep -v "# " | wc -l
# Target: 0

# 3. Single settings registry
grep -rn 'os.getenv.*localhost' --include="*.py" .
# Target: 0

# 4. No TODOs in production
grep -rn "TODO\|FIXME" --include="*.py" . | wc -l
# Target: 0
```

---

## Summary: Files to CREATE

| Path | Purpose |
|------|---------|
| `infra/standalone/` | NEW isolated folder |
| `config/settings_registry.py` | Centralized mode dispatcher |
| `config/standalone_settings.py` | Standalone config |
| `config/saas_settings.py` | SaaS config (from saas/config.py) |

## Summary: Files to DELETE

| Path | Reason |
|------|--------|
| `services/common/secret_manager.py` | Legacy Redis/Fernet |
| `infra/tilt/.env` | Scattered config |
| Multiple `.env` files | Consolidate to `.env.example` |
| `saas/config.py` | Move to config/ |

---

*Signed: SOMA COLLECTIVE INTELLIGENCE*
*PhD Developer • PhD Analyst • PhD QA Engineer • ISO Documenter • Security Auditor • Performance Engineer • UX Consultant*
