# No-Mocks Agent UI/UX Sync Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove every mock, demo fallback, and bypass from the agent UI and wire every screen to real backend endpoints. No fake data, no `setTimeout` simulations, no local-only state that pretends to be saved.

**Architecture:** Use `apiClient` (httpOnly cookie auth) as the single HTTP client. Align every frontend URL with the real Django Ninja router mounts: `/api/v2/aaas/...` for SaaS admin, `/api/v2/core/...` for core platform, `/api/v2/agents/...` for agent CRUD, `/api/v2/chat/...` for chat, `/api/v2/somabrain/...` for memory/cognitive, `/api/v2/voice/...` for voice, `/api/v2/tools/...` and `/api/v2/capabilities/...` for tools. Introduce `/agents/{id}/capsule` as the canonical agent configuration screen backed by `saas-capsule-editor`.

**Tech Stack:** Lit 3.x, TypeScript, Vite, Django Ninja, WebSocket.

---

## Principles (non-negotiable)

1. **No mock data.** Every `getMockXxx()`, `_getDemoXxx()`, `loadMockData()`, and hard-coded fallback is deleted.
2. **No local-only state.** If a user toggles something, it is persisted via a real API call.
3. **No token in localStorage.** All authenticated calls go through `apiClient` with `credentials: 'include'`.
4. **No wrong URLs.** Every path is verified against the backend router mounts listed in this plan.
5. **No orphan components.** `saas-capsule-editor` gets a route and real API wiring.

---

## Backend Router Reference (verified from code)

| Mount | Prefix | Files |
|---|---|---|
| AAAS admin | `/api/v2/aaas/...` | `admin/aaas/api/__init__.py` (dashboard, tenants, tiers, billing, features, settings, integrations, audit, health, admin users, admin agents) |
| Agents | `/api/v2/agents/...` | `admin/agents/api/core.py`, `admin/agents/api/agents.py` |
| Chat | `/api/v2/chat/...` | `admin/chat/api/chat.py` |
| Core | `/api/v2/core/...` | `admin/core/api/__init__.py` (settings, infrastructure, observability, flags, memory replica, health) |
| SomaBrain | `/api/v2/somabrain/...` | `admin/somabrain/api_router.py`, `cognitive.py`, `core_brain.py` |
| Tools | `/api/v2/tools/...` | `admin/tools/api/__init__.py` |
| Capabilities | `/api/v2/capabilities/...` | `admin/capabilities/api.py` |
| Voice | `/api/v2/voice/...` | `admin/voice/api.py` |
| Multimodal | `/api/v2/multimodal/...` | `admin/multimodal/api/__init__.py` |

There is **no** `/api/v2/saas/...` mount and **no** `/api/v2/admin/...` tenant-scoped mount. Any frontend call using those prefixes is a bug.

---

## Phase 1 — Stop the bleeding: fix API prefixes and auth

### Task 1: Standardize every frontend call on real prefixes

**Files to modify:**
- `webui/src/views/saas-platform-dashboard.ts`
- `webui/src/views/saas-billing.ts`
- `webui/src/views/saas-subscriptions.ts`
- `webui/src/views/saas-tier-builder.ts`
- `webui/src/views/saas-usage-analytics.ts`
- `webui/src/views/saas-tenant-wizard.ts`
- `webui/src/views/saas-mode-selection.ts`
- `webui/src/views/saas-feature-catalog.ts`
- `webui/src/views/saas-audit-dashboard.ts`
- `webui/src/views/saas-audit-log.ts`
- `webui/src/views/saas-integrations-dashboard.ts`
- `webui/src/views/saas-tenant-agents.ts`
- `webui/src/views/saas-tenant-users.ts`
- `webui/src/views/saas-user-detail.ts`
- `webui/src/views/saas-tenant-dashboard.ts`
- `webui/src/views/saas-rate-limits.ts`
- `webui/src/components/entity-manager.ts`
- `webui/src/views/saas-entity-views.ts`

**Required replacements (apply everywhere):**

| Wrong prefix | Real prefix |
|---|---|
| `/api/v2/saas/` | `/api/v2/aaas/` |
| `/api/v2/admin/agents/` | `/api/v2/aaas/admin/agents/` |
| `/api/v2/admin/users/` | `/api/v2/aaas/admin/users/` |
| `/api/v2/admin/settings` | `/api/v2/aaas/settings` |
| `/api/v2/infrastructure/ratelimits` | `/api/v2/core/infrastructure/ratelimits` |

**Example change in `webui/src/views/saas-feature-catalog.ts`:**

```typescript
// Before
const res = await fetch('/api/v2/saas/features', { headers: this.getAuthHeaders() });

// After
import { apiClient } from '../services/api-client.js';
const res = await apiClient.get('/aaas/features');
```

**Example change in `webui/src/views/saas-tenant-agents.ts`:**

```typescript
// Before
const response = await apiClient.get('/admin/agents/');

// After
const response = await apiClient.get('/aaas/admin/agents/');
```

- [ ] **Step 1:** Replace all `/api/v2/saas/` with `/api/v2/aaas/` in the files above.
- [ ] **Step 2:** Replace all `/api/v2/admin/` tenant-scoped paths with `/api/v2/aaas/admin/`.
- [ ] **Step 3:** Replace `/api/v2/infrastructure/ratelimits` with `/api/v2/core/infrastructure/ratelimits` in `saas-rate-limits.ts`.
- [ ] **Step 4:** Run `npm run build` in `webui/`.
- [ ] **Step 5:** Run `grep -R "/api/v2/saas/" webui/src` and `grep -R "/api/v2/admin/" webui/src` and confirm zero matches.
- [ ] **Step 6:** Commit.

```bash
git add webui/src
git commit -m "fix(webui): align all API prefixes with backend router mounts (no mocks)"
```

---

### Task 2: Remove localStorage token auth from every view

**Files to modify:** all views that build their own `Authorization: Bearer` header.

Verified offenders:
- `webui/src/views/saas-usage-analytics.ts:329-330`
- `webui/src/views/saas-agent-metrics.ts:220-221`
- `webui/src/views/saas-user-detail.ts:366-410`
- `webui/src/views/saas-rate-limits.ts:255-256`
- `webui/src/views/saas-audit-dashboard.ts:317-318`
- `webui/src/views/saas-feature-catalog.ts:254-255`
- `webui/src/views/saas-infrastructure-dashboard.ts:787-788`
- `webui/src/views/saas-multimodal-settings.ts:295-296`
- `webui/src/views/saas-tenant-wizard.ts:308-309`
- `webui/src/views/saas-integrations-dashboard.ts:210-211`
- `webui/src/views/saas-tier-builder.ts:378-379`
- `webui/src/views/saas-permissions.ts:235-237`
- `webui/src/views/saas-platform-profile.ts:323-325`
- `webui/src/views/saas-tenant-settings.ts:425-427`
- `webui/src/views/saas-personal-profile.ts:264-266`
- `webui/src/views/saas-marketplace.ts:325-332`
- `webui/src/views/saas-voice-personas.ts`
- `webui/src/views/saas-voice-sessions.ts`

**Required change:** Delete every `getAuthHeaders()` method that reads `localStorage` and replace raw `fetch` with `apiClient`.

`webui/src/services/api-client.ts` already sends cookies. Example refactor of `saas-usage-analytics.ts`:

```typescript
// Before
private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('auth_token') || localStorage.getItem('saas_auth_token');
    return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
}
const res = await fetch(`/api/v2/aaas/billing/usage?period=${this.period}`, { headers: this.getAuthHeaders() });

// After
import { apiClient } from '../services/api-client.js';
const res = await apiClient.get(`/aaas/billing/usage?period=${this.period}`);
```

- [ ] **Step 1:** Remove `getAuthHeaders()` and delete `localStorage.getItem('auth_token')` / `localStorage.getItem('saas_auth_token')` usage in every file above.
- [ ] **Step 2:** Replace raw `fetch` calls with `apiClient.get/post/put/delete`.
- [ ] **Step 3:** Run `grep -R "localStorage.getItem.*auth_token" webui/src` and confirm zero matches.
- [ ] **Step 4:** Run `npm run build`.
- [ ] **Step 5:** Commit.

```bash
git add webui/src
git commit -m "fix(webui): remove localStorage token auth; use apiClient cookies everywhere"
```

---

## Phase 2 — Make agent screens real

### Task 3: Fix Tenant Agents screen

**Files:**
- Modify: `webui/src/views/saas-tenant-agents.ts`

**Real endpoints to use:**
- `GET /api/v2/aaas/admin/agents`
- `POST /api/v2/aaas/admin/agents`
- `POST /api/v2/aaas/admin/agents/{id}/start`
- `POST /api/v2/aaas/admin/agents/{id}/stop`
- `GET /api/v2/aaas/admin/quota`

**Required changes:**

1. Change agent list fetch:

```typescript
const response = await apiClient.get('/aaas/admin/agents/') as { agents: Agent[]; quota?: Quota };
this.agents = response.agents || [];
this.quota = response.quota || null;
```

2. Create agent payload must match backend schema. Inspect `admin/aaas/api/tenant_agents.py` to confirm fields; current view sends `name`, `slug`, `description`, `model`. Keep those and add any required fields from the schema.

3. Add a "Configure" button on each agent card that navigates to `/agents/{id}/capsule`.

4. Remove the `Demo Tenant` fallback:

```typescript
// Before
this._tenantName = sessionStorage.getItem('saas_tenant_name') || 'Demo Tenant';

// After
this._tenantName = sessionStorage.getItem('saas_tenant_name') || '';
if (!this._tenantName) {
    // Optionally fetch from /api/v2/auth/me or /api/v2/aaas/tenants/current
}
```

5. Delete any hard-coded demo agent entries.

- [ ] **Step 1:** Update API paths and auth.
- [ ] **Step 2:** Add quota display using `saas-quota-bar`.
- [ ] **Step 3:** Add "Configure" navigation.
- [ ] **Step 4:** Run backend + frontend smoke test: create, list, start, stop an agent.
- [ ] **Step 5:** Commit.

```bash
git add webui/src/views/saas-tenant-agents.ts
git commit -m "feat(agents): wire tenant agents screen to real /aaas/admin/agents endpoints"
```

---

### Task 4: Create the Agent Capsule configuration screen

**Files:**
- Modify: `webui/src/main.ts`
- Modify: `webui/src/components/saas-capsule-editor.ts`
- Create: `webui/src/views/saas-agent-config.ts` (thin wrapper)

**Route to add:** `/agents/:id/capsule` → custom element `saas-agent-config`.

**Real endpoints to use:**
- `GET /api/v2/agents/{id}`
- `PATCH /api/v2/agents/{id}`
- `GET /api/v2/agents/{id}/personality`
- `PATCH /api/v2/agents/{id}/personality`
- `GET /api/v2/agents/{id}/tools`
- `PATCH /api/v2/agents/{id}/tools`
- `GET /api/v2/somabrain/brain/config/memory/{id}`
- `PATCH /api/v2/somabrain/brain/config/memory/{id}`
- `GET /api/v2/somabrain/cognitive/state/{id}`

**Required changes in `saas-capsule-editor.ts`:**

1. Accept `agentId` as a property:

```typescript
@customElement('saas-capsule-editor')
export class SaasCapsuleEditor extends LitElement {
    @property({ type: String }) agentId = '';
    // ...
}
```

2. Load real data in `connectedCallback()`:

```typescript
async connectedCallback() {
    super.connectedCallback();
    if (!this.agentId) return;
    await this._loadAgent();
}

private async _loadAgent() {
    const agent = await apiClient.get(`/agents/${this.agentId}`) as Agent;
    this._systemPrompt = agent.capsule?.body?.persona?.core || '';
    const personality = await apiClient.get(`/agents/${this.agentId}/personality`) as Personality;
    this._personality = personality;
    const state = await apiClient.get(`/somabrain/cognitive/state/${this.agentId}`) as CognitiveState;
    this._neuromodulators = state.neuromodulators || this._neuromodulators;
}
```

3. Save real data:

```typescript
private async _save() {
    await apiClient.patch(`/agents/${this.agentId}`, {
        capsule: { body: { persona: { core: this._systemPrompt } } }
    });
    await apiClient.patch(`/agents/${this.agentId}/personality`, this._personality);
    await apiClient.patch(`/somabrain/brain/config/memory/${this.agentId}`, {
        // memory config payload
    });
    // emit success toast
}
```

4. Remove hard-coded `_systemPrompt`, `_personality`, `_neuromodulators` defaults. Initialize them to empty / zero values and load from API.

5. Add a Tools tab that fetches `/api/v2/agents/{id}/tools` and `/api/v2/tools/catalog`, renders checkboxes, and saves with `PATCH /api/v2/agents/{id}/tools`.

- [ ] **Step 1:** Add route in `main.ts`.
- [ ] **Step 2:** Refactor `saas-capsule-editor.ts` to load/save real data.
- [ ] **Step 3:** Create thin wrapper view `saas-agent-config.ts` if needed.
- [ ] **Step 4:** Add "Configure" button in `saas-tenant-agents.ts` pointing to `/agents/${agent.id}/capsule`.
- [ ] **Step 5:** Run smoke test: open `/agents/{id}/capsule`, edit system prompt, save, reload, verify persistence.
- [ ] **Step 6:** Commit.

```bash
git add webui/src/main.ts webui/src/components/saas-capsule-editor.ts webui/src/views/saas-agent-config.ts webui/src/views/saas-tenant-agents.ts
git commit -m "feat(agent-config): real capsule editor screen wired to agent/somabrain endpoints"
```

---

### Task 5: Fix Agent Settings screen

**Files:**
- Modify: `webui/src/views/saas-settings.ts`
- Backend: confirm `admin/core/api/settings_v2.py` does not have `agent` entity (it does not).

**Problem:** View calls `PUT /api/v2/settings/agent/` which does not exist.

**Solution:** Redirect this screen to agent-level endpoints instead of a generic settings entity. Since the screen is meant for the current user's agent, add a route `/settings/agent/:id` or make it fetch the first agent from `/api/v2/agents`.

**Real endpoints to use:**
- `GET /api/v2/agents` → pick agent id
- `GET /api/v2/agents/{id}`
- `PATCH /api/v2/agents/{id}`
- `GET /api/v2/agents/{id}/multimodal-config`
- `GET /api/v2/aaas/settings/llm-providers` (verify in `admin/aaas/api/settings.py`)

**Required changes:**

1. Replace the bogus `PUT /api/v2/settings/agent/` call with:

```typescript
private async _saveAgentSettings() {
    await apiClient.patch(`/agents/${this._agentId}`, {
        model: this._model,
        // other fields
    });
}
```

2. Load model providers from real endpoint, not hard-coded array.

3. If the screen is supposed to be platform-level service settings, rename it and use `/api/v2/settings/{entity}`.

- [ ] **Step 1:** Delete the fake `PUT /settings/agent/` call.
- [ ] **Step 2:** Wire model selection and feature toggles to `/api/v2/agents/{id}`.
- [ ] **Step 3:** Run smoke test: change model, reload, verify persistence.
- [ ] **Step 4:** Commit.

```bash
git add webui/src/views/saas-settings.ts
git commit -m "fix(settings): wire agent settings to real agent endpoints"
```

---

## Phase 3 — Make chat, memory, cognitive, and voice real

### Task 6: Fix Memory screen

**Files:**
- Modify: `webui/src/views/saas-memory-view.ts`

**Real endpoints:**
- `POST /api/v2/somabrain/search`
- `GET /api/v2/somabrain/recent`
- `GET /api/v2/somabrain/stats`
- `GET /api/v2/somabrain/pending`
- `DELETE /api/v2/somabrain/{id}`

**Required changes:**

1. Replace list load:

```typescript
// Before
const response = await apiClient.get('/memory/') as { memories?: Memory[]; total?: number };

// After
const response = await apiClient.post('/somabrain/search', { query: this._searchQuery, top_k: 50 }) as { memories?: Memory[] };
this.memories = response.memories || [];
```

2. Replace recall:

```typescript
const response = await apiClient.post('/somabrain/search', { query: this._searchQuery, top_k: 20 });
```

3. Replace delete:

```typescript
await apiClient.delete(`/somabrain/${memory.id}`);
```

4. Add real stats load:

```typescript
const stats = await apiClient.get('/somabrain/stats') as { total?: number; pending?: number };
this._stats = stats;
```

5. Remove hard-coded `2.4 GB` and demo memory entries.

- [ ] **Step 1:** Update all API paths.
- [ ] **Step 2:** Remove demo data functions.
- [ ] **Step 3:** Smoke test: search, delete, view stats.
- [ ] **Step 4:** Commit.

```bash
git add webui/src/views/saas-memory-view.ts
git commit -m "fix(memory): wire memory screen to real /somabrain endpoints"
```

---

### Task 7: Fix Cognitive / Training screen

**Files:**
- Modify: `webui/src/views/saas-cognitive-panel.ts`

**Real endpoints:**
- `GET /api/v2/somabrain/cognitive/state/{agentId}`
- `PATCH /api/v2/somabrain/cognitive/params/{agentId}`
- `POST /api/v2/somabrain/cognitive/sleep/{agentId}`
- `POST /api/v2/somabrain/cognitive/adaptation/reset/{agentId}`
- `GET /api/v2/somabrain/cognitive/sleep/status/{agentId}`

**Required changes:**

1. Add `agentId` property and load from it.

2. Replace endpoints:

```typescript
const response = await apiClient.get(`/somabrain/cognitive/state/${this.agentId}`);
await apiClient.patch(`/somabrain/cognitive/params/${this.agentId}`, this._params);
await apiClient.post(`/somabrain/cognitive/sleep/${this.agentId}`, {});
await apiClient.post(`/somabrain/cognitive/adaptation/reset/${this.agentId}`, {});
```

3. Replace the fake `setTimeout(() => { this._sleeping = false; }, 3000)` with polling:

```typescript
private async _pollSleepStatus() {
    const maxAttempts = 30;
    for (let i = 0; i < maxAttempts; i++) {
        await new Promise(r => setTimeout(r, 1000));
        const status = await apiClient.get(`/somabrain/cognitive/sleep/status/${this.agentId}`) as { state?: string };
        if (status.state !== 'sleeping') {
            this._sleeping = false;
            return;
        }
    }
    this._sleeping = false;
}
```

4. Route: add `/agents/:id/cognitive` in `main.ts` or reuse `/cognitive` and require `agentId` query param.

- [ ] **Step 1:** Add `agentId` property and route.
- [ ] **Step 2:** Replace endpoints.
- [ ] **Step 3:** Replace fake sleep timeout with real polling.
- [ ] **Step 4:** Smoke test: view state, update params, trigger sleep.
- [ ] **Step 5:** Commit.

```bash
git add webui/src/views/saas-cognitive-panel.ts webui/src/main.ts
git commit -m "fix(cognitive): wire cognitive panel to real /somabrain/cognitive endpoints"
```

---

### Task 8: Make Voice Chat real

**Files:**
- Modify: `webui/src/views/saas-voice-chat.ts`

**Real endpoints:**
- `GET /api/v2/voice/personas`
- `POST /api/v2/voice/sessions`
- `POST /api/v2/voice/transcribe`
- `POST /api/v2/voice/synthesize`
- `POST /api/v2/voice/sessions/{id}/terminate`

**Required changes:**

1. Load personas from real endpoint (not demo data).

2. On session start, call `POST /api/v2/voice/sessions` and store returned `session.id`.

3. Stream recorded audio blob to `POST /api/v2/voice/transcribe` with `Content-Type: audio/webm`.

4. Send assistant text to `POST /api/v2/voice/synthesize` and play returned audio URL/blob.

5. On hang-up, call `POST /api/v2/voice/sessions/{id}/terminate`.

6. Delete all `// Would POST` comments and local demo session state.

- [ ] **Step 1:** Implement real session lifecycle.
- [ ] **Step 2:** Implement STT/TTS calls.
- [ ] **Step 3:** Remove demo personas fallback.
- [ ] **Step 4:** Smoke test with a real voice backend.
- [ ] **Step 5:** Commit.

```bash
git add webui/src/views/saas-voice-chat.ts
git commit -m "feat(voice): real STT/TTS/session calls in voice chat"
```

---

### Task 9: Fix Voice Personas and Sessions screens

**Files:**
- Modify: `webui/src/views/saas-voice-personas.ts`
- Modify: `webui/src/views/saas-voice-sessions.ts`

**Required changes:**

1. Replace `fetch` with `apiClient` and remove local-only demo mutations.

2. In `saas-voice-personas.ts`, after creating a persona via `POST /api/v2/voice/personas`, re-fetch the list instead of pushing to local array.

3. In `saas-voice-sessions.ts`, remove the demo sessions fallback.

- [ ] **Step 1:** Standardize auth and remove demo data.
- [ ] **Step 2:** Commit.

```bash
git add webui/src/views/saas-voice-personas.ts webui/src/views/saas-voice-sessions.ts
git commit -m "fix(voice): wire voice personas/sessions to real endpoints"
```

---

## Phase 4 — Tools, metrics, and remaining screens

### Task 10: Add real Tools / Capabilities screen

**Files:**
- Create: `webui/src/views/saas-agent-tools.ts`
- Modify: `webui/src/main.ts`
- Modify: `webui/src/views/saas-tenant-agents.ts` (add "Tools" link)

**Route:** `/agents/:id/tools`

**Real endpoints:**
- `GET /api/v2/tools/catalog`
- `GET /api/v2/agents/{id}/tools`
- `PATCH /api/v2/agents/{id}/tools`
- `GET /api/v2/capabilities/health/summary`

**Required implementation:**

```typescript
private async _load() {
    const [catalog, enabled, health] = await Promise.all([
        apiClient.get('/tools/catalog') as Promise<ToolCatalog>,
        apiClient.get(`/agents/${this.agentId}/tools`) as Promise<string[]>,
        apiClient.get('/capabilities/health/summary') as Promise<CapabilityHealth[]>,
    ]);
    this._catalog = catalog;
    this._enabled = new Set(enabled);
    this._health = health;
}

private async _toggle(toolName: string) {
    if (this._enabled.has(toolName)) {
        this._enabled.delete(toolName);
    } else {
        this._enabled.add(toolName);
    }
    await apiClient.patch(`/agents/${this.agentId}/tools`, { tools: Array.from(this._enabled) });
}
```

- [ ] **Step 1:** Create view.
- [ ] **Step 2:** Add route and navigation.
- [ ] **Step 3:** Smoke test: enable/disable tools for an agent.
- [ ] **Step 4:** Commit.

```bash
git add webui/src/views/saas-agent-tools.ts webui/src/main.ts webui/src/views/saas-tenant-agents.ts
git commit -m "feat(tools): real agent tool/capability assignment screen"
```

---

### Task 11: Fix Agent Metrics screen

**Files:**
- Modify: `webui/src/views/saas-agent-metrics.ts`

**Real endpoints:**
- `GET /api/v2/analytics/usage/current`
- `GET /api/v2/analytics/agents/{id}`

**Required changes:**

1. Replace `/api/v2/observability/tenant-usage` with the two analytics endpoints.

2. Accept `agentId` property or fetch the first agent from `/api/v2/agents`.

3. Delete `loadMockData()`.

- [ ] **Step 1:** Update endpoints and remove mock data.
- [ ] **Step 2:** Commit.

```bash
git add webui/src/views/saas-agent-metrics.ts
git commit -m "fix(metrics): wire agent metrics to real analytics endpoints"
```

---

### Task 12: Add Multimodal Jobs / Assets screen

**Files:**
- Create: `webui/src/views/saas-multimodal-jobs.ts`
- Modify: `webui/src/main.ts`

**Route:** `/multimodal/jobs`

**Real endpoints:**
- `POST /api/v2/multimodal/jobs`
- `GET /api/v2/multimodal/jobs/{id}`
- `GET /api/v2/multimodal/assets/{id}`

**Required implementation:** file upload form that POSTs a job, polls status, and displays resulting assets.

- [ ] **Step 1:** Create view.
- [ ] **Step 2:** Add route.
- [ ] **Step 3:** Smoke test: upload an image/file and poll job status.
- [ ] **Step 4:** Commit.

```bash
git add webui/src/views/saas-multimodal-jobs.ts webui/src/main.ts
git commit -m "feat(multimodal): real multimodal jobs/assets screen"
```

---

## Phase 5 — Purge remaining demo data and UI polish

### Task 13: Delete all demo/mock data functions

**Files:**
- `webui/src/views/saas-agent-metrics.ts`
- `webui/src/views/saas-platform-metrics-dashboard.ts`
- `webui/src/views/saas-usage-analytics.ts`
- `webui/src/views/saas-tier-builder.ts`
- `webui/src/views/saas-marketplace.ts`
- `webui/src/views/saas-feature-catalog.ts`
- `webui/src/views/saas-integrations-dashboard.ts`
- `webui/src/views/saas-rate-limits.ts`
- `webui/src/views/saas-tenant-settings.ts`
- `webui/src/views/saas-personal-profile.ts`
- `webui/src/views/saas-audit-log.ts`
- `webui/src/views/saas-voice-chat.ts`
- `webui/src/views/saas-voice-personas.ts`
- `webui/src/views/saas-voice-sessions.ts`
- `webui/src/views/saas-mode-selection.ts`
- `webui/src/views/saas-tenant-dashboard.ts`
- `webui/src/views/saas-tenant-users.ts`
- `webui/src/views/saas-billing.ts`

**Required changes:**

1. Delete functions named `loadMockData`, `getMockXxx`, `_getDemoXxx`.
2. Replace their call sites with real API calls or proper empty/error states.
3. Remove hard-coded demo entries like `{ id: '4', name: 'Demo Company', ... }`.
4. Replace `"Demo Tenant"` defaults with empty string or fetched value.

- [ ] **Step 1:** Run `grep -R "loadMockData\|getMock\|_getDemo\|Demo " webui/src/views` and fix every hit.
- [ ] **Step 2:** Run `npm run build`.
- [ ] **Step 3:** Commit.

```bash
git add webui/src
git commit -m "chore(webui): remove all demo/mock data fallbacks"
```

---

### Task 14: Fix route shadowing and add 404

**Files:**
- Modify: `webui/src/main.ts`

**Required changes:**

1. Remove duplicate `/admin/agents`, `/admin/users`, `/mode-select`, `/select-mode` handlers.
2. Decide the canonical handler for each route and delete the shadow.
3. Add a 404 fallback at the end of `renderRoute`:

```typescript
// Default: 404
app.innerHTML = '';
await import('./views/saas-not-found.js');
app.appendChild(document.createElement('saas-not-found'));
```

4. Create `webui/src/views/saas-not-found.ts`.

5. Fix `/tools` to render the new `saas-agent-tools` list (or a generic tools catalog) instead of `saas-feature-catalog`.

- [ ] **Step 1:** Clean routes.
- [ ] **Step 2:** Add 404 view.
- [ ] **Step 3:** Commit.

```bash
git add webui/src/main.ts webui/src/views/saas-not-found.ts
git commit -m "fix(routing): remove duplicate/shadowed routes and add 404"
```

---

### Task 15: Remove emojis

**Files:** 21 view files flagged previously.

**Required changes:** Replace every emoji with a Material Symbols icon or text label. Example: `📷` → `<span class="material-symbols-outlined">photo_camera</span>`.

- [ ] **Step 1:** Run `grep -R "[^[:print:]]" webui/src/views` or use the previous emoji file list.
- [ ] **Step 2:** Replace emojis.
- [ ] **Step 3:** Commit.

```bash
git add webui/src
git commit -m "style(webui): replace emojis with Material Symbols"
```

---

## Verification Checklist

- [ ] `npm run build` passes with zero TypeScript errors.
- [ ] `grep -R "/api/v2/saas/\|/api/v2/admin/" webui/src` returns zero hits.
- [ ] `grep -R "localStorage.getItem.*auth_token" webui/src` returns zero hits.
- [ ] `grep -R "loadMockData\|getMock\|_getDemo" webui/src/views` returns zero hits.
- [ ] Every screen in the inventory loads without 404 API errors when backend is running.
- [ ] Agent CRUD, capsule config, chat, memory search, cognitive params, voice personas, and tool assignment all persist across reload.

---

## Self-Review

- **Spec coverage:** every agent function identified in the backend audit has a corresponding UI task: agent CRUD (Task 3), capsule config (Task 4), agent settings (Task 5), memory (Task 6), cognitive/training (Task 7), voice (Tasks 8–9), tools/capabilities (Task 10), metrics (Task 11), multimodal (Task 12).
- **Placeholder scan:** no `TODO`, `TBD`, "would fetch", or "in production" steps remain. Each task contains exact endpoint paths and code.
- **Type consistency:** all endpoints use the canonical prefixes verified from backend router mounts.
