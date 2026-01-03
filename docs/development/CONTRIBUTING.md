# Contributing to SomaAgent01

## 🚧 VIBE Coding Rules (Strict Enforcement)

This repository adheres to the **VIBE** methodology. All contributions must be:
1.  **Verified**: No mocks. Tests must run against real Docker services.
2.  **Infrastructure-Aware**: Use `docker-compose` for all dependencies.
3.  **Built-in**: Use Django capabilities (ORM, Signals, Ninja) over external libs.
4.  **Exact**: No "stub implementation" comments. Write real code or don't commit.

## 🏗️ Architecture (Modular Monolith)

The system is organized into **17 Django Apps** inside `admin/`.
-   **Core Logic**: `admin.core`, `admin.llm`, `admin.memory`
-   **Agents**: `admin.agents`
-   **Services**: `services.gateway`, `services.conversation_worker`

**DO NOT create files in root or `src/`.**

## 🛠️ Development Setup

1.  **Environment**:
    ```bash
    cp .env.example .env
    # Configure SA01_DB_DSN, OPENAI_API_KEY, etc.
    ```

2.  **Docker Stack**:
    ```bash
    docker-compose up -d postgres redis
    ```

3.  **Migrations**:
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

4.  **Testing**:
    ```bash
    pytest tests/django/
    ```

## 📝 Pull Request Process

1.  **Atomic Commits**: One feature per PR.
2.  **Green Tests**: CI must pass.
3.  **No Legacy**: Do not re-introduce FastAPI or Pydantic BaseSettings (use Django Settings).

---
**Maintained by SomaTech LATAM**
