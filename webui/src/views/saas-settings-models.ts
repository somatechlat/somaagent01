/**
 * SomaAgent SaaS — Models Settings Screen (C5 / MD-01…MD-06)
 *
 * VIBE COMPLIANT:
 * - Real Lit 3.x, saas-* components
 * - Real APIs: /api/v2/llm (LLMModelConfig), /api/v2/secrets (Vault keys)
 * - Write-only API keys (never echoed)
 * - No mock data, no hardcoded API keys
 * - Material Symbols only, no emojis
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import '../components/saas-status-badge.js';
import '../components/saas-toggle.js';

type TabId = 'providers' | 'slots' | 'presets' | 'models';

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
    model_type: 'chat' | 'embedding';
    provider: string;
    api_base: string;
    is_active: boolean;
    ctx_length: number;
    capabilities: string[];
}

interface SlotsState {
    chat_model_id: string | null;
    utility_model_id: string | null;
    embedding_model_id: string | null;
    capsule_id: string | null;
    scope: string;
}

interface PresetRow {
    id: string;
    name: string;
    chat_model_id: string | null;
    utility_model_id: string | null;
    embedding_model_id: string | null;
    notes: string;
}

interface SetupGate {
    needs_setup: boolean;
    active_models: number;
    chat_ready: boolean;
    utility_ready: boolean;
    embedding_ready: boolean;
    message: string;
}

interface CapsuleOption {
    id: string;
    name: string;
}

@customElement('saas-settings-models')
export class SaasSettingsModels extends LitElement {
    static styles = css`
        :host {
            display: flex;
            height: 100vh;
            background: var(--saas-bg-page, #f5f5f5);
            font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
            color: var(--saas-text-primary, #1a1a1a);
        }
        * { box-sizing: border-box; }
        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: 20px;
            line-height: 1;
            display: inline-block;
            white-space: nowrap;
            -webkit-font-feature-settings: 'liga';
            -webkit-font-smoothing: antialiased;
        }

        .sidebar {
            width: 240px;
            background: var(--saas-bg-card, #ffffff);
            border-right: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
            padding: 24px 0;
        }
        .sidebar-header { padding: 0 20px 20px; border-bottom: 1px solid var(--saas-border-light, #e0e0e0); margin-bottom: 16px; }
        .sidebar-title { font-size: 20px; font-weight: 600; margin: 0 0 4px 0; }
        .sidebar-subtitle { font-size: 13px; color: var(--saas-text-secondary, #666); margin: 0; }
        .tab-list { display: flex; flex-direction: column; gap: 4px; padding: 0 12px; }
        .tab-item {
            display: flex; align-items: center; gap: 12px;
            padding: 12px 14px; border-radius: 8px; font-size: 14px;
            color: var(--saas-text-secondary, #666); cursor: pointer;
            border: none; background: transparent; width: 100%; text-align: left;
        }
        .tab-item:hover { background: var(--saas-bg-hover, #fafafa); color: var(--saas-text-primary, #1a1a1a); }
        .tab-item.active { background: var(--saas-bg-active, #f0f0f0); color: var(--saas-text-primary, #1a1a1a); font-weight: 500; }
        .back-btn {
            display: flex; align-items: center; gap: 8px;
            padding: 12px 20px; margin-top: auto; font-size: 14px;
            color: var(--saas-text-secondary, #666); cursor: pointer;
            border: none; background: transparent;
        }

        .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
        .header {
            padding: 16px 24px; background: var(--saas-bg-card, #ffffff);
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex; align-items: center; justify-content: space-between; gap: 16px;
        }
        .header-title { font-size: 18px; font-weight: 600; margin: 0; }
        .header-actions { display: flex; gap: 8px; align-items: center; }
        .content { flex: 1; overflow-y: auto; padding: 24px; }

        .section {
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 12px; padding: 24px; margin-bottom: 20px;
        }
        .section-title {
            font-size: 16px; font-weight: 600; margin: 0 0 8px 0;
            display: flex; align-items: center; gap: 10px;
        }
        .section-desc { font-size: 13px; color: var(--saas-text-secondary, #666); margin: 0 0 20px 0; }

        .btn {
            display: inline-flex; align-items: center; gap: 8px;
            padding: 10px 16px; border-radius: 8px; font-size: 13px; font-weight: 500;
            cursor: pointer; border: 1px solid var(--saas-border-light, #e0e0e0);
            background: var(--saas-bg-card, #ffffff); color: var(--saas-text-primary, #1a1a1a);
        }
        .btn:hover { background: var(--saas-bg-hover, #fafafa); }
        .btn.primary { background: #1a1a1a; color: #fff; border-color: #1a1a1a; }
        .btn.primary:hover { background: #333; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn .material-symbols-outlined { font-size: 16px; }

        .provider-row {
            display: grid;
            grid-template-columns: 160px 80px 1fr 1fr auto;
            gap: 12px; align-items: end;
            padding: 16px 0; border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
        }
        .provider-row:last-child { border-bottom: none; }
        .provider-name { font-weight: 600; font-size: 14px; display: flex; align-items: center; gap: 8px; min-height: 40px; }

        label.field-label {
            display: block; font-size: 12px; font-weight: 500;
            margin-bottom: 6px; color: var(--saas-text-secondary, #666);
        }
        input, select {
            width: 100%; padding: 10px 12px; border-radius: 8px;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            font-size: 13px; background: var(--saas-bg-card, #ffffff);
            color: var(--saas-text-primary, #1a1a1a);
        }
        input:focus, select:focus { outline: none; border-color: #1a1a1a; }
        input[type="password"] { font-family: monospace; letter-spacing: 0.05em; }

        .key-row {
            display: grid; grid-template-columns: 160px 1fr auto auto;
            gap: 12px; align-items: end;
            padding: 12px 0; border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
        }
        .key-row:last-child { border-bottom: none; }
        .key-hint { font-size: 11px; color: var(--saas-text-muted, #999); margin-top: 4px; }

        .slot-grid {
            display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;
        }
        @media (max-width: 960px) {
            .provider-row { grid-template-columns: 1fr 1fr; }
            .slot-grid { grid-template-columns: 1fr; }
            .key-row { grid-template-columns: 1fr; }
        }
        .slot-card {
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 10px; padding: 16px; background: var(--saas-bg-hover, #fafafa);
        }
        .slot-card h4 {
            margin: 0 0 4px 0; font-size: 14px;
            display: flex; align-items: center; gap: 8px;
        }
        .slot-card p { margin: 0 0 12px 0; font-size: 12px; color: var(--saas-text-secondary, #666); }

        .gate {
            border: 1px solid #f59e0b;
            background: rgba(245, 158, 11, 0.08);
            border-radius: 12px; padding: 20px 24px; margin-bottom: 20px;
            display: flex; gap: 16px; align-items: flex-start;
        }
        .gate .material-symbols-outlined { color: #d97706; font-size: 28px; }
        .gate h3 { margin: 0 0 6px 0; font-size: 15px; }
        .gate p { margin: 0; font-size: 13px; color: var(--saas-text-secondary, #555); line-height: 1.5; }

        .toast {
            position: fixed; bottom: 24px; right: 24px; z-index: 1000;
            padding: 12px 18px; border-radius: 8px; font-size: 13px;
            background: #1a1a1a; color: #fff; max-width: 420px;
        }
        .toast.error { background: #b91c1c; }
        .toast.ok { background: #047857; }

        .table {
            width: 100%; border-collapse: collapse; font-size: 13px;
        }
        .table th {
            text-align: left; font-size: 11px; text-transform: uppercase;
            letter-spacing: 0.4px; color: var(--saas-text-secondary, #666);
            padding: 8px 10px; border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
        }
        .table td {
            padding: 10px; border-bottom: 1px solid var(--saas-border-light, #eee);
            vertical-align: middle;
        }
        .row-actions { display: flex; gap: 6px; justify-content: flex-end; }
        .muted { color: var(--saas-text-muted, #999); font-size: 12px; }
        .form-grid {
            display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px;
        }
        .inline-form {
            display: grid; grid-template-columns: 1fr 1fr 1fr 1fr auto; gap: 12px; align-items: end;
            margin-top: 16px;
        }
        @media (max-width: 960px) {
            .form-grid, .inline-form { grid-template-columns: 1fr; }
        }
        .badge-wrap { display: inline-flex; gap: 6px; }
    `;

    @state() private _tab: TabId = 'providers';
    @state() private _loading = false;
    @state() private _saving = false;
    @state() private _message: { kind: 'ok' | 'error'; text: string } | null = null;

    @state() private _providers: ProviderRow[] = [];
    @state() private _keys: Record<string, { configured: boolean; draft: string }> = {};
    @state() private _models: ModelRow[] = [];
    @state() private _slots: SlotsState = {
        chat_model_id: null,
        utility_model_id: null,
        embedding_model_id: null,
        capsule_id: null,
        scope: 'tenant',
    };
    @state() private _capsules: CapsuleOption[] = [];
    @state() private _presets: PresetRow[] = [];
    @state() private _gate: SetupGate | null = null;
    @state() private _testBusy: Record<string, boolean> = {};
    @state() private _testResult: Record<string, { ok: boolean; detail: string }> = {};
    @state() private _presetName = '';
    @state() private _presetNotes = '';
    @state() private _newModel: Partial<ModelRow> & { provider: string; name: string; model_type: 'chat' | 'embedding' } = {
        name: '',
        provider: 'openai',
        model_type: 'chat',
        display_name: '',
        api_base: '',
    };

    private _tabs: { id: TabId; label: string; icon: string }[] = [
        { id: 'providers', label: 'Providers', icon: 'dns' },
        { id: 'slots', label: 'Model Slots', icon: 'account_tree' },
        { id: 'presets', label: 'Presets', icon: 'bookmark' },
        { id: 'models', label: 'Model Catalog', icon: 'smart_toy' },
    ];

    async connectedCallback() {
        super.connectedCallback();
        await this._loadAll();
    }

    private async _loadAll() {
        this._loading = true;
        try {
            await Promise.all([
                this._loadProviders(),
                this._loadKeys(),
                this._loadModels(),
                this._loadSlots(),
                this._loadPresets(),
                this._loadCapsules(),
                this._loadGate(),
            ]);
        } catch (err) {
            this._flash('error', `Failed to load model settings: ${err instanceof Error ? err.message : err}`);
        } finally {
            this._loading = false;
        }
    }

    private _flash(kind: 'ok' | 'error', text: string) {
        this._message = { kind, text };
        window.setTimeout(() => {
            if (this._message?.text === text) this._message = null;
        }, 5000);
    }

    private async _loadProviders() {
        this._providers = await apiClient.get<ProviderRow[]>('/llm/providers');
    }

    private async _loadKeys() {
        const rows = await apiClient.get<{ provider: string; configured: boolean }[]>('/secrets/providers');
        const next: Record<string, { configured: boolean; draft: string }> = {};
        for (const row of rows) {
            next[row.provider] = { configured: row.configured, draft: this._keys[row.provider]?.draft ?? '' };
        }
        this._keys = next;
    }

    private async _loadModels() {
        this._models = await apiClient.get<ModelRow[]>('/llm/models');
    }

    private async _loadSlots() {
        const capsuleId = this._slots.capsule_id || undefined;
        const q = capsuleId ? `?capsule_id=${encodeURIComponent(capsuleId)}` : '';
        this._slots = await apiClient.get<SlotsState>(`/llm/slots${q}`);
    }

    private async _loadPresets() {
        this._presets = await apiClient.get<PresetRow[]>('/llm/presets');
    }

    private async _loadCapsules() {
        try {
            const rows = await apiClient.get<{ id: string; name: string }[]>('/capsules/');
            this._capsules = (rows || []).map(r => ({ id: String(r.id), name: r.name }));
        } catch {
            this._capsules = [];
        }
    }

    private async _loadGate() {
        const capsuleId = this._slots.capsule_id || undefined;
        const q = capsuleId ? `?capsule_id=${encodeURIComponent(capsuleId)}` : '';
        this._gate = await apiClient.get<SetupGate>(`/llm/setup-gate${q}`);
    }

    private async _saveProvider(p: ProviderRow) {
        this._saving = true;
        try {
            await apiClient.put(`/llm/providers/${p.id}`, {
                enabled: p.enabled,
                base_url: p.base_url,
                model_name: p.model_name,
                label: p.is_custom ? p.label : undefined,
            });
            this._flash('ok', `Provider ${p.label} saved`);
            await Promise.all([this._loadProviders(), this._loadGate()]);
        } catch (err) {
            this._flash('error', `Save provider failed: ${err instanceof Error ? err.message : err}`);
        } finally {
            this._saving = false;
        }
    }

    private async _saveKey(provider: string) {
        const draft = (this._keys[provider]?.draft || '').trim();
        if (!draft) {
            this._flash('error', 'API key is required (write-only — it will not be shown again)');
            return;
        }
        this._saving = true;
        try {
            const res = await apiClient.put<{ saved: boolean; detail: string }>(
                `/secrets/providers/${provider}`,
                { api_key: draft }
            );
            if (!res.saved) {
                this._flash('error', `Key not saved for ${provider}: ${res.detail}`);
                return;
            }
            this._keys = {
                ...this._keys,
                [provider]: { configured: true, draft: '' },
            };
            this._flash('ok', `API key for ${provider} stored in Vault (never echoed back)`);
            await this._loadProviders();
        } catch (err) {
            this._flash('error', `Save key failed: ${err instanceof Error ? err.message : err}`);
        } finally {
            this._saving = false;
        }
    }

    private async _deleteKey(provider: string) {
        this._saving = true;
        try {
            await apiClient.delete(`/secrets/providers/${provider}`);
            this._keys = {
                ...this._keys,
                [provider]: { configured: false, draft: '' },
            };
            this._flash('ok', `API key for ${provider} deleted from Vault`);
            await this._loadProviders();
        } catch (err) {
            this._flash('error', `Delete key failed: ${err instanceof Error ? err.message : err}`);
        } finally {
            this._saving = false;
        }
    }

    private async _testConnection(opts: {
        provider: string;
        model?: string;
        base_url?: string;
        model_id?: string;
        api_key?: string;
    }) {
        const key = opts.model_id || opts.provider;
        this._testBusy = { ...this._testBusy, [key]: true };
        try {
            const res = await apiClient.post<{ success: boolean; latency_ms?: number; detail: string }>(
                '/llm/test-connection',
                {
                    provider: opts.provider,
                    model: opts.model || undefined,
                    base_url: opts.base_url || undefined,
                    model_id: opts.model_id || undefined,
                    api_key: opts.api_key || undefined,
                }
            );
            this._testResult = {
                ...this._testResult,
                [key]: {
                    ok: res.success,
                    detail: res.success
                        ? `Connected${res.latency_ms != null ? ` (${res.latency_ms}ms)` : ''}`
                        : res.detail || 'Connection failed',
                },
            };
        } catch (err) {
            this._testResult = {
                ...this._testResult,
                [key]: { ok: false, detail: err instanceof Error ? err.message : String(err) },
            };
        } finally {
            this._testBusy = { ...this._testBusy, [key]: false };
        }
    }

    private async _saveSlots() {
        this._saving = true;
        try {
            await apiClient.put('/llm/slots', {
                chat_model_id: this._slots.chat_model_id,
                utility_model_id: this._slots.utility_model_id,
                embedding_model_id: this._slots.embedding_model_id,
                capsule_id: this._slots.capsule_id,
            });
            this._flash('ok', 'Model slots saved');
            await Promise.all([this._loadSlots(), this._loadGate()]);
        } catch (err) {
            this._flash('error', `Save slots failed: ${err instanceof Error ? err.message : err}`);
        } finally {
            this._saving = false;
        }
    }

    private async _savePreset() {
        const name = this._presetName.trim();
        if (!name) {
            this._flash('error', 'Preset name is required');
            return;
        }
        this._saving = true;
        try {
            await apiClient.post('/llm/presets', {
                name,
                notes: this._presetNotes,
                chat_model_id: this._slots.chat_model_id,
                utility_model_id: this._slots.utility_model_id,
                embedding_model_id: this._slots.embedding_model_id,
            });
            this._presetName = '';
            this._presetNotes = '';
            this._flash('ok', `Preset "${name}" saved`);
            await this._loadPresets();
        } catch (err) {
            this._flash('error', `Save preset failed: ${err instanceof Error ? err.message : err}`);
        } finally {
            this._saving = false;
        }
    }

    private async _applyPreset(p: PresetRow) {
        this._saving = true;
        try {
            await apiClient.post(
                `/llm/presets/${p.id}/apply${this._slots.capsule_id ? `?capsule_id=${this._slots.capsule_id}` : ''}`,
                {}
            );
            this._flash('ok', `Preset "${p.name}" applied`);
            await Promise.all([this._loadSlots(), this._loadGate()]);
        } catch (err) {
            this._flash('error', `Apply preset failed: ${err instanceof Error ? err.message : err}`);
        } finally {
            this._saving = false;
        }
    }

    private async _deletePreset(p: PresetRow) {
        try {
            await apiClient.delete(`/llm/presets/${p.id}`);
            this._flash('ok', `Preset "${p.name}" deleted`);
            await this._loadPresets();
        } catch (err) {
            this._flash('error', `Delete preset failed: ${err instanceof Error ? err.message : err}`);
        }
    }

    private async _createModel() {
        const m = this._newModel;
        if (!m.name.trim() || !m.provider.trim()) {
            this._flash('error', 'Model name and provider are required');
            return;
        }
        this._saving = true;
        try {
            await apiClient.post('/llm/models', {
                name: m.name.trim(),
                display_name: (m.display_name || m.name).trim(),
                model_type: m.model_type,
                provider: m.provider.trim(),
                api_base: (m.api_base || '').trim(),
                is_active: true,
            });
            this._newModel = {
                name: '',
                provider: this._newModel.provider,
                model_type: this._newModel.model_type,
                display_name: '',
                api_base: '',
            };
            this._flash('ok', 'Model configuration created');
            await Promise.all([this._loadModels(), this._loadGate()]);
        } catch (err) {
            this._flash('error', `Create model failed: ${err instanceof Error ? err.message : err}`);
        } finally {
            this._saving = false;
        }
    }

    private async _toggleModelActive(m: ModelRow) {
        try {
            await apiClient.patch(`/llm/models/${m.id}`, { is_active: !m.is_active });
            await Promise.all([this._loadModels(), this._loadGate()]);
        } catch (err) {
            this._flash('error', `Toggle model failed: ${err instanceof Error ? err.message : err}`);
        }
    }

    private async _deleteModel(m: ModelRow) {
        try {
            await apiClient.delete(`/llm/models/${m.id}`);
            this._flash('ok', `Model ${m.name} deleted`);
            await Promise.all([this._loadModels(), this._loadSlots(), this._loadGate()]);
        } catch (err) {
            this._flash('error', `Delete model failed: ${err instanceof Error ? err.message : err}`);
        }
    }

    private _chatModels() {
        return this._models.filter(m => m.model_type === 'chat' && m.is_active);
    }

    private _embedModels() {
        return this._models.filter(m => m.model_type === 'embedding' && m.is_active);
    }

    render() {
        return html`
            <aside class="sidebar">
                <div class="sidebar-header">
                    <h1 class="sidebar-title">Models</h1>
                    <p class="sidebar-subtitle">Providers, keys, slots, presets</p>
                </div>
                <div class="tab-list">
                    ${this._tabs.map(tab => html`
                        <button
                            class="tab-item ${this._tab === tab.id ? 'active' : ''}"
                            @click=${() => { this._tab = tab.id; }}
                        >
                            <span class="material-symbols-outlined">${tab.icon}</span>
                            ${tab.label}
                        </button>
                    `)}
                </div>
                <button class="back-btn" @click=${() => this._navigate('/settings')}>
                    <span class="material-symbols-outlined">arrow_back</span> Back to Settings
                </button>
            </aside>

            <main class="main">
                <header class="header">
                    <h2 class="header-title">${this._tabs.find(t => t.id === this._tab)?.label || 'Models'}</h2>
                    <div class="header-actions">
                        ${this._loading ? html`<span class="muted">Loading…</span>` : nothing}
                        <button class="btn" @click=${() => this._loadAll()} ?disabled=${this._loading}>
                            <span class="material-symbols-outlined">refresh</span> Refresh
                        </button>
                    </div>
                </header>
                <div class="content">
                    ${this._renderGate()}
                    ${this._tab === 'providers' ? this._renderProviders() : nothing}
                    ${this._tab === 'slots' ? this._renderSlots() : nothing}
                    ${this._tab === 'presets' ? this._renderPresets() : nothing}
                    ${this._tab === 'models' ? this._renderModels() : nothing}
                </div>
            </main>
            ${this._message
                ? html`<div class="toast ${this._message.kind}">${this._message.text}</div>`
                : nothing}
        `;
    }

    private _renderGate() {
        const gate = this._gate;
        if (!gate || !gate.needs_setup) return nothing;
        return html`
            <div class="gate" role="status">
                <span class="material-symbols-outlined">warning</span>
                <div>
                    <h3>Model setup required</h3>
                    <p>
                        ${gate.message}
                        Configure a provider and API key under <strong>Providers</strong>,
                        add a model in <strong>Model Catalog</strong>, then bind
                        <strong>Chat / Utility / Embedding</strong> slots.
                        Chat stays blocked until at least one model is active.
                    </p>
                    <p class="muted" style="margin-top: 8px;">
                        Active models: ${gate.active_models} ·
                        Chat ${gate.chat_ready ? 'ready' : 'unbound'} ·
                        Utility ${gate.utility_ready ? 'ready' : 'unbound'} ·
                        Embedding ${gate.embedding_ready ? 'ready' : 'unbound'}
                    </p>
                </div>
            </div>
        `;
    }

    private _keyBadge(providerId: string) {
        const keyState = this._keys[providerId];
        const configured = keyState?.configured ?? this._providers.find(p => p.id === providerId)?.has_api_key ?? false;
        return configured
            ? html`<saas-status-badge variant="success" size="sm" dot>key stored</saas-status-badge>`
            : html`<saas-status-badge variant="danger" size="sm" dot>no key</saas-status-badge>`;
    }

    private _modelsForProvider(providerId: string): ModelRow[] {
        return this._models.filter(m => m.provider === providerId);
    }

    private _providerHasKey(providerId: string): boolean {
        const keyState = this._keys[providerId];
        if (keyState?.configured) return true;
        return this._providers.find(p => p.id === providerId)?.has_api_key ?? false;
    }

    private _renderProviders() {
        return html`
            <div class="section">
                <h3 class="section-title">
                    <span class="material-symbols-outlined">dns</span>
                    Providers
                </h3>
                <p class="section-desc">
                    One row per provider: base URL, default model, and the Vault key that every
                    model on that provider uses. Keys are write-only and never echoed back.
                </p>

                <table class="table">
                    <thead>
                        <tr>
                            <th>Provider</th>
                            <th>Base URL</th>
                            <th>Default model</th>
                            <th>Key</th>
                            <th>Models that use this key</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this._providers.map(p => {
                            const keyState = this._keys[p.id] || { configured: false, draft: '' };
                            const dependents = this._modelsForProvider(p.id);
                            const hasKey = keyState.configured || p.has_api_key;
                            return html`
                                <tr>
                                    <td>
                                        <strong>${p.label}</strong>
                                        ${p.is_custom
                                            ? html`<saas-status-badge variant="info" size="sm">custom</saas-status-badge>`
                                            : nothing}
                                        <div class="muted" style="margin-top: 6px;">
                                            <saas-toggle
                                                .checked=${p.enabled}
                                                @change=${() => {
                                                    this._providers = this._providers.map(x =>
                                                        x.id === p.id ? { ...x, enabled: !x.enabled } : x
                                                    );
                                                }}
                                            ></saas-toggle>
                                            ${p.enabled ? 'Enabled' : 'Disabled'}
                                        </div>
                                    </td>
                                    <td>
                                        <input
                                            type="url"
                                            .value=${p.base_url}
                                            placeholder="https://api.example.com/v1"
                                            @input=${(e: Event) => {
                                                const v = (e.target as HTMLInputElement).value;
                                                this._providers = this._providers.map(x =>
                                                    x.id === p.id ? { ...x, base_url: v } : x
                                                );
                                            }}
                                        />
                                    </td>
                                    <td>
                                        <input
                                            type="text"
                                            .value=${p.model_name}
                                            placeholder="model-id"
                                            @input=${(e: Event) => {
                                                const v = (e.target as HTMLInputElement).value;
                                                this._providers = this._providers.map(x =>
                                                    x.id === p.id ? { ...x, model_name: v } : x
                                                );
                                            }}
                                        />
                                    </td>
                                    <td>
                                        ${this._keyBadge(p.id)}
                                        <div style="margin-top: 8px;">
                                            <input
                                                type="password"
                                                autocomplete="new-password"
                                                placeholder=${hasKey ? '••••••••  rotate in Vault' : 'Paste API key'}
                                                .value=${keyState.draft}
                                                @input=${(e: Event) => {
                                                    const v = (e.target as HTMLInputElement).value;
                                                    this._keys = {
                                                        ...this._keys,
                                                        [p.id]: { configured: keyState.configured, draft: v },
                                                    };
                                                }}
                                            />
                                            <div class="key-hint">
                                                Write-only. Stored at Vault secret/agent/api_keys/${p.id}_api_key.
                                            </div>
                                            <div class="row-actions" style="justify-content: flex-start; margin-top: 6px;">
                                                <button
                                                    class="btn primary"
                                                    @click=${() => this._saveKey(p.id)}
                                                    ?disabled=${this._saving || !(this._keys[p.id]?.draft || '').trim()}
                                                >Save key</button>
                                                <button
                                                    class="btn"
                                                    @click=${() => this._deleteKey(p.id)}
                                                    ?disabled=${this._saving || !hasKey}
                                                    title=${hasKey ? 'Delete the stored key from Vault' : 'No key is stored for this provider'}
                                                >Delete</button>
                                            </div>
                                        </div>
                                    </td>
                                    <td>
                                        ${dependents.length === 0
                                            ? html`<span class="muted">No models bound</span>`
                                            : html`
                                                <ul style="margin: 0; padding-left: 16px;">
                                                    ${dependents.map(m => html`
                                                        <li>
                                                            ${m.display_name || m.name}
                                                            ${m.is_active
                                                                ? html`<saas-status-badge variant="success" size="sm">active</saas-status-badge>`
                                                                : html`<saas-status-badge variant="warning" size="sm">inactive</saas-status-badge>`}
                                                        </li>
                                                    `)}
                                                </ul>
                                            `}
                                    </td>
                                    <td>
                                        <div class="row-actions">
                                            <button class="btn" @click=${() => this._saveProvider(p)} ?disabled=${this._saving}>Save</button>
                                            <button
                                                class="btn"
                                                @click=${() => this._testConnection({
                                                    provider: p.id,
                                                    model: p.model_name,
                                                    base_url: p.base_url,
                                                })}
                                                ?disabled=${this._testBusy[p.id] || !hasKey}
                                                title=${hasKey ? 'Test the stored key against this provider' : 'No API key stored for this provider.'}
                                            >
                                                <span class="material-symbols-outlined">network_check</span>
                                                ${this._testBusy[p.id] ? 'Testing…' : 'Test'}
                                            </button>
                                        </div>
                                        ${!hasKey
                                            ? html`<div class="key-hint">No API key stored for this provider.</div>`
                                            : nothing}
                                        ${this._testResult[p.id]
                                            ? html`<div class="key-hint" style="color: ${this._testResult[p.id].ok ? '#047857' : '#b91c1c'}">
                                                ${this._testResult[p.id].ok ? 'OK' : 'Fail'} — ${this._testResult[p.id].detail}
                                            </div>`
                                            : nothing}
                                    </td>
                                </tr>
                            `;
                        })}
                    </tbody>
                </table>
            </div>
        `;
    }

    private _renderSlots() {
        const chat = this._chatModels();
        const emb = this._embedModels();
        return html`
            <div class="section">
                <h3 class="section-title">
                    <span class="material-symbols-outlined">account_tree</span>
                    Chat / Utility / Embedding slots
                </h3>
                <p class="section-desc">
                    Bind three model roles to the active Capsule or tenant defaults (MD-06).
                    Chat maps to Capsule.chat_model when a Capsule is selected.
                </p>

                <div class="form-grid" style="margin-bottom: 20px;">
                    <div>
                        <label class="field-label">Binding scope</label>
                        <select
                            .value=${this._slots.capsule_id || ''}
                            @change=${async (e: Event) => {
                                const v = (e.target as HTMLSelectElement).value || null;
                                this._slots = { ...this._slots, capsule_id: v };
                                await this._loadSlots();
                                await this._loadGate();
                            }}
                        >
                            <option value="">Tenant defaults</option>
                            ${this._capsules.map(c => html`
                                <option value=${c.id} ?selected=${this._slots.capsule_id === c.id}>
                                    Capsule: ${c.name}
                                </option>
                            `)}
                        </select>
                        <div class="key-hint">Scope: ${this._slots.scope}</div>
                    </div>
                </div>

                <div class="slot-grid">
                    <div class="slot-card">
                        <h4><span class="material-symbols-outlined">chat</span> Chat model</h4>
                        <p>Primary conversational engine (Capsule.chat_model).</p>
                        <select
                            .value=${this._slots.chat_model_id || ''}
                            @change=${(e: Event) => {
                                const v = (e.target as HTMLSelectElement).value || null;
                                this._slots = { ...this._slots, chat_model_id: v };
                            }}
                        >
                            <option value="">— unset —</option>
                            ${chat.map(m => html`
                                <option value=${m.id} ?selected=${this._slots.chat_model_id === m.id}>
                                    ${m.provider}/${m.display_name || m.name}
                                </option>
                            `)}
                        </select>
                    </div>
                    <div class="slot-card">
                        <h4><span class="material-symbols-outlined">build</span> Utility model</h4>
                        <p>Lightweight tasks: naming, summarization, routing.</p>
                        <select
                            .value=${this._slots.utility_model_id || ''}
                            @change=${(e: Event) => {
                                const v = (e.target as HTMLSelectElement).value || null;
                                this._slots = { ...this._slots, utility_model_id: v };
                            }}
                        >
                            <option value="">— unset —</option>
                            ${chat.map(m => html`
                                <option value=${m.id} ?selected=${this._slots.utility_model_id === m.id}>
                                    ${m.provider}/${m.display_name || m.name}
                                </option>
                            `)}
                        </select>
                    </div>
                    <div class="slot-card">
                        <h4><span class="material-symbols-outlined">vector_array</span> Embedding model</h4>
                        <p>Memory / knowledge vector generation.</p>
                        <select
                            .value=${this._slots.embedding_model_id || ''}
                            @change=${(e: Event) => {
                                const v = (e.target as HTMLSelectElement).value || null;
                                this._slots = { ...this._slots, embedding_model_id: v };
                            }}
                        >
                            <option value="">— unset —</option>
                            ${emb.map(m => html`
                                <option value=${m.id} ?selected=${this._slots.embedding_model_id === m.id}>
                                    ${m.provider}/${m.display_name || m.name}
                                </option>
                            `)}
                        </select>
                    </div>
                </div>

                <div style="margin-top: 20px; display: flex; gap: 8px;">
                    <button class="btn primary" @click=${this._saveSlots} ?disabled=${this._saving}>
                        <span class="material-symbols-outlined">save</span>
                        ${this._saving ? 'Saving…' : 'Save slots'}
                    </button>
                    <span class="muted" style="align-self: center;">
                        ${chat.length === 0 ? 'No active chat models yet — add one in Model Catalog.' : ''}
                    </span>
                </div>
            </div>
        `;
    }

    private _renderPresets() {
        return html`
            <div class="section">
                <h3 class="section-title">
                    <span class="material-symbols-outlined">bookmark</span>
                    Model presets
                </h3>
                <p class="section-desc">
                    Save and load named Chat / Utility / Embedding bundles.
                    Presets persist through the LLMModelConfig-backed slot API.
                </p>

                <div class="inline-form">
                    <div>
                        <label class="field-label">Preset name</label>
                        <input
                            type="text"
                            .value=${this._presetName}
                            placeholder="e.g. low-cost"
                            @input=${(e: Event) => { this._presetName = (e.target as HTMLInputElement).value; }}
                        />
                    </div>
                    <div style="grid-column: span 2;">
                        <label class="field-label">Notes</label>
                        <input
                            type="text"
                            .value=${this._presetNotes}
                            placeholder="Optional description"
                            @input=${(e: Event) => { this._presetNotes = (e.target as HTMLInputElement).value; }}
                        />
                    </div>
                    <div class="muted" style="padding-bottom: 10px;">
                        Saves current slot selection
                    </div>
                    <button class="btn primary" @click=${this._savePreset} ?disabled=${this._saving || !this._presetName.trim()}>
                        Save preset
                    </button>
                </div>

                ${this._presets.length === 0
                    ? html`<p class="muted" style="margin-top: 16px;">No presets saved yet.</p>`
                    : html`
                        <table class="table" style="margin-top: 20px;">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Chat</th>
                                    <th>Utility</th>
                                    <th>Embedding</th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                ${this._presets.map(p => html`
                                    <tr>
                                        <td>
                                            <strong>${p.name}</strong>
                                            ${p.notes ? html`<div class="muted">${p.notes}</div>` : nothing}
                                        </td>
                                        <td>${this._modelLabel(p.chat_model_id)}</td>
                                        <td>${this._modelLabel(p.utility_model_id)}</td>
                                        <td>${this._modelLabel(p.embedding_model_id)}</td>
                                        <td>
                                            <div class="row-actions">
                                                <button class="btn" @click=${() => this._applyPreset(p)} ?disabled=${this._saving}>Load</button>
                                                <button class="btn" @click=${() => this._deletePreset(p)}>Delete</button>
                                            </div>
                                        </td>
                                    </tr>
                                `)}
                            </tbody>
                        </table>
                    `}
            </div>
        `;
    }

    private _modelLabel(id: string | null): string {
        if (!id) return '—';
        const m = this._models.find(x => x.id === id);
        return m ? `${m.provider}/${m.display_name || m.name}` : id;
    }

    private _renderModels() {
        const n = this._newModel;
        return html`
            <div class="section">
                <h3 class="section-title">
                    <span class="material-symbols-outlined">smart_toy</span>
                    Model catalog (LLMModelConfig)
                </h3>
                <p class="section-desc">
                    Real rows from admin.llm.LLMModelConfig. Each model uses its provider's Vault key —
                    the key badge on every row is that provider's key status, never a per-model secret.
                </p>

                <div class="inline-form">
                    <div>
                        <label class="field-label">Provider</label>
                        <select
                            .value=${n.provider}
                            @change=${(e: Event) => {
                                this._newModel = { ...this._newModel, provider: (e.target as HTMLSelectElement).value };
                            }}
                        >
                            ${this._providers.map(p => html`<option value=${p.id}>${p.label}</option>`)}
                        </select>
                    </div>
                    <div>
                        <label class="field-label">Model name</label>
                        <input
                            type="text"
                            .value=${n.name}
                            placeholder="e.g. gpt-4o-mini"
                            @input=${(e: Event) => {
                                this._newModel = { ...this._newModel, name: (e.target as HTMLInputElement).value };
                            }}
                        />
                    </div>
                    <div>
                        <label class="field-label">Type</label>
                        <select
                            .value=${n.model_type}
                            @change=${(e: Event) => {
                                this._newModel = {
                                    ...this._newModel,
                                    model_type: (e.target as HTMLSelectElement).value as 'chat' | 'embedding',
                                };
                            }}
                        >
                            <option value="chat">Chat</option>
                            <option value="embedding">Embedding</option>
                        </select>
                    </div>
                    <div>
                        <label class="field-label">API base (optional)</label>
                        <input
                            type="url"
                            .value=${n.api_base || ''}
                            placeholder="https://..."
                            @input=${(e: Event) => {
                                this._newModel = { ...this._newModel, api_base: (e.target as HTMLInputElement).value };
                            }}
                        />
                    </div>
                    <button class="btn primary" @click=${this._createModel} ?disabled=${this._saving || !n.name.trim()}>
                        Add model
                    </button>
                </div>

                ${this._models.length === 0
                    ? html`<p class="muted" style="margin-top: 16px;">No models configured.</p>`
                    : html`
                        <table class="table" style="margin-top: 20px;">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Provider / key</th>
                                    <th>Type</th>
                                    <th>Active</th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                ${this._models.map(m => html`
                                    <tr>
                                        <td>
                                            <strong>${m.display_name || m.name}</strong>
                                            <div class="muted">${m.name}</div>
                                        </td>
                                        <td>
                                            <strong>${m.provider}</strong>
                                            <div style="margin-top: 4px;">${this._keyBadge(m.provider)}</div>
                                            <div class="key-hint">Uses the ${m.provider} provider key</div>
                                        </td>
                                        <td style="text-transform: capitalize">${m.model_type}</td>
                                        <td>
                                            <saas-toggle
                                                .checked=${m.is_active}
                                                @change=${() => this._toggleModelActive(m)}
                                            ></saas-toggle>
                                        </td>
                                        <td>
                                            <div class="row-actions">
                                                <button
                                                    class="btn"
                                                    @click=${() => this._testConnection({
                                                        provider: m.provider,
                                                        model_id: m.id,
                                                    })}
                                                    ?disabled=${this._testBusy[m.id] || !this._providerHasKey(m.provider)}
                                                    title=${this._providerHasKey(m.provider)
                                                        ? 'Test this model through its provider key'
                                                        : 'No API key stored for this provider.'}
                                                >
                                                    ${this._testBusy[m.id] ? 'Testing…' : 'Test'}
                                                </button>
                                                <button class="btn" @click=${() => this._deleteModel(m)}>Delete</button>
                                            </div>
                                            ${this._testResult[m.id]
                                                ? html`<div class="key-hint" style="color: ${this._testResult[m.id].ok ? '#047857' : '#b91c1c'}">
                                                    ${this._testResult[m.id].ok ? 'OK' : 'Fail'} — ${this._testResult[m.id].detail}
                                                </div>`
                                                : nothing}
                                        </td>
                                    </tr>
                                `)}
                            </tbody>
                        </table>
                    `}
            </div>
        `;
    }

    private _navigate(route: string) {
        window.dispatchEvent(new CustomEvent('saas-navigate', { detail: { route } }));
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-settings-models': SaasSettingsModels;
    }
}
