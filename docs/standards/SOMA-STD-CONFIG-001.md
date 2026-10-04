# SOMA-STD-CONFIG-001 — Configuration and Service Endpoint Resolution

## Document Control

| Field | Value |
|---|---|
| Document Title | SOMA-STD-CONFIG-001 — Configuration and Service Endpoint Resolution |
| Document Identifier | SOMA-STD-CONFIG-001 |
| Version | 1.0.0 |
| Date | 2026-10-03 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-28 |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-03 | SomaTech Engineering | Initial issue. Normative four-step configuration pattern, resolution chain, Vault/Django/AgentSetting custody, fail-closed endpoint rule, worked example, anti-patterns. |

## Normative References

| ID | Reference | Role |
|---|---|---|
| N-1 | `docs/standards/SOMA-STD-CODING-001.md` | VIBE rules: §2 check first, §4 no hardcoded values, fail-closed Rule 91 |
| N-2 | `docs/iso/SOMA-SETTINGS-MODEL-001.md` | Settings model, category taxonomy, inventory |
| N-3 | `docs/iso/SOMA-01-DOCS-001.md` | Document control and traceability procedure |
| N-4 | `admin/core/helpers/settings_model.py` | Schema: one field per tunable, `_dj` default factory |
| N-5 | `admin/core/helpers/capsule_settings.py` | Resolution order and `KEY_CATEGORY` |
| N-6 | `admin/core/helpers/service_urls.py` | `require_service_url` / `require_setting` |
| N-7 | `admin/core/helpers/vendor_api_bases.py` | Vendor public API **protocol constants** |
| N-8 | ARCHITECTURE-INVARIANTS §6 | Memory seam fail-closed; no localhost substitute |

---

## 1. Purpose and Scope

This standard defines **how every tunable value and every deployment URL is
declared, registered, read and refused** in somaAgent01.

In scope:

- deployment service endpoints (this product's own services and sidecars);
- behavioural tunables (timeouts, limits, thresholds, rate windows);
- vendor public API bases (protocol constants) and their effective override;
- tenant / authz identity fallbacks;
- the custody split between Vault, Django settings, AgentSetting and Capsule.

Out of scope:

- concrete production values (that is deployment configuration);
- third-party library environment variables;
- test-only fixtures (`TEST_*`).

Where this standard and a call site disagree, this standard wins. Where this
standard and `SOMA-SETTINGS-MODEL-001` disagree on the *model*, the model
document wins; this standard is normative for *how code resolves* values.

---

## 2. The four-step pattern (normative)

Every tunable value and every deployment URL **shall** be:

1. **Declared once** on `admin/core/helpers/settings_model.py` as a field with
   `default_factory=lambda: …_dj("UPPER_NAME", default)`.
   - The schema default is the **last** layer, never a guessed host for a
     deployment URL. URL schema defaults are the empty string.
   - Behavioural tunables carry their honest schema default (the value a
     standalone unit test may rely on), named in one place only.
2. **Registered** in `admin/core/helpers/capsule_settings.py` `KEY_CATEGORY`
   under the **UPPER Django name** (that is what `getattr(settings, key)`
   finds) so Capsule and AgentSetting can override it.
3. **Read** through `admin.core.helpers.settings.get_settings()` or
   `admin.core.helpers.capsule_settings.resolve_setting()`. Deployment URLs
   that must exist are read through
   `admin.core.helpers.service_urls.require_service_url()`.
4. **Never** a bare literal at a call site, never
   `getattr(settings, X, "http://localhost…")`, never a guessed host, never a
   second copy of the default.

```
Call site
   │
   ├─ require_service_url("UPPER_NAME")   → URL or ImproperlyConfigured
   ├─ require_setting("UPPER_NAME")       → value or ImproperlyConfigured
   ├─ get_settings().field                → SettingsModel view
   └─ resolve_setting("UPPER_NAME", …)    → one key, full chain
```

### 2.1 Why the KEY_CATEGORY key is the UPPER Django name

`resolve_setting(key)` does `getattr(django_settings, key)`. Django settings
attributes are UPPER_SNAKE. A KEY_CATEGORY entry of `somabrain_url` would never
match `settings.SOMABRAIN_URL`, so Capsule/AgentSetting overlays would appear
to work in the API and silently fail at runtime. The key is the **same string**
operators put in Django settings / env, and the same string AgentSetting rows
store. `SettingsModel` fields are the snake_case *schema view* of that name
(`SOMABRAIN_URL` → `service_somabrain_url`); `require_service_url` maps between
them.

---

## 3. Resolution chain (normative)

Highest wins:

```
1. Capsule.persona_config["settings"][CATEGORY][UPPER_NAME]   (agent identity)
2. AgentSetting ORM  (agent_id, UPPER_NAME)                   (runtime override)
3. Django settings   / SettingsModel                          (infra authority)
4. Schema default on SettingsModel                            (optional keys only)
```

Implementation: `admin/core/helpers/capsule_settings.resolve_setting` and
`admin.core.helpers.settings.get_settings`. There is **one** chain. A second
lookup path is a second source of truth.

For deployment URLs, layer 4 is empty. Absence is misconfiguration, not a
licence to invent a host.

---

## 4. What lives where

| Kind of value | Custody | Example |
|---|---|---|
| Credentials, tokens, passwords, API keys | **Vault only** (VIBE 164). AgentSetting may store a *Vault path* (`is_secret=True`), never the secret. | `llm_api_key`, `django_secret_key`, `somabrain_memory_http_token` |
| Deployment topology (hosts, ports, service URLs, broker lists) | Django settings (env override) → AgentSetting → Capsule. Declared on SettingsModel. | `SOMABRAIN_URL`, `OPA_URL`, `KAFKA_BOOTSTRAP_SERVERS`, `WHISPER_API_URL` |
| Behavioural tunables (timeouts, limits, thresholds, rate windows) | Same chain as topology. Schema default is honest and unique. | `TOOL_EXEC_TIMEOUT_S`, `MEM_SIMILARITY_THRESHOLD`, `LOGIN_RATE_LIMIT` |
| Agent identity / persona behaviour | Capsule `persona_config["settings"][CAT][KEY]` | `system_prompt`, `memory_recall_top_k` |
| Vendor public API bases (protocol constants) | `admin/core/helpers/vendor_api_bases.py` only. Effective base overridable (proxy / region). | `https://api.openai.com/v1`, `https://api.telegram.org` |
| Process environment | 12-factor override of Django settings for URLs/hosts/ports and non-secret tunables. **Never** secrets. | `SA01_WHISPER_URL`, `MEM_EMBED_DIM` |

`os.environ` is not a general config store. `config/settings.py` /
`services/gateway/settings.py` read env **once** into Django settings; code
below that layer reads Django settings / SettingsModel.

---

## 5. Fail-closed rule for missing endpoints (normative)

A service endpoint that is not configured **raises**. It does not default to
`localhost`, `127.0.0.1`, a docker hostname, or an empty call.

- Use `require_service_url("UPPER_NAME")` (shared helper in
  `admin/core/helpers/service_urls.py`). Do not re-implement it.
- Use `require_setting("UPPER_NAME")` for required non-URL topology (broker
  lists, names).
- Health endpoints may report `down` for an unconfigured dependency; they must
  not invent a URL to probe.
- Authorization and memory paths treat a missing **tenant** as **deny/raise**.
  There is no `or "default"`.

Rationale: a guessed host is a URL an operator cannot change and a reviewer
cannot see. It also turns "not configured" into "wrong service answered".

---

## 6. Vendor public API bases (protocol constants)

Third-party public API bases are **protocol constants**: the host and path
prefix the vendor documents. They are not this product's deployment topology.

- They live in exactly one module:
  `admin/core/helpers/vendor_api_bases.py`, with a module docstring saying so.
- Call sites import the constant (or use `effective_base(constant, override)`).
- The **effective** base is configurable: model `api_base`, channel config, or
  env override wins when set, so an operator can point traffic at a proxy or a
  regional endpoint. When no override is set, the protocol constant is used
  unchanged.

Ollama's `http://localhost:11434/v1` is the documented default listen address
of a **local** runtime, kept as a UI preset seed only. The effective base must
still come from `LLMModelConfig.api_base` or an operator override.

---

## 7. Worked example — adding a service endpoint

Goal: the platform must call a new `Foo` service.

1. **Declare** on `SettingsModel`:

```python
service_foo_url: str = Field(default_factory=lambda: str(_dj("FOO_URL", "")))
```

2. **Register** in `KEY_CATEGORY`:

```python
"FOO_URL": CATEGORY_INFRA,
```

3. **Read** at the call site:

```python
from admin.core.helpers.service_urls import require_service_url

foo_base = require_service_url("FOO_URL")
async with httpx.AsyncClient(timeout=… ) as client:
    response = await client.post(f"{foo_base}/run", …)
```

4. **Never** write:

```python
foo_base = getattr(settings, "FOO_URL", "http://localhost:9999")  # forbidden
```

Operators set `FOO_URL` in Django settings / env / AgentSetting / Capsule.
Unit tests set `django.conf.settings.FOO_URL` or the AgentSetting row. The
schema default stays empty; `require_service_url` raises until someone
configures it.

---

## 8. Anti-patterns (forbidden — never repeat)

| Anti-pattern | Why it is forbidden | Do this instead |
|---|---|---|
| Invented key names (`"SOMA_BRAIN_URL"`, `"whisper"` in KEY_CATEGORY) | Overlay layers never match `getattr(settings, …)` | UPPER Django name only |
| `getattr(settings, X, "http://localhost…")` | Guesses a host when the setting is absent; hides misconfiguration | `require_service_url("X")` |
| `or "http://127.0.0.1:3100"` / `f"http://127.0.0.1:{port}"` fallback | Same as above, for sidecars | Require `BRIDGE_BASE_URL` / channel config |
| Duplicated defaults (`= 10` at two call sites, or default in both settings.py **and** a getattr) | Drift; one site silently wins | One schema default on SettingsModel |
| `or "default"` / `or ""` on authz or memory tenant paths | Evaluates the request as the wrong subject | Raise / deny |
| `os.environ.get("…", "http://…")` inside business logic | Second config store; bypasses Capsule/AgentSetting | Django settings → SettingsModel |
| Re-implementing `require_service_url` in a router | Two behaviours for one rule | Import the shared helper |
| Vendor URL pasted at a call site | External host not reviewable in one place | `vendor_api_bases` constant + `effective_base` |
| Empty-string secret default (`API_KEY or ""`) | Sends `Bearer ` to a real service | Missing credential raises (Rule 164) |
| A field that holds a credential and is never read | Secret store with a friendly name | Delete the field; Vault owns secrets |

---

## 9. Conformance

- `python3 -m pytest tests/unit -q --deselect tests/unit/test_identity_local_login.py`
  includes `test_no_silent_default_tenant.py`, `test_no_hardcoded_chat_config.py`
  and `test_settings_conformance.py`.
- `python3 -m compileall admin services config -q` after every edit.
- `make docs-check` for document control.

A new tunable that appears as a literal in a router, consumer or worker is a
conformance failure, not a style preference.

---

## 10. Traceability

| Requirement | Evidence |
|---|---|
| Four-step pattern | `admin/core/helpers/settings_model.py`, `capsule_settings.py`, `service_urls.py` |
| Resolution chain | `capsule_settings.resolve_setting`, `settings.get_settings` |
| Fail-closed endpoints | `service_urls.require_service_url` raises `ImproperlyConfigured` |
| Vendor protocol constants | `admin/core/helpers/vendor_api_bases.py` |
| No silent default tenant | `tests/unit/test_no_silent_default_tenant.py`; assets/idempotency/tool-validation raise |
| No hardcoded chat config | `tests/unit/test_no_hardcoded_chat_config.py` |
