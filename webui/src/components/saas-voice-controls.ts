/**
 * Voice Controls
 *
 * Renders session status, stats, waveform, and call controls.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import '../components/voice-waveform.js';
import type { VoicePersona } from '../controllers/voice-chat-controller.js';

@customElement('saas-voice-controls')
export class SaasVoiceControls extends LitElement {
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
            margin: 0;
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

        .persona-subtitle {
            font-size: 14px;
            font-weight: 400;
            color: var(--saas-text-dim, #64748b);
        }

        .error-banner {
            padding: 12px 16px;
            background: rgba(239, 68, 68, 0.1);
            color: #dc2626;
            border-radius: 8px;
            font-size: 14px;
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

        .waveform-section {
            background: var(--saas-surface, white);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid var(--saas-border, #e2e8f0);
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
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
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

        .action-btn.danger {
            background: #ef4444;
            color: white;
        }

        .action-btn.danger:hover {
            background: #dc2626;
        }
    `;

    @property({ type: String }) sessionStatus: 'idle' | 'active' | 'completed' =
        'idle';
    @property({ type: Object }) selectedPersona: VoicePersona | null = null;
    @property({ type: Number }) duration = 0;
    @property({ type: Number }) turnCount = 0;
    @property({ type: Boolean }) isLoading = false;
    @property({ type: Boolean }) isRecording = false;
    @property({ type: String }) error = '';

    private _formatDuration(seconds: number): string {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    private _startSession() {
        this.dispatchEvent(new CustomEvent('start-session'));
    }

    private _endSession() {
        this.dispatchEvent(new CustomEvent('end-session'));
    }

    private _onRecordingStart(e: CustomEvent) {
        this.dispatchEvent(
            new CustomEvent('recording-start', {
                detail: e.detail,
                bubbles: true,
                composed: true,
            })
        );
    }

    private _onRecordingStop() {
        this.dispatchEvent(
            new CustomEvent('recording-stop', {
                bubbles: true,
                composed: true,
            })
        );
    }

    render() {
        const statusLabel =
            this.sessionStatus === 'active'
                ? 'Active Session'
                : this.sessionStatus === 'completed'
                  ? 'Session Ended'
                  : 'Ready';

        return html`
            <div class="header">
                <h1>
                    <span class="material-symbols-outlined">mic</span>
                    Voice Chat
                    ${this.selectedPersona
                        ? html`
                              <span class="persona-subtitle">
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

            <div class="waveform-section">
                <voice-waveform
                    .status=${this.isRecording ? 'listening' : 'idle'}
                    .showControls=${this.sessionStatus === 'active'}
                    @recording-start=${this._onRecordingStart}
                    @recording-stop=${this._onRecordingStop}
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
                                            <span class="material-symbols-outlined"
                                                >mic</span
                                            >
                                            Start Voice Session
                                        `}
                              </button>
                          `
                        : html`
                              <button
                                  class="action-btn danger"
                                  @click=${this._endSession}
                              >
                                  <span class="material-symbols-outlined"
                                      >stop_circle</span
                                  >
                                  End Session
                              </button>
                          `}
                </div>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-voice-controls': SaasVoiceControls;
    }
}
