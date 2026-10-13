# SOMA-RPT-PROD-HARDENING-001 — Production Hardening Skill-vs-Code Audit

## Document Control

| Field | Value |
|---|---|
| Document Title | Production hardening skill-vs-code audit (gateway, authz, middleware, rate limits, SSRF + peer blocks) |
| Document Identifier | SOMA-RPT-PROD-HARDENING-001 |
| Version | 1.1.0 |
| Date | 2026-10-14 |
| Status | Draft |
| Author | soma-prod-hardening |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2027-01-14 |
| Related | `.mimocode/agent/soma-prod-hardening.md`, `docs/standards/SOMA-STD-TRIAD-001.md`, `docs/standards/SOMA-STD-SECURITY-001.md`, `docs/standards/SOMA-LAW-SECURITY-001.md`, `docs/reports/SOMA-RPT-SEC-REVIEW-2026-10-13.md` |
| Audience | Operators, security-reviewer, triad agents |
| Scope | `somaAgent01` (authz catalog, gateway settings, security middleware, rate limits, egress/SSRF) + peer security blocks in sibling checkouts `somabrain` / `somafractalmemory` |
| Mode | Docs + skill-text only. No production code, settings, or runtime config changed. Chat/Docker untouched. No secrets read or printed. |
| Commits | Skill alignment + report + A2A claim/ledger only |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | soma-prod-hardening | Initial issue. Skill-vs-code alignment matrix, P0–P3 findings with `file:line`, invariant map. |
| 1.1.0 | 2026-10-14 | soma-prod-hardening | Re-audit against live code. Added AuthZ catalog surface (`admin/core/authz.py`) and security middleware (`admin/common/middleware.py`) to the matrix. Skill text aligned to live code (anchors table, proxy-TLS SSL exception, scope = this repo + sibling peer audit, authz one-path rule). All `file:line` re-verified. |

---

## 1. Purpose and method

Question: **do the `soma-prod-hardening` skill instructions match live code, and where are the production hardening gaps?**

Sources read (live, not paraphrase):

| Surface | Path |
|---|---|
| Skill (the bar) | `.mimocode/agent/soma-prod-hardening.md` |
| Shared law | `docs/standards/SOMA-STD-TRIAD-001.md`, `docs/standards/SOMA-STD-SECURITY-001.md`, `docs/standards/SOMA-LAW-SECURITY-001.md` |
| Settings authority | `config/settings.py` → `services/gateway/settings.py` (one chain) |
| AuthZ catalog | `admin/core/authz.py` |
| Security middleware | `admin/common/middleware.py` (`SessionMiddleware`, `CSPMiddleware`) |
| Rate limits | `admin/common/rate_limit.py`, `services/common/rate_limiter.py`, `admin/ratelimit/api.py` |
| Outbound / SSRF | `services/tool_executor/assistant_tools/web_read.py`, `services/tool_executor/assistant_tools/web_search.py`, `admin/auth/api_sso.py`, `admin/platform/api/integrations.py` |
| Peer security blocks | `somabrain/somabrain/settings/django_core.py`, `somafractalmemory/somafractalmemory/settings/django_core.py` (sibling checkouts under `Documents/GitHub/`) |

Commands actually run this turn:

```text
rg (settings / rate limit / top_k / limit / save / SSRF / pagination / authz sweeps)
ls + sed on the anchors listed above (line-level re-verification)
```

`manage.py check --deploy` still **fail-closed before Django loads** when Vault is absent: `RuntimeError: VIBE Rule 164 VIOLATION: VAULT_ADDR is not set` at `services/gateway/settings.py:35` → `services/common/unified_secret_manager.py:48`. That is correct behaviour (Vault-only secrets, no default), not a defect. Deploy-check findings therefore cannot be enumerated in this offline audit — acceptance item 8 remains **open** pending a Vault-backed run (see P2-8). Per operator: no Docker restart, no runtime config change this turn.

---

## 2. Alignment matrix — skill instruction vs live code

Legend: **MATCH** = skill text and code agree · **PARTIAL** = some call sites obey · **GAP** = required control missing or contradicted · **SKILL-TEXT** = skill wording vs code (fixed in 1.1.0) · **OPEN** = evidence not obtainable this turn.

| # | Skill requirement (normative) | Code evidence | Verdict |
|---|---|---|---|
| A0 | AuthZ one catalog, fail-closed, no wildcards | `admin/core/authz.py:1-26` law (no wildcards :15-16, fail-closed :18-19, org-scoped :21-23); catalog build guard `:206`; role guards `:439-448`; `permissions_for_principal` key/role split `:512-550`; consumers: `services/common/authorization.py:103`, `admin/auth/api_helpers.py:17`, `admin/platform/models/choices.py:79-88` (vocabulary must agree). Skill now names this path | **MATCH** (after skill alignment) |
| A1 | `SECURE_SSL_REDIRECT` on in prod **unless** TLS at proxy (documented exception + HSTS kept) | Absent in gateway `services/gateway/settings.py` (rg zero hits in `somaAgent01`). Peers document the intentional exception: `somabrain/somabrain/settings/django_core.py:199-201`, `somafractalmemory/somafractalmemory/settings/django_core.py:153-155` ("TLS at a proxy… breaks plain-HTTP health checks"). HSTS still set on peers (:208-210 / :161-163) | **MATCH** (skill text corrected 1.1.0; see P3-1) |
| A2 | `SESSION_COOKIE_SECURE=True` | Gateway `services/gateway/settings.py:55` `= not DEBUG`; peers unconditional when `not DEBUG` (Brain `django_core.py:203` / SFM `:156`) | **MATCH** (prod path) |
| A3 | `SESSION_COOKIE_HTTPONLY=True` | **Not set** in gateway (Django default is `True`, but skill demands explicit). Peers set it: Brain `:205` / SFM `:158` | **PARTIAL** (P2-2) |
| A4 | `CSRF_COOKIE_SECURE=True` | Gateway `services/gateway/settings.py:56` `= not DEBUG`; peers Brain `:204` / SFM `:157` | **MATCH** (prod path) |
| A5 | `CSRF_COOKIE_HTTPONLY=True` (where applicable) | **Not set** in gateway. Peers set it: Brain `:206` / SFM `:159` | **GAP** (P1-2) |
| A6 | `SECURE_HSTS_SECONDS` set (+includeSubDomains/preload) | Gateway `services/gateway/settings.py:203` `= 0 if DEBUG else _behaviour("sa01_hsts_seconds")` — operator knob, field `Optional[str]` `admin/core/helpers/settings_model.py:609` `default_factory=lambda: _dj("SECURE_HSTS_SECONDS")` → may resolve empty/None ⇒ HSTS off in prod. Flags `:60-61` `= not DEBUG`. Peers pin `31536000` + both flags (Brain `:208-210` / SFM `:161-163`) | **PARTIAL** (P1-3) |
| A7 | `X_FRAME_OPTIONS=DENY` (never absent) | Gateway `services/gateway/settings.py:59` = `"DENY"`; peers Brain `:212` / SFM `:165` | **MATCH** |
| A8 | `SECURE_CONTENT_TYPE_NOSNIFF=True` | Gateway `services/gateway/settings.py:58`; peers Brain `:211` / SFM `:164` | **MATCH** |
| A8b | Security middleware present | `admin/common/middleware.py:263-289` `CSPMiddleware` emits `Content-Security-Policy` (`frame-ancestors 'none'`, `base-uri 'self'`, `form-action 'self'`); `SessionMiddleware` `:60+` validates session on non-excluded paths `:21-37`. Wired at `services/gateway/settings.py:99-110` (SecurityMiddleware + CSP + XFrameOptions) | **MATCH** |
| A9 | `CONN_MAX_AGE` on prod DB | Gateway `services/gateway/settings.py:167` `_db["CONN_MAX_AGE"] = _behaviour_int("sa01_db_conn_max_age", "60")`; schema default `admin/core/helpers/settings_model.py:437-438` | **MATCH** |
| A10 | `CONN_HEALTH_CHECKS` on prod DB | **Absent** in `somaAgent01` (rg zero hits outside peers). Peers set `True` (Brain `django_core.py:281`, SFM `django_core.py:243`) | **GAP** (P1-4) |
| A11 | `DEBUG` decoupled from log level | `DEBUG` from env (`services/gateway/settings.py:44`) with prod guard `:45-46`. Root log level from `_behaviour("log_level")` (`:476`) — **separate knob**. No `DEBUG` driven by `LOG_LEVEL` | **MATCH** (see P2-3 for admin logger override) |
| A12 | Rate limits on auth/chat/tools/search — shared limiter | Shared Redis limiter exists (`services/common/rate_limiter.py:49-75` sorted-set sliding window; URL resolver comment `:63-66`). Enforced only on login: `admin/auth/api.py:555-561` `await check_rate_limit(client_ip, "/api/v2/auth/login")`. Decorator `admin/common/rate_limit.py:98` has **zero production call sites** (only its own docstring `:107`) | **GAP** (P0-1) |
| A13 | `top_k`/`offset`/`limit` hard-capped server-side | Caps present: `services/tool_executor/memory_tools.py:202,527` (`min(top_k,50)`), `admin/memory/api/memory.py:150` (`min(limit,100)`), `:212` (`min(payload.top_k,50)`), `admin/agents/api/core.py:73` (`min(max(limit,1),200)`). **Uncapped:** `admin/somabrain/api_router.py:60` `limit: int = 10` → `:110` `max(1, int(payload.limit))` (floor only); `admin/notifications/api/notifications.py:45` `limit: int = 50` → store slice `services/common/notifications_store.py:63` `[:limit]` | **PARTIAL** (P1-5) |
| A14 | Pagination on list endpoints | Present: `admin/chat/api/chat.py:166,191` / `:517,541`, `admin/platform/api/users.py:127-130`, `admin/platform/api/tenant_agents.py:118-126`, `admin/voice/service.py:390-404`. **Missing:** `admin/tools/api/tools.py:50-73` `list_tools` + `:75` `list_catalog` (full Capability dump, no page/cursor), `admin/notifications/api/notifications.py:43-53` (limit only) | **PARTIAL** (P2-5) |
| A15 | SSRF guards on outbound URL fetches | Real guard on `web_read`: `services/tool_executor/assistant_tools/web_read.py:27-45` `_is_public_http_url` (scheme allowlist, localhost/.local/.internal/.lan deny, `ipaddress` private/link-local/reserved deny for literal IPs) enforced at `:99` before fetch. `web_search` takes base host only from the operator settings chain (`web_search.py:4-6,45-64` — model never supplies host). **No shared guard** on `admin/auth/api_sso.py:41-47` (caller-influenced `issuer_url` → `client.get(discovery_url)`; mitigations: `AuthBearer` + `authorize(..., "system:manage_integrations")` `:22-33`) or integration probes `admin/platform/api/integrations.py:291-325`. Claimed `services/common/http_egress.py` (A2A LEDGER C-1) **does not exist on disk** | **PARTIAL** (P1-6) |
| A16 | `save(update_fields=...)` on hot rows | Good: `services/gateway/consumers/chat.py:420` neuromodulator_state; `admin/chat/api/chat.py:378` `update_fields=["title", "updated_at"]`; `services/bridge_worker/dispatcher.py:580` `["context", "updated_at"]`; `services/common/job_planner.py:126` `["status", "started_at", "updated_at"]`; `admin/llm/api.py:722` `update_fields=[fk_name]`. Full-row saves remain on reachable update paths: `admin/llm/api.py:600`, `admin/agents/services/agent_service.py:129,146`, `admin/platform/api/users.py:240,304,467,490,686,780`, `services/conversation_worker/zero_loss_activities.py:138` | **PARTIAL** (P2-6) |
| A17 | Live-verified headers on Brain and SFM | Not verifiable this turn: settings fail-closed without Vault (see §1); operator forbade Docker/runtime change. Peer settings source shows the block is present when `not DEBUG` | **OPEN** (P2-8) |
| A18 | `manage.py check --deploy` findings addressed | Cannot execute (Vault-only `SECRET_KEY`). Unrun | **OPEN** (P2-8) |
| A19 | Vault-only secrets / fail-closed | `services/gateway/settings.py:35-41` hard-fails missing `django_secret_key`; `unified_secret_manager.py:48` hard-fails missing `VAULT_ADDR`. No fallback | **MATCH** |
| A20 | T-1 one memory path | `services/common/memory_gateway.py:13` → `SomaBrainAdapter`; `admin/core/context/builder.py:223` documents no SFM client | **MATCH** |
| A21 | Skill text accuracy vs live code | 1.0.0 skill required `SECURE_SSL_REDIRECT` "on in prod" flat, and implied Brain+SFM live in this repo. Fixed 1.1.0: proxy-TLS exception cited with peer `file:line`; Role scoped to this repo + sibling peer audit; Live-code anchors table added; authz one-path rule added | **SKILL-TEXT → FIXED** (P3-1) |

---

## 3. Findings (P0–P3)

### P0 — production abuse / missing enforcement

#### P0-1 · Rate limits not on the sensitive surface
- **Law:** skill A12 · "Rate limits on sensitive endpoints (auth, chat, tools, search) — shared limiter".
- **Evidence:**
  - Shared limiter **exists** and is Redis-backed: `services/common/rate_limiter.py:49-75` (`RedisRateLimiter`), `:94-124` (sorted-set sliding window).
  - Only enforcement site: `admin/auth/api.py:555-561` `await check_rate_limit(client_ip, "/api/v2/auth/login")`.
  - Decorator `admin/common/rate_limit.py:98-151` — **zero production call sites** (rg `@rate_limit` hits only its own docstring at `:107`).
  - Unthrottled sensitive handlers: `admin/chat/api/chat.py` `send_message`, `admin/somabrain/api_router.py:110` `search_memories` → `gateway.recall`, `admin/tools/api/tools.py:50` `list_tools`, `admin/memory/api/memory.py` `recall`.
- **Why P0:** shared limiter is built and unused on the expensive path; chat/search/tools are the DoS and cost surface. Per-process counters would also violate the backend rate-limit law — do not "fix" with a local dict.
- **Disposition:** IMPLEMENT (code turn). Wire `check_rate_limit` / `@rate_limit` on chat send, memory search/recall, tools list/execute, web_search. Keep Redis shared store. Evidence required: config + a real 429 observation.

### P1 — security block / bounds / SSRF

#### P1-1 · `SECURE_SSL_REDIRECT` policy fork — RESOLVED in skill text (1.1.0)
- **Law:** skill A1. Stop condition forbids turning SSL redirect off to pass a test.
- **Evidence:** gateway has no `SECURE_SSL_REDIRECT` (rg zero hits in `somaAgent01`). Peers deliberately omit it with an explicit reason: `somabrain/somabrain/settings/django_core.py:199-201`, `somafractalmemory/somafractalmemory/settings/django_core.py:153-155` (TLS terminates at a proxy; Django-level redirect breaks plain-HTTP health checks and local compose; HSTS still pins browsers).
- **Analysis:** this is a documented deployment constraint, not a silent miss. The skill text was the outlier.
- **Disposition (done):** skill A1 now states "on in prod **unless** TLS terminates at a proxy — document the exception and keep HSTS", citing the peer `file:line`. The control itself was **not** weakened in code; HSTS remains mandatory. If an operator later wants Django-level redirect behind a non-proxy deploy, that is a code turn, not a skill rewrite.

#### P1-2 · `CSRF_COOKIE_HTTPONLY` missing on gateway
- **Evidence:** not set in `services/gateway/settings.py` (rg). Peers set `True` (Brain `:206`, SFM `:159`).
- **Impact:** CSRF token readable by XSS in the SPA origin.
- **Disposition:** IMPLEMENT `CSRF_COOKIE_HTTPONLY = not DEBUG` (or `True`) in the one settings module.

#### P1-3 · HSTS can resolve to empty in prod
- **Evidence:** `services/gateway/settings.py:203` `SECURE_HSTS_SECONDS = 0 if DEBUG else _behaviour("sa01_hsts_seconds")`; field is `Optional[str]` with `default_factory=lambda: _dj("SECURE_HSTS_SECONDS")` (`admin/core/helpers/settings_model.py:609`). If the knob is unset, prod gets **no HSTS**, while peers pin `31536000`.
- **Disposition:** IMPLEMENT — schema default `31536000` (or fail-closed raise when prod and empty). Never "fix" by zeroing peers.

#### P1-4 · `CONN_HEALTH_CHECKS` missing on gateway DB
- **Evidence:** `services/gateway/settings.py:167-170` sets `CONN_MAX_AGE` and `connect_timeout` only. Peers set `CONN_HEALTH_CHECKS = True` (Brain `:281`, SFM `:243`).
- **Impact:** dead pooled sockets fail late/silently after `CONN_MAX_AGE` reuse.
- **Disposition:** IMPLEMENT `_db["CONN_HEALTH_CHECKS"] = True` beside `CONN_MAX_AGE`.

#### P1-5 · Client can raise `limit` without a server cap
- **Evidence:**
  - `admin/somabrain/api_router.py:60` `limit: int = 10` → `:110` `gateway.recall(..., max(1, int(payload.limit)), ...)` — floor only, **no ceiling**.
  - `admin/notifications/api/notifications.py:45` `limit: int = 50` → store `services/common/notifications_store.py:63` `[:limit]` — no clamp.
- **Contrast (correct pattern):** `admin/memory/api/memory.py:150` `limit = max(1, min(limit, 100))`; `services/tool_executor/memory_tools.py:202` `top_k = max(1, min(top_k, 50))`; `admin/agents/api/core.py:73` `min(max(limit, 1), 200)`.
- **Law:** "Client-supplied values may only lower the cap, never raise it."
- **Disposition:** IMPLEMENT server-side `min()` ceilings on every `limit`/`top_k`/`offset` ingress.

#### P1-6 · SSRF guard only on `web_read`/`web_search`; admin outbound probes unguarded
- **Evidence:**
  - Guarded: `services/tool_executor/assistant_tools/web_read.py:27-45` (`_is_public_http_url`) — scheme allowlist, name denylist, `ipaddress` private/link-local/reserved deny for literal IPs. Enforced at `:99` before httpx. Real code, not comments.
  - Host never model-controlled on search: `services/tool_executor/assistant_tools/web_search.py:4-6,45-64` (`SEARXNG_URL` via settings chain or refuse).
  - Unguarded caller-influenced fetch: `admin/auth/api_sso.py:41-47` builds `discovery_url` from `config["issuer_url"]` and `client.get`s it. Mitigations present: `AuthBearer` + `authorize(..., "system:manage_integrations")` at `:22-33` (good), but **no host allowlist / private-range block**.
  - Unguarded probe: `admin/platform/api/integrations.py:291-325` httpx GET/HEAD to `config['endpoint']` (operator-controlled config — lower risk, still no shared guard).
  - A2A LEDGER cites `services/common/http_egress.py` (C-1 SSRF); **file does not exist** in the tree (re-verified this turn).
  - Residual in `web_read`: hostname denylist is pre-resolve; a DNS name that rebinds to a private IP is not caught (no resolve-then-pin).
- **Disposition:** IMPLEMENT one shared egress guard (allowlist / private-range deny) and route `api_sso` + integrations through it. Keep `web_read`'s check; do not replace it with a weaker one. Document or fix the DNS-rebinding residual.

### P2 — hardening quality / operability

#### P2-2 · `SESSION_COOKIE_HTTPONLY` not explicit on gateway
- Django default is `True`, so the live posture is likely correct; skill demands the setting. Peers set it. One-line explicit set in `services/gateway/settings.py` removes the dependency on a framework default.

#### P2-3 · `admin.*` loggers hardcode DEBUG
- **Evidence:** `services/gateway/settings.py:487-490` `admin`, `admin.platform`, `admin.core`, `admin.agents` all `"level": "DEBUG"` regardless of `log_level` knob (`:476`).
- **Impact:** A11 (DEBUG vs log level) holds at root, but the admin namespace ignores the operator log-level knob in prod — noise + potential sensitive detail in logs.
- **Disposition:** IMPLEMENT — bind these to the `log_level` behaviour (or a separate `admin_log_level`), never a hardcoded DEBUG.

#### P2-5 · List endpoints without pagination
- **Evidence:** `admin/tools/api/tools.py:50-73` `list_tools` and `:75` `list_catalog` return full Capability lists; `admin/notifications/api/notifications.py:43-53` limit-only.
- **Disposition:** IMPLEMENT cursor/offset pagination (skill A14). Update API docs in the same change (docs = truth).

#### P2-6 · Full-row `save()` on reachable update paths
| Site | Model | Note |
|---|---|---|
| `admin/llm/api.py:600` | `LLMModelConfig` | PATCH loop `setattr` then full-row save |
| `admin/agents/services/agent_service.py:129,146` | Capsule / Agent | create/update paths |
| `admin/platform/api/users.py:240,304,467,490,686,780` | user / profile / prefs rows | full-row |
| `services/conversation_worker/zero_loss_activities.py:138` | outbox/WAL row | hot if replay runs |

- Hot paths already correct: `services/gateway/consumers/chat.py:420`, `admin/chat/api/chat.py:378`, `services/bridge_worker/dispatcher.py:580`, `services/common/job_planner.py:126`, `admin/llm/api.py:722`.
- **Law:** do not convert blindly — if a required field write would be dropped, set the correct field list (skill stop condition). Disposition: IMPLEMENT per-site with explicit `update_fields` lists.

#### P2-8 · Deploy-check and live-header proof unobtained
- `manage.py check --deploy` blocked by Vault-only `SECRET_KEY` (correct fail-closed). Live HSTS/X-Frame-Options/NOSNIFF header curl not possible this turn (operator: chat must stay up; no Docker restart / runtime config change).
- **Disposition:** run against a Vault-backed environment; ticket until then. Do not stub a fake SECRET_KEY to force the check.

### P3 — docs / skill text

#### P3-1 · Skill wording vs peer SSL policy and repo layout — FIXED (1.1.0)
- **Was:** skill required `SECURE_SSL_REDIRECT` "on in prod" flat; "Role" said hardening "on Brain and SFM (both apps)" inside `somaAgent01`.
- **Now:** `.mimocode/agent/soma-prod-hardening.md` —
  - A1 row carries the proxy-TLS exception with peer `file:line` citations (`django_core.py:199-201` / `:153-155`);
  - Role scoped to this repo + sibling peer audit;
  - Live-code anchors table names `admin/core/authz.py`, `services/gateway/settings.py`, `admin/common/middleware.py`, `services/common/rate_limiter.py`, `web_read._is_public_http_url`;
  - Data-path hardening adds the authz one-path rule (fail-closed, no wildcards, never a second permission table).
- **Not weakened:** HSTS, cookies, NOSNIFF, XFO requirements unchanged; the SSL exception is documentation of live peer code, not a new bypass.

---

## 4. Invariant map

| Invariant | State | Anchor |
|---|---|---|
| AuthZ one catalog, fail-closed, no wildcards | Holds | `admin/core/authz.py:15-23,206,439-448` |
| Security block (cookies, XFO, NOSNIFF, CSP) | Present on gateway + peers | `services/gateway/settings.py:55-61`, `admin/common/middleware.py:270-289`, peer `django_core.py` blocks |
| Security block (SSL redirect, HSTS floor, CSRF httponly, CONN_HEALTH_CHECKS) | **Broken / absent** on gateway | P1-1..P1-4 (P1-1 skill-side closed) |
| Bounded inputs (`top_k`/`limit`/`offset`) | Partial — memory/tools/agents capped, search/notifications not | P1-5 |
| Pagination | Partial — chat/users/voice yes; tools/notifications no | P2-5 |
| SSRF | Real guard on `web_read`; host-not-model-controlled on `web_search`; `api_sso`/integrations open | P1-6 |
| `update_fields` on hot rows | Partial — chat/bridge/job/llm-fk good; llm/user/outbox full-row | P2-6 |
| Shared rate limit | Built (Redis), enforced on login only | P0-1 |
| DEBUG ⊥ log level | Holds at root; admin loggers hardcode DEBUG | A11 / P2-3 |
| Secrets Vault-only, fail-closed | Holds | `settings.py:35-41` |
| T-1 MemoryGateway only | Holds | `memory_gateway.py:13` |

---

## 5. Skill-vs-code alignment applied this turn

| Skill text | Change | Why |
|---|---|---|
| `description` frontmatter | Names authz catalog, middleware, rate limits, SSRF + sibling peer scope | Match live surfaces |
| New "Live code anchors" table | 6 paths with verify-first rule | Docs = truth; no paraphrase |
| Role | "this repo + audit peer blocks in sibling checkouts" | Brain/SFM are not inside `somaAgent01` |
| Django block A1 | Proxy-TLS exception + HSTS-kept, peer `file:line` | Matches `django_core.py:199-201` / `:153-155` without weakening HSTS |
| Data-path hardening | AuthZ one-path rule + shared-limiter path | Matches `admin/core/authz.py` law and `services/common/rate_limiter.py` |

No production Python, settings, or runtime config was modified.

---

## 6. What was NOT done (honest scope)

- No production code, settings, or model edits (operator: docs/skill-text only this turn).
- No live `curl` header proof, no `check --deploy` findings list — Vault-gated; Docker left running (chat stays up).
- No SFM/Brain code changes; peer settings were read only for alignment.
- No rate-limit wiring, no `CONN_HEALTH_CHECKS`, no HSTS default — those are the next **code** turn (§7).

---

## 7. Priority order for the next code turn

1. **P0-1** rate limits on chat/search/tools (shared Redis limiter, real 429 evidence).
2. **P1-4** `CONN_HEALTH_CHECKS=True` + **P1-2** `CSRF_COOKIE_HTTPONLY` + **P1-3** HSTS schema default (small, high value, same file).
3. **P1-5** server-side `min()` ceilings on `limit`/`top_k`.
4. **P1-6** shared SSRF egress guard on `api_sso` / integrations (and delete the phantom `http_egress.py` claim or implement the file).
5. **P2-*** log-level bind, pagination, `update_fields` sites, deploy-check under Vault.

---

## 8. Test / verification commands run

```text
rg -n "SECURE_SSL_REDIRECT|SESSION_COOKIE|CSRF_COOKIE|SECURE_HSTS|X_FRAME_OPTIONS|SECURE_CONTENT_TYPE_NOSNIFF|CONN_MAX_AGE|CONN_HEALTH_CHECKS" --glob '*.py'
rg -n "check_rate_limit|@rate_limit" --glob '*.py'
rg -n "top_k|limit|offset|update_fields|\.save\(" --glob '*.py'
rg -n "httpx|urlopen|SSRF|is_public|allowlist|private_range" --glob '*.py'
rg -n "from admin.core.authz import|permissions_for_|ROLE_PERMISSIONS" --glob '*.py'
sed -l anchors: services/gateway/settings.py · admin/core/authz.py · admin/common/middleware.py · services/common/rate_limiter.py · admin/common/rate_limit.py · web_read.py · web_search.py · api_sso.py · integrations.py · peer django_core.py
```

A2A: claim appended `docs/plans/a2a/CLAIMS.md` before edits. LEDGER row in the commit turn.

---

*I hardened the real path, and did not weaken a gate to pass.*
