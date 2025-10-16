## Essential local development stack

This doc explains how to run a minimal set of services for local development and quick iteration.

Included services (minimal):
- kafka
- redis
- postgres
- memory-service
- gateway
- conversation-worker
- tool-executor

Run the stack (requires Docker and docker-compose / Docker Desktop):

```bash
# From the repository root (agent-zero)
docker compose -f docker-compose.essential.yaml up --build
```

Gateway: http://localhost:8010/health

Notes:
- This composition uses the project `DockerfileLocal` to build per-service images. The `SERVICE` build-arg is set to keep image size smaller for per-service builds.
- For a faster start you can pre-build the base image `somaagent01-dev:latest` in your environment.
- Optional services (OpenFGA, OPA, Grafana, Qdrant) are purposefully excluded to reduce resource usage.

For Docker-specific guidance (build-args, TORCH_VARIANT, and exact compose commands), see the canonical development guide: `docs/development.md`.

