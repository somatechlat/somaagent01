# SOMA-UI-BINDINGS-001 — Click-path map: every mock control → live API/WS

## Document Control

| Field | Value |
|---|---|
| Document Title | Agent Soma — UI mock control → live binding map |
| Document Identifier | SOMA-UI-BINDINGS-001 |
| Version | 1.0.0 |
| Date | 2026-10-08 |
| Status | Draft |
| Source of truth | Live Lit views + `admin/**/api.py` (code is truth) |
| Related | SOMA-UI-NAV-001 · SOMA-UI-CHAT-WORKSPACE-001 · UI-S-* · UI-X-* |
| Rules | **No inventions.** Every control binds to a real endpoint/WS frame or is **GATED** with a reason string. Memory once at `/memory`. No “slot” UI copy, no SaaS / Eye of God, no fabricated metrics. |

API base prefix: `/api/v2/` (`apiClient`). WS base: `/ws/v2/` (`main.ts:430-431`).

---

## 1. Chat workspace (UI-S-07 · routes `/` · `/chat` · `/chat/:id` · `/workspace`)

Live: `webui/src/views/soma-chat.ts` · composer `soma-composer.ts` · topbar `soma-chat-topbar.ts` · tools `soma-tool-timeline.ts` · registry `soma-right-panel.ts`.

| Screen | Control | Event | API / WS (exact path) | Request / response fields | Live source (file:line) |
|---|---|---|---|---|---|
| Chat | Send / Enter | `send-message` | **WS** `wss://…/ws/v2/chat/{capsule_id\|agent_id}` · frame `chat.message` | req: `{content, conversation_id, mode, attachments[{name,type,size,file_id?}]}` · stream in: `chat.delta` `{delta\|content, response_id}` · `chat.done` `{content, confidence, response_id}` · `chat.message` `{id, role, content, timestamp}` | send `soma-chat.ts:1764-1772`; WS open `1155-1267`; stream `1315-1372` |
| Chat | Pause | `soma-chat-control` `pause` | WS `chat.pause` | req: `{conversation_id}` · gateway `CONTROL_MSG_TYPES` | `soma-chat.ts:1572-1574`, `1607-1615`; `soma-chat-topbar.ts` |
| Chat | Resume | `resume` | WS `chat.resume` | same payload | `soma-chat.ts:1575-1578` |
| Chat | Stop | `stop` | WS `chat.stop` then local finalize | same payload | `soma-chat.ts:1580-1581`, `1618-1627` |
| Chat | Reset | `reset` | WS `chat.reset` + `POST /chat/conversations` | WS `{conversation_id}` · REST req `{agent_id}` → `{id}` | `soma-chat.ts:1583-1584`, `1629-1650`, `1060-1070` |
| Chat | Nudge | `nudge` | WS `chat.nudge` | req: `{conversation_id}` · server `chat.nudged` | `soma-chat.ts:1586-1588`, `1607-1615` |
| Chat | Tool expand / collapse | `click` step header | **local** (`_expanded` map) over live WS tool frames | in: `tool.call` · `tool.delta` `{tool_call_id, name, arguments_delta, iteration, index}` · `tool.done` `{result, ok, error, duration_ms, status}` | expand `soma-tool-timeline.ts:275-276`, `331-338`; frames `soma-chat.ts:1178-1186`, `1468-1528` |
| Chat | HITL Approve | `tool-approval` `{approved:true}` | WS `tool.approval` | req: `{conversation_id, tool_call_id, name, approved}` · in: `tool.approval_request` sets `approval_required` | `soma-tool-timeline.ts:310`, `375-381`; `soma-chat.ts:1531-1561` |
| Chat | HITL Reject / Deny | `tool-approval` `{approved:false}` | WS `tool.approval` | same fields | `soma-tool-timeline.ts:382-384`; `soma-chat.ts:1547-1561` |
| Chat | Rename conversation | confirm | `PATCH /chat/conversations/{id}` | req: `{title}` | `soma-chat.ts:1072-1088`, `2021-2028` |
| Chat | Delete conversation | confirm | `DELETE /chat/conversations/{id}` | — | `soma-chat.ts:1091-1103`, `2065-2077` |
| Chat | Export conversation | click download | `GET /chat/conversations/{id}/messages` (if not active) + **client** Blob download | resp rows: `{id, role, content, created_at, metadata.confidence}` | `soma-chat.ts:1105-1141`, `2054-2063` |
| Chat | Queue while busy | send while `busy` | **local** `soma-composer` `_queue`; drain on idle → same WS `chat.message` | queue chip count + drop clears `_queue` | `soma-composer.ts:352-356`, `392-395`, `411-413`, `603-615` |
| Chat | Drop queue | close on chip | local `_queue = []` | — | `soma-composer.ts:411-413` |
| Chat | New Chat | click | `POST /chat/conversations` | req `{agent_id}` → `{id}` | `soma-chat.ts:1784-1801`, `1060-1070` |
| Chat | Conversation select | click row | `GET /chat/conversations/{id}/messages` | resp: message rows | `soma-chat.ts:1804-1834` |
| Chat | Conversation list | load | `GET /chat/conversations` | `{id, title, last_message, updated_at, message_count?}` | `soma-chat.ts:1033-1058` |
| Chat | Conversation search | input | **local filter** over already-loaded list | — | `soma-chat.ts:1868-1876`, `1914-1925` |
| Chat | Mic / STT | stop recording | `POST /voice/transcribe` | req `{audio_base64, format: webm\|m4a\|ogg, language: null}` → `{text}` | `soma-composer.ts:424-508`, `488-492`; route `admin/voice/api.py:69-86` |
| Chat | Attach (+ menu) | file pick | **local** `composerStore` → on send **REST** `POST /api/v2/filesv2/upload` (+ presigned `PUT` or `POST /api/v2/filesv2/upload-local/{file_id}`); `file_id` rides WS `chat.message.attachments`; upload failure lands on the user message, never a guessed id | `{name, type, size, file_id?}` · identity `{id, tenant_id}` from `GET /auth/me` | `soma-composer.ts:536-553`; upload `services/file-upload.ts`; send `soma-chat.ts` `_deliverUserMessage` |
| Chat | Clear chat (composer menu) | event | **local** clear transcript | — | `soma-chat.ts:1652-1656` |
| Chat | Export chat (composer menu) | event | **client** Blob of `_messages` | — | `soma-chat.ts:1658-1691` |
| Chat | Agent select | change | `GET /agents/` then **WS reconnect** `/ws/v2/chat/{wsId}` | agents: `{agent_id, name, description, capsule_id?}` | `soma-chat.ts:1004-1031`, `2370-2380` |
| Chat | Mode STD/DEV/RO/DGR | select | **local** `mode` on next `chat.message` payload | `mode: AgentMode` | `soma-chat.ts:2364-2368`, `897-904`; send `1769` |
| Chat | Mode TRN / ADM | locked | **GATED** — reason: locked in this build (mode list `locked: true`) | — | `soma-chat.ts:900-901`, `2205-2206` |
| Chat | User card | load | `GET /auth/me` | `{name?, username?, email?, role?}` | `soma-chat.ts:984-1001` |
| Chat | Logout | click | `POST /auth/logout` (`apiClient.logout`) then `/login` | — | `soma-chat.ts:1846-1861`; `admin/auth/api.py:316` |
| Chat | **Brain micro-indicator** ◉ (12px) | health | `GET /core/brain-connector` | `{connected, circuit, last_error?}` | `soma-chat.ts:963-982` → `soma-status-dot` |
| Chat | Sync ○ / Memory ◌ aides | same | brain-connector + memory list | status only | `soma-status-dot` |
| Welcome | Connect Channels cards | bridges | `GET /api/v2/bridges/channels` | kinds `telegram`/`whatsapp` + email handlers | `soma-chat` welcome |
| Welcome | System RAM/CPU/Disk | diagnostics | `GET /api/v2/somabrain/admin/diagnostics` | psutil cpu/ram/disk | `soma-chat` welcome |
| Chat | Turn meta strip (model · context · lanes · recall) | WS | `chat.turn_meta` | `{model, lanes{}, memory_hits[{text,score,kind}], context_tokens}` | `soma-chat.ts:1190-1197`, `1479-1491`, `2106-2157` |
| Chat | Title | WS | `title_update` + PATCH title | `{title, conversation_id?}` | `soma-chat.ts:1198-1203` |
| Chat | Surface rail toggle | click | local show/hide `soma-right-panel` | — | `soma-chat.ts:2332-2354` |
| Chat | Nav Memory / Models / Channels / Settings | click | SPA `soma-navigate` → routes in §7 | — | `soma-chat.ts:1951-1963`, `1842-1844` |

### Right-rail surfaces (UI-X-01…08) — `soma-right-panel.ts`

| Screen | Control | Event | API / WS | Request / response | Live source |
|---|---|---|---|---|---|
| UI-X-01 Files | list | tab open | `GET /filesv2/?page=1&per_page=50` | `FileListResponse {files[FileOut], total, page, per_page}` | `soma-right-panel.ts:708-725`, `98-117` |
| UI-X-01 | open file | click row | `GET /filesv2/{id}/download-url` then GET signed URL | `DownloadUrlOut {download_url, expires_in, filename}` | `727-751` |
| UI-X-02 Tools | list + schema expand | tab / button | `GET /tools` + **WS** `tool.call` / `tool.done` ring buffer | `{tools[ToolInfo], count}`; schema = `parameters` | `756-770`, `891-979`, `230-245` |
| UI-X-03 Browser | surface | select | **GATED** — `blockedReason: "Bind a browser model on UI-S-02 first"` (no browser model on `/llm/slots`, no viewport backend) | — | `62-65`, `982-996` |
| UI-X-04 Editor | read buffer | from Files | signed download only; **read-only** — no file-write endpoint | text body | `999-1036`, `727-751` |
| UI-X-05 Debug | frame log + filter + Clear stream | input / click | **local** `wsFrameLog` from live WS frames | `{id, type, dir, ts, payload}` | `1039-1097`; `websocket-client.ts` |
| UI-X-06 Capsule | editor | tab | `GET /agents/{id}/capsule` · `PATCH /agents/{id}/capsule` · `POST /agents/{id}/archive` | capsule config fields | `soma-capsule-editor.ts:315`, `338`, `363` |
| UI-X-07 Brain | cognitive panel | tab | same endpoints as UI-S-02 (below) — **same component**, not a second Brain UI | — | `soma-right-panel.ts:833`; `soma-cognitive-panel.ts` |
| UI-X-08 Desktop | surface | select | **GATED** — `blockedReason: "Requires a remote-desktop capability in somaAgent01. Not available today."` | — | `70-77`, `1117-1128` |

---

## 2. Memory — **ONCE** at `/memory` (UI-S-04 · `soma-memory-view.ts`)

One Memory UI. Entries (left rail, C2 Open Memory, ⋮, ⌘K) all navigate here — never a second surface (`UI-S-04`, `SOMA-UI-NAV-001` §3).

| Screen | Control | Event | API / WS (exact path) | Request / response fields | Live source |
|---|---|---|---|---|---|
| Memory | List / Refresh | load / Refresh | `GET /memory/` | `{memories[{text, coord, score, store, created_at, content?, kind?}], total, tenant_id}` | `soma-memory-view.ts:705-724`, `832-834`; `admin/memory/api/memory.py:58-78` |
| Memory | Search / recall (probe) | Enter on search | `POST /memory/recall` | req `{query}` (`top_k` omitted → server default 10) · resp `{memories[], total, query}` | `736-759`; `memory.py:81-101`, `29-31` |
| Memory | Run probe (button) | click | same `POST /memory/recall` | same | mock `UI-S-04` #2 (design §5 chrome; call is the live recall above) |
| Memory | Forget / Delete | confirm | `POST /memory/forget` | req `{coord}` → `{forgotten, coord, memory_id}` | `803-818`; `memory.py:144-159` |
| Memory | Forget alt | — | `DELETE /memory/{coord}` (prefer POST body for comma coords) | same | `memory.py:162-178` |
| Memory | Save (agent write lane) | API only | `POST /memory/save` | req `{text, kind, salience}` → `{saved, memory_id, tenant_id, acks[]}` | `memory.py:104-137` |
| Memory | Total Memories | sidebar stat | `response.total` from `GET /memory/` | number or `—` until server reports | `soma-memory-view.ts:586-592`, `716` |
| Memory | Export JSON | click | **client** Blob of loaded rows | — | `821-830` |
| Memory | Copy | click | `navigator.clipboard` | — | `798-801` |
| Memory | Type filter chips · Sort | click / change | **client** filter/sort over server rows | kinds only when server sent them | `761-792` |
| Memory | Dashboard WM / LTM counts | tiles | **GATED / design §5** — no dedicated WM/LTM count field on `GET /memory/` or `POST /memory/recall`. Server may send per-hit `store`; aggregate tiles render `—` until an API reports them. Never invent counts. | design `UI-S-04` §3 | `memory.py:58-101`; `UI-S-04-memory.md:97-103` |
| Memory | Layer filter `wm\|ltm\|both` | chip | **GATED / design §5** — client filter only when server sends store layer on hits | `store` per hit | `UI-S-04` #3 |
| Memory | This-turn filter / hits (`?turn=current`) | route + clear | **GATED / design §5** — filter over hits already in `chat.turn_meta.memory_hits` or `/memory/`; no separate turn API | `memory_hits[]` | `UI-S-04` #4-5; `soma-chat.ts:1479-1491` |
| Memory | Open record drawer | click | **local** over a loaded hit | fields already on the row | `UI-S-04` #11 |
| Memory | Kafka metrics (not on this screen) | — | `GET /memory/metrics` | `{kafka}` | `memory.py:191-207` |

**Anti-triplication:** Chat C2 is a **readout + route link** only (`chat.turn_meta.memory_hits` → navigate `/memory`). Canvas has **no Memory tab**. Cognitive `memory_stats` is Brain-only, not a Memory UI.

---

## 3. Brain / neuromod (UI-S-02 · UI-X-07 · `/cognitive` · `/training`)

| Screen | Control | Event | API / WS | Request / response | Live source |
|---|---|---|---|---|---|
| Brain | Neuromod DA / 5-HT / NE / ACh (raw name→value) | load | `GET /somabrain/cognitive/state/{agent_id}` | `CognitiveStateResponse {agent_id, neuromodulators: dict, adaptation_params: dict, memory_stats: dict, last_sleep, degraded}` | `soma-cognitive-panel.ts:729-779`; `admin/somabrain/cognitive.py:247-277`, `75-83` |
| Brain | Adaptation params (learningRate, explorationRate, attentionSpan) | number input | same state read; dirty local | `adaptation_params` untyped dict | `soma-cognitive-panel.ts:702-727`, `767-769` |
| Brain | Memory params (memoryConsolidation, emotionalSensitivity) | number input | same | same dict keys | `656-657` |
| Brain | Apply Changes | click | `PATCH /somabrain/cognitive/params/{agent_id}` | req: params dict → `{agent_id, updated_params, success}` | `786-800`; `cognitive.py:280-309` |
| Brain | Trigger Sleep Cycle | click | `POST /somabrain/cognitive/sleep/{agent_id}` | req `SleepCycleRequest {duration_minutes, consolidate_memory}` → `{status, memories_consolidated, …}` | `803-821`; `cognitive.py:346-385` |
| Brain | Reset Adaptation | confirm | `POST /somabrain/cognitive/adaptation/reset/{agent_id}` | → `{agent_id, status, result}` | `823-841`; `cognitive.py:312-338` |
| Brain | Sleep status | read | `GET /somabrain/cognitive/sleep/status/{agent_id}` | `{is_sleeping, last_sleep, next_scheduled}` | `cognitive.py:388-416` |
| Brain | SomaBrain Connected badge | derived | true when state GET succeeds | — | `soma-cognitive-panel.ts:756` |
| Brain | Activity log | client log of real actions | **local** only (save / sleep / reset / load fail) | — | `740-743`, `792-795`, `811-814` |
| Brain | Percentage neuromod meters | — | **GATED** — REQ-UIX-010: API sends no min/max/unit and no `last_synced_at`; raw values only | — | `soma-cognitive-panel.ts:23-25`, `607-619`, `688-699` |
| Brain | Sliders with min/max | — | **GATED** — server dict has no declared scale; number inputs only | — | `702-704` |

Real read path for DA/5-HT/NE/ACh: **only** `GET /api/v2/somabrain/cognitive/state/{agent_id}` → `neuromodulators` (flat `name → number`). Status-bar neuromod meters (CHAT-WORKSPACE §E) are **GATED** until that API is bound into the strip — never fabricate (`UI-S-07` §3 E row).

---

## 4. Models (UI-S-51 · `/settings/models` · `/agent/models` · `/platform/models`)

Backend: `admin/llm/api.py` (`ModelIn` 117–135). UI: `soma-settings-models.ts`.

| Screen | Control | Event | API / WS | Request / response | Live source |
|---|---|---|---|---|---|
| Models | List models | load | `GET /llm/models` | `ModelOut[]` (`id, name, display_name, model_type, provider, api_base, capabilities, priority, cost_tier, domains, ctx_length, limit_*, vision, kwargs, is_active, created_at, updated_at`) | `soma-settings-models.ts:375`; `llm/api.py:462-480` |
| Models | Used-for badges (Chat/Help/Memory) | load | `GET /llm/slots` | `{chat_model_id, utility_model_id, embedding_model_id, capsule_id, scope}` | `376`; `llm/api.py:560-587` |
| Models | Key status chip | load | `GET /secrets/providers` | `[{provider, configured}]` | `377-382`; `admin/secrets/api.py:58-74` |
| Models | Activate / Make live | click | `PATCH /llm/models/{id}` `{is_active:true}` then `PUT /llm/slots` | slots body: `chat_model_id` / `embedding_model_id` / optional `utility_model_id` | `419-434`; `llm/api.py:526-538`, `590-635` |
| Models | Used for role bind | click | `PUT /llm/slots` | `{chat_model_id\|utility_model_id\|embedding_model_id: id}` | `436-441` |
| Models | Save to Vault (key) | click | `PUT /secrets/providers/{provider}` | req `{api_key}` (write-only) → `{detail: saved_to_vault\|…}` | `455-469`; `secrets/api.py:81-110` |
| Models | Load models (live catalog) | click | `POST /llm/models/search` | req `{provider, query, model_type, api_base, api_key?}` → `{models[], source: live\|registry\|none\|error, detail}` | `471-497`; `llm/api.py:737-844` |
| Models | Save model (create) | click | `POST /llm/models` | `ModelIn` fields only | `509-512`; `llm/api.py:483-514` |
| Models | Save model (update) | click | `PATCH /llm/models/{id}` | `ModelPatch` | `509-510`; `llm/api.py:526-538` |
| Models | Test connection | click | `POST /llm/test-connection` | req `{provider, model?, base_url?, api_key?, model_id?}` → `{success, latency_ms, detail}` | `524-545`; `llm/api.py:852-928` |
| Models | Delete model | confirm | `DELETE /llm/models/{id}` | `{deleted, id}` | `547-553`; `llm/api.py:541-552` |
| Models | Presets (if used) | — | `GET/POST /llm/presets` · `POST /llm/presets/{id}/apply` · `DELETE /llm/presets/{id}` | `PresetIn/Out` | `llm/api.py:648-729` |
| Models | Setup gate | read | `GET /llm/setup-gate` | `{needs_setup, active_models, chat_ready, utility_ready, embedding_ready, message}` | `llm/api.py:931-963` |
| Models | Provider registry | read/update | `GET /llm/providers` · `PUT /llm/providers/{id}` | `ProviderOut {id,label,enabled,base_url,model_name,is_custom,has_api_key}` | `llm/api.py:381-454` |

**API key never enters `ModelIn`** (`llm/api.py:11`, `138-139`). Vault path: `secret/agent/api_keys/{provider}_api_key` (`secrets/api.py:3-4`).

---

## 5. Voice (UI-S-46/47/48 · `/voice*`)

| Screen | Control | Event | API / WS | Request / response | Live source |
|---|---|---|---|---|---|
| Composer / Voice | Transcribe | mic stop | `POST /voice/transcribe` | `{audio_base64, format, language}` → `{text}` | `soma-composer.ts:488-492`; `voice/api.py:69-86` |
| Voice | Synthesize | play | `POST /voice/synthesize` | `SynthesizeRequest` → `SynthesizeResponse` | `voice/api.py:89-106` |
| Voice | List voices | load | `GET /voice/voices` | `VoiceListResponse` | `voice/api.py:109-118` |
| Voice | Service status | load | `GET /voice/status` | `VoiceStatusResponse` | `voice/api.py:121-128` |
| Voice personas | List | load | `GET /voice/personas?active_only=&page=&page_size=` | `VoicePersonaListOut` | `soma-voice-personas.ts:257-258`; `voice/api.py:174-193` |
| Voice personas | Create | save | `POST /voice/personas` | `VoicePersonaCreate` | `soma-voice-personas.ts:360`; `voice/api.py:196-205` |
| Voice personas | Update | save | `PUT /voice/personas/{id}` | `VoicePersonaUpdate` | `358`; `voice/api.py:220-233` |
| Voice personas | Delete | confirm | `DELETE /voice/personas/{id}` | — | `331`; `voice/api.py:236-244` |
| Voice personas | Set default | click | `POST /voice/personas/{id}/set-default` | — | `320`; `voice/api.py:247-255` |
| Voice personas | LLM options | load | `GET /voice/llm-configs?model_type=chat` | active LLM configs | `269-270`; `voice/api.py:162-171` |
| Voice personas | TTS model list | load | `GET /voice/models` | `VoiceModelListOut` | `281-282`; `voice/api.py:313-322` |
| Voice sessions | List + stats | load | `GET /voice/sessions` · `GET /voice/sessions/stats` | `VoiceSessionListOut` · `VoiceSessionStats` | `soma-voice-sessions.ts:203-204`; `voice/api.py:263-294` |
| Voice sessions | Terminate | click | `POST /voice/sessions/{id}/terminate` | — | `334`; `voice/api.py:297-305` |
| Voice chat | Live stream | WS | `wss://…/ws/voice/?tenant_id=…` | voice session frames | `voice-chat-controller.ts:157` |
| Voice | Streaming transcription | call | **GATED** — `POST /voice/transcribe/stream` always 503: needs Django Channels WS consumer not wired | `ServiceUnavailableError voice_stream` | `voice/api.py:131-154` |

---

## 6. Status bar / strip metrics — real sources only

| Metric (UI-S-07 band E / turn meta) | Source | Live source |
|---|---|---|
| Model | WS `chat.turn_meta.model` | `soma-chat.ts:1485-1487` |
| Context tokens | WS `chat.turn_meta.context_tokens` | `1488-1490`, `2116-2118` |
| Lanes (5-lane governor) | WS `chat.turn_meta.lanes` | `2119-2127` |
| Memory recall count / hits | WS `chat.turn_meta.memory_hits[]` | `2128-2155` |
| Tools this turn | WS `tool.call` / `tool.done` count in `_activeTools` | `1468-1528` |
| Queue | composer `_queue.length` | `soma-composer.ts:603-615` |
| Connection | `GET /core/brain-connector` + WS connect/disconnect | `soma-chat.ts:963-982`, `1204-1241` |
| DA / 5-HT / NE / ACh in status strip | **GATED** — bind `GET /somabrain/cognitive/state/{agent_id}` first; never invent meters | `UI-S-07` §3 E; `cognitive.py:247-277` |

---

## 7. GATED surfaces — reason strings only

| Surface / control | Reason string (verbatim source) | Source |
|---|---|---|
| UI-X-03 Browser | “Bind a browser model on UI-S-02 first” | `soma-right-panel.ts:64` |
| UI-X-08 Desktop | “Requires a remote-desktop capability in somaAgent01. Not available today.” | `soma-right-panel.ts:75-76` |
| UI-X-04 Editor write | “This deployment exposes no file-write endpoint; the buffer is read-only.” | `soma-right-panel.ts:1032-1034` |
| `/themes` Skins | “Capsule-owned skins are specified in SOMA-UI-SKINS-001 and not implemented yet. Appearance is compiled into component styles. The only appearance control available today is light / dark polarity.” | `main.ts:370-374` |
| `/reset-password` | “no password-reset route is mounted in admin/auth/api.py (mounted: /token /refresh /me /logout /login /register /impersonate plus /sso /oauth /mfa)” | `main.ts:99-105` |
| `/verify-email` | “no email-verification route is mounted…” (same mount list) | `main.ts:99-105` |
| Mode TRN / ADM | locked in mode list (`locked: true`) | `soma-chat.ts:900-901` |
| Neuromod % meters | No min/max/unit, no `last_synced_at` (REQ-UIX-010) | `soma-cognitive-panel.ts:23-25` |
| Adaptation sliders | Server dict has no declared min/max/step | `soma-cognitive-panel.ts:702-704` |
| Memory dashboard WM/LTM tiles | No count fields on `/memory/*`; tiles show `—` until API reports | `UI-S-04` §3; `memory.py:58-101` |
| Voice stream transcribe | “Real-time streaming transcription requires Django Channels WebSocket support, which is not yet implemented.” | `voice/api.py:150-154` |
| Band-E neuromod + ⌘K + 🔔 + Voice left-rail (design chrome) | Not wired in `soma-chat.ts` — excluded until a real binding exists | `UI-S-07` §3 |

---

## 8. NAV completeness — every `main.ts` route ↔ mock

| `main.ts` route | View | Mock / binding note |
|---|---|---|
| `/login` | `soma-login` | UI-S-29 · `POST /auth/login` |
| `/register` · `/onboarding` · `/invite/*` | `soma-register` | UI-S-30 · `POST /auth/register` |
| `/forgot-password` | `soma-forgot-password` | UI-S-31 |
| `/reset-password` · `/verify-email` | notice only | UI-S-31 note · **GATED** (reason §7) |
| `/auth/callback` | `soma-auth-callback` | UI-S-33 |
| `/logout` | redirect | `POST /auth/logout` |
| `/` · `/chat` · `/chat/:id` · `/soma/chat` · `/workspace` · default | `soma-chat` | **UI-S-07** |
| `/memory` | `soma-memory-view` | **UI-S-04** (only Memory) |
| `/settings` | `soma-settings` | UI-S-50 shell · `GET /config/flags`, `/secrets/providers`, `/auth/me` |
| `/settings/models` · `/agent/models` · `/platform/models` | `soma-settings-models` | UI-S-51 |
| `/settings/channels` · `/agent/channels` | `soma-settings-channels` | UI-S-52 · `/bridges/channels`, `/modules` |
| `/settings/multimodal` · `/agent/multimodal` | `soma-multimodal-settings` | UI-S-49 · `/agents/{id}/multimodal-config` |
| `/cognitive` · `/training` | `soma-cognitive-panel` | UI-S-02 / UI-X-07 |
| `/voice` · `/voice/chat` · `/platform/voice/chat` | `soma-voice-chat` | UI-S-46 |
| `/voice/personas` · `/platform/voice/personas` | `soma-voice-personas` | UI-S-48 |
| `/voice/sessions` · `/platform/voice/sessions` | `soma-voice-sessions` | UI-S-47 |
| `/profile` · `/admin/profile` · `/platform/profile` | personal / platform profile | UI-S-34 / UI-S-35 |
| `/mfa/setup` · `/settings/mfa` | `soma-mfa-setup` | UI-S-32 · `POST /auth/mfa/*` |
| `/themes` | disabled notice | **GATED** (skins) |
| `/soma/dashboard` · `/soma` · `/platform` · `/admin/metrics` | `soma-agent-metrics` | UI-S-37/45 · `/observability/tenant-usage` |
| `/platform/infrastructure` · ratelimits aliases | `soma-infrastructure-dashboard` | UI-S-39/40 |
| `/platform/integrations` · `/soma/settings/integrations` | `soma-integrations-dashboard` | UI-S-41 |
| `/platform/roles` · matrix/permissions aliases | `soma-admin-roles-list` | UI-S-23/24 |
| `/platform/api-keys` | `soma-admin-api-keys` | UI-S-53 · `/aaas/settings/api-keys` |
| `/platform/metrics` · `/soma/metrics` | `platform-metrics-dashboard` | UI-S-38 |
| `/platform/audit` · `/soma/audit` · `/audit` · `/admin/audit` | `soma-audit-dashboard` | UI-S-43/44 · `/aaas/audit/*` |
| `/platform/settings/{entity}` | `settings-form` | UI-S-50 · `GET/PUT /config/{entity}` |
| `/admin/users` | `soma-users-view` | UI-S-22 |
| `/admin/users/{id}` | `soma-user-detail` | UI-S-22 detail |
| `/admin/agents` | `soma-agents-view` | UI-S-15 |

**Acceptance:** every row above has a mock or an explicit GATED reason. Zero controls without a real binding or GATED. Memory implemented once (`/memory`). Neuromod DA/5-HT/NE/ACh read path is exactly `GET /somabrain/cognitive/state/{agent_id}`.

End of Document
