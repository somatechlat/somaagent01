⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# SomaAgent 01 Model Scoring Job

## Purpose
Aggregates telemetry recorded in Postgres (`slm_metrics`) and computes per-model scores over a rolling window. Results are stored in `model_scores` for the model profile service/UI to consume.

## Location
`services/scoring_job/main.py`

## Behaviour
- Window size configurable via `SCORING_WINDOW_HOURS` (default 6 hours).
- Runs continuously (interval `SCORING_INTERVAL_SECONDS`, default 3600 seconds) updating scores.
- Score formula (heuristic): `score = 1 / (1 + latency + tokens/1000)` where lower latency/token usage yields higher scores.
- Writes results to `model_scores` using `TelemetryStore.save_model_score`.

## Inputs
- `slm_metrics` table populated by conversation worker telemetry.
- Runtime mode (`SOMA_AGENT_MODE`) to tag scores with the correct deployment context.

## Outputs
- `model_scores` table rows (model, deployment_mode, window start/end, avg latency, avg tokens, score).
- Logs describing updates for auditing.

## Next Steps
- Enhance scoring to incorporate refusal rates and reliability once telemetry is expanded.
- Wire scores into the settings UI to recommend model profile upgrades/downgrades automatically.
