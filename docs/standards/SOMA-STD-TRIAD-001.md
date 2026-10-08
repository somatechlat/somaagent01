# SOMA-STD-TRIAD-001 — Shared rules for somaAgent01 · somabrain · somafractalmemory

## Document Control

| Field | Value |
|---|---|
| Document Title | Shared triad rules (same stack, same rules, all three repos) |
| Document Identifier | SOMA-STD-TRIAD-001 |
| Version | 1.0.0 |
| Date | 2026-10-08 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2027-01-08 |
| Related | `docs/standards/SOMA-STD-CODING-001.md`, `docs/standards/SOMA-RAPID-DEVELOPMENT-001.md`, `docs/plans/SOMA-AGENT-HANDOFF-001.md` |
| Audience | Every agent and human working the triad |
| Scope | All three repos; A2A peers included |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-08 | SomaTech Engineering | Initial issue. Single rule pack for triad agents. |

---

## 1. Why this file exists

Three repos, one product. Every agent (MiMoCode, Claude Code, Codex) must load **the same**
rules before editing. Project files reference this file; they do not fork it.

| Repo | Role |
|---|---|
| `somaAgent01` | Agent runtime, Django API, Lit UI, Temporal workers, memory seam client |
| `somabrain` | Brain: memory, cognition, neuromod, sleep, outbox |
| `somafractalmemory` | SFM: long-term store, Milvus, graph |

---

## 2. THE ONE PATH (never create a lane)

```
browser → WS /ws/v2/chat/{capsule_id} → ChatConsumer → V3ChatOrchestrator
  → run_tool_loop → FanoutMemoryGateway → SomaBrainAdapter → SomaBrain → SFM
```

**T-1:** Agent never holds an SFM client. Memory I/O only through `MemoryGateway` → `SomaBrainAdapter`.
**T-6:** Durable-before-hop, not after-failure.
Forbidden: new WS route · new orchestrator · new memory client · direct SFM · new auth check · temporary endpoint · shim.

---

## 3. Non-negotiable rules (load-bearing)

| # | Rule |
|---|---|
| 1 | **No hardcoded values** — no literal URL, host, port, path, or number in application code. A default IS a hardcoded value. Declaration-site only (R-VAL-04). |
| 2 | **No fallbacks** — missing setting = refusal naming the setting. |
| 3 | **One settings chain** — Capsule → AgentSetting → InfrastructureConfig → SettingsModel → RAISE. Env is topology only. Secrets = Vault only. Never invent a setting name. |
| 4 | **No stubs, mocks, shims, TODOs, placeholders.** Fix the consumer; delete the old path. |
| 5 | **Vault-only secrets.** KV v2 POST replaces the whole document — read → merge → write full → read back. |
| 6 | **Fail-closed.** Never guess a host or credential. |
| 7 | **Never weaken a gate to pass a test.** |
| 8 | **Check first, code second.** Read architecture and full files. If context missing, ask. |
| 9 | **No unnecessary files.** Delete; do not back up. |
| 10 | **Documentation = truth.** Cite `file:line`. Code wins. |
| 11 | **Commits:** user's git identity only. **No AI attribution** of any kind. |
| 12 | **Design criteria:** rules · millions of transactions · security · speed · latency · thin. |

### Stack lock (same on all three repos)

| Layer | Choice | Forbidden |
|---|---|---|
| Agent API | Django 5 + Django Ninja | FastAPI |
| ORM | Django ORM | SQLAlchemy, Alembic |
| Frontend | Lit 3.x | React, Alpine.js |
| Vector | Milvus | Qdrant |
| Memory path | MemoryGateway → SomaBrain → SFM | Direct SFM from agent |
| Async | Temporal owns long/scheduled work | Parallel cron/queue authorities |
| Proof | Real infra + Playwright human session | Source-grep as proof, skip-to-green |

---

## 4. A2A (always on)

- Claim before edit: `docs/plans/a2a/CLAIMS.md`
- Log commits: `docs/plans/a2a/LEDGER.md`
- Messages: `INBOX.md` / `OUTBOX.md` — append-only
- Partition: somabrain seat owns `somabrain/memory/*`; somaAgent01 seat owns `webui/`, `docs/design/`, agent seam
- Handshake before large waves

---

## 5. Every wave = builder + adversarial skeptic

Operator standing order: deploy skeptics in parallel with builders. Findings need
`file:line`, severity, DELETE-or-IMPLEMENT. No wave is done until ADV is clean or
defects are queued in the ledger.

---

## 6. Done definition

`tests/e2e/test_human_chat_session.spec.js` (or repo-equivalent live gate) green
against **real** services — not skipped, not mocked.
