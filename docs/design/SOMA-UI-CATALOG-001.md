# SOMA-UI-CATALOG-001 — Curated UI/UX file set (Agent Soma)

## Document Control

| Field | Value |
|---|---|
| Document Title | Agent Soma — curated UI/UX catalog (every screen, click, field) |
| Document Identifier | SOMA-UI-CATALOG-001 |
| Version | 1.0.0 |
| Date | 2026-10-08 |
| Status | Draft |
| Source of truth | Live `somaAgent01` code + `somabrain` APIs. **No invented fields.** |
| Rule | Memory once · no “slot” · Capsules/Tools/Brain/Memory all real |

---

## 1. Read in this order

| # | File | Role |
|---|---|---|
| 1 | `SOMA-UI-NAV-001.md` | Real routes from `main.ts` + one-home rules |
| 2 | `SOMA-UI-NAV-AUDIT-001.md` | Duplicate / missing / orphan audit (fixes) |
| 3 | `SOMA-UI-CHAT-WORKSPACE-001.md` | Hero workspace bands A–E |
| 4 | `SOMA-UI-BINDINGS-001.md` | **Every click → real REST/WS** |
| 5 | `SOMA-UI-SPEC-001.md` / `SOMA-UI-SPEC-002.md` | Tokens + components |
| 6 | `docs/design/mockups/UI-S-*` + `UI-X-*` | Screen mocks |
| 7 | `somabrain/docs/project/SOMA-UI-MODEL-ADMIN-001.md` | Models cards (Used for) |
| 8 | `somabrain/docs/project/SOMA-UI-FIELD-PARITY-001.md` | AZ field parity |

---

## 2. Screen index (complete product)

### Auth
| ID | Screen | Route | Live view |
|---|---|---|---|
| UI-S-29 | Login | `/login` | `soma-login` |
| UI-S-30 | Register | `/register` | `soma-register` |
| UI-S-31 | Forgot / reset | `/forgot-password` | `soma-forgot-password` |
| UI-S-32 | MFA setup | `/mfa/setup` | `soma-mfa-setup` |
| UI-S-33 | Auth callback | `/auth/callback` | `soma-auth-callback` |

### Chat (hero)
| ID | Screen | Route | Live view |
|---|---|---|---|
| **UI-S-07** | **Chat workspace** | `/chat` | `soma-chat` |
| UI-S-08 | Message detail | in-chat inspect | `soma-message` |
| UI-S-09 | Conversation export | chat ⋮ → Export | `soma-chat` JSON |
| UI-S-10 | Message queue | composer queue | `soma-composer` |

### Memory (ONCE)
| ID | Screen | Route | Live view |
|---|---|---|---|
| **UI-S-04** | **Memory + dashboard** | `/memory` | `soma-memory-view` |

### Brain / Capsule / Tools
| ID | Screen | Route | Live API |
|---|---|---|---|
| UI-S-02 | Brain / cognition | `/cognitive` | `GET /api/v2/somabrain/cognitive/state/{agent_id}` |
| UI-S-11…14 | Capsules list/editor/version/instances | `/agents/{id}/capsule` | `GET/PATCH .../capsule` (`CapsuleConfigOut`) |
| UI-S-15…18 | Modules / capabilities | tools catalog | `GET /api/v2/tools` · `GET /tools/catalog` · `PUT /tools/catalog/{name}` |
| UI-X-01…08 | Canvas surfaces | chat right rail | see §4 |

### Settings (one shell)
| ID | Screen | Section | Live |
|---|---|---|---|
| UI-S-50 | Settings · Agent | personality, prompt, knowledge, limits | `soma-settings` |
| UI-S-51 | Settings · Models | cards + modal | `soma-settings-models` + `ModelIn` |
| UI-S-48-settings-voice | Settings · Voice | personas CRUD | `VoicePersona*` + synthesize/transcribe |
| UI-S-54-settings-interface | Settings · Interface | theme, language, timezone, prefs | `/aaas/admin/preferences` |
| UI-S-55-settings-tools | Settings · Tools | Capability enable + limits | `GET/PUT /tools/catalog` + agent limits |
| UI-S-52 | Settings · Integrations | Vault keys, channels | `PUT /secrets/providers/{id}` |
| UI-S-53 | Settings · Advanced | modules, quotas, API keys | `/platform/api-keys` |

### Platform / ops (enterprise)
UI-S-19…28 tenants/users/roles/billing · UI-S-34…45 profile/dashboards/audit/metrics · UI-S-46…49 voice/multimodal

### Chrome
| ID | Screen |
|---|---|
| UI-S-00 | Global chrome (top bar, facet tabs, instance strip, neuromod) |

---

## 3. Real domain fields (do not invent)

### Capsule (`admin/agents/api/schemas.py` CapsuleConfigOut/Update)
| Field | UI label |
|---|---|
| `capsule_id` | Capsule |
| `name` | Name |
| `description` | Description |
| `memory_config` | Memory |
| `learning_config` | Learning |
| (model FKs) | Used for: Chat / Help / Memory |

Route: `GET/PATCH /api/v2/agents/{agent_id}/capsule`

### Tools (`admin/tools/api/tools.py`)
| Schema | Fields | Endpoints |
|---|---|---|
| `ToolInfo` | name, description, parameters | `GET /api/v2/tools` |
| `ToolCatalogItem` | name, description, category, **enabled** | `GET /tools/catalog` · `PUT /tools/catalog/{name}` |

Canonical store: `admin.core.models.Capability` (`is_enabled`, `category`, `schema`).

### Models (`admin/llm/api.py` ModelIn — 16 fields only)
name · display_name · model_type · provider · api_base · capabilities · priority · cost_tier · domains · ctx_length · limit_requests · limit_input · limit_output · vision · kwargs · is_active  
Keys → **Vault only** `PUT /secrets/providers/{id}`.

### Memory (brain + agent)
| Action | Endpoint |
|---|---|
| List | `GET /api/v2/memory/` |
| Recall | `POST /api/v2/memory/recall` |
| Forget | `POST /api/v2/memory/forget` |
| Remember | `POST /api/v2/memory/remember` (via chat/tools) |
| WM/LTM counts | **no count API** — show `—` / GATED until real |

### Brain neuromod (real)
`GET /api/v2/somabrain/cognitive/state/{agent_id}` → `neuromodulators` flat dict  
DA · 5-HT · NE · ACh — **raw values only**, no fake % meters.

### Chat WS (real)
`WS /ws/v2/chat/{id}` — `chat.message|delta|done` · `tool.call|delta|done|approval_request` · `chat.pause|resume|stop|reset|nudge` · `tool.approval`

---

## 4. Canvas surfaces (chat right rail — no Memory tab)

| ID | Surface | Status | Binding |
|---|---|---|---|
| UI-X-01 | Files | LIVE | `GET /api/v2/filesv2/` |
| UI-X-02 | Tools | LIVE | `GET /api/v2/tools` + WS `tool.*` |
| UI-X-03 | Browser | **GATED** | “Bind a browser model on UI-S-02 first” |
| UI-X-04 | Editor | LIVE (RO) | file from UI-X-01 |
| UI-X-05 | Debug | LIVE | WS frame ring |
| UI-X-06 | Capsule | LIVE | `GET/PATCH /agents/{id}/capsule` |
| UI-X-07 | Brain | LIVE | cognitive state (same as UI-S-02) |
| UI-X-08 | Desktop | **GATED** | “Requires a remote-desktop capability…” |

---

## 5. Navigation law (one home)

| Feature | Home | Allowed entries | Forbidden |
|---|---|---|---|
| **Memory** | `/memory` | left rail, C2 Open Memory, ⋮, ⌘K | canvas tab, welcome card, mini-panel |
| **Models** | `/settings/models` | Settings, model chip | second library |
| **Tools** | `/settings` Tools + canvas Tools | Settings · Tools | duplicate catalog |
| **Capsule** | canvas Capsule + `/agents` | chat Agent ▾ | second editor |
| **Brain** | `/cognitive` + canvas Brain | facet, surface | orphan widgets |
| **Chat** | `/chat` | default | — |

---

## 6. Full flow map (every click)

```
LOGIN (UI-S-29)
  → POST /api/v2/auth/login → /chat WELCOME (UI-S-07 empty)
       ├─ Type → COMPOSER → WS send → stream + process groups
       ├─ Attach → filesv2 + composer chips
       ├─ Voice mic → POST /voice/transcribe
       ├─ Pause/Stop/Reset/Nudge → WS chat.*
       ├─ Tool expand → UI-S-08 (in stream)
       ├─ HITL Approve/Reject → WS tool.approval
       ├─ C2 Open Memory → /memory (UI-S-04)
       ├─ Canvas Files/Tools/Editor/Debug/Capsule/Brain → UI-X-*
       ├─ Browser/Desktop → GATED reason
       ├─ Left Memory → /memory
       ├─ Left Models / ⚙️ → /settings (UI-S-50…55)
       ├─ Model chip → /settings/models (UI-S-51)
       ├─ 👤 → /profile (UI-S-34)
       └─ ⋮ Rename/Export/Delete → REST /chat/conversations*
```

---

## 7. Acceptance (this catalog)

- [x] Every mock file listed with route + live view/API  
- [x] Capsule / Tools / ModelIn / Memory / neuromod fields = real schemas  
- [x] Memory once  
- [x] Canvas 8 surfaces honest  
- [x] Settings 7 sections  
- [x] BINDINGS-001 maps every control to REST/WS  
- [x] NAV-AUDIT names duplicates/missing/orphans  

**No product code claims without file:line. No invented metrics.**

End of Document
