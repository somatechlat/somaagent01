/**
 * Voice Config Panel Component
 * 
 * VIBE COMPLIANT - Lit Component
 * Form for editing voice persona settings (STT, TTS, LLM, turn detection).
 * References existing LLMModelConfig - no model duplication.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

interface VoiceConfig {
    voice_id: string;
    voice_speed: number;
    stt_model: string;
    stt_language: string;
    llm_config_id: string | null;
    system_prompt: string;
    temperature: number;
    max_tokens: number;
    turn_detection_enabled: boolean;
    turn_detection_threshold: number;
    silence_duration_ms: number;
}

interface LLMOption {
    id: string;
    name: string;
    provider: string;
}

@customElement('voice-config-panel')
export class VoiceConfigPanel extends LitElement {
    static styles = css`
        :host {
            display: block;
        }

        .config-panel {
            background: var(--saas-surface, rgba(30, 41, 59, 0.85));
            border-radius: var(--saas-radius-lg, 12px);
            padding: 24px;
            border: 1px solid var(--saas-border, rgba(148, 163, 184, 0.1));
        }

        .section {
            margin-bottom: 24px;
        }

        .section:last-child {
            margin-bottom: 0;
        }

        .section-title {
            font-size: var(--saas-text-sm, 13px);
            font-weight: 600;
            color: var(--saas-text-dim, #94a3b8);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 12px;
        }

        .form-row {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-bottom: 16px;
        }

        .form-row.full {
            grid-template-columns: 1fr;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        label {
            font-size: var(--saas-text-xs, 11px);
            color: var(--saas-text-muted, #64748b);
            font-weight: 500;
        }

        input, select, textarea {
            background: var(--saas-bg-base, rgba(15, 23, 42, 0.5));
            border: 1px solid var(--saas-border, rgba(148, 163, 184, 0.2));
            border-radius: var(--saas-radius-sm, 4px);
            padding: 8px 12px;
            color: var(--saas-text-main, #e2e8f0);
            font-size: var(--saas-text-sm, 13px);
            font-family: inherit;
        }

        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: var(--saas-accent, #94a3b8);
        }

        textarea {
            min-height: 80px;
            resize: vertical;
        }

        .range-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .range-row {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        input[type="range"] {
            flex: 1;
            padding: 0;
            height: 4px;
            cursor: pointer;
        }

        .range-value {
            min-width: 40px;
            text-align: right;
            font-size: var(--saas-text-sm, 13px);
            color: var(--saas-text-main, #e2e8f0);
        }

        .toggle-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px;
            background: var(--saas-bg-base, rgba(15, 23, 42, 0.5));
            border-radius: var(--saas-radius-sm, 4px);
        }

        .toggle-label {
            font-size: var(--saas-text-sm, 13px);
            color: var(--saas-text-main, #e2e8f0);
        }

        .toggle {
            width: 40px;
            height: 20px;
            background: var(--saas-border, rgba(148, 163, 184, 0.3));
            border-radius: 10px;
            position: relative;
            cursor: pointer;
            transition: background 0.2s ease;
        }

        .toggle.active {
            background: var(--saas-success, #22c55e);
        }

        .toggle::after {
            content: '';
            position: absolute;
            top: 2px;
            left: 2px;
            width: 16px;
            height: 16px;
            background: white;
            border-radius: 50%;
            transition: transform 0.2s ease;
        }

        .toggle.active::after {
            transform: translateX(20px);
        }

        .preview-btn {
            background: var(--saas-accent, #94a3b8);
            border: none;
            border-radius: var(--saas-radius-sm, 4px);
            padding: 8px 16px;
            color: var(--saas-bg-base, #1e293b);
            font-size: var(--saas-text-sm, 13px);
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s ease;
        }

        .preview-btn:hover {
            transform: scale(1.02);
        }
    `;

    @property({ type: Object }) config: VoiceConfig | null = null;
    @property({ type: Array }) llmOptions: LLMOption[] = [];
    @property({ type: Array }) voiceOptions: string[] = ['af_heart', 'af_bella', 'af_nicole', 'am_adam', 'am_michael'];

    @state() private _config: VoiceConfig = {
        voice_id: 'af_heart',
        voice_speed: 1.0,
        stt_model: 'tiny',
        stt_language: 'en',
        llm_config_id: null,
        system_prompt: '',
        temperature: 0.7,
        max_tokens: 1024,
        turn_detection_enabled: true,
        turn_detection_threshold: 0.5,
        silence_duration_ms: 500,
    };

    connectedCallback() {
        super.connectedCallback();
        if (this.config) {
            this._config = { ...this._config, ...this.config };
        }
    }

    render() {
        return html`
            <div class="config-panel">
                <!-- Voice (TTS) Settings -->
                <div class="section">
                    <div class="section-title">Voice (Text-to-Speech)</div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Voice</label>
                            <select .value=${this._config.voice_id} @change=${(e: Event) => this._updateConfig('voice_id', (e.target as HTMLSelectElement).value)}>
                                ${this.voiceOptions.map(v => html`<option value=${v} ?selected=${v === this._config.voice_id}>${v}</option>`)}
                            </select>
                        </div>
                        <div class="form-group">
                            <button class="preview-btn" @click=${this._handlePreview}>
                                ▶ Preview
                            </button>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="range-group">
                            <label>Voice Speed</label>
                            <div class="range-row">
                                <input type="range" min="0.5" max="2.0" step="0.1" 
                                    .value=${String(this._config.voice_speed)}
                                    @input=${(e: Event) => this._updateConfig('voice_speed', parseFloat((e.target as HTMLInputElement).value))}
                                />
                                <span class="range-value">${this._config.voice_speed}x</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- STT Settings -->
                <div class="section">
                    <div class="section-title">Speech-to-Text</div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Model</label>
                            <select .value=${this._config.stt_model} @change=${(e: Event) => this._updateConfig('stt_model', (e.target as HTMLSelectElement).value)}>
                                <option value="tiny">Whisper Tiny</option>
                                <option value="small">Whisper Small</option>
                                <option value="medium">Whisper Medium</option>
                                <option value="large">Whisper Large</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Language</label>
                            <select .value=${this._config.stt_language} @change=${(e: Event) => this._updateConfig('stt_language', (e.target as HTMLSelectElement).value)}>
                                <option value="en">English</option>
                                <option value="es">Spanish</option>
                                <option value="fr">French</option>
                                <option value="de">German</option>
                                <option value="auto">Auto-detect</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- LLM Settings -->
                <div class="section">
                    <div class="section-title">LLM Configuration</div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Model (from LLMModelConfig)</label>
                            <select .value=${this._config.llm_config_id || ''} @change=${(e: Event) => this._updateConfig('llm_config_id', (e.target as HTMLSelectElement).value || null)}>
                                <option value="">Select LLM...</option>
                                ${this.llmOptions.map(opt => html`
                                    <option value=${opt.id} ?selected=${opt.id === this._config.llm_config_id}>
                                        ${opt.provider}/${opt.name}
                                    </option>
                                `)}
                            </select>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="range-group">
                            <label>Temperature</label>
                            <div class="range-row">
                                <input type="range" min="0" max="2" step="0.1"
                                    .value=${String(this._config.temperature)}
                                    @input=${(e: Event) => this._updateConfig('temperature', parseFloat((e.target as HTMLInputElement).value))}
                                />
                                <span class="range-value">${this._config.temperature}</span>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Max Tokens</label>
                            <input type="number" min="128" max="8192" step="128"
                                .value=${String(this._config.max_tokens)}
                                @input=${(e: Event) => this._updateConfig('max_tokens', parseInt((e.target as HTMLInputElement).value))}
                            />
                        </div>
                    </div>
                    <div class="form-row full">
                        <div class="form-group">
                            <label>System Prompt</label>
                            <textarea 
                                .value=${this._config.system_prompt}
                                @input=${(e: Event) => this._updateConfig('system_prompt', (e.target as HTMLTextAreaElement).value)}
                                placeholder="Enter the system prompt for this persona..."
                            ></textarea>
                        </div>
                    </div>
                </div>

                <!-- Turn Detection -->
                <div class="section">
                    <div class="section-title">Turn Detection</div>
                    <div class="toggle-row">
                        <span class="toggle-label">Enable VAD Turn Detection</span>
                        <div class="toggle ${this._config.turn_detection_enabled ? 'active' : ''}"
                            @click=${() => this._updateConfig('turn_detection_enabled', !this._config.turn_detection_enabled)}>
                        </div>
                    </div>
                    ${this._config.turn_detection_enabled ? html`
                        <div class="form-row" style="margin-top: 16px;">
                            <div class="range-group">
                                <label>Threshold</label>
                                <div class="range-row">
                                    <input type="range" min="0" max="1" step="0.1"
                                        .value=${String(this._config.turn_detection_threshold)}
                                        @input=${(e: Event) => this._updateConfig('turn_detection_threshold', parseFloat((e.target as HTMLInputElement).value))}
                                    />
                                    <span class="range-value">${this._config.turn_detection_threshold}</span>
                                </div>
                            </div>
                            <div class="form-group">
                                <label>Silence Duration (ms)</label>
                                <input type="number" min="100" max="2000" step="100"
                                    .value=${String(this._config.silence_duration_ms)}
                                    @input=${(e: Event) => this._updateConfig('silence_duration_ms', parseInt((e.target as HTMLInputElement).value))}
                                />
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    private _updateConfig<K extends keyof VoiceConfig>(key: K, value: VoiceConfig[K]) {
        this._config = { ...this._config, [key]: value };
        this.dispatchEvent(new CustomEvent('config-change', {
            bubbles: true,
            composed: true,
            detail: { config: this._config }
        }));
    }

    private _handlePreview() {
        this.dispatchEvent(new CustomEvent('voice-preview', {
            bubbles: true,
            composed: true,
            detail: { voice_id: this._config.voice_id, voice_speed: this._config.voice_speed }
        }));
    }

    getConfig(): VoiceConfig {
        return { ...this._config };
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'voice-config-panel': VoiceConfigPanel;
    }
}
