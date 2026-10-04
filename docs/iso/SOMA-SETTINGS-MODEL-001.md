# SOMA-SETTINGS-MODEL-001 — Soma Settings Model and Configuration Inventory

## Document Control

| Field | Value |
|---|---|
| Document Title | Soma Settings Model and Configuration Inventory |
| Document Identifier | SOMA-SETTINGS-MODEL-001 |
| Version | 1.0.1 |
| Date | 2026-09-27 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO/IEC 25010 (quality model, category lens) · ISO/IEC 27001:2022 (A.8.9 configuration management) · ISO 9001:2015 (documented information) |
| Next Review | 2026-12-27 |
| Related | `SOMA-01-DOCS-001.md`, `SOMA-01-SEC-001.md`, `SOMA-01-ARCH-001.md`, `SOMA-A0-PARITY-001.md`, `docs/standards/SOMA-STD-CODING-001.md`, `docs/standards/SOMA-STD-CONFIG-001.md` |
| Source of truth | This document for the settings *model*; code paths cited per row for *live values* |
| Audience | All engineering contributors, operators, and any agent acting on somaAgent01 / somabrain / somafractalmemory |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-09-27 | SomaTech Engineering | Initial issue. Normative authority model, category taxonomy, full settings inventory, Capsule/Constitution binding rules, env-vs-Vault rules, conformance checklist, drift register. |
| 1.0.1 | 2026-10-03 | SomaTech Engineering | Cross-reference SOMA-STD-CONFIG-001 (endpoint resolution, anti-patterns). Service URLs registered through KEY_CATEGORY; schema defaults empty for deployment URLs. |

## Normative References

| ID | Reference | Role |
|---|---|---|
| N-1 | `docs/standards/SOMA-STD-CODING-001.md` | Standing engineering rules: no hardcoded product behavior, Vault for secrets, fail-closed |
| N-1b | `docs/standards/SOMA-STD-CONFIG-001.md` | Configuration and service endpoint resolution: four-step pattern, fail-closed URLs, vendor protocol constants |
| N-2 | `SOMA-01-DOCS-001` | Document control and traceability procedure |
| N-3 | `SOMA-01-SEC-001` | Security requirements; secret custody |
| N-4 | `SOMA-01-ARCH-001` | System architecture; memory seam |
| N-5 | ARCHITECTURE-INVARIANTS §2, §6 | Embedding-dimension unity; memory seam fail-closed |
| N-6 | `admin/core/helpers/capsule_settings.py` | Runtime resolution order and category constants (must stay in sync with this document) |
| N-7 | ISO/IEC 27001:2022 A.8.9 | Configuration management — baseline, control, inventory |
| N-8 | ISO/IEC 25010:2018 | Quality model — used only as a category lens, not as certification |

---

## 1. Purpose and Scope

### 1.1 Purpose

This document is the **authority for the Soma settings model**: it defines

1. the **ownership layers** (who is allowed to hold a value and in what role),
2. a **normative category taxonomy** for every setting,
3. the **resolution order** when more than one layer holds a value,
4. the **Capsule / Constitution binding rules** for agent-behaviour defaults,
5. the **env-vs-Vault rules** (what may live in the process environment),
6. a **complete inventory** of every settings key discovered in the triad codebase,
7. a **conformance checklist** and a **drift register**.

It does **not** set product behaviour values. Any literal that appears in code is either
(a) a schema fallback for standalone tests, or (b) a **tracked drift item** (§10).
Normative behaviour defaults belong to the Agent settings model / Capsule / Constitution
(§7), not to this document.

### 1.2 Scope

In scope — every configuration key read or written by:

| Repository | Primary sources inventoried |
|---|---|
| `somaAgent01` | `config/settings.py`, `config/settings_registry.py`, `services/gateway/settings.py`, `admin/core/helpers/settings_model.py`, `admin/core/helpers/settings_defaults.py`, `admin/core/helpers/capsule_settings.py`, `admin/core/models/core.py` (Capsule / Constitution / AgentSetting / UISetting), `admin/llm/api.py`, `admin/llm/models.py`, `admin/core/agentiq/*`, `services/common/memory_contract.py`, `services/common/env_config.py`, `services/common/vault_secrets.py`, bridge workers, tool executor, conversation/delegation workers |
| `somabrain` | `somabrain/settings/cognitive.py`, `somabrain/settings/infra.py`, `somabrain/core/security/vault_client.py` |
| `somafractalmemory` | `somafractalmemory/settings/infra.py` |

Out of scope: third-party library environment variables (`.venv`), test-only fixtures
(`TEST_*` — listed in §9.6 for completeness), generated artefacts, git history.

### 1.3 Out of Scope

- Choosing concrete production values for any key (that is deployment configuration).
- API request/response schemas that are not persisted settings.
- Secrets' contents (Vault owns them; only the *custody rule* is in scope).

---

## 2. Terms and Definitions

| Term | Definition |
|---|---|
| **Setting** | Any named configuration input that changes system or agent behaviour. |
| **Owner (owning layer)** | The single layer authorised to be the *authority* for a setting's value. |
| **Authority** | The layer whose value wins when layers disagree, after Capsule/Agent overrides. |
| **Env injection** | 12-factor population of a setting from the process environment at boot. |
| **Capsule-overridable** | Whether an agent-scoped instance may hold a different value than the infrastructure default. |
| **Schema fallback** | A literal used only when no authority layer produced a value — **not** a product default. |
| **Drift** | A value that influences behaviour but is not yet reachable through a documented setting. |
| **Seam** | The triad memory contract (`services/common/memory_contract.py`) shared by Agent, SomaBrain, SFM. |

---

## 3. Normative Requirements Language

Requirements use **SHALL** (mandatory), **SHALL NOT** (prohibited), **SHOULD** (recommended),
and **MAY** (permitted) per `SOMA-01-SRS-001` §2 convention.

---

## 4. Ownership Layers (Normative)

Four, and only four, layers may own a setting. Every inventory row SHALL name exactly one.

| Layer ID | Name | Role | May hold |
|---|---|---|---|
| **L1** | **Django settings** | Infrastructure authority. `config/settings.py`, `services/gateway/settings.py`, `config/settings_registry.py`, `services/gateway/django_setup.py` as loaded. | Timeouts, tunables, limits, feature switches, non-secret identifiers, topology constants that are *behaviour of the platform* |
| **L2** | **Agent settings model / Capsule / Constitution** | Agent behaviour authority. `SettingsModel` (`admin/core/helpers/settings_model.py`), `AgentSetting` ORM (`admin/core/models/core.py:724`), `Capsule.persona_config` / `tool_policy` / `memory_pointer` (`admin/core/models/core.py:109`), `Constitution` (`admin/core/models/core.py:63`), `UISetting` (`admin/core/models/core.py:495`) | Persona, knobs, tool policy, model slot bindings, per-agent memory policy, UI preferences, constitutional rules |
| **L3** | **Env (URL / port / host only)** | Deployment topology injection. | Service URLs, hostnames, ports, bootstrap addresses, namespace names used as addressing |
| **L4** | **Vault (secrets)** | Secret custody. `services/common/unified_secret_manager.py`, `services/common/vault_secrets.py`, `somabrain/core/security/vault_client.py`, `somafractalmemory/.../vault_client.py`. Secrets MAY transit env only as a Vault-unwrapped boot strap and SHALL NOT be persisted in source or in this document. | API keys, tokens, passwords, private keys, client secrets |

### 4.1 Layer rules (normative)

- **R-OWN-01** — Django settings SHALL be the infrastructure authority. Adapters SHALL read
  tunables via Django settings or `services/common/memory_contract.get_memory_setting()`,
  not via `os.environ` (ARCHITECTURE-INVARIANTS §6; `memory_contract.py:180-211`).
- **R-OWN-02** — Env SHALL be used for **URLs, hosts, ports, and addressing namespaces only**.
  Behavioural tunables SHALL NOT be "env-first". Env MAY populate a Django setting at boot;
  after boot, Django settings is the authority.
- **R-OWN-03** — Secrets SHALL be owned by Vault (L4). Code SHALL NOT embed secret literals.
  `AgentSetting.is_secret=True` marks a row whose *value* is secret material; the row is a
  pointer/override slot, not a secret store (`capsule_settings.py:200-215`).
- **R-OWN-04** — Agent behaviour defaults SHALL be savable on the Capsule body/persona and,
  where they are governance constraints, on the Constitution (§7).
- **R-OWN-05** — No layer other than L1–L4 SHALL introduce a second resolution path.
  A second lookup path is a second source of truth (VIBE §4; `memory_contract.py:194-195`).
- **R-OWN-06** — This document SHALL NOT present code literals as product defaults (VIBE §4).
  See §10 for literals that currently act as implicit behaviour.

---

## 5. Resolution Order (Normative)

When a setting is overridable, resolution is highest-wins:

```
1. Capsule.persona_config["settings"][CATEGORY][key]     (agent identity / body)
2. AgentSetting ORM (agent_id, key)                      (runtime override)
3. Django settings                                       (infrastructure authority)
4. Schema fallback — only when the key is optional and no authority produced a value
```

Implemented by `admin/core/helpers/capsule_settings.py:138-175` (`resolve_setting`).
Constitution constraints are *constraints*, not values: they filter what steps 1–3 may
select (§7.3), they do not supply tunables.

**R-RES-01** — Implementations SHALL follow the order above.
**R-RES-02** — `admin/core/helpers/settings_defaults.py:100-111` (`_env_or_db`: ENV > DB > default)
is a **known deviation** (§10, D-07). It SHALL be reconciled to this order or explicitly
scoped as a migration shim.

---

## 6. Category Taxonomy (Normative)

Ten categories. Constants live in `admin/core/helpers/capsule_settings.py:20-42`
(`CATEGORY_*`, `CATEGORIES`) and SHALL stay in sync with this section.

| ID | Category | Definition | Typical owner |
|---|---|---|---|
| C1 | **INFRA** | Deployment topology, service URLs/hosts/ports, brokers, database, transport timeouts, resilience knobs (circuit breakers), connection pooling. | L1 / L3 |
| C2 | **SECURITY** | Secret material, tokens, credentials, signing keys, auth posture flags that gate access. | L4 (secrets) / L1 (posture flags) |
| C3 | **MEMORY** | Embedding dimension, recall top-k, namespaces, WAL/degraded topics, salience, history limits, memorisation policy. | L1 (seam contract) / L2 (per-agent recall policy) |
| C4 | **LLM** | Providers, model identities/slots, context lengths, rate limits, retries, LLM transport timeouts, model presets. | L1 (defaults) / L2 (slots & presets) |
| C5 | **AGENT** | Tool policy, AgentIQ knobs and derived settings, governor controls, degraded-mode ratios, tool rewards, capability enablement. | L2 |
| C6 | **PERSONALITY** | System prompt, Big-Five traits, neuromodulator baseline/state, learning/GMD config, voice persona. | L2 (Capsule core) |
| C7 | **UI** | Theme, locale/language, presentation preferences. | L2 (`UISetting`) |
| C8 | **GOVERNANCE** | Quotas, budgets, tier limits, tenant identity, constitutional rules, permission maps. | L1 (platform quotas) / L2 (Constitution, per-agent) |
| C9 | **OBSERVABILITY** | Metrics endpoints/bindings, logging level/format, tracing/OTLP, health probes. | L1 |
| C10 | **INTEGRATION** | Bridges (WhatsApp/Telegram/voice), OAuth clients, external renderers, MCP/A2A surface. | L1 (endpoints) / L2 (per-agent enablement) |

Mapping to external models (informative): C1↔25010 performance/compatibility substrate;
C2↔27001 A.8; C3–C6↔functional suitability / agent behaviour; C8↔27001 A.5–A.6 governance;
C9↔25010 observability; C10↔25010 compatibility.

---

## 7. Capsule / Constitution Binding Rules

### 7.1 Capsule is the atomic unit of agent identity

Source: `admin/core/models/core.py:109-418` (Rule 91). The Capsule SHALL carry agent
behaviour defaults so an agent is portable ("agent DNA") without touching infrastructure.

| Capsule field | Category | Contents (per model docstrings / `_build_body_dict`) | Capsule-overridable |
|---|---|---|---|
| `system_prompt` | PERSONALITY | Base cognitive instruction set | Yes |
| `personality_traits` | PERSONALITY | Big-Five traits, 0.0–1.0 | Yes |
| `neuromodulator_baseline` | PERSONALITY | Baseline chemical state | Yes |
| `learning_config` | PERSONALITY | GMD hyperparameters (eta, lambda, alpha) & reward thresholds | Yes |
| `persona_config.knobs` | AGENT | `intelligence_level`, `autonomy_level`, `resource_budget` | Yes |
| `persona_config.prompts` | PERSONALITY / AGENT | injection prompts, tool prompts | Yes |
| `persona_config.memory` | MEMORY | `recall_limit`, `similarity_threshold` | Yes |
| `persona_config.learned` | AGENT | learned lane preferences | Yes |
| `persona_config.settings` | any | Categorized override bucket (`capsule_settings.py:116-135`) | Yes |
| `persona_config.governance` | GOVERNANCE | `opa_policies`, `spicedb_relations` | Yes |
| `tool_policy` | AGENT | `auto_execute`, `approval_required`, `denied` tool lists | Yes |
| `memory_pointer` | MEMORY | tenant, namespace, recall_limit, similarity_threshold | Yes |
| `neuromodulator_state` | PERSONALITY | Last-synced state from SomaBrain | Yes (state, not policy) |
| `chat_model` / `image_model` / `voice_model` / `browser_model` | LLM | FK → `llm.LLMModelConfig` (body model sovereignty) | Yes |
| `capabilities` | AGENT | M2M → `Capability` (hands) | Yes |
| `resource_limits` | GOVERNANCE | Max wall clock, concurrency, etc. | Yes |
| `constitution` / `constitution_ref` | GOVERNANCE | Binding legal framework + cross-system ref | Binding, not overridable away |

### 7.2 AgentIQ: 3 knobs → 12 derived settings

Source: `admin/core/agentiq/settings.py` (`DerivedSettings`), `admin/core/agentiq/derivation.py`.
All 12 are **derived**, not independently set. Knobs SHALL be savable on
`Capsule.persona_config.knobs`.

| Knob (Capsule) | Range | Derived settings |
|---|---|---|
| `intelligence_level` | 1–10 | `temperature`, `max_tokens`, `rlm_iterations`, `recall_limit`, `model_tier`, `brain_query_enabled` |
| `autonomy_level` | 1–10 | `require_hitl`, `tool_approval`, `egress_allowed` |
| `resource_budget` | $/turn | `token_limit`, `cost_tier`, `thinking_budget` |

**R-CAP-01** — Agent behaviour defaults SHALL be savable on the Capsule body/persona.
**R-CAP-02** — Derived settings SHALL NOT be written directly; only knobs are written.
**R-CAP-03** — `Capsule.body` (`core.py:356-418`) SHALL remain the canonical structured view
consumed by ContextBuilder, AgentIQ, UnifiedGate, and Export/Import.

### 7.3 Constitution

Source: `admin/core/models/core.py:63-101`; tenant rules API `admin/gateway/api/gateway.py:200-232`.
The Constitution is **immutable once signed** (`content_hash` + Ed25519 `signature`).
It carries `content` (JSON law) and a tenant-scoped `rules: list[str]` surface.

**R-CON-01** — Every Capsule SHALL reference a valid Constitution (`constitution` FK, `PROTECT`).
**R-CON-02** — Constitution constrains *which* Capsule/AgentSetting values are permissible;
it SHALL NOT itself supply infrastructure tunables.
**R-CON-03** — Exactly one Constitution SHALL be `is_active` at a time.

### 7.4 AgentSetting and UISetting

| Store | Key space | Scope | Secret flag |
|---|---|---|---|
| `AgentSetting` (`core.py:724`) | free `key` + JSON `value` | `agent_id` (tenant defaults use `agent_id="default"`, `admin/llm/api.py:29`) | `is_secret` bool |
| `UISetting` (`core.py:495`) | free `key` + JSON `value` | `tenant` + optional `user_id` | n/a |

Known `AgentSetting` keys (authoritative list of *named* keys in code):

| Key | Category | Scope | Source |
|---|---|---|---|
| `chat_model_id` | LLM | tenant (`default`) | `admin/llm/api.py:529,576-580` |
| `utility_model_id` | LLM | tenant or Capsule | `admin/llm/api.py:519,530,565` |
| `embedding_model_id` | LLM | tenant or Capsule | `admin/llm/api.py:520,531,573` |
| `llm_provider_configs` | LLM | tenant (`default`) | `admin/llm/api.py:314,401` |
| `model_presets` | LLM | tenant (`default`) | `admin/llm/api.py:590,633` |
| every `SettingsModel` field name | per field | agent_id | `settings_defaults.py` `_get_agent_setting` |

---

## 8. Env-vs-Vault Rules (Normative)

| Rule | Statement |
|---|---|
| **R-ENV-01** | Env SHALL carry **URLs, hosts, ports, and addressing namespaces only** (L3). |
| **R-ENV-02** | Secrets (L4) SHALL be sourced from Vault. Env MAY carry a Vault address / token *bootstrap* (`VAULT_ADDR`, `VAULT_TOKEN`, `VAULT_TOKEN_FILE`) to reach Vault; it SHALL NOT carry application secrets as a steady state. |
| **R-ENV-03** | Missing required topology SHALL fail closed (`get_required_env`, `services/common/env_config.py:11`; `MemoryConfigurationError`, `memory_contract.py:48-53`). No localhost fallback and no baked-in credential (`config/settings.py:35-40`). |
| **R-ENV-04** | `DEBUG=true` SHALL be rejected outside dev (`services/gateway/settings.py:42-44`). |
| **R-ENV-05** | Secret-like env names that exist today (`*_TOKEN`, `*_SECRET`, `*_PASSWORD`, `*_API_KEY`) are **legacy injection points**. They SHALL be treated as Vault-unwrapped boot straps and are listed under C2 with Owner=Vault. |
| **R-ENV-06** | This document SHALL NOT record secret values. |

Vault entry points: `services/common/vault_secrets.py`, `services/common/unified_secret_manager.py`,
`somabrain/core/security/vault_client.py` (`SOMABRAIN_VAULT_*`),
`somafractalmemory/.../vault_client.py` (`SOMA_VAULT_*`).

---

## 9. Full Inventory

Notation for **Owner**: `Django` = L1 · `Agent` = L2 (SettingsModel / AgentSetting / Capsule / Constitution / UISetting) · `Env` = L3 (URL/host/port) · `Vault` = L4 (secret).

**Capsule-overridable**: `Yes` if `resolve_setting` / Capsule fields may hold a per-agent
value; `No` if the setting is platform-wide.

**Values**: per §1.1 this document does **not** publish product defaults. "Type" is the
parsed type at the read site. Code fallbacks, where they exist, are cited only as
*implementation* facts and collected in §10.

### 9.1 C1 — INFRA

| Key | Owner | Type | Description | Capsule-overridable | Source |
|---|---|---|---|---|---|
| `SA01_DEPLOYMENT_MODE` | Env | str | Deployment mode selector (`STANDALONE` \| `AAAS` \| `DEV` \| `PROD`) driving SettingsRegistry dispatch | No | `config/settings_registry.py:362`, `config/settings.py:18` |
| `SA01_DEPLOYMENT_TARGET` | Env | str | Deployment target (`LOCAL` \| `EKS` \| `GKE`) | No | `config/settings_registry.py:171` |
| `SA01_ENVIRONMENT` | Env | str | Environment name; drives `IS_DEV_ENV` | No | `services/gateway/settings.py:24` |
| `SA01_ALLOWED_HOSTS` / `ALLOWED_HOSTS` | Env | csv str | Django `ALLOWED_HOSTS` | No | `services/gateway/settings.py:46-52`, `config/settings_registry.py:198` |
| `SA01_DB_DSN` | Env | str | PostgreSQL DSN (credentials portion is Vault material) | No | `services/gateway/settings.py:136-139` |
| `SA01_DB_CONN_MAX_AGE` | Django | int | Django `CONN_MAX_AGE` | No | `services/gateway/settings.py:162` |
| `SA01_DB_CONNECT_TIMEOUT` | Django | int | PG `connect_timeout` (seconds) | No | `services/gateway/settings.py:164` |
| `POSTGRES_HOST` | Env | str | Postgres host | No | `config/settings_registry.py:173` |
| `POSTGRES_PORT` | Env | int | Postgres port | No | `config/settings_registry.py:176` |
| `POSTGRES_DB` | Env | str | Database name | No | `config/settings_registry.py:177` |
| `POSTGRES_USER` | Env | str | Database user | No | `config/settings_registry.py:178` |
| `SA01_REDIS_URL` / `REDIS_URL` | Env | str | Redis connection URL (cache + channels) | No | `services/gateway/settings.py:214`, `config/settings.py:114` |
| `REDIS_HOST` | Env | str | Redis host | No | `config/settings.py:112`, `config/settings_registry.py:180` |
| `REDIS_PORT` | Env | int | Redis port | No | `config/settings.py:113`, `config/settings_registry.py:183` |
| `REDIS_DB` | Env | int | Redis logical DB | No | `config/settings_registry.py:184` |
| `SA01_TEMPORAL_HOST` | Env | str | Temporal frontend `host:port` | No | `services/gateway/settings.py:217` |
| `SA01_TEMPORAL_NAMESPACE` | Env | str | Temporal namespace | No | `services/gateway/settings.py:218` |
| `SA01_TEMPORAL_CONVERSATION_QUEUE` | Env | str | Conversation workflow queue | No | `services/gateway/settings.py:219` |
| `SA01_TEMPORAL_A2A_QUEUE` | Env | str | A2A workflow queue | No | `services/gateway/settings.py:220` |
| `KAFKA_BOOTSTRAP_SERVERS` / `SA01_KAFKA_BOOTSTRAP_SERVERS` | Env | str | Kafka brokers | No | `services/gateway/settings.py:223-225`, `config/settings_registry.py:201` |
| `KAFKA_SECURITY_PROTOCOL` | Env | str | Kafka security protocol | No | `config/settings_registry.py:202` |
| `KAFKA_SASL_MECHANISM` | Env | str | Kafka SASL mechanism | No | `config/settings_registry.py:203` |
| `KAFKA_SASL_USERNAME` | Env | str | Kafka SASL username | No | `config/settings_registry.py:204` |
| `KAFKA_SASL_PASSWORD` | Vault | str | Kafka SASL password | No | `config/settings_registry.py:205` |
| `PUBLISH_KAFKA_TIMEOUT_SECONDS` | Django | float | Kafka publish timeout | No | `config/settings_registry.py:206-208` |
| `CONVERSATION_INBOUND` | Env | str | Conversation inbound topic | No | `services/gateway/settings.py:226`, `services/conversation_worker/main.py` |
| `CONVERSATION_OUTBOUND` | Env | str | Conversation outbound topic | No | `services/conversation_worker/main.py` |
| `CONVERSATION_GROUP` | Env | str | Conversation consumer group | No | `services/conversation_worker/main.py` |
| `DELEGATION_TOPIC` | Env | str | Delegation topic | No | `services/delegation_gateway/main.py` |
| `DELEGATION_GROUP` | Env | str | Delegation consumer group | No | `services/delegation_worker/main.py` |
| `A2A_TOPIC` | Env | str | A2A topic | No | `services/delegation_gateway/temporal_worker.py` |
| `A2A_OUT_TOPIC` | Env | str | A2A outbound topic | No | `services/delegation_gateway/main.py` |
| `TOOL_REQUESTS_TOPIC` | Env | str | Tool-executor request topic | No | `services/tool_executor/config.py` |
| `TOOL_RESULTS_TOPIC` | Env | str | Tool-executor result topic | No | `services/tool_executor/config.py` |
| `TOOL_EXECUTOR_TOPICS` | Env | csv str | Additional tool-executor topics | No | `services/tool_executor/config.py` |
| `TOOL_EXECUTOR_GROUP` | Env | str | Tool-executor consumer group | No | `services/tool_executor/config.py` |
| `TASK_FEEDBACK_TOPIC` | Env | str | Task feedback topic | No | `services/tool_executor/result_publisher.py` |
| `MEMORY_REPLICATOR_GROUP` | Env | str | Memory replicator consumer group | No | `services/memory_replicator/main.py` |
| `MILVUS_HOST` | Env | str | Milvus host (AAAS) | No | `config/settings_registry.py:298` |
| `MILVUS_PORT` | Env | int | Milvus port | No | `config/settings_registry.py:301` |
| `SOMA_MILVUS_HOST` | Env | str | SFM-side Milvus host | No | `infra/aaas/unified_settings.py` |
| `SOMA_MILVUS_PORT` | Env | int | SFM-side Milvus port | No | `infra/aaas/unified_settings.py` |
| `SPICEDB_HOST` | Env | str | SpiceDB host | No | `config/settings_registry.py:186` |
| `SPICEDB_PORT` | Env | int | SpiceDB port | No | `config/settings_registry.py:187` |
| `SPICEDB_INSECURE` | Env | bool | SpiceDB plaintext flag | No | `config/settings_registry.py:189` |
| `HTTP_CONNECT_TIMEOUT_S` | Django | float | Generic HTTP connect timeout | No | `config/settings.py:95` |
| `HTTP_READ_TIMEOUT_S` | Django | float | Generic HTTP read timeout | No | `config/settings.py:96` |
| `HTTP_SLOW_READ_TIMEOUT_S` | Django | float | Slow-path HTTP read timeout | No | `config/settings.py:97` |
| `CB_FAILURE_THRESHOLD` | Django | int | Circuit-breaker failure threshold | No | `config/settings.py:108` |
| `CB_RESET_TIMEOUT_S` | Django | float | Circuit-breaker reset timeout | No | `config/settings.py:109` |
| `SOMABRAIN_URL` / `SA01_SOMA_BASE_URL` | Env | str | SomaBrain cognitive runtime URL | No | `services/gateway/settings.py:242-247`, `config/settings.py:39` |
| `SOMAFRACTALMEMORY_URL` | Env | str | SomaFractalMemory store URL | No | `config/settings.py:43`, `services/gateway/settings.py:251` |
| `SOMA_MEMORY_URL` | Env | str | Legacy SFM URL alias | No | `services/common/adapters/memory_http.py` |
| `SA01_OPA_URL` | Env | str | Open Policy Agent URL | No | `services/gateway/settings.py:297` |
| `SA01_POLICY_URL` | Env | str | Policy service URL | No | `services/common/policy_client.py` |
| `SA01_POLICY_DATA_PATH` | Env | str | Local policy data path | No | `services/common/policy_client.py` |
| `SA01_POLICY_CACHE_TTL` | Django | seconds | Policy cache TTL | No | `services/common/policy_client.py` |
| `POLICY_BASE_URL` | Env | str | Policy base URL (tool executor) | No | `services/tool_executor/main.py` |
| `POLICY_REQUEUE_PREFIX` | Django | str | Redis requeue key prefix | No | `config/settings_registry.py:211` |
| `POLICY_REQUEUE_PREFIX_EXTRA` | Django | str | Extra requeue prefix | No | `services/tool_executor/config.py` |
| `SA01_GATEWAY_BASE` | Env | str | Internal gateway base URL | No | `services/tool_executor/tools.py` |
| `SA01_WORKER_GATEWAY_BASE` | Env | str | Worker→gateway base URL | No | `services/conversation_worker/main.py` |
| `ROUTER_URL` | Env | str | Model-router URL | No | `services/common/router_client.py` |
| `TENANT_CONFIG_PATH` | Env | str | Tenant config file path | No | `services/common/tenant_config.py` |
| `TENANT_CONFIG_PATH_EXTRA` | Env | str | Extra tenant config path | No | `services/tool_executor/config.py` |
| `SA01_REDIS_URL` (requeue store) | Env | str | Requeue Redis URL | No | `config/settings_registry.py:210` |
| `SOMA_AAAS_MODE` | Env | str | AAAS mode (`true` \| `direct` \| `false`) | No | `config/settings_registry.py:259,376` |

### 9.2 C2 — SECURITY

| Key | Owner | Type | Description | Capsule-overridable | Source |
|---|---|---|---|---|---|
| `SECRET_KEY` | Vault | str | Django `SECRET_KEY` | No | `config/settings.py:13`, `services/gateway/settings.py:33-39` |
| `VAULT_ADDR` | Env | str | Vault address (bootstrap) | No | `config/settings.py:31` |
| `VAULT_TOKEN` | Vault | str | Vault token (bootstrap) | No | `config/settings.py:32`, `services/common/vault_secrets.py` |
| `VAULT_TOKEN_FILE` | Env | str | Path to Vault token file | No | `services/common/vault_secrets.py` |
| `VAULT_MOUNT` | Env | str | Vault KV mount | No | `config/settings.py:33` |
| `VAULT_PATH_PREFIX` | Env | str | Vault path prefix | No | `config/settings_registry.py:195` |
| `VAULT_NAMESPACE` | Env | str | Vault namespace | No | `services/common/vault_secrets.py` |
| `VAULT_CA_CERT` | Env | str | Vault CA bundle path | No | `services/common/vault_secrets.py` |
| `VAULT_SKIP_VERIFY` | Env | bool | Skip TLS verify (dev only) | No | `services/common/vault_secrets.py` |
| `SOMABRAIN_MEMORY_HTTP_TOKEN` | Vault | str | SomaBrain service bearer token | No | `config/settings.py:40`, `services/gateway/settings.py:248` |
| `SOMA_API_TOKEN` | Vault | str | SFM / triad API token | No | `config/settings.py:44` |
| `SA01_SOMABRAIN_API_KEY` | Vault | str | SomaBrain API key (alias of `SOMA_API_TOKEN`) | No | `services/gateway/settings.py:254` |
| `KEYCLOAK_CLIENT_SECRET` / `SA01_KEYCLOAK_CLIENT_SECRET` | Vault | str | Keycloak client secret | No | `config/settings.py:24`, `services/gateway/settings.py:330` |
| `SA01_KEYCLOAK_PUBLIC_KEY` | Env | str | Keycloak realm public key (PEM) | No | `services/gateway/settings.py:331` |
| `SA01_JWT_SECRET` | Vault | str | Gateway JWT secret | No | `services/gateway/providers.py` |
| `GOOGLE_CLIENT_SECRET` | Vault | str | Google OAuth client secret | No | `services/gateway/settings.py:352` |
| `SA01_LLM_API_KEY` | Vault | str | Internal LLM service API key | No | `services/gateway/settings.py:308` |
| `SA01_GATEWAY_INTERNAL_TOKEN` | Vault | str | Internal worker→gateway token | No | `services/conversation_worker/main.py` |
| `SPICEDB_TOKEN` | Vault | str | SpiceDB token | No | `config/settings_registry.py:188` |
| `SOMA_REGISTRY_PRIVATE_KEY` | Vault | str | Registry Ed25519 private key | No | `services/registry_service.py` |
| `SOMABRAIN_VAULT_TOKEN` | Vault | str | SomaBrain→Vault token | No | `somabrain/core/security/vault_client.py` |
| `SOMA_VAULT_TOKEN` | Vault | str | SFM→Vault token | No | `somafractalmemory/.../vault_client.py` |
| `WA_CLOUD_API_TOKEN` | Vault | str | WhatsApp Cloud API token | No | `admin/bridges/services/whatsapp_bridge.py` |
| `WA_CLOUD_APP_SECRET` | Vault | str | WhatsApp app secret | No | `admin/bridges/services/whatsapp_bridge.py` |
| `WA_CLOUD_WEBHOOK_VERIFY_TOKEN` | Vault | str | WhatsApp webhook verify token | No | `admin/bridges/services/whatsapp_bridge.py` |
| `SA01_AUTH_REQUIRED` | Django | bool | Auth required posture | No | `services/gateway/settings.py:237` |
| `SA01_AUTHZ_FAIL_OPEN` | Django | bool | AuthZ fail-open flag (fail-closed default) | No | `config/settings_registry.py:217` |
| `AUTH_MAX_ATTEMPTS` | Django | int | Account lockout max attempts | No | `config/settings_registry.py:213` |
| `AUTH_LOCKOUT_DURATION` | Django | int | Lockout duration (s) | No | `config/settings_registry.py:214` |
| `AUTH_ATTEMPT_WINDOW` | Django | int | Attempt window (s) | No | `config/settings_registry.py:215` |
| `SA01_JWT_ISSUER_STRICT` | Django | bool | JWT issuer strictness | No | `services/gateway/settings.py:344` |
| `SA01_HSTS_SECONDS` | Django | int | HSTS max-age | No | `services/gateway/settings.py:60` |
| `auth_login` / `auth_password` / `root_password` | Vault | str | Legacy agent credentials (`SettingsModel`) | Yes | `settings_model.py:121-123`, `settings_defaults.py:309-311` |
| `api_keys` | Vault | dict | Per-provider API keys in settings model | Yes | `settings_model.py:120` |
| `mcp_server_token` | Vault | str | MCP server token | Yes | `settings_model.py:158` |
| `secrets` | Vault | str | Agent secrets blob | Yes | `settings_model.py:163` |
| `rfc_password` | Vault | str | RFC/Docker tunnel password | Yes | `settings_model.py:133` |

### 9.3 C3 — MEMORY

| Key | Owner | Type | Description | Capsule-overridable | Source |
|---|---|---|---|---|---|
| `MEM_EMBED_DIM` | Django | int | Shared embedding dimension; MUST equal SFM `SOMA_VECTOR_DIM` and SomaBrain `SOMABRAIN_EMBED_DIM` (ARCHITECTURE-INVARIANTS §2) | No | `config/settings.py:50`, `memory_contract.py:221-233` |
| `SOMA_VECTOR_DIM` | Django | int | SFM vector dim (mirrors `MEM_EMBED_DIM`) | No | `somafractalmemory/settings/infra.py:73` |
| `SOMABRAIN_EMBED_DIM` | Django | int | SomaBrain embed dim (env key `EMBED_DIM`) | No | `somabrain/settings/cognitive.py:111` |
| `MEM_HTTP_TIMEOUT` | Django | float | Memory HTTP timeout | No | `config/settings.py:55` |
| `MEM_RECALL_TOP_K` | Django | int | Default recall top-k | **Yes** | `config/settings.py:63`, `settings_model.py:100-108` |
| `MEM_PROXIMITY_TOP_K` | Django | int | Proximity/solutions top-k | **Yes** | `config/settings.py:64`, `settings_model.py:103-111` |
| `MEM_HISTORY_LIMIT` | Django | int | History limit | **Yes** | `config/settings.py:65`, `settings_model.py:96-98` |
| `MEM_CHAT_NAMESPACE` | Django | str | Chat-history namespace | **Yes** | `config/settings.py:66` |
| `MEM_DEFAULT_KIND` | Django | str | Default memory kind (`episodic`/`semantic`/`belief`) | **Yes** | `config/settings.py:67` |
| `MEM_DEFAULT_SALIENCE` | Django | float | Default salience | **Yes** | `config/settings.py:68` |
| `MEM_DEFAULT_SOURCE` | Django | str | Default source label | **Yes** | `config/settings.py:69` |
| `MEM_WRITE_TIMEOUT_S` | Django | float | Memory write timeout | No | `config/settings.py:70` |
| `MEM_RECALL_TIMEOUT_S` | Django | float | Memory recall timeout | No | `config/settings.py:71` |
| `MEM_HISTORY_TIMEOUT_S` | Django | float | History fetch timeout | No | `config/settings.py:72` |
| `MEMORY_WAL_TOPIC` | Django | str | Degraded-mode WAL topic | No | `config/settings.py:75` |
| `MEMORY_DEGRADED_TOPIC` | Django | str | Degradation events topic | No | `config/settings.py:76`, `services/common/degraded_memory_queue.py:34-37` |
| `SFM_NAMESPACE` | Env | str | SFM namespace | **Yes** | `config/settings.py:56` |
| `SOMABRAIN_NAMESPACE` | Env | str | SomaBrain namespace | **Yes** | `config/settings.py:57` |
| `SA01_MEMORY_NAMESPACE` | Env | str | Registry memory namespace | No | `config/settings_registry.py:223` |
| `SOMA_MEMORY_NAMESPACE` | Env | str | AAAS memory namespace | No | `infra/aaas/unified_settings.py` |
| `SOMA_NAMESPACE` | Env | str | AAAS general namespace | No | `infra/aaas/unified_settings.py` |
| `SA01_NAMESPACE` | Env | str | Tool-executor namespace | No | `services/tool_executor/result_publisher.py` |
| `SA01_TENANT_ID` | Env | str | Default tenant id for idempotency | No | `config/settings_registry.py:222` |
| `memory_recall_enabled` | Agent | bool | Enable recall | **Yes** | `settings_model.py:94` |
| `memory_recall_delayed` | Agent | bool | Delayed recall | **Yes** | `settings_model.py:95` |
| `memory_recall_interval` | Agent | int | Recall interval | **Yes** | `settings_model.py:96-98` |
| `memory_recall_history_len` | Agent | int | History length for recall | **Yes** | `settings_model.py:99` |
| `memory_recall_memories_max_search` | Agent | int | Max memories to search | **Yes** | `settings_model.py:100-102` |
| `memory_recall_solutions_max_search` | Agent | int | Max solutions to search | **Yes** | `settings_model.py:103-105` |
| `memory_recall_memories_max_result` | Agent | int | Max memories returned | **Yes** | `settings_model.py:106-108` |
| `memory_recall_solutions_max_result` | Agent | int | Max solutions returned | **Yes** | `settings_model.py:109-111` |
| `memory_recall_similarity_threshold` | Agent | float | Similarity threshold | **Yes** | `settings_model.py:112` |
| `memory_recall_query_prep` | Agent | bool | Query preparation | **Yes** | `settings_model.py:113` |
| `memory_recall_post_filter` | Agent | bool | Post-filtering | **Yes** | `settings_model.py:114` |
| `memory_memorize_enabled` | Agent | bool | Enable memorisation | **Yes** | `settings_model.py:115` |
| `memory_memorize_consolidation` | Agent | bool | Enable consolidation | **Yes** | `settings_model.py:116` |
| `memory_memorize_replace_threshold` | Agent | float | Replace threshold | **Yes** | `settings_model.py:117` |
| `Capsule.memory_pointer.{tenant,namespace,recall_limit,similarity_threshold}` | Agent | mixed | Per-capsule memory namespace pointer | **Yes** | `core.py:279-290` |
| `Capsule.persona_config.memory.{recall_limit,similarity_threshold}` | Agent | mixed | Per-capsule recall policy | **Yes** | `core.py:261,407` |
| `SA01_CACHE_WM_LIMIT` | Django | int | Working-memory cache limit | No | `admin/core/helpers/memory.py` |
| `SOMABRAIN_DEFAULT_TENANT` | Env | str | SomaBrain default tenant | No | `infra/aaas/unified_settings.py` |
| `SOMABRAIN_HRR_DIM` | Django | int | HRR vector dim (SomaBrain) | No | `somabrain/settings/cognitive.py:245` |
| `SOMABRAIN_HRR_DTYPE` | Django | str | HRR dtype | No | `somabrain/settings/cognitive.py` |
| `SOMABRAIN_QUANTUM_DIM` | Django | int | Quantum/HRR quantum dim | No | `somabrain/settings/cognitive.py:274` |

### 9.4 C4 — LLM

| Key | Owner | Type | Description | Capsule-overridable | Source |
|---|---|---|---|---|---|
| `DEFAULT_CHAT_MODEL_PROVIDER` | Django | str | Default chat provider | **Yes** | `config/settings.py:100`, `settings_model.py:37-39` |
| `DEFAULT_CHAT_MODEL_NAME` | Django | str | Default chat model name | **Yes** | `config/settings.py:101` |
| `DEFAULT_UTIL_MODEL_PROVIDER` | Django | str | Default utility provider | **Yes** | `config/settings.py:102` |
| `DEFAULT_UTIL_MODEL_NAME` | Django | str | Default utility model | **Yes** | `config/settings.py:103` |
| `DEFAULT_EMBED_MODEL_PROVIDER` | Django | str | Default embedding provider | **Yes** | `config/settings.py:104` |
| `DEFAULT_EMBED_MODEL_NAME` | Django | str | Default embedding model | **Yes** | `config/settings.py:105` |
| `DEFAULT_VOICE_MODEL` | Django | str | Default voice model | **Yes** | `config/settings.py:99`, `services/gateway/settings.py:309` |
| `AAAS_DEFAULT_CHAT_MODEL` | Django | str | AAAS default chat model | No | `services/gateway/settings.py:198` |
| `LLM_CONNECT_TIMEOUT_S` | Django | float | LLM connect timeout (`SA01_LLM_CONNECT_TIMEOUT`) | No | `config/settings.py:88` |
| `LLM_READ_TIMEOUT_S` | Django | float | LLM read timeout | No | `config/settings.py:89` |
| `LLM_MAX_RETRIES` | Django | int | LLM max retries | No | `config/settings.py:90` |
| `LLM_RETRY_BASE_DELAY_S` | Django | float | Retry base delay | No | `config/settings.py:91` |
| `LLM_RETRY_BACKOFF_CAP_S` | Django | float | Retry backoff cap | No | `config/settings.py:92` |
| `LLM_RETRY_AFTER_CAP_S` | Django | float | Retry-After cap | No | `config/settings.py:93` |
| `LLM_HTTP_TIMEOUT` | Django | float | Legacy LLM HTTP timeout | No | `services/common/llm_adapter.py` |
| `SA01_LLM_API_URL` | Env | str | Internal LLM API URL | No | `services/gateway/settings.py:307` |
| `SA01_LLM_BASE_URL` | Env | str | LLM base URL | No | `services/gateway/providers.py` |
| `SA01_LLM_MODEL` | Env | str | LLM model override | **Yes** | `admin/core/api/llm.py` |
| `SA01_VISION_MODEL` | Env | str | Vision model name | **Yes** | `services/common/asset_critic.py` |
| `SA01_GEMINI_COMPAT_ENABLED` | Django | bool | Gemini compat shim | No | `services/common/llm_compatibility.py` |
| `SA01_JSON_CLEANING_ENABLED` | Django | bool | JSON cleaning shim | No | `services/common/llm_compatibility.py` |
| `chat_model_provider` / `chat_model_name` / `chat_model_api_base` | Agent | str | Chat model binding | **Yes** | `settings_model.py:37-43` |
| `chat_model_kwargs` | Agent | dict | Chat model kwargs (e.g. temperature) | **Yes** | `settings_model.py:44` |
| `chat_model_ctx_length` | Agent | int | Chat context length | **Yes** | `settings_model.py:45` |
| `chat_model_ctx_history` | Agent | float | History share of context | **Yes** | `settings_model.py:46` |
| `chat_model_vision` | Agent | bool | Chat vision capability | **Yes** | `settings_model.py:47` |
| `chat_model_rl_requests` / `rl_input` / `rl_output` | Agent | int | Chat rate limits | **Yes** | `settings_model.py:48-50` |
| `util_model_*` (provider, name, api_base, ctx_length, ctx_input, kwargs, rl_*) | Agent | mixed | Utility model binding | **Yes** | `settings_model.py:52-64` |
| `embed_model_*` (provider, name, api_base, kwargs, rl_*) | Agent | mixed | Embedding model binding | **Yes** | `settings_model.py:66-76` |
| `browser_model_*` (provider, name, api_base, vision, rl_*, kwargs, http_headers) | Agent | mixed | Browser model binding | **Yes** | `settings_model.py:79-91` |
| `chat_model_id` | Agent | id | LLMModelConfig FK for chat slot | **Yes** | `admin/llm/api.py:529`; Capsule.chat_model FK |
| `utility_model_id` | Agent | id | LLMModelConfig id for utility slot | **Yes** | `admin/llm/api.py:519,565` |
| `embedding_model_id` | Agent | id | LLMModelConfig id for embedding slot | **Yes** | `admin/llm/api.py:520,573` |
| `llm_provider_configs` | Agent | dict | Per-provider enable/base_url/model_name/label | **Yes** | `admin/llm/api.py:314,401` |
| `model_presets` | Agent | list | Named slot bundles | **Yes** | `admin/llm/api.py:590,633` |
| `LLMModelConfig.{name,display_name,model_type,provider,api_base}` | Django/Agent | mixed | Model registry identity | Via Capsule FK | `admin/llm/models.py:38-42` |
| `LLMModelConfig.{capabilities,priority,cost_tier,domains}` | Django/Agent | mixed | Capability-based routing | Via Capsule FK | `admin/llm/models.py:45-64` |
| `LLMModelConfig.{ctx_length,limit_requests,limit_input,limit_output}` | Django/Agent | int | Model limits | Via Capsule FK | `admin/llm/models.py:67-70` |
| `LLMModelConfig.{vision,kwargs,is_active}` | Django/Agent | mixed | Model config flags | Via Capsule FK | `admin/llm/models.py:73-77` |
| `USE_LLM` | Agent | bool | Master LLM switch | **Yes** | `settings_model.py:165` |
| `litellm_global_kwargs` | Agent | dict | LiteLLM global kwargs | **Yes** | `settings_model.py:164` |
| `SA01_CHAT_*` / `SA01_UTIL_*` / `SA01_EMBED_*` / `SA01_BROWSER_*` | Env→Agent | mixed | Env mirrors of the model-binding fields (see `settings_defaults.py:161-244`) | **Yes** | `admin/core/helpers/settings_defaults.py` |

### 9.5 C5 — AGENT

| Key | Owner | Type | Description | Capsule-overridable | Source |
|---|---|---|---|---|---|
| `Capsule.persona_config.knobs.intelligence_level` | Agent | int 1–10 | Intelligence knob | **Yes** | `core.py:259`, `agentiq/derivation.py:49` |
| `Capsule.persona_config.knobs.autonomy_level` | Agent | int 1–10 | Autonomy knob | **Yes** | `core.py:259`, `agentiq/derivation.py:50` |
| `Capsule.persona_config.knobs.resource_budget` | Agent | float $/turn | Resource budget knob | **Yes** | `core.py:259`, `agentiq/derivation.py:51` |
| Derived: `temperature`, `max_tokens`, `rlm_iterations`, `recall_limit`, `model_tier`, `brain_query_enabled` | Agent (derived) | mixed | From intelligence_level | via knobs | `agentiq/settings.py:56-62` |
| Derived: `require_hitl`, `tool_approval`, `egress_allowed` | Agent (derived) | mixed | From autonomy_level | via knobs | `agentiq/settings.py:64-69` |
| Derived: `token_limit`, `cost_tier`, `thinking_budget` | Agent (derived) | mixed | From resource_budget | via knobs | `agentiq/settings.py:70-72` |
| `Capsule.tool_policy.auto_execute` | Agent | list[str] | Tools auto-executed | **Yes** | `core.py:267-277` |
| `Capsule.tool_policy.approval_required` | Agent | list[str] | Tools needing approval | **Yes** | `core.py:267-277` |
| `Capsule.tool_policy.denied` | Agent | list[str] | Denied tools | **Yes** | `core.py:267-277` |
| `Capsule.capabilities` | Agent | M2M | Enabled tools / MCP servers | **Yes** | `core.py:243-248` |
| `TOOL_REWARD_SUCCESS` | Django | float | Tool success reward (SomaBrain FeedbackRequest.utility) | **Yes** | `config/settings.py:79` |
| `TOOL_REWARD_FAILURE` | Django | float | Tool failure reward | **Yes** | `config/settings.py:80` |
| `SOMABRAIN_CONTEXT_CONFIDENCE_DEFAULT` | Django | float | Default context confidence | **Yes** | `config/settings.py:81-83` |
| `agent_profile` | Agent | str | Agent profile name | **Yes** | `settings_model.py:126` |
| `agent_memory_subdir` | Agent | str | Memory subdir | **Yes** | `settings_model.py:127` |
| `agent_knowledge_subdir` | Agent | str | Knowledge subdir | **Yes** | `settings_model.py:128` |
| `shell_interface` | Agent | str | Shell interface (`local`/`ssh`) | **Yes** | `settings_model.py:138` |
| `SA01_TOOL_TIMEOUT_SECONDS` | Django | float | Tool execution timeout | **Yes** | `services/tool_executor/execution_engine.py` |
| `SA01_TOOL_TIMEOUT_SECONDS` circuit knobs (`TOOL_EXECUTOR_CIRCUIT_*`) | Django | mixed | Tool circuit breaker | No | `services/tool_executor/execution_engine.py` |
| `TOOL_EXECUTOR_MAX_CONCURRENT` | Django | int | Max concurrent tools | No | `services/tool_executor/resource_manager.py` |
| `TOOL_FETCH_TIMEOUT` | Django | float | Tool fetch timeout | No | `services/tool_executor/tools.py` |
| `TOOL_WORK_DIR` | Env | str | Tool working directory | No | `services/tool_executor/tools.py` |
| `SA01_MULTIMODAL_POLL_INTERVAL` | Django | seconds | Multimodal poll interval | No | `services/tool_executor/main.py` |
| `mcp_servers` | Agent | str (JSON) | MCP server registry | **Yes** | `settings_model.py:154` |
| `mcp_client_init_timeout` | Agent | int | MCP init timeout | **Yes** | `settings_model.py:155` |
| `mcp_client_tool_timeout` | Agent | int | MCP tool timeout | **Yes** | `settings_model.py:156` |
| `mcp_server_enabled` | Agent | bool | Expose MCP server | **Yes** | `settings_model.py:157` |
| `a2a_server_enabled` | Agent | bool | Expose A2A server | **Yes** | `settings_model.py:159` |
| `variables` | Agent | str | Agent variables blob | **Yes** | `settings_model.py:162` |
| `SA01_ENABLE_MULTIMODAL_CAPABILITIES` | Django | bool | Multimodal capability gate | No | `admin/core/.../process_message.py` |

### 9.6 C6 — PERSONALITY

| Key | Owner | Type | Description | Capsule-overridable | Source |
|---|---|---|---|---|---|
| `system_prompt` | Agent | text | Base cognitive instruction set | **Yes** | `core.py:184,387` |
| `personality_traits` | Agent | dict | Big-Five traits 0.0–1.0 | **Yes** | `core.py:185-187,388` |
| `neuromodulator_baseline` | Agent | dict | Baseline chemical state | **Yes** | `core.py:188-190,389` |
| `neuromodulator_state` | Agent | dict | Last-synced state (dopamine, serotonin, norepinephrine, acetylcholine, last_synced_at) | **Yes** | `core.py:292-302` |
| `learning_config` | Agent | dict | GMD hyperparameters (eta, lambda, alpha) & reward thresholds | **Yes** | `core.py:191-194` |
| `Capsule.persona_config.prompts.injection_prompts` | Agent | list | Injection prompts | **Yes** | `core.py:260` |
| `Capsule.persona_config.prompts.tool_prompts` | Agent | dict | Tool prompts | **Yes** | `core.py:260` |
| `speech_provider` | Agent | str | Speech provider | **Yes** | `settings_model.py:146` |
| `speech_realtime_enabled` | Agent | bool | Realtime speech | **Yes** | `settings_model.py:147` |
| `speech_realtime_model` | Agent | str | Realtime speech model | **Yes** | `settings_model.py:148` |
| `speech_realtime_voice` | Agent | str | Realtime voice | **Yes** | `settings_model.py:149` |
| `speech_realtime_endpoint` | Agent | str | Realtime sessions endpoint | **Yes** | `settings_model.py:150` |
| `stt_model_size` | Agent | str | STT model size | **Yes** | `settings_model.py:141` |
| `stt_language` | Agent | str | STT language | **Yes** | `settings_model.py:142` |
| `stt_silence_threshold` | Agent | float | STT silence threshold | **Yes** | `settings_model.py:143` |
| `stt_silence_duration` | Agent | int | STT silence duration (ms) | **Yes** | `settings_model.py:144` |
| `stt_waiting_timeout` | Agent | int | STT waiting timeout (ms) | **Yes** | `settings_model.py:145` |
| `tts_kokoro` | Agent | bool | Kokoro TTS toggle | **Yes** | `settings_model.py:151` |

### 9.7 C7 — UI

| Key | Owner | Type | Description | Capsule-overridable | Source |
|---|---|---|---|---|---|
| `UISetting` key space (`tenant`, `user_id`, `key`, `value`) | Agent | JSON | Per-tenant / per-user UI preferences (theme, locale, panels) | **Yes** (user/tenant) | `core.py:495-515`, `settings_defaults.py:69-97` |
| `diagram_theme` | Agent | enum | Mermaid diagram theme (`default`/`dark`/`forest`/`neutral`) | **Yes** | `webui/src/views/saas-multimodal-settings.ts:26` |
| `LANGUAGE_CODE` | Django | str | Django language code | No | `services/gateway/settings.py:170` |
| `TIME_ZONE` | Django | str | Default timezone | No | `services/gateway/settings.py:171` |
| `USE_I18N` | Django | bool | i18n enabled | No | `services/gateway/settings.py:172` |
| `LOG_FORMAT` | Django | str | `json` \| console (presentation of logs) | No | `services/gateway/settings.py:407` |

> Note: a dedicated `theme` / `locale` UISetting key was **not** found as a named constant in
> Python. The UI key space is free-form (`UISetting.key`); theme/locale SHALL be expressed as
> UISetting rows and registered here when first named (§10, D-11).

### 9.8 C8 — GOVERNANCE

| Key | Owner | Type | Description | Capsule-overridable | Source |
|---|---|---|---|---|---|
| `AAAS_DEFAULT_TENANT_ID` | Env | str | Default tenant for unauthenticated/dev | No | `config/settings.py:28`, `services/gateway/settings.py:196` |
| `AAAS_DEFAULT_MAX_AGENTS` | Django | int | Tier default max agents | No | `services/gateway/settings.py:201` |
| `AAAS_DEFAULT_MAX_USERS` | Django | int | Tier default max users | No | `services/gateway/settings.py:202` |
| `AAAS_DEFAULT_MAX_TOKENS_MONTHLY` | Django | int | Tier default monthly tokens | No | `services/gateway/settings.py:203` |
| `AAAS_DEFAULT_STORAGE_GB` | Django | float | Tier default storage (GB) | No | `services/gateway/settings.py:204` |
| `SA01_DEFAULT_TOKEN_BUDGET` | Django | int | Default per-turn token budget | **Yes** | `config/settings_registry.py:225` |
| `SA01_FEATURE_PROFILE` | Env | str | Feature profile name | No | `services/gateway/settings.py:229`, `config/settings_registry.py:220` |
| `ENDPOINT_PERMISSIONS` | Django | dict | Endpoint-level permission map (`{perm: [user_ids] | "*"}`); empty = DENY | No | `services/gateway/settings.py:234` |
| `Constitution.content` | Agent | JSON | The supreme law (immutable once signed) | Binding | `core.py:80` |
| `Constitution.rules` (tenant API) | Agent | list[str] | Tenant constitutional rules | Binding | `admin/gateway/api/gateway.py:200-232` |
| `Capsule.constitution_ref` | Agent | dict | Cross-system constitution ref (`checksum`, `url`) | Binding | `core.py:173-175` |
| `Capsule.resource_limits` | Agent | dict | Max wall clock, concurrency, etc. | **Yes** | `core.py:317` |
| `Capsule.persona_config.governance.opa_policies` | Agent | dict | OPA policy bindings | **Yes** | `core.py:412` |
| `Capsule.persona_config.governance.spicedb_relations` | Agent | dict | SpiceDB relation bindings | **Yes** | `core.py:413` |
| Budget metrics (`tokens`, `images`, `tool_calls`, …) | Django/Agent | per metric | Budget gate metrics; exhaustion → HTTP 402 | Per-tenant | `admin/core/budget/gate.py`, `admin/core/budget/registry.py` |

### 9.9 C9 — OBSERVABILITY

| Key | Owner | Type | Description | Capsule-overridable | Source |
|---|---|---|---|---|---|
| `LOG_LEVEL` | Django | str | Root log level | No | `services/gateway/settings.py:409`, `config/settings_registry.py:199` |
| `LOG_FORMAT` | Django | str | `json` \| console | No | `services/gateway/settings.py:407` |
| `SA01_BRIDGE_LOG_LEVEL` | Django | str | Bridge-worker log level | No | `services/bridge_worker/__main__.py` |
| `SA01_OTLP_ENDPOINT` / `OTLP_ENDPOINT` | Env | str | OTLP collector endpoint | No | `admin/core/observability/tracing.py`, workers |
| `SA01_PROMETHEUS_URL` | Env | str | Prometheus URL | No | `services/gateway/settings.py:317` |
| `CONVERSATION_METRICS_HOST` / `CONVERSATION_METRICS_PORT` | Env | str/int | Conversation worker metrics bind | No | `services/conversation_worker/main.py` |
| `DELEGATION_METRICS_HOST` / `DELEGATION_METRICS_PORT` | Env | str/int | Delegation metrics bind | No | `services/delegation_gateway/main.py` |
| `METRICS_HOST` / `METRICS_PORT` | Env | str/int | Delegation gateway metrics bind | No | `services/delegation_gateway/main.py` |
| `TOOL_EXECUTOR_METRICS_HOST` / `TOOL_EXECUTOR_METRICS_PORT` | Env | str/int | Tool executor metrics bind | No | `services/tool_executor/metrics.py` |
| `REPLICATOR_METRICS_HOST` / `REPLICATOR_METRICS_PORT` | Env | str/int | Memory replicator metrics bind | No | `services/memory_replicator/main.py` |
| `SOMA_LOG_LEVEL` | Django | str | SFM log level | No | `somafractalmemory/.../logger.py` |
| `SOMA_LOG_JSON` | Django | bool | SFM JSON logging | No | `somafractalmemory/.../logger.py` |

### 9.10 C10 — INTEGRATION

| Key | Owner | Type | Description | Capsule-overridable | Source |
|---|---|---|---|---|---|
| `SA01_WHISPER_URL` | Env | str | Whisper STT service URL | No | `services/gateway/settings.py:300` |
| `SA01_WHISPER_API_URL` | Env | str | Whisper transcribe endpoint | No | `services/gateway/settings.py:301` |
| `SA01_KOKORO_URL` | Env | str | Kokoro TTS service URL | No | `services/gateway/settings.py:302` |
| `SA01_KOKORO_TTS_URL` | Env | str | Kokoro synthesize endpoint | No | `services/gateway/settings.py:303` |
| `SA01_VOICEVOX_URL` | Env | str | AgentVoiceVox base URL | No | `services/gateway/settings.py:304` |
| `SA01_MERMAID_CLI_URL` | Env | str | Mermaid CLI URL | No | `services/gateway/settings.py:312` |
| `SA01_IMAGE_GEN_URL` | Env | str | Image generation endpoint | No | `services/gateway/settings.py:313` |
| `SA01_DIAGRAM_URL` | Env | str | Diagram render endpoint | No | `services/gateway/settings.py:314` |
| `KEYCLOAK_URL` / `SA01_KEYCLOAK_URL` | Env | str | Keycloak base URL | No | `config/settings.py:21`, `services/gateway/settings.py:327` |
| `KEYCLOAK_REALM` / `SA01_KEYCLOAK_REALM` | Env | str | Keycloak realm | No | `config/settings.py:22`, `services/gateway/settings.py:328` |
| `KEYCLOAK_CLIENT_ID` / `SA01_KEYCLOAK_CLIENT_ID` | Env | str | Keycloak client id | No | `config/settings.py:23`, `services/gateway/settings.py:329` |
| `SA01_JWT_JWKS_URL` | Env | str | JWKS URL | No | `services/gateway/settings.py:340` |
| `SA01_JWT_ALGORITHMS` | Env | csv str | Accepted JWT algorithms | No | `services/gateway/settings.py:341` |
| `SA01_JWT_LEEWAY` | Django | int | JWT clock leeway (s) | No | `services/gateway/settings.py:342` |
| `JWT_ALGORITHM` / `JWT_AUDIENCE` / `JWT_ISSUER` | Django | str | Derived JWT parameters | No | `services/gateway/settings.py:334-336` |
| `GOOGLE_CLIENT_ID` | Env | str | Google OAuth client id | No | `services/gateway/settings.py:351` |
| `GOOGLE_REDIRECT_URI` | Env | str | Google OAuth redirect URI | No | `services/gateway/settings.py:353` |
| `GOOGLE_JAVASCRIPT_ORIGIN` | Env | str | Google OAuth JS origin | No | `services/gateway/settings.py:354` |
| `WA_BRIDGE_MODE` | Env | str | WhatsApp bridge mode | No | `admin/bridges/services/whatsapp_bridge.py` |
| `WA_BRIDGE_BASE_URL` | Env | str | WhatsApp bridge base URL | No | `admin/bridges/services/whatsapp_bridge.py` |
| `WA_BRIDGE_PORT` | Env | int | WhatsApp bridge port | No | `admin/bridges/services/whatsapp_bridge.py` |
| `WA_BRIDGE_SESSION_DIR` | Env | str | WhatsApp session dir | No | `admin/bridges/services/whatsapp_bridge.py` |
| `WA_BRIDGE_MEDIA_DIR` | Env | str | WhatsApp media dir | No | `admin/bridges/services/whatsapp_bridge.py` |
| `WA_BRIDGE_SIDECAR_CMD` | Env | str | WhatsApp sidecar command | No | `admin/bridges/services/whatsapp_bridge.py` |
| `WA_BRIDGE_SIDECAR_DIR` | Env | str | WhatsApp sidecar dir | No | `admin/bridges/services/whatsapp_bridge.py` |
| `WA_CLOUD_PHONE_NUMBER_ID` | Env | str | WhatsApp phone number id | No | `admin/bridges/services/whatsapp_bridge.py` |
| `TG_API_BASE` | Env | str | Telegram API base | No | `admin/bridges/services/telegram_bridge.py` |
| `TG_BRIDGE_MODE` | Env | str | Telegram bridge mode | No | `admin/bridges/services/telegram_bridge.py` |
| `TG_WEBHOOK_URL` | Env | str | Telegram webhook URL | No | `admin/bridges/services/telegram_bridge.py` |
| `SA01_BRIDGE_POLL_INTERVAL` | Django | seconds | Bridge poll interval | No | `services/bridge_worker/main.py` |
| `SA01_BRIDGE_CHANNEL_REFRESH` | Django | seconds | Bridge channel refresh | No | `services/bridge_worker/main.py` |
| `SA01_BRIDGE_MAX_SEND_ATTEMPTS` | Django | int | Bridge max send attempts | No | `services/bridge_worker/dispatcher.py` |
| `SA01_BRIDGE_BACKOFF_BASE` | Django | float | Bridge backoff base | No | `services/bridge_worker/dispatcher.py` |
| `SA01_BRIDGE_BACKOFF_CAP` | Django | float | Bridge backoff cap | No | `services/bridge_worker/dispatcher.py` |
| `CANVAS_SERVICE_URL` | Env | str | Canvas service URL | No | `services/tool_executor/tools.py` |
| `CANVAS_SERVICE_TIMEOUT` | Django | float | Canvas service timeout | No | `services/tool_executor/tools.py` |
| `rfc_auto_docker` | Agent | bool | RFC auto-Docker tunnel | **Yes** | `settings_model.py:131` |
| `rfc_url` | Agent | str | RFC host | **Yes** | `settings_model.py:132` |
| `rfc_port_http` | Agent | int | RFC HTTP port | **Yes** | `settings_model.py:134` |
| `rfc_port_ssh` | Agent | int | RFC SSH port | **Yes** | `settings_model.py:135` |
| `SOMABRAIN_VAULT_ADDR` / `SOMABRAIN_VAULT_MOUNT_POINT` / `SOMABRAIN_VAULT_KV_MOUNT` / `SOMABRAIN_VAULT_BYPASS` | Env | mixed | SomaBrain Vault client topology | No | `somabrain/core/security/vault_client.py` |
| `SOMA_VAULT_ADDR` | Env | str | SFM Vault address | No | `somafractalmemory/.../vault_client.py` |
| `AV_SCAN_ENABLED` | Django | bool | Antivirus/content scan capability | No | `admin/gateway/api/gateway.py:245` |

### 9.11 Test-only keys (not product settings)

Listed for traceability; excluded from conformance counts.
`TEST_DB_NAME`, `TEST_DB_USER`, `TEST_DB_PASSWORD`, `TEST_DB_HOST`, `TEST_DB_PORT`, `TEST_DB_DSN`,
`TEST_SOMA_API_TOKEN`, `TEST_AGENT_ID`, `TEST_AUTH_TOKEN`, `TEST_TENANT_ID`, `TEST_USER_ID`,
`TEST_USER_EMAIL`, `TEST_USER_PASSWORD`, `TEST_PG_*`, `TEST_REDIS_URL`, `TEST_MEMORY_HTTP_ENDPOINT`,
`SA01_INFRA_AVAILABLE`, `SOMA_INFRA_AVAILABLE`, `SA01_TEST_TOKEN`, `SA01_WS_URL`, `AGENT_URL`,
`BRAIN_URL`, `SFM_URL` / `SFM_API_URL` / `SFM_ENDPOINT` / `SFM_PORT`, `SOMABRAIN_MEMORY_URL`,
`SOMABRAIN_JWT_SECRET`, `SOMABRAIN_KAFKA_URL`, `SOMABRAIN_OPA_URL`, `SOMABRAIN_REDIS_URL`,
`DJANGO_SETTINGS_MODULE` (process bootstrap).

---

## 10. Drift Register (hardcoded values NOT yet settings)

These are concrete, located literals that currently influence behaviour without a
documented settings authority. Per VIBE §4 they are **not** product defaults; they are gaps.

| ID | Location | Literal / behaviour | Category | Required action |
|---|---|---|---|---|
| D-01 | `somabrain/memory/milvus_client.py:158` | `getattr(settings, "SOMABRAIN_EMBED_DIM", 128)` | MEMORY | Remove the `128` fallback; fail closed or use the settings value. Conflicts with `somabrain/settings/cognitive.py:111` (768) and the seam invariant. |
| D-02 | `somabrain/memory/consolidation.py:194` | `getattr(settings, "SOMABRAIN_EMBED_DIM", 256)` | MEMORY | Second inconsistent fallback (`256`). Same fix as D-01. |
| D-03 | `somafractalmemory/admin/core/services.py:127` | `getattr(settings, "SOMA_VECTOR_DIM", 256)` | MEMORY | Fallback `256` conflicts with `settings/infra.py:73` (768). Fail closed. |
| D-04 | `somabrain/api/endpoints/cognitive.py:102`, `somabrain/api/endpoints/config.py:54` | `HRR_DIM` fallback `512` vs `SOMABRAIN_HRR_DIM` default `8192` (`settings/cognitive.py:245`) | MEMORY | Two names / two fallbacks for one dimension. Unify on `SOMABRAIN_HRR_DIM`. |
| D-05 | `services/common/memory_contract.py:43` | `DEFAULT_MEM_EMBED_DIM = 768` module constant | MEMORY | Acceptable only as last-resort for non-Django scripts; MUST equal the seam dim. Documented here; keep in lockstep with `MEM_EMBED_DIM`. |
| D-06 | `services/common/degraded_memory_queue.py:25` | `DEGRADED_TOPIC = "degradation.events"` module constant | MEMORY | Duplicate of the `MEMORY_DEGRADED_TOPIC` fallback in `config/settings.py:76`. Collapse to one. |
| D-07 | `admin/core/helpers/settings_defaults.py:100-111` | Resolution `ENV > DB > default` | (model) | Contradicts §5 (`Capsule > AgentSetting > Django`). Reconcile or mark as migration shim. |
| D-08 | `admin/core/helpers/settings_model.py` (multiple fields) | Schema fallbacks such as context lengths, thresholds, RFC ports, STT params, `agent_profile="agent0"`, MCP empty registry | LLM / MEMORY / AGENT | These are schema defaults, not settings-backed. Move behavioural ones behind `resolve_setting` so Capsule/AgentSetting can win. |
| D-09 | `admin/core/helpers/settings_model.py:150` | Hardcoded URL `https://api.openai.com/v1/realtime/sessions` as `speech_realtime_endpoint` default | INTEGRATION | Violates R-ENV-01/R-OWN-02 (URL belongs to Env/topology). Remove the literal URL from the schema. |
| D-10 | `admin/core/agentiq/derivation.py:49-51` | Knob defaults `5`, `5`, `0.10` | AGENT | Knob defaults currently live in code. Persist them on Capsule / settings model so they are savable agent behaviour defaults (R-OWN-04). |
| D-11 | UI layer | No named `theme` / `locale` UISetting keys in Python | UI | Register explicit UISetting key names when first used; currently free-form. |
| D-12 | `services/gateway/settings.py:334`, `:170` | `JWT_ALGORITHM = "RS256"`, `LANGUAGE_CODE = "en-us"` literals | SECURITY / UI | Algorithm may stay a platform constant; `LANGUAGE_CODE` should be operator-configurable. |
| D-13 | `admin/core/helpers/capsule_settings.py:54-63` | `KEY_CATEGORY` maps `LLM_*` timeouts/retries to `INFRA` | taxonomy | This document places them in `LLM` (§9.4). Align `KEY_CATEGORY` with this document or amend this table. |
| D-14 | `config/settings.py:199-203` | Dev `CHANNEL_LAYERS` = `InMemoryChannelLayer` vs gateway `RedisChannelLayer` | INFRA | Two Django settings modules disagree on channel transport. Declare which module is authoritative per deployment. |
| D-15 | `somabrain/settings/cognitive.py:111` | Env key is `EMBED_DIM`, not `SOMABRAIN_EMBED_DIM` | MEMORY | Naming mismatch across repos for one dimension. Document the alias explicitly (done above) and converge names. |

---

## 11. Conformance Checklist

An implementation conforms to this settings model when **all** of the following hold.

| # | Requirement | Verification |
|---|---|---|
| K-01 | Every setting is assigned exactly one owner from {Django, Agent, Env, Vault} | Inventory §9 complete; no unmapped key in code |
| K-02 | Env carries only URLs / hosts / ports / addressing namespaces | Grep for behavioural `os.environ` reads outside Django settings load |
| K-03 | Secrets are Vault-owned; no secret literals in source or docs | `SOMA-01-SEC-001` audit + this §8 |
| K-04 | Resolution order is Capsule → AgentSetting → Django → schema fallback | `capsule_settings.resolve_setting` matches §5 |
| K-05 | Agent behaviour defaults are savable on Capsule body/persona | Capsule fields §7.1; `save_capsule_setting` |
| K-06 | Governance constraints bind via Constitution; exactly one active | §7.3; `Constitution.is_active` |
| K-07 | Memory seam reads tunables only via `get_memory_setting` | ARCHITECTURE-INVARIANTS §6 |
| K-08 | `MEM_EMBED_DIM == SOMA_VECTOR_DIM == SOMABRAIN_EMBED_DIM` at runtime | Seam test; no divergent fallbacks (D-01…D-03, D-05, D-15) |
| K-09 | No hardcoded product defaults in documentation | §1.1; drift items tracked in §10 |
| K-10 | `capsule_settings.KEY_CATEGORY` is in sync with §6/§9 | Diff `KEY_CATEGORY` against this document |
| K-11 | Fail-closed on missing required topology; no localhost/credential fallback | `get_required_env`, `MemoryConfigurationError` |
| K-12 | Every drift item in §10 is either fixed or explicitly accepted with an owner | §10 status column |

---

## 12. Summary Counts

Counts below are **inventory table rows** as written in §9 (a row may cover a field family
such as `util_model_*` when the fields share one owner and one resolution path).
`SettingsModel` alone contributes 78 declared fields (`admin/core/helpers/settings_model.py`).

| Category | Inventory rows | Rows marked Capsule-overridable (`**Yes**`) |
|---|---|---|
| C1 INFRA | 66 | 0 |
| C2 SECURITY | 37 | 6 |
| C3 MEMORY | 43 | 22 |
| C4 LLM | 41 | 33 |
| C5 AGENT | 29 | 21 |
| C6 PERSONALITY | 17 | 17 |
| C7 UI | 5 | 1 |
| C8 GOVERNANCE | 14 | 6 |
| C9 OBSERVABILITY | 11 | 0 |
| C10 INTEGRATION | 43 | 5 |
| **Total** | **306** | **111** |

Test-only keys: listed in §9.11 (excluded). Drift items: 15 (§10).

---

## 13. Maintenance

- Any new setting SHALL be added to §9 with owner, category, type, Capsule-overridability,
  and source citation before it is read in production code.
- Any new category SHALL be added to `capsule_settings.CATEGORIES` and §6 together.
- Drift items SHALL be closed by code change or explicitly accepted in §10 with an owner.
- This document SHALL be reviewed on `Next Review` or when the resolution order changes.
