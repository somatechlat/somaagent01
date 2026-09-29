# SOMA-01-DEPLOY-001 — Deployment Model Specification — Standalone and Enterprise

## Document Control

| Field | Value |
|---|---|
| Document Title | Deployment Model Specification — Standalone and Enterprise |
| Document Identifier | SOMA-01-DEPLOY-001 |
| Version | 1.1.0 |
| Date | 2026-09-29 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO/IEC 27001:2022 — Information security management systems; ISO/IEC 42001:2023 — Artificial intelligence management systems |
| Next Review | 2026-12-29 |
| Related | `SOMA-01-DOCS-001.md`, `SOMA-01-QMS-001.md`, `SOMA-01-SEC-001.md`, `SOMA-01-RISK-001.md`, `SOMA-01-AAAS-001.md`, `SOMA-01-ARCH-001.md`, `SOMA-01-SRS-001.md`, `SOMA-SETTINGS-MODEL-001.md` |
| Source of truth | This document for the two deployment models, their identity sources, and the role and profile model of SomaAgent01. |
| Audience | Deployment engineers, security and compliance reviewers, administrators, and any agent acting on somaAgent01 |
| Scope | The Standalone and Enterprise deployment models of SomaAgent01; identity and authentication per model; the role and profile model; boot requirements and refusals; the SomaAgent Hub seam at contract level. |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-09-29 | SomaTech Engineering | Initial issue. Defines the dual deployment model (Standalone and Enterprise), the identity sources for each, the eight-role access model and the profiles it operates on, boot requirements and refusals, and the SomaAgent Hub seam at contract level. Records the gaps between specified intent and current implementation. |
| 1.1.0 | 2026-09-29 | SomaTech Engineering | Records the remediation pass. §3.5 and §6.3 rewritten against the settled topology surface (`SA01_DEPLOYMENT_MODE` is the only selector; `SOMA_AAAS_MODE` removed; `PROD` refuses to be selected as a topology). §5.5 now states one permission vocabulary (`admin/core/authz.py`) instead of three, and the wildcard role is gone. §6.4 closes G-4, G-5, G-6 and G-7 and adds the fail-open seams that were removed: the unauthenticated gateway and Vault credential surface, the gate without an RBAC floor, the `is_admin` / bare-`admin` grant, the `SA01_AUTH_REQUIRED` switch, the `auth_required=False` default, and the vision-check error path that passed itself. |

---

## Normative References

| ID | Reference | Role |
|---|---|---|
| N-1 | `SOMA-01-DOCS-001` | Document Control and Traceability Procedure; rules C-01…C-12 govern this document |
| N-2 | `SOMA-01-QMS-001` | Quality Manual; §7 Document Reference Matrix is the suite registry |
| N-3 | `SOMA-01-SEC-001` | Security Assessment Report; §2 ISO 27001 Annex A control mapping |
| N-4 | `SOMA-01-RISK-001` | Risk Register |
| N-5 | `SOMA-01-AAAS-001` | Soma AAAS Deployment Specification; §2 Deployment Models Overview |
| N-6 | `SOMA-SETTINGS-MODEL-001` | Settings Model and Configuration Inventory |
| N-7 | `docs/standards/SOMA-STD-CODING-001` | Vibe Coding Rules (seven numbered sections; no `Rule NNN` namespace) |
| N-8 | ISO/IEC 27001:2022 | Information security management systems — requirements |
| N-9 | ISO/IEC 27002:2022 | Information security controls — guidance |
| N-10 | ISO/IEC 42001:2023 | Artificial intelligence management system — requirements |
| N-11 | ISO 9001:2015 clause 7.5 | Control of documented information |

---

## 1. Purpose and Scope

### 1.1 Purpose

SomaAgent01 is a standalone, complete enterprise agent stack. Its administration surface
administers the agent itself. This document specifies the two shapes in which that agent is
deployed, what each requires, what never differs between them, the identity source each uses, and
the access model that governs both.

It is written so that a deployer can install the agent and use it within seconds, and so that a
security reviewer can trace every claim to the implementation or see it marked as a gap.

### 1.2 Scope

This document covers:

- The Standalone and Enterprise deployment models
- Identity and authentication per model
- The role and profile model, and the permission vocabulary it targets
- Boot requirements, refusals and degradation posture per model
- The SomaAgent Hub seam at contract level
- Auditability and security parameters
- Gaps between specified intent and current implementation

This document does not cover:

- SomaAgent Hub internals. Hub is a separate product; this codebase links out to it (§7)
- Detailed API schemas
- Operational runbooks (see `SOMA-01-OPS-001`)
- Implementation of the gaps recorded in §6.4

### 1.3 Out of scope — commerce

SomaAgent01 is **not** a commercial software-as-a-service product. It has no billing, no pricing,
no invoices, no payment methods, no purchasable subscription tiers, and no marketplace. Those
surfaces have been removed from this codebase.

Multi-organization operation **is** in scope (§3.3): an Enterprise deployment serves one or more
organizations. That is an isolation and governance concern, not a commercial one. Nothing in this
document implies a sale, a plan upgrade, or a metered charge.

### 1.4 Audience

Deployment engineers; security, audit and compliance reviewers; administrators operating either
model; and any agent acting on somaAgent01.

---

## 2. Definitions

| Term | Definition |
|---|---|
| **Standalone** | A deployment of SomaAgent01 on a single machine as a single all-in-one Docker unit, with local identity and no outbound connection to a management plane. |
| **Enterprise** | A deployment of SomaAgent01 that federates identity and may attach an outbound link to SomaAgent Hub and other organization-wide services. |
| **SomaAgent Hub** | A separate product that manages a fleet of agents. SomaAgent01 links out to it. Not implemented in this codebase. |
| **Organization** | The unit of isolation. One Enterprise deployment serves one or more organizations. Represented by the `Tenant` model, whose docstring is "Organization/company entity" (`admin/aaas/models/tenants.py:21`). |
| **Identity source** | The system that authenticates a person and issues their identity. Local credentials in Standalone; a federated identity provider in Enterprise. |
| **Role** | A named set of authorities granted to a subject within a scope. |
| **Profile** | A persistent configuration record: system defaults, organization settings, or an individual's personal and session state. |
| **Permission** | A single named authority, expressed in the vocabulary of §5.5. |
| **Fail-closed** | Where an authorization decision cannot be made, access is denied. |

**Terminology caution.** `SOMA-01-AAAS-001` §2 and `docs/operations/SOMA-OPS-MODES-001.md` use a
different pair — `STANDALONE` versus `AAAS` — to describe process and infrastructure topology, and
in that material "control plane" means *this application*, not a remote hub. Those are topology
modes (§3.5). This document's Standalone/Enterprise pair is a **deployment model**, orthogonal to
topology. The two vocabularies shall not be conflated.

---

## 3. Deployment Models

### 3.1 Model overview

There is one product, one user interface, one data model and one access model. Deployment model
selects the **identity source** and whether a **Hub is attached**. Nothing else.

| | Standalone | Enterprise |
|---|---|---|
| Topology | One machine, one Docker, all-in-one | The same agent, federated |
| Deploy time | Seconds | Seconds, plus connection configuration |
| Identity source | Local username and password | SSO / identity-provider federation |
| SomaAgent Hub | Not attached | Outbound link (separate product) |
| Organizations | One — itself | One or more |
| Role-based access control | Full | Full |
| Audit trail | Full | Full, plus Hub-reported |
| User interface | — identical — | — identical — |
| Data model | — identical — | — identical — |
| Agent behaviour | — identical — | — identical — |

### 3.2 Standalone

A single machine runs a single all-in-one Docker unit. It must fully work: the agent, its
administration surface, its roles and its audit trail are all live. Installation is a
`docker compose up`; a person then signs in with a username and password and works under their own
profile and role.

Standalone is the default shipping shape. It is intended to be deployable in seconds by a
developer and immediately usable by a person with no prior configuration.

### 3.3 Enterprise

The same agent, federated. At setup the deployment asks for connections — SomaAgent Hub, Single
Sign-On, and other organization-wide services. It serves one or more organizations, so it carries
the full security and auditability parameters of enterprise software.

Enterprise does not remove any Standalone capability. It adds panels and connection points.

### 3.4 What never differs

These are invariant across both models:

1. **Role-based access control.** The role model of §5 applies in full in both models. A
   Standalone deployment is not a single implicit superuser.
2. **The data model.** Organization, agent, user, profile and audit records are the same records.
3. **The audit trail.** Every privileged action is recorded in both models.
4. **Agent behaviour.** The agent does not change its reasoning, tools or memory behaviour with
   deployment model.

This invariance is deliberate. It is the reason the audit story is clean: a reviewer inspects one
access model and one audit schema, and the deployment model appears only as an attribute of the
session and of the identity source.

### 3.5 Mode selection

Topology is selected by exactly one input, `SA01_DEPLOYMENT_MODE`, read once in
`config/settings_registry.py:62` (`MODE_ENV_VAR`) and resolved at `:432`. Its accepted values are
`STANDALONE`, `AAAS`, `AAASMODE` and `DEV` (`config/settings_registry.py:64`). The default is
`STANDALONE`.

The value selects a topology, not an environment:

| Value | Topology loaded | Where |
|---|---|---|
| `STANDALONE` | `_STANDALONE_TOPOLOGY` | `config/settings_registry.py:218`, loaded at `:353` |
| `AAAS`, `AAASMODE` | `_AAAS_TOPOLOGY` | `config/settings_registry.py:255`, loaded at `:387` |
| `DEV` | `_STANDALONE_TOPOLOGY`, with a log line saying so | `config/settings_registry.py:441-443` |
| `PROD` | **refuses to boot** | `config/settings_registry.py:444-452` |

`PROD` is refused deliberately and the refusal states why: *"PROD is an environment, not a
topology."* An environment must not double as a topology selector, because then the same word
means two things and the second one is guessed. `SOMA_AAAS_MODE` used to arbitrate here and is no
longer a configuration input — being in AAAS mode is established by `SA01_DEPLOYMENT_MODE=AAAS`
and nothing else (`config/settings_registry.py:382-383`).

An unknown value raises `VIBE Rule 91 VIOLATION` and does not fall back to a default.

The **deployment model** of this document is a separate concern from topology and is determined by
the configured identity source and by whether a Hub link is attached (§2, §3.1, §7).

---

## 4. Identity and Authentication

### 4.1 Standalone: local username and password

Standalone authenticates a person with a username and password held by the agent itself. The
signed-in subject is assigned roles per §5 and acts under those roles from first login.

The requirement is stated at `admin/auth/api_schemas.py:13` ("Login request with username/password
or OAuth code") and `admin/auth/api_schemas.py:87` ("Email/password login request"), and enforced
at `admin/auth/api.py:102` ("Username and password required").

### 4.2 Enterprise: SSO and federation

Enterprise federates authentication to an identity provider. The subject is asserted by the
provider and mapped to the same roles per §5. A Hub link may additionally report identity and
access events to the Hub.

### 4.3 Session, MFA and lockout

Session lifetime, multi-factor policy and lockout are organization-level settings
(`TenantSettings.mfa_policy`, `TenantSettings.sso_enabled`, `TenantSettings.session_timeout` at
`admin/aaas/models/profiles.py:192-195`), applied identically in both models. Session state is
recorded per subject (`UserSession`, `admin/aaas/models/profiles.py:328`).

### 4.4 Gap — no local credential path exists today

> **GAP.** Stated requirement is local username and password for Standalone. The implementation is
> Keycloak-backed only.

| Claim | Evidence |
|---|---|
| Login accepts username and password | `admin/auth/api_schemas.py:13`, `admin/auth/api_schemas.py:87` |
| Credentials are validated against Keycloak | `admin/common/auth.py:29` (`class KeycloakConfig`), `admin/common/auth.py:54` (`get_keycloak_config`) |
| No local credential store or local password verification exists | `admin/common/auth.py` — single identity implementation |
| Consequence: Standalone still requires an identity-provider process | `services/gateway/settings.py:324` (`SA01_KEYCLOAK_URL` required) |

> **GAP.** The multi-provider SSO catalogue in the user interface has no backing implementation.
> `admin/auth/api_sso.py` is fail-closed and reports so explicitly:
> `admin/auth/api_sso.py:58` ("LDAP/AD validation is not implemented: no directory bind is
> performed"), `admin/auth/api_sso.py:71` (other providers "validation is not implemented"),
> `admin/auth/api_sso.py:94-95` ("SSO configuration persistence is not implemented: no
> configuration store is wired to this endpoint"). OAuth providers Google and GitHub are brokered
> through the identity provider rather than federated directly
> (`admin/auth/api_oauth.py`, `supported_providers = {"google", "github"}`).
>
> This document shall not be read as asserting a working multi-provider SSO. The provider
> abstraction is a gap.

---

## 5. Role and Profile Model

### 5.1 Principles

1. **Fail-closed.** Where an authorization decision cannot be made, access is denied.
2. **Least privilege.** A role carries the minimum authority for its job, and nothing more.
3. **No wildcard role.** Every granted authority is named and therefore traceable. A role that
   grants everything cannot produce a permission trace and is incompatible with auditability
   (§5.6).
4. **Org-scoped.** Authority granted inside one organization does not extend to another. Every
   authorization check and every audit record carries the organization identity (§8).
5. **Separation of duties.** The person who runs an agent is not the person who reconfigures it;
   the person who audits is not the person who acts.

### 5.2 The eight roles

| Role | Scope | Job | Must NOT do |
|---|---|---|---|
| `sysadmin` | System | Runtime: infrastructure, rate limits, model registry, integrations, system-wide defaults, security policy, audit export | Read organization content by default |
| `org_admin` | One organization | Its agents, its users, role assignment within it, its organization settings | Reach outside its organization |
| `agent_owner` | One agent | Configure it: persona, tools, memory policy | Set organization security policy |
| `agent_operator` | One agent | Run it: start, stop, logs, conversations | Reconfigure it |
| `developer` | One organization | Engineering surface of the same administration UI: capsules, tools, models, diagnostics, non-security settings | User management, organization security policy, audit export |
| `trainer` | One agent | Cognitive tuning: neuromodulator levels and persona knobs | Tools, users, security, infrastructure |
| `member` | One organization | Ordinary use of the agent | Configuration |
| `auditor` | System | Read-only across audit and activity records | Any write |

**`developer` and `trainer` are distinct roles.** They were previously at risk of being collapsed
into agent activation modes. They are not the same job:

- **`trainer`** acts on the agent's *cognitive state*. Its subject matter is neuromodulator levels
  — dopamine, serotonin, norepinephrine and related signals — and the persona knobs
  (`intelligence_level`, `autonomy_level`, `resource_budget`). Its surface is real:
  `admin/core/somabrain_client.py:536` (`get_neuromodulators`),
  `admin/core/somabrain_client.py:555` (`update_neuromodulators`),
  `admin/core/chat_orchestrator.py:1308` (`_load_neuromodulators`),
  `admin/core/chat_orchestrator.py:794-795` (`iq.apply_neuromodulators`),
  `webui/src/views/saas-cognitive-panel.ts:2` ("Cognitive Panel (TRN Mode)") and
  `webui/src/views/saas-cognitive-panel.ts:12` (neuromodulator gauges),
  `webui/src/components/saas-brain-panel.ts`. Authorities: `cognitive:view`, `cognitive:edit`.
- **`developer`** acts on the *engineering surface*: capsules, tools, models, diagnostics and
  non-security settings in the same administration interface. It has no cognitive authority and no
  organizational authority.

Granting `developer` must never confer `trainer` authority, nor the reverse.

### 5.3 Rationale per role

| Role | Why it exists | Evidence it already exists |
|---|---|---|
| `sysadmin` | Someone must operate the runtime without being able to read organization content; that separation is what makes the audit trail of the operator meaningful | `infra_admin` with `infra:view`, `infra:configure`, `infra:ratelimit`, `platform:read_metrics` — `admin/core/permissions.py:195` |
| `org_admin` | Administration of one organization's agents and people is a distinct job from operating the system | `tenant_admin` and `tenant_sysadmin` — `admin/core/permissions.py:103`, `admin/auth/api_helpers.py` |
| `agent_owner` | One organization runs many agents; the owner of an agent is not the owner of the organization | `agent_owner`, `admin/core/permissions.py:136` |
| `agent_operator` | Separation of duties: the operator who runs the agent must not be able to reconfigure it | `agent_operator`, `admin/core/permissions.py:156` |
| `developer` | Engineering work in the same administration surface, without granting organizational or security authority | `developer`, `admin/auth/api_helpers.py:69` |
| `trainer` | Cognitive tuning is a specialist activity with its own surface and its own risk | `trainer`, `admin/auth/api_helpers.py:75` |
| `member` | Ordinary use is the common case and must be the least privileged | `user` and `viewer`, `admin/core/permissions.py:171,181` |
| `auditor` | Enterprise requires an independent reader of the record; without this role, the operators audit themselves | `security_auditor`, `admin/core/permissions.py:187` |

### 5.4 Profiles

Profiles are the persistent records these roles act upon. The layering is deliberate: cosmetic
state is never conflated with security state.

| Profile | Purpose | Governing role | Location |
|---|---|---|---|
| `PlatformConfig` | Singleton of system-wide defaults; organization settings merge over it | `sysadmin` | `admin/aaas/models/profiles.py:23` |
| `TenantSettings` | Per-organization policy: MFA, SSO, session timeout, compliance, feature overrides | `org_admin` | `admin/aaas/models/profiles.py:167` |
| `AdminProfile` | Per-operator personal settings and session context: session timeout, notification preferences, last login and IP | Self, audited | `admin/aaas/models/profiles.py:107` |
| `UserPreferences` | Per-person cosmetic state: theme, locale, date format. Never security-relevant | Self | `admin/aaas/models/profiles.py:265` |
| `UserSession` | Session lifecycle and last-login/IP — the record of who was in | System | `admin/aaas/models/profiles.py:328` |
| `ApiKey` | Credential lifecycle: prefix, hash, expiry, last use, revocation | `org_admin` | `admin/aaas/models/profiles.py:367` |

### 5.5 Permission vocabulary

One vocabulary, in `admin/core/authz.py`:

```
system:*     org:*     agent:*     resource:*     cognitive:*     audit:*     identity:*
```

This is no longer a target namespace. It is the only permission vocabulary the product has. The
three that previously disagreed on both role and permission names have been collapsed into it, and
every enforcement site resolves through `admin.core.authz.resolve_action`, which raises on a name
the catalog does not contain and denies rather than defaulting.

The last family is narrow on purpose. `identity:*` holds exactly one permission, `identity:self`
(`admin/core/authz.py:112`) — the principal acting on itself: its own profile, its own MFA, its own
sessions, its own logout. Every role holds it (`_EVERY_PRINCIPAL`, `admin/core/authz.py:294`)
because every authenticated person must be able to do those things to themselves. It is not a
grant over anyone else, and it is the only permission in the catalog that is universal.

Two properties are enforced by construction and pinned by
`tests/unit/test_authz_fail_closed.py`:

- **No wildcards.** A role that grants `"*"` cannot produce a permission trace, so it cannot be
  audited. `admin/core/authz.py:369` asserts that no role grants one. The literal
  `{"id": "admin", "permissions": ["*"]}` that previously sat in the bootstrap role list is gone
  (`admin/aaas/models/profiles.py:86`); bootstrap roles are now derived from
  `ROLE_PERMISSIONS`, so what the platform advertises is what the catalog grants.
- **Level 0 is `SYSTEM`.** `admin/core/authz.py:56` defines `PermissionLevel` as
  `system | org | agent | resource`. It was previously labelled "God Mode"
  (`admin/core/permission_matrix.py:74` records the rename). A permission trace that opens with
  "God Mode" is not a document a reviewer can sign.

**Principals are two kinds and are never mixed.** A *person* holds roles. A *delegation* (an API
key) holds explicit scopes and never inherits its issuer's roles —
`permissions_for_principal` (`admin/core/authz.py:437`) ignores the `roles` argument entirely when
`scopes` is passed, rather than unioning them in. Unioning is exactly the escalation a scope list
exists to prevent.

API keys are issued with a mandatory, non-empty scope list that is validated against the catalog
and may not exceed the issuer (`validate_scopes`, `admin/core/authz.py:532`). Issuance is identical
at both call sites — `sk_` + `secrets.token_urlsafe(32)` (256 bits of CSPRNG), 8-character
`key_prefix` for display, SHA-256 `key_hash` as verifier, plaintext returned exactly once
(`admin/aaas/api/settings.py:89-91`, `admin/gateway/api/gateway.py`). The verifier is not a
credential.

### 5.6 Derivation from current code

No role above is invented. Before this pass the code carried **nine** role names, defined twice and
disagreeing:

- `admin/auth/api_helpers.py:21` `ROLE_PRIORITY`: `aaas_admin`, `tenant_sysadmin`, `tenant_admin`,
  `agent_owner`, `developer`, `trainer`, `user`, `viewer`
- `admin/core/permissions.py:101` `ROLE_PERMISSIONS`: `aaas_super_admin`, `tenant_admin`,
  `agent_owner`, `agent_operator`, `user`, `viewer`, `security_auditor`, `infra_admin`
- `admin/aaas/models/choices.py:23` `TenantRole`: OWNER, ADMIN, MEMBER, VIEWER
- `admin/aaas/models/choices.py:32` `AgentRole`: MANAGER, OPERATOR, VIEWER

Mapping to the eight:

| Role | Collapses | Evidence |
|---|---|---|
| `sysadmin` | `infra_admin` | `admin/core/permissions.py:195` |
| `org_admin` | `tenant_admin` + `tenant_sysadmin` | `admin/core/permissions.py:103`, `admin/auth/api_helpers.py` |
| `agent_owner` | `agent_owner` | `admin/core/permissions.py:136` |
| `agent_operator` | `agent_operator` | `admin/core/permissions.py:156` |
| `developer` | `developer` (widened — was only `agent:activate_dev`) | `admin/auth/api_helpers.py:69` |
| `trainer` | `trainer` | `admin/auth/api_helpers.py:75` |
| `member` | `user` + `viewer` | `admin/core/permissions.py:171`, `:181` |
| `auditor` | `security_auditor` | `admin/core/permissions.py:187` |

`tenant_admin` / `tenant_sysadmin` and `user` / `viewer` were two names each for one job. That
duplication was a defect, not a feature: the same subject received different authority depending
on which table was consulted.

**Status: realized.** The eight are now the only role names, in one place
(`admin/core/authz.py` `ROLE_PRIORITY` / `ROLE_PERMISSIONS`). Retired names grant nothing —
`permissions_for_role` resolves an unrecognized name to the empty set
(`admin/core/authz.py:428`), which is the fail-closed outcome and is pinned by
`tests/unit/test_authz_fail_closed.py`.

Stored values were moved onto the same vocabulary by a data migration,
`admin/aaas/migrations/0002_canonical_role_values.py`, so resolution needs no translation table at
read time — a translation table is exactly where four vocabularies drifted apart. One step in that
migration moves authority and is recorded rather than silent: `viewer` → `member`. The eight roles
have no strictly-read-only seat; that is `auditor`, and it holds authority
(`audit:export`, `org:user_activity`, `org:apikey_read`) a viewer never had and must not be handed
by a migration. Anyone for whom `member` is too much is one `org:assign_roles` away from
`auditor`, which writes nothing.

**Deliberately removed: the wildcard role.** `"aaas_super_admin": ["*"]`
(`admin/core/permissions.py:102`) is gone. A wildcard cannot produce a permission trace, so it
cannot satisfy the auditability requirement that governs this document. Any authority previously
held under it is reassigned to a named role or not held at all.

---

## 6. Boot Requirements and Refusals

### 6.1 Requirements per model

**Specified intent:** Standalone boots as a single all-in-one unit and works with no external
dependencies.

| Dependency | Standalone intent | Enterprise | Behaviour today | Evidence |
|---|---|---|---|---|
| Secret store | Internal to the unit | Enterprise secret management | **Required in every mode; raises** | `services/common/unified_secret_manager.py:37`, `:50` |
| PostgreSQL | Internal to the unit | External | **Required, no default** | `config/settings_registry.py:231`, `:322` |
| Redis | Internal to the unit | External | **Required** | `services/gateway/settings.py:201` |
| Identity provider | Local credentials | Federated | **Required** | `services/gateway/settings.py:324` |
| Cognition / memory | Internal to the unit | External | Soft at client, fail-closed at settings | `admin/core/somabrain_client.py`, `config/settings.py` |
| Policy engines | Absent | Optional | Disabled when unconfigured; **fail-closed when enabled** | `services/common/spicedb_client.py`, `services/common/policy_client.py` |
| Event / vector / model services | Absent | Optional | Degrade via circuit breaker and health flags | `services/common/health_monitor.py`, `services/common/circuit_breaker.py` |

### 6.2 Degradation posture

Authorization policy is fail-closed. Service availability degrades gracefully.

- Policy checks: the role floor always decides. A policy engine is not the authority — it may only
  narrow, and only when attached. An engine that is absent, unreachable or erroring has no opinion
  and grants nothing; an attached engine that fails denies.
  `services/common/policy_client.py` sets `fail_open_default = False`.
- Service health: each checker reports `healthy`, `degraded` or `down`, rolled up per deployment
  (`admin/aaas/api/health.py`). Critical services — cognition, database, model access — put the
  deployment into degraded mode (`services/common/health_monitor.py`).
- Resilience: circuit breakers on the cognition and model paths
  (`services/common/circuit_breaker.py`); memory writes are queued and replayed when cognition is
  unavailable (`services/common/degradation_monitor.py`).

### 6.3 Deployment-mode vocabulary

`config/settings_registry.py` is the source of truth for topology. It holds one mode selector
(`SA01_DEPLOYMENT_MODE`, `MODE_ENV_VAR` at `:62`), one accepted value set
(`_VALID_MODES = ("STANDALONE", "AAAS", "AAASMODE", "DEV", "PROD")` at `:64`), one default
(`STANDALONE`, `:432`) and two topology tables (`_STANDALONE_TOPOLOGY` at `:218`,
`_AAAS_TOPOLOGY` at `:255`). `SOMA_AAAS_MODE` is no longer a configuration input.

`PROD` is refused at `:444-452` with the reason stated in the refusal: *"PROD is an environment,
not a topology."* An unknown value raises rather than falling back (VIBE Rule 91, zero-fallback).

> **GAP (G-3, partial).** Peripheral readers of the mode have not all been reconciled onto that
> enum. They are no longer the authority and cannot change a boot, but they still accept or
> default to names the registry does not:
>
> | Source | Accepted values | Default |
> |---|---|---|
> | `config/settings_registry.py:64` | **authority** — STANDALONE, AAAS, AAASMODE, DEV, PROD | STANDALONE |
> | `services/common/deployment_mode.py:21` | AAAS, STANDALONE, DEV | DEV |
> | `admin/core/config/models.py` | DEV, STAGING, PROD, LOCAL, TEST, AAAS — no `STANDALONE` | — |
>
> These are naming stragglers, not a second decision path: nothing consults them to choose a
> topology. Removing the last of them is the remainder of G-3.

### 6.4 Gap register

#### 6.4.1 Open

| ID | Gap | Evidence | Effect |
|---|---|---|---|
| G-1 | No local credential path; identity is Keycloak-only | `admin/common/auth.py:29`, `:54`; `services/gateway/settings.py:324` | Standalone still requires an identity-provider process |
| G-2 | Multi-provider SSO is a fail-closed stub; UI catalogue unbacked | `admin/auth/api_sso.py:58`, `:71`, `:94-95` | Enterprise SSO beyond the single provider is not implemented |
| G-3 | Peripheral mode readers not yet on the registry enum (partial) | `services/common/deployment_mode.py:21`, `admin/core/config/models.py` | Naming stragglers only; no longer a second decision path — see §6.3 |
| G-8 | Standalone topology still runs external services | `infra/standalone/docker-compose.yml` | Not yet a true single all-in-one unit |
| G-9 | SomaAgent Hub absent from the codebase | repo-wide search: zero occurrences | §7 is contract-only, not implemented |

#### 6.4.2 Closed

Each of these was a live violation, not a design shortfall. "Closed" means the behaviour is gone
and the property is pinned by a test.

| ID | Was | Closed by | Evidence |
|---|---|---|---|
| G-4 | Three competing permission and role vocabularies; same subject got different answers by call site | Collapsed into `admin/core/authz.py`; every enforcement site resolves through `resolve_action`, which denies on an unknown name | `admin/core/authz.py:518`; `tests/unit/test_authz_fail_closed.py` |
| G-5 | Wildcard role `["*"]`, including `{"id": "admin", "permissions": ["*"]}` in the bootstrap roles and three `includes('*')` shortcuts in the webui | No role grants a wildcard; bootstrap roles derived from `ROLE_PERMISSIONS`; webui matches exactly | `admin/core/authz.py:369`, `admin/aaas/models/profiles.py:86`, `tests/unit/test_authz_fail_closed.py::test_no_role_grants_a_wildcard` |
| G-6 | `ApiKey.scopes` never populated — every key was all-or-nothing, and keys were issued but never verified | Mandatory non-empty scopes validated against the catalog and capped at the issuer; `ApiKey.verify` + `decode_token` routing; a key holds scopes and never its issuer's roles | `admin/core/authz.py:532`, `:437`; `admin/aaas/models/profiles.py`; `tests/unit/test_authz_fail_closed.py` |
| G-7 | Level 0 labelled "God Mode" | Renamed `SYSTEM`; `PermissionLevel` is `system \| org \| agent \| resource` | `admin/core/authz.py:56`; `admin/core/permission_matrix.py:74` |
| G-10 | The restricted surface — Vault provider credentials, API-key issuance and revocation, memory migration, constitution writes, A2A dispatch, impersonation — was reachable with identity alone or with no check at all | Each now carries a catalog `authorize()` gate naming a real permission; the route register (`tests/unit/test_route_authorization_coverage.py`) treats this surface as never-debt and fails if any entry is ungated | `admin/secrets/api.py`, `admin/gateway/api/gateway.py`, `admin/core/api/migrate.py`, `admin/auth/api.py::impersonate_tenant` |
| G-11 | Impersonation was gated on Keycloak realm roles named `super_admin` / `aaas_admin` — a role namespace outside the catalog, so the RBAC did not decide | Gate is `system:impersonate`, granted to `sysadmin` and nobody else | `admin/auth/api.py`, `admin/core/authz.py:118`, `:292` |
| G-12 | `is_admin` boolean or a bare `"admin"` scope conferred admin | Admin is now "holds a `PermissionLevel.SYSTEM` permission", decided by the catalog | `services/common/authorization.py:264-281` |
| G-13 | `SA01_AUTH_REQUIRED` could disable authentication by environment variable | Removed. There is no unauthenticated mode and no switch to reach one; `AUTH_REQUIRED = True` is a constant | `services/gateway/settings.py`, `admin/core/config/loader.py:204` |
| G-14 | `auth_required` defaulted to `False`, and its cross-field validator was commented out | Defaults to true; the validator is restored and refuses `False`; the setter refuses `False` | `admin/core/config/models.py:157`, `:317`, `:412` |
| G-15 | `UnifiedGate` had no RBAC floor and allowed every non-tool action by default | `_check_role_floor` runs first and denies without roles; `_check_scope` is a tool-only capability filter, not an authority source | `admin/core/agentiq/unified_gate.py:119`, `:235`, `:438` |
| G-16 | An unconfigured OPA / SpiceDB denied everyone (Standalone could not authorize at all) | An absent engine has no opinion and never narrows; the role floor decides. An engine that is attached may only narrow further | `admin/core/agentiq/unified_gate.py:293`, `:333`, `:414`; `services/common/authorization.py` |
| G-17 | Vision-check error, skip and encode-failure paths returned "passed" | Every path returns `passed=False` with score `0.0` | `services/common/asset_critic.py:344`, `:353`, `:422`, `:429` |
| G-18 | Retired role names (`admin`, `aaas_admin`, `owner`, `viewer`, `user`, `manager`, `operator`) at enforcement sites and in the webui role select | Unrecognized names grant nothing; a data migration moved stored values onto the catalog vocabulary; the role select offers assignable roles only | `admin/aaas/migrations/0002_canonical_role_values.py`, `admin/core/authz.py:428`, `webui/src/views/saas-user-detail.ts` |
| G-19 | API-key prefix and length disagreed between the two issuance sites (one wrote 12 characters into `CharField(max_length=8)` and omitted `sk_`) | One shape at both sites: `sk_` + `secrets.token_urlsafe(32)`, 8-character prefix | `admin/aaas/api/settings.py`, `admin/gateway/api/gateway.py`, `admin/common/auth.py:187` |

---

## 7. SomaAgent Hub Seam (contract level)

### 7.1 What the seam is, and what it is not

SomaAgent Hub is a **separate product**. SomaAgent01 links out to it. This codebase does not
implement Hub and this document does not describe Hub internals.

The seam is the boundary at which this agent presents itself to a management plane and accepts
direction from it. It is specified here so that the two products can be built independently
against a stable contract.

### 7.2 Contract surface

| Interaction | Direction | Purpose |
|---|---|---|
| Enrolment | Agent → Hub | Present identity and deployment attributes; receive a managed-agent identifier |
| Heartbeat | Agent → Hub | Report liveness and health, so a fleet view is truthful |
| Policy receipt | Hub → Agent | Receive policy this deployment must apply |
| Identity and access reporting | Agent → Hub | Report privileged actions for fleet-level audit |

Each interaction must be authenticated, must carry the organization identity, and must be recorded
in the local audit trail — the Hub link is never a bypass of local auditability.

### 7.3 Status

> **GAP (G-9).** SomaAgent Hub does not appear anywhere in this repository. There is no enrolment,
> heartbeat or policy-receipt code. This section is a contract to be implemented, not a
> description of existing behaviour.

---

## 8. Auditability and Security Parameters

Enterprise software is judged on whether a reviewer can reconstruct who did what, to which
organization's data, under which authority, and whether that record can be tampered with.

Requirements:

1. **Every privileged action is recorded**, with subject, role, authority exercised, target and
   organization identity.
2. **Every authorization check carries the organization identity.** Authority granted inside one
   organization does not extend to another. This is the property that makes multi-organization
   operation safe, and it must be visible on the check itself, not inferred.
3. **The audit record is append-only.** `admin/aaas/models/audit.py` records actor, action,
   resource and tenant; indexes support actor and tenant reconstruction.
4. **The auditor role is independent.** `auditor` reads the record and writes nothing.
5. **Break-glass is explicit and recorded.** Where `sysadmin` must reach organization content, the
   access is named, time-bounded and written to the audit trail with operator and target. It is
   never an ambient right.
6. **Secrets are held in the secret manager**, never in the database or the environment, and a
   secret-shaped key may hold only a reference. This is enforced at write time
   (`services/common/unified_secret_manager.py:37`).
7. **Authorization is fail-closed** (§6.2).

Both deployment models carry these parameters. The Enterprise model adds Hub reporting on top; it
does not substitute Hub reporting for the local trail.

---

## 9. Traceability

| ID | Requirement | Priority | Source | Verification |
|---|---|---|---|---|
| REQ-DEPLOY-001 | The product shall deploy in two models: Standalone and Enterprise | Must | §3.1 | Deployment of each model succeeds |
| REQ-DEPLOY-002 | Standalone shall be a single machine, single all-in-one unit | Must | §3.2 | Single compose unit provisions and serves |
| REQ-DEPLOY-003 | Standalone shall authenticate with a local username and password | Must | §4.1 | Sign-in succeeds with local credentials |
| REQ-DEPLOY-004 | Enterprise shall federate authentication to an identity provider | Must | §4.2 | Federated sign-in succeeds |
| REQ-DEPLOY-005 | Full role-based access control shall apply in both models | Must | §3.4 | Role enforcement observed in both |
| REQ-DEPLOY-006 | The data model, user interface and agent behaviour shall not vary by model | Must | §3.4 | Structural comparison |
| REQ-DEPLOY-007 | Eight roles shall exist, as specified | Must | §5.2 | Role table matches §5.2 |
| REQ-DEPLOY-008 | `developer` and `trainer` shall be distinct and non-substitutable | Must | §5.2 | Granting one confers neither the other's authority |
| REQ-DEPLOY-009 | No role shall grant a wildcard authority | Must | §5.1, §5.6 | No role carries `*` |
| REQ-DEPLOY-010 | Permission checks shall carry the organization identity | Must | §8 | Check and audit record both carry it |
| REQ-DEPLOY-011 | Authorization shall be fail-closed | Must | §5.1, §6.2 | Denied where undecidable |
| REQ-DEPLOY-012 | Every privileged action shall be recorded in the audit trail | Must | §8 | Audit row per privileged action |
| REQ-DEPLOY-013 | API keys shall be issued with explicit scopes from the permission vocabulary | Should | §5.5 | Key narrower than its issuer is issuable |
| REQ-DEPLOY-014 | The deployment-model vocabulary shall be one enum with one default | Should | §6.3 | Single source of truth for the mode |
| REQ-DEPLOY-015 | The Hub seam shall be authenticated, org-scoped and locally audited | Should | §7.2 | Each interaction meets all three |
| REQ-DEPLOY-016 | The product shall contain no commerce surface | Must | §1.3 | No billing, pricing, invoicing or purchasable tier |

---

## 10. Verification

| Check | Method |
|---|---|
| Document control complete | All ten mandatory fields present and non-empty; `Status` and `Classification` within their closed sets; `Approver` and `Next Review` present |
| Register agreement | `make docs-register` then `make docs-check` passes rules C-01…C-12 |
| QMS agreement | A row for `SOMA-01-DEPLOY-001` exists in `SOMA-01-QMS-001` §7 |
| Evidence cited | Every gap claim names `file` and line |
| No commerce vocabulary | No billing, pricing, invoice, payment or purchasable-tier term appears in this document |
| No invented control fields | No field from the prohibited list of `SOMA-01-DOCS-001` §3.1 |

End of Document
