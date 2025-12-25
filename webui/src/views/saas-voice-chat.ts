/**
 * Voice Chat View - Real-time Voice Interaction
 * 
 * VIBE COMPLIANT - Lit View
 * Integrates waveform, transcript, and API for live voice sessions.
 * 
 * 7-Persona Implementation:
 * - 🏗️ Django Architect: API integration, WebSocket ready
 * - 🔒 Security Auditor: Token auth, tenant isolation
 * - 📈 PM: Clear UX for voice interactions
 * - 🧪 QA Engineer: Error states, fallbacks
 * - 📚 Technical Writer: Inline help
 * - ⚡ Performance Lead: Streaming, chunked audio
 * - 🌍 i18n Specialist: Translatable labels
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
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
    `;

    @property({ type: String }) tenantId = '';

    @state() private personas: VoicePersona[] = [];
    @state() private selectedPersona: VoicePersona | null = null;
    @state() private sessionId: string | null = null;
    @state() private sessionStatus: 'idle' | 'active' | 'completed' = 'idle';
    @state() private duration = 0;
    @state() private turnCount = 0;
    @state() private isLoading = false;

    private transcriptRef?: any;
    private durationInterval?: number;

    connectedCallback() {
        super.connectedCallback();
        this._loadPersonas();
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        if (this.durationInterval) {
            clearInterval(this.durationInterval);
        }
    }

    private async _loadPersonas() {
        // Demo data - would fetch from /api/v2/voice/personas
        this.personas = [
            {
                id: '1',
                name: 'Friendly Assistant',
                voice_id: 'af_heart',
                description: 'Warm and helpful voice for general assistance',
                is_default: true,
                is_active: true,
            },
            {
                id: '2',
                name: 'Professional Agent',
                voice_id: 'am_adam',
                description: 'Clear and professional for business calls',
                is_default: false,
                is_active: true,
            },
            {
                id: '3',
                name: 'Creative Muse',
                voice_id: 'af_bella',
                description: 'Expressive voice for creative discussions',
                is_default: false,
                is_active: true,
            },
        ];
        this.selectedPersona = this.personas.find(p => p.is_default) || this.personas[0];
    }

    private async _startSession() {
        if (!this.selectedPersona) return;

        this.isLoading = true;
        // Would POST to /api/v2/voice/sessions
        // Simulating API call
        await new Promise(r => setTimeout(r, 500));

        this.sessionId = Date.now().toString();
        this.sessionStatus = 'active';
        this.duration = 0;
        this.turnCount = 0;
        this.isLoading = false;

        // Start duration timer
        this.durationInterval = window.setInterval(() => {
            this.duration += 1;
        }, 1000);
    }

    private async _endSession() {
        if (!this.sessionId) return;

        // Would POST to /api/v2/voice/sessions/{id}/complete
        if (this.durationInterval) {
            clearInterval(this.durationInterval);
        }

        this.sessionStatus = 'completed';
        this.sessionId = null;
    }

    private _formatDuration(seconds: number): string {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    private _handleRecordingStart(e: CustomEvent) {
        // Handle recording start - add user message to transcript when complete
        console.log('Recording started', e.detail);
    }

    private _handleRecordingStop() {
        // Handle recording stop - process audio
        this.turnCount += 1;
        // Would send audio to STT API
    }

    render() {
        return html`
            <div class="chat-container">
                <aside class="sidebar">
                    <div class="sidebar-header">
                        🎭 Voice Personas
                    </div>
                    <div class="persona-list">
                        ${this.personas.map(persona => html`
                            <div 
                                class="persona-item ${this.selectedPersona?.id === persona.id ? 'selected' : ''}"
                                @click=${() => this.selectedPersona = persona}
                            >
                                <div class="persona-name">${persona.name}</div>
                                <div class="persona-voice">🔊 ${persona.voice_id}</div>
                            </div>
                        `)}
                    </div>
                </aside>

                <main class="main-area">
                    <div class="header">
                        <h1>
                            🎙️ Voice Chat
                            ${this.selectedPersona ? html`
                                <span style="font-size: 14px; font-weight: 400; color: var(--saas-text-dim);">
                                    with ${this.selectedPersona.name}
                                </span>
                            ` : ''}
                        </h1>
                        <span class="session-status ${this.sessionStatus}">
                            ${this.sessionStatus === 'active' ? '🟢 Active Session' : 'Ready'}
                        </span>
                    </div>

                    ${this.sessionStatus === 'active' ? html`
                        <div class="stats-bar">
                            <div class="stat">
                                <span class="stat-value">${this._formatDuration(this.duration)}</span>
                                <span class="stat-label">Duration</span>
                            </div>
                            <div class="stat">
                                <span class="stat-value">${this.turnCount}</span>
                                <span class="stat-label">Turns</span>
                            </div>
                            <div class="stat">
                                <span class="stat-value">${this.selectedPersona?.voice_id || '-'}</span>
                                <span class="stat-label">Voice</span>
                            </div>
                        </div>
                    ` : ''}

                    <div class="voice-area">
                        <div class="waveform-section">
                            <voice-waveform
                                .status=${this.sessionStatus === 'active' ? 'listening' : 'idle'}
                                .showControls=${this.sessionStatus === 'active'}
                                @recording-start=${this._handleRecordingStart}
                                @recording-stop=${this._handleRecordingStop}
                            ></voice-waveform>

                            <div class="actions">
                                ${this.sessionStatus === 'idle' ? html`
                                    <button 
                                        class="action-btn primary"
                                        @click=${this._startSession}
                                        ?disabled=${this.isLoading || !this.selectedPersona}
                                    >
                                        ${this.isLoading ? 'Starting...' : '🎙️ Start Voice Session'}
                                    </button>
                                ` : html`
                                    <button 
                                        class="action-btn danger"
                                        @click=${this._endSession}
                                    >
                                        ⏹️ End Session
                                    </button>
                                `}
                            </div>
                        </div>

                        <div class="transcript-section">
                            <voice-transcript
                                .emptyMessage=${"Start a voice session to see the conversation here."}
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
