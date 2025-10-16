---
title: SomaBrain Memory Subsystem
slug: technical-memory
version: 1.0.0
last-reviewed: 2025-10-15
audience: platform-engineers, data engineers
owner: platform-architecture
reviewers:
  - infra
  - data-platform
prerequisites:
  - Access to SomaAgent01 repository
  - Basic understanding of Redis and Postgres
verification:
  - Memory save/load/search integration tests pass
  - Redis and Postgres health checks green
---

# SomaBrain Memory Subsystem

## Role

Provide durable, queryable factual context so LLM agents operate with continuity and verifiable truths.

```mermaid
classDiagram
    class MemoryItem {
        string id
        string key
        string type
        string tenant_id
        string persona_id
        datetime created_at
        float relevance
        dict payload
    }

    class MemoryStore {
        +save(item: MemoryItem)
        +load(key: str) MemoryItem
        +search(query: MemoryQuery) list~MemoryItem~
        +delete(id: str)
    }

    class MemoryQuery {
        string key
        string text
        string type
        float min_relevance
        int limit
    }

    MemoryStore --> MemoryItem
    MemoryStore --> MemoryQuery
```

- **Key:** stable identifier (for example `user.preferences.format`).
- **Type:** schema namespace (`UserPreference`, `ProjectDecision`).
- **Payload:** JSON encoded data validated by Pydantic models.

## Storage Layers

| Layer | Technology | Purpose |
| --- | --- | --- |
| Hot cache | Redis | Millisecond access to recent entries |
| Durable store | Postgres (`memory_items` table) | Long-term persistence |
| Indexing | Optional Qdrant / embeddings | Semantic search for fuzzy recall |

Adapters under `python/helpers/memory/` keep the codebase provider-agnostic.

## API Surface

| Function | Location | Description |
| --- | --- | --- |
| `memory_save` | Gateway tool call | Persist structured payload with TTL/relevance |
| `memory_load` | Gateway tool call | Retrieve by key (exact match) |
| `memory_search` | Gateway tool call | Retrieve by vector/text query |
| `AgentContext.memory` | Runtime helper | Wraps the above with persona scoping |

## Retrieval Workflow

1. Gateway receives conversation request.
2. Extracts tenant/persona identifiers.
3. Runs `memory_search` per persona configuration (`conf/tenants.yaml`).
4. Injects selected memories into system prompt.
5. After response, new facts summarized and written via `memory_save`.

## Best Practices

- Store structured JSON (Pydantic models → dictionaries).
- Include metadata such as author, confidence, source, expiry.
- Keep entries concise (<400 tokens) to avoid prompt overflow.
- Prune stale items via background jobs.

## Machine Integration

```python
from python.helpers.memory import save_memory, search_memory

save_memory(
    key="project.decisions.backend",
    payload={"stack": "FastAPI", "decision_date": "2025-10-01"},
    type="ProjectDecision",
)

recent = search_memory(key_prefix="project.decisions", limit=5)
```

## Failure Considerations

| Issue | Impact | Mitigation |
| --- | --- | --- |
| Redis eviction | First lookup slower (fallback to Postgres) | Warm cache via background worker |
| Postgres outage | Memory writes fail | Retry with backoff, surface warning |
| Schema drift | Payload parsing errors | Version schemas, migrate data periodically |

## Roadmap

- Embedder-backed semantic search (Qdrant).
- Tenant-level retention policies / GDPR hooks.
- Automated summarization when memory exceeds token budgets.
