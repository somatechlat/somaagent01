/**
 * Eye of God Cognitive View
 * Per Eye of God UIX Design Section 2.2
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - LLM parameter tuning
 * - Prompt template management
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import '../components/eog-card.js';
import '../components/eog-slider.js';
import '../components/eog-toggle.js';
import '../components/eog-tabs.js';
import '../components/eog-input.js';

interface CognitiveConfig {
    temperature: number;
    top_p: number;
    top_k: number;
    max_tokens: number;
    presence_penalty: number;
    frequency_penalty: number;
    stop_sequences: string[];
    system_prompt: string | null;
}

interface PromptTemplate {
    id: string;
    name: string;
    description: string;
    template: string;
    variables: string[];
    category: string;
}

@customElement('eog-cognitive')
export class EogCognitive extends LitElement {
    static styles = css`
        :host {
            display: block;
            padding: var(--eog-spacing-lg, 24px);
            height: 100%;
            overflow-y: auto;
        }

        .cognitive-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--eog-spacing-xl, 32px);
        }

        h1 {
            font-size: var(--eog-text-2xl, 24px);
            font-weight: 600;
            color: var(--eog-text-main, #e2e8f0);
            margin: 0;
        }

        .config-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: var(--eog-spacing-lg, 24px);
            margin-bottom: var(--eog-spacing-xl, 32px);
        }

        .param-card {
            padding: var(--eog-spacing-lg, 24px);
        }

        .param-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--eog-spacing-md, 16px);
        }

        .param-title {
            font-size: var(--eog-text-base, 14px);
            font-weight: 600;
            color: var(--eog-text-main, #e2e8f0);
        }

        .param-value {
            font-size: var(--eog-text-sm, 13px);
            color: var(--eog-accent, #94a3b8);
            font-weight: 600;
        }

        .param-description {
            font-size: var(--eog-text-xs, 11px);
            color: var(--eog-text-dim, #64748b);
            margin-top: var(--eog-spacing-sm, 8px);
        }

        .templates-section {
            margin-top: var(--eog-spacing-xl, 32px);
        }

        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--eog-spacing-lg, 24px);
        }

        h2 {
            font-size: var(--eog-text-lg, 16px);
            font-weight: 600;
            color: var(--eog-text-main, #e2e8f0);
            margin: 0;
        }

        .templates-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: var(--eog-spacing-md, 16px);
        }

        .template-card {
            cursor: pointer;
        }

        .template-name {
            font-weight: 600;
            color: var(--eog-text-main, #e2e8f0);
            margin-bottom: var(--eog-spacing-xs, 4px);
        }

        .template-category {
            font-size: var(--eog-text-xs, 11px);
            color: var(--eog-accent, #94a3b8);
            text-transform: uppercase;
            margin-bottom: var(--eog-spacing-sm, 8px);
        }

        .template-preview {
            font-size: var(--eog-text-sm, 13px);
            color: var(--eog-text-dim, #64748b);
            line-height: 1.5;
            max-height: 60px;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .template-variables {
            display: flex;
            flex-wrap: wrap;
            gap: var(--eog-spacing-xs, 4px);
            margin-top: var(--eog-spacing-sm, 8px);
        }

        .variable-tag {
            font-size: var(--eog-text-xs, 11px);
            padding: 2px 6px;
            border-radius: var(--eog-radius-sm, 4px);
            background: rgba(148, 163, 184, 0.1);
            color: var(--eog-accent, #94a3b8);
        }

        .system-prompt-section {
            margin-top: var(--eog-spacing-xl, 32px);
        }

        .system-prompt-textarea {
            width: 100%;
            min-height: 150px;
            padding: var(--eog-spacing-md, 16px);
            border-radius: var(--eog-radius-md, 8px);
            border: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.1));
            background: var(--eog-bg-base, #1e293b);
            color: var(--eog-text-main, #e2e8f0);
            font-family: monospace;
            font-size: var(--eog-text-sm, 13px);
            resize: vertical;
        }

        .actions {
            display: flex;
            gap: var(--eog-spacing-sm, 8px);
            margin-top: var(--eog-spacing-md, 16px);
        }
    `;

    @state() private _config: CognitiveConfig = {
        temperature: 0.7,
        top_p: 0.95,
        top_k: 40,
        max_tokens: 4096,
        presence_penalty: 0.0,
        frequency_penalty: 0.0,
        stop_sequences: [],
        system_prompt: null,
    };

    @state() private _templates: PromptTemplate[] = [];
    @state() private _isLoading = false;
    @state() private _isSaving = false;

    private _tabs = [
        { id: 'parameters', label: 'Parameters' },
        { id: 'templates', label: 'Templates' },
        { id: 'system', label: 'System Prompt' },
    ];

    @state() private _activeTab = 'parameters';

    connectedCallback() {
        super.connectedCallback();
        this._loadConfig();
        this._loadTemplates();
    }

    render() {
        return html`
            <header class="cognitive-header">
                <h1>⚙️ Cognitive Settings</h1>
            </header>

            <eog-tabs
                .tabs=${this._tabs}
                .selected=${this._activeTab}
                @eog-tab-change=${(e: CustomEvent) => this._activeTab = e.detail.id}
            >
                <div slot="parameters">
                    ${this._renderParameters()}
                </div>
                <div slot="templates">
                    ${this._renderTemplates()}
                </div>
                <div slot="system">
                    ${this._renderSystemPrompt()}
                </div>
            </eog-tabs>
        `;
    }

    private _renderParameters() {
        return html`
            <div class="config-grid">
                <eog-card class="param-card">
                    <div class="param-header">
                        <span class="param-title">Temperature</span>
                        <span class="param-value">${this._config.temperature}</span>
                    </div>
                    <eog-slider
                        .value=${this._config.temperature}
                        .min=${0}
                        .max=${2}
                        .step=${0.1}
                        @eog-change=${(e: CustomEvent) => this._updateConfig('temperature', e.detail.value)}
                    ></eog-slider>
                    <p class="param-description">Controls randomness. Lower = focused, Higher = creative</p>
                </eog-card>

                <eog-card class="param-card">
                    <div class="param-header">
                        <span class="param-title">Top P (Nucleus)</span>
                        <span class="param-value">${this._config.top_p}</span>
                    </div>
                    <eog-slider
                        .value=${this._config.top_p}
                        .min=${0}
                        .max=${1}
                        .step=${0.05}
                        @eog-change=${(e: CustomEvent) => this._updateConfig('top_p', e.detail.value)}
                    ></eog-slider>
                    <p class="param-description">Nucleus sampling threshold</p>
                </eog-card>

                <eog-card class="param-card">
                    <div class="param-header">
                        <span class="param-title">Max Tokens</span>
                        <span class="param-value">${this._config.max_tokens}</span>
                    </div>
                    <eog-slider
                        .value=${this._config.max_tokens}
                        .min=${256}
                        .max=${32000}
                        .step=${256}
                        @eog-change=${(e: CustomEvent) => this._updateConfig('max_tokens', e.detail.value)}
                    ></eog-slider>
                    <p class="param-description">Maximum tokens to generate</p>
                </eog-card>

                <eog-card class="param-card">
                    <div class="param-header">
                        <span class="param-title">Presence Penalty</span>
                        <span class="param-value">${this._config.presence_penalty}</span>
                    </div>
                    <eog-slider
                        .value=${this._config.presence_penalty}
                        .min=${-2}
                        .max=${2}
                        .step=${0.1}
                        @eog-change=${(e: CustomEvent) => this._updateConfig('presence_penalty', e.detail.value)}
                    ></eog-slider>
                    <p class="param-description">Penalty for tokens already in context</p>
                </eog-card>

                <eog-card class="param-card">
                    <div class="param-header">
                        <span class="param-title">Frequency Penalty</span>
                        <span class="param-value">${this._config.frequency_penalty}</span>
                    </div>
                    <eog-slider
                        .value=${this._config.frequency_penalty}
                        .min=${-2}
                        .max=${2}
                        .step=${0.1}
                        @eog-change=${(e: CustomEvent) => this._updateConfig('frequency_penalty', e.detail.value)}
                    ></eog-slider>
                    <p class="param-description">Penalty for frequently used tokens</p>
                </eog-card>
            </div>

            <div class="actions">
                <eog-button @click=${this._saveConfig} ?loading=${this._isSaving}>Save Changes</eog-button>
                <eog-button variant="secondary" @click=${this._resetConfig}>Reset to Defaults</eog-button>
            </div>
        `;
    }

    private _renderTemplates() {
        return html`
            <div class="section-header">
                <h2>Prompt Templates</h2>
                <eog-button @click=${this._createTemplate}>+ New Template</eog-button>
            </div>

            <div class="templates-grid">
                ${this._templates.map(template => html`
                    <eog-card class="template-card" clickable @eog-click=${() => this._editTemplate(template)}>
                        <div class="template-category">${template.category}</div>
                        <div class="template-name">${template.name}</div>
                        <div class="template-preview">${template.template.slice(0, 100)}...</div>
                        <div class="template-variables">
                            ${template.variables.map(v => html`
                                <span class="variable-tag">{{${v}}}</span>
                            `)}
                        </div>
                    </eog-card>
                `)}
            </div>
        `;
    }

    private _renderSystemPrompt() {
        return html`
            <div class="system-prompt-section">
                <eog-card>
                    <h2>System Prompt</h2>
                    <p class="param-description" style="margin-bottom: 16px;">
                        Define the AI's persona and behavior. This prompt is sent at the start of every conversation.
                    </p>
                    <textarea
                        class="system-prompt-textarea"
                        .value=${this._config.system_prompt || ''}
                        @input=${(e: Event) => this._updateConfig('system_prompt', (e.target as HTMLTextAreaElement).value)}
                        placeholder="You are a helpful AI assistant..."
                    ></textarea>
                    <div class="actions">
                        <eog-button @click=${this._saveConfig}>Save System Prompt</eog-button>
                    </div>
                </eog-card>
            </div>
        `;
    }

    private async _loadConfig() {
        this._isLoading = true;
        try {
            const response = await fetch('/api/v2/cognitive/config', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('eog_auth_token')}` }
            });
            if (response.ok) {
                this._config = await response.json();
            }
        } catch (error) {
            console.error('Failed to load cognitive config:', error);
        } finally {
            this._isLoading = false;
        }
    }

    private async _loadTemplates() {
        try {
            const response = await fetch('/api/v2/cognitive/templates', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('eog_auth_token')}` }
            });
            if (response.ok) {
                this._templates = await response.json();
            }
        } catch (error) {
            console.error('Failed to load templates:', error);
        }
    }

    private _updateConfig(key: keyof CognitiveConfig, value: unknown) {
        this._config = { ...this._config, [key]: value };
    }

    private async _saveConfig() {
        this._isSaving = true;
        try {
            const response = await fetch('/api/v2/cognitive/config', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('eog_auth_token')}`
                },
                body: JSON.stringify(this._config),
            });
            if (response.ok) {
                this.dispatchEvent(new CustomEvent('eog-toast', {
                    detail: { message: 'Settings saved', type: 'success' },
                    bubbles: true, composed: true,
                }));
            }
        } catch (error) {
            console.error('Failed to save config:', error);
        } finally {
            this._isSaving = false;
        }
    }

    private async _resetConfig() {
        try {
            const response = await fetch('/api/v2/cognitive/config/reset', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('eog_auth_token')}` }
            });
            if (response.ok) {
                this._config = await response.json();
            }
        } catch (error) {
            console.error('Failed to reset config:', error);
        }
    }

    private _createTemplate() {
        this.dispatchEvent(new CustomEvent('eog-navigate', {
            detail: { path: '/cognitive/templates/new' },
            bubbles: true, composed: true,
        }));
    }

    private _editTemplate(template: PromptTemplate) {
        this.dispatchEvent(new CustomEvent('eog-navigate', {
            detail: { path: `/cognitive/templates/${template.id}` },
            bubbles: true, composed: true,
        }));
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-cognitive': EogCognitive;
    }
}
