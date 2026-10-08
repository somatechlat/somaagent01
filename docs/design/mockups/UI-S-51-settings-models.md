# UI-S-51 — Settings — Models

**Settings — Models** — section **Models** inside the one Settings shell — routes `/settings/models` · `/agent/models` · `/platform/models`.
Chrome abbreviated (UI-S-00). Left section nav (7) is visible; Models is active.

**Field truth.** Card and modal edit **only** `ModelIn` (`somaAgent01/admin/llm/api.py` 117–135):
`name` · `display_name` · `model_type` · `provider` · `api_base` · `capabilities` · `priority` · `cost_tier` · `domains` · `ctx_length` · `limit_requests` · `limit_input` · `limit_output` · `vision` · `kwargs` · `is_active`.
No invented fields. Provider key is **not** a `ModelIn` field — it goes to Vault only.

```
┌─ UI-S-00 chrome (abbrev) ────────────────────────────────────────────────────────────────────────┐
│ ☰ SOMA    Settings · Models     [Search settings…]                           [Save] [Cancel]     │
├──────────────┬───────────────────────────────────────────────────────────────────────────────────┤
│ SECTION NAV  │  MODELS · card library                                    [Add model] [Keys →]    │
│  Agent       │  [Search…]   Type [All ▾]   Status [All ▾]   Used for [All ▾]                     │
│  Models   ●  │                                                                                   │
│  Voice       │  ┌─────────────────────────────────┐  ┌─────────────────────────────────┐          │
│  Interface   │  │ ● Active    chat     standard    │  │ ○ Inactive  chat     low         │          │
│  Tools       │  │ deepseek-2.8                     │  │ mimo-v2.6                        │          │
│  Integrations│  │ DeepSeek 2.8 · Groq              │  │ MiMo v2.6 · Custom               │          │
│  Advanced    │  │ api.groq.com/openai/v1           │  │ <custom-url>                     │          │
│              │  │ ──────────────────────────────── │  │ ──────────────────────────────── │          │
│              │  │ ctx 131072 · in 0 · out 8192     │  │ ctx 32768 · in 0 · out 4096      │          │
│              │  │ vision · priority 10             │  │ priority 50                      │          │
│              │  │ Used for: Chat · Help            │  │ Used for: —                      │          │
│              │  │ key ● saved in Vault             │  │ key ● saved in Vault             │          │
│              │  │ [Activate] [Edit] [Test]         │  │ [Activate] [Edit] [Test]         │          │
│              │  └─────────────────────────────────┘  └─────────────────────────────────┘          │
│              │                                                                                   │
│              │  Default LIVE: Groq · deepseek-2.8     ·  setup gate only when API says so         │
├──────────────┴───────────────────────────────────────────────────────────────────────────────────┤
│ status: <load / save state> · source: live endpoint · <n> models                                 │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Modal — model setup (click card / Add model)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ✕  Model setup · deepseek-2.8 · Groq · ● LIVE                                                   │
│ [ Normal ]   [ Advanced ]   [ Used for ]                                                         │
│                                                                                                │
│ ── NORMAL ────────────────────────────────────────────────────────────────────────────────────  │
│  Provider        [Groq                                    ▼]   ← ModelIn.provider                │
│                   (Groq, OpenAI, Anthropic, Custom / OpenAI-compatible, Ollama, …)               │
│  Custom URL      [https://api.groq.com/openai/v1           ]   ← ModelIn.api_base                │
│                   Empty = provider standard address. MiMo / gateway / local → paste URL.         │
│  Provider key    [____________] [Save to Vault]   ● saved                                       │
│                   Vault only · write-only · never files · never shown again.                     │
│  ┌─ Model list ──────────────────────────────────────────────────────────────────────────────┐   │
│  │ [ Load models ]   uses Key + Custom URL (or standard)                                     │   │
│  │ Source: live endpoint · 12 models · [Refresh]                                             │   │
│  │  ● deepseek-2.8          (click to select)                                                │   │
│  │  ○ deepseek-2.8-lite                                                                     │   │
│  │  ○ deepseek-r1                                                                           │   │
│  └───────────────────────────────────────────────────────────────────────────────────────────┘   │
│  Model ID        [deepseek-2.8             ]   ← ModelIn.name   (from list, or type manually)    │
│  Display name    [DeepSeek 2.8             ]   ← ModelIn.display_name                            │
│  Type            [Chat                      ▼]   ← ModelIn.model_type  chat | embedding          │
│  Price level     [low                        ▼]   ← ModelIn.cost_tier                             │
│                   free | low | standard | premium                                                 │
│  Sees images     [●]                         ← ModelIn.vision                                    │
│  Use this model  [●]                         ← ModelIn.is_active                                 │
│  [ Test connection ]                                                                               │
│                                                                                                │
│ ── ADVANCED ───────────────────────────────────────────────────────────────────────────────────  │
│  Context window  [131072]     ← ModelIn.ctx_length                                               │
│  Req/min         [0]          ← ModelIn.limit_requests                                           │
│  In-tok/min      [0]          ← ModelIn.limit_input                                              │
│  Out-tok/min     [0]          ← ModelIn.limit_output                                             │
│  Max output      [8192]       ← kwargs.max_tokens                                                │
│  Priority        [10]         ← ModelIn.priority                                                 │
│  Good at         [chat, reasoning]           ← ModelIn.capabilities (csv → list[str])            │
│  Used in         [general]                   ← ModelIn.domains     (csv → list[str])            │
│  Extra options   [ { "temperature": 0.7, … } ]  ← ModelIn.kwargs (JSON object)                   │
│                   Also accepts kwargs keys: max_tokens · timeout · ctx_history · max_embeds       │
│                                                                                                │
│ ── USED FOR ───────────────────────────────────────────────────────────────────────────────────  │
│  [✓] Chat    main conversation model                                                             │
│  [✓] Help    fast utility work                                                                   │
│  [ ] Memory  embeddings / vectors                                                                │
│  (binding labels only — API may use internal names; UI copy stays Chat / Help / Memory)          │
│                                                                                                │
│ [ Save model ]   [ Make live ]   [ Delete… ]                                                     │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Load models — backend contract

| Input | Meaning |
|---|---|
| provider | `groq` / `openai` / `anthropic` / `ollama` / `custom` / … |
| api_key (Vault) | auth to that endpoint (never leaves Vault) |
| api_base (Custom URL) | empty = vendor standard; else your URL |
| model_type | chat / embedding filter |

**Output:** list of model IDs + source (`live` | `registry` | `error`).
Click a row to fill `name`; or type `name` manually (private / gateway names).

## Collapsed card → ModelIn map

| Card line | Field |
|---|---|
| `● Active` / `○ Inactive` | `is_active` |
| `chat` / `embedding` chip | `model_type` |
| `cost: standard` | `cost_tier` |
| `deepseek-2.8` | `name` |
| `DeepSeek 2.8 · Groq` | `display_name` · `provider` |
| `api.groq.com/openai/v1` | `api_base` |
| `ctx 131072 · in 0 · out 8192` | `ctx_length` · `limit_input` · `limit_output` |
| `vision · priority 10` | `vision` · `priority` |
| `Used for: Chat · Help` | bindings (not ModelIn) |
| `key ● saved in Vault` | Vault status only |

## Seeded catalog (first-run defaults — Capsule / agent config data, not files)

| Provider | Models (seeded) | Notes |
|---|---|---|
| **Groq** | **deepseek-2.8** (LIVE), deepseek-2.8-lite, llama-3.3-70b, llama-3.1-8b, mixtral | default chat |
| OpenAI | gpt-4o, gpt-4o-mini, o4-mini, text-embed-3-small | embeddings seed |
| Anthropic | claude-sonnet, claude-haiku | |
| Custom URL | (empty until Load models) | MiMo v2.6, gateways |
| Ollama | llama3.1, qwen, nomic-embed-text | local |
| vLLM / LM Studio | (from Load models) | |

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-071 | model card | Whole `ModelIn` at a glance. Activate makes it live. |
| 2 | UI-C-117 | Add model / card Edit | Opens the modal. All 16 `ModelIn` fields editable across Normal + Advanced. |
| 3 | UI-C-118 | Load models | Calls live endpoint with Vault key + `api_base`. disabled-when: no key and provider requires auth — disabled-reason: "Save a provider key to Vault first." |
| 4 | UI-C-084 | Provider key (write-only) | Typed here → Vault only. When saved, renders `•••••• (saved in Vault)`. Never an editable echo of the secret. |
| 5 | UI-C-119 | Used for toggles | Chat / Help / Memory. Card shows the active labels. |
| 6 | UI-C-120 | Activate / Make live | One-click live. Default LIVE seed: Groq · deepseek-2.8. |
| 7 | UI-C-068 | Test connection | Calls the real connection test. Prints ok / ms / error on the card. |

**State variants.**

- **Loading.** Card skeletons + `loading` chip. No counts while loading.
- **Empty.** "Add a model + provider key."
- **Load models empty.** "No models returned from this endpoint. Check the Custom URL and key."
- **Error.** "Couldn't load models. ‹ reason from API ›" (also on card after a failed Test).
- **Setup gate.** Show the setup notice only when the API reports it.
- **Permission-denied.** "You don't have access to model settings. Requires the agent-owner role."
- **Offline.** "You're offline. Changes will not be saved until the connection returns."

**Modal overlays.** The model modal above (Normal / Advanced / Used for). UI-M-01 Drawer — key write (Vault, write-only). UI-M-03 Dialog — "Delete model `‹ name ›`?" (destructive).

**Route evidence.** `webui/src/main.ts` `'/settings/models' || '/agent/models'` and `'/platform/models'` → `soma-settings-models`. Field list matches `admin/llm/api.py` `ModelIn` 117–135.
