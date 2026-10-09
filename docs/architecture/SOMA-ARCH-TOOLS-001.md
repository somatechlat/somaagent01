# SOMA-ARCH-TOOLS-001 — Agent tool framework (assistant file/OS tools)

## Document Control

| Field | Value |
|---|---|
| Document Title | Agent tool framework — standardized implementation for assistant file/OS tools |
| Document Identifier | SOMA-ARCH-TOOLS-001 |
| Version | 1.3.0 |
| Date | 2026-10-09 |
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
| 1.2.0 | 2026-10-09 | SomaTech Engineering | Full tool catalog vs Agent Zero inventory (core + plugins). File creation suite (docs/PPT/XLSX/PDF/plots). Package ensure profiles (math/plot stack) with allowlist + Temporal — no free shell pip. Architecture-audit hardening notes. |
| 1.2.1 | 2026-10-09 | SomaTech Engineering | §5.7 complete 23-tool A0 audit table (every `agent.system.tool.*` + connector remote tools). Explicit Do-not-clone list. Power model: free work inside PathGuard/Temporal/OPA rails. |
| 1.2.2 | 2026-10-09 | SomaTech Engineering | Fix T-1 violation in catalog prose: `document_query` and all memory/RAG I/O go **MemoryGateway → SomaBrain** only — never direct SFM from the agent (SOMA-STD-TRIAD-001 T-1). |
| 1.2.3 | 2026-10-09 | SomaTech Engineering | §5.9 Document RAG redesign grounded in live `memory_gateway.py` + `somabrain_adapter.py`: index via `remember_text`, query via `recall`, no second client. Ingest currently extracts only; index + document_query still OPEN. |
| 1.2.4 | 2026-10-09 | SomaTech Engineering | §5.9.1–5.9.6 user journey: filesv2 bytes vs Brain chunks; extract full text for same-turn answer; index for durable recall; document_query; honesty rules. Design only. |
| 1.2.5 | 2026-10-09 | SomaTech Engineering | Implement `document_index` + `document_query` on MemoryGateway (A0 document_query journey without FAISS/SFM). Capsule default policy approval. 10 unit tests green. |
| 1.3.0 | 2026-10-09 | SomaTech Engineering | §5.10 Internet/browser/search requirement: A0 SearxNG+Playwright audit; recommended OSS stack (SearxNG, trafilatura, Playwright container); generic Capability/MCP extension model; Capsule profiles. Host browser DENY. |

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

## 5. Full tool catalog (normative)

This §5 is the **single catalog** for agent hands. Status values: **LIVE** (in tree, wired), **PLANNED** (spec only — not stubbed), **DENY** (must stay off until operator profile). Tiers: **1** auto-safe · **2** approval · **3** human / image / Temporal-only start.

### 5.1 How this compares to Agent Zero (audit summary)

| A0 behaviour | A0 mechanism | Soma form | Why better |
|---|---|---|---|
| text_editor read/write/patch | Path expand `~`/abs; no jail | PathGuard L1 + approval on write/patch | No host escape |
| code_execution python/shell | Interactive PTY, SSH optional, pip/apt in-loop | `code_execute` restricted + Temporal jobs + Package Ensure profiles | No free host root; durable multi-step |
| office_artifact docx/xlsx/pptx | LibreOffice + document store | `artifact_create` / `artifact_edit` (Temporal) → workroot + filesv2 | PathGuard + approval + audit |
| search_engine | DDG/SearxNG | `web_search` + egress allowlist + IQ | OPA egress gate |
| scheduler | In-process cron | Temporal schedules + `job_status` | Durable, not process-local |
| browser / desktop / connector SSH | Full host automation | Gated surfaces only; **not default** | Operator profile only |
| memory_* | FAISS local | T-1 MemoryGateway → SomaBrain → SFM | One write lane |
| plugin installer / shell | Arbitrary | Package Ensure allowlist + image bake | Supply-chain control |

**Do not copy** A0 unrestricted host shell, in-loop `pip install anything`, SSH-to-user-machine, or self-rewritable instruction files.

### 5.2 LIVE — default kit (every agent)

| Tool | Tier | Policy | Notes |
|---|---|---|---|
| `timestamp` | 1 | auto | UTC |
| `memory_recall` / `save` / `forget` / `proximity` / `get` | 1 | auto (NON_DISABLEABLE) | T-1 only |
| `file_read` | 1 | auto | PathGuard; workroot |
| `file_list` | 1 | auto | PathGuard; metadata |
| `file_search` | 1 | auto | PathGuard; literal |
| `file_write` | 2 | approval | PathGuard; SHA-256 |
| `file_patch` | 2 | approval | PathGuard; exact once |
| `research_report` | 2 | approval | Temporal ResearchReportWorkflow |
| `job_status` | 1 | auto | Temporal describe + progress query |
| `code_execute` | 2 | approval | Restricted Python; **not** a security sandbox (L0–L4 is) |
| `http_fetch` | 2 | approval + egress | SSRF deny-list; IQ `egress_allowed` |
| `document_ingest` | 2 | approval | Attachment → knowledge (upload lane live; ingest residual) |
| `canvas_append` | 1 | auto | Session canvas |

### 5.3 File creation suite (docs / decks / sheets / plots) — PLANNED

Long multi-step creation **must** be Temporal (invariant 7). Chat tool starts workflow; bytes never enter history.

| Tool | Tier | Durable | Formats | Notes |
|---|---|---|---|---|
| `artifact_create` | 2 | **Temporal** ArtifactCreateWorkflow | md, txt, **docx, odt, pptx, odp, xlsx, ods, pdf, csv** | Structured kind+format; writes via PathGuard; publishes to filesv2 |
| `artifact_edit` | 2 | optional Temporal | same | Text replace / slide/sheet ops on workroot file |
| `artifact_read` | 1 | no | same | PathGuard; truncated |
| `chart_render` | 2 | optional | **png, svg, pdf** plot | Runs in Package Ensure venv (matplotlib etc.); output PathGuard |
| `file_build` | 2–3 | **Temporal** FileBuildWorkflow | multi-step assemble | Outline → sections → merge → filesv2 |
| `document_index` | 2 | no | **LIVE** — chunk → `remember_text` (T-1). A0 FAISS replaced by Brain. |
| `document_query` | 2 | no | **LIVE** — `recall` + optional `attachment_id` filter. Never SFM. See §5.9. |

**Honesty:** PLANNED tools are **not registered** until code+tests exist. Unlisted = approval if someone adds them without listing.

**Implementation preference:** one `artifact_*` family sharing Temporal activities (python-docx / openpyxl / python-pptx / reportlab / matplotlib) inside the **agent worker image**, not host LibreOffice on the chat process.

### 5.4 Package ensure (install libraries) — PLANNED, tier 3

Operator scenario: *“INSTALL all libraries for MATH plots”* must **not** be free-shell `pip install` in the chat loop (A0 pattern; supply-chain + non-reproducible).

| Tool | Tier | Durable | Behaviour |
|---|---|---|---|
| `packages_ensure` | 3 | **Temporal** PackageEnsureWorkflow | Ensure **profiles** or **allowlisted** packages in the **workroot-scoped venv** (or next image bake). Approval mandatory. |
| `packages_list` | 1 | no | Show installed distributions in workroot venv / image tag |

**Profiles** (curated; versions pinned in repo lockfile, not model-guessed):

| Profile id | Intent | Example pins (lockfile owns truth) |
|---|---|---|
| `scientific` | Math + plots | numpy, scipy, matplotlib, pandas, sympy, seaborn |
| `office` | Docs/decks/sheets | python-docx, openpyxl, python-pptx, reportlab, odfpy |
| `data` | Frames / IO | pandas, pyarrow, openpyxl |
| `vision` | Image QA helpers | pillow (opencv only if operator allowlist) |

**Hard rules**

1. No `pip` / `apt` / `curl|sh` strings in tool protocol — structured `{profile|packages[]}` only.  
2. Packages must be on the **operator allowlist** (Capsule/AgentIQ or platform config). Unknown package → fail-closed with explicit deny reason.  
3. Install runs only under **PackageEnsureWorkflow** (Temporal) → L0 container; timeout + audit.  
4. Side effect is **workroot venv** (`.venv` under `TOOL_WORK_DIR`) or a **proposed image bake** — never mutate the host OS or chat process environment.  
5. `code_execute` may use the venv path returned by `packages_ensure`; it must not install packages itself.  
6. Network egress for PyPI is an **egress allowlist** entry; disabled → ensure fails honestly.

**OS packages (container only) — `os_packages_ensure`:**  
Same rails as Python packages. Installs **allowlisted** apt packages **inside the agent L0 container** via Temporal (`argv[]`, never shell strings). Profiles e.g. `media` (ffmpeg, imagemagick), `docs` (poppler-utils, unzip). Always approval. **Never** mutates the user host OS or chat process. Operator extends the OS allowlist or bakes the agent image. Host `apt` / docker.sock / free shell = DENY.

**Example user → tool path (target UX)**

```
User: INSTALL all libraries for MATH plots in your OS
Agent: packages_ensure { profile: "scientific" }   → approval modal
Human: Approve
Temporal: PackageEnsureWorkflow creates workroot venv, installs pin set
Agent: job_status / packages_list → "scientific profile ready (venv: …)"
User: Plot sine waves…
Agent: chart_render or code_execute using that venv → PNG in workroot → filesv2
```

### 5.5 Sandbox / process / egress — PLANNED or DENY

| Tool | Tier | Status | Notes |
|---|---|---|---|
| `shell_exec` | 3 | DENY default | `{binary, argv[]}` only; container; opt-in capsule; **no** `sh -c` strings |
| `package_install` (legacy name) | 3 | superseded by `packages_ensure` | Do not implement free-form |
| `web_search` | 2 | **LIVE** | SearxNG via `SEARXNG_URL` settings chain; egress IQ; no localhost default |
| `browser_use` | 2–3 | PLANNED gated | Playwright in isolated container; canvas panel; not host Chrome |
| `computer_use` / remote connector | 3 | DENY | Separate operator profile only |
| `call_subordinate` | 2 | PLANNED | Capsule-to-capsule via existing delegation; same choke |

### 5.6 Orchestration / product tools — existing or PLANNED

| Tool | Tier | Status | Notes |
|---|---|---|---|
| `response` / break | 1 | part of loop | Not a free LLM rewrite layer |
| `notify_user` | 2 | PARTIAL (notifications app) | Bound to real notifications API |
| `skills` load | 1–2 | PLANNED | Skill markdown inject; not A0 infection-style |
| `scheduler_*` | 2 | PLANNED on Temporal schedules | Not in-process cron |
| `a2a_message` | 2 | PLANNED | Matches docs/plans/a2a protocol; no peer FS write |

### 5.7 Complete Agent Zero inventory (audited 2026-10-09)

Source tree: `/Users/macbookpro201916i964gb1tb/Downloads/agent-zero-main`.  
User-facing tools = every `agent.system.tool.*.md` loaded by `extensions/python/system_prompt/_11_tools_prompt.py` after `tool_policy.filter_tool_prompts`.

| # | A0 tool | A0 path | What A0 does | Soma id | Disposition |
|---|---|---|---|---|---|
| 1 | `response` | `tools/response.py` | End loop / final answer | loop control | LIVE (orchestrator) |
| 2 | `code_execution` | `plugins/_code_execution` | **python / nodejs / terminal** interactive PTY sessions; optional **SSH**; apt/pip via terminal | `code_execute` + `packages_ensure` + (future) `shell_exec` | LIVE restricted Python; **install = packages_ensure**; shell DENY default |
| 3 | `input` | `plugins/_code_execution/tools/input.py` | Keyboard into running terminal | `code_input` | PLANNED only if shell_exec opt-in |
| 4 | `text_editor` | `plugins/_text_editor` | read/write/patch (+ freshness, multi patch modes) | `file_read/write/patch` | **LIVE** PathGuard |
| 5 | `office_artifact` | `plugins/_office` | create/open/read/edit **odt/ods/odp/docx/xlsx/pptx** + LibreOffice validate | `artifact_*` | PLANNED §5.3 Temporal |
| 6 | `document_query` | `plugins/_document_query` | RAG over uploaded docs | `document_query` | **LIVE** §5.9 — MemoryGateway.recall; A0 FAISS not cloned |
| 7 | `memory` + `behaviour` | `plugins/_memory` | save/load/forget/delete + behaviour rules | `memory_*` + Capsule persona | **LIVE** T-1 |
| 8 | `goal` | `plugins/_goal` | create/update/complete per-chat goal | `goal` | PLANNED |
| 9 | `browser` | `plugins/_browser` | navigate/click/type/screenshot/script in isolated browser | `browser_use` | PLANNED gated (container) |
| 10 | `search_engine` | `tools/search_engine.py` | SearxNG search | `web_search` | PLANNED + egress |
| 11 | `scheduler` | `tools/scheduler.py` | cron/adhoc/planned tasks | Temporal schedules + `scheduler_*` | PLANNED on Temporal |
| 12 | `skills` | `tools/skills_tool.py` | list/load skill markdown into context | `skills` | PLANNED |
| 13 | `vision_load` | `tools/vision_load.py` | image → vision model context | multimodal | PLANNED |
| 14 | `call_subordinate` | `tools/call_subordinate.py` | spawn subordinate agent | `call_subordinate` | PLANNED (Capsule delegation) |
| 15 | `notify_user` | `tools/notify_user.py` | agent → user notification | `notify_user` | PARTIAL (notifications app) |
| 16 | `parallel` | `tools/parallel.py` | multi-tool parallel worker | Temporal fan-out | prefer WF not in-loop |
| 17 | `wait` | `tools/wait.py` | sleep in loop | Temporal timer | prefer WF |
| 18 | `a2a_chat` | `tools/a2a_chat.py` | HTTP A2A to peer agent | `a2a_message` | PLANNED (protocol match) |
| 19 | `unknown` | `tools/unknown.py` | unknown tool feedback | executor error | LIVE structured error |
| 20 | `text_editor_remote` | `plugins/_a0_connector` | edit **user host** FS | — | **Do not clone** |
| 21 | `code_execution_remote` | `plugins/_a0_connector` | code on **user host** | — | **Do not clone** |
| 22 | `computer_use_remote` | `plugins/_a0_connector` | GUI control **user host** | — | **Do not clone** / DENY |
| 23 | `input_remote` | `plugins/_a0_connector` | keyboard on **user host** | — | **Do not clone** |
| — | (MCP servers) | `helpers/mcp_handler.py` | external MCP tools | MCP client Capabilities | PLANNED |
| — | (plugins installer) | `_plugin_installer` | install A0 plugins | — | use Capsules + packages_ensure |
| — | (bridges WA/TG/Email) | plugins | messaging | Capsules | out of tool catalog |

**A0 sandbox reality (do not copy):** no in-process FS jail; Docker only boundary; text_editor expands absolute/`~`; terminal can `cd` anywhere; pip/apt in the same PTY as the agent.

**Soma power model (clone capacity, keep firewalls):** PathGuard workroot + tiered approval + UnifiedGate/OPA + Temporal durability + packages_ensure allowlist profiles + optional shell_exec argv-only opt-in — agent works freely **inside** those rails, never outside them.

### 5.9 Document RAG redesign — THE ONE PATH only (T-1)

**Wrong (forbidden):** tool → Milvus/SFM client → store.  
**Right (only path that exists):** tool → `MemoryGateway` → `SomaBrainAdapter` → SomaBrain → SFM.

Code already owns this lane (`services/common/memory_gateway.py:1-5`, `somabrain_adapter.py` POST `/memory/remember|recall|forget`). Document tools **must not** add a second client.

```
┌─────────────┐   extract    ┌──────────────────┐  remember_text   ┌─────────────┐
│ filesv2 /   │ ───────────► │ DocumentIngest   │ ───────────────► │ MemoryGW    │
│ attachment  │  (Temporal)  │ chunk + tag      │  kind=semantic   │ → Adapter   │
└─────────────┘              │ source=document: │  source=document │ → Brain     │
                             │   {attachment_id}│   :{id}[:n]      │ → SFM       │
                             └──────────────────┘                  └──────▲──────┘
                                                                          │
┌─────────────┐  recall(k)   ┌──────────────────┐   MemoryHit[]           │
│ document_   │ ───────────► │ MemoryGateway    │ ────────────────────────┘
│ query tool  │  query embed │ .recall() only   │  (same embed_text / dim)
└─────────────┘              └──────────────────┘
```

| Step | Owner | API (real, in tree) |
|---|---|---|
| 1 Extract | Temporal `DocumentIngestWorkflow` (or live extract tool) | attachment bytes → text (existing `IngestDocumentTool` extract path) |
| 2 Index | **only** `FanoutMemoryGateway.remember_text` | T-6 durable-before-hop WAL → `POST /memory/remember` |
| 3 Query | **only** `FanoutMemoryGateway.recall` | precomputed `embed_text` → `POST /memory/recall` |
| 4 Forget | `forget` | `POST /memory/forget` |

**Chunk write shape** (no new DTO — reuse `MemoryWrite`):

| Field | Value |
|---|---|
| `kind` | `semantic` |
| `source` | `document:{attachment_id}` (adapter already sends `source` + tags) |
| `text` | `[doc:{attachment_id} #{chunk_n}] {chunk_text}` — prefix so recall hits can be scoped |
| `tenant_id` | caller tenant (fail-closed; same as memory tools) |
| `coord` / `embedding` | `make_coord` + `embed_text` (seam contract — never invent) |

**`document_query` tool contract (PLANNED):**

```
args: { query: str, k?: int, attachment_id?: str, tenant_id: str }
run:
  hits = await get_memory_gateway().recall(query, k or 8, tenant_id)
  if attachment_id: keep hits whose text startswith f"[doc:{attachment_id} "
  return digest (same shape as memory_recall digest — no second hit schema)
```

**Forbidden in this redesign:** SFM URL/env · Milvus client · second embedder · local FAISS · brain bypass · inventing `/memory/search_documents` without peer contract.

**Peer boundary:** if Brain later exposes a document-filtered recall, agent still only calls MemoryGateway; peer owns `somabrain/memory/*`. Ask via A2A; do not invent.

**Current tree gaps (honest):**

| Piece | Status |
|---|---|
| MemoryGateway remember/recall/forget | LIVE |
| `document_ingest` extract text | LIVE — **does not index** (returns text only) |
| Chunk → `remember_text` index | **LIVE** `document_index` |
| `document_query` tool | **LIVE** (approval tier) |
| Temporal DocumentIngestWorkflow | PLANNED |

#### 5.9.1 Two homes for a document (never collapse)

| Home | Holds | Who reads it | Lifetime |
|---|---|---|---|
| **filesv2** | Original bytes (PDF, DOCX, …), version, mime, download URL | UI Files, re-extract, audit | Until delete |
| **SomaBrain → SFM** | **Searchable text chunks** as semantic memory (`remember` / `recall`) | Agent via MemoryGateway only | Until `forget` / retention |

**filesv2 is not the brain. Brain is not the file store.**  
Upload always lands in filesv2 first. Indexing into Brain is a **separate, explicit** step so the agent can later answer “what’s in that PDF?” without re-uploading and without holding the whole file in chat history forever.

#### 5.9.2 User journey — “Upload this PDF and tell me what’s inside”

```
User (chat)                    Agent                         Stores
──────────                    ─────                         ──────
1. Attach report.pdf  ──►  POST /filesv2/upload
                              + upload-local bytes
                              → { attachment_id / file_id }
                              (LIVE today)

2. “Summarize it”     ──►  tool: document_ingest
                              { attachment_id }
                           ├─ fetch bytes (gateway/filesv2)
                           ├─ EXTRACT full text (fitz/OCR)
                           └─ return text (+ optional auto-INDEX)

3a. Same-turn answer         LLM sees extracted text (or digested
                             sections) → answers “what’s inside”
                             — this is READ of full content in-context

3b. Durable index            for each chunk:
                             MemoryGateway.remember_text(
                               text="[doc:{id} #n] …",
                               kind=semantic,
                               source="document:{id}")
                           → Brain → SFM  (T-1 path only)

4. Next week:               document_query { query, attachment_id? }
   “What did §3 say?”   ──►  gateway.recall → hits → filter [doc:id]
                             → answer from chunks, not from chat memory
```

#### 5.9.3 Full content vs chunks — when each is used

| Need | Mechanism | Why not the other |
|---|---|---|
| **Immediate** “what’s in this PDF?” | **Extract full text** → feed LLM (capped, e.g. first N chars / section digests) | Chunk recall alone can miss structure (TOC, page order) |
| **Durable** “remember this document forever” | **Chunk + index** via `remember_text` | Full text in one memory row is too coarse for recall and blows limits |
| **Later** “ask about section 3” | **`document_query`** → `recall` on tagged chunks | Re-parsing the PDF every question is wasteful; chat history is not RAG |

**Rule of thumb for the orchestrator (design):**

1. Always **extract** on ingest (tool result for this turn).  
2. Always **index** chunks when the user wants the doc to *stay* known (default on for chat uploads; Temporal for large PDFs so the turn is not blocked).  
3. **Never** dump multi-MB PDF text into permanent chat history as the only copy.  
4. **Never** open SFM; only MemoryGateway.

#### 5.9.4 What the model is allowed to see

| Stage | Model sees |
|---|---|
| Upload ack | `file_id`, filename, mime, size — not full bytes |
| Ingest result | Extracted text **or** section summaries + `indexed_chunks: n` + `document_id` |
| document_query | Ranked chunk digests (`[doc:… #n]` + summary + score) — same digest shape as `memory_recall` |
| Never | Raw Milvus payloads, SFM coords as “file paths”, host filesystem paths outside workroot |

Large PDF policy (design): if extract text > context budget → Temporal DocumentIngestWorkflow indexes first; chat answer uses `document_query` / progressive section reads — **fail honestly** (“document indexed; ask about a section”) rather than truncate silently.

#### 5.9.5 Tool surface for this journey (design — no code yet)

| Tool | Role |
|---|---|
| composer upload → filesv2 | bytes home (LIVE) |
| `document_ingest` | extract (+ kick index workflow); returns text summary + document_id |
| `document_index` (optional explicit) | force re-index / index workroot file already PathGuard-read |
| `document_query` | recall chunks via gateway only |
| `memory_forget` | remove one chunk coord; or document-level forget job (list coords by source prefix — may need brain filter; A2A if missing) |

#### 5.9.6 Failure honesty

| Failure | User-visible |
|---|---|
| filesv2 upload down | upload error — no fake file_id |
| extract fail (scanned PDF, no OCR) | “could not extract text” — no empty success |
| Brain remember 503 | index queued (T-6 WAL) / “stored in filesv2; not yet searchable” — **never** “indexed” |
| recall outage | `MemoryRecallUnavailable` → “memory unavailable”, not empty answer |

---

### 5.8 Registration rule (unchanged)

1. Implement under `services/tool_executor/assistant_tools/`.  
2. Export in `AVAILABLE_TOOLS` / `default_tool_definitions` only when tier ≤ 2 **and** capsule may enable.  
3. Tier 2/3 must appear in capsule `auto_execute` **or** `approval_required` — never rely on unlisted auto.  
4. Catalog row in this §5 must move PLANNED → LIVE in the same PR as code.  
5. Every action hits `decide_and_authorize_tool` (§11).

---

### 5.10 Internet / browser / search — A0 audit + Soma stack (requirement)

**Requirement (Operator):** internet access and browser automation must be **generic** — any tool can be registered as a Capsule Capability and run through the same choke. Math plots were only an example; this section is the normative web stack.

#### 5.10.1 What Agent Zero actually does (source: `Downloads/agent-zero-main`)

| A0 piece | Mechanism | Soma disposition |
|---|---|---|
| `search_engine` tool | Always calls **SearxNG** `POST http://localhost:55510/search` (`helpers/searxng.py`); formats top 10 title/url/snippet | Clone **behaviour** as `web_search` → **operator SearxNG URL** (settings/BrainSetting topology, no localhost default) |
| `duckduckgo_search` helper | `duckduckgo_search.DDGS` library | Optional secondary backend **behind** SearxNG or as fallback only if SearxNG down; still egress-gated |
| `perplexity_search` helper | Exists in tree | Optional paid backend — **not** default; Vault key if enabled |
| `_browser` plugin | **Playwright Chromium in Docker** (`runtime_backend: container`); optional **host browser** via A0 CLI connector | **Container only**. Host browser = DENY (same as computer_use_remote) |
| Browser actions | navigate, content (DOM refs `[link 1]`), click/type/submit, screenshot, evaluate JS, tabs, history screenshots, canvas panel | Same action set, **isolated** Playwright service |
| DOM annotation | refs for model actions | Keep — structured refs, not raw HTML dump |
| Extensions | Unpacked Chromium extensions in Docker browser | Operator profile only; not default |
| Proxy | Config for internal Docker browser | Capsule/infra setting; secrets Vault |

A0 search is thin (one SearxNG URL hardcoded). A0 browser is rich but **host-browser path is a security hole** for multi-tenant Soma.

#### 5.10.2 Recommended open-source Soma stack

| Layer | Open source | Role | Why better than A0 default |
|---|---|---|---|
| **Web search** | **[SearxNG](https://github.com/searxng/searxng)** (self-host) | Meta-search; JSON API | No single-vendor lock; multi-engine; private; same as A0 but **URL is topology** |
| **Fetch page text** | **[trafilatura](https://github.com/adbar/trafilatura)** or **readability-lxml** | HTML → clean text | Better than raw browser for “read article” |
| **HTTP client** | **httpx** (already in tree) | `http_fetch` + SSRF deny | Shared client, timeouts |
| **Browser automation** | **Playwright** (Python) in **dedicated container** | navigate/click/type/screenshot | Same as A0 container mode; no host Chrome |
| **Optional browser API** | **[Browserless](https://www.browserless.io/)** or Playwright MCP server | HTTP Playwright if we want out-of-process | Still container; operator choice |
| **MCP for external tools** | Official **MCP** (stdio/HTTP) | Materialize Capabilities | Generic “any tool” path |
| **Screenshots→vision** | existing multimodal + Capsule `browser_model` | Visual QA | Keep |

**Do not use as defaults:** bare `curl|sh`, scraping APIs with secrets in Capsule JSON, host Chrome via CDP on user machine, unlimited `page.evaluate`.

#### 5.10.3 Tool surface (Soma)

| Tool | Tier | Backend | Notes |
|---|---|---|---|
| `web_search` | 2 | SearxNG (config URL) | `{query, k?}`; egress IQ; no localhost default |
| `http_fetch` | 2 | httpx | LIVE already |
| `browser_session` | 2 | Playwright container | open/list/close tabs |
| `browser_navigate` | 2 | Playwright | SSRF deny (link-local, metadata, private ranges unless allowlist) |
| `browser_content` | 2 | Playwright | a11y/text refs; not full HTML |
| `browser_click` / `type` / `submit` | 2 | Playwright | by ref/selector |
| `browser_screenshot` | 2 | Playwright → workroot PathGuard | optional filesv2 |
| `browser_eval` | **3** | Playwright | always approval; sandboxed page only |

All **approval** until Capsule lists them in `auto_execute`. Unlisted = approval (already law).

#### 5.10.4 Generic tool extension (any tool → Capsule)

This is the **requirement** for “create any tool and add it to the Capsule”:

```
ToolDefinition (native or MCP)
  → Capability row (name, schema, implementation{type:native|mcp, …})
  → Capsule.capabilities M2M  (enabled_capabilities)
  → Capsule.tool_policy bucket
  → AgentIQ floor
  → one choke per call
```

| Implementation.type | Meaning |
|---|---|
| `native` | Python class under `services/tool_executor/` |
| `mcp` | MCP server + remote tool name; client on choke |
| `packages` | ensure profile + import (scientific, office, …) |
| `temporal` | start workflow + job_status |
| `http` | operator-registered HTTP action (allowlisted URL template) |

**Marketplace / plugins** install **Capability packs + MCP server defs + policy templates** into a Capsule — never raw shell, never secrets.

#### 5.10.5 Capsule profiles (portable SKUs)

| Profile | Internet pack |
|---|---|
| `base` | `http_fetch` only |
| `researcher` | + `web_search`, `browser_*`, document_* |
| `developer` | + `packages_ensure`, files, code |
| `analyst` | + packages data/scientific, chart_render |

Profile = Capsule body template (tool_policy + IQ + capability set). Standalone download = pick profile → clone Capsule → sign.

#### 5.10.6 Hard rules (non-negotiable)

1. SearxNG / browser hosts come from **settings topology**, never hardcoded `localhost`.  
2. Host-browser connector and unrestricted `page.evaluate` on user Chrome = **DENY**.  
3. Every web tool: egress IQ + OPA `tool.request` + Capsule scope.  
4. Screenshots written via **PathGuard** into workroot only.  
5. MCP tools are Capabilities — same choke, same policy.  
6. No second chat loop for “browser agents.”

---

## 6. Temporal durability (assistant jobs)

| Workflow | Purpose | Status |
|---|---|---|
| `ResearchReportWorkflow` | Outline → research → write sections → assemble → filesv2 | **LIVE** (registered) |
| `ArtifactCreateWorkflow` | Create/edit office/markdown/PDF artifacts in workroot | PLANNED §5.3 |
| `FileBuildWorkflow` | Multi-step document build / merge | PLANNED |
| `PackageEnsureWorkflow` | Install allowlisted profile into workroot venv | PLANNED §5.4 |
| `DocumentPipelineWorkflow` | OCR/convert/bulk | PLANNED |
| Existing | Sleep, JobAdvance, OutboxReplay, Conversation, A2A | LIVE |

**Input:** `{topic|spec, capsule_id, tenant_id, filesv2_ids?, profile?}`  
**Activities** write via PathGuard + filesv2 IDs.  
**History:** manifests and IDs only — never multi-MB content.  
**Signals:** cancel/pause. **Queries:** progress.  
**Chat UX:** “Durable job `wf_…` started — Jobs panel.”

---

## 7. Policy defaults

```json
{
  "auto_execute": ["timestamp", "memory_recall", "memory_save", "memory_forget", "memory_proximity", "memory_get", "file_list", "file_read", "file_search", "job_status", "packages_list", "artifact_read"],
  "approval_required": ["file_write", "file_patch", "document_query", "research_report", "file_build", "artifact_create", "artifact_edit", "chart_render", "packages_ensure", "code_execute", "http_fetch", "document_ingest", "web_search"],
  "denied": ["shell_exec", "computer_use", "package_install_freeform"]
}
```

`shell_exec` / free-form package install stay **denied** until an operator profile enables them (then still tier 3 + allowlist).

IQ autonomy floor may only **tighten** (existing `_apply_autonomy_floor`).

---

## 8. Implementation path (order)

| Step | Deliverable | Status |
|---|---|---|
| A | PathGuard + unit tests | **DONE** |
| B | ToolPolicy unlisted → approval_required | **DONE** |
| C | One choke `decide_and_authorize_tool` chat + Kafka | **DONE** |
| D | file_list / file_read / file_search PathGuard | **DONE** |
| E | file_write / file_patch + Files editor save | tools **DONE**; editor save residual |
| F | Composer upload → filesv2 → attachment_id → ingest | upload **DONE**; ingest residual |
| G | ResearchReportWorkflow + ArtifactCreateWorkflow + FileBuildWorkflow | Research **DONE**; others PLANNED |
| H | job_status + Jobs UI panel | job_status **DONE**; panel residual |
| I | **PackageEnsureWorkflow** + profiles + `packages_ensure` | PLANNED §5.4 |
| J | Playwright: report job creates file visible in Files tab | OPEN |
| K | chart_render + scientific profile e2e (math plots) | PLANNED |
| L | shell_exec opt-in container profile | DENY until I + L0 proven |
| M | filesv2 object-level tenancy | OPEN §11.3 |

---

## 9. Doc hygiene (this architecture wins)

| Conflict | Resolution |
|---|---|
| Docs implying file tools auto-run | **Unlisted = approval_required** |
| A0-parity “full shell” as default | **Opt-in only**; parity is capability, not host root |
| SandboxManager “in-process” as security | **Rename narrative**: timeout helper, not sandbox; L0–L4 is the sandbox |
| Multiple file planes | Tools use workroot; bytes home is filesv2; UI lists both via API ids |
| “Install packages via shell” | **`packages_ensure` profiles only** (§5.4) — never free pip in chat loop |
| Prompt-only “must use tool X” | Enforced in code choke (§11), not prompt text |

Do not invent a second memory client or second chat loop.

---

## 9a. Architecture-audit hardening (agent stack)

Apply the 12-layer audit to every new tool wave:

| Layer | Control in Soma |
|---|---|
| 6 Tool selection | Capsule capabilities ∩ tool_policy; empty = deny |
| 7 Tool execution | Real executor only; no “claimed call without run” |
| 8 Tool interpretation | Structured JSON results; no silent rewrite |
| 11 Hidden repair | No second LLM that rewrites tool results without contract |
| 12 Persistence | Temporal history = IDs/manifests; cache never = live evidence |

**Severity findings to avoid (from A0 clone risk):** free shell (critical), unlisted auto (high — fixed), dual memory clients (critical — T-1), prompt-only tool gates (high — choke exists).

---

## 10. Definition of done

1. PathGuard rejects sibling-dir and absolute paths (tests green).  
2. New tools never auto-execute unless listed in `auto_execute`.  
3. “Write a research report” starts a Temporal workflow that completes without the chat session.  
4. Output file appears under workroot and in filesv2/Files tab.  
5. No shell string execution; no host path escape.  
6. Every tool action passes granular authz (§11).  
7. `check_docs.py` clean on this document.  
8. `packages_ensure` for profile `scientific` installs only allowlisted pins into workroot venv under Temporal approval — proven by unit/integration test, not prompt text.  
9. `artifact_create` kind=deck|document|sheet produces a real file under workroot (not a mock).  
10. Catalog §5.3/§5.4 rows are LIVE only when code+tests ship in the same change.

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

*End of SOMA-ARCH-TOOLS-001 v1.3.0*
