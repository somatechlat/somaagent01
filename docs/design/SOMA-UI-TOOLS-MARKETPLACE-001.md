# SOMA-UI-TOOLS-MARKETPLACE-001 — Tools Administration & Marketplace

## Document Control

| Field | Value |
|---|---|
| Document Title | Tools Administration, Marketplace & Connector Suite |
| Document Identifier | SOMA-UI-TOOLS-MARKETPLACE-001 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9241-210:2019 · ISO 9001:2015 §7.5 |
| Next Review | 2027-01-13 |
| Source of truth | `admin/tools/` · `services/tool_executor/` · `admin/core/models.Capability` · `Capsule.tool_policy` |
| Related | `SOMA-ARCH-TOOLS-001` · `SOMA-UI-PROFILE-001` · `SOMA-UI-I18N-001` · `SOMA-UI-MODULE-CATALOG-001` |
| Law | Soma law: NO SHIMS/FAKES/MOCKS/STUBS. Real APIs only. Honest GATED. No emojis. I18N strings. |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | SomaTech Engineering | Initial: Tools admin + Marketplace + Connectors + per-tool permissions. |

---

## 1. Product model (why)

Agents work with **tools** and **connectors**. After login, the user:
1. Opens **Tools** (marketplace catalog)
2. **Installs** tools for the agent (Drive, Mail, Photos, WhatsApp, GitHub…)
3. Grants **permissions** per tool (scope + policy)
4. The agent can then search / act through those tools under policy.

**Technical:** install = link `Capability` to agent + `tool_policy` + (connector) OAuth/session.  
**UI name:** Tools · Marketplace · Connectors — never “Capsule” in UI.

---

## 2. Information architecture

```
Settings · Tools
├─ Installed on this agent     (Hands)
├─ Marketplace                 (catalog)
└─ Connectors                  (Mail, Drive, Photos, WhatsApp, …)

Tools (full page / modal)      ← main admin surface
├─ My tools (installed)
├─ Catalog (marketplace)
├─ Connectors & accounts
└─ Permissions matrix
```

**Entry points (≤1 click):** Settings › Tools · Welcome · Command palette (later) · Profile does **not** duplicate Tools.

---

## 3. WIREFRAME — Tools marketplace (full window)

```
┌ Tools ──────────────────────────────────────────────────── [×] ┐
│ [Installed 12] [Catalog] [Connectors] [Permissions]            │
├────────────────────────────────────────────────────────────────┤
│ 🔍 Search tools…     category [All ▾]   tier [All ▾]  [Install]│
│                                                                │
│  ┌─ Google Drive ────────┐ ┌─ Gmail ─────────────────────┐   │
│  │ storage · connector   │ │ mail · connector            │   │
│  │ Read/write files      │ │ Read/send email             │   │
│  │ [Connect] [Install]   │ │ [Connect] [Install]         │   │
│  └───────────────────────┘ └─────────────────────────────┘   │
│  ┌─ Photos ──────────────┐ ┌─ WhatsApp ──────────────────┐   │
│  │ image · connector     │ │ messaging · connector       │   │
│  │ [Connect] [Install]   │ │ [Connect] [Install]         │   │
│  └───────────────────────┘ └─────────────────────────────┘   │
│  ┌─ web_search ──────────┐ ┌─ file_read ─────────────────┐   │
│  │ tier 2 · core         │ │ tier 1 · core               │   │
│  │ [Install] · policy    │ │ Installed · policy          │   │
│  └───────────────────────┘ └─────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘

MODAL Install tool
│ tool: google_drive · tier 2 · category connector               │
│ permissions: [ ] read files  [ ] write files  [ ] list folder   │
│ policy: ( Needs approval ▾ )  Auto | Needs approval | Deny      │
│ connector: [Connect Google account]  (OAuth — scopes listed)    │
│ [Cancel] [Install & enable]                                    │

MODAL Connector OAuth
│ Scopes: drive.readonly · drive.file                            │
│ Account: name@company.com                                      │
│ [Allow] [Cancel]                                               │
```

---

## 4. Control map (TM-* marketplace · CN-* connectors)

### 4.1 Shell

| ID | Label | Type | Binding | Status |
|---|---|---|---|---|
| TM-01 | Tabs | tabs | Installed/Catalog/Connectors/Permissions | PLANNED |
| TM-02 | Search | input | filter | PLANNED |
| TM-03 | Category / tier filters | select | filter | PLANNED |

### 4.2 Catalog card

| ID | Label | Type | Binding | Status |
|---|---|---|---|---|
| TM-10 | Tool name + desc | card | `GET /tools/catalog` | LIVE (core) |
| TM-11 | Install | button | install+link Capability | PLANNED |
| TM-12 | Policy | select | `tool_policy` | PLANNED |
| TM-13 | Uninstall | button | unlink | GATED (no unlink API) |
| TM-14 | Inspect | button | schema modal | PLANNED |

### 4.3 Connector

| ID | Label | Type | Binding | Status |
|---|---|---|---|---|
| CN-01 | Connect | button | OAuth / `PUT /secrets/providers/{id}` | PLANNED |
| CN-02 | Scopes list | readout | provider config | PLANNED |
| CN-03 | Connected account | chip | OAuth session | PLANNED |
| CN-04 | Disconnect | button | revoke | PLANNED |
| CN-05 | Test | button | provider ping | PLANNED |

### 4.4 Permissions

| ID | Label | Type | Binding | Status |
|---|---|---|---|---|
| PM-01 | Per-tool permission checkboxes | checkbox | install modal / policy | PLANNED |
| PM-02 | Role matrix | table | RBAC `authz.py` | LIVE (admin) |
| PM-03 | HITL / approval | toggle | `tool_policy.approval_required` | PLANNED |

---

## 5. Permission model (per tool)

| Layer | Meaning |
|---|---|
| **RBAC** | who may install (`system:configure` / `agent:update`) |
| **Tool tier** | 1 auto · 2 approval · 3 human |
| **tool_policy** | `auto_execute` / `approval_required` / `deny` on agent |
| **Connector scopes** | least privilege (e.g. `drive.readonly`) |
| **UnifiedGate + OPA** | every tool call at runtime |

**UI rule:** Install dialog lists **exact OAuth scopes**. Never silent full-access.

---

## 6. Connector suite (v1 catalog)

| Connector | Tool family | Scopes (example) | Status |
|---|---|---|---|
| Gmail / Mail | `mail_search` `mail_send` | `gmail.readonly` `gmail.send` | PLANNED |
| Google Drive | `drive_list` `drive_read` `drive_write` | `drive.readonly` `drive.file` | PLANNED |
| Photos | `photos_list` `photos_read` | `photoslibrary.readonly` | PLANNED |
| WhatsApp | `whatsapp_send` | business API | PLANNED (bridge exists) |
| GitHub | `git_status` `pr_list` | `repo` (minimal) | PLANNED |
| Calendar | `calendar_list` | `calendar.events.readonly` | PLANNED |

Core tools (already LIVE): memory_*, file_*, web_search/read, code_execute, document_*, packages_*.

---

## 7. Install flow (sequence)

```
User → Catalog → Install
  → choose permissions + policy
  → Connect account (OAuth) if connector
  → POST /tools/install {tool, agent_id, policy, scopes}
  → Capability linked + tool_policy updated
  → Toast success · Tools table shows Installed
Agent → tool_call → UnifiedGate (tier + policy + scopes) → execute
```

Fail-closed: missing connector session → tool GATED with reason (no fake success).

---

## 8. Standard agent Profile window (alignment)

| Profile contains | Profile does **not** contain |
|---|---|
| Identity · photo · channels | Tools marketplace |
| **Display** (chat settings 1-click) | Connector OAuth (Tools owns) |
| Security · sign out | Admin user CRUD |

**One-click:** Profile › Display → Chat settings. Tools is Settings › Tools / Tools modal.

---

## 9. I18N

All marketplace strings via `t('tools.*')` · `t('connectors.*')` · `t('common.*')` per SOMA-UI-I18N-001.

## 10. Acceptance (Playwright)

| AC | Proof |
|---|---|
| AC-TM-01 | Catalog lists tools from live API |
| AC-TM-02 | Install modal shows scopes + policy |
| AC-TM-03 | Install → agent Hands shows tool |
| AC-TM-04 | Connector OAuth GATED when provider unconfigured (honest) |
| AC-TM-05 | Permission deny → tool call blocked |
| AC-TM-06 | No emoji · locale switch works |
| AC-TM-07 | Soma law: zero mock rows |

## 12. REAL WIREFRAMES — fields + realistic data (no mocks; live schema)

### 12.1 Tools catalog (real `ToolCatalogItem` + `ToolInfo`)

```
┌ Tools · Catalog ─────────────────────────────────────────────────────────┐
│ 🔍 Search tools…          category [All|core|connector|document ▾]       │
│                                                                          │
│ name              tier  category    enabled  used-by  actions            │
│ web_search        2     core        ●        3        [Install][Policy]  │
│ file_read         1     core        ●        5        [Installed][Policy]│
│ google_drive      2     connector   ○        0        [Connect][Install] │
│ gmail             2     connector   ○        0        [Connect][Install] │
│ document_index    2     document    ●        2        [Installed][Policy]│
│ packages_ensure   3     core        ●        1        [Installed][Policy]│
└──────────────────────────────────────────────────────────────────────────┘
```

| Field | Source (real) | Example |
|---|---|---|
| name | `GET /api/v2/tools` `ToolInfo.name` | `web_search` |
| description | `ToolInfo.description` | Search via configured SearxNG |
| tier | tool class `tier` | 1 / 2 / 3 |
| category | `GET /tools/catalog` `category` | core / connector |
| enabled | `ToolCatalogItem.enabled` | true / false |

### 12.2 Install modal (real policy keys)

```
┌ Install tool → Default Agent ────────────────────────────────────────────┐
│ tool     web_search · tier 2 · egress · approval                         │
│ policy   auto_execute [ ]   approval_required [✓]   deny [ ]             │
│          (Capsule.tool_policy JSON keys — live PATCH)                    │
│ scope    network (IQ egress gate)                                        │
│ [Cancel]  [Install & enable]                                             │
└──────────────────────────────────────────────────────────────────────────┘
```

### 12.3 Connector (real Vault + OAuth shapes)

```
┌ Connect Gmail ───────────────────────────────────────────────────────────┐
│ provider_id   gmail                                                   │
│ account       adrian@somatech.lat                                       │
│ scopes        gmail.readonly · gmail.send                               │
│ credential    → Vault secret/agent/api_keys/gmail_api_key (write-only) │
│ status        not connected                                             │
│ [Test connection]  [Connect]  [Cancel]                                  │
└──────────────────────────────────────────────────────────────────────────┘
```

### 12.4 Profile window (real `/auth/me` + channels)

```
┌ Profile ─────────────────────────────────────────────────────────────────┐
│ (photo)  Adrian Daniel          [×]                                     │
│          test@soma.dev                                                  │
│          [sysadmin]                                                     │
├ Account │ Channels │ Display │ Security ────────────────────────────────┤
│ Display name [Adrian Daniel_________]  email [test@soma.dev] (ro)       │
│ WhatsApp     [+593 99 123 4567_____] [Add]                             │
│ Email extra  [adrian@somatech.lat____] [Add]                            │
│ [Chat settings]  [Save profile]  [Sign out]                             │
└──────────────────────────────────────────────────────────────────────────┘
```

### 12.5 Files modal (real filesv2 fields)

```
name                         mime           size_bytes  created_at
Photo on 11-10-26 at 13.53.jpg  image/jpeg   549953      2026-10-13T18:32:38Z
soma-test-upload.txt           text/plain        24      2026-10-13T18:11:03Z
```

**Field law:** every column maps to a live API property (never invented). Synthetic **values** in diagrams are realistic; **schemas** are real.

---

## 13. Build phases (after GO)

| P | Work |
|---|---|
| 1 | Tools admin UI: Installed + policy + catalog list |
| 2 | Install/uninstall APIs + Capability link |
| 3 | Connector OAuth (Drive, Mail) + scopes |
| 4 | Permissions matrix + HITL |
| 5 | Photos/WhatsApp connectors |
| 6 | I18N + Playwright evidence |

**End of Tools Marketplace & Connector Suite Spec.**
