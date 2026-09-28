/**
 * Voice Chat View - Real-time Voice Interaction
 *
 * VIBE COMPLIANT - Lit View
 * Layout and coordination shell for the voice chat experience.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { ref } from 'lit/directives/ref.js';
import {
    VoiceChatController,
    type VoicePersona,
} from '../controllers/voice-chat-controller.js';
import '../components/saas-voice-session-picker.js';
import '../components/saas-voice-controls.js';
import '../components/saas-voice-transcript.js';
import type { SaasVoiceTranscript } from '../components/saas-voice-transcript.js';

@customElement('saas-voice-chat')
export class SaasVoiceChat extends LitElement {
    static styles = css`
        :host {
            display: block;
            height: 100%;
            background: var(--saas-bg, #f8fafc);
        }

        .chat-container {
            display: grid;
            grid-template-columns: 280px 1fr;
            height: 100%;
            gap: 24px;
            padding: 24px;
        }

        @media (max-width: 768px) {
            .chat-container {
                grid-template-columns: 1fr;
            }

            .sidebar {
                display: none;
            }
        }

        .main-area {
            display: flex;
            flex-direction: column;
            gap: 20px;
            min-height: 0;
        }

        .voice-area {
            flex: 1;
            display: grid;
            grid-template-rows: auto 1fr;
            gap: 20px;
            min-height: 0;
        }
    `;

    @property({ type: String }) tenantId = '';

    private _controller = new VoiceChatController(this, {
        onTranscriptAdd: (
            role: 'user' | 'assistant',
            content: string,
            isPartial?: boolean
        ) => {
            this._transcriptRef?.addMessage(role, content, isPartial);
        },
        onTranscriptUpdate: (content: string, isPartial?: boolean) => {
            this._transcriptRef?.updateLastMessage(content, isPartial);
        },
    });

    private _transcriptRef?: SaasVoiceTranscript;

    connectedCallback() {
        super.connectedCallback();
        this._controller.loadPersonas();
    }

    disconnectedCallback() {
        this._controller.destroy();
        super.disconnectedCallback();
    }

    private _setTranscriptRef(el: Element | undefined) {
        this._transcriptRef = el as SaasVoiceTranscript | undefined;
    }

    render() {
        const c = this._controller;

        return html`
            <div class="chat-container">
                <saas-voice-session-picker
                    class="sidebar"
                    .personas=${c.personas}
                    .selectedPersona=${c.selectedPersona}
                    .loading=${c.isLoading}
                    @persona-selected=${(e: CustomEvent) =>
                        c.selectPersona(e.detail.persona as VoicePersona)}
                ></saas-voice-session-picker>

                <main class="main-area">
                    <saas-voice-controls
                        .sessionStatus=${c.sessionStatus}
                        .selectedPersona=${c.selectedPersona}
                        .duration=${c.duration}
                        .turnCount=${c.turnCount}
                        .isLoading=${c.isLoading}
                        .isRecording=${c.isRecording}
                        .error=${c.error}
                        @start-session=${() => c.startSession(this.tenantId)}
                        @end-session=${() => c.endSession()}
                        @recording-start=${(e: CustomEvent) =>
                            c.handleRecordingStart(
                                e.detail.stream as MediaStream
                            )}
                        @recording-stop=${() => c.handleRecordingStop()}
                    ></saas-voice-controls>

                    <div class="transcript-section">
                        <saas-voice-transcript
                            ${ref(this._setTranscriptRef)}
                        ></saas-voice-transcript>
                    </div>
                </main>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-voice-chat': SaasVoiceChat;
    }
}
