Shared Infra dependency and handoff

The shared infrastructure (Postgres, Redis, Kafka, OPA, Vault, Prometheus, Grafana, Etcd) was split out to its own repo: https://github.com/somatechlat/somastack

What moved out
- Helm umbrella chart: infra/helm/soma-infra
- Kind and Compose helpers: infra/kind/soma-kind.yaml, infra/docker/shared-infra.compose.yaml
- Environment examples and manuals: docs/infra/*

How to bring up Shared Infra (quick)
1) Clone somastack and render the chart:
   - helm template soma-infra infra/helm/soma-infra -n soma-infra -f infra/helm/soma-infra/values-dev.yaml
2) Optional: Kind install
   - kind create cluster --config infra/kind/soma-kind.yaml
   - kubectl create ns soma-infra
   - helm upgrade --install soma-infra infra/helm/soma-infra -n soma-infra -f infra/helm/soma-infra/values-dev.yaml --wait --timeout 10m
3) Endpoints to use from Agent services
   - Postgres: postgres.soma-infra.svc.cluster.local:5432
   - Redis: redis.soma-infra.svc.cluster.local:6379
   - Kafka: kafka.soma-infra.svc.cluster.local:9092 (disabled by default in dev values)
   - OPA: opa.soma-infra.svc.cluster.local:8181
   - Vault: vault.soma-infra.svc.cluster.local:8200

Docs
- See somastack docs/infra/SHARED_INFRA_MANUAL.md and ENV_VARS_AND_SECRETS.md for env contracts and secret handling.
