# OpenFGA Migration Service (`somaAgent01_openfga-migrate`)

The **OpenFGA migration** container is responsible for applying database schema migrations to the OpenFGA PostgreSQL datastore before the OpenFGA service starts.

## How it works
| Property | Value |
|----------|-------|
| **Container name** | `somaAgent01_openfga-migrate` |
| **Image** | `openfga/openfga:v1.8.3` |
| **Command** | `migrate --datastore-engine postgres --datastore-uri postgres://openfga:openfga@postgres:5432/openfga?sslmode=disable` |
| **Restart policy** | `on-failure` – will retry only if the migration exits with a non‑zero status. |
| **Depends on** | `postgres` (condition: `service_healthy`). The OpenFGA service itself depends on this container with `condition: service_completed_successfully` so it only starts after migrations finish. |
| **Lifecycle** | The container **exits with status 0** after a successful migration. This is expected – it is a one‑shot task. |

## Common confusion
- **Container exits** – Seeing the container in `Exited` state is normal; it means the migrations completed successfully.
- **Re‑running migrations** – Docker Compose will reuse the existing container on subsequent `docker compose up`. To force a fresh migration run, use:
  ```bash
  docker compose -f infra/docker-compose.somaagent01.yaml up --force-recreate openfga-migrate
  ```
  or delete the container first:
  ```bash
  docker rm -f somaAgent01_openfga-migrate
  docker compose -f infra/docker-compose.somaagent01.yaml up -d openfga-migrate
  ```
- **Failure handling** – If the migration fails (non‑zero exit code), the `on-failure` restart policy will attempt to restart the container, giving you a chance to fix any DB connectivity or schema issues.

## Recommendations
1. **Leave the container as‑is** – The current `restart: "on-failure"` ensures it will retry on transient errors but will not keep running indefinitely.
2. **Include it in your deployment checklist** – Verify the logs after a fresh compose up:
   ```bash
   docker logs somaAgent01_openfga-migrate
   ```
   You should see lines similar to:
   ```
   2025/10/07 01:49:17 current version 5
   2025/10/07 01:49:17 running all migrations
   2025/10/07 01:49:17 migration done
   ```
3. **No healthcheck needed** – Since the container exits on success, Docker treats it as completed. The dependent `openfga` service uses `condition: service_completed_successfully` to wait for it.

---
*Generated on $(date)*
