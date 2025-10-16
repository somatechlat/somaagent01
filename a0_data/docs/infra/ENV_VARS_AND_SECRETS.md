# Environment variables and secrets inventory (Shared Infra)

This document lists the environment variables, default values observed in the repo, where they are defined, their sensitivity level, and recommended storage and handling for Kubernetes (Secrets or Vault).

IMPORTANT: The user requested "no mocks" and "no placeholder secrets". Before production usage, rotate any dev tokens and move secrets into Vault or Kubernetes Secrets.

## How to read this file
- Location: where the value was found in the repository
- Default: the default value observed in the file (may be an example)
- Sensitivity: Low / Medium / High
- Recommended storage: K8s Secret / Vault / ConfigMap

---

## Postgres
- Location: `infra/docker/shared-infra.compose.yaml` and `infra/helm/soma-infra/values.yaml` and `infra/helm/soma-infra/charts/postgres/values.yaml`
- POSTGRES_USER / postgresUser
  - Default: `soma`
  - Sensitivity: Low
  - Recommended storage: ConfigMap for username; Secret for consistency if you prefer

- POSTGRES_PASSWORD / postgresPassword
  - Default: `soma`
  - Sensitivity: High
  - Recommended storage: Kubernetes Secret (base64) or Vault secret. Use Secret references in Helm values.

- POSTGRES_DB / postgresDb
  - Default: `soma` / `somaagent01` (compose uses `somaagent01`)
  - Sensitivity: Low
  - Recommended storage: ConfigMap

- PGDATA
  - Default: `/var/lib/postgresql/data/pgdata`
  - Sensitivity: Low
  - Recommended storage: ConfigMap

Notes:
- In Helm chart the Postgres values are injected into the StatefulSet as plain env values. Replace these with `valueFrom: secretKeyRef` or use Helm templating to mount a Secret.

---

## Kafka (KRaft single-node / Bitnami / Confluent variants)
- Location: `infra/docker/shared-infra.compose.yaml` and `infra/helm/soma-infra/charts/kafka/*` and `infra/helm/soma-infra/values*.yaml`
- KAFKA_CFG_NODE_ID, KAFKA_CFG_PROCESS_ROLES, KAFKA_CFG_LISTENERS, KAFKA_CFG_CONTROLLER_QUORUM_VOTERS, KAFKA_CFG_AUTO_CREATE_TOPICS_ENABLE, KAFKA_CFG_NUM_PARTITIONS, KAFKA_ENABLE_KRAFT, KAFKA_CFG_KRAFT_CLUSTER_ID, KAFKA_CFG_ADVERTISED_LISTENERS, KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP, KAFKA_CFG_CONTROLLER_LISTENER_NAMES, KAFKA_CFG_INTER_BROKER_LISTENER_NAME
  - Default: various example values in compose/values (see files)
  - Sensitivity: Low–Medium (cluster ids and controller voters are operational, not secrets)
  - Recommended storage: ConfigMap for operational configs. If SASL/SSL creds are introduced later, store them as Secrets.

- KAFKA_CLUSTER_ID / KAFKA_CFG_KRAFT_CLUSTER_ID
  - Default: `soma-shared-01` or example cluster id
  - Sensitivity: Low

Notes:
- For KRaft in dev, the cluster id and controller voters are required. If using images that accept file-based configuration, prefer mounting config via a ConfigMap. If you add username/password for clients, store them as Secrets.

---

## Redis
- Location: `infra/docker/shared-infra.compose.yaml`, `infra/helm/soma-infra/charts/redis/values.yaml`
- REDIS_URL
  - Default (env example): `redis://localhost:6380/0` (compose) and `redis://redis.soma.svc.cluster.local:6379/0` (k8s)
  - Sensitivity: Medium (if no password; high if ACL/TLS credentials present)
  - Recommended storage: ConfigMap for plain URL if unauthenticated; Secret if password/ACL used.

---

## Vault
- Location: `infra/docker/shared-infra.compose.yaml`, `infra/helm/soma-infra/charts/vault/values.yaml`, `infra/vault/config/config.hcl`
- VAULT_DEV_ROOT_TOKEN_ID / VAULT_DEV_LISTEN_ADDRESS / VAULT_ADDR
  - Default: `root` (dev token in compose), `0.0.0.0:8200` (listen)
  - Sensitivity: High (root token is highly privileged)
  - Recommended storage: For dev-only local clusters, a dev token may be acceptable but must be rotated. For any shared environment, do NOT keep root tokens in source. Use a bootstrap process to unseal/initialize Vault and put root tokens into a secure store (local OS keychain or CI secrets). In Kubernetes, integrate Vault via Helm chart with Raft storage and use Kubernetes auth for apps.

Notes:
- The compose file exposes `VAULT_DEV_ROOT_TOKEN_ID: root`. This is only acceptable for ephemeral local development. Replace this with instructions to initialize Vault and create an application token stored in K8s Secret or in Vault policies.

---

## Grafana
- Location: `infra/helm/soma-infra/charts/grafana/values.yaml`
- GF_SECURITY_ADMIN_PASSWORD / adminPassword
  - Default: `admin`
  - Sensitivity: High (Grafana admin)
  - Recommended storage: Kubernetes Secret. Consider injecting via Helm from a pre-created Secret or using an external secrets operator.

---

## Prometheus
- Location: `infra/helm/soma-infra/charts/prometheus/*`, `infra/archived` monitoring configs
- No direct secrets in default values; scrape configs in chart may reference targets only.

---

## Etcd
- Location: `infra/helm/soma-infra/charts/etcd/*`
- No plaintext secrets by default in the chart. Etcd may be configured for TLS in prod; certificates should be stored in Secrets.
- StorageClass: persistence.storageClass should be set in `values-dev.yaml` to match cluster storage classes (e.g., `standard`). Ensure StatefulSet's `volumeClaimTemplates` have `storageClassName` set.

---

## App-level env (K8s overlays and archived examples)
- Several app overlays and archived k8s manifests use a shared secret name `somaagent-secrets` containing keys such as `GATEWAY_JWT_SECRET`, `POSTGRES_PASSWORD`, `KAFKA_SASL_PASSWORD`. Examples are in `archived/a0_data/infra/k8s/base/secrets.yaml`.
- GATEWAY_JWT_SECRET
  - Default: `change-me` (archived example)
  - Sensitivity: High (used for signing/verification unless using JWKS)
  - Recommended storage: Kubernetes Secret or (preferred) store signing keys in Vault and publish JWKS to apps.

---

## Environment examples (infra/env/.env.shared.example)
The repo includes `infra/env/.env.shared.example` with K8s and Docker host examples:
- POSTGRES_DSN=postgresql://soma:soma@localhost:5436/somaagent01
- KAFKA_BOOTSTRAP_SERVERS=localhost:9094
- REDIS_URL=redis://localhost:6380/0
- VAULT_ADDR=http://localhost:8201
- K8S_* variants pointing to cluster DNS names (postgres.soma.svc.cluster.local, kafka.soma.svc.cluster.local, etc.)

These examples contain plaintext credentials (soma/soma). Replace them with secrets prior to sharing or production usage.

---

## Immediate actions recommended
1. Remove dev high-privilege tokens from compose/values files (VAULT_DEV_ROOT_TOKEN_ID=root, POSTGRES_PASSWORD `soma`, Grafana `admin`). Replace them with references to Kubernetes Secrets or have an initialization job create the secrets securely.
2. Create `soma-infra` namespace secrets before Helm install (or use Helm pre-install hooks) for:
   - `postgres-credentials` (POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB)
   - `vault-root` (only for dev - prefer dynamic unseal)
   - `grafana-admin` (GF_SECURITY_ADMIN_PASSWORD)
3. Use Vault for long-lived secrets and Kubernetes Secrets for bootstrapping values. Consider integrating Kubernetes auth for Vault and/or use external-secrets operator to sync secrets from Vault to K8s.
4. Audit the repository for any other plaintext credentials (e.g., archived secrets.yaml). Delete or rotate any exposed secrets.

---

## How to create secrets (examples)

Kubernetes secrets (example):

kubectl -n soma-infra create secret generic postgres-credentials --from-literal=POSTGRES_USER=soma --from-literal=POSTGRES_PASSWORD="<REPLACE>" --from-literal=POSTGRES_DB=somaagent01

Replace `<REPLACE>` with a properly-generated password; then update Helm values to reference the secret via `valueFrom.secretKeyRef` in templates.

For Vault: initialize Vault, enable kv v2 at `secret/`, and store secrets there. Use Vault Agent or an external-secrets controller to inject secrets into Kubernetes at deployment time.

---

If you want, I can now:
 - Generate a Helm-compatible secrets manifest and place it under `infra/helm/soma-infra/secrets/` with instructions to create the Kubernetes Secrets before running `helm upgrade --install` (dev-safe, not checked in with real values).
 - Or replace the chart values to read from secretKeyRefs (small template change) so Helm will render Secrets if present.

Next step: I'll mark todo #1 completed and stage/commit this file. Then we can proceed to clear the Helm pending-install and apply the storageClass fix so PVCs bind.
