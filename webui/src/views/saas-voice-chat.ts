/**
 * Voice Chat View - Real-time Voice Interaction
 *
 * VIBE COMPLIANT - Lit View
 * Integrates waveform, transcript, and the real-time voice WebSocket
 * for live STT/LLM/TTS sessions.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { ref } from 'lit/directives/ref.js';
import { apiClient } from '../services/api-client.js';
import '../components/voice-waveform.js';
import '../components/voice-transcript.js';
import '../components/voice-persona-card.js';

interface VoicePersona {
    id: string;
    name: string;
    voice_id: string;
    description: string;
    is_default: boolean;
    is_active: boolean;
}

interface PersonaListResponse {
    items: VoicePersona[];
    total: number;
}

interface WSMessage {
    type: string;
    session_id?: string;
    text?: string;
    data?: string;
    status?: string;
    message?: string;
    duration_seconds?: number;
    turn_count?: number;
    is_final?: boolean;
    turn?: number;
    tokens?: number;
    chunk_index?: number;
}

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

        .sidebar {
            background: var(--saas-surface, white);
            border-radius: 12px;
            border: 1px solid var(--saas-border, #e2e8f0);
            padding: 20px;
            overflow-y: auto;
        }

        .sidebar-header {
            font-size: 16px;
            font-weight: 600;
            color: var(--saas-text, #1e293b);
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
            border: 1px solid var(--saas-border, #e2e8f0);
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .persona-item:hover {
            background: var(--saas-bg, #f8fafc);
        }

        .persona-item.selected {
            border-color: var(--saas-primary, #3b82f6);
            background: rgba(59, 130, 246, 0.05);
        }

        .persona-name {
            font-size: 14px;
            font-weight: 500;
            color: var(--saas-text, #1e293b);
        }

        .persona-voice {
            font-size: 12px;
            color: var(--saas-text-dim, #64748b);
            margin-top: 4px;
        }

        .main-area {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header h1 {
            font-size: 24px;
            font-weight: 600;
            color: var(--saas-text, #1e293b);
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .session-status {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }

        .session-status.idle {
            background: var(--saas-bg, #f8fafc);
            color: var(--saas-text-dim, #64748b);
        }

        .session-status.active {
            background: rgba(34, 197, 94, 0.1);
            color: #22c55e;
        }

        .session-status.completed {
            background: rgba(59, 130, 246, 0.1);
            color: #3b82f6;
        }

        .voice-area {
            flex: 1;
            display: grid;
            grid-template-rows: auto 1fr;
            gap: 20px;
        }

        .waveform-section {
            background: var(--saas-surface, white);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid var(--saas-border, #e2e8f0);
        }

        .transcript-section {
            min-height: 300px;
            max-height: 500px;
        }

        .actions {
            display: flex;
            gap: 12px;
            margin-top: 8px;
        }

        .action-btn {
            flex: 1;
            padding: 12px 20px;
            border-radius: 8px;
            border: none;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .action-btn.primary {
            background: var(--saas-primary, #3b82f6);
            color: white;
        }

        .action-btn.primary:hover {
            background: var(--saas-primary-hover, #2563eb);
        }

        .action-btn.primary:disabled {
            background: #93c5fd;
            cursor: not-allowed;
        }

        .action-btn.secondary {
            background: var(--saas-surface, white);
            border: 1px solid var(--saas-border, #e2e8f0);
            color: var(--saas-text, #1e293b);
        }

        .action-btn.secondary:hover {
            background: var(--saas-bg, #f8fafc);
        }

        .action-btn.danger {
            background: #ef4444;
            color: white;
        }

        .action-btn.danger:hover {
            background: #dc2626;
        }

        .stats-bar {
            display: flex;
            gap: 24px;
            padding: 16px 20px;
            background: var(--saas-surface, white);
            border-radius: 8px;
            border: 1px solid var(--saas-border, #e2e8f0);
        }

        .stat {
            display: flex;
            flex-direction: column;
        }

        .stat-value {
            font-size: 18px;
            font-weight: 600;
            color: var(--saas-text, #1e293b);
        }

        .stat-label {
            font-size: 12px;
            color: var(--saas-text-dim, #64748b);
        }

        .error-banner {
            padding: 12px 16px;
            background: rgba(239, 68, 68, 0.1);
            color: #dc2626;
            border-radius: 8px;
            font-size: 14px;
        }
    `;

    @property({ type: String }) tenantId = '';

    @state() private personas: VoicePersona[] = [];
    @state() private selectedPersona: VoicePersona | null = null;
    @state() private sessionId: string | null = null;
    @state() private sessionStatus: 'idle' | 'active' | 'completed' = 'idle';
    @state() private duration = 0;
    @state() private turnCount = 0;
    @state() private isLoading = false;
    @state() private error = '';
    @state() private isRecording = false;

    private transcriptRef?: any;
    private durationInterval?: number;
    private ws: WebSocket | null = null;
    private mediaRecorder: MediaRecorder | null = null;
    private audioBuffer: string[] = [];
    private currentAudio: HTMLAudioElement | null = null;

    private _setTranscriptRef(el: Element | undefined) {
        this.transcriptRef = el;
    }

    connectedCallback() {
        super.connectedCallback();
        this._loadPersonas();
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this._stopDurationTimer();
        this._closeWebSocket();
        this._stopRecording();
    }

    private async _loadPersonas() {
        this.isLoading = true;
        try {
            const data = await apiClient.get<PersonaListResponse>(
                '/voice/personas?active_only=true'
            );
            this.personas = data.items || [];
            this.selectedPersona =
                this.personas.find(p => p.is_default) || this.personas[0] || null;
        } catch (e) {
            console.error('Failed to load voice personas:', e);
            this.error = 'Unable to load voice personas. Please try again later.';
        }
        this.isLoading = false;
    }

    private _getTenantId(): string {
        return (
            this.tenantId ||
            sessionStorage.getItem('saas_tenant_id') ||
            'default'
        );
    }

    private _startSession() {
        if (!this.selectedPersona) return;

        this.error = '';
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const tenantId = this._getTenantId();
        const wsUrl = `${protocol}//${window.location.host}/ws/voice/?tenant_id=${encodeURIComponent(tenantId)}`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            this._sendWS({
                type: 'start_session',
                persona_id: this.selectedPersona!.id,
            });
        };

        this.ws.onmessage = (event) => {
            try {
                const msg: WSMessage = JSON.parse(event.data);
                this._handleWSMessage(msg);
            } catch (e) {
                console.error('Invalid WebSocket message:', e);
            }
        };

        this.ws.onerror = () => {
            this.error = 'Voice connection error. Please try again.';
            this._resetSession();
        };

        this.ws.onclose = () => {
            if (this.sessionStatus === 'active') {
                this.sessionStatus = 'completed';
                this._stopDurationTimer();
            }
            this.ws = null;
        };

        this.isLoading = true;
    }

    private _handleWSMessage(msg: WSMessage) {
        switch (msg.type) {
            case 'connected':
                this.sessionId = msg.session_id || null;
                break;
            case 'session_started':
                this.sessionStatus = 'active';
                this.duration = 0;
                this.turnCount = 0;
                this.isLoading = false;
                this._startDurationTimer();
                break;
            case 'status':
                // Waveform status is driven by recording state, but future
                // enhancements could mirror the server status here.
                break;
            case 'transcription':
                if (msg.text) {
                    this.turnCount = msg.turn || this.turnCount + 1;
                    this.transcriptRef?.addMessage('user', msg.text, false);
                }
                break;
            case 'response_start':
                this.audioBuffer = [];
                this.transcriptRef?.addMessage('assistant', '...', true);
                break;
            case 'audio_chunk':
                if (msg.data) {
                    this.audioBuffer.push(msg.data);
                }
                break;
            case 'response_end':
                if (msg.text) {
                    this.transcriptRef?.updateLastMessage(msg.text, false);
                }
                this._playAudioBuffer();
                break;
            case 'session_ended':
                this.sessionStatus = 'completed';
                this._stopDurationTimer();
                this._closeWebSocket();
                break;
            case 'error':
                this.error = msg.message || 'Voice session error.';
                break;
        }
    }

    private _sendWS(payload: object) {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(payload));
        }
    }

    private _closeWebSocket() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    private _endSession() {
        this._sendWS({ type: 'end_session' });
        this._closeWebSocket();
        this._stopRecording();
        this._stopDurationTimer();
        this.sessionStatus = 'completed';
    }

    private _resetSession() {
        this._closeWebSocket();
        this._stopRecording();
        this._stopDurationTimer();
        this.sessionStatus = 'idle';
        this.sessionId = null;
        this.isLoading = false;
    }

    private _startDurationTimer() {
        this._stopDurationTimer();
        this.durationInterval = window.setInterval(() => {
            this.duration += 1;
        }, 1000);
    }

    private _stopDurationTimer() {
        if (this.durationInterval) {
            clearInterval(this.durationInterval);
            this.durationInterval = undefined;
        }
    }

    private _formatDuration(seconds: number): string {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    private _handleRecordingStart(e: CustomEvent) {
        const stream = e.detail?.stream as MediaStream | undefined;
        if (!stream || !this.ws) return;

        this.isRecording = true;
        this.error = '';

        try {
            const mimeType = MediaRecorder.isTypeSupported('audio/webm')
                ? 'audio/webm'
                : MediaRecorder.isTypeSupported('audio/mp4')
                  ? 'audio/mp4'
                  : '';
            this.mediaRecorder = mimeType
                ? new MediaRecorder(stream, { mimeType })
                : new MediaRecorder(stream);

            this.mediaRecorder.ondataavailable = async (event: BlobEvent) => {
                if (event.data && event.data.size > 0) {
                    const base64 = await this._blobToBase64(event.data);
                    this._sendWS({
                        type: 'audio_chunk',
                        data: base64,
                        format: this._formatFromMimeType(this.mediaRecorder?.mimeType || 'webm'),
                    });
                }
            };

            this.mediaRecorder.start(250);
        } catch (err) {
            console.error('MediaRecorder error:', err);
            this.error = 'Could not start audio recording.';
            this.isRecording = false;
        }
    }

    private _handleRecordingStop() {
        this._stopRecording();
        if (this.sessionStatus === 'active') {
            // Allow the user to record again for the next turn.
        }
    }

    private _stopRecording() {
        this.isRecording = false;
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            try {
                this.mediaRecorder.stop();
            } catch {
                // ignore
            }
        }
        this.mediaRecorder = null;
    }

    private _blobToBase64(blob: Blob): Promise<string> {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => {
                const result = reader.result as string;
                const base64 = result.split(',')[1] || '';
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }

    private _formatFromMimeType(mimeType: string): string {
        if (mimeType.includes('mp4')) return 'mp4';
        if (mimeType.includes('webm')) return 'webm';
        if (mimeType.includes('ogg')) return 'ogg';
        if (mimeType.includes('wav')) return 'wav';
        return 'webm';
    }

    private _playAudioBuffer() {
        if (this.audioBuffer.length === 0) return;
        try {
            const byteCharacters = atob(this.audioBuffer.join(''));
            const byteNumbers = new Array(byteCharacters.length)
                .fill(0)
                .map((_, i) => byteCharacters.charCodeAt(i));
            const byteArray = new Uint8Array(byteNumbers);
            const blob = new Blob([byteArray], { type: 'audio/mpeg' });
            const url = URL.createObjectURL(blob);

            this.currentAudio = new Audio(url);
            this.currentAudio.onended = () => {
                URL.revokeObjectURL(url);
            };
            this.currentAudio.play().catch((err) => {
                console.warn('Audio playback failed:', err);
            });
        } catch (err) {
            console.error('Failed to play audio response:', err);
        }
    }

    render() {
        const statusLabel =
            this.sessionStatus === 'active'
                ? 'Active Session'
                : this.sessionStatus === 'completed'
                  ? 'Session Ended'
                  : 'Ready';

        return html`
            <div class="chat-container">
                <aside class="sidebar">
                    <div class="sidebar-header">
                        <span class="material-symbols-outlined">theater_comedy</span>
                        Voice Personas
                    </div>
                    <div class="persona-list">
                        ${this.personas.map(
                            (persona) => html`
                                <div
                                    class="persona-item ${this.selectedPersona?.id ===
                                    persona.id
                                        ? 'selected'
                                        : ''}"
                                    @click=${() => (this.selectedPersona = persona)}
                                >
                                    <div class="persona-name">${persona.name}</div>
                                    <div class="persona-voice">
                                        <span class="material-symbols-outlined" style="font-size:12px;">volume_up</span>
                                        ${persona.voice_id}
                                    </div>
                                </div>
                            `
                        )}
                    </div>
                </aside>

                <main class="main-area">
                    <div class="header">
                        <h1>
                            <span class="material-symbols-outlined">mic</span>
                            Voice Chat
                            ${this.selectedPersona
                                ? html`
                                      <span
                                          style="font-size: 14px; font-weight: 400; color: var(--saas-text-dim);"
                                      >
                                          with ${this.selectedPersona.name}
                                      </span>
                                  `
                                : ''}
                        </h1>
                        <span class="session-status ${this.sessionStatus}">
                            ${statusLabel}
                        </span>
                    </div>

                    ${this.error
                        ? html`<div class="error-banner">${this.error}</div>`
                        : ''}

                    ${this.sessionStatus === 'active'
                        ? html`
                              <div class="stats-bar">
                                  <div class="stat">
                                      <span class="stat-value"
                                          >${this._formatDuration(this.duration)}</span
                                      >
                                      <span class="stat-label">Duration</span>
                                  </div>
                                  <div class="stat">
                                      <span class="stat-value">${this.turnCount}</span>
                                      <span class="stat-label">Turns</span>
                                  </div>
                                  <div class="stat">
                                      <span class="stat-value"
                                          >${this.selectedPersona?.voice_id || '-'}</span
                                      >
                                      <span class="stat-label">Voice</span>
                                  </div>
                              </div>
                          `
                        : ''}

                    <div class="voice-area">
                        <div class="waveform-section">
                            <voice-waveform
                                .status=${this.isRecording
                                    ? 'listening'
                                    : this.sessionStatus === 'active'
                                      ? 'idle'
                                      : 'idle'}
                                .showControls=${this.sessionStatus === 'active'}
                                @recording-start=${this._handleRecordingStart}
                                @recording-stop=${this._handleRecordingStop}
                            ></voice-waveform>

                            <div class="actions">
                                ${this.sessionStatus === 'idle'
                                    ? html`
                                          <button
                                              class="action-btn primary"
                                              @click=${this._startSession}
                                              ?disabled=${this.isLoading ||
                                              !this.selectedPersona}
                                          >
                                              ${this.isLoading
                                                  ? 'Starting...'
                                                  : html`
                                                        <span class="material-symbols-outlined">mic</span>
                                                        Start Voice Session
                                                    `}
                                          </button>
                                      `
                                    : html`
                                          <button
                                              class="action-btn danger"
                                              @click=${this._endSession}
                                          >
                                              <span class="material-symbols-outlined">stop_circle</span>
                                              End Session
                                          </button>
                                      `}
                            </div>
                        </div>

                        <div class="transcript-section">
                            <voice-transcript
                                ${ref(this._setTranscriptRef)}
                                .emptyMessage=${'Start a voice session to see the conversation here.'}
                            ></voice-transcript>
                        </div>
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
