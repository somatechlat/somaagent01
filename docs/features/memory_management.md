# Memory Management Guide

## Overview
SomaBrain ensures agents remember key facts across sessions. This guide teaches humans and automations how to curate and leverage memory entries.

## Concepts

- **Memory Item:** Structured JSON payload keyed by domain (`user.preference.language`).
- **Persona Scope:** Each memory tied to tenant + persona to avoid cross-contamination.
- **Relevance Score:** Determines ranking when prompt budget is tight.

## Creating Memories

### Humans via UI
1. Ask agent to "Remember that I prefer dark mode".
2. Gateway stores structured memory under `UserPreference` schema.
3. Verify in Settings → Memory dashboard (coming soon).

### Automations via API
```python
from python.helpers.memory import save_memory

save_memory(
    key="project.stack",
    payload={"backend": "FastAPI", "frontend": "Alpine"},
    type="ProjectDecision",
    relevance=0.9,
)
```

## Retrieving Memories

```python
from python.helpers.memory import search_memory

items = search_memory(key_prefix="project.", limit=3)
for item in items:
    print(item.payload)
```

LLM prompts include selected memories at conversation start; review `docs/architecture/components/memory.md` for pipeline.

## Best Practices

- Keep payload concise (< 400 tokens).
- Store provenance (`source`, `date`) to aid troubleshooting.
- Regularly prune obsolete entries (e.g., deprecated stack choices).

## Limitations

- Prompt window finite (~4k tokens). High-volume memories require ranking.
- Memory is explicit—if never stored, LLM cannot infer it later.

## Auditing

- Use Postgres queries to inspect `memory_items` table.
- Build dashboards to review memory churn, relevance distribution.

## Roadmap

- Memory dashboard UI with edit/delete.
- Semantic clustering for automatic summarization.
- Retention policies per tenant persona.
