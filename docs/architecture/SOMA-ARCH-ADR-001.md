# SOMA-ARCH-ADR-001 — Architecture Decision: Shared Embedding Dimension is 768

## Document Control

| Field | Value |
|---|---|
| Document Title | Architecture Decision: Shared Embedding Dimension is 768 |
| Document Identifier | SOMA-ARCH-ADR-001 |
| Version | 1.0.0 |
| Date | 2026-10-03 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2027-01-03 |
| Related | `docs/architecture/SOMA-ARCH-INVARIANTS-001.md` §2, `docs/iso/SOMA-TRIAD-ARCH-001.md` §12 |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-03 | SomaTech Engineering | Initial issue. Records the single embedding dimension shared by the agent seam and SomaFractalMemory, and the evidence for it. Resolves the 256-vs-768 divergence that existed between `SOMA-ARCH-INVARIANTS-001` and `SOMA-TRIAD-ARCH-001`. |

## Status

**Accepted** — this is what the code already does. The ADR records the decision
so the three documents cannot drift again.

## Context

The agent seam and SomaFractalMemory share one vector space. Milvus
collections are fixed-dim at creation. A dim mismatch is a hard failure, not a
soft one. Before this ADR, `SOMA-ARCH-INVARIANTS-001` said the default was
**256** and `SOMA-TRIAD-ARCH-001` said **768**. One of them had to be wrong.

## Decision

**The shared embedding dimension is 768.** `MEM_EMBED_DIM` (agent) equals
`SOMA_VECTOR_DIM` (SFM) equals `DEFAULT_MEM_EMBED_DIM` equals 768.

768 is not arbitrary: it is the hidden size of the embedding model the agent
seam uses (`microsoft/codebert-base`) and the dim the Milvus collection was
created at.

## Evidence (code, 2026-10-03)

| Where | Value | File:line |
|---|---|---|
| Agent seam constant | `DEFAULT_MEM_EMBED_DIM = 768` | `services/common/memory_contract.py:43` |
| Agent env default | `MEM_EMBED_DIM = int(os.environ.get("MEM_EMBED_DIM", "768"))` | `config/settings.py:116` |
| Gateway settings | same, default `"768"` | `services/gateway/settings.py:254` |
| Unified settings | `SOMA_VECTOR_DIM = int(os.environ.get("SOMA_VECTOR_DIM", "768"))` | `infra/aaas/unified_settings.py:315` |
| SFM TUNABLES | `SOMA_VECTOR_DIM`: `Tunable("int", 768, ...)` | `somafractalmemory/settings/model.py:121-126` |
| SFM refuses to guess | raises if `SOMA_VECTOR_DIM` is not configured | `somafractalmemory/admin/core/services.py:131-133` |
| Compose | `MEM_EMBED_DIM=${MEM_EMBED_DIM:-768}` | `infra/standalone/docker-compose.yml:105` |
| AAAS example | `SFM_VECTOR_DIM=768` | `infra/aaas/aaas/.env.example:60` |
| Enforcement test | `tests/unit/test_embed_dim_seam_768.py` pins 768 and bans 1536 | that file, assertions at 19-76 |

No file in either repository uses 256 as an embedding dimension. Literal `256`
hits are SHA-256, 256-bit tokens, `--maxmemory 256mb`, and `X-Hub-Signature-256`.

## Consequences

1. `SOMA-ARCH-INVARIANTS-001` §2 and §6 are corrected to 768.
2. `SOMA-TRIAD-ARCH-001` already said 768; its F-11 (latent 256 fallback in
   SFM) is marked **FIXED** — the fallback is gone and SFM now refuses to guess.
3. Any future dim change is a coordinated change across agent settings, SFM
   `TUNABLES`, and `tests/unit/test_embed_dim_seam_768.py`. It cannot be made
   on one side only.
4. Precomputed embeddings are the real path; SFM's `HashEmbedder` is a fallback
   when no vector is supplied. Hash hits are demoted (`SOMA_HASH_EMBEDDING_PENALTY`).

## Alternatives considered

| Alternative | Why rejected |
|---|---|
| 256 | No code uses it. It was a stale default in one document and a deleted fallback literal in SFM. |
| Per-deployment configurable dim | It already is (`MEM_EMBED_DIM` / `SOMA_VECTOR_DIM`), but the two must match. The *default* is 768 and is pinned by test. |
| Let each store re-embed | Violates the one-embedding-authority invariant (INVARIANTS §2). SFM's hash embedder is not semantic.
