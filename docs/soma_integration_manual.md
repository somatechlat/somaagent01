# SomaBrain & SomaAgentHub Integration Manual

This manual captures the current state of runtime integrations, the APIs that are live today, and the file-backed assets that still power Agent Zero. Use it as the source of truth when migrating behaviour, prompts, or knowledge into SomaBrain/SomaAgentHub services.

---

## 1. Runtime Integration Map

| Capability | Backing Service | Where Implemented | Notes |
| --- | --- | --- | --- |
| Long-term memory (store/recall/delete/export) | **SomaBrain** (`http://localhost:9696` by default) | `python/integrations/soma_client.py`, `python/helpers/memory.py` (`SomaMemory`, `_SomaDocStore`) | Fully integrated. All memory CRUD operations call SomaBrain via `SomaClient`. Docker compose sets `SOMA_BASE_URL` to `host.docker.internal:9696`. |
| Knowledge imports | SomaBrain | `python/helpers/memory.py` (`SomaMemory.preload_knowledge`) | Local FAISS preload is bypassed when SomaBrain is enabled; knowledge should be ingested via SomaBrain (API `migrate_import`). |
| Working-memory cache | SomaBrain | `python/helpers/memory.py` (`_SomaDocStore.refresh`) | Uses `migrate_export` with `SOMA_CACHE_INCLUDE_WM` and `SOMA_CACHE_WM_LIMIT` to warm local cache. |
| Health checks | SomaBrain | `python/integrations/soma_client.py::health()` | Returns `/health` payload from SomaBrain; call when validating environment. |
| Capsule/registry, policy, other orchestration | **SomaAgentHub** (`http://localhost:60010/openapi.json`) | _Not yet wired_ | Compose & docs reference the hub endpoints, but no Python code currently calls them. Integration hooks need to be added. |

### 1.1 SomaBrain client quick reference

`python/integrations/soma_client.py` exposes:

- `SomaClient.get()` – singleton accessor, honors env (`SOMA_BASE_URL`, `SOMA_API_KEY`, `SOMA_TENANT_ID`, `SOMA_NAMESPACE`, `SOMA_TIMEOUT_SECONDS`, `SOMA_VERIFY_SSL`).
- `remember(documents)` – POST `/memory/remember` to persist docs.
- `recall(query, k, threshold, filters)` – POST `/memory/recall` for semantic search.
- `delete(coordinate)` – DELETE `/memory/{coord}`.
- `migrate_export(include_wm, wm_limit)` – GET `/memory/export` for snapshot sync.
- `migrate_import(payload)` – POST `/memory/import` to restore snapshots.
- `health()` – GET `/health`.

Callers: `_SomaDocStore` wraps these primitives and the legacy `Memory` class still presents a FAISS-like API to upstream call sites.

### 1.2 SomaAgentHub status

- Expected OpenAPI document: `http://localhost:60010/openapi.json` (update older docs that still point at `60000`).
- No client is present in `python/integrations/` and no service references the Hub; integration is still on the roadmap (see `ROADMAP_SPRINTS.md`, `docs/connectivity.md`).
- To inspect the schema locally:

  ```bash
  curl http://localhost:60010/openapi.json | jq '.info, .paths'
  ```

  (The command above assumes the Hub service is running on the host. Adjust base URL if tunneled.)

- **Recommended landing zones once the client exists:**
  - `services/gateway/main.py` for request orchestration and policy checks.
  - `services/router/main.py` for runtime task routing data.
  - `python/somaagent/` package for shared SDK helpers (align with capsule registry client patterns).

---

## 2. File-backed Assets Still in Use

The agent still hydrates large portions of its behaviour from Markdown files. These should be the primary targets when moving content into SomaBrain or SomaAgentHub storage.

| Domain | Paths | Loader(s) | Purpose |
| --- | --- | --- | --- |
| **System prompts & templates** | `prompts/**/*.md` | `agent.Agent.read_prompt` → `python/helpers/files.read_prompt_file` | Core message scaffolding (`fw.*`, `agent.system.*`, tool instructions). Defaults in `prompts/`, persona overrides pulled from `agents/<profile>/prompts/`. |
| **Persona context** | `agents/<persona>/_context.md` | `agent.AgentConfig.profile` + `Agent.parse_prompt` | Seeds persona background, abilities, tone. |
| **Behaviour overrides** | `memory/<persona>/behaviour.md` | `python/extensions/system_prompt/_20_behaviour_prompt.py` | Injects bespoke behaviour block ahead of system prompt. |
| **Knowledge base** | `knowledge/<persona>/<area>/**/*.md` and `instruments/**` | `python/helpers/knowledge_import.load_knowledge` (TextLoader) | Source material ingested into memory store; when SomaBrain is active metadata is forwarded but ingestion is still file-triggered. |
| **Flow templates** | `prompts/fw.*.md` (e.g. `fw.user_message.md`, `fw.topic_summary.*`) | `agent.hist_add_user_message`, `python/helpers/history` | Template user and AI messages, topic summaries, warnings. |
| **Memory consolidation & tooling** | `prompts/memory.*.md`, `prompts/fw.document_query.*.md` | `python/helpers/memory_consolidation`, `python/helpers/document_query` | Provide LLM instructions for consolidation, document QA, etc. |
| **Legacy packaged assets** | `a0_data/` mirror of the above | `python/helpers/files.find_file_in_dirs` falls back here | Containers mount `a0_data`; keep in sync until remote storage replaces file dependency. |

> 🔍 **Audit commands**
>
> - `grep -R "\.md" python/` – locate code paths that still open Markdown files.
> - `find prompts agents knowledge memory -type f -name '*.md'` – enumerate current file artefacts.

### Migration guidance

1. **System prompts** – store canonical prompt bodies in SomaAgentHub (e.g. `/personas/{id}`) and replace `Agent.read_prompt` to fetch from the Hub with local cache fallback.
2. **Knowledge** – push knowledge documents via SomaBrain `migrate_import`. Maintain a checksum index so file watchers can trigger remote updates.
3. **Behaviour overrides** – surface persona “rules” as editable records in the Hub and drop the `memory/<persona>/behaviour.md` dependency once an API exists.
4. **Flow templates** – convert frequently-used templates (`fw.*`) into Hub-managed snippets; update call sites to retrieve by key instead of reading Markdown.

---

## 3. Manual Integration Checklist

1. **Confirm SomaBrain availability**
   - `curl -s ${SOMA_BASE_URL:-http://localhost:9696}/health | jq`
   - Run `python - <<'PY' ... SomaClient.health()` to ensure environment variables resolve correctly (see `python/integrations/soma_client.py`).

2. **Cache warm-up**
   - `await SomaMemory.refresh()` from a REPL to pull remote memories into local cache. Check logs for `[SomaClient] response` entries.

3. **Inspect SomaAgentHub schema**
   - `curl http://localhost:60010/openapi.json | jq '.paths | keys'`
   - Identify resources relevant to prompts/personas (e.g. `/personas`, `/prompts`, `/knowledge`) and map them to file-backed areas above.

4. **Introduce a Hub client**
   - Create `python/integrations/soma_agent_hub_client.py` mirroring the SomaBrain client structure: env-driven base URL (`SOMA_HUB_BASE_URL`), auth headers, shared `httpx.AsyncClient`.
   - Scaffold operations based on the OpenAPI spec (consider `datamodel-code-generator` or `httpx` + `pydantic` models).

5. **Refactor prompt/knowledge loaders**
   - Wrap `Agent.read_prompt` and `Agent.parse_prompt` to prefer Hub responses. Keep Markdown fallback until parity is reached.
   - Update `knowledge_import.load_knowledge` to optionally push changes via the Hub before (or instead of) local ingestion.

6. **Update documentation & configuration**
   - Add new env vars (`SOMA_HUB_BASE_URL`, `SOMA_HUB_API_KEY`, etc.) to `docker-compose.somaagent01.yaml`, `.env.example`, and `docs/development.md`.
   - Document the migration path in `docs/project_handbook.md` and `docs/features_overview.md` once live.

---

## 4. Known Gaps & Risks

- **Duplicate Markdown mirrors** – `a0_data/` mirrors `prompts/`, `agents/`, `knowledge/`. Once Hub storage is authoritative, remove the mirror or ensure sync tooling keeps artefacts aligned.
- **Docs referencing old Hub port (60000)** – Update `docs/connectivity.md` and any other references to use `60010`.
- **No Hub health checks in CI** – Extend test suites (`tests/integration/`) to cover SomaAgentHub interactions once implemented.
- **Fallback behaviour** – While migrating, ensure Hub outages degrade gracefully to Markdown + SomaBrain paths to avoid runtime regressions.

---

## 5. Quick Commands & Snippets

```bash
# List all Markdown assets backing prompts/knowledge
find prompts agents knowledge memory -type f -name '*.md' | sort

# Verify SomaBrain export/import endpoints
python - <<'PY'
import asyncio
from python.integrations.soma_client import SomaClient

async def main():
    client = SomaClient.get()
    print(await client.health())
    dump = await client.migrate_export(include_wm=False)
    print(f"memories exported: {len(dump.get('memories', []))}")

asyncio.run(main())
PY

# Inspect SomaAgentHub OpenAPI summary
curl http://localhost:60010/openapi.json | jq '.info'
```

Keep this manual current as integration work progresses. Whenever a Markdown dependency is eliminated or a new Hub endpoint comes online, update the tables and checklist so engineers and operators can track the migration state at a glance.
