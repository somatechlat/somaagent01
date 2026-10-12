# SOMA-ARCH-SEC-TOKEN-001 — TRIAD Token/Secret Trust Boundary

## Document Control

| Field | Value |
|---|---|
| Document Title | TRIAD Token/Secret Trust Boundary — Architectural Decision Record |
| Document Identifier | SOMA-ARCH-SEC-TOKEN-001 |
| Version | 1.0.0 |
| Date | 2026-10-12 |
| Status | **Accepted — Operator LAW 2026-10-12** |
| Author | security-reviewer (somaAgent01) |
| Approver | Operator |
| Classification | Internal |
| Applies to | `somaAgent01`, `somabrain`, `somafractalmemory` |
| **Authority** | **SOLE normative authority for the TRIAD token/secret trust boundary, agent↔brain authentication, and degradation security.** |
| Subordinates | `SOMA-STD-SECURITY-001` (operational pattern — upgrade to v1.1.0 binds to this ADR), `SOMA-STD-BOOTSTRAP-001` (lifecycle/threat model), `SOMA-STD-CONFIG-001` R-SEC-*, `SOMA-STD-TOKEN-001` (token *format* only). Where any of these conflict with this ADR on trust boundary / token custody / degradation security, **this ADR wins**. |
| Supersedes | wipe-and-pray recovery (volume wipe + `VAULT_TOKEN` in compose env); shared T0; root-in-T0; `/run/secrets/*` password files; `SOMABRAIN_VAULT_*` / `SOMA_VAULT_*` name forks; dual T0 token path |
| Governing law | VIBE 164 (Vault-only), VIBE 91 (fail-closed), R-15 (honest MemoryAck), Rule 164 (never unauthenticated brain calls), Operator LAW 2026-10-12 |
| Next Review | 2027-01-12 |

### Why an ADR and not another Standard

`SOMA-STD-SECURITY-001` v1.0.0 already prescribed the right *pattern* (Cluster Ceremonial Seeder, per-consumer T0, Channel ENV) and the bootstrap still broke: reused T0 volumes minted against a previous Vault generation 403'd a fresh cluster, recovery spread root through compose ENV, and degradation returned fake empty success. Those are **missing architectural decisions** — generation binding, custodian lifecycle, degradation security — not missing pattern text. This ADR makes those decisions. The Standard operationalizes them. **One decision authority (this ADR). One pattern authority (SECURITY-001 v1.1.0). No third voice.**

---

## 1. Context

### 1.1 The broken trust boundary (evidence)

| Defect | Evidence | Consequence |
|---|---|---|
| T0 tokens outlive their Vault generation | `bootstrap_exec.py:272-274` skips mint when `t0_read(account)` is non-empty; `vault_scoped_tokens.py` same skip-if-exists. T0 is a named volume (`docker-compose.yml` `t0_ram`) that survives `vault volume rm` of *Vault data only*. | Fresh `sys/init` ⇒ new token namespace. Stale T0 token ⇒ 403 on `lookup-self` / KV read ⇒ operators "fix" by exporting `VAULT_TOKEN` into compose. |
| Root still readable from T0 by sibling tools | `init_vault.py:65-69` `_load_vault_token()` reads `T0_DIR/vault_root_token`; `vault_unseal.py:170-175` `load_material(ROOT_ACCOUNT)` falls back to T0. SECURITY-001 §1.4 forbids this; code still does it. | Root in a shared RAM volume = any container UID that can read it rewrites the trust boundary. |
| Dual token path | `vault_inject.py:38-46` accepts `VAULT_TOKEN` **or** `VAULT_TOKEN_FILE`. Compose legacy profile still has `vault_unseal` + `ceremony` + `vault_scoped_tokens` + `init_vault` as separate long-lived-ish services. | Two bootstrap authorities (F-20 race), two token sources, no single generation stamp. |
| Fake empty success on outage | `services/common/chat_service.py:107-108` `except MemoryRecallUnavailable: return []`; `admin/agents/services/somabrain_integration.py:134-139` returns `[]` on **both** `MemoryRecallUnavailable` and bare `Exception`. | Contract violation of `memory_contract.py:68-71` ("never report an outage as an empty recall"). Chat proceeds as if memory is empty. |
| C-1 SSRF | `services/tool_executor/tools.py:233-271` `HttpFetchTool` accepts any `http*` URL and `httpx.get`s it. No host allowlist, no private/link-local/metadata refuse, no redirect cap. Contrast the correct pattern already in-tree: `assistant_tools/web_read.py:27-44`. | Agent tool = SSRF pivot into Vault (:8200), Postgres, cloud metadata. |
| C-2 IDOR | `admin/filesv2/api.py` `get_file:225-247`, `upload_local:250-287`, `delete_file:290-305`, `get_download_url:308-345` all do `File.objects.get(id=file_id)` with **no tenant/user filter**. `list_files:91-93` trusts client-supplied `tenant_id`. `create_upload_url:122-176` trusts client-supplied `tenant_id`/`user_id`. | Any authenticated principal reads/overwrites/deletes any tenant's files. |

### 1.2 What "perfect" means (Operator outcome)

1. Agent ↔ brain is enterprise: fail-closed URL, fail-closed Bearer, fail-closed tenant, honest acks, durable-before-hop, no invented outcomes.
2. Degradation is automatic and honest both directions: brain down ⇒ typed unavailable + queue; brain up ⇒ probe, drain, restore. Never fake success. Never wipe volumes to recover.

---

## 2. Decision — the trust boundary

### 2.1 Identity classes (who holds what)

There are exactly **five** material classes. No sixth class may be invented.

| # | Class | What it is | Who may hold it | Custodian | Lifetime | Rotation / revoke |
|---|---|---|---|---|---|---|
| **K0** | Unseal key / shamir share | Unlocks Vault seal | Operator / KMS | OS keychain `soma-vault-t0` (local) · 3-of-5 (staging) · Cloud KMS auto-unseal (prod) | Until `vault operator rekey` | Annual / operator departure. **Never** a file, never a T0, never an app. |
| **K1** | Root token | `sys/*`, policy install, mint | **Ceremonial Seeder process RAM only** | None — RAM of `bootstrap_exec.py` for the length of one ceremony | Ceremony duration; then **revoke** (prod) / drop (local) | `generate-root` break-glass only, dual-control, time-boxed 15 min, alert-on-use. |
| **K2** | Scoped service token (Vault) | `auth/token/*` TTL lease, policy-bound (`agent-runtime` / `brain-runtime` / `sfm-runtime`) | One consumer process | **Per-consumer private T0 tmpfs** `/run/t0/<consumer>_runtime_token` 0700/0600 | `VAULT_TOKEN_TTL_HOURS` (required, no default), renewable `renew-self` | Re-mint by ceremony on F-10 expiry. **Stop, never widen.** |
| **K3** | Application secret (KV v2) | `somabrain_memory_http_token`, `django_secret_key`, `postgres_password`, pepper, provider keys | Vault (system of record) + the consumer process that just read it | Vault KV v2 `secret/…`; delivered by Channel (§2.4) | Until rotated | KV merge-write + read-back; consumers re-read via Channel API. Provider keys: revoke at provider first. |
| **K4** | Assertion headers | `X-Namespace`, `X-Tenant-ID` | Agent process | Not a secret — a **claim** bound to K3 | Per request | Must equal the namespace/tenant the K3 credential is bound to; brain rejects mismatch. |

**Decisions D1–D12 (the bullets):**

- **D1 — Vault is the only system of record.** No plaintext secret on any disk in any seat. Custodians outside Vault are K0/K1 only, and only in the named custodians above.
- **D2 — Cluster generation binding (fixes C-3 class).** On `sys/init` the seeder writes `secret/agent/credentials/vault_cluster_id = <uuid4>` and stamps the same id into every T0 sidecar file `<account>.cluster_id`. A consumer (and the seeder) **must** compare: T0 token usable only if `token.cluster_id == KV vault_cluster_id`. Mismatch ⇒ treat T0 as **empty**, re-mint. This makes a reused T0 volume after Vault re-init a **non-event**, not a 403 mystery. Never "wipe volumes to fix bootstrap".
- **D3 — Root is ceremony-RAM only.** Delete every `t0_read(ROOT_ACCOUNT)` / `load_material(ROOT_ACCOUNT)` fallback (`bootstrap_exec.py` already correct; **`init_vault.py:65-69`, `vault_unseal.py:170-175` must be purged**). Root never enters any consumer T0. `bootstrap_exec.py` continues to `env.pop("VAULT_TOKEN")` before `execve` (`:377`).
- **D4 — Per-consumer T0, tmpfs, 0700/0600.** One file pair per consumer (`<account>` + `<account>.cluster_id`). No shared `t0_ram` named volume. Compose shape: `tmpfs: /run/t0:mode=0700,uid=<svc-uid>,size=1m`. Swap must be off (F-19).
- **D5 — One token name, whole TRIAD.** `VAULT_TOKEN_FILE` (path) + `VAULT_ADDR` + `VAULT_UNSEAL_KEY` (one-shot) + `VAULT_TOKEN` (one-shot ceremony only). **Deleted forever:** `SOMABRAIN_VAULT_*`, `SOMA_VAULT_*`, `SECRETS_DIR`, `*_PASSWORD_FILE`, `SOMA_T0_SECRETS_DIR`, `/run/secrets/*`.
- **D6 — Channel unification (the one delivery law).**
  - **Third-party PID1** (postgres, keycloak, minio): **Channel ENV** via `vault_inject.py` (RAM → `execve` mapped env). Never compose `environment:` secret, never `*_FILE`.
  - **First-party long-running apps** (agent, brain, SFM): **Channel T0 token file** (K2) + Channel API for K3 re-read. Target state: Channel FD (inherited memfd/pipe, one read + close) — implement when the injector is unified; until then T0 file is the blessed interim and is what the agent seat already runs.
  - **Banned:** host secret files, compose secret env, image-layer secrets, argv secrets, log values.
- **D7 — Agent→brain auth is K3 Bearer, fail-closed.** `SOMABRAIN_URL` (settings chain, no localhost fallback) + `Authorization: Bearer somabrain_memory_http_token` (Vault `secret/agent/credentials/somabrain_memory_http_token`) + `X-Namespace` = configured namespace + `X-Tenant-ID` = `SA01_DEFAULT_TENANT_ID`. Missing token ⇒ `MemoryConfigurationError` / refuse. Never unauthenticated (Rule 164). Never invent a route (`/api/remember` dialect is dead).
- **D8 — Honest acks and honest absence (R-15 / R-05).** `MemoryAck.ok` only on `durability ∈ {persisted_ltm, durable_outbox}`. A recall outage raises `MemoryRecallUnavailable`; **`[]` means "recall ran and found nothing"**. Returning `[]` on outage is a contract violation and is banned at every call site (chat_service, somabrain_integration, orchestrator lanes).
- **D9 — Failure taxonomy mapping (no invented outcomes).**

  | Wire signal | Agent maps to | Counts toward breaker | Safe user-visible |
  |---|---|---|---|
  | timeout / connect error / DNS | `MemoryRecallUnavailable` (transport) | yes | "Memory degraded — queued" |
  | 502/503/504 | `MemoryRecallUnavailable` (brain down) | yes | same |
  | 401/403 | `MemoryConfigurationError` (auth/tenant) — **not** "memory empty" | no (config, not outage) | refuse turn's memory lane; alert operator |
  | 400/422 | `MemoryWriteError` / validation — surface the brain's `error` field | no | fail the operation, no queue-retry of invalid payloads |
  | 2xx with `ok=false` | write not durable → durable-accept only; outbox stays pending | partial | "Queued until the brain confirms" |

  The agent never fabricates a status the brain did not send.

- **D10 — Degradation security contract (§3).** Writes that cannot reach the brain are **durable-accepted into `memory.wal` outbox** and replayed by `memory-replicator` only (T-6, one authority). Reads degrade to sentinels + banner. Recovery is breaker `HALF_OPEN` probe with the *same* fail-closed auth. **Never** unauthenticated probe. **Never** widen policy on outage.
- **D11 — C-1 / C-2 are in-bound of this trust boundary** (§5). An SSRF tool is a secret-exfiltration channel; an IDOR file API is a tenant-boundary breach. Both are token/secret treatment failures in disguise.
- **D12 — Dev is recoverable without spreading root.** Bootstrap is **idempotent + generation-stamped** (D2): re-ceremony after a volume wipe is `sys/init` → seed → mint → drop root. Operator recovery paths that put `VAULT_TOKEN` in compose `environment:` or long-lived ENV are **banned**. Volumes may be wiped; trust boundary may not.

### 2.2 Token/secret matrix (seat × artifact × custodian × TTL × rotate/revoke)

| Seat | Artifact (class) | Custodian | TTL | Rotate | Revoke | Notes |
|---|---|---|---|---|---|---|
| Operator | Unseal key (K0) | keychain `soma-vault-t0` / KMS | n/a | `vault operator rekey` | n/a | 1-of-1 local; 3-of-5 staging; KMS prod |
| Ceremony | Root (K1) | **process RAM only** | ceremony | mint-and-revoke | `revoke-self` end of ceremony | Never T0, never file, never app env |
| agent (`somaagent_standalone`) | `agent_runtime_token` (K2) | `/run/t0` tmpfs 0700/0600 + `.cluster_id` | `VAULT_TOKEN_TTL_HOURS` | re-mint on expiry / generation change | F-10 stop | `VAULT_TOKEN_FILE` path only |
| brain | `brain_runtime_token` (K2) | brain's own `/run/t0` (never agent T0) | same | same | same | policy `brain-runtime` |
| SFM | `sfm_runtime_token` (K2) | SFM's own `/run/t0` | same | same | same | policy `sfm-runtime` |
| postgres PID1 | `postgres_password` (K3) | Channel ENV at execve | n/a (static first-boot) | `ALTER ROLE` from Vault value | n/a | SCRAM verifier in `pg_authid` is the designed exception |
| agent→brain | `somabrain_memory_http_token` (K3) | Vault KV + agent process memory | until rotate | ceremony merge-write + read-back; brain re-reads | delete KV version | **one authority**, brain never regenerates |
| all | `identity_password_pepper` (K3) | Vault KV | until rotate | explicit dual-control | n/a | rotation invalidates every hash — never automatic |
| provider keys | `*_api_key` (K3) | Vault KV `secret/agent/api_keys` | provider terms | provider revoke → delete KV → re-seed via one-shot `SOMA_SECRET_<KEY>` | provider | |

### 2.3 Cluster generation stamp (normative shape)

```
sys/init  →  root, unseal in seeder RAM
         →  PUT secret/agent/credentials { vault_cluster_id: uuid4() }   # merge-write
         →  for each consumer:  mint K2  →  t0_write(account, token)
                                              t0_write(account + ".cluster_id", cluster_id)
consumer boot:
         cid_file  = t0_read("<account>.cluster_id")
         cid_vault = kv2_read(secret/agent/credentials, "vault_cluster_id")   # via K2
         if cid_file != cid_vault:  treat T0 as EMPTY → refuse start (F-2) → re-ceremony
         else:                      renew-self; proceed
```

A stale T0 after Vault re-init therefore **fails closed at the consumer**, with a message that names generation mismatch — not a generic 403, and not an invitation to export root.

### 2.4 Delivery channels (unification table)

| Consumer | Today | Target (this ADR) | Peer action |
|---|---|---|---|
| agent app | Channel T0 file (`VAULT_TOKEN_FILE`) ✅ | keep; add `.cluster_id` | — |
| postgres (agent) | `entrypoint_pg_vault.py` reads `VAULT_TOKEN_FILE` then KV → Channel ENV to stock entrypoint | keep | — |
| brain app | `VAULT_TOKEN_FILE=/run/vault/token` + `/run/secrets/*` volume renders ❌ | Channel T0 file 0700/0600 + Channel ENV for third-party; **delete** `vault_pg_secrets` / `vault_minio_secrets` / `POSTGRES_PASSWORD_FILE` / `MINIO_*_FILE` | somabrain ACK + impl |
| SFM app | `VAULT_TOKEN_FILE=/run/t0/sfm_runtime_token` ✅ shape, but `POSTGRES_PASSWORD_FILE=/run/t0/postgres_password` ❌ and `SOMA_VAULT_*` forks ❌ | same as brain: Channel ENV for postgres; delete name forks | SFM ACK + impl |
| keycloak / minio | mixed / file-based | Channel ENV via `vault_inject` | both peers |

---

## 3. Degradation security contract (detect → degrade → queue → recover)

```
        DETECT                         DEGRADE                      QUEUE                      RECOVER
─────────────────────────────   ──────────────────────────   ──────────────────────────   ─────────────────────────
CB on memory_gateway:           Read:                        Write:                       CB state OPEN
  failures ≥ CB_FAILURE_          MemoryRecallUnavailable      durable-accept row in        after CB_RESET_TIMEOUT_S
  THRESHOLD (default 5)           raised — NEVER []            OutboxMessage memory.wal     → HALF_OPEN
  within window                 Chat continues with            (status=pending)             one probe request with
                                  sentinel "[Long-term       memory-replicator is THE       FULL fail-closed auth
adapter maps wire taxonomy        memory unavailable this       one replay authority         (D7). Success ⇒ CLOSED
  (D9) → typed errors             turn]"                       (no second drainer)          + outbox drain + UI
                                UI banner "Memory degraded                                   /memory/status +
                                  — messages queue until                                   /core/brain-connector
                                  the brain recovers"                                      restore. Probe fail ⇒
                                MemoryAck.ok=false only                                    OPEN again.
                                  (never ok=true on outage)
```

**Safe when brain is down:** chat turn completes; writes durable-accepted; outbox pending; user sees honest banner + sentinel.

**Must refuse when brain is down:** fake `[]` recall; `MemoryAck.ok=true`; unauthenticated calls; policy widening; reading a backup token; root in any service; SFM client from the agent (T-1).

**Recovery auth:** the HALF_OPEN probe uses the same Bearer + namespace + tenant as steady state. Recovery is a *health* event, not a *trust* event — no credential is loosened to recover.

**Gap to close (implementation wave):** replace the two `return []` sites with typed raise / honest result (§5). Live behavioral test of auto-degrade/auto-recover is required — source-shape tests are not proof.

---

## 4. Sequence flows (specification)

### 4.1 Boot (first cluster)

```
Operator → vault (sealed) → bootstrap_exec.py (root in RAM)
  → sys/init → write vault_cluster_id → install policies → seed K3 (merge + read-back)
  → mint K2 per consumer into per-consumer T0 + .cluster_id
  → drop/revoke root → execve target (VAULT_TOKEN stripped)
Consumer → read T0 + .cluster_id → compare to KV → renew-self → serve
```

### 4.2 Happy chat

```
browser → WS /ws/v2/chat → ChatConsumer → V3ChatOrchestrator
  → FanoutMemoryGateway → SomaBrainAdapter
      headers: Bearer K3, X-Namespace, X-Tenant-ID
      POST {SOMABRAIN_URL}/memory/recall | remember | forget | remember/batch
  ← 2xx; MemoryAck.ok ⇔ durability ∈ {persisted_ltm, durable_outbox}
  → chat renders; outbox empty
```

### 4.3 Brain down

```
request → adapter → timeout/5xx → MemoryRecallUnavailable
  → CB failure++ → OPEN at threshold
  → chat: sentinel + banner (no fake [])
  → write: OutboxMessage memory.wal pending (durable-before-hop)
  → MemoryAck.ok=false
```

### 4.4 Brain up

```
CB timeout → HALF_OPEN → probe (full auth) → 2xx
  → CLOSED → memory-replicator drains outbox in order
  → UI /memory/status + brain-connector restore
  → next turn: real recall (not [])
```

### 4.5 Token rotate (K3 `somabrain_memory_http_token`)

```
ceremony (root-in-RAM one-shot):
  kv2_write_merge(secret/agent/credentials, somabrain_memory_http_token, new)
  read-back assert (new present AND siblings survive)
  → agent re-reads via Channel API (cache TTL ≤ VAULT_CACHE_TTL_SECONDS)
  → brain re-reads on next request / restart
  → old KV version destroyed deliberately
No downtime window where calls are unauthenticated. If a 401 occurs mid-swap it is
mapped as MemoryConfigurationError (D9), not "memory empty".
```

### 4.6 Vault re-seal / re-init

```
Vault sealed → apps refuse to start (F-2) / fail closed on call
unseal (K0) → services resume with existing K2 if still valid (renew-self)
vault data LOST → sys/init new generation → new vault_cluster_id
  → all T0 .cluster_id mismatch → consumers refuse → re-ceremony mints new K2
  → rotate all K3 (old ciphertext gone)
NEVER: export root to "just get it running".
```

---

## 5. C-1 / C-2 / C-3 — root cause + fix plan

### C-1 SSRF (`http_fetch`) — CRITICAL

**Root cause.** `services/tool_executor/tools.py:244-252` validates only `url.startswith("http")`, then `httpx.AsyncClient.get(url)` with no host policy, no IP-class refuse, no redirect limit, no size cap. The tool is agent-reachable, so any prompt-influenced URL becomes a request from inside the stack net — a direct path to `http://somaagent_vault:8200`, Postgres, Redis, or `169.254.169.254`. The repo already contains the correct pattern: `services/tool_executor/assistant_tools/web_read.py:27-44` (`_is_public_http_url` refuses localhost, `.local`, `.internal`, `.lan`, private/link-local/reserved IPs) plus body caps (`MAX_BYTES`, `MAX_CHARS`).

**Fix.** (1) Extract `_is_public_http_url` (and resolve-then-check: DNS answer must be global before connect, and re-check after redirects — `follow_redirects=False` + manual hop cap ≤3, revalidating each hop) into a single `services/common/http_egress.py` used by **both** `http_fetch` and `web_read`. (2) `http_fetch` must set `needs_egress=True` / approval gate like `web_read`, cap response bytes, and strip `Set-Cookie` / auth headers from the returned `headers` dict (today it returns **all** response headers — an additional leak). (3) Deny-by-default scheme: http/https only. (4) Unit tests: localhost, RFC1918, link-local, metadata IP, redirect-to-private, DNS-rebind-shaped names, `.internal`.

### C-2 filesv2 IDOR — CRITICAL

**Root cause.** Object-level authorization is absent. `admin/filesv2/api.py:232` `File.objects.get(id=file_id, deleted_at__isnull=True)` (and the same shape at `:265`, `:297`, `:317`) never constrains `tenant_id`/`user_id` to the authenticated principal. `list_files:82-93` takes `tenant_id` from the **query string** (client-controlled). `create_upload_url:122-176` takes `tenant_id` and `user_id` from the **body** and writes them into the row — a caller can create files under another tenant. `authorize_sync(..., resource="files")` is a coarse capability check ("can use files"), not an ownership check.

**Fix.** (1) Derive `tenant_id`/`user_id` from the auth principal (`request.user_claims` / session) — **never** from body or query. (2) Every lookup becomes `File.objects.get(id=file_id, tenant_id=principal.tenant_id, deleted_at__isnull=True)`; cross-tenant ⇒ 404 (not 403, to avoid existence oracle). (3) `list_files` drops the `tenant_id` parameter. (4) `upload_local` asserts the row's `user_id == principal.user_id` (or tenant-admin) before `default_storage.save`. (5) `get_download_url` same ownership filter. (6) Tests: cross-tenant read/write/delete/download all 404; same-tenant non-owner policy explicitly asserted.

### C-3 Dual T0 token path / generation mismatch — CRITICAL

**Root cause.** Three cooperating defects: (a) **no generation stamp** — a token minted against cluster A is indistinguishable from one minted against cluster B (`bootstrap_exec.py:272-274` reuses any non-empty T0 token); (b) **root reachable from T0** in sibling tools (`init_vault.py:65-69`, `vault_unseal.py:170-175`) contradicting SECURITY-001 §1.4; (c) **dual bootstrap authorities** — legacy compose profile (`vault_unseal` + `ceremony` + `vault_scoped_tokens` + `init_vault`) coexists with `bootstrap_exec.py`, and `vault_inject.py:38-46` accepts `VAULT_TOKEN` **or** `VAULT_TOKEN_FILE`, so a "recovery" that exports root is silently accepted. Root cause *class*: T0 lifetime is decoupled from Vault lifetime.

**Fix.** (1) Implement D2 generation stamp (`.cluster_id` sidecar + KV `vault_cluster_id`) and make both seeder and consumer refuse on mismatch. (2) Delete root fallbacks in `init_vault.py` / `vault_unseal.py` (D3). (3) Collapse bootstrap to **one** authority: `bootstrap_exec.py` remains the only seeder path for the agent stack; legacy `vault_unseal`/`init_vault`/`vault_scoped_tokens` become **library functions** called by it, or one-shot CLI used only by ceremony — never compose long-running services. (4) `vault_inject.py` accepts **only** `VAULT_TOKEN_FILE` at runtime (`VAULT_TOKEN` one-shot only for the seeder itself, stripped before exec). (5) Compose: per-consumer `tmpfs`, no `t0_ram` named volume (D4). (6) Recovery runbook: "re-ceremony" command that is idempotent under D2 — **delete the wipe-and-pray playbook**.

---

## 6. Implementation waves (ordered, TDD anchors)

| Wave | Scope | Files (agent seat) | TDD anchor (RED first) |
|---|---|---|---|
| **W0** | Honesty gap (D8) — small, unblocks degradation proof | `services/common/chat_service.py:107-108`, `admin/agents/services/somabrain_integration.py:134-139` | `tests/unit/test_chat_service_memory_honesty.py` (claimed) — assert raise/honest result, **not** `[]` |
| **W1** | C-2 IDOR | `admin/filesv2/api.py` (+ auth principal helper) | `tests/unit/test_filesv2_idor.py` — cross-tenant 404 matrix |
| **W2** | C-1 SSRF | `services/common/http_egress.py` (new), `services/tool_executor/tools.py` HttpFetchTool, `assistant_tools/web_read.py` (refactor to shared) | `tests/unit/test_http_egress_ssrf.py` — private/metadata/redirect cases |
| **W3** | C-3 generation stamp + root purge + inject single-path | `infra/standalone/bootstrap_exec.py`, `init_vault.py`, `vault_unseal.py`, `vault_scoped_tokens.py`, `vault_inject.py`, `docker-compose.yml` (tmpfs per consumer), `services/common/vault_secrets.py` | `tests/unit/test_t0_cluster_id.py` — stale T0 ⇒ refuse; matching ⇒ pass |
| **W4** | Degradation live proof | `tests/e2e/test_degradation_auto.py` (claimed) | kill brain container ⇒ banner + pending outbox; start ⇒ drain + CLOSED |
| **W5** | Peer seats (A2A) | somabrain compose/`vault_client`; SFM compose/`vault_client` | peer-owned tests; agent seat holds the contract |
| **W6** | SECURITY-001 v1.1.0 + BOOTSTRAP cross-links, verification gates | `docs/standards/SOMA-STD-SECURITY-001.md` | CI greps from SECURITY-001 §5 must pass |

Claim discipline: W0 already claimed (`chat_service.py` by MiMoCode-somaAgent01 CONDITION-001). W1–W3 under `security-reviewer` claim (docs/standards + vault seats) extended by this ADR's claim row. No shims. No mocks. Live services only (T-8).

---

## 7. Residual risks

| # | Risk | Sev | Mitigation |
|---|---|---|---|
| R-1 | Peer seats still shipping `/run/secrets/*` + name-forks until ACK | HIGH | A2A HOLD; this ADR is the contract; CI greps |
| R-2 | DNS rebinding against `_is_public_http_url` if only host-string checked | HIGH | W2 must resolve-then-check + re-check each redirect hop |
| R-3 | Same-UID read of K2 in T0 tmpfs | HIGH | 0700/0600, short TTL, per-consumer T0, F-10 stop |
| R-4 | Channel ENV visible in `/proc/<pid>/environ` of third-party PID1 | MED | container UID isolation, no shared PID ns, core dumps off |
| R-5 | Pepper loss ⇒ password verify unavailable | MED | re-provision via `bootstrap_identity` (stdin); never mint on read path |
| R-6 | KV merge race if two seeders run | MED | single ceremonial seeder invariant (F-20); generation stamp makes double-init loud |
| R-7 | AppRole still deferred | LOW | named production target when KMS/K8s auth exists; not required for this generation |

---

## 8. Verification gates

```bash
# D3/D5: no root in T0 readers, no name forks
grep -RInE 'ROOT_ACCOUNT|vault_root_token' infra/standalone/*.py   # RAM-only comments
grep -RInE 'SOMABRAIN_VAULT_TOKEN|SOMA_VAULT_TOKEN' .               # empty
# D6: no secret files / *_FILE passwords
find . -name 'vault-token' -o -path '*/secrets/*' -o -name '*_PASSWORD_FILE*'
# D4: no world-readable T0
grep -RInE '0o777|0o644|chmod 777|mode=0?777' infra/
# D8: no fake-empty on outage
grep -RInE 'except MemoryRecallUnavailable:\s*$' -A2 services/ admin/ | grep -E 'return \[\]'   # empty
# D2: generation stamp present
grep -RIn 'vault_cluster_id' infra/standalone/ services/common/
# C-1: shared egress gate
grep -RIn '_is_public_http_url\|http_egress' services/tool_executor/
# C-2: object-level auth
grep -RIn 'File.objects.get' admin/filesv2/   # every site filters tenant_id
```

---

## 9. A2A / ACK ledger (binding)

This ADR is issued to seats `soma-vault-authority`, `soma-prod-hardening`, `MiMoCode-somabrain`, SFM seat via `docs/plans/a2a/{CLAIMS,OUTBOX,INBOX,LEDGER}.md`. Peer seats implement the same pattern; **no seat invents a local variant**. Merge of peer secret-path changes requires ACK against this ADR.

---

*security-reviewer owns this ADR. Operator is final authority (Covenant Art 5).*

*End of SOMA-ARCH-SEC-TOKEN-001 v1.0.0*
