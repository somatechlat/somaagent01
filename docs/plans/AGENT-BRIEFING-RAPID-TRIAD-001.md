# AGENT BRIEFING — RAPID TRIAD 001

**Every agent dispatched under `2026-10-04-RAPID-TRIAD-001.md` receives this briefing verbatim, plus its own TASK block. An agent that has not read this file has not started.**

---

## 0. WHO YOU ARE, WHAT YOU MAY TOUCH

You are ONE specialist. Your TASK block names:
- **ONE repo** (or ONE file set if explicitly listed)
- **ONE defect class**
- **Exact file:line anchors**

**You may edit ONLY the files named in your TASK block.** If a fix requires touching a file outside your block: **STOP. Report it. Do not edit it.** Cross-cutting changes go back to the coordinator, not to you.

Never touch `somaAgent01` if your block says `somabrain`. Never touch `webui/` if your block says Python. This is not politeness — two agents editing one file is how the last session lost work.

---

## 1. READ BEFORE YOU WRITE (non-negotiable)

In this order. **No code until all four are read.**

1. `docs/standards/SOMA-RAPID-DEVELOPMENT-001.md` — Rules 1–12, THE ONE PATH, the two greps
2. `docs/standards/SOMA-STD-CODING-001.md` §§1–7 — the VIBE core
3. `docs/standards/SOMA-STD-CONFIG-001.md` — R-SEC/R-TOP/R-BEH/R-RES/R-VAL/R-SCL + AP-01…AP-07
4. **The two files named in your TASK block**, plus every caller of the function you are changing

If a document and the code disagree: **the code is what ships, the document is what must be corrected.** Report the disagreement. Do not build the fiction.

If context is missing → **ASK. Do not assume.**

---

## 2. THE LAW (condensed — the files above are the authority)

| | |
|---|---|
| **Rule 1** | **NO HARDCODED VALUES.** A default IS one. No literal URL/host/port/path/number in code, compose, tests or docs. |
| **Rule 2** | **NO FALLBACKS.** A value comes from a real setting or the call **refuses**. Deleting a fallback is always correct; replacing one is not. |
| **Rule 3** | **ONE CHAIN:** `Capsule > AgentSetting > InfrastructureConfig > SettingsModel > EMPTY`. ENV = bootstrap only, each required, never defaulted: `SA01_DEPLOYMENT_MODE`, `VAULT_ADDR`, `VAULT_TOKEN_FILE`, `POSTGRES_HOST`, `POSTGRES_PORT`. Every service URL is an administrator parameter. |
| **Rule 4** | **NO STUBS / MOCKS / SHIMS / TODOs / PLACEHOLDERS.** A shim is a bypass. Fix the consumer; never keep the old path alive. |
| **Rule 5** | **SECRETS — Vault only.** KV v2 `POST` **replaces** the document: read → merge → write full object → **read back and assert every key present**. Never write a secret to any file including `/tmp`. `VAULT_TOKEN` env is **banned**; `VAULT_TOKEN_FILE` only. |
| **Rule 6** | **FAIL-CLOSED (Rule 91).** A missing required value is a refusal naming the setting. |
| **Rule 7** | **NEVER WEAKEN A GATE TO PASS A TEST.** Absent credential ⇒ failure naming it. No dummy, no skip, no fake state. |
| **Rule 8** | **CHECK FIRST, CODE SECOND.** |
| **Rule 9** | **NO UNNECESSARY FILES.** Modify existing. **DELETE what is wrong — never back it up.** |
| **Rule 10** | **DOCUMENTATION = TRUTH.** |
| **Rule 11** | **COMMITS:** the user's own git identity. **No AI attribution of any kind** — no `Co-Authored-By`, no "Generated with Claude Code", no session links. Small coherent chunks. |
| **Rule 12** | **DESIGN CRITERIA:** the rules · millions of transactions · security · speed · latency · thin. |
| **Rule 84** | No mocks. Real Django ORM. |
| **Rule 91** | Zero-fallback / fail-fast on missing config. |
| **Rule 100** | All settings in `config/settings_registry.py`. |
| **Rule 164** | ALL secrets from Vault. Never env, never Django, never DB. |
| **Rule 245** | **No Python module exceeds 650 lines.** |
| **Rule 216** | Django 5+ backend sovereignty. |
| **Rule 124** | Real infra only — fail closed. |

### Anti-patterns AP-01…AP-07 — if you write any of these, stop and delete it
- **AP-01** invented key names (look first; `MEM_RECALL_LIMIT` was invented while `MEM_RECALL_TOP_K` existed)
- **AP-02** `getattr(settings, X, "http://localhost…")`
- **AP-03** a default duplicated in the model *and* a call site
- **AP-04** `or "default"` on an authz path
- **AP-05** a secret written to `os.environ`
- **AP-06** a second vocabulary for one concept
- **AP-07** `env.str(..., default="")` for a credential

### THE ONE PATH — never create a lane
Forbidden to create: a new WebSocket route or chat consumer · a new orchestrator or "just call the LLM directly" path · a new memory client, a direct SFM connection, or a second write path · a new auth check, role store, or settings resolver · a "temporary" endpoint · a parallel config file or `.env`-only path · a test-only settings override, fake Vault, or dummy credential.

**"A bypass is the same violation as a mock. Routing around a broken hop leaves the real consumer broken and the architecture rotting. Fix the hop."**

---

## 3. MANDATORY GREPS — run after EVERY edit, paste the output

```bash
# Must return NOTHING (only comments may match the first):
grep -rnE 'https?://|localhost|127\.0\.0\.1|host\.docker\.internal|:[0-9]{4,5}' <files you touched> | grep -v '^\s*#'
grep -rnE 'os\.environ\.get\([^)]*,[^)]+\)|\$\{[A-Z0-9_]+:-|getattr\([^,]+,[^,]+,\s*["\x27]http' <files you touched>
```

If either returns something you wrote: **you violated Rule 1. Fix it before reporting.**

---

## 4. HOW TO VERIFY — evidence, never assertion

1. Run the real command. Paste the **real output**.
2. If it needs a credential and the credential is absent: **report the failure naming the missing secret.** That is the correct outcome. Do not invent a token.
3. Never write "should work", "likely", "probably", "appears to". Either it ran or it did not.
4. Never claim a test passed unless you ran it and pasted the output.

**If you cannot verify it, say so explicitly.**

---

## 5. REQUIRED REPORT FORMAT — a report missing any section is rejected

```markdown
## REPORT: <agent name>

### 1. What I changed
| File:line | Before | After | Where the value comes from now |
|---|---|---|---|

### 2. Hardcoded values found
| File:line | Literal | What replaced it |
|---|---|---|

### 3. Fallbacks deleted
| File:line | Deleted fallback | Behaviour when missing now |
|---|---|---|

### 4. Verification — REAL OUTPUT ONLY
$ <command>
<paste output verbatim>

### 5. What I did NOT do
<list anything blocked, out of scope, or left for another agent — with the reason>

### 6. Disagreements found
<doc vs doc, doc vs code, or code vs code contradictions you hit. With file:line.>

### 7. Lane statement
I connected via the existing chain, and did not create a new lane.
```

Section 7 is mandatory. If you did create a lane, say so and revert it.

---

## 6. STOP CONDITIONS — stop and report, do not guess

Stop immediately and report if:
- Your TASK block points at a file that does not exist
- The fix requires editing outside your named file set
- A test needs a credential that is absent
- Two authorities disagree and you cannot tell which is correct
- You would have to add a fallback, a default, a shim, or a "temporary" path to make something pass
- You are about to create a file that already exists under another name

**Continuing past a stop condition is how the codebase rots.**

---

## 7. WHAT DRIFTED LAST TIME — do not repeat

Measured failures from the 2026-10-03/04 sessions:

| Drift | What happened | Your rule |
|---|---|---|
| Invented routes | 9 client methods posted to routes that do not exist, including `publish_reward` → `/learning/reward` called on **every chat turn** | Verify a route exists (`grep @router` in the server) before calling it |
| Lowercase settings | 67 settings declared lowercase; Django copies UPPERCASE only; every knob read as *unset* | Django names are UPPERCASE. Grep for `getattr(django_settings, key)`. |
| Second lane | An agent created `sfm_adapter.py` — a second dialect that wrote around the brain | T-1: the agent never holds an SFM client. It was deleted. Do not resurrect it. |
| Backup copies | Duplicate modules "kept just in case" | **Delete. Never back up.** |
| Phantom tests | A test named *"a service URL can be changed"* that never changes a URL | A test must assert the thing its name claims |
| Claimed passes | "6 passed" reported from an interrupted run | Paste output or say "not run" |
| Split credential | Brain token len 17, agent token len 64 — two generations of one trust boundary | One credential, seeded merge-safe, read back |

---

## 8. TASK BLOCK (template — the coordinator fills this)

```
AGENT:        <name>
REPO:         <path>
FILES YOU MAY EDIT:
  - <path:line range>
  - <path>
DEFECT:       <one paragraph, with the measured evidence>
FIX SHAPE:    <the contract to implement — not "fix it", the actual shape>
GATE:         <the command that proves it, and its expected output>
NEVER:        <task-specific prohibitions>
```

---

## WORKED EXAMPLE — the embedding-space fix (agent 13)

```
AGENT:        Embedding space fix
REPO:         /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01
FILES YOU MAY EDIT:
  - services/common/adapters/somabrain_adapter.py
  - services/common/memory_contract.py   (read-only unless the fix requires it)
DEFECT:
  somabrain_adapter.py:284-290 — `recall` sends
    {"query": query, "top_k": ..., "layer": "both", "tenant": ..., "namespace": ...}
  with NO `embedding` key. SomaBrain forwards text-only search to SFM, which
  then runs `HashEmbedder.embed(query)` (somafractalmemory admin/core/services.py:388-395).
  That is a DIFFERENT algorithm from the write path's `embed_text()`
  (memory_contract.py:261-281, SHA-256 token bag-of-words).
  Two vector spaces ⇒ cosine similarity is meaningless ⇒ recall returns noise.
  SOMA-ARCH-INVARIANTS-001.md §2.1 forbids this: "Never let a store re-embed."

FIX SHAPE:
  Compute the query vector with the SAME embedder the write path uses, at the
  SAME dimension, and send it TOP-LEVEL in the recall body — exactly as
  `remember` already does for `value.embedding`.
  - embedder: `embed_text(query, get_mem_embed_dim())` from memory_contract
  - dimension: `get_mem_embed_dim()` — 768, never a literal
  - key: top-level `embedding` in the recall request body
  - do NOT nest it in `payload` (SFM silently drops nested embeddings and
    hash-embeds instead, ranking the record × 0.25 — this bug shipped once)
  - if the brain's MemoryRecallRequest does not accept `embedding`, STOP and
    report it — that is a contract change and belongs to the coordinator.

GATE:
  pytest tests/e2e/test_triad_integration.py -v
  Expected: remember→recall returns the same row, score > 0, store == "somabrain".
  Paste the output. If infra is absent, report the missing service by name.

NEVER:
  - do not add a fallback embedder
  - do not change the write path
  - do not touch somafractalmemory
  - do not add a config knob for "embedding mode" — there is one embedder
```
