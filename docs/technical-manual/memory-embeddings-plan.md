# Memory & Embeddings Plan

## Current Pipeline
1. Gateway writes memory events (remember) → Memory Write Outbox (Postgres) as fallback.
2. `memory_sync` publishes to `memory.wal` topic.
3. `memory_replicator` consumes WAL, writes replica table (`memory_replicas`).
4. Query endpoints read from replica (fast path) with filters.

## Gaps
- No vector embeddings abstraction (embedding function provider variance).
- No TTL/compaction strategy (potential unbounded growth).
- No memory importance scoring for prioritization.

## Abstraction Proposal
`MemoryStore` interface:
- `add(memory_event)`: returns ID and embedding vector metadata.
- `search(query_vector, filters, limit, min_score)`.
- `compact(strategy)`: perform TTL or size-based pruning; strategies: `ttl`, `lru`, `importance`.

Vector Layer:
- Pluggable provider (OpenAI, local model) via `EmbeddingProvider` with `embed_text(list[str])`.
- Cache embeddings keyed by sha256(text) to avoid recompute.

Schema Additions:
- `embedding` (vector serialized as list[float] or binary) column in replica table.
- `score` / `importance` field numeric.
- `expires_at` for TTL-managed memories.

Metrics:
- `memory_embeddings_total{provider}`
- `memory_embedding_latency_seconds{provider}`
- `memory_replica_rows_total` gauge
- `memory_compaction_rows_deleted_total{strategy}`

Background Jobs:
- Embeddings backfill: scan rows without embedding, compute, update.
- Compaction job: run interval (e.g., 10m) applying strategy (default TTL days from config overlay).

Search API Upgrade:
- Add `/v1/memory/search` accepting hybrid params: text query, semantic toggle, filters.
- If semantic enabled: embed query; perform vector similarity; merge with keyword results.

Phased Delivery:
Phase 1: Embedding provider + schema column + ingestion embedding.
Phase 2: Search endpoint hybrid; metrics instrumentation.
Phase 3: Compaction + TTL + importance scorer (simple heuristic: length + recency weight).
Phase 4: Provider registry + multi-model A/B support.

Risks & Mitigation:
- Vector size inflation: enforce max embedding dimensions and provider-specific normalization.
- Long compute times: asynchronous embedding pipeline + caching.
- Backward compatibility: embedding column nullable; queries fallback to keyword search.

Next Steps:
1. Add `embedding` nullable column to replica table migration.
2. Implement `EmbeddingProvider` interface and OpenAI stub.
3. Hook provider into `memory_replicator` on consume.
4. Add metrics counters/histograms.
5. Implement `/v1/memory/search` hybrid endpoint.
6. Compaction + TTL job scaffold.
