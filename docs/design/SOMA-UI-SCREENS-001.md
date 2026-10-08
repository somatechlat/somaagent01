# SOMA-UI-SCREENS-001 — Implemented screens · flows · mock sync

## Document Control

| Field | Value |
|---|---|
| Document Title | Implemented screens, agent flows, and mockup sync |
| Document Identifier | SOMA-UI-SCREENS-001 |
| Version | 1.1.0 |
| Date | 2026-10-08 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2027-01-08 |
| Related | `SOMA-UI-MOCKUPS-001`, `SOMA-UI-IA-001`, `SOMA-UI-IDREG-001`, `SOMA-ARCH-TOOLS-001`, `SOMA-01-UIUX-001` |
| Source of truth | Live `webui/src/main.ts` routes + `docs/design/mockups/` |
| Audience | Agents implementing UI; design reviewers |
| Scope | Screen inventory, primary agent flows, mock annex sync — no product code |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-08 | SomaTech Engineering | Initial issue. Full screen inventory, agent flows, mock index sync (UI-S-56/57). |
| 1.1.0 | 2026-10-08 | SomaTech Engineering | UI-S-56/57 corrected to live-API-only fields; tool_policy 3-bucket and capabilities PUT marked GAP (no HTTP). |

---

## 1. Design direction (binding for new UI)

- **Product:** operator + assistant agent console (Lit 3.x only).
- **Audience:** daily chat users; sysadmin configuring tools/brain.
- **Tone:** dense, quiet, scannable — not marketing.
- **Memorable detail:** A0 chrome (composer hero, thin status, left-rail Memory+Settings) + honest degradation chips (Memory queued, CTX %).
- **Icons:** Material Symbols only — **no emoji**.
- **Honesty:** every disabled control prints a blocking reason; secrets masked; live API fields only.

---

## 2. Implemented routes (sync table)

| Route | View module | Mock | Status |
|---|---|---|---|
| `/login` | `soma-login` | UI-S-29 | implemented |
| `/register` | `soma-register` | UI-S-30 | implemented |
| `/forgot-password` | `soma-forgot-password` | UI-S-31 | implemented |
| `/reset-password`, `/verify-email` | inline notice | — | honest disabled |
| `/auth/callback` | `soma-auth-callback` | UI-S-33 | implemented |
| `/` `/chat` `/workspace` | `soma-chat` | UI-S-07 | implemented |
| `/memory` | `soma-memory-view` | UI-S-04 | implemented (queued amber) |
| `/cognitive` `/training` | `soma-cognitive-panel` | UI-S-02 / UI-X-07 | implemented |
| `/settings` | `soma-settings` | UI-S-50…57 family | shell + tabs |
| `/settings/models` `/platform/models` | `soma-settings` / `soma-settings-models` | UI-S-51 | implemented |
| `/settings/channels` | `soma-settings` external tab | UI-S-52 | implemented |
| `/themes` | inline notice | — | gated honest |
| `/admin/users` `/admin/agents` | `soma-entity-views` | UI-S-22 / UI-S-11 | partial |
| `/platform/roles` `/role-matrix` | roles + matrix | UI-S-23 | implemented |
| `/platform/api-keys` | `soma-admin-api-keys` | — | implemented |
| `/platform/audit` `/audit` | `soma-audit-dashboard` | UI-S-43 | implemented |
| `/platform/infrastructure` | infra dashboard | UI-S-39 | implemented |
| `/platform/metrics` `/admin/metrics` | metrics | UI-S-38/45 | implemented |
| `/platform/integrations` | integrations | UI-S-41 | implemented |
| `/platform/ratelimits` | infra ratelimits | UI-S-40 | partial |
| `/profile` `/platform/profile` | profiles | UI-S-34/35 | implemented |
| `/mfa/setup` | `soma-mfa-setup` | UI-S-32 | implemented |
| `/voice/*` | voice views | UI-S-46…48 | implemented |
| Right-rail surfaces | `soma-right-panel` | UI-X-01…08 | Files/Tools/Editor/Debug/Capsule/Brain live; Browser/Desktop gated |

### Mocks not yet routed (design-only or orphan)

| Mock | Title | Note |
|---|---|---|
| UI-S-01…06 | Capsule facets Soul/Brain/Hands/Memory/Body/Govern | in capsule editor / right-rail, not standalone routes |
| UI-S-08…10 | Message detail / export / queue | partial in chat |
| UI-S-12…18 | Capsule edit / versions / modules | partial / planned |
| UI-S-19…28 | Tenants / billing / marketplace | non-routed by design |
| UI-S-56 | **Settings — SomaBrain** | **new mock — build next** |
| UI-S-57 | **Settings — Agent admin** | **new mock — build next** |
| UI-S-03 | Hands / tools policy | maps to UI-S-55 + **UI-S-57** |

---

## 3. Primary agent flows (ISO)

### F1 — Login → chat → memory
1. `/login` → POST `/api/v2/auth/login` → token  
2. Default route chat → WS `/ws/v2/chat/{agent_id}`  
3. Send `chat.message` → stream deltas → `chat.done`  
4. Memory writes via MemoryGateway; if brain OPA deny → dock Memory **amber queued**, chat continues  

### F2 — Cognitive loop (right-rail Brain / UI-S-07 dock)
1. Open chat → dock Brain/Sync/Memory dots + CTX %  
2. Optional right-rail Brain → cognitive state + sleep  
3. Knobs → AgentIQ (server-derived only)  

### F3 — Files assistant (tools)
1. Capsule policy + capabilities allow `file_*`  
2. Tool loop → PathGuard → workroot  
3. `file_write` approval in timeline  
4. Files tab lists filesv2 / workroot  

### F4 — Durable research job
1. `research_report` → Temporal `ResearchReportWorkflow`  
2. Chat shows workflow id  
3. Output file in workdir + Files tab  

### F5 — Operator: Agent admin
1. sysadmin → Settings → Agent admin  
2. Set tool_policy buckets + capabilities  
3. Live preview matches chat choke  

### F6 — Operator: SomaBrain settings
1. sysadmin → Settings → SomaBrain  
2. URL/namespace/token (Vault)  
3. Test connection; memory lane status  
4. Cognitive defaults; Temporal strip  

---

## 4. A0 chrome checklist (current)

| Rule | Status |
|---|---|
| Composer hero | PASS |
| Thin top strip | OPEN (see chat plan) |
| Left-rail Memory + Settings only | PASS |
| Memory one home `/memory` | PASS |
| Models in Settings | PASS |
| No emoji | PASS (dock fixed) |
| Honest disabled states | PASS where implemented |

---

## 5. Build order for missing settings surfaces

| Order | Screen | Mock |
|---|---|---|
| 1 | SomaBrain settings tab | UI-S-56 |
| 2 | Agent admin (tools & permissions) | UI-S-57 |
| 3 | Chat thin top + turn topbar | UI-S-07 refresh |
| 4 | Jobs panel (Temporal) | new UI-S-58 when specified |

---

## 6. Compliance notes

- Mock annexes under `docs/design/mockups/` follow `SOMA-01-DOCS-001` §3.3.4 (no own Document Control).
- This index document is controlled (`SOMA-UI-SCREENS-001`).
- Lit 3.x only; no React.

---

*End of SOMA-UI-SCREENS-001 v1.0.0*
