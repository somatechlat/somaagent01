# SOMA-ARCH-TOOLS-001 — Agent tool framework (assistant file/OS tools)

## Document Control

| Field | Value |
|---|---|
| Document Title | Agent tool framework — standardized implementation for assistant file/OS tools |
| Document Identifier | SOMA-ARCH-TOOLS-001 |
| Version | 1.1.0 |
| Date | 2026-10-08 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2027-01-08 |
| Related | `SOMA-STD-CODING-001`, `SOMA-STD-TRIAD-001`, `SOMA-ARCH-INVARIANTS-001`, `SOMA-PM-RAPID-WIRING-001`, `SOMA-A0-PARITY-001` |
| Source of truth | Agent Zero catalog audit + soma tool map + ADV sandbox review (2026-10-08) |
| Audience | Tool implementers, capsule operators, reviewers |
| Scope | New assistant tools (files, documents, Temporal jobs). Does **not** replace memory T-1 seam. |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-08 | SomaTech Engineering | Initial issue. Standardized tool abstraction, sandbox layers, Temporal durability for long file jobs, and policy default (unlisted = approval). |
| 1.1.0 | 2026-10-08 | SomaTech Engineering | §11 granular authorization: every tool action is RBAC role floor → OPA → SpiceDB → capsule scope via UnifiedGate; chat path must call the same choke as Kafka. PathGuard + unlisted=approval landed in tree. |

---

## 1. Purpose

Give the agent real assistant capabilities (create/edit/read files, documents,
PDFs, long research reports) **without** cloning Agent Zero’s unrestricted host
shell. Same orchestrator + capsule + tools; **our** sandbox and **Temporal**
for anything that must not die.

## 2. Non-negotiable invariants

1. **One path:** tools run through the existing chat tool loop → one policy choke → sandbox → PathGuard/Temporal. No second loop.
2. **T-1 memory:** file tools never write SFM; memory remains `MemoryGateway` → SomaBrain.
3. **Unlisted tool = approval_required** (not auto_execute).
4. **No shell strings** in the protocol. Structured `{binary, argv[]}` only for exec.
5. **No in-loop pip/apt** of arbitrary packages. Pre-baked image or human-merged lockfile.
6. **Workroot** is server-side (`tenant_id`/`capsule_id` derived). Never from model args.
7. **Long jobs → Temporal.** File bytes never go in workflow history — IDs/manifests only.
8. **No host SSH / docker.sock / computer-use** unless a separate operator profile (not default).

---

## 3. Sandbox layers (L0–L4)

| Layer | Mechanism | Code |
|---|---|---|
| L0 OS | Workroot volume; non-root; no host mounts except workdir | infra compose |
| L1 Path | `services/common/path_guard.py` | PathGuard |
| L2 Process | Tiered exec; no shell string | future `process_runner` |
| L3 Approval | Capsule policy + IQ floor + WS gate; resolved-effect approval | `tool_calling.py` |
| L4 Audit | Decision log + claim verifier | tool executor audit |

**Do not copy from A0:** unrestricted text_editor, host PTY/SSH root, in-loop apt/pip, self-rewritable instruction files.

---

## 4. Tool abstraction (every new tool)

### 4.1 Class shape

```python
class SomaAssistantTool:
    name: str                 # stable catalog id
    description: str          # for OpenAI function schema
    tier: int                 # 1=auto-safe, 2=approval, 3=human/image
    needs_workroot: bool = False
    needs_egress: bool = False
    durable: bool = False     # True → prefer Temporal activity, not one-shot

    def input_schema(self) -> dict: ...
    async def run(self, args: dict, *, guard: PathGuard | None, ctx: ToolContext) -> dict: ...
```

`ToolContext`: `tenant_id`, `capsule_id`, `session_id`, `user_id`, `approval_id`.

### 4.2 Registration

1. Implement in `services/tool_executor/assistant_tools/` (new package).
2. Export in `AVAILABLE_TOOLS` / `default_tool_definitions` only when tier ≤ 2 **and** capsule may enable.
3. Capsule `tool_policy` must list tier-2/3 tools in `auto_execute` **or** `approval_required` — never rely on unlisted auto.
4. Register in `docs/iso/SOMA-01-TOOLS-CATALOG-001` (or this doc §5 table).

### 4.3 File ops contract

| Op | Args | Returns |
|---|---|---|
| `file_list` | `path?`, `glob?` | names, types, sizes (no content dump) |
| `file_read` | `path`, `line_from?`, `line_to?` | content range + `hash` + `total_lines` |
| `file_write` | `path`, `content` | path, bytes, hash (approval or Temporal if large) |
| `file_patch` | `path`, `old`/`new` or unified patch | path, diff summary, hash |
| `file_search` | `query`, `path?` | matches with line numbers, truncated |

All paths **must** `guard.resolve(path)` first.

---

## 5. Catalog (assistant tools to build)

| Tool | Tier | Durable | Notes |
|---|---|---|---|
| `file_list` | 1 | no | |
| `file_read` | 1 | no | PathGuard mandatory |
| `file_search` | 1 | no | |
| `file_write` | 2 | optional | large → Temporal |
| `file_patch` | 2 | optional | |
| `document_ingest` | existing | optional | needs attachment upload lane |
| `document_query` | 2 | optional | after ingest |
| `research_report` | 2–3 | **Temporal** | ResearchReportWorkflow |
| `file_build` | 2–3 | **Temporal** | FileBuildWorkflow |
| `job_status` | 1 | — | query Temporal |
| `shell_exec` | 3 | optional | container; argv only; opt-in capsule |
| `package_install` | 3 | yes | image bake or human merge only |

Existing default kit (timestamp, memory_*, code_execute, file_read, http_fetch, document_ingest, canvas_append) remains; **file_read** switches to PathGuard; **code_execute** stays restricted (not a sandbox).

---

## 6. Temporal durability (assistant jobs)

| Workflow | Purpose |
|---|---|
| `ResearchReportWorkflow` | Outline → research → write sections → assemble → filesv2 |
| `FileBuildWorkflow` | Multi-step document build |
| `DocumentPipelineWorkflow` | OCR/convert/bulk |
| Existing | Sleep, JobAdvance, OutboxReplay, Conversation, A2A |

**Input:** `{topic|spec, capsule_id, tenant_id, filesv2_ids?}`  
**Activities** write via PathGuard + filesv2 IDs.  
**History:** manifests and IDs only — never multi-MB content.  
**Signals:** cancel/pause. **Queries:** progress.  
**Chat UX:** “Durable job `wf_…` started — Jobs panel.”

---

## 7. Policy defaults

```json
{
  "auto_execute": ["timestamp", "memory_recall", "memory_save", "memory_forget", "memory_proximity", "memory_get", "file_list", "file_read", "file_search", "job_status"],
  "approval_required": ["file_write", "file_patch", "document_query", "research_report", "file_build", "code_execute", "http_fetch", "document_ingest"],
  "denied": []
}
```

`shell_exec` / `package_install` stay **denied** until an operator profile enables them.

IQ autonomy floor may only **tighten** (existing `_apply_autonomy_floor`).

---

## 8. Implementation path (order)

| Step | Deliverable |
|---|---|
| A | PathGuard + unit tests (sibling-dir bypass, absolute, `~`) |
| B | ToolPolicy unlisted → approval_required (done in code with this issue) |
| C | One choke: run_tool_loop calls shared `decide_tool()` (policy + egress + capsule capabilities) |
| D | file_list / file_read via PathGuard (replace startswith jail) |
| E | file_write / file_patch + Files tab editor save |
| F | Composer upload → filesv2 → attachment_id → ingest |
| G | ResearchReportWorkflow + FileBuildWorkflow (Temporal) |
| H | job_status + Jobs UI panel |
| I | shell_exec opt-in container profile |
| J | Playwright: report job creates file visible in Files tab |

---

## 9. Doc hygiene (this architecture wins)

| Conflict | Resolution |
|---|---|
| Docs implying file tools auto-run | **Unlisted = approval_required** |
| A0-parity “full shell” as default | **Opt-in only**; parity is capability, not host root |
| SandboxManager “in-process” as security | **Rename narrative**: timeout helper, not sandbox; L0–L4 is the sandbox |
| Multiple file planes | Tools use workroot; bytes home is filesv2; UI lists both via API ids |

Do not invent a second memory client or second chat loop.

---

## 10. Definition of done

1. PathGuard rejects sibling-dir and absolute paths (tests green).  
2. New tools never auto-execute unless listed in `auto_execute`.  
3. “Write a research report” starts a Temporal workflow that completes without the chat session.  
4. Output file appears under workroot and in filesv2/Files tab.  
5. No shell string execution; no host path escape.  
6. Every tool action passes granular authz (§11).  
7. `check_docs.py` clean on this document.

---

## 11. Granular authorization (RBAC · OPA · SpiceDB · capsule)

**Every tool action is authorized, not only chat send.**

### 11.1 Layered decision (fail-closed)

```
subject (user + tenant + roles)
  → 1. RBAC role floor     (admin/core/authz.py ROLE_PERMISSIONS)
  → 2. OPA                 (policy/*.rego — tool.execute / resource actions)
  → 3. SpiceDB             (relation check when configured)
  → 4. Capsule scope       (enabled_capabilities ∩ tool_policy ∩ IQ floor)
  → 5. PathGuard / egress  (environment effects)
```

Implemented as **one** function used by **both** chat `run_tool_loop` and Kafka `tool_executor.RequestHandler` — not two authorities (ADV P-04).

### 11.2 Resource / verb map (examples)

| Action | RBAC resource | OPA input | SpiceDB verb |
|---|---|---|---|
| `file_list` / `file_read` | `resource:file_read` | `tool.request` + path in workroot | view |
| `file_write` / `file_patch` | `resource:file_write` | `tool.request` + approval | edit |
| `file_delete` | `resource:file_delete` | deny-by-default | delete |
| `shell_exec` | `resource:tool_execute` | always approval | manage |
| `research_report` | `resource:tool_execute` | approval + Temporal start | manage |
| `document_ingest` / egress | `resource:file_upload` + egress IQ | host allowlist | view/edit |
| `memory_*` | existing memory authz | T-1 seam only | — |

Capsule `enabled_capabilities` **must** include the tool name or UnifiedGate `_check_scope` denies (empty list = deny all tools).

### 11.3 Implementation status (this issue)

| Piece | Status |
|---|---|
| UnifiedGate layering | Exists (`unified_gate.py:134-249`) |
| Capsule scope `_check_scope` | Exists but **not called per-tool in chat** — **OPEN** |
| Kafka path OPA | Exists (`request_handler.py`) — action name must match rego (`tool.execute` vs `tool.request`) |
| Chat path OPA per tool | **OPEN** — must call same choke |
| Unlisted = approval | **LANDED** (`tool_calling.py` ToolPolicy.decision) |
| PathGuard | **LANDED** (`services/common/path_guard.py`); `file_read` uses it |
| filesv2 object-level tenancy | **OPEN** — list/get must bind caller tenant |

### 11.4 Operator knobs

- **Capsule.tool_policy** — three buckets (auto / approval / denied)  
- **AgentIQ** — `tool_approval`, `require_hitl`, `egress_allowed` (tighten only)  
- **RBAC roles** — `ROLE_PERMISSIONS` floor  
- **OPA rego** — deny-by-default; explicit allows for agent memory + file tools  
- **SpiceDB** — subject/resource/relations when deployed  

Absent OPA/SpiceDB: fail per UnifiedGate semantics (absent engine = that layer absent; role floor + capsule still apply). Never invent a deny-all that breaks Standalone when engines are optional — but **never auto-execute unlisted tools**.

---

*End of SOMA-ARCH-TOOLS-001 v1.1.0*
