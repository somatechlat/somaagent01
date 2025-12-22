/**
 * Eye of God Settings View
 * Per Eye of God UIX Design Section 4.3
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - 4 settings tabs (Agent, External, Connectivity, System)
 * - API integration for persistence
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import '../components/eog-button.js';
import '../components/eog-input.js';
import '../components/eog-toast.js';

export type SettingsTab = 'agent' | 'external' | 'connectivity' | 'system';

export interface SettingsData {
    tab: SettingsTab;
    data: Record<string, unknown>;
    updated_at: string;
    version: number;
}

@customElement('eog-settings')
export class EogSettings extends LitElement {
    static styles = css`
        :host {
            display: block;
            height: 100%;
        }

        .settings-container {
            display: grid;
            grid-template-columns: 240px 1fr;
            height: 100%;
            background: var(--eog-bg-base, #1e293b);
        }

        .sidebar {
            background: var(--eog-surface, rgba(30, 41, 59, 0.85));
            border-right: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.05));
            padding: var(--eog-spacing-md, 16px);
        }

        .sidebar h2 {
            font-size: var(--eog-text-lg, 16px);
            font-weight: 600;
            color: var(--eog-text-main, #e2e8f0);
            margin: 0 0 var(--eog-spacing-md, 16px) 0;
        }

        .nav-list {
            list-style: none;
            padding: 0;
            margin: 0;
            display: flex;
            flex-direction: column;
            gap: var(--eog-spacing-xs, 4px);
        }

        .nav-item {
            padding: var(--eog-spacing-sm, 8px) var(--eog-spacing-md, 16px);
            border-radius: var(--eog-radius-md, 8px);
            color: var(--eog-text-dim, #64748b);
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: var(--eog-spacing-sm, 8px);
        }

        .nav-item:hover {
            background: rgba(255, 255, 255, 0.05);
            color: var(--eog-text-main, #e2e8f0);
        }

        .nav-item.active {
            background: rgba(148, 163, 184, 0.15);
            color: var(--eog-accent, #94a3b8);
        }

        .nav-icon {
            width: 20px;
            text-align: center;
        }

        .content {
            padding: var(--eog-spacing-xl, 32px);
            overflow-y: auto;
        }

        .content-header {
            margin-bottom: var(--eog-spacing-xl, 32px);
        }

        .content-header h1 {
            font-size: var(--eog-text-2xl, 24px);
            font-weight: 600;
            color: var(--eog-text-main, #e2e8f0);
            margin: 0 0 var(--eog-spacing-xs, 4px) 0;
        }

        .content-header p {
            font-size: var(--eog-text-sm, 13px);
            color: var(--eog-text-dim, #64748b);
            margin: 0;
        }

        .section {
            background: var(--eog-surface, rgba(30, 41, 59, 0.85));
            border: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.05));
            border-radius: var(--eog-radius-lg, 12px);
            padding: var(--eog-spacing-lg, 24px);
            margin-bottom: var(--eog-spacing-lg, 24px);
        }

        .section-title {
            font-size: var(--eog-text-base, 14px);
            font-weight: 600;
            color: var(--eog-text-main, #e2e8f0);
            margin: 0 0 var(--eog-spacing-md, 16px) 0;
        }

        .field-group {
            display: flex;
            flex-direction: column;
            gap: var(--eog-spacing-md, 16px);
        }

        .field-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: var(--eog-spacing-md, 16px);
        }

        .actions {
            display: flex;
            gap: var(--eog-spacing-sm, 8px);
            justify-content: flex-end;
            margin-top: var(--eog-spacing-lg, 24px);
        }

        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 200px;
            color: var(--eog-text-dim, #64748b);
        }
    `;

    @property({ type: String }) tab: SettingsTab = 'agent';
    @state() private _settings: Record<SettingsTab, SettingsData | null> = {
        agent: null,
        external: null,
        connectivity: null,
        system: null,
    };
    @state() private _loading = false;
    @state() private _saving = false;

    private _tabs: { id: SettingsTab; label: string; icon: string; description: string }[] = [
        { id: 'agent', label: 'Agent', icon: '🤖', description: 'Configure agent behavior and model settings' },
        { id: 'external', label: 'External', icon: '🔌', description: 'API keys and external service integrations' },
        { id: 'connectivity', label: 'Connectivity', icon: '🌐', description: 'Network and connection settings' },
        { id: 'system', label: 'System', icon: '⚙️', description: 'System configuration and maintenance' },
    ];

    async connectedCallback() {
        super.connectedCallback();
        await this._loadSettings();
    }

    render() {
        const currentTab = this._tabs.find(t => t.id === this.tab)!;

        return html`
            <div class="settings-container">
                <nav class="sidebar">
                    <h2>Settings</h2>
                    <ul class="nav-list" role="tablist">
                        ${this._tabs.map(tab => html`
                            <li 
                                class="nav-item ${this.tab === tab.id ? 'active' : ''}"
                                role="tab"
                                aria-selected=${this.tab === tab.id}
                                @click=${() => this._selectTab(tab.id)}
                            >
                                <span class="nav-icon">${tab.icon}</span>
                                ${tab.label}
                            </li>
                        `)}
                    </ul>
                </nav>

                <main class="content" role="tabpanel">
                    <header class="content-header">
                        <h1>${currentTab.label} Settings</h1>
                        <p>${currentTab.description}</p>
                    </header>

                    ${this._loading ? html`
                        <div class="loading">Loading settings...</div>
                    ` : this._renderTabContent()}

                    <div class="actions">
                        <eog-button @eog-click=${this._resetSettings}>Reset</eog-button>
                        <eog-button 
                            variant="primary" 
                            .loading=${this._saving}
                            @eog-click=${this._saveSettings}
                        >
                            Save Changes
                        </eog-button>
                    </div>
                </main>
            </div>
        `;
    }

    private _renderTabContent() {
        switch (this.tab) {
            case 'agent':
                return this._renderAgentSettings();
            case 'external':
                return this._renderExternalSettings();
            case 'connectivity':
                return this._renderConnectivitySettings();
            case 'system':
                return this._renderSystemSettings();
        }
    }

    private _renderAgentSettings() {
        const data = this._settings.agent?.data || {};
        return html`
            <section class="section">
                <h3 class="section-title">Chat Model</h3>
                <div class="field-row">
                    <eog-input 
                        label="Provider" 
                        .value=${data.chat_provider || 'openai'}
                        @eog-input=${(e: CustomEvent) => this._updateField('agent', 'chat_provider', e.detail.value)}
                    ></eog-input>
                    <eog-input 
                        label="Model" 
                        .value=${data.chat_model || 'gpt-4'}
                        @eog-input=${(e: CustomEvent) => this._updateField('agent', 'chat_model', e.detail.value)}
                    ></eog-input>
                </div>
            </section>

            <section class="section">
                <h3 class="section-title">Memory</h3>
                <div class="field-row">
                    <eog-input 
                        label="Recall Interval (s)" 
                        type="number"
                        .value=${String(data.recall_interval || 30)}
                        @eog-input=${(e: CustomEvent) => this._updateField('agent', 'recall_interval', parseInt(e.detail.value))}
                    ></eog-input>
                    <eog-input 
                        label="Max Memories" 
                        type="number"
                        .value=${String(data.max_memories || 100)}
                        @eog-input=${(e: CustomEvent) => this._updateField('agent', 'max_memories', parseInt(e.detail.value))}
                    ></eog-input>
                </div>
            </section>
        `;
    }

    private _renderExternalSettings() {
        const data = this._settings.external?.data || {};
        return html`
            <section class="section">
                <h3 class="section-title">API Keys</h3>
                <div class="field-group">
                    <eog-input 
                        label="OpenAI API Key" 
                        type="password"
                        .value=${data.openai_key || ''}
                        @eog-input=${(e: CustomEvent) => this._updateField('external', 'openai_key', e.detail.value)}
                    ></eog-input>
                    <eog-input 
                        label="Groq API Key" 
                        type="password"
                        .value=${data.groq_key || ''}
                        @eog-input=${(e: CustomEvent) => this._updateField('external', 'groq_key', e.detail.value)}
                    ></eog-input>
                </div>
            </section>
        `;
    }

    private _renderConnectivitySettings() {
        const data = this._settings.connectivity?.data || {};
        return html`
            <section class="section">
                <h3 class="section-title">Network</h3>
                <div class="field-group">
                    <eog-input 
                        label="API Base URL" 
                        .value=${data.api_base_url || '/api/v2'}
                        @eog-input=${(e: CustomEvent) => this._updateField('connectivity', 'api_base_url', e.detail.value)}
                    ></eog-input>
                    <eog-input 
                        label="WebSocket URL" 
                        .value=${data.ws_url || '/ws/v2/events'}
                        @eog-input=${(e: CustomEvent) => this._updateField('connectivity', 'ws_url', e.detail.value)}
                    ></eog-input>
                </div>
            </section>
        `;
    }

    private _renderSystemSettings() {
        const data = this._settings.system?.data || {};
        return html`
            <section class="section">
                <h3 class="section-title">Logging</h3>
                <div class="field-group">
                    <eog-input 
                        label="Log Level" 
                        .value=${data.log_level || 'INFO'}
                        @eog-input=${(e: CustomEvent) => this._updateField('system', 'log_level', e.detail.value)}
                    ></eog-input>
                </div>
            </section>
        `;
    }

    private _selectTab(tab: SettingsTab) {
        this.tab = tab;
        this.dispatchEvent(new CustomEvent('tab-change', { detail: { tab } }));
    }

    private async _loadSettings() {
        this._loading = true;
        try {
            const response = await apiClient.get<SettingsData[]>('/settings');
            for (const setting of response) {
                this._settings[setting.tab] = setting;
            }
        } catch (error) {
            console.error('Failed to load settings:', error);
        } finally {
            this._loading = false;
        }
    }

    private _updateField(tab: SettingsTab, field: string, value: unknown) {
        const current = this._settings[tab] || { tab, data: {}, updated_at: '', version: 1 };
        this._settings = {
            ...this._settings,
            [tab]: {
                ...current,
                data: { ...current.data, [field]: value },
            },
        };
    }

    private async _saveSettings() {
        this._saving = true;
        try {
            const current = this._settings[this.tab];
            if (current) {
                await apiClient.put(`/settings/${this.tab}`, {
                    tab: this.tab,
                    data: current.data,
                    version: current.version,
                });
            }

            this.dispatchEvent(new CustomEvent('settings-saved', { detail: { tab: this.tab } }));
        } catch (error) {
            console.error('Failed to save settings:', error);
        } finally {
            this._saving = false;
        }
    }

    private async _resetSettings() {
        await this._loadSettings();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-settings': EogSettings;
    }
}
