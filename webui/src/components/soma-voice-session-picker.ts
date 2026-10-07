/**
 * Voice Session Picker
 *
 * Renders the voice persona selection sidebar.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { VoicePersona } from '../controllers/voice-chat-controller.js';

@customElement('soma-voice-session-picker')
export class SomaVoiceSessionPicker extends LitElement {
    static styles = css`
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

        :host {
            display: block;
        }

        .sidebar {
            background: var(--soma-surface, white);
            border-radius: 12px;
            border: 1px solid var(--soma-border, #e2e8f0);
            padding: 20px;
            overflow-y: auto;
            height: 100%;
        }

        .sidebar-header {
            font-size: 16px;
            font-weight: 600;
            color: var(--soma-text, #1e293b);
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .persona-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .persona-item {
            padding: 12px;
            border-radius: 8px;
            border: 1px solid var(--soma-border, #e2e8f0);
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .persona-item:hover {
            background: var(--soma-bg, #f8fafc);
        }

        .persona-item.selected {
            border-color: var(--soma-primary, #3b82f6);
            background: rgba(59, 130, 246, 0.05);
        }

        .persona-name {
            font-size: 14px;
            font-weight: 500;
            color: var(--soma-text, #1e293b);
        }

        .persona-voice {
            font-size: 12px;
            color: var(--soma-text-dim, #64748b);
            margin-top: 4px;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .loading {
            font-size: 14px;
            color: var(--soma-text-dim, #64748b);
            text-align: center;
            padding: 20px 0;
        }
    `;

    @property({ type: Array }) personas: VoicePersona[] = [];
    @property({ type: Object }) selectedPersona: VoicePersona | null = null;
    @property({ type: Boolean }) loading = false;

    private _selectPersona(persona: VoicePersona) {
        this.dispatchEvent(
            new CustomEvent('persona-selected', {
                detail: { persona },
                bubbles: true,
                composed: true,
            })
        );
    }

    render() {
        return html`
            <aside class="sidebar">
                <div class="sidebar-header">
                    <span class="material-symbols-outlined">theater_comedy</span>
                    Voice Personas
                </div>

                ${this.loading
                    ? html`<div class="loading">Loading personas...</div>`
                    : ''}

                <div class="persona-list">
                    ${this.personas.map(
                        (persona) => html`
                            <div
                                class="persona-item ${this.selectedPersona?.id ===
                                persona.id
                                    ? 'selected'
                                    : ''}"
                                @click=${() => this._selectPersona(persona)}
                            >
                                <div class="persona-name">${persona.name}</div>
                                <div class="persona-voice">
                                    <span
                                        class="material-symbols-outlined"
                                        style="font-size:12px;"
                                        >volume_up</span
                                    >
                                    ${persona.voice_id}
                                </div>
                            </div>
                        `
                    )}
                </div>
            </aside>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-voice-session-picker': SomaVoiceSessionPicker;
    }
}
