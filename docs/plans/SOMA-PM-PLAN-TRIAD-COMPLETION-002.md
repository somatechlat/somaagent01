# SOMA-PM-PLAN-TRIAD-COMPLETION-002 — Audit of Touched Code + Completion Plan

| Field | Value |
|---|---|
| Document ID | SOMA-PM-PLAN-TRIAD-COMPLETION-002 |
| Revision | 0.1 |
| Status | DRAFT — awaiting owner approval to execute |
| Date | 2026-10-04 |
| Scope | somaAgent01 · somabrain · somafractalmemory |
| Predecessor | `docs/plans/SOMA-PM-PLAN-CHAT-COGNITION-001.md`, `docs/plans/2026-10-03-triad-full-integration.md` |
| Authority | `docs/standards/SOMA-STD-CODING-001.md` (VIBE) |

**Design criteria applied to every decision below:** the rules · millions of transactions · security · speed · latency · thin.

---

## Part 0 — AUDIT OF CODE TOUCHED IN THIS SESSION

Every item below was verified by running the code or reading the diff, not by assertion.

### 0.1 Defects I introduced and must fix (P0)

| ID | Defect | Evidence | Severity |
|---|---|---|---|
| **A-1** | `_from_infraconfig` is **dead on the async request path**. `asyncio.get_event_loop().run_until_complete(...)` raises `RuntimeError: This event loop is already running`, the bare `except Exception` swallows it, the resolver returns `None`, and the operator layer never applies. It also creates an **un-awaited coroutine** — the exact class of bug already fixed once elsewhere. | Reproduced: `async path result: SILENTLY-LOST -> RuntimeError: This event loop is already running` + `RuntimeWarning: coroutine 'SyncToAsync.__call__' was never awaited` | **P0 — the feature is a lie** |
| **A-2** | I wrote literal Vault URLs (`http://localhost:20882`, `http://localhost:30200`) as defaults in a new file. | Removed; file deleted | Fixed |
| **A-3** | I copied `vault_root_token` and `somabrain_memory_http_token` into `/tmp/secrets` inside a container. Violates *"never write a secret to any file, including /tmp — pass it in-process only."* | Removed and verified clean | Fixed |
| **A-4** | I created `infra/standalone/provision_shared_brain_token.py` — an unnecessary file that hand-seeds secrets instead of fixing the real provisioning path. | Deleted | Fixed |
| **A-5** | I introduced compose `${VAR:-default}` values and a duplicated `SUPERVISOR_HTTP_PASS` line. `:-` **is** a hardcoded fallback. | Rewritten to `:?set VAR` throughout the `vault_init` job | Fixed (one job; whole file still to sweep) |

### 0.2 What is correct and must not be re-litigated

| Change | Commit | Why it is right |
|---|---|---|
| ENV removed from the service-URL resolution chain | `10c43808` | A value sourced from ENV is one an operator cannot edit and an auditor cannot see. Chain is now `Capsule > AgentSetting > InfrastructureConfig > SettingsModel`, and a missing value **raises**. |
| `SOMABRAIN_URL` resolves through the operator layer | `9dfddab5` | The owner ruled a service URL is an editable parameter. (Subject to A-1: the layer must actually work first.) |
| Tool loop produces an answer, not a stop string | `30e84566` | Terminal round after the tool chain; `tool_choice` sent; approval executes on approve and is terminal on deny; digests under the message cap. |
| One replay authority for memory writes | `6c576f86`, `f3c23136` | T-6 durable-before-hop; the Kafka `memory.wal` outbox is the single degraded path. |
| Model↔key relation, duplicates and dummies removed from UI | `5a1df10a`, `c6c4610d` | Relational (one secret, both directions visible); 7 duplicate screens deleted; fabricated figures and dead controls deleted; `iq-store.ts` no longer re-implements the lookup tables. |
| Brain compose: shared credential written to the path the reader uses | somabrain `e894bee` + uncommitted follow-up | `vault_client.get_runtime_secret` reads `secret/agent/credentials[somabrain_memory_http_token]`. The old write to `somabrain/runtime` was invisible to it. |

### 0.3 Uncommitted work that must be landed or discarded

| Tree | State | Action |
|---|---|---|
| somaAgent01 | `D infra/standalone/provision_shared_brain_token.py` | Commit the deletion (correct — it was an unnecessary file). |
| somabrain | `M infra/standalone/docker-compose.yml` | The `vault_init` rewrite. Validate, then commit. |

---

## Part 1 — VERIFIED STATE OF THE TRIAD (facts, not aspiration)

| Fact | Evidence |
|---|---|
| SomaBrain answers `/health` 200 | live curl, `localhost:30101` |
| Memory **write and recall fail 401** | brain token len=**17**, agent token len=**64** — two independent generations of one trust-boundary credential |
| Root cause of the 401 is in the provisioning code | `vault_init` wrote `memory_http_token` to `somabrain/runtime`; `vault_client.py` reads `secret/agent/credentials`. Writer and reader disagreed. |
| `DisallowedHost` is a real defect, now fixed in compose | `ALLOWED_HOSTS` held `somabrain_standalone_app` — underscores fail Django's `host_validation_re`, so that entry could never match. Clean alias `somabrain` added. |
| Unit suite **refuses to start without Vault** | `RuntimeError: VIBE Rule 164 VIOLATION: django_secret_key is missing` — fail-closed, correct behaviour |
| Last green unit baseline in-session | 598 passed · 2 failed (`phase_completed >= 8`) · 3 skipped |
| Chat answers | live WS: `{"content":"STREAM-OK","model":"groq/openai/gpt-oss-120b",...}` |

---

## Part 2 — THE PLAN

### Part A — Make the memory lane round-trip *(gates everything)*

**Goal:** the user can type "what codeword did I ask you to remember?" and get the fact back.

| # | Task | Files | Gate |
|---|---|---|---|
| A1 | **Fix A-1.** Make the settings resolver work from both sync and async without swallowing errors. Resolve once, cache in a bounded store invalidated on settings write. An async call site must not block the event loop. | `admin/core/helpers/service_urls.py`, `admin/core/helpers/settings.py` | Unit test: resolver returns an `InfrastructureConfig` value when called from `asyncio.run`, and raises (not `None`) when unconfigured. No un-awaited coroutine warning. |
| A2 | **One shared credential, one authority.** `init_vault.py` (agent) is the generator. Brain `vault_init` reads the **same t=0 material** via `SOMABRAIN_MEMORY_HTTP_TOKEN_FILE` (a path, like `VAULT_TOKEN_FILE`) and writes it to `secret/agent/credentials`. No ENV value, no per-stack generation. | somabrain `infra/standalone/docker-compose.yml`, `somaAgent01/infra/standalone/init_vault.py` | Re-run `vault_init`; read-back matches agent t=0 length. |
| A3 | **Remove `SOMABRAIN_MEMORY_HTTP_TOKEN` from ENV everywhere.** It is a secret. Every service reads it from Vault via `UnifiedSecretManager.get_credential`. | all three repos, compose + settings | `grep -rn "SOMABRAIN_MEMORY_HTTP_TOKEN" **/docker-compose*.yml` → only the `*_FILE` path reference remains |
| A4 | **Live round-trip.** | — | Playwright: save fact → new turn → recall returns it. ≤2 tool calls. Never a stop string. |

### Part B — Purge every hardcoded value *(the owner's standing order)*

Two agents are already sweeping. Their output becomes the backlog for this part.

| # | Task | Gate |
|---|---|---|
| B1 | Every literal URL / host / port in `config/`, `admin/`, `services/`, `somabrain/`, `somafractalmemory/` resolves through the chain or **raises** | `grep -rnE "localhost\|127\.0\.0\.1\|host\.docker\.internal"` → only bootstrap + comments |
| B2 | Every compose `${VAR:-default}` becomes `${VAR:?set VAR}` | `grep -rnE '\$\{[A-Z0-9_]+:-' infra/` → empty |
| B3 | Every magic number that is really policy becomes a setting (timeouts, limits, dims — the seam dim is **768** and must come from settings, not `np.zeros(512)`) | tests assert the value is read from settings |
| B4 | **No fallbacks.** Delete `getattr(settings, X, default)` and `os.environ.get(KEY, default)` outside the bootstrap allow-list | the bootstrap allow-list is exactly: `SA01_DEPLOYMENT_MODE`, `VAULT_ADDR`, `VAULT_TOKEN_FILE`, `POSTGRES_HOST`, `POSTGRES_PORT` |

### Part C — Enterprise RBAC, one store, zero-trust

Owner ruling: *"Why are you using JSON for roles?! … unified whole pattern RBAC Django + SpiceDB … we leave only the one managed by enterprise infra … zero-trust."*

| # | Task | Gate |
|---|---|---|
| C1 | Delete `LocalIdentity.roles` as an authority; delete `PlatformConfig.defaults["roles"]` and the decoy `PATCH /aaas/settings/roles/{id}` | one store answers every role question |
| C2 | `sysadmin` becomes a superset of every role (today it cannot chat); same for `org_admin` | `test_role_superset.py` |
| C3 | `TenantRole` vocabulary equals `ROLE_PERMISSIONS` exactly — enforced at import | mismatch fails at boot |
| C4 | SpiceDB always consulted, may only narrow; unmapped verb denies; no tenant denies (T-5) | `check_endpoint_permission` uses the same map as `check()` |

### Part D — Capsule-owned, auto-discoverable tools

| # | Task | Gate |
|---|---|---|
| D1 | Owner FK on `Capability`; name unique **per capsule** | two capsules with different tool sets |
| D2 | Loader for `Capability.implementation` (`{type, module, class}` — already on the model) | a capsule tool runs |
| D3 | Discovery filters by capsule **and** permission — a tool the subject may not use is never advertised | discovery output matches authz |
| D4 | Per-tool authz at execution: `authorize(..., "resource:tool_execute", resource=name)` | deny is terminal |
| D5 | MCP routing (`provider="mcp"`); the SRS trace matrix cites a file that does not exist — fix or delete the citation | docs match code |

### Part E — 100% of SomaBrain and SFM capacity

Security first: constitution routes are now gated; OPA update fails closed (landed). Then:

| # | Task | Gate |
|---|---|---|
| E1 | Start gRPC/UDS (`serve_brain_grpc` landed) — compose volume `soma_run:/run/soma`, and a service that actually starts it | `grpcurl` a real RPC |
| E2 | `remember/batch`; advanced recall (`perform_recall` fields now mounted) | batch write returns N acks |
| E3 | Unify the three neuromod stores onto `bootstrap.singletons` (landed) — verify chat's neuro sync actually changes cognition | a sync changes a cognitive readout |
| E4 | Full sleep FSM with the edge back to ACTIVE (landed) + WM→LTM promotion + NREM/REM (landed) | state machine reaches ACTIVE again |
| E5 | oak, threads, `context/feedback`, `plan/suggest`, `personality` | each has one live test |
| E6 | SFM: `GET /graph/path`, `/stats`, `/metrics`, AuditLog, `export_graph` | each returns real data |
| E7 | Temporal wired to the whole cycle; degradation when SomaBrain is unreachable | kill SomaBrain → chat still answers, writes queue to `memory.wal`, drain replays |

### Part F — UI/UX, testing workbench, docs truth

| # | Task | Gate |
|---|---|---|
| F1 | AgentIQ editable and visible — today Save is blocked because no HTTP surface exposes knobs/`DerivedSettings`. **Build the surface**; the UI already refuses to fake one | knob save round-trips |
| F2 | One settings surface grouped by `SOMA-SETTINGS-MODEL-001` L1–L4; every service URL administrator-editable there | edit `SOMABRAIN_URL` in UI → memory lane repoints without a rebuild |
| F3 | Testing workbench runs what actually needs testing; delete what does not work | workbench reflects real suites |
| F4 | Docs that lie are corrected: `somabrain/README.md`, `FINAL_VERIFICATION_REPORT.md`, `VIOLATIONS.md`, `SOMA-BRAIN-COMPLIANCE-001.md`, `SOMA-01-UIUX-001.md` (invented `role:manage`), `SOMA-UI-SPEC-001/002` (three disagreeing model↔key designs) | `python3 scripts/check_docs.py` → 0 non-compliant |
| F5 | ISO document control + traceability for every requirement in this plan | each row traces to a test |

---

## Part 3 — ORDER AND GATES

| # | Part | Gate before the next |
|---|---|---|
| 1 | **A1** — the resolver actually works | unit: async + sync both resolve; missing → raises |
| 2 | **A2–A3** — one credential | read-back length matches the agent t=0 value |
| 3 | **A4** — live memory round-trip | Playwright: save → recall returns the fact |
| 4 | **B** — hardcoded values gone | both greps empty; suite green |
| 5 | **C** — one role store | `sysadmin` can chat **and** configure |
| 6 | **D** — capsule tools | two capsules, different tool sets, permission-filtered |
| 7 | **E** — 100% capacity | each capability live or explicitly out of scope |
| 8 | **F** — UI + docs truth | every control has a handler; `check_docs.py` clean |

Chat is the product → the memory lane is how the agent learns → roles block the UI → tools are how the agent acts → SomaBrain is how it thinks.

---

## Part 4 — WHAT I WILL NOT DO

- **No fallbacks.** A missing value raises. Not a default, not a substitute host.
- **No secrets in ENV, and never written to a file** — including `/tmp`. In-process only.
- **No stubs, shims, TODOs or "temporary" code.** A shim is a bypass.
- **No hardcoded values.** A URL or number in source is a URL an operator cannot change and an auditor cannot see.
- **No weakening a gate to pass a test.** If a test needs a real credential and it is absent, the honest outcome is a failure naming the missing secret.
- **No Claude attribution** in commits or PRs.

---

## Part 5 — IMMEDIATE NEXT ACTIONS (in order)

1. **Fix A-1** — the resolver. Everything about "the operator owns the URL" is false until this is true. Highest leverage single fix in the plan.
2. Commit the `provision_shared_brain_token.py` deletion and validate + commit the brain `vault_init` rewrite.
3. Re-run brain `vault_init` against the agent's t=0 material → the 401 closes.
4. Run the live repro: `CODEWORD-BLUE-FALCON-77` save, then *"what codeword did I ask you to remember?"*
5. Fold the two hardcoded-value sweeps into Part B and execute.

**Stop gate:** nothing in Parts C–F starts until Part A's gate is green, because until the memory lane round-trips the user cannot chat, and chat is the product.
