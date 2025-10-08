# Monitoring Quickstart

This guide summarizes the current Prometheus-only monitoring stack that ships with the SomaAgent01 development stack. Grafana has been retired from the default Compose profile; bring your own dashboard tooling if you need rich visualisation.

## Prometheus

- **Service**: `prometheus` container in `docker-compose.somaagent01.yaml`
- **Config path**: `infra/observability/prometheus.yml`
- **Alert rules**: `infra/observability/alerts.yml`
- **Profiles**: The base Compose stack now boots Prometheus by default; the legacy `metrics` profile is no longer required for Grafana.

Key scrape jobs:
- `prometheus`: self-scrape for diagnostics.
- `delegation-gateway`: collects FastAPI metrics exposed at `http://delegation:8015/metrics`.
- `openfga`: scrapes the OpenFGA exporter port (`:2112`).
- `opa`: collects metrics from OPA on port `8181`.
- `circuit-breakers`: polls the standalone exporter started by the gateway at `http://gateway:9610/` (root path) to surface the circuit-breaker counters.

Alert coverage:
- Delegation gateway availability, error rate (>5%) and p95 latency (>1 s sustained for 10 minutes).
- Gateway-wide latency > 2 s (p95) and error rate > 1 % courtesy of the FastAPI `/metrics` endpoint.
- Circuit breaker openings (`CircuitBreakerOpenEvents`) to surface resilience issues in upstream services.
- OpenFGA, OPA, and legacy telemetry-worker availability checks.

> Mirror files exist under `a0_data/infra/observability` so baked images receive identical configuration.

## How to run

```bash
# From repo root, start Prometheus alongside key services
docker compose up -d prometheus delegation openfga opa
```

Prometheus listens on `http://localhost:9090`. Open the **Alerts** and **Graph** tabs to inspect rules (`infra/observability/alerts.yml`) and live metrics. To reload Prometheus after editing `alerts.yml`, restart the container or trigger a configuration reload:

```bash
docker compose exec prometheus kill -HUP 1
```

## Validation checklist

- Delegation gateway `/metrics` responds with Prometheus exposition format.
- Prometheus `Alerts` UI shows `GatewayHighLatencyP95`, `GatewayHighErrorRate`, and `CircuitBreakerOpenEvents` after sending load / triggering failures.
- The `circuit-breakers` job appears under **Status → Targets** after the gateway boots (requires `CIRCUIT_BREAKER_METRICS_PORT` to be non-zero in the gateway container).
- Force a failure (e.g., return synthetic 500s) to see `GatewayHighErrorRate` transition to `Pending`.
- Stop the OpenFGA container; Prometheus should mark `OpenfgaDown` pending within ~2 minutes.

## Next steps

- Wire alert notifications to Alertmanager once an endpoint is available.
- Replace the legacy telemetry-worker alert with a live target or remove it if unused.
- If you need dashboards, integrate with an external Grafana instance or lightweight alternatives such as `promxy`/`promdash`.
- Tune the exporter via `CIRCUIT_BREAKER_METRICS_PORT` / `CIRCUIT_BREAKER_METRICS_HOST` on any service that imports `python.helpers.circuit_breaker` to expose the counters from other components.
