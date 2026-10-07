/**
 * SomaAgent — Models settings (card library + Activate + Normal/Advanced modal)
 *
 * Design: SOMA-UI-MODEL-ADMIN-001 v3.2 · FIELD-PARITY-001
 * - One CSS card = one model (all identity fields visible)
 * - Activate / Make live one-click
 * - Modal: Normal | Advanced | Used for
 * - Custom URL + Load models (live list) + manual Model ID
 * - API key typed here → Vault only (write-only, never echoed)
 * - No “slot” language (Used for: Chat / Help / Memory)
 * - Default LIVE seed: Groq · DeepSeek 2.8
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import '../components/soma-status-badge.js';

type ModelType = 'chat' | 'embedding';
type ModalTab = 'normal' | 'advanced' | 'used';

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

interface UsedFor {
    chat_model_id: string | null;
    utility_model_id: string | null;
    embedding_model_id: string | null;
    capsule_id: string | null;
    scope: string;
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

const PROVIDERS = [
    { id: 'groq', label: 'Groq' },
    { id: 'openai', label: 'OpenAI' },
    { id: 'anthropic', label: 'Anthropic' },
    { id: 'ollama', label: 'Ollama' },
    { id: 'custom', label: 'Custom / OpenAI-compatible' },
];

function emptyDraft(provider = 'groq'): Draft {
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
    static styles = css`
        :host {
            display: block;
            min-height: 100%;
            background: var(--soma-bg-page, #0a0a0a);
            color: var(--soma-text-primary, #e5e5e5);
            font-family: var(--soma-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif);
        }
        * { box-sizing: border-box; }
        .wrap { max-width: 1120px; margin: 0 auto; padding: 24px 20px 48px; }
        .head { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
        h1 { font-size: 1.35rem; font-weight: 650; margin: 0; flex: 1; letter-spacing: -0.02em; }
        .sub { color: var(--soma-text-secondary, #9ca3af); font-size: 0.9rem; margin-bottom: 20px; }
        .toolbar { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 18px; }
        input, select, textarea {
            background: var(--soma-bg-input, #1a1a1a);
            border: 1px solid var(--soma-border, #2a2a2a);
            color: inherit;
            border-radius: 8px;
            padding: 9px 12px;
            font-size: 0.9rem;
        }
        input:focus, select:focus, textarea:focus {
            outline: 2px solid #3b82f6;
            outline-offset: 1px;
        }
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border: 1px solid var(--soma-border, #2a2a2a);
            background: var(--soma-bg-card, #141414);
            color: inherit;
            border-radius: 8px;
            padding: 8px 14px;
            font-size: 0.88rem;
            font-weight: 550;
            cursor: pointer;
        }
        .btn:hover { border-color: #3b82f6; }
        .btn.primary { background: #3b82f6; border-color: #3b82f6; color: #fff; }
        .btn.ghost { background: transparent; }
        .btn.danger { border-color: #ef4444; color: #ef4444; }
        .btn:disabled { opacity: 0.45; cursor: not-allowed; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 14px;
        }
        .card {
            background: var(--soma-bg-card, #141414);
            border: 1px solid var(--soma-border, #2a2a2a);
            border-radius: 12px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            transition: border-color 0.15s, box-shadow 0.15s;
            cursor: pointer;
        }
        .card:hover { border-color: #6366f1; }
        .card.live {
            border-color: #3b82f6;
            box-shadow: 0 0 0 1px #3b82f655;
        }
        .card-top { display: flex; align-items: center; gap: 8px; }
        .chip {
            font-size: 0.68rem;
            font-weight: 650;
            letter-spacing: 0.02em;
            padding: 2px 8px;
            border-radius: 999px;
            background: #1f2937;
            color: #cbd5e1;
        }
        .chip.live { background: #1d4ed8; color: #fff; }
        .chip.type { background: #312e81; color: #c7d2fe; }
        .chip.warn { background: #78350f; color: #fcd34d; }
        .chip.err { background: #7f1d1d; color: #fecaca; }
        .model-id { font-weight: 650; font-size: 1rem; letter-spacing: -0.01em; }
        .meta { color: var(--soma-text-secondary, #9ca3af); font-size: 0.8rem; line-height: 1.45; }
        .facts {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 4px 10px;
            font-size: 0.75rem;
            color: var(--soma-text-secondary, #94a3b8);
        }
        .facts b { color: var(--soma-text-primary, #e5e5e5); font-weight: 550; }
        .actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }
        .actions .btn { padding: 6px 10px; font-size: 0.78rem; }
        .empty {
            border: 1px dashed var(--soma-border, #2a2a2a);
            border-radius: 12px;
            padding: 36px 20px;
            text-align: center;
            color: var(--soma-text-secondary, #9ca3af);
        }
        .modal-backdrop {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.55);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            padding: 16px;
        }
        .modal {
            width: min(720px, 100%);
            max-height: min(92vh, 900px);
            overflow: auto;
            background: var(--soma-bg-card, #121212);
            border: 1px solid var(--soma-border, #2a2a2a);
            border-radius: 14px;
            padding: 20px 22px 22px;
        }
        .modal h2 { margin: 0 0 4px; font-size: 1.15rem; }
        .tabs { display: flex; gap: 6px; margin: 14px 0 16px; border-bottom: 1px solid var(--soma-border, #2a2a2a); }
        .tab {
            background: transparent;
            border: none;
            color: var(--soma-text-secondary, #9ca3af);
            padding: 10px 14px;
            font-weight: 600;
            cursor: pointer;
            border-bottom: 2px solid transparent;
        }
        .tab.on { color: #fff; border-bottom-color: #3b82f6; }
        .field {
            display: grid;
            grid-template-columns: 170px 1fr;
            gap: 10px;
            align-items: start;
            margin-bottom: 12px;
        }
        .field label {
            font-size: 0.82rem;
            color: var(--soma-text-secondary, #9ca3af);
            padding-top: 9px;
        }
        .field .hint {
            grid-column: 2;
            font-size: 0.72rem;
            color: var(--soma-text-secondary, #64748b);
            margin-top: -6px;
            margin-bottom: 6px;
        }
        .field input, .field select, .field textarea { width: 100%; }
        .field textarea { min-height: 88px; font-family: ui-monospace, monospace; font-size: 0.8rem; }
        .row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .modal-foot {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 18px;
            padding-top: 14px;
            border-top: 1px solid var(--soma-border, #2a2a2a);
        }
        .model-list {
            border: 1px solid var(--soma-border, #2a2a2a);
            border-radius: 8px;
            max-height: 180px;
            overflow: auto;
            margin: 6px 0 2px;
        }
        .model-list button {
            display: block;
            width: 100%;
            text-align: left;
            background: transparent;
            border: none;
            border-bottom: 1px solid var(--soma-border, #2a2a2a);
            color: inherit;
            padding: 8px 12px;
            cursor: pointer;
            font-size: 0.85rem;
        }
        .model-list button:hover, .model-list button.sel { background: #1e3a5f; }
        .status { font-size: 0.85rem; min-height: 1.2em; margin: 8px 0; }
        .status.err { color: #f87171; }
        .status.ok { color: #34d399; }
    `;

    @state() private _models: ModelRow[] = [];
    @state() private _used: UsedFor | null = null;
    @state() private _draft: Draft | null = null;
    @state() private _tab: ModalTab = 'normal';
    @state() private _search = '';
    @state() private _filterType = 'all';
    @state() private _status = '';
    @state() private _statusOk = true;
    @state() private _loading = true;
    @state() private _keySaved: Record<string, boolean> = {};
    @state() private _liveModels: string[] = [];
    @state() private _liveSource = '';

    connectedCallback(): void {
        super.connectedCallback();
        void this._reload();
    }

    private async _reload(): Promise<void> {
        this._loading = true;
        try {
            this._models = await apiClient.get<ModelRow[]>('/llm/models');
            this._used = await apiClient.get<UsedFor>('/llm/slots');
            const secrets = await apiClient.get<{ provider: string; configured: boolean }[]>(
                '/secrets/providers',
            );
            const map: Record<string, boolean> = {};
            for (const s of secrets || []) map[s.provider] = !!s.configured;
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

    private _usedFor(id: string): string[] {
        if (!this._used) return [];
        const out: string[] = [];
        if (this._used.chat_model_id === id) out.push('Chat');
        if (this._used.utility_model_id === id) out.push('Help');
        if (this._used.embedding_model_id === id) out.push('Memory');
        return out;
    }

    private _isLive(id: string): boolean {
        return !!this._used && this._used.chat_model_id === id;
    }

    private async _activate(m: ModelRow): Promise<void> {
        try {
            await apiClient.patch(`/llm/models/${m.id}`, { is_active: true });
            const body: Record<string, string | null> = {};
            if (m.model_type === 'chat') body.chat_model_id = m.id;
            if (m.model_type === 'embedding') body.embedding_model_id = m.id;
            if (m.model_type === 'chat' && !this._used?.utility_model_id) body.utility_model_id = m.id;
            if (Object.keys(body).length) await apiClient.put('/llm/slots', body);
            this._statusOk = true;
            this._status = `Live: ${m.name}`;
            await this._reload();
        } catch (e) {
            this._statusOk = false;
            this._status = e instanceof Error ? e.message : String(e);
        }
    }

    private async _setUsed(role: 'chat' | 'help' | 'memory', id: string): Promise<void> {
        const key =
            role === 'chat' ? 'chat_model_id' : role === 'help' ? 'utility_model_id' : 'embedding_model_id';
        await apiClient.put('/llm/slots', { [key]: id });
        await this._reload();
    }

    private _openCreate(): void {
        this._draft = emptyDraft('groq');
        this._tab = 'normal';
        this._liveModels = [];
    }

    private _openEdit(m: ModelRow): void {
        this._draft = draftFromModel(m);
        this._tab = 'normal';
        this._liveModels = [];
    }

    private async _saveKey(): Promise<void> {
        if (!this._draft?.api_key?.trim()) return;
        try {
            await apiClient.put(`/secrets/providers/${this._draft.provider}`, {
                api_key: this._draft.api_key.trim(),
            });
            this._draft.api_key = '';
            this._keySaved = { ...this._keySaved, [this._draft.provider]: true };
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
        await apiClient.delete(`/llm/models/${this._draft.id}`);
        this._draft = null;
        await this._reload();
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
            this._draft = { ...this._draft };
        };
    }

    private _card(m: ModelRow) {
        const used = this._usedFor(m.id);
        const live = this._isLive(m.id);
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
                    <span class="chip type">${m.model_type === 'embedding' ? 'Embeddings' : 'Chat'}</span>
                    ${!this._keySaved[m.provider]
                        ? html`<span class="chip warn">Needs key</span>`
                        : nothing}
                </div>
                <div class="model-id">${m.name}</div>
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
                        ? html`<span class="chip live">✓ Active</span>`
                        : html`<button class="btn primary" @click=${() => void this._activate(m)}>
                              Activate
                          </button>`}
                    <button class="btn ghost" @click=${() => this._openEdit(m)}>Edit</button>
                    <button class="btn ghost" @click=${() => this._openEdit(m)}>Test</button>
                </div>
            </article>
        `;
    }

    private _editor() {
        const d = this._draft;
        if (!d) return nothing;
        return html`
            <div class="modal-backdrop" @click=${(e: Event) => {
                if (e.target === e.currentTarget) this._draft = null;
            }}>
                <div class="modal" role="dialog" aria-label="Model editor">
                    <h2>${d.id ? `Edit model — ${d.name}` : 'Add model'}</h2>
                    <div class="meta">
                        ${d.provider}
                        ${this._isLive(d.id || '')
                            ? html` · <span class="chip live">LIVE</span>`
                            : nothing}
                    </div>
                    <div class="tabs">
                        <button
                            class="tab ${this._tab === 'normal' ? 'on' : ''}"
                            @click=${() => (this._tab = 'normal')}
                        >
                            Normal
                        </button>
                        <button
                            class="tab ${this._tab === 'advanced' ? 'on' : ''}"
                            @click=${() => (this._tab = 'advanced')}
                        >
                            Advanced
                        </button>
                        <button
                            class="tab ${this._tab === 'used' ? 'on' : ''}"
                            @click=${() => (this._tab = 'used')}
                        >
                            Used for
                        </button>
                    </div>

                    ${this._tab === 'normal'
                        ? html`
                              <div class="field">
                                  <label>Provider</label>
                                  <select .value=${d.provider} @change=${this._bind('provider')}>
                                      ${PROVIDERS.map(
                                          (p) =>
                                              html`<option value=${p.id} ?selected=${p.id === d.provider}>
                                                  ${p.label}
                                              </option>`,
                                      )}
                                  </select>
                              </div>
                              <div class="field">
                                  <label>Custom URL</label>
                                  <input
                                      .value=${d.api_base}
                                      @input=${this._bind('api_base')}
                                      placeholder="https://… (optional — MiMo / gateway / local)"
                                  />
                                  <div class="hint">
                                      Empty uses the provider standard address. Used for “Load models” and
                                      runtime calls.
                                  </div>
                              </div>
                              <div class="field">
                                  <label>Provider key</label>
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
                                      <button class="btn" @click=${() => void this._saveKey()}>
                                          Save to Vault
                                      </button>
                                  </div>
                                  <div class="hint">
                                      Typed here, stored in Vault only. Never files. Never shown again.
                                  </div>
                              </div>
                              <div class="field">
                                  <label>Model list</label>
                                  <div>
                                      <button class="btn" @click=${() => void this._loadModels()}>
                                          Load models
                                      </button>
                                      <div class="meta" style="margin-top: 6px">
                                          Source: ${this._liveSource || '—'}
                                      </div>
                                      <div class="model-list">
                                          ${this._liveModels.length === 0
                                              ? html`<button disabled>No models loaded yet</button>`
                                              : this._liveModels.map(
                                                    (name) =>
                                                        html`<button
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
                                                        </button>`,
                                                )}
                                      </div>
                                      <div class="hint">Click a name — or type below.</div>
                                  </div>
                              </div>
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
                                      <option
                                          value="embedding"
                                          ?selected=${d.model_type === 'embedding'}
                                      >
                                          Embeddings
                                      </option>
                                  </select>
                              </div>
                              <div class="field">
                                  <label>Price level</label>
                                  <select .value=${d.cost_tier} @change=${this._bind('cost_tier')}>
                                      ${['free', 'low', 'standard', 'premium'].map(
                                          (t) =>
                                              html`<option value=${t} ?selected=${t === d.cost_tier}>
                                                  ${t}
                                              </option>`,
                                      )}
                                  </select>
                              </div>
                              <div class="field">
                                  <label>Sees images</label>
                                  <input
                                      type="checkbox"
                                      .checked=${d.vision}
                                      @change=${this._bind('vision')}
                                  />
                              </div>
                              <div class="field">
                                  <label>Use this model</label>
                                  <input
                                      type="checkbox"
                                      .checked=${d.is_active}
                                      @change=${this._bind('is_active')}
                                  />
                              </div>
                          `
                        : nothing}

                    ${this._tab === 'advanced'
                        ? html`
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
                                  <input
                                      type="number"
                                      .value=${String(d.timeout)}
                                      @input=${this._bind('timeout')}
                                  />
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
                                  <input
                                      type="number"
                                      .value=${String(d.max_embeds)}
                                      @input=${this._bind('max_embeds')}
                                  />
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
                                  <input
                                      type="number"
                                      .value=${String(d.priority)}
                                      @input=${this._bind('priority')}
                                  />
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
                                  <label>Extra options</label>
                                  <textarea
                                      .value=${d.kwargs_text}
                                      @input=${this._bind('kwargs_text')}
                                  ></textarea>
                                  <div class="hint">JSON. temperature, top_p, and other model params.</div>
                              </div>
                          `
                        : nothing}

                    ${this._tab === 'used'
                        ? html`
                              <div class="field">
                                  <label>Chat</label>
                                  <input
                                      type="checkbox"
                                      .checked=${this._used?.chat_model_id === d.id}
                                      @change=${() => d.id && void this._setUsed('chat', d.id)}
                                  />
                                  <div class="hint">Primary conversations</div>
                              </div>
                              <div class="field">
                                  <label>Help</label>
                                  <input
                                      type="checkbox"
                                      .checked=${this._used?.utility_model_id === d.id}
                                      @change=${() => d.id && void this._setUsed('help', d.id)}
                                  />
                                  <div class="hint">Summaries and background work</div>
                              </div>
                              <div class="field">
                                  <label>Memory</label>
                                  <input
                                      type="checkbox"
                                      .checked=${this._used?.embedding_model_id === d.id}
                                      @change=${() => d.id && void this._setUsed('memory', d.id)}
                                  />
                                  <div class="hint">Embeddings for memory and search</div>
                              </div>
                          `
                        : nothing}

                    ${this._status
                        ? html`<div class="status ${this._statusOk ? 'ok' : 'err'}">${this._status}</div>`
                        : nothing}

                    <div class="modal-foot">
                        <button class="btn primary" @click=${() => void this._saveModel()}>Save model</button>
                        <button class="btn" @click=${() => void this._testConnection()}>
                            Test connection
                        </button>
                        ${d.id
                            ? html`<button class="btn" @click=${() => void this._activate(this._models.find((m) => m.id === d.id!)!)}>
                                  Make live
                              </button>
                              <button class="btn danger" @click=${() => void this._deleteModel()}>
                                  Delete
                              </button>`
                            : nothing}
                        <button class="btn ghost" @click=${() => (this._draft = null)}>Cancel</button>
                    </div>
                </div>
            </div>
        `;
    }

    render() {
        return html`
            <div class="wrap">
                <div class="head">
                    <h1>Models</h1>
                    <button class="btn ghost" @click=${() => void this._reload()}>Refresh</button>
                    <button class="btn" @click=${() => (window.location.hash = '#/settings')}>
                        Manage keys
                    </button>
                    <button class="btn primary" @click=${() => this._openCreate()}>Add model</button>
                </div>
                <div class="sub">
                    Cards show the whole model. Activate to make one live. Open a card for Normal /
                    Advanced / Used for. Keys go to Vault only. Custom URL supports MiMo and gateways.
                </div>
                <div class="toolbar">
                    <input
                        style="flex: 1; min-width: 180px"
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
                    </select>
                </div>
                ${this._status && !this._draft
                    ? html`<div class="status ${this._statusOk ? 'ok' : 'err'}">${this._status}</div>`
                    : nothing}
                ${this._loading
                    ? html`<div class="empty">Loading models…</div>`
                    : this._visible.length === 0
                      ? html`<div class="empty">
                            No models yet. <b>Add model</b> or seed Groq DeepSeek 2.8 from the agent
                            defaults.
                        </div>`
                      : html`<div class="grid">${this._visible.map((m) => this._card(m))}</div>`}
            </div>
            ${this._editor()}
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-settings-models': SomaSettingsModels;
    }
}
