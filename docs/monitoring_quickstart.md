# Monitoring Quickstart

This guide summarizes the current Prometheus and Grafana setup that ships with the SomaAgent01 development stack.

## Prometheus

- **Service**: `prometheus` container in `docker-compose.somaagent01.yaml`
- **Config path**: `infra/observability/prometheus.yml`
- **Alert rules**: `infra/observability/alerts.yml`
- **Profiles**: Start with the `metrics` Docker Compose profile to include Grafana along with Prometheus.

Key scrape jobs:
- `prometheus`: self-scrape for diagnostics.
- `delegation-gateway`: collects FastAPI metrics exposed at `http://delegation:8015/metrics`.
- `openfga`: scrapes the OpenFGA exporter port (`:2112`).
- `opa`: collects metrics from OPA on port `8181`.

Alert coverage:
- Delegation gateway availability, 5xx error rate (>5%) and p95 latency (>1s sustained for 10 minutes).
- OpenFGA and OPA availability checks.
- Legacy telemetry-worker availability placeholder kept for future wiring.

> Mirror files exist under `a0_data/infra/observability` so baked images receive identical configuration.

## Grafana

- **Service**: `grafana` container (optional; enabled with `metrics` profile).
- **Provisioning**: `infra/observability/grafana/provisioning/dashboards/dashboards.yaml` registers a file provider pointing to `/etc/grafana/dashboards`.
- **Dashboards**: JSON files in `infra/observability/grafana/dashboards/`; currently ships with `delegation-gateway.json`.

When the stack starts with the metrics profile, Grafana mounts both provisioning and dashboards directories, so dashboards auto-import on startup.

## How to run

```bash
# From repo root
docker compose --profile metrics up -d prometheus grafana delegation openfga opa
```

Once containers are healthy:
1. Open Grafana at http://localhost:3000 (default admin password prompt is disabled; login as `admin`/`admin` if prompted).
2. Navigate to **Dashboards → Browse** and open "Delegation Gateway Overview".
   - Use the method/path template variables to filter metrics.
3. Check **Alerting → Alert rules** to confirm the delegation, OpenFGA, and OPA alerts are loaded.

To reload Prometheus after editing `alerts.yml`, restart the container or trigger a configuration reload:

```bash
docker compose exec prometheus kill -HUP 1
```

## Validation checklist

- Delegation gateway `/metrics` responds with Prometheus exposition format.
- Grafana dashboard shows non-empty request rate and latency graphs after sending traffic to the gateway.
- Force a failure (e.g., return synthetic 500s) to see the "High Error Rate" alert rule transition to `Pending`.
- Stop the OpenFGA container; Prometheus should mark `OpenfgaDown` pending within ~2 minutes.

## Next steps

- Add additional dashboards (e.g., OpenFGA, Kafka) by dropping JSON exports into the dashboards directory.
- Wire alert notifications to Alertmanager once an endpoint is available.
- Replace the legacy telemetry-worker alert with a live target or remove it if unused.
