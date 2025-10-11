Agent quickstart (without shared infra)

This repo contains the Agent runtime and app services. The Shared Infra (Postgres, Redis, Kafka, OPA, Vault, Prometheus, Grafana, Etcd) now lives in its own repository: https://github.com/somatechlat/somastack

Run the agent locally via Docker Compose

- Minimal stack (app only):
  - docker compose -f docker-compose.somaagent01.yaml up --build
  - UI: http://localhost:7002

- If your services depend on Shared Infra, start it from somastack separately and point env vars (POSTGRES_DSN, REDIS_URL, KAFKA_BOOTSTRAP_SERVERS, OPA_URL, VAULT_ADDR) to the cluster endpoints published by somastack (see that repo’s docs/infra/SHARED_INFRA_MANUAL.md).

Ports
- Gateway/UI: 7002 (Docker dev)
- Other internal services: 8010–8016

Notes
- No shared-infra is included here. Use somastack for infra; keep this repo focused on agent code/services.
