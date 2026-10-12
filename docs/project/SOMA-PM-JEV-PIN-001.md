> **SUPERSEDED / RETIRED 2026-10-09.** OpenJev integration **removed** by operator order.
> Replacement: Cloudflare **Clef / Clef-flash** (Jev-API compatible). Do not implement from this document.

# SOMA-PM-JEV-PIN-001 — OpenJev pin, contract freeze, G-0 release record

## Document Control

| Field | Value |
|---|---|
| Document Title | OpenJev pin, contract freeze, G-0 release record |
| Document Identifier | SOMA-PM-JEV-PIN-001 |
| Version | 1.1.0 |
| Date | 2026-10-09 |
| Status | Obsolete |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2027-01-09 |
| Related | `SOMA-ARCH-CLEF-001` (replacement), `SOMA-ARCH-JEV-002` (obsolete), `SOMA-PM-PLAN-JEV-INTEGRATION-001` (obsolete) |
| Source of truth | Historical — superseded by `SOMA-ARCH-CLEF-001` |
| Audience | Historical reference only |
| Scope | H.0 freeze record for OpenJev. **OBSOLETE — OpenJev removed; use SOMA-ARCH-CLEF-001.** |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-09 | SomaTech Engineering | Initial issue. Operator released G-0 for H.0 + W-J1 + W-J2. Pin SHA recorded. Contracts frozen per ARCH-002 §5–§6. |
| 1.1.0 | 2026-10-09 | triad-iso-docs | Retired. OpenJev removed by operator order. Status Draft → Obsolete. Superseded by `SOMA-ARCH-CLEF-001`. Historical record only. |

---

## 0.1 ABSOLUTE LAW — REAL CODE ONLY

**NO SHIMS. NO FAKES. NO MOCKS. NO STUBS. NO PLACEHOLDERS. NO TODO PASSES.**
Rule 4 handoff / VIBE / T-8. OpenJev = real library or real `openjev serve` only.

---

## 1. G-0 release

| Gate | Status | Evidence |
|---|---|---|
| Operator GO | **RELEASED 2026-10-09** | Verbal GO in session: “GO and document everything… develop the best agent” |
| ARCH-002 reviewed | Draft accepted in-session (architect 7.5/10 + evaluator 4.0/5) | Dual actor reviews |
| Confidence contract corrected | **YES** — §3 | ARCH-002 §5 |
| Scope cut | First ship **H.0 + W-J1 + W-J2 only** | Evaluator condition |
| Full code after W-J2 evidence | **HOLD** for D-3/D-4/D-5 expansion | Plan W-J3 deferred |

**Authorized work now:** H.0 · W-J1 · W-J2 (pin, client, real OpenJev dependency, mod_jev, brain write, guardrail choke, golden sets, evidence).

---

## 2. OpenJev pin (G-0b)

| Field | Value |
|---|---|
| Upstream | `https://github.com/GPT-AGI/OpenJev.git` |
| Local working tree | `~/dev/OpenJev` (dev machine; CI must clone the pin) |
| **Pinned commit SHA** | **`0e7bb990211df139da13dc67aa2a7aceca311af7`** |
| Commit subject | `social: fix v3 headline overflow` |
| Branch at pin | `main` |
| Version | `0.1.0` Phase 0 alpha |
| License | MIT |
| Verified | Platform suite 59/59 (mock backend) 2026-10-09; CLI `--file` quickstart OK |

**Rule:** integration uses this SHA as a **real** dependency (no wrapper/shim). Upstream drift is absorbed by the integration layer; contract tests fail the build on schema break (R-1).

**Upgrade procedure:** new SHA → run `tests/contract/test_openjev_contract.py` against the real dependency → update this pin table → redeploy the real service/process.

---

## 3. Frozen contracts

### 3.1 Signal split (C-1 — binding)

| OpenJev field | Meaning | OPA / choke input |
|---|---|---|
| `NoulAnswer.noul` | P(true) e.g. P(safe) | `input.p_safe` |
| `ScoreAnswer.score` | risk expectation | `input.risk` |
| `ChoiceAnswer.confidence` | 1 − H_norm | `input.confidence` |
| `ScoreAnswer.confidence` | 1 − H_norm | `input.confidence` |

**Forbidden:** `input.confidence = noul`.

### 3.2 SystemOneRequest / Response

Identical to OpenJev `SystemOneRequest` / `SystemOneResponse` JSON (Jev-compatible). No wrapper fields inside `state` that leak secrets — use `args_digest`, `risk_class`, `tenant` only.

### 3.3 Decision-fact (brain write — mandatory)

```
decision_id, tenant_id, trace_id, mode(choice|score|noul), question_id,
payload{choice|score|noul, probabilities, confidence},
input_state_digest, caller(v3|conversation_worker|temporal|tool),
model_id, latency_ms, outcome(allow|require_approval|deny|advisory),
opa_decision_ref, created_at
```

Namespace: `jev.decisions.{guardrail|router|triage|escalation}`  
Path: shared client → outbox envelope → `MemoryGateway.remember` → SomaBrain.

### 3.4 First-ship thresholds

| Condition | Effect |
|---|---|
| `p_safe` null (JEV down) + tier-3 | deny / require_approval |
| `p_safe` &lt; 0.30 | deny tier-3 · require_approval tier-2 |
| `p_safe` 0.30–0.70 | require_approval |
| `p_safe` &gt; 0.70 and `risk` ≤ 1 | allow tier-1/2 |
| `risk` ≥ 2 | require_approval |
| `confidence` &lt; 0.30 | should_flag |

Tier-3 keeps human approval until W-J4 calibration evidence.

---

## 4. Product law (repeat — binding)

ALL data is saved and passed through THE BRAIN.

```
agent → MemoryGateway → SomaBrain → SomaFractalMemory
```

No JEV store. No side channel. If it is not in the brain, it did not happen.

---

## 5. Profile / skill corrections (this release)

| File | Change |
|---|---|
| `.mimocode/agent/soma-jev-engineer.md` | **NEW** — JEV integration owner |
| `soma-wiring-engineer.md` | JEV decision-fact lane via MemoryGateway only |
| `soma-cognitive-engineer.md` | OPA `p_safe`/`risk`/`confidence` contract |
| `soma-temporal-ops.md` | Seam D reuses existing queues |
| `soma-ui-engineer.md` | JEV probability UI honesty rules |
| `soma-adversarial-skeptic.md` | JEV attack list (noul≠confidence, optional brain write, mock leak) |
| `CLAUDE.md` | Agent table + `soma-jev-engineer` |

---

## 6. Exit checklist for H.0

- [x] Pin SHA recorded
- [x] Contracts frozen (ARCH-002 + this doc)
- [x] G-0 released for W-J1/W-J2
- [x] A2A claims on implementation paths
- [x] Profiles corrected
- [ ] `check_docs.py` PASS after register regen
- [ ] W-J1 start

*End of document — SOMA-PM-JEV-PIN-001 v1.0.0*
