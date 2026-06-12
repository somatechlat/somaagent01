/**
 * SomaAgent SaaS — Agent Settings Screen
 *
 * Route: /agents/:id/settings
 * Edits core agent fields:
 * - name
 * - description
 * - model
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient, ApiError } from '../services/api-client.js';

interface Agent {
    agent_id: string;
    name: string;
    description?: string;
    model: string;
    status: string;
}

const MODEL_OPTIONS = [
    { value: 'gpt-4o', label: 'GPT-4o' },
    { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
    { value: 'claude-3-opus', label: 'Claude 3 Opus' },
    { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' },
    { value: 'gpt-4', label: 'GPT-4' },
];

@customElement('saas-agent-settings')
export class SaasAgentSettings extends LitElement {
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
            letter-spacing: normal;
            text-transform: none;
            display: inline-block;
            white-space: nowrap;
            word-wrap: normal;
            direction: ltr;
            -webkit-font-feature-settings: 'liga';
            -webkit-font-smoothing: antialiased;
        }

        .sidebar {
            width: var(--saas-sidebar-width, 260px);
            flex-shrink: 0;
        }

        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .header {
            padding: 16px 24px;
            background: var(--saas-bg-card, #ffffff);
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header-title {
            font-size: 18px;
            font-weight: 600;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .header-subtitle {
            font-size: 13px;
            color: var(--saas-text-secondary, #666);
            margin: 4px 0 0 0;
        }

        .content {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
        }

        .form {
            max-width: 640px;
            margin: 0 auto;
        }

        .section {
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 20px;
        }

        .section-header {
            padding: 16px 20px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            font-weight: 600;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .section-body {
            padding: 24px 20px;
        }

        .field {
            margin-bottom: 20px;
        }

        .field:last-child {
            margin-bottom: 0;
        }

        .field-label {
            display: block;
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 8px;
        }

        .field-hint {
            font-size: 12px;
            color: var(--saas-text-secondary, #666);
            font-weight: 400;
            margin-left: 6px;
        }

        .form-input,
        .form-select,
        .form-textarea {
            width: 100%;
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            font-size: 14px;
            background: var(--saas-bg-card, #ffffff);
            color: var(--saas-text-primary, #1a1a1a);
            font-family: inherit;
            outline: none;
            transition: border-color 0.15s ease;
        }

        .form-input:focus,
        .form-select:focus,
        .form-textarea:focus {
            border-color: var(--saas-text-primary, #1a1a1a);
        }

        .form-textarea {
            resize: vertical;
            min-height: 100px;
        }

        .actions {
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 12px;
            padding-top: 8px;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            background: var(--saas-bg-card, #ffffff);
            color: var(--saas-text-primary, #1a1a1a);
            transition: all 0.1s ease;
        }

        .btn:hover:not(:disabled) { background: var(--saas-bg-hover, #fafafa); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }

        .btn.primary {
            background: #1a1a1a;
            color: #ffffff;
            border-color: #1a1a1a;
        }

        .btn.primary:hover:not(:disabled) { background: #333333; }

        .btn .material-symbols-outlined { font-size: 18px; }

        .status {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
        }

        .status.success { color: var(--saas-status-success, #22c55e); }
        .status.error { color: var(--saas-status-danger, #ef4444); }

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
            color: var(--saas-text-secondary, #666);
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .error-message {
            color: var(--saas-status-danger, #ef4444);
            margin: 12px 0 20px;
            max-width: 480px;
        }
    `;

    @state() private _agentId = '';
    @state() private _agent: Agent | null = null;
    @state() private _name = '';
    @state() private _description = '';
    @state() private _model = '';
    @state() private _loading = true;
    @state() private _loadError = '';
    @state() private _saving = false;
    @state() private _saveStatus = '';
    @state() private _saveStatusType: 'success' | 'error' | '' = '';

    connectedCallback() {
        super.connectedCallback();
        this._agentId = this._parseAgentId();
        if (this._agentId) {
            this._loadAgent();
        } else {
            this._loading = false;
            this._loadError = 'Invalid agent ID in URL';
        }
    }

    private _parseAgentId(): string {
        const path = window.location.pathname;
        const match = path.match(/^\/agents\/([^/]+)\/settings$/);
        return match?.[1] ?? '';
    }

    private async _loadAgent() {
        this._loading = true;
        this._loadError = '';
        try {
            const data = await apiClient.get<Agent>(`/agents/${this._agentId}`);
            this._agent = data;
            this._name = data.name;
            this._description = data.description ?? '';
            this._model = data.model;
        } catch (e) {
            const message = e instanceof ApiError ? e.message : 'Failed to load agent settings';
            this._loadError = message;
            console.error('[saas-agent-settings] load error:', e);
        } finally {
            this._loading = false;
        }
    }

    private async _save() {
        this._saving = true;
        this._saveStatus = '';
        this._saveStatusType = '';

        try {
            await apiClient.patch(`/agents/${this._agentId}`, {
                name: this._name,
                description: this._description,
                model: this._model,
            });
            this._saveStatus = 'Settings saved successfully';
            this._saveStatusType = 'success';
            if (this._agent) {
                this._agent = {
                    ...this._agent,
                    name: this._name,
                    description: this._description,
                    model: this._model,
                };
            }
        } catch (e) {
            const message = e instanceof ApiError ? e.message : 'Failed to save agent settings';
            this._saveStatus = message;
            this._saveStatusType = 'error';
            console.error('[saas-agent-settings] save error:', e);
        } finally {
            this._saving = false;
        }
    }

    private _reset() {
        if (!this._agent) return;
        this._name = this._agent.name;
        this._description = this._agent.description ?? '';
        this._model = this._agent.model;
        this._saveStatus = '';
        this._saveStatusType = '';
    }

    render() {
        if (this._loading) {
            return html`
                <div class="loading">
                    <span class="material-symbols-outlined loading-icon">sync</span>
                    <p>Loading agent settings...</p>
                </div>
            `;
        }

        if (this._loadError || !this._agent) {
            return html`
                <div class="error">
                    <span class="material-symbols-outlined" style="font-size: 40px; color: var(--saas-status-danger, #ef4444);">error</span>
                    <h2>Unable to load agent</h2>
                    <p class="error-message">${this._loadError}</p>
                    <button class="btn" @click=${() => this._loadAgent()}>
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
                            <span class="material-symbols-outlined">settings</span>
                            Agent Settings
                        </h1>
                        <p class="header-subtitle">${this._agent.name} · Agent ${this._agentId.slice(0, 8)}</p>
                    </div>
                </header>

                <div class="content">
                    <div class="form">
                        <div class="section">
                            <div class="section-header">
                                <span class="material-symbols-outlined">tune</span>
                                General
                            </div>
                            <div class="section-body">
                                <div class="field">
                                    <label class="field-label">
                                        Name
                                        <span class="field-hint">Display name for this agent</span>
                                    </label>
                                    <input
                                        type="text"
                                        class="form-input"
                                        .value=${this._name}
                                        @input=${(e: Event) => { this._name = (e.target as HTMLInputElement).value; }}
                                    />
                                </div>

                                <div class="field">
                                    <label class="field-label">
                                        Description
                                        <span class="field-hint">Purpose or notes for this agent</span>
                                    </label>
                                    <textarea
                                        class="form-textarea"
                                        .value=${this._description}
                                        @input=${(e: Event) => { this._description = (e.target as HTMLTextAreaElement).value; }}
                                    ></textarea>
                                </div>

                                <div class="field">
                                    <label class="field-label">
                                        Model
                                        <span class="field-hint">LLM used by this agent</span>
                                    </label>
                                    <select
                                        class="form-select"
                                        .value=${this._model}
                                        @change=${(e: Event) => { this._model = (e.target as HTMLSelectElement).value; }}
                                    >
                                        ${MODEL_OPTIONS.map(option => html`
                                            <option value="${option.value}">${option.label}</option>
                                        `)}
                                    </select>
                                </div>
                            </div>
                        </div>

                        <div class="actions">
                            ${this._saveStatus
                                ? html`<div class="status ${this._saveStatusType}">
                                      <span class="material-symbols-outlined">
                                          ${this._saveStatusType === 'success' ? 'check_circle' : 'error'}
                                      </span>
                                      ${this._saveStatus}
                                  </div>`
                                : ''}
                            <button class="btn" @click=${this._reset} ?disabled=${this._saving}>
                                <span class="material-symbols-outlined">refresh</span>
                                Reset
                            </button>
                            <button class="btn primary" @click=${this._save} ?disabled=${this._saving}>
                                <span class="material-symbols-outlined">save</span>
                                ${this._saving ? 'Saving...' : 'Save Settings'}
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
        'saas-agent-settings': SaasAgentSettings;
    }
}
