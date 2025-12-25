/**
 * Voice Persona Card Component
 * 
 * VIBE COMPLIANT - Lit Component
 * Displays voice persona info with edit/delete actions.
 * Follows soma-voice-button patterns.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

interface VoicePersona {
    id: string;
    name: string;
    description: string;
    voice_id: string;
    voice_speed: number;
    stt_model: string;
    stt_language: string;
    llm_config_name: string | null;
    llm_provider: string | null;
    system_prompt: string;
    is_active: boolean;
    is_default: boolean;
}

@customElement('voice-persona-card')
export class VoicePersonaCard extends LitElement {
    static styles = css`
        :host {
            display: block;
        }

        .persona-card {
            background: var(--soma-surface, rgba(30, 41, 59, 0.85));
            border-radius: var(--soma-radius-lg, 12px);
            padding: 20px;
            border: 1px solid var(--soma-border, rgba(148, 163, 184, 0.1));
            transition: all 0.2s ease;
        }

        .persona-card:hover {
            border-color: var(--soma-accent, #94a3b8);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .persona-card.inactive {
            opacity: 0.6;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }

        .title-row {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .icon {
            font-size: 24px;
        }

        .name {
            font-size: var(--soma-text-lg, 18px);
            font-weight: 600;
            color: var(--soma-text-main, #e2e8f0);
        }

        .default-badge {
            background: var(--soma-accent, #94a3b8);
            color: var(--soma-bg-base, #1e293b);
            font-size: var(--soma-text-xs, 11px);
            padding: 2px 8px;
            border-radius: 12px;
            font-weight: 600;
        }

        .description {
            color: var(--soma-text-dim, #94a3b8);
            font-size: var(--soma-text-sm, 13px);
            margin-bottom: 16px;
        }

        .config-row {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 16px;
        }

        .config-item {
            display: flex;
            align-items: center;
            gap: 4px;
            background: var(--soma-bg-base, rgba(15, 23, 42, 0.5));
            padding: 4px 10px;
            border-radius: var(--soma-radius-sm, 4px);
            font-size: var(--soma-text-xs, 11px);
            color: var(--soma-text-dim, #94a3b8);
        }

        .config-item .label {
            color: var(--soma-text-muted, #64748b);
        }

        .config-item .value {
            color: var(--soma-text-main, #e2e8f0);
            font-weight: 500;
        }

        .actions {
            display: flex;
            gap: 8px;
        }

        .action-btn {
            background: transparent;
            border: 1px solid var(--soma-border, rgba(148, 163, 184, 0.2));
            color: var(--soma-text-dim, #94a3b8);
            padding: 6px 12px;
            border-radius: var(--soma-radius-sm, 4px);
            font-size: var(--soma-text-xs, 11px);
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .action-btn:hover {
            border-color: var(--soma-accent, #94a3b8);
            color: var(--soma-text-main, #e2e8f0);
        }

        .action-btn.primary {
            background: var(--soma-accent, #94a3b8);
            border-color: var(--soma-accent, #94a3b8);
            color: var(--soma-bg-base, #1e293b);
        }

        .action-btn.danger:hover {
            border-color: var(--soma-danger, #ef4444);
            color: var(--soma-danger, #ef4444);
        }

        .status-badge {
            padding: 2px 8px;
            border-radius: 12px;
            font-size: var(--soma-text-xs, 11px);
            font-weight: 500;
        }

        .status-badge.active {
            background: rgba(34, 197, 94, 0.2);
            color: var(--soma-success, #22c55e);
        }

        .status-badge.inactive {
            background: rgba(148, 163, 184, 0.2);
            color: var(--soma-text-dim, #94a3b8);
        }
    `;

    @property({ type: Object }) persona: VoicePersona | null = null;
    @property({ type: Boolean }) editable = true;

    render() {
        if (!this.persona) return html``;

        const p = this.persona;

        return html`
            <div class="persona-card ${p.is_active ? '' : 'inactive'}">
                <div class="header">
                    <div class="title-row">
                        <span class="icon">🎙️</span>
                        <span class="name">${p.name}</span>
                        ${p.is_default ? html`<span class="default-badge">★ Default</span>` : ''}
                    </div>
                    <span class="status-badge ${p.is_active ? 'active' : 'inactive'}">
                        ${p.is_active ? 'Active' : 'Inactive'}
                    </span>
                </div>

                ${p.description ? html`<div class="description">${p.description}</div>` : ''}

                <div class="config-row">
                    <div class="config-item">
                        <span class="label">Voice:</span>
                        <span class="value">${p.voice_id}</span>
                    </div>
                    <div class="config-item">
                        <span class="label">STT:</span>
                        <span class="value">${p.stt_model}</span>
                    </div>
                    ${p.llm_config_name ? html`
                        <div class="config-item">
                            <span class="label">LLM:</span>
                            <span class="value">${p.llm_provider}/${p.llm_config_name}</span>
                        </div>
                    ` : ''}
                    <div class="config-item">
                        <span class="label">Speed:</span>
                        <span class="value">${p.voice_speed}x</span>
                    </div>
                </div>

                ${this.editable ? html`
                    <div class="actions">
                        <button class="action-btn primary" @click=${this._handleEdit}>Edit</button>
                        <button class="action-btn" @click=${this._handleDuplicate}>Duplicate</button>
                        ${!p.is_default ? html`
                            <button class="action-btn" @click=${this._handleSetDefault}>Set Default</button>
                        ` : ''}
                        <button class="action-btn danger" @click=${this._handleDelete}>Delete</button>
                    </div>
                ` : ''}
            </div>
        `;
    }

    private _handleEdit() {
        this.dispatchEvent(new CustomEvent('persona-edit', {
            bubbles: true,
            composed: true,
            detail: { persona: this.persona }
        }));
    }

    private _handleDuplicate() {
        this.dispatchEvent(new CustomEvent('persona-duplicate', {
            bubbles: true,
            composed: true,
            detail: { persona: this.persona }
        }));
    }

    private _handleSetDefault() {
        this.dispatchEvent(new CustomEvent('persona-set-default', {
            bubbles: true,
            composed: true,
            detail: { persona: this.persona }
        }));
    }

    private _handleDelete() {
        this.dispatchEvent(new CustomEvent('persona-delete', {
            bubbles: true,
            composed: true,
            detail: { persona: this.persona }
        }));
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'voice-persona-card': VoicePersonaCard;
    }
}
