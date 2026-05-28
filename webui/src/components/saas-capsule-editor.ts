/**
 * SomaAgent01 — Capsule Editor
 * Tabbed editor for Soul, Body, Hands, Memory, Governance
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

@customElement('saas-capsule-editor')
export class SaasCapsuleEditor extends LitElement {
    @state() private _activeTab: 'soul' | 'body' | 'hands' | 'memory' | 'governance' = 'soul';
    @state() private _systemPrompt = 'You are an expert software developer. Be concise, write clean code, explain your reasoning.';
    @state() private _personality = { openness: 6.2, conscientiousness: 8.1, extraversion: 4.5, agreeableness: 7.3, neuroticism: 3.1 };
    @state() private _neuromodulators = { dopamine: 0.72, serotonin: 0.95, noradrenaline: 0.18, acetylcholine: 0.51 };

    static styles = css`
        :host {
            display: block;
        }

        .header {
            font-size: 14px;
            font-weight: 600;
            color: var(--aaas-text-primary, #ffffff);
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .capsule-name {
            font-size: 13px;
            color: var(--aaas-text-muted, #6b6b6b);
            font-weight: 400;
        }

        .tabs {
            display: flex;
            gap: 4px;
            margin-bottom: 16px;
            border-bottom: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            padding-bottom: 8px;
        }

        .tab {
            padding: 6px 12px;
            border-radius: var(--aaas-radius-md, 8px);
            font-size: 12px;
            font-weight: 500;
            color: var(--aaas-text-muted, #6b6b6b);
            cursor: pointer;
            transition: all 150ms ease;
            border: none;
            background: transparent;
        }

        .tab:hover {
            color: var(--aaas-text-secondary, #a1a1a1);
            background: var(--aaas-bg-hover, #141414);
        }

        .tab.active {
            color: var(--aaas-accent, #e8e4dc);
            background: var(--aaas-bg-active, #1a1a1a);
        }

        .section {
            margin-bottom: 20px;
        }

        .section-title {
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--aaas-text-muted, #6b6b6b);
            margin-bottom: 12px;
        }

        .field {
            margin-bottom: 16px;
        }

        .field-label {
            font-size: 13px;
            color: var(--aaas-text-secondary, #a1a1a1);
            margin-bottom: 6px;
            display: block;
        }

        textarea, input[type="text"] {
            width: 100%;
            background: var(--aaas-bg-hover, #141414);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            border-radius: var(--aaas-radius-md, 8px);
            padding: 10px 12px;
            color: var(--aaas-text-primary, #ffffff);
            font-size: 13px;
            font-family: inherit;
            outline: none;
            resize: vertical;
            min-height: 80px;
            transition: border-color 150ms ease;
        }

        textarea:focus, input[type="text"]:focus {
            border-color: var(--aaas-border-medium, rgba(255,255,255,0.1));
        }

        .slider-row {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }

        .slider-label {
            font-size: 13px;
            color: var(--aaas-text-secondary, #a1a1a1);
            min-width: 140px;
        }

        .slider-track {
            flex: 1;
            height: 6px;
            background: var(--aaas-bg-hover, #141414);
            border-radius: var(--aaas-radius-full, 9999px);
            position: relative;
            cursor: pointer;
        }

        .slider-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--aaas-success, #22c55e), var(--aaas-warning, #f59e0b), var(--aaas-danger, #ef4444));
            border-radius: var(--aaas-radius-full, 9999px);
            transition: width 200ms ease;
        }

        .slider-value {
            font-size: 12px;
            color: var(--aaas-text-muted, #6b6b6b);
            min-width: 40px;
            text-align: right;
            font-variant-numeric: tabular-nums;
        }

        .neuro-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }

        .neuro-card {
            background: var(--aaas-bg-hover, #141414);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            border-radius: var(--aaas-radius-lg, 12px);
            padding: 14px;
        }

        .neuro-name {
            font-size: 12px;
            color: var(--aaas-text-muted, #6b6b6b);
            margin-bottom: 8px;
        }

        .neuro-value {
            font-size: 22px;
            font-weight: 700;
            color: var(--aaas-text-primary, #ffffff);
            font-variant-numeric: tabular-nums;
        }

        .neuro-bar {
            height: 4px;
            background: var(--aaas-bg-active, #1a1a1a);
            border-radius: var(--aaas-radius-full, 9999px);
            margin-top: 8px;
            overflow: hidden;
        }

        .neuro-fill {
            height: 100%;
            border-radius: var(--aaas-radius-full, 9999px);
            transition: width 300ms ease;
        }

        .actions {
            display: flex;
            gap: 8px;
            margin-top: 20px;
            padding-top: 16px;
            border-top: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
        }

        .btn {
            padding: 8px 16px;
            border-radius: var(--aaas-radius-md, 8px);
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 150ms ease;
            border: none;
        }

        .btn-primary {
            background: var(--aaas-accent, #e8e4dc);
            color: var(--aaas-bg-void, #0a0a0a);
        }

        .btn-primary:hover {
            background: var(--aaas-accent-hover, #ffffff);
        }

        .btn-secondary {
            background: var(--aaas-bg-hover, #141414);
            color: var(--aaas-text-secondary, #a1a1a1);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
        }

        .btn-secondary:hover {
            background: var(--aaas-bg-active, #1a1a1a);
            color: var(--aaas-text-primary, #ffffff);
        }

        .btn-danger {
            background: transparent;
            color: var(--aaas-danger, #ef4444);
            border: 1px solid rgba(239, 68, 68, 0.2);
        }

        .btn-danger:hover {
            background: rgba(239, 68, 68, 0.1);
        }
    `;

    private _renderSoul() {
        return html`
            <div class="section">
                <div class="section-title">System Prompt</div>
                <textarea .value=${this._systemPrompt} @input=${(e: Event) => this._systemPrompt = (e.target as HTMLTextAreaElement).value}></textarea>
            </div>

            <div class="section">
                <div class="section-title">Personality (Big Five)</div>
                ${Object.entries(this._personality).map(([trait, value]) => html`
                    <div class="slider-row">
                        <span class="slider-label">${trait.charAt(0).toUpperCase() + trait.slice(1)}</span>
                        <div class="slider-track">
                            <div class="slider-fill" style="width: ${(value / 10) * 100}%"></div>
                        </div>
                        <span class="slider-value">${value.toFixed(1)}</span>
                    </div>
                `)}
            </div>

            <div class="section">
                <div class="section-title">Neuromodulator Baseline</div>
                <div class="neuro-grid">
                    ${Object.entries(this._neuromodulators).map(([name, value]) => html`
                        <div class="neuro-card">
                            <div class="neuro-name">${name.charAt(0).toUpperCase() + name.slice(1)}</div>
                            <div class="neuro-value">${value.toFixed(2)}</div>
                            <div class="neuro-bar">
                                <div class="neuro-fill" style="width: ${value * 100}%; background: ${value > 0.7 ? 'var(--aaas-success, #22c55e)' : value > 0.4 ? 'var(--aaas-warning, #f59e0b)' : 'var(--aaas-info, #3b82f6)'}"></div>
                            </div>
                        </div>
                    `)}
                </div>
            </div>
        `;
    }

    private _renderBody() {
        return html`
            <div class="section">
                <div class="section-title">Models</div>
                <div class="field">
                    <label class="field-label">Chat Model</label>
                    <input type="text" value="claude-3-sonnet-20240229" />
                </div>
                <div class="field">
                    <label class="field-label">Image Model</label>
                    <input type="text" value="dall-e-3" />
                </div>
                <div class="field">
                    <label class="field-label">Voice Model</label>
                    <input type="text" value="kokoro" />
                </div>
            </div>
        `;
    }

    private _renderHands() {
        return html`
            <div class="section">
                <div class="section-title">Capabilities</div>
                <div class="placeholder" style="color:var(--aaas-text-muted);font-size:13px;padding:20px 0;">
                    Tool registry will be displayed here.
                </div>
            </div>
        `;
    }

    private _renderMemory() {
        return html`
            <div class="section">
                <div class="section-title">Memory Configuration</div>
                <div class="field">
                    <label class="field-label">Recall Limit</label>
                    <input type="text" value="50" />
                </div>
                <div class="field">
                    <label class="field-label">Similarity Threshold</label>
                    <input type="text" value="0.75" />
                </div>
            </div>
        `;
    }

    private _renderGovernance() {
        return html`
            <div class="section">
                <div class="section-title">Governance</div>
                <div class="field">
                    <label class="field-label">Constitution</label>
                    <input type="text" value="default-constitution-v1" readonly />
                </div>
                <div style="font-size:13px;color:var(--aaas-success);margin-top:8px;">✓ Certified (Ed25519)</div>
            </div>
        `;
    }

    render() {
        return html`
            <div class="header">
                <span>Capsule Editor</span>
                <span class="capsule-name">Dev-Assistant-v2.1</span>
            </div>

            <div class="tabs">
                ${(['soul', 'body', 'hands', 'memory', 'governance'] as const).map(t => html`
                    <button class="tab ${this._activeTab === t ? 'active' : ''}" @click=${() => this._activeTab = t}>
                        ${t.charAt(0).toUpperCase() + t.slice(1)}
                    </button>
                `)}
            </div>

            ${this._activeTab === 'soul' ? this._renderSoul() : ''}
            ${this._activeTab === 'body' ? this._renderBody() : ''}
            ${this._activeTab === 'hands' ? this._renderHands() : ''}
            ${this._activeTab === 'memory' ? this._renderMemory() : ''}
            ${this._activeTab === 'governance' ? this._renderGovernance() : ''}

            <div class="actions">
                <button class="btn btn-primary">💾 Save Draft</button>
                <button class="btn btn-secondary">✅ Certify</button>
                <button class="btn btn-secondary">📤 Export</button>
                <button class="btn btn-danger">🗑 Archive</button>
            </div>
        `;
    }
}
