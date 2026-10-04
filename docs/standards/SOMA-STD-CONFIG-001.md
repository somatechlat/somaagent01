# SOMA-STD-CONFIG-001 — Configuration, Endpoints and Secret Resolution

## Document Control

| Field | Value |
|---|---|
| Document Title | Configuration, Endpoints and Secret Resolution |
| Document Identifier | SOMA-STD-CONFIG-001 |
| Version | 1.0.0 |
| Date | 2026-10-03 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements · ISO/IEC 27001:2022 A.8.9 configuration management |
| Next Review | 2026-12-28 |
| Related | `SOMA-STD-CODING-001.md`, `SOMA-SETTINGS-MODEL-001.md`, `SOMA-01-DOCS-001.md`, `SOMA-01-QMS-001.md`, `SOMA-UI-SKINS-001.md` |
| Source of truth | This document for the rules; `admin/core/helpers/capsule_settings.py`, `service_urls.py`, `vendor_api_bases.py`; `somabrain/somabrain/settings/resolve.py`, `constants.py`; `somafractalmemory/somafractalmemory/settings/model.py` for the live pattern |
| Audience | All engineering contributors, operators, and any agent acting on somaAgent01 / somabrain / somafractalmemory |
| Scope | Cross-repo rules for where a configuration value may live, how it resolves, how endpoints and secrets are read, and what is forbidden. **This document is a standard. It does not change code.** |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-03 | SomaTech Engineering | Initial issue. Three value classes, the resolution chain, value rules, scale rules, the `SOMABRAIN_URL` worked example across the triad, anti-patterns with their real incidents, and the per-repo appendix. |

## Normative References

| ID | Reference | Role |
|---|---|---|
| N-1 | `docs/standards/SOMA-STD-CODING-001.md` | VIBE law. Rule 91 (zero-fallback), Rule 164 (zero-hardcode / secrets in Vault), check-first-code-second |
| N-2 | `SOMA-SETTINGS-MODEL-001.md` | Settings ownership layers L1–L4, category taxonomy C1–C10, full key inventory |
| N-3 | `SOMA-01-DOCS-001.md` | Document control and traceability procedure |
| N-4 | `SOMA-01-QMS-001.md` | Quality manual; §7 Document Reference Matrix |
| N-5 | `admin/core/helpers/capsule_settings.py` | Live four-step resolver and `KEY_CATEGORY` |
| N-6 | `admin/core/helpers/service_urls.py` | Fail-closed deployment-URL resolver |
| N-7 | `admin/core/helpers/vendor_api_bases.py` | Vendor protocol constants and `effective_base` |
| N-8 | `somabrain/somabrain/settings/resolve.py` | SomaBrain resolver (`require_url`, `require_tenant`, `resolve_tunable`) |
| N-9 | `somafractalmemory/somafractalmemory/settings/model.py` | SFM `TUNABLES` registry and `resolve_setting` / `service_url` |
| N-10 | `services/common/policy_client.py` | Bounded LRU decision cache (the scale pattern) |
| N-11 | ISO/IEC 27001:2022 A.8.9 | Configuration management — baseline, control, inventory |

---

## 1. Purpose and standing order

### 1.1 Purpose

This standard fixes **where a configuration value may live, how it is read, and what is forbidden**. It exists because the same mistakes have already been made in this codebase more than once (§7), each time by a call site that decided a value was "just a default".

It binds all three repositories of the cognitive triad. `SOMA-SETTINGS-MODEL-001` owns the *inventory* (which keys exist, who owns each one, what category it is in). This document owns the *rules* (which class a value is, which chain reads it, what a legal default looks like). Where the two disagree, the rule wins and the inventory is wrong.

### 1.2 The standing order

These are the design criteria. They are quoted here because every rule below is derived from them.

> **the rules · millions of transactions · security · speed · latency · thin**
>
> A per-request external hop is a latency wall. Anything hot must be cached and bounded; the external dependency is the slow path.

What that means for configuration: a value that is read on a hot path **SHALL NOT** trigger a network hop to obtain. It is resolved from a chain that is already in process memory or in a bounded cache (§5). Secrets, topology and behaviour are separated precisely so that the hot path never has to go and ask someone else what a value is.

### 1.3 Scope

| Repository | In scope |
|---|---|
| `somaAgent01` | `config/settings.py`, `services/gateway/settings.py`, `admin/core/helpers/{capsule_settings,settings_model,settings_defaults,service_urls,vendor_api_bases}.py`, `services/common/{policy_client,env_config,vault_secrets,unified_secret_manager}.py`, every worker and adapter that reads a setting |
| `somabrain` | `somabrain/settings/{resolve,constants,infra,django_core,cognitive}.py`, `somabrain/core/security/vault_client.py`, every call site that needs a URL, host, tunable or secret |
| `somafractalmemory` | `somafractalmemory/settings/{model,infra,django_core}.py`, `somafractalmemory/admin/core/security/vault_client.py`, every call site that needs a tunable or a service URL |

Out of scope: third-party library environment variables, test-only fixtures (`TEST_*`), generated artefacts, concrete production values (that is deployment configuration).

### 1.4 Relationship to other documents

| Document | Relationship |
|---|---|
| `SOMA-STD-CODING-001` | Parent law. This standard is the configuration clause of VIBE Rules 91 and 164. |
| `SOMA-SETTINGS-MODEL-001` | Inventory and category taxonomy. **SHALL** reference this standard; this standard **SHALL NOT** restate the inventory. |
| `SOMA-UI-SKINS-001` | Example of the same shape applied to one feature: data is administrable, machinery is written once. |
| `SOMA-01-DOCS-001` | Document control procedure this document follows. |

---

## 2. The three value classes

Every configuration value belongs to **exactly one** of three classes. The class decides where the value may live. A value that does not fit a class is not configuration; it is a literal, and literals in logic are defects.

| Class | What it is | Where it may live | Where it SHALL NOT live |
|---|---|---|---|
| **Secret** | Credential material: API keys, tokens, passwords, private keys, client secrets | **Vault only** — `secret/agent/credentials/*`, `secret/agent/api_keys/*` | Never in ENV as a steady state, never in a file in git, never in the database as a value, never in this document |
| **Topology** | Deployment addressing: hosts, ports, URLs, namespaces, modes | Deployment env / Compose / Helm (L3 in `SOMA-SETTINGS-MODEL-001` §4) | Never a literal in code, never a schema default on a URL |
| **Behaviour** | A knob an administrator can turn: limits, timeouts, toggles, model slots, recall policy, persona | `SettingsModel` + `AgentSetting` (and Capsule/Constitution where the value is agent identity) | Never hardcoded at a call site, never a second lookup path |

### 2.1 Secrets

**R-SEC-01.** A secret **SHALL** be sourced from Vault (`services/common/vault_secrets.py`, `services/common/unified_secret_manager.py`, `somabrain/core/security/vault_client.py`, `somafractalmemory/.../vault_client.py`). Rule 164: a secret is read from Vault and used; it is never copied into `os.environ`, never written to a file, never persisted in the database as a value.

**R-SEC-02.** `AgentSetting.is_secret=True` (`admin/core/models/core.py:724`, `admin/core/helpers/capsule_settings.py:232-246`) marks a row whose *value* is secret material. The row is a pointer/override slot, not a secret store.

**R-SEC-03.** Env **MAY** carry a Vault bootstrap only (`VAULT_ADDR`, `VAULT_TOKEN`, `VAULT_TOKEN_FILE`). Those are topology to reach the secret store, not application secrets. `SOMA-SETTINGS-MODEL-001` §8 R-ENV-02 states the same rule.

**R-SEC-04.** This document and every other document **SHALL NOT** record a secret value.

### 2.2 Topology

**R-TOP-01.** A host, port, URL or addressing namespace **SHALL** come from deployment env/Compose at boot and be read through Django settings or the repo's resolver after boot. After boot, Django settings is the authority (`SOMA-SETTINGS-MODEL-001` R-OWN-02).

**R-TOP-02.** A deployment URL **SHALL NOT** have a code default. `service_urls.require_service_url` raises `ImproperlyConfigured` when no layer configures it (`admin/core/helpers/service_urls.py:74-78`). SomaBrain's `require_url` raises `UnconfiguredServiceError` (`somabrain/somabrain/settings/resolve.py:87-101`). SFM's `service_url` raises when absent or non-absolute (`somafractalmemory/somafractalmemory/settings/model.py:395-418`). All three are the same rule.

**R-TOP-03.** Missing required topology **SHALL** fail closed. There is no `getattr(settings, X, "http://localhost…")` and no silent substitute (`services/common/env_config.py:11` `get_required_env`; `MemoryConfigurationError` in `services/common/memory_contract.py:48-53`).

### 2.3 Behaviour

**R-BEH-01.** A behavioural tunable **SHALL** be declared on the settings model (`SettingsModel` in somaAgent01, `BrainSetting` / Django settings in somabrain, `TUNABLES` in SFM) so an administrator can change it without a code change.

**R-BEH-02.** A behavioural tunable **SHALL** be read through the repo's single resolver (§3). A call site that reads it another way has created a second source of truth.

**R-BEH-03.** Agent behaviour defaults **SHALL** be savable on the Capsule body/persona (`SOMA-SETTINGS-MODEL-001` R-OWN-04, R-CAP-01). Constitution constraints are constraints, not values.

### 2.4 Vendor public API bases are protocol constants

A third-party vendor's published base URL is **not** this product's topology. It is part of that vendor's API protocol. It lives in **one named module per repo**, never at a call site:

| Repo | Module | Contents |
|---|---|---|
| `somaAgent01` | `admin/core/helpers/vendor_api_bases.py` | `OPENAI_API_BASE`, `ANTHROPIC_API_BASE`, `TELEGRAM_API_BASE`, `WHATSAPP_CLOUD_API_BASE`, … (`:31-45`), plus `effective_base()` (`:48-60`) |
| `somabrain` | `somabrain/settings/constants.py` | Scheme tokens only (`HTTP_SCHEME`, `HTTPS_SCHEME`, … `:14-20`). Effective bases are settings, read through `require_url` (`resolve.py:87-101`) |
| `somafractalmemory` | **OPEN-01** — no vendor-bases module exists. SFM calls no vendor cloud today; if it ever does, the module **SHALL** be created under `somafractalmemory/settings/` |

**R-VEN-01.** The protocol constant is the *default of last resort* for the effective base, never the only allowed value. An operator override (model `api_base`, env, AgentSetting) wins so traffic can be pointed at a proxy or a regional endpoint: `effective_base(protocol_constant, override)` (`vendor_api_bases.py:48-60`).

**R-VEN-02.** This product's own service topology **SHALL NOT** be placed in the vendor-bases module. Those are deployment URLs: declared on `SettingsModel` / Django settings, registered in `KEY_CATEGORY`, resolved through `require_service_url` (`vendor_api_bases.py:16-19`).

**R-VEN-03.** Call sites **SHALL NOT** embed a URL string. One module is the only place a reviewer has to look to see every external host.

---

## 3. The resolution chain

### 3.1 The chain, exactly

When a setting is overridable, resolution is highest-wins:

```
Capsule  >  AgentSetting  >  SettingsModel / Django  >  schema default
```

| Step | Layer | What it is | Evidence |
|---|---|---|---|
| 1 | `Capsule.persona_config["settings"][CATEGORY][key]` | Agent identity / body | `capsule_settings.py:179-183` |
| 2 | `AgentSetting` ORM (`agent_id`, `key`) | Runtime override, administrator-managed | `capsule_settings.py:185-194` |
| 3 | Django settings | Infrastructure authority | `capsule_settings.py:196-204` — `getattr(django_settings, key, None)` |
| 4 | Schema default | Only when the key is optional and no authority produced a value | `capsule_settings.py:206` `return default` |

Implemented by `resolve_setting` in `admin/core/helpers/capsule_settings.py:170-206`. The sibling resolvers are the same chain with fewer layers because those repos have fewer:

| Repo | Resolver | Chain |
|---|---|---|
| `somaAgent01` | `capsule_settings.resolve_setting` (`:170-206`); `service_urls.require_service_url` (`:33-78`) | Capsule → AgentSetting → Django → schema default (empty for every deployment URL) |
| `somabrain` | `settings.resolve.resolve_tunable` (`:135-169`); `require_url` / `require_setting` (`:65-101`) | `BrainSetting` (tenant) → Django settings → schema default only when optional |
| `somafractalmemory` | `settings.model.resolve_setting` (`:339-376`); `service_url` (`:395-418`) | Django settings → `TUNABLES` schema default (SFM has no Capsule and no AgentSetting; the chain is two steps) |

**R-RES-01.** Implementations **SHALL** follow the chain above. `admin/core/helpers/settings_defaults.py:100-111` (`_env_or_db`: ENV > DB > default) is a **known deviation** tracked in `SOMA-SETTINGS-MODEL-001` §10 D-07. It **SHALL** be reconciled or explicitly scoped as a migration shim.

**R-RES-02.** There is exactly one resolver per repo for a given value class. A second lookup path is a second source of truth (`SOMA-SETTINGS-MODEL-001` R-OWN-05).

### 3.2 `KEY_CATEGORY` keys are the UPPER Django name

`KEY_CATEGORY` (`capsule_settings.py:45-139`) maps a settings key to its ISO category. The key **SHALL** be the **UPPER Django name** — the same string that `getattr(settings, key)` finds on the Django settings object.

Why: step 3 of the chain is literally `getattr(django_settings, key, None)` (`capsule_settings.py:201`). If the registry key is not the Django attribute name, step 3 silently misses and the resolver falls through to a schema default that no operator set. The name in the registry, the name in env/Compose, the name on `SettingsModel` (as `service_<snake>`), and the name an operator types are the **same name**.

`SettingsModel` stores deployment URLs under snake_case `service_*` fields (`settings_model.py:181-219`, e.g. `service_somabrain_url` at `:184`). Those are the schema view of the same UPPER name; `require_service_url` checks both (`service_urls.py:62-72`).

Exception, stated plainly: `KEY_CATEGORY` also lists a few snake_case `SettingsModel` field names (`chat_model_provider`, `memory_recall_enabled`, …) because those are resolved as model fields, not Django attributes. A key is either a Django UPPER name or a model field name. It is never both and never a third thing.

### 3.3 Fail-closed on a required value

**R-RES-03.** A missing value that is load-bearing **SHALL** raise, not default:

| Helper | Raises | Evidence |
|---|---|---|
| `require_service_url(name)` | `ImproperlyConfigured` | `service_urls.py:74-78` |
| `require_setting(name)` | `ImproperlyConfigured` | `service_urls.py:102-105` |
| `require_url(name)` / `require_setting(name)` (SomaBrain) | `UnconfiguredServiceError` | `resolve.py:48-49`, `:65-74`, `:87-101` |
| `require_tenant` / `require_namespace` | `UnconfiguredServiceError` | `resolve.py:112-132` |
| `service_url(key)` (SFM) | `ImproperlyConfigured` | `model.py:395-418` |
| `resolve_setting(key)` with `REQUIRED` | `ImproperlyConfigured` | `model.py:373-376` |

---

## 4. The rules for a value

These are the rules a value must satisfy. They are the checklist a reviewer applies.

| ID | Rule |
|---|---|
| **R-VAL-01** | **Declared exactly once.** The value's name, type and schema default appear in exactly one declaration site (the `TUNABLES` row, the `SettingsModel` field, the `KEY_CATEGORY` entry). The same number **SHALL NOT** appear as a literal at a call site. |
| **R-VAL-02** | **Administrable.** A behaviour value **SHALL** have CRUD — `AgentSetting` / `BrainSetting` / `TUNABLES` + Django settings — so an operator can change it without a deploy. A value nobody can change is a literal wearing a name. |
| **R-VAL-03** | **Read through one resolver.** Every read goes through `resolve_setting` / `require_service_url` / `resolve_tunable` / `service_url`. `os.environ.get` at a call site, `getattr(settings, X, fallback)`, and a hand-rolled lookup are all forbidden. |
| **R-VAL-04** | **Fail-closed when missing and load-bearing.** See §3.3. A default is legal only when the key is declared optional and the default lives at the declaration site. |
| **R-VAL-05** | **A knob with no reader is deleted, not documented.** If nothing reads the key, it is removed from the registry, from the model, and from the inventory. `somafractalmemory/settings/model.py:16-18` states this as the SFM rule ("a tunable with no reader is a lie"). |
| **R-VAL-06** | **One vocabulary per concept.** One key name, one category, one permission name, one owner. A second name for the same concept is where drift starts (§7 AP-06). |
| **R-VAL-07** | **Category from the taxonomy.** Every key **SHALL** carry a category from `SOMA-SETTINGS-MODEL-001` §6 via `KEY_CATEGORY`. Unknown keys default to `INFRA` in somaAgent01 (`capsule_settings.py:142-145`) and **raise** in SFM (`model.py:313-320`). |

---

## 5. The scale rules

The standing order (§1.2) is not decorative. It decides what is allowed on a hot path.

**R-SCL-01 — Hot values are cached and bounded.** A decision that is consulted per-request **SHALL** sit in a bounded LRU with a TTL, not be fetched per request. The reference implementation is the policy decision cache:

| Setting | Bound | Evidence |
|---|---|---|
| `POLICY_CACHE_TTL_S` | 2.0 s | `services/common/policy_client.py:67`, `:85` |
| `POLICY_CACHE_MAX` | 4096 entries | `services/common/policy_client.py:70`, `:89` |
| Eviction | `OrderedDict` LRU, `popitem(last=False)` when over max | `services/common/policy_client.py:69`, `:88`, `:157-160` |
| Hit path | TTL check + `move_to_end`, no network | `services/common/policy_client.py:133-138` |

**R-SCL-02 — External engines are the slow path.** OPA, Vault, Kafka, LLM providers and the memory stores are **never** consulted to resolve a configuration value on a hot path. They are consulted to *do work*, behind a timeout and a circuit breaker. The configuration chain (§3) is in-process; that is what makes it legal to call it per request.

**R-SCL-03 — Every external hop has a timeout and a bound.** Cited settings:

| Setting | What it bounds | Evidence |
|---|---|---|
| `HTTP_CONNECT_TIMEOUT_S` / `HTTP_READ_TIMEOUT_S` / `HTTP_SLOW_READ_TIMEOUT_S` | Generic HTTP | `config/settings.py:120-122` |
| `LLM_CONNECT_TIMEOUT_S` / `LLM_READ_TIMEOUT_S` | LLM calls | `config/settings.py:113-114` |
| `MEM_HTTP_TIMEOUT`, `MEM_WRITE_TIMEOUT_S`, `MEM_RECALL_TIMEOUT_S`, `MEM_HISTORY_TIMEOUT_S` | Memory seam | `config/settings.py:80`, `:95-97` |
| `CB_FAILURE_THRESHOLD` / `CB_RESET_TIMEOUT_S` | Circuit breaker | `config/settings.py:108-109` (per `SOMA-SETTINGS-MODEL-001` §9.1) |
| `SOMA_OPA_TIMEOUT` | OPA evaluation | `somafractalmemory/settings/model.py:228` |
| `SOMA_MILVUS_TIMEOUT_S` | Milvus connect/IO | `somafractalmemory/settings/model.py:96-98` |
| `SOMA_CIRCUIT_FAILURE_THRESHOLD` / `SOMA_CIRCUIT_RESET_INTERVAL` | SFM circuit breaker | `somafractalmemory/settings/model.py:236-241` |
| `SOMA_RATE_LIMIT_MAX` / `SOMA_RATE_LIMIT_WINDOW` | SFM API rate | `somafractalmemory/settings/model.py:206-211` |
| `SOMA_MAX_REQUEST_BODY_MB` | SFM request body | `somafractalmemory/settings/model.py:203-205` |

**R-SCL-04 — Authz is fail-closed and cached, never fail-open.** `PolicyClient.evaluate` denies when no engine is attached, denies on transport error, and never honours a fail-open flag (`policy_client.py:101-121`, `:162-165`, `:86-87`). A cached decision expires by TTL (R-SCL-01); it is not a permanent grant.

**R-SCL-05 — Thin.** No configuration layer is added "for flexibility". The chain has four steps because there are four owners (§2). A fifth layer is a bug.

---

## 6. Worked example: `SOMABRAIN_URL` through the triad

One endpoint, one name, three repos. This is what conforming looks like.

### 6.1 What the value is

| | |
|---|---|
| Class | **Topology** (§2.2) — a deployment URL |
| Name | `SOMABRAIN_URL` (UPPER Django name) |
| Category | `INFRA` (`capsule_settings.py:47`, duplicated key at `:113`) |
| Owner | L3 env at boot → Django settings after boot |
| Schema default | **empty string / unset.** A URL has no code default. |

### 6.2 somaAgent01 — the caller

| Step | Where | What happens |
|---|---|---|
| Declare (Django) | `config/settings.py:64` | `SOMABRAIN_URL = os.environ.get("SOMABRAIN_URL")` — env populates Django at boot; no fallback |
| Declare (model) | `settings_model.py:184` | `service_somabrain_url: str = Field(default_factory=lambda: str(_dj("SOMABRAIN_URL", "")))` — the schema view of the same name |
| Register | `capsule_settings.py:47`, `:113` | `KEY_CATEGORY["SOMABRAIN_URL"] = CATEGORY_INFRA` |
| Resolve | `service_urls.py:33-78` | `require_service_url("SOMABRAIN_URL", capsule=…, agent_id=…)` walks Capsule → AgentSetting → Django → `service_somabrain_url`, then **raises** if all empty |
| Read | `admin/core/api/health.py:195` | `require_service_url("SOMABRAIN_URL")` — health check refuses to invent a host |
| Read | `admin/core/chat_orchestrator.py:146` | `getattr(django_settings, "SOMABRAIN_URL", "")` then empty → fail-closed (no localhost) |

The call site never names a host. The operator changes env/Compose; the reviewer sees the name in one registry row and one model field.

### 6.3 somabrain — the service itself

SomaBrain does not read `SOMABRAIN_URL`; it *is* that service. Its own base is `SOMABRAIN_API_URL`:

| Step | Where | What happens |
|---|---|---|
| Declare | `somabrain/settings/django_core.py:33`, `:52`; `somabrain/settings/infra.py:327` | `SOMABRAIN_API_URL` from env |
| Scheme constants | `somabrain/settings/constants.py:14-20` | `HTTP_SCHEME` / `HTTPS_SCHEME` only — never a host |
| Resolve | `somabrain/settings/resolve.py:87-101` | `require_url("SOMABRAIN_API_URL")` — must contain `://`, strips trailing `/`, else raises `UnconfiguredServiceError` |
| Identity | `resolve.py:112-132` | `require_tenant` / `require_namespace` **raise** on empty. There is no `or "default"` on an auth, memory or namespace path |

### 6.4 somafractalmemory — the store

SFM is reached from the other two via `SOMAFRACTALMEMORY_URL` / `SOMA_MEMORY_URL`. SFM itself resolves its own topology through `TUNABLES`:

| Step | Where | What happens |
|---|---|---|
| Declare | `somafractalmemory/settings/model.py:76-256` | `TUNABLES` registry: name, kind, schema default, category, description — declared once |
| Resolve | `model.py:339-376` | `resolve_setting(key)` — Django settings → schema default, or raise when `REQUIRED` |
| URLs | `model.py:395-418` | `service_url(key)` — absolute `http(s)` or raise. "No URL may be named in logic." |
| Assembled URIs | `model.py:421-437` | `milvus_uri()` — the only place that knows how to build the vector-store URI |

SFM has no Capsule and no AgentSetting layer. The chain is two steps (`settings/model.py:5-7`). That is correct for that repo, not a gap.

### 6.5 The same rule in all three

| Question | somaAgent01 | somabrain | somafractalmemory |
|---|---|---|---|
| Where declared? | Django settings + `SettingsModel` | Django settings (`settings/*.py`) | `TUNABLES` registry |
| Who may override? | Capsule, AgentSetting | `BrainSetting` (tenant) | — (no agent layer) |
| How read? | `require_service_url` / `resolve_setting` | `require_url` / `resolve_tunable` | `service_url` / `resolve_setting` |
| Missing URL? | `ImproperlyConfigured` | `UnconfiguredServiceError` | `ImproperlyConfigured` |
| Localhost fallback? | none | none | none |

---

## 7. Anti-patterns

Each of these has already happened. The incident is named so the mistake is recognisable when it is about to be repeated.

| ID | Anti-pattern | The real incident | The rule it breaks |
|---|---|---|---|
| **AP-01** | **Invented key names.** A call site invents a new setting name because it did not look. | `MEM_RECALL_LIMIT` was written into the chat lane while `MEM_RECALL_TOP_K` already existed, declared and registered (`config/settings.py:88`, `capsule_settings.py:69`, `settings_model.py:100-108`). Commit `391e2fa5`: *"I invented MEM_RECALL_LIMIT when MEM_RECALL_TOP_K already existed… Both violate check-first-code-second."* | R-VAL-01, R-VAL-06; VIBE check-first-code-second |
| **AP-02** | **`getattr(settings, X, "http://localhost…")`.** A call site invents a host when the setting is missing. | `admin/core/infrastructure/health_checker.py:8` documents the pattern as the defect it removed; `somabrain/api/endpoints/system_health.py:246` still reads `getattr(settings, "SOMABRAIN_OPA_URL", "http://localhost:20181")`; `somabrain/memory/milvus_client.py:169` falls back to `"localhost"`. A URL a caller invents is a URL an operator cannot change and a reviewer cannot see. | R-TOP-02, R-TOP-03; Rule 91 |
| **AP-03** | **A default duplicated in a model *and* a call site.** The same number lives in two places and they drift. | `MEM_RECALL_TOP_K` default `8` appears at `config/settings.py:88`, `services/gateway/settings.py:256`, `settings_model.py:101` and `:107`, and again as a call-site literal at `admin/core/chat_orchestrator.py:1315` and `:1318`, and `services/tool_executor/memory_tools.py:81` and `:84`. Commit `391e2fa5` fixed the one-off knobs: *"The number appears in exactly one place."* The remaining `8` literals are tracked drift. | R-VAL-01 |
| **AP-04** | **`or "default"` on an authz path.** A missing tenant or namespace is silently remapped to a shared partition. | Commit `4b9b89c9`: *"a missing tenant on an authorisation path now denies instead of being silently remapped to 'default', and a memory write with no tenant refuses instead of landing in a shared namespace."* Guard test: `tests/unit/test_no_silent_default_tenant.py:23-40`. `somabrain/settings/resolve.py:112-132` exists so this cannot come back. | R-VAL-04, R-RES-03 |
| **AP-05** | **A secret written to `os.environ`.** A secret read from Vault is exported "so other modules can see it". | somabrain wrote Vault-sourced secrets back into env at seven sites (`somabrain/settings/infra.py:70`, `:77`, `:29`; `somabrain/settings/django_core.py:110`, `:119-120`, `:130-131`). Tracked as BLOCKER in `docs/plans/2026-10-03-triad-full-integration.md` Task 7.1. *"A secret that is copied into ENV is a secret in ENV — the Vault migration is undone the moment the process starts."* | R-SEC-01; Rule 164 |
| **AP-06** | **A second vocabulary for one concept.** Two action names, two key names, two hosts for the same thing. | `skin:*` sat next to catalog `org:*` / `system:*` as a second authority vocabulary (`policy/skins.rego:26-63` vs `admin/ui/api/skins.py:168`, `:211`). `admin/core/authz.py:519-523` retired it: *"a second vocabulary is where authority drifts."* Tracked as S-F-05 / OPEN-10 in `SOMA-UI-SKINS-001.md`. | R-VAL-06 |
| **AP-07** | **`env.str(..., default="")` for a credential.** A secret-like key is given an empty-string schema default, so "unset" and "empty password" look identical. | `somabrain/settings/infra.py:334` `SUPERVISOR_HTTP_PASS = env.str("SUPERVISOR_HTTP_PASS", default="")`, `:358` `OUTBOX_API_TOKEN = env.str("OUTBOX_API_TOKEN", default="")`. A credential has no schema default; it is Vault material (§2.1). | R-SEC-01, R-VAL-04; Rule 164 |

A reviewer who sees any of these shapes stops the change. None of them is a style preference; each one has already caused a defect with a commit message and a guard test.

---

## 8. Per-repo appendix

The pattern is the same in all three repos; the module names are not. This table is so the pattern is recognisable.

### 8.1 Module map

| Role | somaAgent01 | somabrain | somafractalmemory |
|---|---|---|---|
| Settings declaration | `config/settings.py`, `services/gateway/settings.py` | `somabrain/settings/{infra,django_core,cognitive,neuro}.py` | `somafractalmemory/settings/{infra,django_core}.py` |
| Registry / model | `admin/core/helpers/settings_model.py` (`SettingsModel`, 78 fields) | `somabrain/brain_settings/models.py` (`BrainSetting`) | `somafractalmemory/settings/model.py` (`TUNABLES`, `Tunable`) |
| Category map | `admin/core/helpers/capsule_settings.py:45-139` (`KEY_CATEGORY`) | categories on the brain-settings model | `model.py:258-259` (`KEY_CATEGORY` derived from `TUNABLES`) |
| Resolver | `capsule_settings.resolve_setting` (`:170-206`) | `settings.resolve.resolve_tunable` (`:135-169`) | `settings.model.resolve_setting` (`:339-376`) |
| URL resolver (fail-closed) | `admin/core/helpers/service_urls.require_service_url` (`:33-78`) | `settings.resolve.require_url` (`:87-101`) | `settings.model.service_url` (`:395-418`) |
| Identity guard | `admin/core/authz.py` (catalog vocabulary) | `settings.resolve.require_tenant` / `require_namespace` (`:112-132`) | namespace tunables in `TUNABLES` (`:106-112`) |
| Vendor protocol bases | `admin/core/helpers/vendor_api_bases.py` | `somabrain/settings/constants.py` (scheme tokens) | **OPEN-01** (none today) |
| Secrets | `services/common/vault_secrets.py`, `unified_secret_manager.py` | `somabrain/core/security/vault_client.py` | `somafractalmemory/admin/core/security/vault_client.py` |
| Hot-path cache exemplar | `services/common/policy_client.py` (`OrderedDict` LRU, TTL) | same client, copied bounds | circuit breaker + rate limit in `TUNABLES` (`:206-211`, `:236-247`) |

### 8.2 How to read each repo's resolver

| Repo | Read a required URL | Read an optional tunable | Missing required value |
|---|---|---|---|
| somaAgent01 | `require_service_url("SOMABRAIN_URL", capsule=c, agent_id=a)` | `resolve_setting(key, capsule=c, agent_id=a)` | `ImproperlyConfigured` |
| somabrain | `require_url("SOMABRAIN_API_URL")` | `optional_setting(name)` / `resolve_tunable(key, tenant=t)` | `UnconfiguredServiceError` |
| somafractalmemory | `service_url("SOMA_OPA_URL")` | `resolve_optional(key)` | `ImproperlyConfigured` |

### 8.3 Naming conventions that are load-bearing

| Convention | Why |
|---|---|
| UPPER Django name is the key | Step 3 of the chain is `getattr(django_settings, key)` (`capsule_settings.py:201`) |
| `service_<snake>` on `SettingsModel` | The schema view of the same UPPER name (`settings_model.py:181-219`; `service_urls.py:62-72`) |
| `SOMA_*` / `SOMABRAIN_*` prefixes | Repo-scoped names, so a key is unambiguous when all three settings modules are in one workspace |
| `REQUIRED` sentinel (SFM) | Absent means fail closed, not "empty" (`model.py:53-60`) |
| No `or "default"` | Tenant and namespace are security boundaries (AP-04) |

---

## 9. Conformance checklist

An implementation conforms to this standard when all of the following hold.

| # | Requirement | Verification |
|---|---|---|
| K-01 | Every value is in exactly one class (§2): secret, topology or behaviour | Inventory `SOMA-SETTINGS-MODEL-001` §9; no unmapped key |
| K-02 | Secrets resolve from Vault only; none is written to `os.environ`, a file, or a DB value | AP-05 guard test; `SOMA-01-SEC-001` audit |
| K-03 | Topology has no code default; a missing required URL raises | `require_service_url` / `require_url` / `service_url` raise paths |
| K-04 | Resolution is `Capsule > AgentSetting > SettingsModel/Django > schema default` | `capsule_settings.resolve_setting` matches §3.1 |
| K-05 | `KEY_CATEGORY` keys are UPPER Django names (or documented model field names) | Diff `KEY_CATEGORY` against `getattr(settings, key)` |
| K-06 | Every value is read through one resolver (R-VAL-03) | Grep for `os.environ.get` / `getattr(settings` outside settings load |
| K-07 | Every behaviour value is administrable (R-VAL-02) | CRUD surface exists |
| K-08 | A knob with no reader is deleted (R-VAL-05) | Reader grep per registry row |
| K-09 | Decision caches are bounded LRU with TTL (R-SCL-01) | `policy_client.py` bounds |
| K-10 | Every external hop has a timeout (R-SCL-03) | §5 table |
| K-11 | No anti-pattern from §7 is present in a change under review | Review checklist |
| K-12 | OPEN items (§10) are either closed or explicitly accepted with an owner | §10 |

---

## 10. OPEN items

| ID | Question | Default if unresolved | Owner |
|---|---|---|---|
| OPEN-01 | Does somafractalmemory need a vendor protocol-bases module? SFM calls no vendor cloud today. | No module; create `somafractalmemory/settings/vendor_api_bases.py` the first time it does (R-VEN-01) | Architecture |
| OPEN-02 | Should `settings_defaults._env_or_db` (`:100-111`, ENV > DB > default) be reconciled to §3.1 or explicitly scoped as a migration shim? (Also `SOMA-SETTINGS-MODEL-001` D-07.) | Reconcile to §3.1 | Architecture |
| OPEN-03 | Should the residual `MEM_RECALL_TOP_K`, `8` call-site literals (AP-03: `chat_orchestrator.py:1315`, `:1318`; `memory_tools.py:81`, `:84`) be deleted so the number appears only at its declaration sites? | Yes; read through `resolve_setting` / `get_memory_setting` with no call-site literal | Engineering |
| OPEN-04 | Should somabrain's remaining `getattr(settings, …, "localhost…")` sites (AP-02: `system_health.py:246`, `milvus_client.py:169`, `core_singletons.py:354`, `config_runtime.py:31`) be converted to `require_url` / `require_setting`? | Yes | somabrain |
| OPEN-05 | Should `KEY_CATEGORY`'s duplicate `SOMABRAIN_URL` entries (`capsule_settings.py:47` and `:113`) be collapsed to one? | Yes; one key, one row | Engineering |
| OPEN-06 | SFM `SOMA_DB_HOST` schema default is `"localhost"` (`model.py:79`). Topology with a schema default is against R-TOP-02's spirit for *service* URLs; is a local Postgres default acceptable for a single-node store? | Accept for `SOMA_DB_*` (local store, not a service URL); keep `service_url()` strict for http(s) targets | Architecture |
| OPEN-07 | Canonical cross-repo name for the SomaBrain base: `SOMABRAIN_URL` (agent), `SOMABRAIN_API_URL` (self), `SA01_SOMA_BASE_URL` (legacy agent). Converge on one? | Keep repo-scoped names (§8.3); document the alias map here when an operator surface needs one | Ops + Architecture |

---

## 11. Document Reference Matrix

This document is registered in `docs/iso/DOCUMENT-REGISTER.md` and listed in `SOMA-01-QMS-001.md` §7.

| Document | Identifier | ISO Reference | Purpose |
|---|---|---|---|
| Configuration, Endpoints and Secret Resolution | SOMA-STD-CONFIG-001 | ISO 9001:2015 clause 7.5; ISO/IEC 27001:2022 A.8.9 | Cross-repo rules for value classes, resolution, and secrets |

End of Document
