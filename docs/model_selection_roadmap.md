# Automated LLM Selection Roadmap

## Vision
Give operators and end users the best response quality for the lowest cost without manual babysitting. The router evaluates every conversation against real-time performance metrics and automatically chooses the most efficient LLM profile that still meets persona-specific SLAs. Operators can override the choice per tenant or persona through the upcoming Command Center UI, while SLM and micro-LLM tiers stay disabled until we revisit mobile and edge constraints.

## Guiding Principles
- **Cost-aware by default**: Compute `cost_per_completion` and `tokens_per_success` from telemetry to rank candidates automatically.
- **Persona fidelity**: Respect persona SLAs (latency, safety, accuracy) when selecting the cheapest model.
- **Safe overrides**: Expose deterministic overrides with clear audit trails through the settings service and UI.
- **Telemetry-first**: Every routing decision publishes structured events so scorecards reflect the chosen model, reason, and outcome.
- **Feature-flagged**: Keep rollout under `AUTO_MODEL_SELECTION_ENABLED` for gradual adoption.

## Release Goals
1. Automated selection operational in development with clear dashboards proving cost/performance wins.
2. Override experience shipped in the Command Center tab, including toast confirmations and persistence through settings APIs.
3. Back-end contracts and telemetry schemas stable so future SLM tiers can plug in without churn.

## High-Level Phases

### Phase A – Foundations (Telemetry + Scoring)
- Extend telemetry publisher/store to record `cost_per_1k_tokens`, `success_rate_24h`, and `latency_p95` for each profile.
- Build ClickHouse roll-ups (5m/1h/24h) exposed via the model metrics API.
- Add router scoring module that ranks profiles per persona using weighted scoring (default weights: cost 0.5, success 0.3, latency 0.2).
- Introduce feature flag `AUTO_MODEL_SELECTION_ENABLED` to gate the behavior.

### Phase B – Dynamic Routing
- Update conversation worker to request top-ranked profile when the flag is on, with fallback to current default on errors/timeouts.
- Emit `router.selection` events detailing candidate list, chosen profile, and decision rationale.
- Persist last-selected profile per conversation for audit/debug.
- Add regression tests covering selection logic, fallbacks, and feature-flag toggles.

### Phase C – Operator Controls & UX
- Extend settings service to allow per-tenant and per-persona overrides, including optional lock to a specific profile.
- Surface overrides plus telemetry snapshots in the Command Center tab (build on `docs/ui_roadmap.md`).
- Add confirmation toasts and activity log entries when overrides change.
- Document runbooks for enabling/disabling the flag, interpreting scorecards, and troubleshooting.

### Phase D – Hardening & Rollout
- Run load tests comparing cost/performance before and after enabling auto-selection.
- Define production rollout checklist (flag strategy, observability checks, rollback).
- Train support teams; update `docs/SomaAgent01_Modes.md` and `docs/SomaAgent01_Telemetry.md` with finalized schemas.

## Sprint Breakdown (2-week cadence)

| Sprint | Key Deliverables |
| --- | --- |
| **Sprint 1 – Telemetry Lift** | ClickHouse roll-ups, telemetry schema updates, unit tests, draft dashboards. |
| **Sprint 2 – Scoring Engine** | Router scoring module, feature flag plumbing, regression tests, initial cost/success analysis notebook. |
| **Sprint 3 – Dynamic Routing Beta** | Conversation worker integration, `router.selection` events, QA in development environment, cost/performance comparison report. |
| **Sprint 4 – Operator Controls** | Settings service overrides, Command Center UI cards, toast + audit logging, Cypress smoke tests. |
| **Sprint 5 – Hardening & Rollout** | Load tests, runbooks, documentation updates, production readiness review, staged rollout plan. |

## Dependencies
- Telemetry aggregation tasks from `docs/SomaAgent01_Telemetry.md`.
- Command Center UI roadmap (`docs/ui_roadmap.md`).
- Feature flag infrastructure (LaunchDarkly or internal toggle service).

## Risks & Mitigations
- **Telemetry lag**: Mitigate with roll-ups and fallback to default profile if metrics older than 15 minutes.
- **Override confusion**: Provide clear UI copy and audit log entries.
- **Flag misconfiguration**: Include health checks that alert if auto-selection is on but telemetry freshness is stale.

## Success Metrics
- ≥15% reduction in cost per essay-like completion in development benchmarks.
- Zero increase in escalation or safety violation rates.
- Operators can change override within 3 clicks; change appears in audit log within 10 seconds.
- Incident response playbook published before production rollout.
