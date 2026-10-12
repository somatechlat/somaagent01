> **SUPERSEDED BY `SOMA-ARCH-JEV-002` (2026-10-09).** Do not implement from this document.
> Known defects fixed in 002: noul≠confidence mapping; mandatory brain-only decision-facts; D-7 removed; no shim/mock. This file is historical only.

# SOMA-ARCH-JEV-001 — OpenJev System One decision layer for SomaAgent01

## Document Control

| Field | Value |
|---|---|
| Document Title | OpenJev System One decision layer for SomaAgent01 |
| Document Identifier | SOMA-ARCH-JEV-001 |
| Version | 1.0.0 |
| Date | 2026-10-09 |
| Status | Obsolete |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015; ISO/IEC/IEEE 29148:2018; ISO/IEC 25010:2011 |
| Next Review | 2027-01-09 |
| Related | `SOMA-JEV-INTG-001`, `SOMA-ARCH-INVARIANTS-001`, `SOMA-ARCH-TOOLS-001`, `SOMA-STD-TRIAD-001`, `SOMA-STD-CODING-001`, `SOMA-PM-PLAN-JEV-INTEGRATION-001` |
| Source of truth | Live `somaAgent01` tree + OpenJev Phase 0 sources (pinned tree at `~/dev/OpenJev`, 2026-10-09) + `SOMA-JEV-INTG-001` |
| Audience | Architecture reviewers, integration implementers, SomaTech evaluation panel |
| Scope | Decision-layer architecture: where OpenJev (JEV) attaches to SA01, which agent decisions it owns, contracts, risks. **Documentation only — no implementation code in this revision.** |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-09 | SomaTech Engineering | Initial issue. Agent-architecture-audit of SA01 decision surfaces; OpenJev capability truth-pass; seam binding; typed decision inventory; middleware architecture; risk and open questions. Docs only per operator gate. |

---

## 1. Purpose

This document is the architecture basis for integrating **OpenJev** (JEV) into
**SomaAgent01** as a **System One decision layer** — not as a chat model, not as a
memory store, not as a replacement for the V3 orchestrator.

It answers three questions:

1. What is broken or fragile in SA01's decision path today (agent-architecture-audit)?
2. Which SA01 decisions should become **typed** `Choice` / `Score` / `Noul` calls?
3. How does OpenJev attach using **existing** control planes only?

Normative requirements live in `SOMA-JEV-INTG-001` (`JEV-R-001`…`JEV-R-019`).
Delivery waves live in `SOMA-PM-PLAN-JEV-INTEGRATION-001`.

---

## 2. Executive verdict

| Field | Value |
|---|---|
| Overall health (decision path) | **medium_risk** — platform is real and fail-closed, but **routing / guardrail / approval decisions are still free-form or rule-only** |
| Primary failure mode | **Tool discipline + untyped decisions** — “must check X” logic spread across prompts, OPA, and Python if-chains with no calibrated probability and no single choke |
| Most urgent fix | Insert a **typed decision choke** (OpenJev-backed) at tool-approval and tool-guardrail points **before** tool execution — code-gated, not prompt-only |
| OpenJev fit | **High** for Noul/Choice/Score micro-decisions; **zero** fit for chat completion (Seam A correctly excluded) |

**Direct diagnosis:** SA01 is not “broken” in the wrapper-regression sense. The
V3 orchestrator, UnifiedGate, T-1 memory seam and tool registry are coherent.
The gap is that the *cognitive* decisions around tools — approve, escalate,
which tool, how severe — are expressed as boolean policy, if-chains, or implied
by the chat model’s own free text. That is exactly the domain OpenJev’s System
One primitives are for: **typed answers with probabilities in one forward pass.**

---

## 3. Scope of this architecture

| In scope | Out of scope |
|---|---|
| SA01 decision-path audit (12-layer agent stack) | Changing OpenJev model quality or training |
| OpenJev Phase 0 capability truth-pass | Billing / Soma Platform commercial packaging |
| Seam binding (B/C/D/E per `SOMA-JEV-INTG-001`) | Replacing the chat LLM (Seam A — excluded) |
| Typed decision inventory for SA01 | Implementation code (gated; see plan) |
| Contracts: invocation, authz, memory, observability | Operations after hand-over |
| Risk register and open questions | Multi-tenant Soma Platform pilot scope (open Q) |

---

## 4. OpenJev truth-pass (what JEV actually is)

Confirmed from the OpenJev Phase 0 tree (clone + 59/59 platform probes, 2026-10-09):

| Aspect | Finding |
|---|---|
| Nature | **Decision engine**, not a chat model. One forward pass; logits over *your* labels only |
| Primitives | `Choice` (2–255 options) · `Score` (2–10 ordered levels, probability-weighted) · `Noul` (P(true) in [0,1]) |
| Shipped interfaces | Python library + Claude Code style REPL + `openjev --file` |
| Roadmap interfaces | Phase 1 `openjev serve` (FastAPI `POST /v1/systemone`); Phase 3 agent middlewares |
| Backends today | `mock` (deterministic, CI-safe) · `hf` (Transformers, CPU/CUDA/MPS) |
| Latency (measured) | Mock: **~1.5 ms** for 4 mixed questions. HF small model: **~100–330 ms** per pass (docs claim) |
| Output shape | Jev-compatible: `answers.{id}.{type,choice|score|noul,probabilities,confidence}` + `usage` + `latency_ms` |
| Confidence | `1 - normalized entropy` of label distribution (transparent approximation of TypeSafe) |
| Closed-world | Softmax over label tokens only — nothing outside the option set can win |
| Status | Phase 0 **alpha** — pin a commit/tag; adapter absorbs API drift |
| License | MIT |

**Consequence (binding, already agreed):** OpenJev shall **not** occupy the LLM
slot. Until Phase 1 `openjev serve` ships, any HTTP consumer needs a **thin
local shim** owned by the integration layer (not SA01 core, not OpenJev upstream).

```
            ┌─────────────────────────────────────────────────────────┐
            │                    SystemOneRequest                      │
            │  state: Any   questions: {id: Choice|Score|Noul}         │
            └───────────────────────────┬─────────────────────────────┘
                                        │ one forward pass per question
                                        ▼
   prompt(state, instructions, labels) → causal LM → logits@answer position
                                        │
                    softmax over labels only (closed world)
                                        ▼
            ┌─────────────────────────────────────────────────────────┐
            │                    SystemOneResponse                     │
            │  answers.{choice|score|noul, probabilities, confidence}  │
            │  usage · latency_ms · model                              │
            └─────────────────────────────────────────────────────────┘
```

---

## 5. Agent-architecture-audit of SA01 (12-layer stack)

Evidence collected from the live tree (file:line references are to
`somaAgent01` unless noted). Severity model per `agent-architecture-audit`:
`critical` / `high` / `medium` / `low`.

### 5.1 Layer map

| # | Layer | SA01 status | Evidence |
|---|---|---|---|
| 1 | System prompt | Real assembly in V3; module hook `system_prompt` can inject | `admin/core/chat_orchestrator.py` Phase 5 context; `admin/modules/hooks.py` `KNOWN_HOOKS` |
| 2 | Session history | V3 history + conversation-worker separate pipeline | `admin/core/chat_orchestrator.py` 12-phase; `admin/core/application/use_cases/conversation/process_message.py` |
| 3 | Long-term memory | **Strong** — T-1 single seam | `services/common/memory_contract.py` · `memory_gateway.py` · `adapters/somabrain_adapter.py` |
| 4 | Distillation | Present as memory store path, not a free-form compressor | Phase 11 `Memory Storage` in orchestrator |
| 5 | Active recall | Phase 5 “5-lane with memory recall” | `chat_orchestrator.py` ~L528 |
| 6 | Tool selection | **Partial** — default kit + capsule tools + Governor; **routing still the chat model** | Phase 7 `chat_orchestrator.py` ~L596–647 |
| 7 | Tool execution | Real engine + registry + OPA | `services/tool_executor/execution_engine.py`, `tool_registry.py`, `policy/tool_policy.rego` |
| 8 | Tool interpretation | Native tool-calls (not regex-parsed) fed back to LLM | Phase 8–9 comment: “tool_calls come back natively” |
| 9 | Answer shaping | Phase 10 Response Formatting | `chat_orchestrator.py` ~L728 |
| 10 | Platform rendering | WS frames `chat.delta` / `chat.done` | `services/gateway/consumers/chat.py` |
| 11 | Hidden repair loops | **Watch** — LiteLLM retry helpers exist; conversation-worker is a second pipeline | `admin/llm/services/litellm_helpers.py` retries; dual pipeline §7.1 AGENT.md |
| 12 | Persistence | Outbox, IdempotencyRecord, FeatureFlag, ExecutionRecord | `admin/core/models/` |

### 5.2 Findings (severity-ranked)

#### F-1 · `high` — Tool approval / guardrail is boolean, not calibrated
- **Mechanism:** Unlisted tools require approval (TOOLS-001 § policy). Dangerous
  name checks (`_name_is_safe`) and deny-lists are **hard booleans**. There is no
  P(tool_is_safe) and no severity score. The chat model can still *request* a
  dangerous tool; the human/policy only sees a gate, not a probability.
- **Source layer:** 6–7 (tool selection / execution)
- **Root cause:** decisions expressed as Rego + Python booleans without a typed
  confidence input (even though `policy/confidence.rego` already defines
  thresholds `0.3` / `min_acceptance`!)
- **Evidence:** `policy/confidence.rego` (unused confidence input surface);
  `policy/tool_policy.rego` default deny + allow lists;
  `services/conversation_worker/os_package_ensure_workflow.py:39` `_name_is_safe`;
  `services/tool_executor/tools.py` tool set
- **Recommended fix:** Feed **OpenJev `Noul` / `Score`** into the existing OPA
  `confidence` input before tool execution (see §7.3). Code-gate the call.

#### F-2 · `high` — Model / tool routing is not a typed decision
- **Mechanism:** Phase 6 `select_model` (capability superset + cost tier) and
  Phase 7 tool offering are **rule-based**; when several models/tools fit, the
  **chat model** chooses via free-text tool_calls. No `Choice` over candidates
  with probabilities.
- **Source layer:** 6
- **Root cause:** no System One micro-decision in the loop
- **Evidence:** `admin/core/model_router.py:40,126` `SelectedModel`, `select_model`;
  `chat_orchestrator.py` Phase 6–7
- **Recommended fix:** Optional **OpenJev `Choice`** router in front of
  `select_model` when `|candidates|>1`, and for tool-priority when many tools
  are offered (§7.2). Keep rule layer as floor (fail-closed).

#### F-3 · `medium` — Dual chat pipelines (V3 vs conversation-worker)
- **Mechanism:** Two independent pipelines can shape the same user-visible
  behaviour differently (wrapper divergence risk).
- **Source layer:** 2, 9, 11
- **Evidence:** `AGENT.md` §7.1; `admin/core/application/use_cases/conversation/process_message.py`
- **Recommended fix:** Any OpenJev choke must be **one shared component** called
  from both pipelines — never a second implementation.

#### F-4 · `medium` — Intent/severity not typed (despite “no keyword classify” rule)
- **Mechanism:** `process_message.py` correctly forbids regex intent — the LLM
  does understanding. But there is **no explicit typed severity/urgency score**
  surfaced to policy, triage, or UI.
- **Source layer:** 6, 9
- **Evidence:** `process_message.py:11` (docstring); absence of Score primitive
- **Recommended fix:** OpenJev `Score` for frustration/urgency/severity attached
  to turn metadata (§7.4).

#### F-5 · `medium` — Repair/retry surface is broad
- **Mechanism:** LiteLLM helpers retry transient errors; JSON cleaning /
  Gemini-compat mutations exist (`llm_compatibility.py`). These are legitimate
  but invisible to the operator.
- **Source layer:** 11
- **Evidence:** `admin/llm/services/litellm_helpers.py` `_is_transient_litellm_error`;
  `services/common/llm_compatibility.py` `should_apply_json_cleaning`
- **Recommended fix:** Not JEV-owned. Log repair events to outbox; JEV must not
  add a silent second LLM pass (T-5 / VIBE).

#### F-6 · `low` — Off-seam SomaBrainClient call sites still exist
- **Mechanism:** AGENT.md §7.3 notes residual `SomaBrainClient` callers outside
  `MemoryGateway` (T-1 debt).
- **Evidence:** `admin/agents/services/somabrain_integration.py`, tool result publisher
- **Recommended fix:** JEV integration uses **only** `MemoryGateway` (JEV-R-010).
  Do not add another memory client.

### 5.3 Quick diagnostic answers

| # | Question | Answer |
|---|---|---|
| 1 | Can the model skip a required tool and still answer? | **Yes** — tool_calls are model-initiated; choke can approve but cannot force use |
| 2 | Does old conversation content appear in new turns? | Bounded by V3 history; dual pipeline risk (F-3) |
| 3 | Same info in system prompt AND memory AND history? | Possible in Phase 5 5-lane context — keep JEV state compact |
| 4 | Platform runs a second LLM pass before delivery? | Not as hidden repair agent; retries exist (F-5) |
| 5 | Output differs internal vs delivered? | WS streaming only; acceptable |
| 6 | “Must use tool X” only in prompt? | Yes for soft rules; OPA choke is code for allow/deny |
| 7 | Can agent monologue become persistent memory? | Phase 11 stores turns — **JEV shall not write monologue as fact** |

### 5.4 What already helps JEV land

| Asset | Why it matters |
|---|---|
| `policy/confidence.rego` | **Already models confidence thresholds** (0.3 critical, `min_acceptance`, `should_flag`). JEV answers can feed `input.confidence` — no new policy language |
| `policy/tool_policy.rego` | Fail-closed allow/deny choke — attach JEV as *additional* deny/flag input |
| `FeatureFlag` + `get_feature_flag` | JEV-R-005 feature gate without new mechanisms |
| `UnifiedGate` | JEV-R-009 authz path |
| Capsule modules (`module.yaml`) | Seam C shell pattern (`mod_email` is the template) |
| `schemas/delegation_task.json` + Kafka `a2a` | Seam D async contract already exists |
| Outbox / AuditLog | JEV-R-016 audit slots |
| V3 phase metrics `record_turn_phase` | JEV-R-017 RED metrics extension points |

---

## 6. Seam binding (decision)

Per `SOMA-JEV-INTG-001` §5, with OpenJev truth applied:

| Seam | Binding | Rationale |
|---|---|---|
| **A — LLM slot** | **EXCLUDED** (permanent) | OpenJev is not a chat model |
| **B — Tool / capability** | **ADOPTED — primary invocation** | `jev_decide` tool + middleware calls |
| **C — Capsule Module** | **ADOPTED — shell** | `admin/modules/mod_jev/` config, flag, settings UI, lifecycle |
| **D — Delegation worker** | **ADOPTED — async only** | Batch scoring, eval, calibration jobs — not chat-critical path |
| **E — Memory** | **ALWAYS** | JEV reads SomaBrain via `MemoryGateway` only (T-1); JEV never owns a store |

**Expected combination (unchanged from RFP, now justified):**
**C shell · B in-turn invocation · D async · E memory.**

### 6.1 Transport posture (open question #1 from RFP — recommended answer)

Until OpenJev Phase 1 `openjev serve` ships:

| Option | Verdict |
|---|---|
| Gate all lanes on upstream HTTP | Rejected — blocks seams B/C/D testing |
| **Build a thin local shim in the integration layer** | **Recommended** — `POST /v1/systemone` over the library; pin OpenJev commit; swap to `openjev serve` when it lands |
| Call the Python library in-process from SA01 | Allowed **only** inside `mod_jev` / shim process — **not** as a hidden import in the orchestrator (keeps fail-closed and testability) |

The shim is a **wrapping concern of the integration layer**, not SA01 core and
not OpenJev upstream (RFP §6.1 already states this).

---

## 7. Typed decision inventory (the interesting part for our agent)

These are the SA01 decisions that become **OpenJev-native**. Anything not
listed stays on its current mechanism.

### 7.1 Decision catalogue

| ID | Decision | Primitive | Where in SA01 | Replaces / augments | Priority |
|---|---|---|---|---|---|
| **D-1** | Tool-call guardrail: “is this tool call safe to run?” | **Noul** | Before `execution_engine` / choke (`admin/core/tool_calling.py`, tool executor) | Boolean deny-list only | **P0** |
| **D-2** | Tool approval for unlisted / tier-3 tools | **Noul** (+ Score) | Approval path (unlisted→approval, packages_ensure, os_packages) | Human-only yes/no without probability | **P0** |
| **D-3** | Tool routing / priority when N tools offered | **Choice** | Phase 7 after tool discovery | Chat model free choice among 20+ tools | **P1** |
| **D-4** | Model router tie-break | **Choice** | Phase 6 `select_model` when `|candidates|>1` | Rule-only | **P1** |
| **D-5** | Urgency / severity / frustration of user turn | **Score** | Turn metadata after user message (pre-LLM) | None today | **P1** |
| **D-6** | Escalation to human | **Noul** | After tool result / error / low confidence | Implicit | **P1** |
| **D-7** | Memory admission: “persist this as long-term fact?” | **Noul** | Phase 11 memory storage (optional) | Store-everything | **P2** |
| **D-8** | Intent route (chat vs research vs workflow) | **Choice** | Use-case pipeline entry | LLM-only (documented “no regex”) | **P2** |
| **D-9** | Degraded-mode tool subset | **Choice**/rules | `select_tools_for_mode` | Pure rules (keep rules as floor) | **P3** |

**Non-goals:** chat completion, code generation, free-text extraction,
embedding, vector search. If a value must be extracted from free text, generate
candidates elsewhere and let JEV **pick**.

### 7.2 D-3/D-4 — Choice router (in-turn)

```
Phase 7 tools_for_llm = {t1…tN}
        │
        ▼
  if N > threshold and feature_flag('jev_router'):
        state  = compact(turn summary, user goal, risk flags)
        q      = Choice("Which tool should own the next action?", options=tool_names)
        → probabilities over tool_names · confidence
        offer tools sorted by p (cap at K) or force single tool
        │
        ▼
  Phase 8–9 LLM tool-calling (unchanged, still native)
```

- Fail-closed: if JEV errors or flag off → **current behaviour** (rules + model).
- Never let JEV invent a tool name — closed-world label set = `tools_for_llm`.

### 7.3 D-1/D-2 — Guardrail + approval choke (the highest value)

```
tool_call requested (name, args)
        │
        ▼
  UnifiedGate / OPA tool_policy.rego  ── deny → stop (unchanged)
        │ allow
        ▼
  OPENJEV CHOKE (feature_flag jev_guardrail)
    state = {tool, args_digest, tenant, risk_class, recent_failures}
    Noul("Would a careful operator run this tool now?")
    Score("How risky is this execution?", 0:safe … 3:critical)
        │
        ▼
  confidence.rego input.p_safe = noul  # SUPERSEDED: noul is P(true)/P(safe), NOT confidence — see ARCH-002 §5 · input.risk = score
        │
        ├─ deny / require_approval / allow
        ▼
  outbox audit (actor, tenant, action, resource, trace_id, outcome, jev_meta)
```

**Why this is the best integration for “the best agent”:**
1. It uses **existing** OPA confidence machinery — no new policy engine.
2. It is **code-gated** (tool cannot run without the choke) — fixes F-1.
3. It gives the human UI a **probability bar** (OpenJev render pattern) instead
   of an opaque allow.
4. It is ~100–300 ms and only on tool boundary — not on every token.

### 7.4 D-5 — Turn Score (triage)

After the user message, before Phase 5:

```
Score(instructions="How urgent is this request for the user?",
      legend={0: "informational", 1: "soon", 2: "urgent", 3: "emergency"})
```

Store on turn metadata (`ExecutionRecord` / session event). Consume in:
- UI badge / queue priority
- D-6 escalation threshold
- Governor budgets (urgent turns may relax cost tier — policy, not hardcode)

### 7.5 D-6 — Escalation Noul

After tool failure, guardrail score ≥ 2, or confidence < 0.3:

```
Noul("Does this situation require a human operator?")
```

→ `should_flag` in `confidence.rego` already supports the “flag without deny”
path. Wire JEV confidence into it.

---

## 8. Target architecture

```
                         ┌──────────────────────────────┐
                         │  User / WS / REST / bridges  │
                         └───────────────┬──────────────┘
                                         ▼
                         ┌──────────────────────────────┐
                         │   V3 ChatOrchestrator (12)   │
                         │   + conversation-worker      │
                         │   (shared decision client)   │
                         └───────────────┬──────────────┘
                 D-5 Score               │         D-8 Choice (opt)
            ┌────────────────────────────┼────────────────────────────┐
            ▼                            ▼                            ▼
   ┌─────────────────┐        ┌────────────────────┐       ┌─────────────────┐
   │ System One      │        │ Phase 6 model      │       │ Phase 7 tools   │
   │ decision client │        │ select_model +     │       │ discover +      │
   │ (JEV adapter)   │        │ D-4 Choice tie-break│      │ D-3 Choice sort │
   └────────┬────────┘        └─────────┬──────────┘       └────────┬────────┘
            │                           │                           │
            │              Phase 8–9 LLM + native tool_calls        │
            │                           │                           ▼
            │                           │                ┌────────────────────┐
            │                           │                │ D-1/D-2 choke      │
            │                           │                │ Noul + Score →     │
            │                           │                │ confidence.rego    │
            │                           │                └─────────┬──────────┘
            │                           ▼                          ▼
            │                  ┌─────────────────┐        ┌─────────────────┐
            │                  │ tool_executor   │        │ outbox / audit  │
            │                  │ PathGuard/Temporal│      │ + RED metrics   │
            │                  └─────────────────┘        └─────────────────┘
            ▼
   ┌────────────────────────────────────────────────────────────────────┐
   │ mod_jev (Capsule Module shell)                                     │
   │  module.yaml · feature flags · Vault creds · settings sections     │
   │  Ninja routes: /api/v2/modules/mod_jev/*                           │
   └───────────────────────────────┬────────────────────────────────────┘
                                   │ HTTP POST /v1/systemone
                                   ▼
   ┌────────────────────────────────────────────────────────────────────┐
   │ openjev-shim (integration-owned process/container)                 │
   │  thin FastAPI/uvicorn wrapper → openjev library (pinned tag)       │
   │  backend: hf (Qwen2.5-0.5B-Instruct) · mock in CI only if allowed │
   │  metrics: jev_latency_ms, jev_confidence, jev_denied               │
   └───────────────────────────────┬────────────────────────────────────┘
                                   │ optional async
                                   ▼
   ┌────────────────────────────────────────────────────────────────────┐
   │ Seam D: delegation task → Kafka a2a → jev worker → callback HMAC   │
   └────────────────────────────────────────────────────────────────────┘
                                   │ memory (bounded)
                                   ▼
   MemoryGateway → SomaBrainAdapter → SomaBrain → SFM   (T-1, never direct)
```

### 8.1 `mod_jev` module contract (Seam C)

Following `admin/modules/mod_email/module.yaml` pattern:

```yaml
name: mod_jev
title: System One decisions (OpenJev)
description: Typed Choice/Score/Noul decision layer — guardrail, router, triage
version: 0.1.0
settings_sections: [agent, external]
permissions: [network, vault:read]
always_enabled: false
feature_flag: jev_decide
```

Settings (via existing config chain only — **no hardcoded URLs/keys**):

| Setting | Purpose |
|---|---|
| `JEV_SHIM_URL` | Service URL (env topology → InfrastructureConfig) |
| `JEV_BACKEND` | `hf` \| `mock` (mock only where VIBE allows) |
| `JEV_MODEL_ID` | e.g. `Qwen/Qwen2.5-0.5B-Instruct` |
| `JEV_TIMEOUT_MS` | Default **10000** REST (JEV-R-003) — declared setting, not call-site default |
| `JEV_GUARDRAIL_ENABLED` | D-1/D-2 master switch (fail-closed when unset) |
| `JEV_ROUTER_ENABLED` | D-3/D-4 |
| `JEV_TRIAGE_ENABLED` | D-5/D-6 |
| Feature flags | `jev_decide`, `jev_guardrail`, `jev_router`, `jev_triage` |

Secrets: Vault only — `secret/agent/credentials/openjev_token` (open Q-3 in RFP).

### 8.2 `jev_decide` tool (Seam B)

One tool, three typed modes (never free-text answers):

| Mode | Args (shape) | Returns |
|---|---|---|
| `choice` | `question`, `options[]` (or `criteria{}`), `state` | `choice`, `probabilities`, `confidence` |
| `score` | `question`, `legend{}`, `state` | `score`, `probabilities`, `confidence` |
| `noul` | `question`, `state` | `noul` (P(true)) |

- Registered in `services/tool_executor` catalog (`TOOLS-001` style), tier-1 **auto**
  for pure scoring of non-sensitive state; **approval** when state contains secrets.
- OPA: `tool_policy.rego` entry `jev_decide` (default kit / tenant flag).
- **Closed world:** options are the only valid answers; validation rejects empty `<2` options.

### 8.3 Shared decision client (anti-F-3)

**One** client used by V3 **and** conversation-worker:

- `services/common/decisions/` (integration-owned module; name fixed in plan)
- API: `decide(request: SystemOneRequest) -> SystemOneResponse`
- Timeouts, retries (none for guardrail — fail-closed), audit, metrics
- Circuit breaker pattern already in repo (`circuit_breaker.py`) reused

---

## 9. Contracts (normative sketch)

Full requirement text remains `JEV-R-*` in `SOMA-JEV-INTG-001`. Architecture
adds these binding shapes.

### 9.1 Invocation

```json
{
  "state": {"tool": "packages_ensure", "risk_class": "tier3", "tenant": "<uuid>"},
  "questions": {
    "safe": {"type": "noul", "instructions": "Would a careful operator run this now?"},
    "risk": {"type": "score", "instructions": "Execution risk?",
             "legend": {"0": "safe", "1": "caution", "2": "risky", "3": "critical"}}
  },
  "model": "openjev-latest"
}
```

Response (OpenJev shape, unchanged):

```json
{
  "model": "openjev-hf/Qwen2.5-0.5B-Instruct",
  "answers": {
    "safe": {"type": "noul", "noul": 0.12},
    "risk": {"type": "score", "score": 2.4,
             "legend": {"0": "safe", "1": "caution", "2": "risky", "3": "critical"},
             "probabilities": {"0": 0.05, "1": 0.15, "2": 0.45, "3": 0.35},
             "confidence": 0.41}
  },
  "usage": {"input_tokens": 312, "output_tokens": 8},
  "latency_ms": 187.5
}
```

- Every call carries `tenant_id` (JEV-R-002).
- Timeout 10 s REST / 5 s memory (JEV-R-003).
- Error envelope matches SA01 Ninja/ApiError conventions (no new envelope).

### 9.2 Authorization & secrets

| Direction | Auth | Fail |
|---|---|---|
| SA01 → shim | Vault token / mTLS per SA01 service pattern | 401/403, no default tenant |
| shim → SA01 (none expected on hot path) | — | — |
| JEV worker → callback | HMAC like `POST /v1/delegation/task/{id}/callback` | 401/403 |
| Policy for JEV actions | `UnifiedGate` | deny + audit if RBAC stubbed (JEV-R-009) |

### 9.3 Memory — ALL DATA THROUGH THE BRAIN (binding product law)

**Operator law (2026-10-09):** *All data is saved and passed through the brain.*
There is no private agent memory, no JEV-local store, no side channel.

| Data class | Path (only) | Rule |
|---|---|---|
| User turns / agent replies | V3 Phase 11 → `MemoryGateway` → SomaBrain → SFM | T-1 |
| JEV `state` (read) | Built by caller via `MemoryGateway.recall` **before** decide | JEV never recalls directly |
| JEV decision record (choice/score/noul + probs + confidence + latency) | Outbox audit **and** mandatory `MemoryGateway.remember` of the **decision fact** (not raw CoT) | Persisted only through the brain lane |
| Tool outcomes / escalations | Existing outbox + memory path | No JEV shadow log as truth |
| Calibration / eval datasets | Seam D artifacts + brain-stored summaries | No second vector store |

- JEV **shall not** hold an SFM client (T-1).
- The shim **shall not** call SomaBrain itself (one dialect: `SomaBrainAdapter`).
- JEV-R-011: bounded `top_k`/`offset`; failure ⇒ structured error, not `[]`.
- **If a JEV value must survive the process, it goes through the brain — or it does not count as saved.**

### 9.4 Observability

| Signal | Labels |
|---|---|
| `jev_decide_total` | mode, decision_id, outcome |
| `jev_decide_latency_ms` | mode |
| `jev_confidence` | decision_id |
| `jev_guardrail_denied_total` | tool, reason |
| Trace | `trace_context` end-to-end (JEV-R-014) |
| Outbox audit | every mutating decision (JEV-R-016) |

Phase metrics: extend `record_turn_phase` with `JEV_DECIDE` — do not fork the metrics path.

---

## 10. Verification sketch (requirement → method)

| Group | Method |
|---|---|
| JEV-R-001…006 | Live-stack tests: tool choke E2E; config round-trip; flag off ⇒ 403 |
| JEV-R-007…009 | Credential matrix + secret scan |
| JEV-R-010…011 | Triad tests: memory only via MemoryGateway |
| JEV-R-012…015 | Delegation negative tests + DLQ replay |
| JEV-R-016…017 | Audit event per call; metrics scrape |
| JEV-R-018…019 | `scripts/check_docs.py` PASS; no code before Approved |
| Decision quality | Golden sets: known unsafe tool calls must yield Noul &lt; 0.3; known safe &gt; 0.7 (calibration later) |
| Latency budget | p95 &lt; 350 ms HF on CPU shim; guardrail never async-loses the call |
| VIBE / T-8 | No mocks in acceptance paths; mock backend only for unit tests of the **adapter**, not for acceptance |

---

## 11. Risk register

| ID | Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|---|
| R-1 | OpenJev Phase 0 API drift | High | Med | Pin tag; adapter absorbs; contract tests |
| R-2 | Shim latency hurts chat p95 | Med | Med | Only on tool/decision boundaries; budget JEV_TIMEOUT; cache none for guardrail |
| R-3 | Double pipeline divergence (F-3) | High | Med | Single shared client |
| R-4 | JEV confidence is entropy, not calibrated | Med | High | Phase 2 temperature calibration; until then treat as signal + human approval for tier-3 |
| R-5 | Prompt-only usage creep | High | Med | Code-gate choke; tests that fail if flag on but call missing |
| R-6 | Memory contamination via state blobs | Med | Low | Compact state; no monologue persistence (D-7 gated) |
| R-7 | Feature flag misconfig opens bypass | High | Low | Fail-closed default; `jev_guardrail` unset ⇒ deny tier-3 |

---

## 12. Constraints inherited (binding)

- T-1 memory only via SomaBrain · T-5 fail-closed · T-8/VIBE no mocks in acceptance
- Secrets Vault only · Lit 3.x only · Django Ninja only · PostgreSQL 16 only
- No React/Alpine/FastAPI/SQLAlchemy/Qdrant in SA01 (OpenJev shim may use FastAPI
  **as its own process** — it is not an SA01 app)

---

## 13. Open questions (aligned with RFP §11 + new)

| # | Question | Recommendation |
|---|---|---|
| Q-1 | Shim now or wait for `openjev serve` | **Shim now** (integration-owned), swap later |
| Q-2 | Single-tenant pilot vs Soma Platform day one | **Single-tenant pilot** first; `tenant_id` still mandatory |
| Q-3 | Vault path | `secret/agent/credentials/openjev_token` |
| Q-4 | Latency budget | Guardrail p95 &lt; 350 ms CPU; triage may be 500 ms async-ish |
| Q-5 | Pin strategy | Pin OpenJev git tag; quarterly contract review |
| Q-6 | Should D-5 Score run for every turn? | Flag-controlled; default on for tools-reaching turns only |
| Q-7 | Human override of JEV deny | Always allow operator override with audit (never silent) |

---

## 14. Why these seams make “the best agent”

| Without OpenJev | With OpenJev layer |
|---|---|
| Tool danger = regex + deny-list | P(safe) + risk score into **existing** OPA confidence |
| 20 tools offered, model free-picks | Ranked tool set with probabilities |
| Severity invisible to policy/UI | Typed Score on the turn |
| Escalation is an if-chain | Calibrated Noul + `should_flag` |
| “Confidence” Rego unused | First real producer of `input.confidence` |
| Approvals opaque | Probability bars in the admin UI (reuse OpenJev render) |

The agent stays T-1-clean, fail-closed, and single-pipeline. OpenJev only makes
the **micro-decisions** honest, typed, and measurable.

---

## 15. Related documents

| Doc | Role |
|---|---|
| `SOMA-JEV-INTG-001` | RFP / requirements `JEV-R-*` |
| `SOMA-PM-PLAN-JEV-INTEGRATION-001` | Waves, ownership, exit criteria |
| `SOMA-ARCH-TOOLS-001` | Tool framework the choke plugs into |
| `SOMA-ARCH-INVARIANTS-001` | T-1…T-8 |
| OpenJev `docs/DESIGN.md` | Upstream phases |

*End of document — SOMA-ARCH-JEV-001 v1.0.0*
