⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# SomaAgent 01 Observability

## Grafana Dashboard
- `infra/observability/grafana-dashboard-somaagent01.json` defines an open-source Grafana dashboard with panels for:
  - SLM latency (`slm_latency_seconds` time series).
  - Budget events table (increase of `budget_events_total`).
- Import into Grafana (OSS) to visualize agent health.

## Metrics Endpoints
- Gateway/worker/tool/audio services expose Prometheus metrics via default `/metrics`.
- Prometheus scrape configs defined in `infra/observability/prometheus.yml`.

## Telemetry Data
- Kafka topics: `slm.metrics`, `tool.metrics`, `budget.events`, `audio.metrics`.
- Stored in Postgres via `TelemetryStore` for dashboards and scoring jobs.

## Regression
- Policy regression script `scripts/run_policy_regression.sh` ensures OPA policies remain correct.
- CLI `scripts/send_message.py` verifies end-to-end message loop.
