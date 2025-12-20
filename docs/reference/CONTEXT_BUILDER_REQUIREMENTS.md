# Production‑Ready Analysis of the Context Builder Roadmap

*Project:* **SomaAgent01 – Context Builder**  
*Date:* 2025‑11‑13  
*Author:* Senior Architect / Senior Developer / Senior Software Analyst (AgentZero)

---

## 1️⃣ Overview
The existing four‑week roadmap defines a solid end‑to‑end pipeline (retrieval → salience → scoring → OPA policy → Presidio redaction → token budgeting → Jinja2 rendering → feedback).  It also provides unit, integration, and end‑to‑end tests, Prometheus observability, and documentation.

**Goal of this analysis:** Identify every gap that prevents a production release, propose concrete mitigations, and produce a final checklist that, once satisfied, makes the implementation production‑ready.

---

## 2️⃣ Production‑Readiness Checklist
| Area | Required Item | Current Status | Action to Reach ✅ |
|------|---------------|----------------|-------------------|
| **Code base** | `python/context_builder.py` exists and imports without errors | ✅ Implemented | Production implementation complete |
| **Templates** | `templates/context_prompt.j2` present and renderable | ✅ Created | Add Jinja2 auto‑escape config and test rendering |
| **Preload** | `preload.py` imports and instantiates `ContextBuilder` | ❌ Missing | Add import + singleton creation (see §3.7) |
| **Dependencies** | All runtime packages listed in `requirements.txt` (presidio‑analyzer, presidio‑anonymizer, tiktoken, jinja2, httpx, prometheus‑client, fastapi, uvicorn) | ✅ Partially listed | Append missing `presidio-analyzer` and pin exact versions |
| **Docker / CI** | Dockerfile installs new deps, CI spins up Somabrain service, runs unit/integration/E2E tests | ❌ Not verified | Update Dockerfile, add Docker‑compose service in CI workflow |
| **Error handling** | Retries / circuit‑breaker for all external calls, explicit failure when Somabrain unavailable | ❌ Not defined | Wrap each `SomaClient` call in `try/except` with exponential back‑off; return a clear error when unavailable |
| **Token budgeting** | Greedy selection may drop high‑value snippets; need optimal selection option | ❌ Not implemented | Add optional knapsack‑style budgeting (`_budget_optimal`) and config flag |
| **Feedback payload** | Includes `doc_id`, `success`, `tenant`; missing score & timestamp for learning | ❌ Not implemented | Extend payload to `{doc_id, success, score, timestamp, tenant}` |
| **Security** | API keys injected via env vars, never logged; secrets masked in logs | ❌ Not verified | Ensure `SOMA_API_KEY` is read from env, add `logging.Filter` to strip it |
| **Observability** | Prometheus metrics defined, exported at `/metrics`, alerts for latency & error rate | ✅ Defined | Verify metrics are registered in the global registry and scraped by Prometheus |
| **Documentation** | MkDocs builds, includes architecture diagram, config table, usage examples | ✅ Drafted | Add Mermaid diagram, env‑var table, and quick‑start snippet; run `mkdocs build` |
| **Compliance** | No test‑double frameworks used; all tests hit a real Somabrain instance | ✅ Planned | Ensure CI starts Somabrain container and waits for health endpoint |
| **Release checklist** | Version bump, changelog, Docker image tag, smoke test in staging | ❌ Not created | Create `CHANGELOG.md` entry and a staging deployment script |

---

## 3️⃣ Detailed Action Items (Grouped by Week)
### Week 1 – Foundation (already completed)
- Verify Dockerfile installs `presidio-analyzer` and pins all versions.
- Run `docker build -t somaagent01:dev .` and confirm image size increase < 100 MB.
- Add `ENV PYTHONPATH=/root/somaagent01:$PYTHONPATH` to Dockerfile.

### Week 2 – Retrieval & Scoring
- **Implement `SomaClient.salience()`** (already drafted).
- **Composite scoring** – ensure normalization of similarity, salience, recency; store weight config in `settings.yaml`.
- **Integration test** – spin up Somabrain container, run `tests/integration/test_context_builder_retrieval.py`.
- **Add logging of scores** (`logger.info(f"Doc {id} score={composite:.3f}")`).

### Week 3 – Guardrails & Rendering
- **OPA policy** – add `SomaClient.evaluate_policy()` and unit‑test it against a real policy bundle in `policy/`.
- **Presidio redaction** – instantiate `AnalyzerEngine` & `AnonymizerEngine`; cache analyzer results per document to reduce latency.
- **Token budgeting** – implement both greedy (`_budget`) and optimal (`_budget_optimal`) algorithms; expose `USE_OPTIMAL_BUDGET` env flag.
- **Jinja2 rendering** – create `templates/context_prompt.j2` with proper auto‑escape and validate template presence at startup.
- **Preload integration** – modify `/root/somaagent01/python/preload.py`:
  ```python
  from python.context_builder import ContextBuilder
  CONTEXT_BUILDER = ContextBuilder(
      max_tokens=int(os.getenv('SOMA_MAX_TOKENS', '2000')),
      top_k=int(os.getenv('SOMA_RECALL_TOPK', '200')),
  )
  ```
- **Error handling** – wrap each external call in `asyncio.wait_for(..., timeout=5)` and retry up to 3 times.

### Week 4 – Feedback, Observability & Release
- **Feedback API** – extend `ContextBuilder.feedback()` payload with `score` and `timestamp`.
- **Prometheus metrics** – increment `CONTEXT_SNIPPETS_TOTAL` with label `stage` at each pipeline step; expose `context_builder_tokens_used` gauge.
- **E2E test** – verify:
  - Prompt length ≤ `SOMA_MAX_TOKENS`.
  - No email/SSN patterns remain (`grep -E "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"`).
  - All snippets passed OPA (`allowed=True`).
- **CI pipeline** – add Docker‑compose service `somabrain` and a health‑check loop before tests.
- **Documentation** – finalize `docs/context_builder.md` with:
  - Mermaid diagram of the pipeline.
  - Table of env vars (`SOMA_MAX_TOKENS`, `SOMA_RECALL_TOPK`, `USE_OPTIMAL_BUDGET`).
  - Example usage in FastAPI endpoint.
- **Release** – bump version in `pyproject.toml`, generate `CHANGELOG.md`, push Docker image with tag `v1.0.0-prod`.

---

## 4️⃣ Acceptance Criteria (Production Ready)
1. **All unit, integration, and E2E tests pass** on a clean CI runner (no test‑double libraries).
2. **Docker image builds** without errors and size increase ≤ 100 MB.
3. **Prometheus metrics** are exposed at `/metrics` and can be scraped.
4. **No PII leakage** – automated regex scan of generated prompts returns zero matches.
5. **OPA policy** never blocks a document that should be allowed (verified with a test policy suite).
6. **Token budget** never exceeds the model’s hard limit (checked via `tiktoken` token count).
7. **Documentation builds** with MkDocs and includes a working quick‑start example.
8. **Security review** confirms API keys are only read from environment variables and never logged.
9. **Release checklist** completed: version bump, changelog, Docker tag, staging smoke test.

---

## 5️⃣ Observability & Alerting
| Metric | Type | Recommended Alert |
|--------|------|-------------------|
| `context_builder_prompt_total` | Counter | Alert if rate drops > 50 % compared to baseline (possible pipeline break). |
| `context_builder_prompt_seconds` | Histogram | Alert on p95 > 200 ms (latency regression). |
| `context_builder_snippets_total{stage="policy"}` | Counter | Alert if policy‑blocked ratio > 30 % (policy too strict). |
| `context_builder_tokens_used` | Gauge | Alert if value > `SOMA_MAX_TOKENS` (should never happen). |
| `httpx_request_errors_total` (custom) | Counter | Alert on sudden spike (> 5/min). |

---

## 6️⃣ Risk Register & Mitigations
| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Somabrain service unavailable during request | Service outage | Medium | Circuit‑breaker with explicit error response and incident logging. |
| Presidio latency > 500 ms per document | Increased latency | Low | Cache analyzer results; run redaction in a thread pool. |
| OPA policy mis‑configuration blocks all docs | Zero context | Low | Include a health‑check endpoint that returns policy status; require manual remediation. |
| Token‑budget algorithm drops high‑value snippet | Reduced relevance | Medium | Provide optimal budgeting flag; monitor `snippets_total` per stage. |
| Dependency version conflict (e.g., httpx vs fastapi) | Build failure | Low | Pin exact versions in `requirements.txt` and run `pip check` in CI. |

---

## 7️⃣ Final Verdict
The roadmap is **almost production‑ready**. By completing the missing preload integration, finalizing dependency pins, adding robust error handling, implementing the optional optimal token‑budget algorithm, extending the feedback payload, and ensuring CI spins up a real Somabrain instance, the solution will satisfy all production criteria listed above.
