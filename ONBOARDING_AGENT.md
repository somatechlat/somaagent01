# Onboarding Agent Guide

**Welcome to SomaAgent01.** This is a VIBE-compliant, Django-based Cognitive Operating System.

## 🗺️ System Map

The system is a **Modular Monolith** powered by **Django 5.0**.

### Key Directories
-   `admin/` - The heart of the system. Contains all 17 Django Apps.
-   `services/` - Executable entrypoints (Gateway, Workers).
-   `tests/` - Comprehensive test suite (Pytest + Docker).

### Core Concepts

#### 1. The Gateway (`services.gateway`)
All external traffic hits the **Django Ninja** API Gateway.
-   **Docs**: `/api/v2/docs`
-   **Auth**: JWT / API Key via `admin.api`

#### 2. The Brain (`admin.memory`)
Long-term semantic memory using Vector Stores (Chroma/Milvus).
-   **Short-term**: Redis
-   **Long-term**: Postgres + Vector

#### 3. The Orchestrator (`admin.orchestrator`)
Manages Agent lifecycles and task delegation graphs.

## 👨‍💻 Developer Workflow

### Adding a New Feature
1.  **Identify Domain**: Does it belong in an existing App?
2.  **Create Model**: Define in `admin/{app}/models.py`.
3.  **Create API**: Define in `admin/{app}/api.py` (Ninja Router).
4.  **Register**: Add to `services.gateway.settings.INSTALLED_APPS`.
5.  **Test**: Write real integration tests in `tests/django/`.

### Rules of Engagement
-   **NO MOCKS**: If you need a DB, use the Docker Postgres.
-   **NO LEGACY**: Do not import from `src`. It does not exist.
-   **NO FASTAPI**: Use Django Ninja.

---
**Maintained by SomaTech LATAM**
