This directory previously contained local Grafana provisioning and dashboards.

Status: Deprecated (2025-10-23)

- Grafana is no longer shipped in this repository. Dashboards now live in the external observability project.
- Keep Prometheus scrape config and alerts in this repo (infra/observability/prometheus.yml, alerts.yml).
- If you need dashboards, import them into your external Grafana and point at this stack's Prometheus.

External dashboards project: TODO: add URL once available.
