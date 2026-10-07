/**
 * Voice Transcript Wrapper
 *
 * Renders the real-time transcript/messages area.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { ref } from 'lit/directives/ref.js';
import './voice-transcript.js';
import type { VoiceTranscript } from './voice-transcript.js';

@customElement('soma-voice-transcript')
export class SomaVoiceTranscript extends LitElement {
    static styles = css`
        :host {
            display: block;
            height: 100%;
            min-height: 300px;
            max-height: 500px;
        }
    `;

    @property({ type: String }) emptyMessage =
        'Start a voice session to see the conversation here.';

    private _transcript?: VoiceTranscript;

    addMessage(role: 'user' | 'assistant', content: string, isPartial = false) {
        this._transcript?.addMessage(role, content, isPartial);
    }

    updateLastMessage(content: string, isPartial = false) {
        this._transcript?.updateLastMessage(content, isPartial);
    }

    private _setTranscriptRef(el: Element | undefined) {
        this._transcript = el as VoiceTranscript | undefined;
    }

    render() {
        return html`
            <voice-transcript
                ${ref(this._setTranscriptRef)}
                .emptyMessage=${this.emptyMessage}
            ></voice-transcript>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-voice-transcript': SomaVoiceTranscript;
    }
}
