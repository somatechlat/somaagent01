# UI-S-05 — Body — resources & limits

Screen UI-S-05 · Facet: Body · Route: NEW (not present in `webui/src/main.ts` today).
Source view per `SOMA-UI-IDREG-001.md`: NEW.

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  Memory  ( Body )  Governance ──────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Body [1]                                        │ SURFACES x8             │
│  Chat    │ ┌────────────────────────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule │ │ QUOTAS [2]                                             │  │ [Editor][Debug][Capsule]│
│  Module  │ │  disk  ‹quota.disk›     egress ‹quota.egress›         │  │ [Brain][Desktop†] †GATED│
│  Platform│ │ LIMITS [3]                                             │  │                         │
│  Ops     │ │  concurrency ‹limit.concurrency›                       │  │                         │
│  Settings│ │  request timeout ‹limit.timeout›                       │  │                         │
│          │ │  budget alert   ‹limit.alert›                          │  │                         │
│          │ │ ── derived AgentIQ (READ-ONLY) [4] ────────────────────│  │                         │
│          │ │  token_limit ‹›     cost_tier ‹›     thinking_budget ‹›│  │                         │
│          │ │  egress_allowed ‹›                                     │  │                         │
│          │ │                                                            │  │                         │
│          │ │ CURRENT USAGE [5]  ‹ live value ›   as of ‹ timestamp › │  │                         │
│          │ │ [ Apply limits ] [6]     [ Revert ] [7]                 │  │                         │
│          │ └────────────────────────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Body) | Screen shell. |
| 2 | UI-C-051 | Quota fields (disk, egress) | Numeric; validated against tenant plan as stored. |
| 3 | UI-C-052 | Limit fields (concurrency, timeout, alert threshold) | Numeric; never pre-filled with invented defaults. |
| 4 | UI-C-008 | Derived AgentIQ readout (token_limit, cost_tier, thinking_budget, egress_allowed) | READ-ONLY, greyed. House rule: never inputs. |
| 5 | UI-C-053 | Current usage readout | READ-ONLY `‹ live value ›` + `‹ timestamp ›`. |
| 6 | UI-A-017 | Apply limits | Writes Body limits to the active capsule. |
| 7 | UI-A-008 | Revert | Discards unsaved limit edits. |

## 3. State variants

- **loading** — Fields skeleton; usage readout verbatim: "Loading usage…"
- **empty** — Fields blank with helper (verbatim): "No limits set for this capsule. Platform defaults apply."
  Usage readout verbatim: "No usage recorded yet."
- **error** — `UI-C-024` verbatim: "Resource limits could not be loaded. Retry, or check that the
  somaAgent01 API is reachable." Apply failure verbatim: "Limits were not applied. Your values are still here."
- **permission-denied** — Fields read-only; `UI-C-025` verbatim:
  "You do not have permission to change resource limits. Ask a platform admin for the tenant-admin role."
- **offline** — Apply disabled with inline reason "Apply is unavailable offline."
  Usage readout keeps its last value and timestamp.

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| UI-A-017 when a limit would exceed the plan | UI-M-03 Dialog | "These limits exceed ‹plan.name›. Apply anyway?" Cancel / Apply. |
| UI-A-008 with unsaved edits | UI-M-03 Dialog | "Discard unsaved limit edits?" Cancel / Discard. |
| — | UI-M-01 / UI-M-02 | Not used by this screen. |

## 5. Honesty notes

Quota, limit and usage values are placeholders. `token_limit`, `cost_tier`, `thinking_budget` and
`egress_allowed` are derived AgentIQ settings and appear only as greyed readouts.

End of Document
