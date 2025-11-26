# Neuromodulation and Sleep Consolidation

## Overview
Sprint 5 introduced advanced cognitive features to the Conversation Worker:
1.  **Neuromodulation**: A `DecisionEngine` that uses simulated neurotransmitters (Dopamine, Serotonin) to modulate decision-making (GO/NOGO).
2.  **Sleep Consolidation**: A background process that triggers memory consolidation during periods of inactivity.

## Architecture

### Decision Engine (`services/conversation_worker/decision_engine.py`)
The `DecisionEngine` replaces the legacy `_basal_ganglia_filter`. It maintains a `NeuroState` for each interaction.

#### NeuroState
-   **Dopamine**: Represents reward/action bias. High dopamine lowers the urgency threshold for action.
-   **Serotonin**: Represents mood stability. High serotonin dampens extreme urgency, promoting deliberation.

#### Decision Logic
Effective Urgency is calculated as:
`Effective Urgency = Base Urgency + (Dopamine Bias) - (Serotonin Dampening)`

-   **GO**: Effective Urgency >= 0.8
-   **NOGO**: Effective Urgency <= 0.3

### Sleep Consolidation (`services/conversation_worker/main.py`)
A background loop (`_sleep_consolidation_loop`) monitors agent activity.

-   **Inactivity Threshold**: 60 seconds (default).
-   **Action**: Calls SomaBrain `/memory/consolidate` endpoint.
-   **Interval**: Consolidation occurs at most once every 5 minutes.

## Verification

### Neuromodulation
To verify the Decision Engine:
1.  Send a message to the agent.
2.  Check logs for `DecisionEngine` activity:
    ```bash
    docker logs somaAgent01_conversation-worker | grep "DecisionEngine"
    ```
3.  Observe "Basal Ganglia GO" or "Basal Ganglia NOGO" logs with reasons derived from `NeuroState`.

### Sleep Consolidation
To verify Sleep Consolidation:
1.  Start the `conversation-worker` service.
2.  Wait for the inactivity threshold (60s).
3.  Check logs for consolidation trigger:
    ```bash
    docker logs somaAgent01_conversation-worker | grep "Sleep consolidation"
    ```
    - Expected: "Sleep consolidation loop started" (on startup)
    - Expected: "Inactivity detected, triggering sleep consolidation" (after delay)

## Future Work
-   **Persistence**: Persist `NeuroState` to the database (Sprint 6).
-   **Complex Dynamics**: Implement non-linear neurotransmitter decay and interaction.
