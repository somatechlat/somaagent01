/**
 * SomaAgent — Models settings (card library + 5-role panel + presets + wizard)
 *
 * Design: SOMA-UI-MODEL-ADMIN-001 v3.2 · FIELD-PARITY-001
 * - Providers come from GET /llm/providers (never a hardcoded list)
 * - One CSS card = one model (all identity fields visible)
 * - Add-model wizard: Provider → key → base URL → Load models → id →
 *   display name → Type (Chat/Embedding/Decision) → Used for → Advanced →
 *   Test connection → Save
 * - Five model roles: chat_role / utility_role / embedding_role /
 *   vision_role / decision_role. UI labels: Used for: Chat / Help / Memory /
 *   Vision / Decisions. API surface: GET/PUT /llm/roles.
 * - Presets panel: bundled + user, Apply to (Global / This agent / This chat),
 *   Duplicate, Edit (all five role bindings), Delete (user only), Restore
 *   bundled presets, Save current roles as preset
 * - API key typed here → Vault only (write-only, never echoed)
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import { glassCard } from '../styles/glass.js';
import { moduleBase } from '../styles/module-base.js';
import '../components/soma-status-badge.js';

type ModelType = 'chat' | 'embedding' | 'decision';

interface ProviderRow {
    id: string;
    label: string;
    enabled: boolean;
    base_url: string;
    model_name: string;
    is_custom: boolean;
    has_api_key: boolean;
}

interface ModelRow {
    id: string;
    name: string;
    display_name: string;
    model_type: ModelType;
    provider: string;
    api_base: string;
    capabilities: string[];
    priority: number;
    cost_tier: string;
    domains: string[];
    ctx_length: number;
    limit_requests: number;
    limit_input: number;
    limit_output: number;
    vision: boolean;
    kwargs: Record<string, unknown>;
    is_active: boolean;
}

interface RoleBindings {
    chat_role: string | null;
    utility_role: string | null;
    embedding_role: string | null;
    vision_role: string | null;
    decision_role: string | null;
    decision_role_id: string | null;
    capsule_id: string | null;
    scope: string;
}

interface PresetRoleDraft {
    chat_model_id: string;
    utility_model_id: string;
    embedding_model_id: string;
    vision_role_id: string;
    decision_role_id: string;
}

interface PresetRow {
    id: string;
    name: string;
    chat_model_id: string | null;
    utility_model_id: string | null;
    embedding_model_id: string | null;
    vision_role_id: string | null;
    decision_role_id: string | null;
    is_bundled: boolean;
    scope: string;
    notes: string;
    created_at: string;
    updated_at: string;
}

interface AgentRow {
    id: string;
    name: string;
    capsule_id?: string;
}

interface Draft {
    id?: string;
    name: string;
    display_name: string;
    model_type: ModelType;
    provider: string;
    api_base: string;
    capabilities: string;
    priority: number;
    cost_tier: string;
    domains: string;
    ctx_length: number;
    limit_requests: number;
    limit_input: number;
    limit_output: number;
    vision: boolean;
    kwargs_text: string;
    is_active: boolean;
    api_key: string;
    max_tokens: number;
    timeout: number;
    ctx_history: number;
    max_embeds: number;
}

/** Role id → the label the product uses (Chat / Help / Memory / Vision / Decisions). */
const ROLE_LABELS: Record<string, string> = {
    chat_role: 'Chat',
    utility_role: 'Help',
    embedding_role: 'Memory',
    vision_role: 'Vision',
    decision_role: 'Decisions',
};

const ROLE_HINTS: Record<string, string> = {
    chat_role: 'Primary conversations',
    utility_role: 'Summaries and background work',
    embedding_role: 'Embeddings for memory and search',
    vision_role: 'Images and vision critique',
    decision_role: 'System One decisions (Clef)',
};

const ROLE_ORDER = [
    'chat_role',
    'utility_role',
    'embedding_role',
    'vision_role',
    'decision_role',
] as const;

type RoleId = (typeof ROLE_ORDER)[number];

/** model_type each role accepts (mirrors admin.llm.api._role_model_type_required). */
const ROLE_REQUIRED_TYPE: Record<RoleId, ModelType | null> = {
    chat_role: 'chat',
    utility_role: null,
    embedding_role: 'embedding',
    vision_role: 'chat',
    decision_role: 'decision',
};

function emptyDraft(provider = ''): Draft {
    return {
        name: '',
        display_name: '',
        model_type: 'chat',
        provider,
        api_base: '',
        capabilities: '',
        priority: 50,
        cost_tier: 'standard',
        domains: '',
        ctx_length: 32768,
        limit_requests: 0,
        limit_input: 0,
        limit_output: 0,
        vision: false,
        kwargs_text: '{}',
        is_active: true,
        api_key: '',
        max_tokens: 8192,
        timeout: 30,
        ctx_history: 0.7,
        max_embeds: 10,
    };
}

function draftFromModel(m: ModelRow): Draft {
    const kw = m.kwargs || {};
    return {
        id: m.id,
        name: m.name,
        display_name: m.display_name || '',
        model_type: m.model_type,
        provider: m.provider,
        api_base: m.api_base || '',
        capabilities: (m.capabilities || []).join(', '),
        priority: m.priority ?? 50,
        cost_tier: m.cost_tier || 'standard',
        domains: (m.domains || []).join(', '),
        ctx_length: m.ctx_length || 0,
        limit_requests: m.limit_requests || 0,
        limit_input: m.limit_input || 0,
        limit_output: m.limit_output || 0,
        vision: !!m.vision,
        kwargs_text: JSON.stringify(kw, null, 2),
        is_active: !!m.is_active,
        api_key: '',
        max_tokens: Number(kw.max_tokens ?? 8192),
        timeout: Number(kw.timeout ?? 30),
        ctx_history: Number(kw.ctx_history ?? 0.7),
        max_embeds: Number(kw.max_embeds ?? 10),
    };
}

function payloadFromDraft(d: Draft): Record<string, unknown> {
    let kwargs: Record<string, unknown> = {};
    try {
        kwargs = JSON.parse(d.kwargs_text || '{}') as Record<string, unknown>;
    } catch {
        kwargs = {};
    }
    if (d.max_tokens > 0) kwargs.max_tokens = d.max_tokens;
    if (d.timeout > 0) kwargs.timeout = d.timeout;
    if (d.ctx_history > 0) kwargs.ctx_history = d.ctx_history;
    if (d.max_embeds > 0) kwargs.max_embeds = d.max_embeds;
    return {
        name: d.name.trim(),
        display_name: d.display_name.trim() || d.name.trim(),
        model_type: d.model_type,
        provider: d.provider,
        api_base: d.api_base.trim(),
        capabilities: d.capabilities.split(',').map((s) => s.trim()).filter(Boolean),
        priority: Number(d.priority) || 50,
        cost_tier: d.cost_tier,
        domains: d.domains.split(',').map((s) => s.trim()).filter(Boolean),
        ctx_length: Number(d.ctx_length) || 0,
        limit_requests: Number(d.limit_requests) || 0,
        limit_input: Number(d.limit_input) || 0,
        limit_output: Number(d.limit_output) || 0,
        vision: !!d.vision,
        kwargs,
        is_active: !!d.is_active,
    };
}

@customElement('soma-settings-models')
export class SomaSettingsModels extends LitElement {
    static styles = [
        glassCard,
        moduleBase,
        css`
        :host {
            display: block;
            min-height: 100%;
            background: var(--skin-color-bg-void);
            color: var(--skin-color-text-primary);
            font-family: var(--skin-font-sans);
        }
        * { box-sizing: border-box; }
        .wrap { max-width: calc(var(--skin-space-md) * 70); margin: 0 auto; padding: var(--skin-space-lg) calc(var(--skin-space-md) + var(--skin-space-xs)) var(--skin-space-2xl); }
        .head { display: flex; align-items: center; gap: calc(var(--skin-space-sm) + var(--skin-space-xs)); margin-bottom: var(--skin-space-sm); }
        h1 { font-size: calc(var(--skin-text-2xl) * 0.9); font-weight: calc(var(--skin-weight-semibold) + (var(--skin-weight-bold) - var(--skin-weight-semibold)) / 2); margin: 0; flex: 1; letter-spacing: -0.02em; }
        h2 { font-size: calc(var(--skin-text-lg) + var(--skin-text-xs) * 0.2); font-weight: calc(var(--skin-weight-semibold) + (var(--skin-weight-bold) - var(--skin-weight-semibold)) / 2); margin: 0 0 var(--skin-space-xs); }
        .sub { color: var(--skin-color-text-secondary); font-size: calc(var(--skin-text-base) + var(--skin-text-xs) * 0.2); margin-bottom: calc(var(--skin-space-md) + var(--skin-space-xs)); }
        .toolbar { display: flex; flex-wrap: wrap; gap: calc(var(--skin-space-sm) + var(--skin-space-xs) / 2); margin-bottom: calc(var(--skin-space-md) + var(--skin-space-xs) / 2); }
        input, select, textarea {
            background: var(--skin-color-bg-card);
            border: var(--skin-border-width) solid var(--skin-color-border);
            color: var(--skin-color-text-primary);
            border-radius: var(--skin-radius-md);
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs) / 4) calc(var(--skin-space-sm) + var(--skin-space-xs));
            font-size: calc(var(--skin-text-base) + var(--skin-text-xs) * 0.2);
        }
        input:focus, select:focus, textarea:focus {
            outline: calc(var(--skin-space-xs) / 2) solid var(--skin-color-info);
            outline-offset: calc(var(--skin-space-xs) / 4);
        }
        .btn {
            display: inline-flex;
            align-items: center;
            gap: calc(var(--skin-space-xs) * 1.5);
            border: var(--skin-border-width) solid var(--skin-color-border);
            background: var(--skin-color-bg-card);
            color: var(--skin-color-text-primary);
            border-radius: var(--skin-radius-md);
            padding: var(--skin-space-sm) calc(var(--skin-space-md) - var(--skin-space-xs) / 2);
            font-size: calc(var(--skin-text-sm) + (var(--skin-text-base) - var(--skin-text-sm)) * 0.6);
            font-weight: calc(var(--skin-weight-medium) + (var(--skin-weight-semibold) - var(--skin-weight-medium)) / 2);
            cursor: pointer;
        }
        .btn:hover { border-color: var(--skin-color-accent); }
        .btn.primary {
            background: var(--skin-color-accent);
            border-color: var(--skin-color-accent);
            color: var(--skin-color-accent-text);
        }
        .btn.ghost { background: transparent; }
        .btn.danger {
            border-color: var(--skin-color-danger);
            color: var(--skin-color-danger);
        }
        .btn:disabled { opacity: 0.45; cursor: not-allowed; }
        .panel {
            background: var(--skin-color-bg-card);
            border: var(--skin-border-width) solid var(--skin-color-border);
            border-radius: var(--skin-radius-lg);
            padding: var(--skin-space-md);
            margin-bottom: calc(var(--skin-space-md) + var(--skin-space-xs) / 2);
        }
        .panel-head {
            display: flex;
            align-items: center;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs) / 2);
            margin-bottom: calc(var(--skin-space-sm) + var(--skin-space-xs));
        }
        .panel-head h2 { flex: 1; margin: 0; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(calc(var(--skin-space-md) * 17.5), 1fr));
            gap: calc(var(--skin-space-md) - var(--skin-space-xs) / 2);
        }
        .card {
            background: var(--skin-color-bg-card);
            border: var(--skin-border-width) solid var(--skin-color-border);
            border-radius: var(--skin-radius-lg);
            padding: var(--skin-space-md);
            display: flex;
            flex-direction: column;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs) / 2);
            transition: border-color var(--skin-motion-fast), box-shadow var(--skin-motion-fast);
            cursor: pointer;
        }
        .card:hover {
            border-color: var(--skin-color-border-strong);
            box-shadow: var(--skin-shadow-md);
        }
        .card.live {
            border-color: var(--skin-color-info);
            box-shadow: 0 0 0 calc(var(--skin-space-xs) / 4) var(--skin-color-info);
        }
        .card-top { display: flex; align-items: center; gap: var(--skin-space-sm); flex-wrap: wrap; }
        .chip {
            font-size: calc(var(--skin-text-xs) + (var(--skin-text-sm) - var(--skin-text-xs)) * 0.4);
            font-weight: calc(var(--skin-weight-semibold) + (var(--skin-weight-bold) - var(--skin-weight-semibold)) / 2);
            letter-spacing: 0.02em;
            padding: calc(var(--skin-space-xs) / 2) var(--skin-space-sm);
            border-radius: var(--skin-radius-full);
            background: var(--skin-color-bg-active);
            color: var(--skin-color-text-secondary);
        }
        .chip.live {
            background: var(--skin-color-success);
            color: var(--skin-color-accent-text);
        }
        .chip.type {
            background: var(--skin-color-bg-hover);
            color: var(--skin-color-text-primary);
            border: var(--skin-border-width) solid var(--skin-color-border);
        }
        .chip.warn {
            background: var(--skin-color-warning);
            color: var(--skin-color-text-primary);
        }
        .chip.err {
            background: var(--skin-color-danger);
            color: var(--skin-color-accent-text);
        }
        .chip.ok {
            background: var(--skin-color-success);
            color: var(--skin-color-accent-text);
        }
        .model-id { font-weight: calc(var(--skin-weight-semibold) + (var(--skin-weight-bold) - var(--skin-weight-semibold)) / 2); font-size: var(--skin-text-lg); letter-spacing: -0.01em; }
        .meta { color: var(--skin-color-text-secondary); font-size: calc(var(--skin-text-sm) + (var(--skin-text-base) - var(--skin-text-sm)) * 0.2); line-height: var(--skin-leading-normal); }
        .facts {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: var(--skin-space-xs) calc(var(--skin-space-sm) + var(--skin-space-xs) / 2);
            font-size: calc(var(--skin-text-xs) + (var(--skin-text-sm) - var(--skin-text-xs)) * 0.7);
            color: var(--skin-color-text-muted);
        }
        .facts b { color: var(--skin-color-text-primary); font-weight: calc(var(--skin-weight-medium) + (var(--skin-weight-semibold) - var(--skin-weight-medium)) / 2); }
        .actions { display: flex; flex-wrap: wrap; gap: var(--skin-space-sm); margin-top: var(--skin-space-xs); }
        .actions .btn { padding: calc(var(--skin-space-xs) * 1.5) calc(var(--skin-space-sm) + var(--skin-space-xs) / 2); font-size: calc(var(--skin-text-xs) + (var(--skin-text-sm) - var(--skin-text-xs)) * 0.7); }
        .empty {
            border: var(--skin-border-width) dashed var(--skin-color-border);
            border-radius: var(--skin-radius-lg);
            padding: calc(var(--skin-space-xl) + var(--skin-space-xs)) calc(var(--skin-space-md) + var(--skin-space-xs));
            text-align: center;
            color: var(--skin-color-text-secondary);
        }
        .editor {
            max-width: calc(var(--skin-space-md) * 60);
            margin: 0 auto;
            padding: var(--skin-space-lg) calc(var(--skin-space-md) + var(--skin-space-xs)) var(--skin-space-2xl);
        }
        .editor-head {
            display: flex;
            align-items: center;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs));
            margin-bottom: var(--skin-space-sm);
        }
        .editor h2 { margin: 0 0 var(--skin-space-xs); font-size: calc(var(--skin-text-lg) + (var(--skin-text-xl) - var(--skin-text-lg)) * 0.6); }
        .section {
            border-top: var(--skin-border-width) solid var(--skin-color-border);
            padding-top: calc(var(--skin-space-md) - var(--skin-space-xs) / 2);
            margin-top: calc(var(--skin-space-md) - var(--skin-space-xs) / 2);
        }
        .section:first-of-type { border-top: none; margin-top: 0; padding-top: 0; }
        .section h3 {
            margin: 0 0 calc(var(--skin-space-sm) + var(--skin-space-xs) / 2);
            font-size: calc(var(--skin-text-xs) + (var(--skin-text-sm) - var(--skin-text-xs)) * 0.8);
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: var(--skin-color-text-secondary);
        }
        .field {
            display: grid;
            grid-template-columns: calc(var(--skin-space-md) * 10.625) 1fr;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs) / 2);
            align-items: start;
            margin-bottom: calc(var(--skin-space-sm) + var(--skin-space-xs));
        }
        .field label {
            font-size: calc(var(--skin-text-xs) + (var(--skin-text-sm) - var(--skin-text-xs)) * 0.8);
            color: var(--skin-color-text-secondary);
            padding-top: calc(var(--skin-space-sm) + var(--skin-space-xs) / 4);
        }
        .field .hint {
            grid-column: 2;
            font-size: calc(var(--skin-text-xs) + (var(--skin-text-sm) - var(--skin-text-xs)) * 0.1);
            color: var(--skin-color-text-muted);
            margin-top: calc(var(--skin-space-xs) * -1.5);
            margin-bottom: calc(var(--skin-space-xs) * 1.5);
        }
        .field input, .field select, .field textarea { width: 100%; }
        .field textarea { min-height: calc(var(--skin-space-md) * 5.5); font-family: var(--skin-font-mono); font-size: calc(var(--skin-text-sm) + (var(--skin-text-base) - var(--skin-text-sm)) * 0.2); }
        .row2 { display: grid; grid-template-columns: 1fr 1fr; gap: calc(var(--skin-space-sm) + var(--skin-space-xs) / 2); }
        .editor-foot {
            display: flex;
            flex-wrap: wrap;
            gap: var(--skin-space-sm);
            margin-top: calc(var(--skin-space-md) + var(--skin-space-xs) / 2);
            padding-top: calc(var(--skin-space-md) - var(--skin-space-xs) / 2);
            border-top: var(--skin-border-width) solid var(--skin-color-border);
        }
        .model-list {
            border: var(--skin-border-width) solid var(--skin-color-border);
            border-radius: var(--skin-radius-md);
            max-height: calc(var(--skin-space-md) * 11.25);
            overflow: auto;
            margin: calc(var(--skin-space-xs) * 1.5) 0 calc(var(--skin-space-xs) / 2);
        }
        .model-list button {
            display: block;
            width: 100%;
            text-align: left;
            background: transparent;
            border: none;
            border-bottom: var(--skin-border-width) solid var(--skin-color-border);
            color: inherit;
            padding: var(--skin-space-sm) calc(var(--skin-space-sm) + var(--skin-space-xs));
            cursor: pointer;
            font-size: calc(var(--skin-text-xs) + (var(--skin-text-sm) - var(--skin-text-xs)) * 0.8);
        }
        .model-list button:hover, .model-list button.sel {
            background: var(--skin-color-bg-hover);
        }
        .status { font-size: calc(var(--skin-text-xs) + (var(--skin-text-sm) - var(--skin-text-xs)) * 0.8); min-height: var(--skin-leading-normal); margin: var(--skin-space-sm) 0; }
        .status.err { color: var(--skin-color-danger); }
        .status.ok { color: var(--skin-color-success); }
        .provider-strip {
            display: flex;
            flex-wrap: wrap;
            gap: var(--skin-space-sm);
            margin-bottom: calc(var(--skin-space-md) + var(--skin-space-xs) / 2);
        }
        .role-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(calc(var(--skin-space-md) * 13.75), 1fr));
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs));
        }
        .role-item {
            display: flex;
            flex-direction: column;
            gap: calc(var(--skin-space-xs) * 1.5);
        }
        .role-item label {
            font-size: calc(var(--skin-text-xs) + (var(--skin-text-sm) - var(--skin-text-xs)) * 0.7);
            font-weight: calc(var(--skin-weight-semibold) + (var(--skin-weight-bold) - var(--skin-weight-semibold)) / 2);
            color: var(--skin-color-text-primary);
        }
        .role-item .hint {
            font-size: calc(var(--skin-text-xs) + (var(--skin-text-sm) - var(--skin-text-xs)) * 0.1);
            color: var(--skin-color-text-muted);
        }
        .role-item select { width: 100%; }
        .preset-row {
            display: flex;
            align-items: center;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs) / 2);
            flex-wrap: wrap;
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs) / 2) 0;
            border-bottom: var(--skin-border-width) solid var(--skin-color-border);
        }
        .preset-row:last-child { border-bottom: none; }
        .preset-name { font-weight: calc(var(--skin-weight-semibold) + (var(--skin-weight-bold) - var(--skin-weight-semibold)) / 2); min-width: calc(var(--skin-space-md) * 8.75); }
        .preset-meta { font-size: calc(var(--skin-text-xs) + (var(--skin-text-sm) - var(--skin-text-xs)) * 0.7); color: var(--skin-color-text-muted); flex: 1; }
        .preset-actions { display: flex; flex-wrap: wrap; gap: calc(var(--skin-space-xs) * 1.5); }
        .preset-actions .btn { padding: calc(var(--skin-space-xs) * 1.25) calc(var(--skin-space-sm) + var(--skin-space-xs) / 4); font-size: calc(var(--skin-text-xs) + (var(--skin-text-sm) - var(--skin-text-xs)) * 0.7); }
    `,
    ];

    @state() private _models: ModelRow[] = [];
    @state() private _providers: ProviderRow[] = [];
    @state() private _roles: RoleBindings | null = null;
    @state() private _presets: PresetRow[] = [];
    @state() private _agents: AgentRow[] = [];
    @state() private _draft: Draft | null = null;
    @state() private _search = '';
    @state() private _filterType = 'all';
    @state() private _status = '';
    @state() private _statusOk = true;
    @state() private _loading = true;
    @state() private _keySaved: Record<string, boolean> = {};
    @state() private _liveModels: string[] = [];
    @state() private _liveSource = '';
    @state() private _applyTarget: Record<string, 'global' | 'agent' | 'chat'> = {};
    @state() private _applyAgent: Record<string, string> = {};
    @state() private _editingPreset: string | null = null;
    @state() private _presetName = '';
    @state() private _presetNotes = '';
    @state() private _presetRoles: PresetRoleDraft | null = null;

    connectedCallback(): void {
        super.connectedCallback();
        void this._reload();
    }

    private async _reload(): Promise<void> {
        this._loading = true;
        try {
            const [models, providers, roles, presets, agents] = await Promise.all([
                apiClient.get<ModelRow[]>('/llm/models'),
                apiClient.get<ProviderRow[]>('/llm/providers'),
                apiClient.get<RoleBindings>('/llm/roles'),
                apiClient.get<PresetRow[]>('/llm/presets'),
                apiClient.get<{ agents: AgentRow[] }>('/agents/').catch(() => ({ agents: [] })),
            ]);
            this._models = models || [];
            this._providers = providers || [];
            this._roles = roles;
            this._presets = presets || [];
            this._agents = (agents?.agents || []).map((a) => ({
                id: a.id || (a as unknown as { agent_id?: string }).agent_id || '',
                name: a.name || '',
                capsule_id: a.capsule_id,
            }));
            const map: Record<string, boolean> = {};
            for (const p of this._providers) map[p.id] = !!p.has_api_key;
            this._keySaved = map;
        } catch (e) {
            this._statusOk = false;
            this._status = e instanceof Error ? e.message : String(e);
        } finally {
            this._loading = false;
        }
    }

    private get _visible(): ModelRow[] {
        let rows = this._models;
        if (this._filterType !== 'all') rows = rows.filter((m) => m.model_type === this._filterType);
        const q = this._search.trim().toLowerCase();
        if (q) {
            rows = rows.filter(
                (m) =>
                    m.name.toLowerCase().includes(q) ||
                    (m.display_name || '').toLowerCase().includes(q) ||
                    (m.provider || '').toLowerCase().includes(q),
            );
        }
        return rows;
    }

    /** Roles this model is currently bound to (UI labels: Chat/Help/Memory/Vision/Decisions). */
    private _usedFor(id: string): string[] {
        if (!this._roles) return [];
        const out: string[] = [];
        for (const role of ROLE_ORDER) {
            const bound =
                this._roles[role] ||
                (role === 'decision_role' ? this._roles.decision_role_id : null);
            if (bound === id) out.push(ROLE_LABELS[role]);
        }
        return out;
    }

    private _isLive(id: string): boolean {
        return this._usedFor(id).length > 0;
    }

    private _providerBase(providerId: string): string {
        const p = this._providers.find((x) => x.id === providerId);
        return p?.base_url || '';
    }

    private async _activate(m: ModelRow): Promise<void> {
        try {
            await apiClient.patch(`/llm/models/${m.id}`, { is_active: true });
            const body: Record<string, string | null> = {};
            if (m.model_type === 'chat') {
                body.chat_role = m.id;
                if (!this._roles?.utility_role) body.utility_role = m.id;
            }
            if (m.model_type === 'embedding') body.embedding_role = m.id;
            if (m.model_type === 'decision') body.decision_role = m.id;
            if (Object.keys(body).length) await apiClient.put('/llm/roles', body);
            this._statusOk = true;
            this._status = `Live: ${m.name}`;
            await this._reload();
        } catch (e) {
            this._statusOk = false;
            this._status = e instanceof Error ? e.message : String(e);
        }
    }

    private async _setRole(role: RoleId, id: string): Promise<void> {
        const value = id || null;
        try {
            await apiClient.put('/llm/roles', { [role]: value });
            this._statusOk = true;
            this._status = value
                ? `${ROLE_LABELS[role]} → ${this._models.find((m) => m.id === value)?.name || value}`
                : `${ROLE_LABELS[role]} cleared.`;
            await this._reload();
        } catch (e) {
            this._statusOk = false;
            this._status = e instanceof Error ? e.message : String(e);
        }
    }

    private _openCreate(): void {
        const first = this._providers.find((p) => p.id !== 'custom') || this._providers[0];
        this._draft = emptyDraft(first?.id || '');
        if (first?.base_url) this._draft.api_base = first.base_url;
        this._liveModels = [];
        this._liveSource = '';
    }

    private _openEdit(m: ModelRow): void {
        this._draft = draftFromModel(m);
        this._liveModels = [];
        this._liveSource = '';
    }

    private async _saveKey(): Promise<void> {
        if (!this._draft?.api_key?.trim()) return;
        try {
            await apiClient.put(`/secrets/providers/${this._draft.provider}`, {
                api_key: this._draft.api_key.trim(),
            });
            this._draft.api_key = '';
            this._keySaved = { ...this._keySaved, [this._draft.provider]: true };
            this._providers = this._providers.map((p) =>
                p.id === this._draft!.provider ? { ...p, has_api_key: true } : p,
            );
            this._statusOk = true;
            this._status = 'Key saved to Vault (not stored in files).';
        } catch (e) {
            this._statusOk = false;
            this._status = e instanceof Error ? e.message : String(e);
        }
    }

    private async _loadModels(): Promise<void> {
        if (!this._draft) return;
        try {
            const res = await apiClient.post<{ models: string[]; source: string; detail: string }>(
                '/llm/models/search',
                {
                    provider: this._draft.provider,
                    query: '',
                    model_type: this._draft.model_type,
                    api_base: this._draft.api_base || null,
                    api_key: this._draft.api_key || null,
                },
            );
            this._liveModels = res.models || [];
            this._liveSource = res.source || 'none';
            if (res.detail) {
                this._statusOk = false;
                this._status = res.detail;
            } else {
                this._statusOk = true;
                this._status = `Loaded ${this._liveModels.length} models (${res.source})`;
            }
        } catch (e) {
            this._statusOk = false;
            this._status = e instanceof Error ? e.message : String(e);
        }
    }

    private async _saveModel(): Promise<void> {
        if (!this._draft) return;
        if (!this._draft.name.trim()) {
            this._statusOk = false;
            this._status = 'Model ID is required.';
            return;
        }
        try {
            if (this._draft.api_key.trim()) await this._saveKey();
            const payload = payloadFromDraft(this._draft);
            if (this._draft.id) {
                await apiClient.patch(`/llm/models/${this._draft.id}`, payload);
            } else {
                await apiClient.post('/llm/models', payload);
            }
            this._statusOk = true;
            this._status = 'Model saved.';
            this._draft = null;
            await this._reload();
        } catch (e) {
            this._statusOk = false;
            this._status = e instanceof Error ? e.message : String(e);
        }
    }

    private async _testConnection(): Promise<void> {
        if (!this._draft) return;
        try {
            const res = await apiClient.post<{ success: boolean; latency_ms?: number; detail: string }>(
                '/llm/test-connection',
                {
                    provider: this._draft.provider,
                    model: this._draft.name || null,
                    base_url: this._draft.api_base || null,
                    api_key: this._draft.api_key || null,
                    model_id: this._draft.id || null,
                },
            );
            this._statusOk = !!res.success;
            this._status = res.success
                ? `Connection OK (${res.latency_ms ?? 0} ms) ${res.detail}`.trim()
                : res.detail || 'Connection failed';
        } catch (e) {
            this._statusOk = false;
            this._status = e instanceof Error ? e.message : String(e);
        }
    }

    private async _deleteModel(): Promise<void> {
        if (!this._draft?.id) return;
        if (!confirm(`Delete model “${this._draft.name}”?`)) return;
        try {
            await apiClient.delete(`/llm/models/${this._draft.id}`);
            this._draft = null;
            this._statusOk = true;
            this._status = 'Model deleted.';
            await this._reload();
        } catch (e) {
            this._statusOk = false;
            this._status = e instanceof Error ? e.message : String(e);
        }
    }

    // ---- Presets -------------------------------------------------------

    private _capsuleFor(presetId: string): string | undefined {
        const target = this._applyTarget[presetId] || 'global';
        if (target === 'global') return undefined;
        const agentId = this._applyAgent[presetId] || this._agents[0]?.id || '';
        const agent = this._agents.find((a) => a.id === agentId);
        return agent?.capsule_id;
    }

    private async _applyPreset(p: PresetRow): Promise<void> {
        try {
            const capsuleId = this._capsuleFor(p.id);
            const qs = capsuleId ? `?capsule_id=${encodeURIComponent(capsuleId)}` : '';
            await apiClient.post(`/llm/presets/${p.id}/apply${qs}`, {});
            const target = this._applyTarget[p.id] || 'global';
            this._statusOk = true;
            this._status = `Preset “${p.name}” applied (${target}).`;
            await this._reload();
        } catch (e) {
            this._statusOk = false;
            this._status = e instanceof Error ? e.message : String(e);
        }
    }

    private async _duplicatePreset(p: PresetRow): Promise<void> {
        try {
            await apiClient.post('/llm/presets', {
                name: `${p.name} (copy)`,
                chat_model_id: p.chat_model_id,
                utility_model_id: p.utility_model_id,
                embedding_model_id: p.embedding_model_id,
                vision_role_id: p.vision_role_id,
                decision_role_id: p.decision_role_id,
                is_bundled: false,
                scope: p.scope,
                notes: p.notes,
            });
            this._statusOk = true;
            this._status = `Duplicated “${p.name}”.`;
            await this._reload();
        } catch (e) {
            this._statusOk = false;
            this._status = e instanceof Error ? e.message : String(e);
        }
    }

    private _openPresetEdit(p: PresetRow): void {
        if (p.is_bundled) {
            this._statusOk = false;
            this._status = 'Bundled presets are catalog rows — use Restore bundled presets to reset them.';
            return;
        }
        this._editingPreset = p.id;
        this._presetName = p.name;
        this._presetNotes = p.notes || '';
        this._presetRoles = {
            chat_model_id: p.chat_model_id || '',
            utility_model_id: p.utility_model_id || '',
            embedding_model_id: p.embedding_model_id || '',
            vision_role_id: p.vision_role_id || '',
            decision_role_id: p.decision_role_id || '',
        };
    }

    private async _savePresetEdit(): Promise<void> {
        const id = this._editingPreset;
        if (!id) return;
        const p = this._presets.find((x) => x.id === id);
        if (!p) return;
        const r = this._presetRoles;
        try {
            await apiClient.patch(`/llm/presets/${id}`, {
                name: this._presetName.trim() || p.name,
                chat_model_id: r?.chat_model_id || null,
                utility_model_id: r?.utility_model_id || null,
                embedding_model_id: r?.embedding_model_id || null,
                vision_role_id: r?.vision_role_id || null,
                decision_role_id: r?.decision_role_id || null,
                is_bundled: p.is_bundled,
                scope: p.scope,
                notes: this._presetNotes,
            });
            this._editingPreset = null;
            this._presetRoles = null;
            this._statusOk = true;
            this._status = 'Preset updated (all five roles).';
            await this._reload();
        } catch (e) {
            this._statusOk = false;
            this._status = e instanceof Error ? e.message : String(e);
        }
    }

    private async _saveCurrentAsPreset(): Promise<void> {
        const roles = this._roles;
        const name = (this._presetName || '').trim() || `Preset ${new Date().toISOString().slice(0, 10)}`;
        try {
            await apiClient.post('/llm/presets', {
                name,
                chat_model_id: roles?.chat_role || null,
                utility_model_id: roles?.utility_role || null,
                embedding_model_id: roles?.embedding_role || null,
                vision_role_id: roles?.vision_role || null,
                decision_role_id: roles?.decision_role || roles?.decision_role_id || null,
                is_bundled: false,
                scope: 'global',
                notes: this._presetNotes || 'Saved from current role bindings.',
            });
            this._presetName = '';
            this._presetNotes = '';
            this._statusOk = true;
            this._status = `Preset “${name}” saved from current roles.`;
            await this._reload();
        } catch (e) {
            this._statusOk = false;
            this._status = e instanceof Error ? e.message : String(e);
        }
    }

    private async _deletePreset(p: PresetRow): Promise<void> {
        if (p.is_bundled) {
            this._statusOk = false;
            this._status = 'Bundled presets cannot be deleted.';
            return;
        }
        if (!confirm(`Delete preset “${p.name}”?`)) return;
        try {
            await apiClient.delete(`/llm/presets/${p.id}`);
            this._statusOk = true;
            this._status = `Deleted “${p.name}”.`;
            await this._reload();
        } catch (e) {
            this._statusOk = false;
            this._status = e instanceof Error ? e.message : String(e);
        }
    }

    private async _restoreBundled(): Promise<void> {
        try {
            const res = await apiClient.post<{
                restored: string[];
                skipped: string[];
                total: number;
            }>('/llm/presets/restore-bundled', {});
            this._statusOk = res.skipped.length === 0;
            this._status = `Restored ${res.restored.length}/${res.total} bundled presets${
                res.skipped.length ? ` (skipped: ${res.skipped.join(', ')})` : ''
            }.`;
            await this._reload();
        } catch (e) {
            this._statusOk = false;
            this._status = e instanceof Error ? e.message : String(e);
        }
    }

    private _bind<K extends keyof Draft>(key: K) {
        return (ev: Event) => {
            if (!this._draft) return;
            const el = ev.target as HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;
            const raw = el.value;
            if (typeof this._draft[key] === 'boolean') {
                (this._draft as Draft)[key] = (el as HTMLInputElement).checked as Draft[K];
            } else if (typeof this._draft[key] === 'number') {
                (this._draft as Draft)[key] = Number(raw) as Draft[K];
            } else {
                (this._draft as Draft)[key] = raw as Draft[K];
            }
            if (key === 'provider') {
                this._draft.api_base = this._providerBase(raw) || this._draft.api_base;
                this._liveModels = [];
            }
            this._draft = { ...this._draft };
        };
    }


    private _typeLabel(t: string): string {
        if (t === 'embedding') return 'Embeddings';
        if (t === 'decision') return 'Decision (Clef)';
        return 'Chat';
    }

    private _modelLabel(id: string | null | undefined): string {
        if (!id) return '—';
        const m = this._models.find((x) => x.id === id);
        return m ? (m.provider && m.name ? `${m.provider}/${m.name}` : m.name) : id;
    }

    private _presetRoleSummary(p: PresetRow): string {
        const parts = [
            `Chat ${this._modelLabel(p.chat_model_id)}`,
            `Help ${this._modelLabel(p.utility_model_id)}`,
            `Memory ${this._modelLabel(p.embedding_model_id)}`,
            `Vision ${this._modelLabel(p.vision_role_id)}`,
            `Decisions ${this._modelLabel(p.decision_role_id)}`,
        ];
        return parts.join(' · ');
    }

    private _presetRoleSelect(
        label: string,
        value: string,
        required: ModelType | null,
        onPick: (id: string) => void,
    ) {
        const options = required
            ? this._models.filter((m) => m.model_type === required)
            : this._models;
        return html`
            <div class="role-item">
                <label>${label}</label>
                <select
                    .value=${value}
                    @change=${(e: Event) => onPick((e.target as HTMLSelectElement).value)}
                >
                    <option value="">— not set —</option>
                    ${options.map(
                        (m) => html`
                            <option value=${m.id} ?selected=${m.id === value}>
                                ${m.provider}/${m.name}
                            </option>
                        `,
                    )}
                </select>
            </div>
        `;
    }

    private _card(m: ModelRow) {
        const used = this._usedFor(m.id);
        const live = this._isLive(m.id);
        const keyOk = this._keySaved[m.provider];
        return html`
            <article
                class="card ${live ? 'live' : ''}"
                @click=${() => this._openEdit(m)}
                @keydown=${(e: KeyboardEvent) => {
                    if (e.key === 'Enter') this._openEdit(m);
                }}
                tabindex="0"
                role="button"
            >
                <div class="card-top">
                    ${live
                        ? html`<span class="chip live">LIVE</span>`
                        : html`<span class="chip">${m.is_active ? 'Ready' : 'Off'}</span>`}
                    <span class="chip type">${this._typeLabel(m.model_type)}</span>
                    ${keyOk
                        ? html`<span class="chip ok">Key in Vault</span>`
                        : html`<span class="chip warn">Missing</span>`}
                </div>
                <div class="model-id">${m.provider && m.name ? `${m.provider}/${m.name}` : m.name}</div>
                <div class="meta">
                    ${m.display_name || m.name} · ${m.provider}
                    ${m.api_base ? html`<br />${m.api_base}` : nothing}
                </div>
                <div class="facts">
                    <span>ctx <b>${m.ctx_length || '—'}</b></span>
                    <span>price <b>${m.cost_tier}</b></span>
                    <span>priority <b>${m.priority}</b></span>
                    <span>vision <b>${m.vision ? 'yes' : 'no'}</b></span>
                </div>
                <div class="meta">
                    ${used.length ? html`Used for: <b>${used.join(', ')}</b>` : html`Used for: —`}
                </div>
                <div class="actions" @click=${(e: Event) => e.stopPropagation()}>
                    ${live
                        ? html`<span class="chip live">Active</span>`
                        : html`<button class="btn primary" @click=${() => void this._activate(m)}>
                              Activate
                          </button>`}
                    <button class="btn ghost" @click=${() => this._openEdit(m)}>Edit</button>
                    <button
                        class="btn ghost"
                        @click=${() => {
                            this._draft = draftFromModel(m);
                            void this._testConnection();
                        }}
                    >
                        Test
                    </button>
                </div>
            </article>
        `;
    }

    private _providerStrip() {
        if (!this._providers.length) return nothing;
        return html`
            <div class="provider-strip" aria-label="Provider key status">
                ${this._providers.map(
                    (p) => html`
                        <span class="chip ${p.has_api_key ? 'ok' : 'warn'}" title=${p.label}>
                            ${p.label} — ${p.has_api_key ? 'Key in Vault' : 'Missing'}
                        </span>
                    `,
                )}
            </div>
        `;
    }

    private _rolesPanel() {
        const roles = this._roles;
        return html`
            <section class="panel" aria-label="Model roles">
                <div class="panel-head">
                    <h2>Model roles</h2>
                    <span class="meta">Used for: Chat / Help / Memory / Vision / Decisions</span>
                </div>
                ${this._loading
                    ? html`<div class="empty">Loading role bindings…</div>`
                    : !roles
                      ? html`<div class="empty">Role bindings unavailable. Fix the error above, then Refresh.</div>`
                      : html`
                            <div class="role-grid">
                                ${ROLE_ORDER.map((role) => {
                                    const current = roles[role] || '';
                                    const required = ROLE_REQUIRED_TYPE[role];
                                    const options = required
                                        ? this._models.filter((m) => m.model_type === required)
                                        : this._models;
                                    return html`
                                        <div class="role-item">
                                            <label for="role-${role}">
                                                ${ROLE_LABELS[role]}
                                                ${role === 'decision_role'
                                                    ? html`<span class="chip type">Clef</span>`
                                                    : nothing}
                                            </label>
                                            <select
                                                id="role-${role}"
                                                .value=${current}
                                                @change=${(e: Event) => {
                                                    void this._setRole(
                                                        role,
                                                        (e.target as HTMLSelectElement).value,
                                                    );
                                                }}
                                            >
                                                <option value="">— not set —</option>
                                                ${options.map(
                                                    (m) => html`
                                                        <option value=${m.id} ?selected=${m.id === current}>
                                                            ${m.provider}/${m.name}
                                                        </option>
                                                    `,
                                                )}
                                            </select>
                                            <div class="hint">
                                                ${ROLE_HINTS[role]}
                                                ${current
                                                    ? html` · bound`
                                                    : html` · not bound`}
                                            </div>
                                        </div>
                                    `;
                                })}
                            </div>
                        `}
            </section>
        `;
    }

    private _presetsPanel() {
        const bundled = this._presets.filter((p) => p.is_bundled);
        const user = this._presets.filter((p) => !p.is_bundled);
        return html`
            <section class="panel" aria-label="Model presets">
                <div class="panel-head">
                    <h2>Presets</h2>
                    <span class="meta">Each preset binds all five roles</span>
                    <button class="btn" @click=${() => void this._saveCurrentAsPreset()}>
                        Save current roles as preset
                    </button>
                    <button class="btn" @click=${() => void this._restoreBundled()}>
                        Restore bundled presets
                    </button>
                </div>
                ${this._loading
                    ? html`<div class="empty">Loading presets…</div>`
                    : this._presets.length === 0
                      ? html`<div class="empty">No presets yet. Restore bundled presets or save the current roles.</div>`
                      : html`
                            ${bundled.length
                                ? html`<div class="meta" style="margin-bottom: calc(var(--skin-space-xs) * 1.5)">Bundled</div>
                                      ${bundled.map((p) => this._presetRow(p))}`
                                : nothing}
                            ${user.length
                                ? html`<div class="meta" style="margin: calc(var(--skin-space-sm) + var(--skin-space-xs)) 0 calc(var(--skin-space-xs) * 1.5)">Yours</div>
                                      ${user.map((p) => this._presetRow(p))}`
                                : nothing}
                        `}
            </section>
        `;
    }

    private _presetRow(p: PresetRow) {
        const target = this._applyTarget[p.id] || 'global';
        const agentId = this._applyAgent[p.id] || this._agents[0]?.id || '';
        const editing = this._editingPreset === p.id;
        const r = this._presetRoles;
        return html`
            <div class="preset-row" style="flex-direction: column; align-items: stretch">
                ${editing && r
                    ? html`
                          <div style="display: flex; flex-wrap: wrap; gap: var(--skin-space-sm); margin-bottom: calc(var(--skin-space-sm) + var(--skin-space-xs) / 2)">
                              <input
                                  .value=${this._presetName}
                                  @input=${(e: Event) => {
                                      this._presetName = (e.target as HTMLInputElement).value;
                                  }}
                                  placeholder="Preset name"
                                  style="min-width: calc(var(--skin-space-md) * 10)"
                              />
                              <input
                                  .value=${this._presetNotes}
                                  @input=${(e: Event) => {
                                      this._presetNotes = (e.target as HTMLInputElement).value;
                                  }}
                                  placeholder="Notes"
                                  style="flex: 1"
                              />
                          </div>
                          <div class="role-grid" style="margin-bottom: calc(var(--skin-space-sm) + var(--skin-space-xs) / 2)">
                              ${this._presetRoleSelect(ROLE_LABELS.chat_role, r.chat_model_id, 'chat', (id) => {
                                  this._presetRoles = { ...r, chat_model_id: id };
                              })}
                              ${this._presetRoleSelect(ROLE_LABELS.utility_role, r.utility_model_id, null, (id) => {
                                  this._presetRoles = { ...r, utility_model_id: id };
                              })}
                              ${this._presetRoleSelect(ROLE_LABELS.embedding_role, r.embedding_model_id, 'embedding', (id) => {
                                  this._presetRoles = { ...r, embedding_model_id: id };
                              })}
                              ${this._presetRoleSelect(ROLE_LABELS.vision_role, r.vision_role_id, 'chat', (id) => {
                                  this._presetRoles = { ...r, vision_role_id: id };
                              })}
                              ${this._presetRoleSelect(ROLE_LABELS.decision_role, r.decision_role_id, 'decision', (id) => {
                                  this._presetRoles = { ...r, decision_role_id: id };
                              })}
                          </div>
                          <div class="preset-actions">
                              <button class="btn primary" @click=${() => void this._savePresetEdit()}>
                                  Save
                              </button>
                              <button
                                  class="btn ghost"
                                  @click=${() => {
                                      this._editingPreset = null;
                                      this._presetRoles = null;
                                  }}
                              >
                                  Cancel
                              </button>
                          </div>
                      `
                    : html`
                          <div style="display: flex; flex-wrap: wrap; gap: calc(var(--skin-space-sm) + var(--skin-space-xs) / 2); align-items: center">
                              <span class="preset-name">${p.name}</span>
                              <span class="chip ${p.is_bundled ? 'type' : 'ok'}">
                                  ${p.is_bundled ? 'Bundled' : 'User'}
                              </span>
                              <span class="preset-meta">${p.notes || p.scope || ''}</span>
                          </div>
                          <div class="preset-meta" style="margin: calc(var(--skin-space-xs) * 1.5) 0">
                              ${this._presetRoleSummary(p)}
                          </div>
                          <div class="preset-actions">
                              <select
                                  .value=${target}
                                  @change=${(e: Event) => {
                                      this._applyTarget = {
                                          ...this._applyTarget,
                                          [p.id]: (e.target as HTMLSelectElement).value as
                                              | 'global'
                                              | 'agent'
                                              | 'chat',
                                      };
                                  }}
                                  style="padding: calc(var(--skin-space-xs) * 1.25) var(--skin-space-sm); font-size: calc(var(--skin-text-xs) * 12 / 11)"
                              >
                                  <option value="global">Global</option>
                                  <option value="agent">This agent</option>
                                  <option value="chat">This chat</option>
                              </select>
                              ${target !== 'global'
                                  ? html`
                                        <select
                                            .value=${agentId}
                                            @change=${(e: Event) => {
                                                this._applyAgent = {
                                                    ...this._applyAgent,
                                                    [p.id]: (e.target as HTMLSelectElement).value,
                                                };
                                            }}
                                            style="padding: calc(var(--skin-space-xs) * 1.25) var(--skin-space-sm); font-size: calc(var(--skin-text-xs) * 12 / 11)"
                                        >
                                            ${this._agents.length
                                                ? this._agents.map(
                                                      (a) => html`
                                                          <option value=${a.id} ?selected=${a.id === agentId}>
                                                              ${a.name || a.id}
                                                          </option>
                                                      `,
                                                  )
                                                : html`<option value="">No agents</option>`}
                                        </select>
                                    `
                                  : nothing}
                              <button class="btn primary" @click=${() => void this._applyPreset(p)}>
                                  Apply
                              </button>
                              <button class="btn ghost" @click=${() => void this._duplicatePreset(p)}>
                                  Duplicate
                              </button>
                              ${p.is_bundled
                                  ? nothing
                                  : html`
                                        <button class="btn ghost" @click=${() => this._openPresetEdit(p)}>
                                            Edit
                                        </button>
                                        <button class="btn danger" @click=${() => void this._deletePreset(p)}>
                                            Delete
                                        </button>
                                    `}
                          </div>
                      `}
            </div>
        `;
    }

    private _editor() {
        const d = this._draft;
        if (!d) return nothing;
        return html`
            <div class="editor" role="region" aria-label="Add model">
                <div class="editor-head">
                    <button class="btn ghost" @click=${() => (this._draft = null)}>
                        <span class="material-symbols-outlined">arrow_back</span>
                        Back to models
                    </button>
                </div>
                <h2>${d.id ? `Model — ${d.name}` : 'Add model'}</h2>
                <div class="meta">
                    ${d.provider}
                    ${this._isLive(d.id || '') ? html` · <span class="chip live">LIVE</span>` : nothing}
                </div>

                <div class="section">
                    <h3>Provider</h3>
                    <div class="field">
                        <label>Provider</label>
                        <select .value=${d.provider} @change=${this._bind('provider')}>
                            ${this._providers.map(
                                (p) => html`
                                    <option value=${p.id} ?selected=${p.id === d.provider}>${p.label}</option>
                                `,
                            )}
                        </select>
                        <div class="hint">
                            ${this._keySaved[d.provider]
                                ? 'Key in Vault'
                                : 'No API key in Vault for this provider yet.'}
                        </div>
                    </div>
                    <div class="field">
                        <label>API key</label>
                        <div class="row2">
                            <input
                                type="password"
                                .value=${d.api_key}
                                @input=${this._bind('api_key')}
                                placeholder="${this._keySaved[d.provider]
                                    ? '•••••• (saved in Vault)'
                                    : 'Paste key…'}"
                                autocomplete="off"
                            />
                            <button class="btn" @click=${() => void this._saveKey()}>Save to Vault</button>
                        </div>
                        <div class="hint">Typed here, stored in Vault only. Never files. Never shown again.</div>
                    </div>
                    <div class="field">
                        <label>Base URL</label>
                        <input
                            .value=${d.api_base}
                            @input=${this._bind('api_base')}
                            placeholder="Optional provider base URL"
                        />
                        <div class="hint">
                            Prefilled from the provider catalog. Empty uses the provider standard
                            address. Used for “Load models” and runtime calls.
                        </div>
                    </div>
                    <div class="field">
                        <label>Model list</label>
                        <div>
                            <button class="btn" @click=${() => void this._loadModels()}>Load models</button>
                            <div class="meta" style="margin-top: calc(var(--skin-space-xs) * 1.5)">Source: ${this._liveSource || '—'}</div>
                            <div class="model-list">
                                ${this._liveModels.length === 0
                                    ? html`<button disabled>No models loaded yet</button>`
                                    : this._liveModels.map(
                                          (name) => html`
                                              <button
                                                  class="${name === d.name ? 'sel' : ''}"
                                                  @click=${() => {
                                                      this._draft = {
                                                          ...this._draft!,
                                                          name,
                                                          display_name:
                                                              this._draft!.display_name || name,
                                                      };
                                                  }}
                                              >
                                                  ${name}
                                              </button>
                                          `,
                                      )}
                            </div>
                            <div class="hint">Click a name — or type below.</div>
                        </div>
                    </div>
                </div>

                <div class="section">
                    <h3>Model</h3>
                    <div class="field">
                        <label>Model ID</label>
                        <input .value=${d.name} @input=${this._bind('name')} />
                    </div>
                    <div class="field">
                        <label>Display name</label>
                        <input .value=${d.display_name} @input=${this._bind('display_name')} />
                    </div>
                    <div class="field">
                        <label>Type</label>
                        <select .value=${d.model_type} @change=${this._bind('model_type')}>
                            <option value="chat" ?selected=${d.model_type === 'chat'}>Chat</option>
                            <option value="embedding" ?selected=${d.model_type === 'embedding'}>
                                Embeddings
                            </option>
                            <option value="decision" ?selected=${d.model_type === 'decision'}>
                                Decision (Clef)
                            </option>
                        </select>
                    </div>
                </div>

                <div class="section">
                    <h3>Used for</h3>
                    ${ROLE_ORDER.map((role) => {
                        const required = ROLE_REQUIRED_TYPE[role];
                        const allowed = !required || required === d.model_type || !!d.id;
                        return html`
                            <div class="field">
                                <label>
                                    ${ROLE_LABELS[role]}
                                    ${role === 'decision_role'
                                        ? html`<span class="chip type">Clef</span>`
                                        : nothing}
                                </label>
                                <input
                                    type="checkbox"
                                    .checked=${this._roles?.[role] === d.id}
                                    ?disabled=${!d.id || !allowed}
                                    @change=${() => {
                                        if (!d.id) return;
                                        const next =
                                            this._roles?.[role] === d.id ? '' : d.id;
                                        void this._setRole(role, next);
                                    }}
                                />
                                <div class="hint">
                                    ${ROLE_HINTS[role]}
                                    ${required && !allowed
                                        ? html` · needs a ${this._typeLabel(required)} model`
                                        : nothing}
                                </div>
                            </div>
                        `;
                    })}
                </div>

                <div class="section">
                    <h3>Advanced</h3>
                    <div class="field">
                        <label>Context window</label>
                        <input
                            type="number"
                            .value=${String(d.ctx_length)}
                            @input=${this._bind('ctx_length')}
                        />
                    </div>
                    <div class="field">
                        <label>Max output tokens</label>
                        <input
                            type="number"
                            .value=${String(d.max_tokens)}
                            @input=${this._bind('max_tokens')}
                        />
                        <div class="hint">Stored in extra options if schema has no column.</div>
                    </div>
                    <div class="field">
                        <label>Timeout (seconds)</label>
                        <input type="number" .value=${String(d.timeout)} @input=${this._bind('timeout')} />
                    </div>
                    <div class="field">
                        <label>Chat history share</label>
                        <input
                            type="number"
                            step="0.01"
                            min="0.01"
                            max="1"
                            .value=${String(d.ctx_history)}
                            @input=${this._bind('ctx_history')}
                        />
                        <div class="hint">
                            Portion of context used for chat history (Agent Zero parity).
                        </div>
                    </div>
                    <div class="field">
                        <label>Max embeds</label>
                        <input type="number" .value=${String(d.max_embeds)} @input=${this._bind('max_embeds')} />
                    </div>
                    <div class="field">
                        <label>Requests / min</label>
                        <input
                            type="number"
                            .value=${String(d.limit_requests)}
                            @input=${this._bind('limit_requests')}
                        />
                    </div>
                    <div class="field">
                        <label>Input tokens / min</label>
                        <input
                            type="number"
                            .value=${String(d.limit_input)}
                            @input=${this._bind('limit_input')}
                        />
                    </div>
                    <div class="field">
                        <label>Output tokens / min</label>
                        <input
                            type="number"
                            .value=${String(d.limit_output)}
                            @input=${this._bind('limit_output')}
                        />
                    </div>
                    <div class="field">
                        <label>Priority</label>
                        <input type="number" .value=${String(d.priority)} @input=${this._bind('priority')} />
                    </div>
                    <div class="field">
                        <label>Price level</label>
                        <select .value=${d.cost_tier} @change=${this._bind('cost_tier')}>
                            ${['free', 'low', 'standard', 'premium'].map(
                                (t) => html`<option value=${t} ?selected=${t === d.cost_tier}>${t}</option>`,
                            )}
                        </select>
                    </div>
                    <div class="field">
                        <label>Good at</label>
                        <input
                            .value=${d.capabilities}
                            @input=${this._bind('capabilities')}
                            placeholder="chat, tools, reasoning"
                        />
                    </div>
                    <div class="field">
                        <label>Used in</label>
                        <input
                            .value=${d.domains}
                            @input=${this._bind('domains')}
                            placeholder="general, product"
                        />
                    </div>
                    <div class="field">
                        <label>Sees images</label>
                        <input type="checkbox" .checked=${d.vision} @change=${this._bind('vision')} />
                    </div>
                    <div class="field">
                        <label>Extra options</label>
                        <textarea .value=${d.kwargs_text} @input=${this._bind('kwargs_text')}></textarea>
                        <div class="hint">JSON. temperature, top_p, and other model params.</div>
                    </div>
                    <div class="field">
                        <label>Use this model</label>
                        <input type="checkbox" .checked=${d.is_active} @change=${this._bind('is_active')} />
                    </div>
                </div>

                ${this._status
                    ? html`<div class="status ${this._statusOk ? 'ok' : 'err'}">${this._status}</div>`
                    : nothing}

                <div class="editor-foot">
                    <button class="btn primary" @click=${() => void this._saveModel()}>Save</button>
                    <button class="btn" @click=${() => void this._testConnection()}>Test connection</button>
                    ${d.id
                        ? html`
                              <button
                                  class="btn"
                                  @click=${() => {
                                      const row = this._models.find((m) => m.id === d.id!);
                                      if (row) void this._activate(row);
                                  }}
                              >
                                  Make live
                              </button>
                              <button class="btn danger" @click=${() => void this._deleteModel()}>
                                  Delete
                              </button>
                          `
                        : nothing}
                    <button class="btn ghost" @click=${() => (this._draft = null)}>Close</button>
                </div>
            </div>
        `;
    }

    render() {
        if (this._draft) return this._editor();
        return html`
            <div class="wrap">
                <div class="head">
                    <h1>Models</h1>
                    <button class="btn ghost" @click=${() => void this._reload()}>Refresh</button>
                    <button
                        class="btn"
                        @click=${() =>
                            window.dispatchEvent(
                                new CustomEvent('soma-navigate', { detail: { route: '/settings' } }),
                            )}
                    >
                        Settings
                    </button>
                    <button class="btn" @click=${() => void this._restoreBundled()}>
                        Restore bundled presets
                    </button>
                    <button class="btn primary" @click=${() => this._openCreate()}>Add model</button>
                </div>
                <div class="sub">
                    Cards show the whole model. Activate to make one live. Open a card for the add-model
                    wizard (Provider → key → base URL → Load models → identity → Type → Used for →
                    Advanced → Test → Save). Keys go to Vault only.
                </div>
                ${this._providerStrip()}
                ${this._rolesPanel()}
                ${this._presetsPanel()}
                <div class="toolbar">
                    <input
                        style="flex: 1; min-width: calc(var(--skin-space-md) * 11.25)"
                        placeholder="Search models…"
                        .value=${this._search}
                        @input=${(e: Event) => {
                            this._search = (e.target as HTMLInputElement).value;
                        }}
                    />
                    <select
                        .value=${this._filterType}
                        @change=${(e: Event) => {
                            this._filterType = (e.target as HTMLSelectElement).value;
                        }}
                    >
                        <option value="all">All types</option>
                        <option value="chat">Chat</option>
                        <option value="embedding">Embeddings</option>
                        <option value="decision">Decision (Clef)</option>
                    </select>
                </div>
                ${this._status
                    ? html`<div class="status ${this._statusOk ? 'ok' : 'err'}">${this._status}</div>`
                    : nothing}
                ${this._loading
                    ? html`<div class="empty">Loading models…</div>`
                    : this._visible.length === 0
                      ? html`<div class="empty">
                            No models yet. <b>Add model</b> or <b>Restore bundled presets</b>.
                        </div>`
                      : html`<div class="grid">${this._visible.map((m) => this._card(m))}</div>`}
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-settings-models': SomaSettingsModels;
    }
}

