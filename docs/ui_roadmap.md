# Settings Command Center UI Roadmap

## Vision
Transform the existing settings modal into a command-center experience without rewriting core components. Reuse the current Alpine.js modal, tab scaffold, and field renderer to present a richer, multi-pane control surface that centralizes environment, model, and budget management.

## Guiding Principles
- **Reuse, dont replace**: Extend the current modal partials and CSS tokens; avoid net-new frameworks.
- **Progressive disclosure**: Keep the modal launch/lightweight for quick tweaks while adding deeper drill-down panels behind tabs and accordions.
- **Telemetry-first**: Surface live health, throughput, and escalation metrics alongside controls to encourage informed changes.
- **Role-aware defaults**: Mirror the back-end `ModelProfileStore` to present tailored defaults (developer, researcher, etc.) and allow safe overrides.

## Phased Rollout

### Phase 1 8d)
- Add a dedicated "Command Center" tab leveraging the existing tab component.
- Render a read-only overview card set using the field renderer (environment, active model box, throughput).
- Introduce quick-links to existing sections (credentials, budgets) via `handleFieldButton` actions.

### Phase 2 8d)
- Build model management cards that map directly to profile definitions (current model, fallback, escalation ladder).
- Allow in-modal switching between saved profiles and ad-hoc overrides stored in the settings service.
- Integrate telemetry spark-lines (reuse existing SVG partials) showing latency, token usage, escalation counts.

### Phase 3 9-12d)
- Add automation toggles (auto-escalate, budget guardrails) with instant feedback from the telemetry publisher.
- Surface live incident banners fed by the notifications service.
- Enable export/import of profile bundles through the existing download/upload pipeline.

## Backlog & Dependencies
- Backend: extend `/settings_get` to return profile summaries, recent telemetry, and linked automation states.
- Telemetry: ensure ClickHouse aggregations expose 5/30/120-minute rollups for latency and escalation signals.
- UI assets: create reusable card/metric partials in `webui/partials/` to avoid duplication.
- QA: add Cypress smoke tests covering tab navigation and critical toggles.

## Risks & Mitigations
- **Payload bloat**: keep telemetry snapshots capped; paginate detailed history via on-demand fetches.
- **Modal overload**: maintain a primary/secondary layout with collapsing accordions to prevent scroll fatigue.
- **State drift**: rely on Alpine store two-way binding and server-side validation to reject conflicting edits.

## Success Criteria
- Command Center tab loads within 250ms on broadband.
- Key metrics (model, latency, escalation status) visible without scrolling.
- Switching profiles triggers confirmation toast and persistence via settings service API.
- No new accessibility regressions (WCAG 2.1 AA parity with current modal).
