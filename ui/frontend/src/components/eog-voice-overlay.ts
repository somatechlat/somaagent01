/**
 * Eye of God Voice Overlay Component
 * Per Eye of God UIX Design Section 5.4
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - Audio visualizer
 * - Real-time transcript display
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { consume } from '@lit/context';
import { voiceContext, type VoiceStateData } from '../stores/voice-store.js';
import './eog-button.js';

@customElement('eog-voice-overlay')
export class EogVoiceOverlay extends LitElement {
    static styles = css`
        :host {
            display: contents;
        }

        .overlay {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(8px);
            z-index: var(--eog-z-overlay, 300);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
        }

        .overlay.open {
            opacity: 1;
            visibility: visible;
        }

        .visualizer {
            width: 200px;
            height: 200px;
            position: relative;
            margin-bottom: var(--eog-spacing-xl, 32px);
        }

        .visualizer-ring {
            position: absolute;
            inset: 0;
            border-radius: 50%;
            border: 2px solid var(--eog-accent, #94a3b8);
            opacity: 0.3;
        }

        .visualizer-ring.active {
            animation: ring-pulse 1.5s infinite;
        }

        .visualizer-ring:nth-child(2) {
            inset: 20px;
            animation-delay: 0.2s;
        }

        .visualizer-ring:nth-child(3) {
            inset: 40px;
            animation-delay: 0.4s;
        }

        @keyframes ring-pulse {
            0%, 100% { opacity: 0.3; transform: scale(1); }
            50% { opacity: 0.8; transform: scale(1.05); }
        }

        .visualizer-core {
            position: absolute;
            inset: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--eog-accent, #94a3b8), var(--eog-info, #3b82f6));
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
            transition: transform 0.1s ease;
        }

        .visualizer-core.speaking {
            animation: speak-pulse 0.5s infinite;
        }

        @keyframes speak-pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }

        .bars {
            position: absolute;
            bottom: 50%;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 4px;
            height: 40px;
        }

        .bar {
            width: 4px;
            background: var(--eog-accent, #94a3b8);
            border-radius: 2px;
            animation: bar-bounce 0.8s infinite ease-in-out;
        }

        .bar:nth-child(1) { animation-delay: 0s; }
        .bar:nth-child(2) { animation-delay: 0.1s; }
        .bar:nth-child(3) { animation-delay: 0.2s; }
        .bar:nth-child(4) { animation-delay: 0.3s; }
        .bar:nth-child(5) { animation-delay: 0.4s; }

        @keyframes bar-bounce {
            0%, 100% { height: 10px; }
            50% { height: 40px; }
        }

        .status {
            font-size: var(--eog-text-lg, 16px);
            font-weight: 600;
            color: var(--eog-text-main, #e2e8f0);
            margin-bottom: var(--eog-spacing-sm, 8px);
        }

        .transcript {
            font-size: var(--eog-text-base, 14px);
            color: var(--eog-text-dim, #64748b);
            max-width: 500px;
            text-align: center;
            min-height: 60px;
            margin-bottom: var(--eog-spacing-lg, 24px);
        }

        .transcript .interim {
            color: var(--eog-text-dim, #64748b);
            font-style: italic;
        }

        .transcript .final {
            color: var(--eog-text-main, #e2e8f0);
        }

        .controls {
            display: flex;
            gap: var(--eog-spacing-md, 16px);
        }

        .hint {
            position: absolute;
            bottom: var(--eog-spacing-xl, 32px);
            font-size: var(--eog-text-xs, 11px);
            color: var(--eog-text-dim, #64748b);
        }
    `;

    @consume({ context: voiceContext, subscribe: true })
    @property({ attribute: false })
    voiceState?: VoiceStateData;

    @property({ type: Boolean }) open = false;

    render() {
        const state = this.voiceState?.state || 'idle';
        const transcript = this.voiceState?.transcript || '';
        const interimTranscript = this.voiceState?.interimTranscript || '';
        const isListening = state === 'listening';
        const isSpeaking = state === 'speaking';

        return html`
            <div class="overlay ${this.open ? 'open' : ''}" @click=${this._handleBackdropClick}>
                <div class="visualizer" @click=${(e: Event) => e.stopPropagation()}>
                    <div class="visualizer-ring ${isListening ? 'active' : ''}"></div>
                    <div class="visualizer-ring ${isListening ? 'active' : ''}"></div>
                    <div class="visualizer-ring ${isListening ? 'active' : ''}"></div>
                    <div class="visualizer-core ${isSpeaking ? 'speaking' : ''}">
                        ${this._getStateIcon(state)}
                    </div>
                    ${isListening ? html`
                        <div class="bars">
                            <div class="bar"></div>
                            <div class="bar"></div>
                            <div class="bar"></div>
                            <div class="bar"></div>
                            <div class="bar"></div>
                        </div>
                    ` : ''}
                </div>

                <div class="status">${this._getStatusText(state)}</div>

                <div class="transcript">
                    ${transcript ? html`<span class="final">${transcript}</span>` : ''}
                    ${interimTranscript ? html`<span class="interim"> ${interimTranscript}</span>` : ''}
                    ${!transcript && !interimTranscript ? html`
                        <span class="interim">Speak now...</span>
                    ` : ''}
                </div>

                <div class="controls">
                    <eog-button 
                        variant="danger"
                        @eog-click=${this._handleCancel}
                    >
                        Cancel
                    </eog-button>
                    ${isListening ? html`
                        <eog-button 
                            variant="primary"
                            @eog-click=${this._handleDone}
                        >
                            Done
                        </eog-button>
                    ` : ''}
                </div>

                <div class="hint">Press Escape to cancel</div>
            </div>
        `;
    }

    private _getStateIcon(state: string): string {
        switch (state) {
            case 'listening': return '🎤';
            case 'processing': return '⏳';
            case 'speaking': return '🔊';
            default: return '🎙️';
        }
    }

    private _getStatusText(state: string): string {
        switch (state) {
            case 'listening': return 'Listening...';
            case 'processing': return 'Processing...';
            case 'speaking': return 'Speaking...';
            default: return 'Ready';
        }
    }

    private _handleBackdropClick() {
        this._handleCancel();
    }

    private _handleCancel() {
        this.dispatchEvent(new CustomEvent('voice-cancel', {
            bubbles: true,
            composed: true,
        }));
    }

    private _handleDone() {
        this.dispatchEvent(new CustomEvent('voice-done', {
            bubbles: true,
            composed: true,
            detail: { transcript: this.voiceState?.transcript },
        }));
    }

    connectedCallback() {
        super.connectedCallback();
        document.addEventListener('keydown', this._handleKeydown);
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        document.removeEventListener('keydown', this._handleKeydown);
    }

    private _handleKeydown = (e: KeyboardEvent) => {
        if (this.open && e.key === 'Escape') {
            this._handleCancel();
        }
    };
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-voice-overlay': EogVoiceOverlay;
    }
}
