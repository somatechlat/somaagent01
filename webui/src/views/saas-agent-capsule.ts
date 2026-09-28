/**
 * Agent Capsule Configuration Screen
 *
 * Route: /agents/:id/capsule
 * Edits the agent's primary Capsule identity fields:
 * - system_prompt
 * - description
 * - personality_traits (JSON)
 * - neuromodulator_baseline (JSON)
 * - learning_config (JSON)
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient, ApiError } from '../services/api-client.js';

interface CapsuleConfig {
    agent_id: string;
    capsule_id: string;
    name: string;
    description?: string;
    status: string;
    system_prompt: string;
    personality_traits: Record<string, unknown>;
    neuromodulator_baseline: Record<string, unknown>;
    learning_config: Record<string, unknown>;
}

interface CapsuleUpdateResult {
    agent_id: string;
    capsule_id: string;
    updated: boolean;
}

@customElement('saas-agent-capsule')
export class SaasAgentCapsule extends LitElement {
    static styles = css`
        :host {
            display: flex;
            height: 100vh;
            background: var(--aaas-bg-void, #0f172a);
            font-family: var(--aaas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
            color: var(--aaas-text-main, #e2e8f0);
        }

        * { box-sizing: border-box; }

        .sidebar {
            width: var(--aaas-sidebar-width, 260px);
            flex-shrink: 0;
        }

        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .header {
            height: var(--aaas-header-height, 64px);
            padding: 0 28px;
            border-bottom: 1px solid var(--aaas-border-color, rgba(255, 255, 255, 0.05));
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header-title {
            font-size: var(--aaas-text-xl, 18px);
            font-weight: 600;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .header-subtitle {
            font-size: var(--aaas-text-xs, 11px);
            color: var(--aaas-text-dim, #64748b);
            margin: 2px 0 0 0;
        }

        .header-meta {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .status-badge {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 4px 8px;
            border-radius: var(--aaas-radius-full, 9999px);
            background: var(--aaas-surface, rgba(30, 41, 59, 0.85));
            border: 1px solid var(--aaas-border-color, rgba(255, 255, 255, 0.05));
        }

        .content {
            flex: 1;
            overflow-y: auto;
            padding: 28px;
        }

        .form {
            max-width: 880px;
            margin: 0 auto;
        }

        .section {
            background: var(--aaas-surface, rgba(30, 41, 59, 0.85));
            border: 1px solid var(--aaas-border-color, rgba(255, 255, 255, 0.05));
            border-radius: var(--aaas-radius-lg, 12px);
            margin-bottom: 20px;
            overflow: hidden;
        }

        .section-header {
            padding: 16px 20px;
            border-bottom: 1px solid var(--aaas-border-color, rgba(255, 255, 255, 0.05));
            font-weight: 600;
            font-size: var(--aaas-text-sm, 13px);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .section-body {
            padding: 20px;
        }

        .field {
            margin-bottom: 20px;
        }

        .field:last-child {
            margin-bottom: 0;
        }

        .field-label {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: var(--aaas-text-sm, 13px);
            color: var(--aaas-text-bright, #f8fafc);
            margin-bottom: 8px;
        }

        .field-hint {
            font-size: 11px;
            color: var(--aaas-text-dim, #64748b);
            font-weight: 400;
        }

        textarea,
        input[type="text"] {
            width: 100%;
            background: var(--aaas-bg-void, #0f172a);
            border: 1px solid var(--aaas-border-color, rgba(255, 255, 255, 0.05));
            border-radius: var(--aaas-radius-md, 8px);
            padding: 12px;
            color: var(--aaas-text-main, #e2e8f0);
            font-size: var(--aaas-text-sm, 13px);
            font-family: inherit;
            outline: none;
            resize: vertical;
            transition: border-color 0.15s ease;
        }

        textarea:focus,
        input[type="text"]:focus {
            border-color: var(--aaas-border-hover, rgba(255, 255, 255, 0.1));
        }

        textarea.json-field {
            font-family: var(--aaas-font-mono, 'JetBrains Mono', 'Fira Code', Consolas, monospace);
            min-height: 140px;
        }

        textarea.system-prompt {
            min-height: 180px;
        }

        textarea.description {
            min-height: 100px;
        }

        .field.invalid textarea,
        .field.invalid input {
            border-color: var(--aaas-danger, #ef4444);
        }

        .field-error {
            font-size: 11px;
            color: var(--aaas-danger, #ef4444);
            margin-top: 6px;
        }

        .actions {
            display: flex;
            justify-content: flex-end;
            gap: 12px;
            padding-top: 8px;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 10px 18px;
            border-radius: var(--aaas-radius-md, 8px);
            font-size: var(--aaas-text-sm, 13px);
            font-weight: 600;
            cursor: pointer;
            border: 1px solid transparent;
            transition: all 0.15s ease;
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .btn-primary {
            background: var(--aaas-text-bright, #f8fafc);
            color: var(--aaas-bg-void, #0f172a);
        }

        .btn-primary:hover:not(:disabled) {
            background: var(--aaas-accent-hover, #cbd5e1);
        }

        .btn-secondary {
            background: transparent;
            color: var(--aaas-text-main, #e2e8f0);
            border-color: var(--aaas-border-color, rgba(255, 255, 255, 0.05));
        }

        .btn-secondary:hover:not(:disabled) {
            background: var(--aaas-surface-hover, rgba(51, 65, 85, 0.9));
        }

        .loading,
        .error {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            flex: 1;
            text-align: center;
            padding: 40px;
        }

        .loading-icon {
            font-size: 32px;
            color: var(--aaas-text-dim, #64748b);
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .error-message {
            color: var(--aaas-danger, #ef4444);
            margin: 12px 0 20px;
            max-width: 480px;
        }

        .save-status {
            font-size: var(--aaas-text-sm, 13px);
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .save-status.success {
            color: var(--aaas-success, #22c55e);
        }

        .save-status.error {
            color: var(--aaas-danger, #ef4444);
        }
    `;

    @state() private _agentId = '';
    @state() private _capsule: CapsuleConfig | null = null;
    @state() private _loading = true;
    @state() private _loadError = '';
    @state() private _saving = false;
    @state() private _saveStatus = '';
    @state() private _saveStatusType: 'success' | 'error' | '' = '';
    @state() private _fieldErrors: Record<string, string> = {};

    private _rawJson: Record<string, string> = {
        personality_traits: '',
        neuromodulator_baseline: '',
        learning_config: '',
    };

    connectedCallback() {
        super.connectedCallback();
        this._agentId = this._parseAgentId();
        if (this._agentId) {
            this._loadCapsule();
        } else {
            this._loading = false;
            this._loadError = 'Invalid agent ID in URL';
        }
    }

    private _parseAgentId(): string {
        const path = window.location.pathname;
        const match = path.match(/^\/agents\/([^/]+)\/capsule$/);
        return match?.[1] ?? '';
    }

    private async _loadCapsule() {
        this._loading = true;
        this._loadError = '';
        try {
            const data = await apiClient.get<CapsuleConfig>(`/agents/${this._agentId}/capsule`);
            this._capsule = data;
            this._rawJson = {
                personality_traits: this._prettyJson(data.personality_traits),
                neuromodulator_baseline: this._prettyJson(data.neuromodulator_baseline),
                learning_config: this._prettyJson(data.learning_config),
            };
        } catch (e) {
            const message = e instanceof ApiError ? e.message : 'Failed to load capsule configuration';
            this._loadError = message;
            console.error('[saas-agent-capsule] load error:', e);
        } finally {
            this._loading = false;
        }
    }

    private _prettyJson(value: unknown): string {
        try {
            return JSON.stringify(value ?? {}, null, 2);
        } catch {
            return '{}';
        }
    }

    private _parseJson(field: string, raw: string): Record<string, unknown> | null {
        try {
            const parsed = JSON.parse(raw);
            if (parsed !== null && typeof parsed === 'object' && !Array.isArray(parsed)) {
                return parsed as Record<string, unknown>;
            }
            this._fieldErrors = { ...this._fieldErrors, [field]: 'Must be a JSON object' };
            return null;
        } catch {
            this._fieldErrors = { ...this._fieldErrors, [field]: 'Invalid JSON' };
            return null;
        }
    }

    private _updateTextField(field: keyof CapsuleConfig, value: string) {
        if (!this._capsule) return;
        this._capsule = { ...this._capsule, [field]: value };
    }

    private _updateJsonField(field: keyof typeof this._rawJson, value: string) {
        this._rawJson = { ...this._rawJson, [field]: value };
        const { [field]: _, ...rest } = this._fieldErrors;
        this._fieldErrors = rest;
    }

    private async _save() {
        if (!this._capsule) return;

        this._fieldErrors = {};
        const personality_traits = this._parseJson('personality_traits', this._rawJson.personality_traits);
        const neuromodulator_baseline = this._parseJson('neuromodulator_baseline', this._rawJson.neuromodulator_baseline);
        const learning_config = this._parseJson('learning_config', this._rawJson.learning_config);

        if (Object.keys(this._fieldErrors).length > 0) {
            this._saveStatus = 'Please fix JSON errors before saving';
            this._saveStatusType = 'error';
            return;
        }

        this._saving = true;
        this._saveStatus = '';
        this._saveStatusType = '';

        try {
            const payload = {
                name: this._capsule.name,
                description: this._capsule.description,
                system_prompt: this._capsule.system_prompt,
                personality_traits,
                neuromodulator_baseline,
                learning_config,
            };
            await apiClient.patch<CapsuleUpdateResult>(`/agents/${this._agentId}/capsule`, payload);
            this._saveStatus = 'Capsule saved successfully';
            this._saveStatusType = 'success';
        } catch (e) {
            const message = e instanceof ApiError ? e.message : 'Failed to save capsule configuration';
            this._saveStatus = message;
            this._saveStatusType = 'error';
            console.error('[saas-agent-capsule] save error:', e);
        } finally {
            this._saving = false;
        }
    }

    private _renderField(
        label: string,
        hint: string,
        fieldKey: keyof CapsuleConfig,
        value: string,
        textareaClass: string,
        onInput: (value: string) => void,
    ) {
        const error = this._fieldErrors[fieldKey as string] ?? '';
        return html`
            <div class="field ${error ? 'invalid' : ''}">
                <label class="field-label">
                    <span>${label}</span>
                    <span class="field-hint">${hint}</span>
                </label>
                <textarea
                    class="${textareaClass}"
                    .value=${value}
                    @input=${(e: Event) => onInput((e.target as HTMLTextAreaElement).value)}
                ></textarea>
                ${error ? html`<div class="field-error">${error}</div>` : ''}
            </div>
        `;
    }

    private _renderJsonField(
        label: string,
        hint: string,
        fieldKey: keyof typeof this._rawJson,
    ) {
        const error = this._fieldErrors[fieldKey] ?? '';
        return html`
            <div class="field ${error ? 'invalid' : ''}">
                <label class="field-label">
                    <span>${label}</span>
                    <span class="field-hint">${hint}</span>
                </label>
                <textarea
                    class="json-field"
                    .value=${this._rawJson[fieldKey]}
                    @input=${(e: Event) => this._updateJsonField(fieldKey, (e.target as HTMLTextAreaElement).value)}
                ></textarea>
                ${error ? html`<div class="field-error">${error}</div>` : ''}
            </div>
        `;
    }

    render() {
        if (this._loading) {
            return html`
                <div class="loading">
                    <span class="material-symbols-outlined loading-icon">sync</span>
                    <p>Loading capsule configuration...</p>
                </div>
            `;
        }

        if (this._loadError || !this._capsule) {
            return html`
                <div class="error">
                    <span class="material-symbols-outlined" style="font-size: 40px; color: var(--aaas-danger)">error</span>
                    <h2>Unable to load capsule</h2>
                    <p class="error-message">${this._loadError}</p>
                    <button class="btn btn-secondary" @click=${() => this._loadCapsule()}>
                        <span class="material-symbols-outlined">refresh</span>
                        Retry
                    </button>
                </div>
            `;
        }

        return html`
            <aside class="sidebar">
                <saas-sidebar active-route="/admin/agents"></saas-sidebar>
            </aside>

            <main class="main">
                <header class="header">
                    <div>
                        <h1 class="header-title">
                            <span class="material-symbols-outlined">workspace_premium</span>
                            Capsule Configuration
                        </h1>
                        <p class="header-subtitle">${this._capsule.name} · Agent ${this._agentId.slice(0, 8)}</p>
                    </div>
                    <div class="header-meta">
                        <span class="status-badge">${this._capsule.status}</span>
                    </div>
                </header>

                <div class="content">
                    <div class="form">
                        <div class="section">
                            <div class="section-header">
                                <span class="material-symbols-outlined">person</span>
                                Identity
                            </div>
                            <div class="section-body">
                                ${this._renderField(
                                    'System Prompt',
                                    'Core cognitive instruction set',
                                    'system_prompt',
                                    this._capsule.system_prompt,
                                    'system-prompt',
                                    (v) => this._updateTextField('system_prompt', v)
                                )}
                                ${this._renderField(
                                    'Description',
                                    'Purpose or notes for this capsule',
                                    'description',
                                    this._capsule.description ?? '',
                                    'description',
                                    (v) => this._updateTextField('description', v)
                                )}
                            </div>
                        </div>

                        <div class="section">
                            <div class="section-header">
                                <span class="material-symbols-outlined">psychology</span>
                                Personality & Neuromodulators
                            </div>
                            <div class="section-body">
                                ${this._renderJsonField(
                                    'Personality Traits',
                                    'Big Five traits as a JSON object, e.g. {"openness": 0.8}',
                                    'personality_traits'
                                )}
                                ${this._renderJsonField(
                                    'Neuromodulator Baseline',
                                    'Baseline chemical state as a JSON object, e.g. {"dopamine": 0.5}',
                                    'neuromodulator_baseline'
                                )}
                            </div>
                        </div>

                        <div class="section">
                            <div class="section-header">
                                <span class="material-symbols-outlined">school</span>
                                Learning
                            </div>
                            <div class="section-body">
                                ${this._renderJsonField(
                                    'Learning Config',
                                    'GMD hyperparameters and reward thresholds as a JSON object',
                                    'learning_config'
                                )}
                            </div>
                        </div>

                        <div class="actions">
                            ${this._saveStatus
                                ? html`<div class="save-status ${this._saveStatusType}">
                                      <span class="material-symbols-outlined">
                                          ${this._saveStatusType === 'success' ? 'check_circle' : 'error'}
                                      </span>
                                      ${this._saveStatus}
                                  </div>`
                                : ''}
                            <button class="btn btn-secondary" @click=${() => this._loadCapsule()} ?disabled=${this._saving}>
                                <span class="material-symbols-outlined">refresh</span>
                                Reset
                            </button>
                            <button class="btn btn-primary" @click=${() => this._save()} ?disabled=${this._saving}>
                                <span class="material-symbols-outlined">save</span>
                                ${this._saving ? 'Saving...' : 'Save Capsule'}
                            </button>
                        </div>
                    </div>
                </div>
            </main>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-agent-capsule': SaasAgentCapsule;
    }
}
