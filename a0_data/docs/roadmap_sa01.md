# SA01 – SomaAgent01 Roadmap

## Objective

Align SA01 with the consolidated architecture:

- Use shared infra services (Auth, OPA, Kafka, Redis, Prometheus/Grafana, Vault, Etcd).
- Communicate with SB via gRPC (`memory.proto`).
- Adopt common configuration and logging utilities from `common/`.
- Deploy via the unified Helm chart.

## Work Items (ordered)

1. **Refactor Settings**
   - Replace local `.env` files with `common/config/settings.py` inheritance.
   - Pull Auth, OPA, and feature-flag endpoints from DNS (`auth.soma.svc.cluster.local`, etc.).
2. **gRPC Client/Server Update**
   - Generate protobuf stubs (`python -m grpc_tools.protoc ...`).
   - Switch existing HTTP calls to the new gRPC client for memory reads/writes.
3. **Logging & Tracing**
   - Import `common/utils/trace.py` and configure OpenTelemetry exporter to Jaeger.
   - Ensure JSON log format and Loki side-car label `service=sa01`.
4. **Dockerfile Simplification**
   - Expose only port 50051 (gRPC).
   - Remove any duplicated Prometheus exporter; rely on shared `/metrics` endpoint.
5. **Helm Chart Integration**
   - Add a sub-chart entry `sa01` under `services/` in `infra/helm/charts/soma-stack/`.
   - Set `values.yaml` to reference shared infra DNS names.
6. **CI/CD Adjustments**
   - Update GitHub Actions to run `pytest` with the new gRPC fixtures.
   - Add a Helm lint step for the `sa01` chart.
7. **Feature-Flag Migration**
   - Move any SA01-specific flags from ConfigMaps to Etcd.
   - Cache them in Redis via the common flag client.
8. **Testing**
   - Write integration tests that spin up a local Kind cluster with the single `soma-infra` chart and the `sa01` chart.
   - Verify health endpoint `/healthz` and gRPC latency < 50 ms.
9. **Documentation**
   - Add a section in `docs/architecture.md` describing SA01’s role and its dependencies on shared infra.

## Milestones

| Milestone | Target Sprint (2-week) |
|-----------|------------------------|
| Settings refactor & DNS switch | Sprint 1 |
| gRPC migration | Sprint 2 |
| Logging/Tracing integration | Sprint 2 |
| Helm chart & CI updates | Sprint 3 |
| Feature-flag migration | Sprint 3 |
| Full integration test suite | Sprint 4 |
| Documentation & hand-off | Sprint 4 |
