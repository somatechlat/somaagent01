# PLAN — Chat Cognition, Capsule-Owned Tools, and Honest UI

## Document Control

| Field | Value |
|---|---|
| Document Title | PLAN — Chat Cognition, Capsule-Owned Tools, and Honest UI |
| Document Identifier | SOMA-PM-PLAN-CHAT-COGNITION-001 |
| Version | 1.0.0 |
| Date | 2026-10-04 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-28 |
| Related | SOMA-STD-CODING-001 (law) · SOMA-STD-CONFIG-001 (config) · SOMA-ARCH-INVARIANTS-001 (T-1…T-8) · SOMA-TRIAD-ARCH-001 · SOMA-SETTINGS-MODEL-001 · SOMA-01-UIUX-001…005 · SOMA-SRS-TOOLS-001 · SOMA-SRS-CHATFLOW-001 |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-04 | SomaTech Engineering | Initial issue. Built from a full read of the chat, tool, memory, RBAC and UI code plus the Agent Zero benchmark. Every finding cites `file:line`. |

---

## 1. Purpose and standing order

Make the agent chat **use the full cognition of the triad**: every SomaBrain capability, the SFM store, and the agent's own IQ — with tools that are **capsule-owned and auto-discovered**, and a UI that tells the truth.

Design criteria applied to every decision below:

> **the rules · millions of transactions · security · speed · latency · thin**
>
> A per-request external hop is a latency wall. Anything hot must be cached and bounded. A knob with no reader is a lie. A control with no handler is a lie. A route that is called and does not exist is a lie.

**Authority:** `docs/standards/SOMA-STD-CODING-001.md`. No stubs, no mocks, no shims, no TODOs, no hardcoded values, fail-closed, documentation = truth.

---

## 2. Measured state (2026-10-04)

Every claim below was read from source. Where docs disagree with code, **code wins**.

### 2.1 What already works
- Chat reply is real: `POST /chat/conversations/{id}/messages` → `{"content":"STREAM-OK","model":"groq/openai/gpt-oss-120b","tokens_used":53}`
- T-1 lane is correct: `ChatOrchestrator → MemoryGateway → SomaBrainAdapter → POST /memory/* → SomaBrain → POST /memories → SFM`
- Native function calling reaches `acompletion` (`litellm_client.py:344-350`); tool results re-enter as proper `ToolMessage`s
- Fail-closed at the credential boundary; Vault-only secrets

### 2.2 The 30 measured defects this plan closes

| # | Defect | Evidence |
|---|---|---|
| **D1** | `memory_recall`'s description **commands** the model to call it before answering | `default_tools.py:52` |
| **D2** | Memory is in the prompt AND the tool is still offered every round | `chat_orchestrator.py:1200-1203` + `:303` |
| **D3** | `tool_choice` is never sent — the model may call tools forever | grep: only read for Groq at `litellm_helpers.py:308` |
| **D4** | Truncation invites re-query (2000 chars/hit × 8 > 12000-char message cap) | `memory_tools.py:45,59` + `tool_calling.py:179-182` |
| **D5** | Empty query → wildcard dump `"*"` | `memory_tools.py:86-87,252` |
| **D6** | `memory_get` miss steers back into the loop | `memory_tools.py:320` |
| **D7** | No terminal "answer now" round — the stop string becomes the answer | `tool_calling.py:477` |
| **D8** | Approval path: approved tools **never execute**; `error` unbound on approve | `tool_calling.py:397-417` |
| **D9** | History lane budgeted then **ignored** for the real prompt | `builder.py:129` vs `chat_orchestrator.py:1212` |
| **D10** | `stream_turn` hardcodes `confidence=0.5`; missing egress filter + brain reorder | `chat_orchestrator.py:1104,956-987` |
| **D11** | Tools are **global**, not capsule-owned | `tools.py:342-351`, `tool_registry.py:69-76` |
| **D12** | `Capability.implementation` is exported/imported and **never loaded** | `core.py:465-475` |
| **D13** | `Capability.name` globally unique — capsules cannot own distinct tools | `core.py:449` |
| **D14** | Phase 7 unconditionally injects the full default kit | `chat_orchestrator.py:590` |
| **D15** | No per-tool `resource:tool_execute` check on the chat path | `execute_tool_call` |
| **D16** | SRS 4-phase discovery gate (REQ-TS-001…011) not implemented | `SOMA-SRS-TOOLS-001.md` |
| **D17** | gRPC: 7 RPCs implemented, **server never started** | `transport/serve.py:461` |
| **D18** | WM→LTM promotion **never attached** | `memory/wm/core.py:502` |
| **D19** | NREM/REM consolidation **never scheduled** | `consolidation.py:90,135` |
| **D20** | **Three neuromod stores** — chat sync is a no-op on cognition | `neuromod.py:34-41` vs `bootstrap/singletons.py:278` |
| **D21** | Oak create/update always 500 (dict vs attribute) | `oak.py:72-77` |
| **D22** | `sleep/transition` calls a method that does not exist | `sleep.py:240` |
| **D23** | FSM has **no edge back to ACTIVE** | `sleep/__init__.py:118-123` |
| **D24** | Advanced recall (8 fields) implemented in `perform_recall` — **nothing imports it** | `api/memory/recall.py:170` |
| **D25** | **Constitution routes have no auth** | `api/endpoints/constitution.py` |
| **D26** | OPA update is **fail-open** (warns and reports success) | `opa.py:55-68` |
| **D27** | **Superset defect** — `sysadmin` cannot chat; `member` cannot configure | `authz.py:303-318` vs `:377` |
| **D28** | Two live role stores + two decoys | `identity.py:83` vs `tenants.py:104`; `profiles.py:88` |
| **D29** | Model↔key: a model **cannot own a key**; three parallel UI lists | `admin/llm/models.py`, `saas-settings-models.ts:665-813` |
| **D30** | Role/permission UI calls a **deleted** `/permissions` API | `admin/api.py:325` vs `saas-role-matrix.ts:352` |

---

## 3. The plan

### PART A — Make the chat answer properly *(blocks everything)*

**A1 · Tell the model to stop (D1, D2, D7)**
- Rewrite `memory_recall`'s description: it is for *when memory in the prompt is insufficient*, not "always before answering".
- Add a terminal round: after the tool loop reaches its cap (or when the model has enough), issue one final call with `tool_choice="none"` to produce the answer. The stop string must **never** be shown as the answer.
- **Decision:** a forced final round costs one LLM call at the end of a tool chain. Against the criteria: *latency* is bounded (one extra call only when tools were used), *thin* (no new subsystem), and it removes a visible lie. Accept.

**A2 · Memory tools return digests, not raw payloads (D4, D5, D6)**
- `memory_recall` returns a ranked digest: `[{rank, summary, coord, score}]` capped to a budget the model can read whole, plus `enough: bool`.
- Empty query is a **refusal**, not a wildcard dump.
- `memory_get` miss returns a terminal hint ("not found — answer from what you have"), not "search again".
- **Decision:** a digest keeps the tool message under the cap so truncation cannot trigger re-query. *Security*: no new exposure. *Thin*: one shaping function.

**A3 · Send `tool_choice` (D3)**
- Default `tool_choice="auto"`; set `"none"` on the terminal round.
- **Decision:** the model currently has no way to say "done". This is the minimal signal.

**A4 · Repair the approval round-trip (D8)**
- Approved tools execute; `error` is defined on both paths; denied tools produce a terminal tool message.
- **Decision:** a control that cannot work is a lie. Either it works or it is deleted. It works.

**A5 · Use the history lane (D9)** — feed the budgeted `context.history` into the prompt instead of the raw list.

**A6 · Make `stream_turn` match `process_turn` (D10)** — real `confidence` from the brain eval, egress filter, `suggested_tools` reorder.

**Tests:** a Playwright human-like turn that asks a recall question must produce an answer containing the fact, with **≤2 tool calls**, never a stop string.

---

### PART B — 100% of SomaBrain in the chat

| ID | Wire | Unlocks | Pre-req |
|---|---|---|---|
| B1 | Start the **gRPC/UDS service** (D17) | batch, `RecallBatch`, `StreamContext`, low-latency local bus | compose volume `soma_run:/run/soma` |
| B2 | `remember/batch` (D-none) | N writes in one round trip | — |
| B3 | Advanced recall fields (D24) | threshold/age/session-pinned/paged recall | mount `perform_recall` as the real handler |
| B4 | `plan/suggest` + `personality` | multi-step plans; trait modulation | fix `np.zeros(512)` → settings dim |
| B5 | **Unify the three neuromod stores** (D20) | chat's neuro sync actually changes cognition | one instance from `bootstrap.singletons` |
| B6 | Full sleep FSM (D22, D23) | light/freeze/util/policy; **add the edge back to ACTIVE** | implement `SleepStateManager.transition` |
| B7 | WM→LTM promotion (D18) + NREM/REM (D19) | real learning and consolidation | call `set_promoter`; schedule `run_nrem`/`run_rem` |
| B8 | Constitution + OPA (D25, D26) | policy-driven behaviour | **authenticate the routes first**; OPA update must fail closed |
| B9 | Oak (D21) + threads | learned behaviours; option sequences | fix dict/attribute; enable `ENABLE_OAK` |
| B10 | `context/feedback` + adaptation | the learning loop closes | — |

**Security first (B8):** constitution routes currently accept anyone. That is closed before any wiring.

**Docs:** every capability above enters `SOMA-TRIAD-ARCH-001` and `SOMA-BRAIN-COMPLIANCE-001`. Hype in `somabrain/README.md`, `FINAL_VERIFICATION_REPORT.md`, `VIOLATIONS.md` is corrected — those files claim *"production-ready"*, *"NO INVENTED APIs"*, *"VIBE 100%"* while inventing `/api/v1/memory/store`, `/recall` with `retrievers`, `/wm/status`.

---

### PART C — Capsule-owned, auto-discoverable tools (D11–D16)

**C1 · A capsule owns its tools.** Add an owner to `Capability` (capsule FK). `Capability.name` becomes unique **per capsule**, not globally.

**C2 · A loader for `Capability.implementation`.** `{type, module, class}` is already on the model and in export/import — load it. Until it loads, a capsule-created tool cannot run.

**C3 · Discovery filters by capsule AND permission.** Phase 7 starts from `capsule.capabilities` (enabled only), then applies `tool_policy`, then the authz/OPA/SpiceDB gate **at discovery** — so a tool the subject may not use is never advertised. This is SRS REQ-TS-001…006.

**C4 · Per-tool authorization at execution.** `execute_tool_call` calls `authorize(..., "resource:tool_execute", resource=tool_name)`.

**C5 · Delete the mandatory-kit lie.** `NON_DISABLEABLE_TOOLS` may stay as the *cognitive floor*, but a capsule must be able to declare "only these tools". If the floor is a product rule, say so in the SRS — not in a silent constant.

**C6 · MCP routing (REQ-TS-008).** `provider="mcp"` routes to an MCP client. The trace matrix cites `admin/core/helpers/mcp_clients.py` — **the file does not exist**.

**Docs:** `SOMA-SRS-TOOLS-001.md` REQ-TS-001…011 move from "not met" to met, or are restated as what the product actually does.

---

### PART D — One role catalog + a permissions UI (D27, D28, D30)

**D1 · `sysadmin` becomes a superset.** Union of every role, minus nothing. Same for `org_admin` at the org level. The hierarchy `ROLE_PRIORITY` implies must actually grant.

**D2 · One role store.** `LocalIdentity.roles` is the authority for Standalone; `TenantUser` becomes the tenant-membership record that *delegates* to it — or one is deleted. Two answers for one subject is the defect.

**D3 · `TenantRole` gains `agent_owner` / `agent_operator`** or the vocabulary is declared identical to `ROLE_PERMISSIONS` and enforced at import.

**D4 · Delete the decoy.** `PlatformConfig.defaults["roles"]` and `PATCH /aaas/settings/roles/{id}` write a map the gate never reads. Delete them, or make them the real store.

**D5 · A real permissions UI.** The screens call a deleted `/permissions` API. Either restore a real catalog API that writes the authority, or make the screens read-only views of `admin.core.authz` with system roles locked and a **real** reason string (`org:assign_roles` — not the invented `role:manage`).

**D6 · Kill invented permissions.** `role:manage`, `permission:manage`, `channel:manage` appear in `SOMA-01-UIUX-001.md` and exist nowhere in the catalog. Replace with real verbs or remove.

**Docs:** `SOMA-01-UIUX-001` UI-S-23/24/52, `SOMA-SETTINGS-MODEL-001`, and `admin/core/authz.py:69` ("six families" — there are seven).

---

### PART E — Honest UI/UX (D29) · benchmark: Agent Zero

**E1 · One model owns one key.** This is the user's core complaint and the code confirms it: `LLMModelConfig` has no key field; keys are per-provider; three parallel lists.

> **Design decision:** a key belongs to a **provider**; a model *uses* a provider. Making keys per-model would duplicate the same secret N times in Vault — *security* and *thin* both say no. So the fix is **relational, not structural**: the model row must show which provider key it uses and whether that key is stored, and the provider row must list the models that depend on it. Both directions visible; one secret.

**E2 · Delete duplicates.** Two settings screens (`saas-settings.ts`, `saas-settings-models.ts`), two right-rails, three permission screens. One of each.

**E3 · Delete every dummy.** Any control with no handler, any unbound input, any fabricated row. A control with no handler is a lie.

**E4 · AgentIQ is editable and visible** — intelligence / autonomy / resource / response-style, with their effects shown (temperature, model tier, tool gate).

**E5 · Lanes are visible** — the 5 context lanes, the tool timeline, memory recall, brain eval, neuromodulators.

**E6 · Settings is one surface** grouped by the `SOMA-SETTINGS-MODEL-001` taxonomy (L1–L4), each row showing its owner and its resolution source.

**Benchmark note:** Agent Zero has the *features* we need (11 settings categories, canvas, extensions, skills, MCP, secrets). Its *design* is often poor — take the feature list, not the layout. Where our docs already exceed Agent Zero (cognitive memory, capsules, IQ), keep our model.

**Docs:** `SOMA-01-UIUX-001`, `UIUX-005` (306 rows), `SOMA-UI-SPEC-001/002`, `SOMA-UI-PARITY-002`, `SOMA-UI-SKINS-001`. **Three of these specify three different designs for the model↔key screen** — one is chosen and the others are corrected.

---

## 4. Order and gates

| Order | Part | Gate (must be green before the next) |
|---|---|---|
| 1 | **A** — chat answers | Playwright: a recall question returns an answer, ≤2 tool calls, never a stop string |
| 2 | **D1–D3** — role catalog | `sysadmin` can chat **and** configure; one role store answers |
| 3 | **C** — capsule-owned tools | two capsules with different tool sets; discovery filters by permission |
| 4 | **B** — SomaBrain capacity | each wired capability has a test; security blockers closed first |
| 5 | **E** — UI/UX | every control has a handler; model↔key visible both ways; no duplicates |

**Rationale for the order:** chat is the product. Roles block it today. Tools are how the agent acts. SomaBrain is how it thinks. UI is how you drive it.

---

## 5. Document traceability

| Requirement source | This plan | Test that proves it |
|---|---|---|
| SOMA-STD-CODING-001 (no stubs, fail-closed, docs=truth) | all | CI grep guards + `check_docs.py` |
| SOMA-ARCH-INVARIANTS-001 T-1…T-8 | B, C, Part A | `tests/e2e/test_triad_integration.py` |
| SOMA-TRIAD-ARCH-001 §11 R-01…R-10 | B1–B10 | e2e + live proof |
| SOMA-SRS-TOOLS-001 REQ-TS-001…011 | C1–C6 | `test_tool_discovery_gate.py` |
| SOMA-SRS-CHATFLOW-001 REQ-011, REQ-020 | A1–A6 | `test_tool_loop_terminal_round.py` |
| SOMA-SRS-CAPSULEPORT-001 REQ-CP-012 | C1–C3 | `test_capsule_owns_tools.py` |
| SOMA-SETTINGS-MODEL-001 (306 rows, L1–L4) | D, E6 | `test_settings_resolution_chain.py` |
| SOMA-01-UIUX-001 UI-S-03, 23, 24, 50–53 | D5, E1–E6 | Playwright `test_human_chat_session.spec.js` |
| SOMA-01-UIUX-005 | E6 | settings-by-role Playwright |
| SOMA-UI-SPEC-001/002, SOMA-UI-PARITY-002 | E1–E5 | UI inventory + Playwright |
| SOMA-UI-SKINS-001 | E (out of scope for code) | — |
| SOMA-A0-PARITY-001 / RPT-FEATMATRIX-001 | E (feature benchmark) | gap table |
| Agent Zero `webui/` | E (feature benchmark) | gap table |

**Documents that must be corrected when this plan is executed** (they currently contradict the code):
`somabrain/README.md` · `somabrain/FINAL_VERIFICATION_REPORT.md` · `somabrain/VIOLATIONS.md` · `somabrain/docs/SOMABRAIN_ARCHITECTURE.md` · `docs/iso/SOMA-BRAIN-COMPLIANCE-001.md` · `docs/iso/SOMA-01-UIUX-001.md` (invented permissions) · `docs/requirements/SOMA-SRS-TOOLS-001.md` (unmet REQs) · `admin/core/authz.py:69` (six vs seven families)

---

## 6. OPEN questions for the owner

| ID | Question | Default if unresolved |
|---|---|---|
| OPEN-01 | Should the cognitive tool floor (`NON_DISABLEABLE_TOOLS`) remain mandatory, or may a capsule run without memory tools? | Keep mandatory; state it in the SRS |
| OPEN-02 | One role store: `LocalIdentity` or `TenantUser`? | `LocalIdentity` (Standalone authority); TenantUser delegates |
| OPEN-03 | Model↔key: relational display (recommended) or per-model secrets? | Relational |
| OPEN-04 | Terminal round always, or only when tools were called? | Only when tools were called |
| OPEN-05 | Is `auditor` meant to read agents? It has no `agent:read` today | Add `agent:read` |
| OPEN-06 | Settings screen grouping: by L1–L4 ownership, or by user task? | L1–L4 |

---

## 7. Definition of done

Against real services:
1. A recall question in the human-like Playwright run returns an **answer containing the fact**, with ≤2 tool calls and never a stop string.
2. Two capsules with different tool sets see different tools; a tool the subject may not use is never advertised.
3. `sysadmin` can chat **and** configure; one role store answers for one subject.
4. Every SomaBrain capability in Part B is wired or explicitly out of scope — no silent gap.
5. The model↔key relationship is visible in both directions; no duplicate screens; no control without a handler.
6. `check_docs.py` reports 0 non-compliant; every document named in §5 matches the code.

---
