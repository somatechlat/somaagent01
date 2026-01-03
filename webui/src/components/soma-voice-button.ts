/**
 * Eye of God Voice Button Component
 * Per Eye of God UIX Design Section 5.4
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - State-driven visual feedback
 * - Audio level visualization
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { consume } from '@lit/context';
import { voiceContext, type VoiceStateData, type VoiceState } from '../stores/voice-store.js';

@customElement('soma-voice-button')
export class SomaVoiceButton extends LitElement {
    static styles = css`
        :host {
            display: inline-block;
        }

        .voice-button {
            position: relative;
            width: 56px;
            height: 56px;
            border-radius: 50%;
            border: none;
            background: var(--soma-surface, rgba(30, 41, 59, 0.85));
            color: var(--soma-text-main, #e2e8f0);
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
        }

        .voice-button:hover:not(:disabled) {
            background: var(--soma-surface-hover, rgba(51, 65, 85, 0.9));
            transform: scale(1.05);
        }

        .voice-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .voice-button.listening {
            background: var(--soma-success, #22c55e);
            animation: pulse 1.5s infinite;
        }

        .voice-button.processing {
            background: var(--soma-info, #3b82f6);
        }

        .voice-button.speaking {
            background: var(--soma-accent, #94a3b8);
        }

        .voice-button.error {
            background: var(--soma-danger, #ef4444);
        }

        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4); }
            50% { box-shadow: 0 0 0 12px rgba(34, 197, 94, 0); }
        }

        .audio-ring {
            position: absolute;
            inset: -4px;
            border-radius: 50%;
            border: 2px solid var(--soma-accent, #94a3b8);
            opacity: 0;
            transform: scale(1);
            transition: all 0.1s ease;
            pointer-events: none;
        }

        .audio-ring.active {
            opacity: 1;
        }

        .mute-indicator {
            position: absolute;
            bottom: -2px;
            right: -2px;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: var(--soma-danger, #ef4444);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            color: white;
        }

        .tooltip {
            position: absolute;
            bottom: calc(100% + 8px);
            left: 50%;
            transform: translateX(-50%);
            background: var(--soma-bg-base, #1e293b);
            color: var(--soma-text-main, #e2e8f0);
            padding: 4px 8px;
            border-radius: var(--soma-radius-sm, 4px);
            font-size: var(--soma-text-xs, 11px);
            white-space: nowrap;
            opacity: 0;
            visibility: hidden;
            transition: all 0.2s ease;
            pointer-events: none;
        }

        .voice-button:hover .tooltip {
            opacity: 1;
            visibility: visible;
        }
    `;

    @consume({ context: voiceContext, subscribe: true })
    @property({ attribute: false })
    voiceState?: VoiceStateData;

    @property({ type: Boolean }) disabled = false;
    @property({ type: String }) size: 'sm' | 'md' | 'lg' = 'md';

    render() {
        const state = this.voiceState?.state || 'idle';
        const audioLevel = this.voiceState?.audioLevel || 0;
        const isMuted = this.voiceState?.isMuted || false;
        const isListening = state === 'listening';

        const ringStyle = isListening
            ? `transform: scale(${1 + audioLevel * 0.3}); opacity: ${audioLevel}`
            : '';

        return html`
            <button
                class="voice-button ${state}"
                ?disabled=${this.disabled}
                @click=${this._handleClick}
                @contextmenu=${this._handleRightClick}
                aria-label=${this._getAriaLabel(state)}
            >
                <span class="audio-ring ${isListening ? 'active' : ''}" style=${ringStyle}></span>
                ${this._getIcon(state)}
                ${isMuted ? html`<span class="mute-indicator">🔇</span>` : ''}
                <span class="tooltip">${this._getTooltip(state)}</span>
            </button>
        `;
    }

    private _getIcon(state: VoiceState): string {
        switch (state) {
            case 'listening': return '🎤';
            case 'processing': return '⏳';
            case 'speaking': return '🔊';
            case 'error': return '⚠️';
            default: return '🎙️';
        }
    }

    private _getTooltip(state: VoiceState): string {
        switch (state) {
            case 'listening': return 'Listening... Click to stop';
            case 'processing': return 'Processing...';
            case 'speaking': return 'Speaking... Click to stop';
            case 'error': return 'Error - Click to retry';
            default: return 'Click to start voice';
        }
    }

    private _getAriaLabel(state: VoiceState): string {
        switch (state) {
            case 'listening': return 'Stop listening';
            case 'processing': return 'Processing voice input';
            case 'speaking': return 'Stop speaking';
            case 'error': return 'Voice error, click to retry';
            default: return 'Start voice input';
        }
    }

    private _handleClick() {
        if (this.disabled) return;

        const state = this.voiceState?.state || 'idle';

        switch (state) {
            case 'idle':
            case 'error':
                this.dispatchEvent(new CustomEvent('voice-start', {
                    bubbles: true,
                    composed: true,
                }));
                break;
            case 'listening':
                this.dispatchEvent(new CustomEvent('voice-stop', {
                    bubbles: true,
                    composed: true,
                }));
                break;
            case 'speaking':
                this.dispatchEvent(new CustomEvent('voice-cancel', {
                    bubbles: true,
                    composed: true,
                }));
                break;
        }
    }

    private _handleRightClick(e: Event) {
        e.preventDefault();
        this.dispatchEvent(new CustomEvent('voice-mute-toggle', {
            bubbles: true,
            composed: true,
        }));
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-voice-button': SomaVoiceButton;
    }
}
