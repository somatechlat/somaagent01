> **SUPERSEDED / RETIRED 2026-10-09.** OpenJev integration **removed** by operator order.
> Replacement: Cloudflare **Clef / Clef-flash** (Jev-API compatible). Do not implement from this document.

# SOMA-PM-PLAN-JEV-INTEGRATION-001 — OpenJev integration delivery plan

## Document Control

| Field | Value |
|---|---|
| Document Title | OpenJev integration delivery plan |
| Document Identifier | SOMA-PM-PLAN-JEV-INTEGRATION-001 |
| Version | 1.1.0 |
| Date | 2026-10-09 |
| Status | Obsolete |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2027-01-09 |
| Related | `SOMA-ARCH-CLEF-001` (replacement), `SOMA-ARCH-JEV-002` (obsolete), `SOMA-ARCH-TOOLS-001`, `SOMA-STD-CODING-001` |
| Source of truth | Historical — superseded by `SOMA-ARCH-CLEF-001` §H |
| Audience | Historical reference only |
| Scope | Waves, ownership, exit criteria for OpenJev (JEV) in SA01. **OBSOLETE — OpenJev removed; use SOMA-ARCH-CLEF-001.** |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-09 | SomaTech Engineering | Initial issue. Docs-only delivery plan. Waves W-J0…W-J4. Operator gate: **no code until explicitly released.** |
| 1.1.0 | 2026-10-09 | triad-iso-docs | Retired. OpenJev removed by operator order. Status Draft → Obsolete. Superseded by `SOMA-ARCH-CLEF-001`. Historical record only. |

---

## 0.1 ABSOLUTE LAW — REAL CODE ONLY

**NO SHIMS. NO FAKES. NO MOCKS. NO STUBS. NO PLACEHOLDERS. NO TODO PASSES.**
OpenJev = real pinned dependency or real `openjev serve` only.

---

## 0. Operator gate (binding)

| Gate | Condition | Status |
|---|---|---|
| **G-0** | Operator says “start code” | **RELEASED** — see PIN-001 |
| G-0a | `SOMA-ARCH-JEV-002` reviewed | Draft — pending review |
| G-0b | OpenJev commit/tag pinned in plan appendix | Pending W-J0 |
| G-0c | A2A claim on implementation paths | At implementation time |

**No production code, no scaffold, no “temporary” shim file before G-0.**
Test stubs that fake JEV answers are prohibited in acceptance paths (T-8/VIBE).

---

## 1. Objectives

1. Attach OpenJev as a **typed System One decision layer** (Choice / Score / Noul).
2. Highest value first: **tool guardrail + approval choke** (D-1/D-2) feeding
   the **existing** `policy/confidence.rego` surface.
3. Keep SA01 invariants: T-1 memory, T-5 fail-closed, single decision client,
   existing control planes only.
4. Leave a clean upgrade path to `openjev serve` when upstream Phase 1 ships.

---

## 2. Wave plan

### W-J0 · Spec lock & pin (docs + vendor inputs) — **0.5–1 day**

| Task | Output | Exit |
|---|---|---|
| Pin OpenJev git tag/commit | Appendix A record | Tag recorded |
| Confirm shim vs upstream HTTP | Decision record in ARCH §6.1 | Already recommended: **shim** |
| Vault path + flag names locked | ARCH §8.1 | Reviewed |
| Register docs in `docs/iso/DOCUMENT-REGISTER.md` | `gen_register.py` | `check_docs.py` PASS |
| A2A: claim `admin/modules/mod_jev/`, `services/common/decisions/`, `services/tool_executor/` choke points | `docs/plans/a2a/CLAIMS.md` | Claimed |

**Owner:** architect + `triad-iso-docs`

### W-J1 · Mod shell + shared client + shim (foundation) — **2–3 days**

| Task | Seam | Notes |
|---|---|---|
| `admin/modules/mod_jev/module.yaml` + registry hooks | C | Follow `mod_email` |
| Settings: `JEV_*` via settings chain only | C | No call-site defaults |
| Feature flags `jev_decide` etc. | C | Fail-closed when unset |
| `services/common/decisions/client.py` — one `decide()` | B | Timeout, audit, metrics, circuit |
| Real OpenJev integration: pinned library `openjev` decide() / real `openjev serve` (NO shim/wrapper) | B | Thin; OpenJev library pinned |
| Vault credential read path | — | `secret/agent/credentials/openjev_token` |
| Unit tests: client envelope, timeout, flag-off deny | — | No live model required for envelope tests |
| Contract test: request/response JSON vs OpenJev | — | Golden files from `examples/quickstart.json` shape |

**Exit:** `GET /api/v2/modules/mod_jev` healthy; flag off ⇒ 403; flag on ⇒
mock/hf shim returns valid `SystemOneResponse` JSON; `check_docs` PASS.

**Owner:** `soma-wiring-engineer` + `soma-adversarial-skeptic` (parallel)

### W-J2 · Guardrail & approval choke (D-1/D-2) — **3–4 days** · **P0 value**

| Task | Notes |
|---|---|
| Insert choke in **one** place: tool authorize path used by chat **and** Kafka (`admin/core/tool_calling.py` / request_handler) | F-3 fix: one choke |
| Call `Noul` + `Score` via shared client | state: tool, args digest, risk_class, tenant |
| Map Noul.noul→input.p_safe, Score.score→input.risk, .confidence→input.confidence (NEVER noul→confidence) | Reuse 0.3 / `min_acceptance` |
| Outbox audit event per decision | JEV-R-016 |
| Metrics `jev_guardrail_denied_total`, `jev_confidence` | JEV-R-017 |
| Tier-3 tools (`packages_ensure`, `os_packages_ensure`, `code_execute`, …) require `noul ≥ min` **or** human approval | No silent allow |
| Operator override endpoint/flow with audit | Q-7 |
| Tests: unsafe golden set deny; safe golden set allow; flag-off = legacy path; shim down = fail-closed for tier-3 | VIBE |

**Exit:** Live stack: requesting a tier-3 tool produces an audit row with JEV
probabilities; denying is visible in UI/logs; p95 &lt; budget.

**Owner:** `soma-wiring-engineer` + `soma-cognitive-engineer`

### W-J3 · Tool/model router + turn triage (D-3–D-6) — **3–5 days** · P1

| Task | Notes |
|---|---|
| D-3: rank `tools_for_llm` with `Choice` when N &gt; threshold | Closed-world tool names only |
| D-4: `select_model` tie-break `Choice` when \|candidates\|&gt;1 | Rules remain floor |
| D-5: turn `Score` urgency into turn metadata | Flag `jev_triage` |
| D-6: escalation `Noul` on failure / low confidence | Wire `should_flag` |
| UI: probability bars (reuse OpenJev render style) in admin/tool approval | Lit 3.x only |
| Delegation (Seam D) optional batch: eval / calibration jobs | Kafka `a2a` + HMAC callback |

**Exit:** E2E shows ranked tools; triage badge on urgent turns; escalation
creates notification/audit.

**Owner:** `soma-cognitive-engineer` + `soma-ui-engineer`

### W-J4 · Hardening, evidence, hand-over — **2–3 days**

| Task | Notes |
|---|---|
| Golden decision sets + calibration notes (entropy conf. caveat) | ARCH §11 R-4 |
| Evidence package `docs/iso/evidence/JEV-WP-*/` | No mocks in acceptance |
| Ops runbook: pin bump, flag rollback, Vault rotation | DEL-6 |
| Contract tests vs upstream when `openjev serve` lands | Swap shim |
| Close RFP DEL-1…DEL-6 | Traceability matrix |

**Exit:** All `JEV-R-*` Verified with evidence paths; hand-over reviewed.

---

## 3. Work breakdown → RFP deliverables

| Deliverable | Wave | Acceptance |
|---|---|---|
| DEL-1 Seam decision record | W-J0 | ARCH §6 binding C+B+D+E |
| DEL-2 Integration specification | ARCH-JEV-001 + this plan | `check_docs.py` PASS |
| DEL-3 Traceability matrix | W-J0/W-J4 | Every `JEV-R` covered |
| DEL-4 Implementation | W-J1–W-J3 | Code review + tests |
| DEL-5 Evidence package | W-J2/W-J4 | `docs/iso/evidence/…` |
| DEL-6 Hand-over | W-J4 | Ops doc matches as-built |

---

## 4. Requirement traceability (architecture → JEV-R)

| JEV-R | Where designed | Wave |
|---|---|---|
| 001 Invocation contract | ARCH §9.1 | W-J1 |
| 002 tenant_id | ARCH §9.1 | W-J1 |
| 003 timeout/retry | ARCH §8.1, §9.1 | W-J1 |
| 004 existing control plane | ARCH §6, §8.1 mod_jev | W-J1 |
| 005 feature flag fail-closed | ARCH §8.1 | W-J1 |
| 006 config endpoints only | ARCH §8.1 | W-J1 |
| 007 Vault secrets | ARCH §9.2 | W-J1 |
| 008 callback JWT/HMAC | ARCH §9.2 | W-J3 (D seam) |
| 009 UnifiedGate | ARCH §9.2 | W-J2 |
| 010 MemoryGateway only | ARCH §9.3 | W-J1 |
| 011 bounded recall | ARCH §9.3 | W-J1 |
| 012–015 Delegation | ARCH §8.3, plan W-J3 | W-J3 |
| 016–017 Audit + RED | ARCH §9.4 | W-J2 |
| 018–019 Docs / no code early | This plan G-0 | W-J0 |

---

## 5. Testing strategy

| Layer | What | Runner |
|---|---|---|
| Unit | Request builder, flag gates, choke mapping, timeout fail-closed | `pytest tests/unit` |
| Contract | JSON schema vs OpenJev golden responses | `pytest tests/contract` (new) |
| Integration | Live shim + OPA confidence + UnifiedGate | standalone stack |
| E2E | Human Playwright: tool request → JEV decision → allow/deny visible | `tests/e2e` |
| Decision quality | Golden unsafe/safe tool-call sets | `tests/proofs` |
| Regression | Flag-off legacy path unchanged | unit + e2e |

**Prohibited:** `--profile mocks` for acceptance (VIBE/T-8). Unit tests may use
the OpenJev **mock backend** only to test the **adapter client**, not the
acceptance of guardrail quality.

---

## 6. Suggested file map (implementation time — not now)

```
admin/modules/mod_jev/
  module.yaml
  api.py                 # Ninja routes /config, /health
  hooks.py               # optional orchestrator hooks
services/common/decisions/
  client.py              # decide() shared
  contracts.py           # SystemOne DTOs mirroring OpenJev
  audit.py
infra/…/openjev-shim/    # integration-owned service
policy/confidence.rego   # extend input docs only if needed
policy/tool_policy.rego  # jev_decide catalog entry
tests/unit/test_jev_*.py
tests/contract/test_openjev_contract.py
docs/iso/evidence/JEV-WP-*/
```

Names may be refined at W-J0 claim time; **do not invent a second memory or
settings stack.**

---

## 7. Rollback & safety

| Scenario | Behaviour |
|---|---|
| Flag `jev_guardrail` off/unset | **deny tier-3** / require_approval (NOT legacy allow) |
| Shim unreachable | Tier-3 ⇒ deny/approval (fail-closed); tier-1 may proceed per policy |
| Bad OpenJev version | Roll pin; shim contract tests catch drift |
| Suspect decisions | Operator override + audit; disable flag |

---

## 8. Effort summary (planning estimate)

| Wave | Effort | Risk |
|---|---|---|
| W-J0 | 0.5–1 d | Low |
| W-J1 | 2–3 d | Med (settings/Vault only) |
| W-J2 | 3–4 d | Med (choke correctness) |
| W-J3 | 3–5 d | Med (UI + router) |
| W-J4 | 2–3 d | Low |
| **Total** | **~11–16 person-days** | excluding vendor RFP overhead |

---

## 9. Immediate next actions (still docs-only)

1. Review `SOMA-ARCH-JEV-002` with SomaTech panel → move Status Draft → In Review.
2. Answer RFP open Q-1…Q-5 in a decision record (this plan § recommendations).
3. Run `python scripts/gen_register.py` + `python scripts/check_docs.py`.
4. **Stop.** Wait for operator G-0 before any code.

*End of document — SOMA-PM-PLAN-JEV-INTEGRATION-001 v1.0.0*
