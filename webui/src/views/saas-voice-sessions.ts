/**
 * Voice Sessions View
 *
 * VIBE COMPLIANT - Lit View
 * Monitor and manage real voice sessions.
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';

import '../components/saas-sidebar.js';
import '../components/saas-data-table.js';
import '../components/saas-stat-card.js';
import '../components/saas-status-badge.js';

interface VoiceSession {
    id: string;
    tenant_id: string;
    persona_name: string | null;
    status: 'created' | 'active' | 'completed' | 'error' | 'terminated';
    duration_seconds: number;
    input_tokens: number;
    output_tokens: number;
    audio_seconds: number;
    turn_count: number;
    created_at: string;
}

interface SessionListResponse {
    items: VoiceSession[];
    total: number;
}

interface SessionStats {
    active_count: number;
    total_count: number;
    total_tokens: number;
    total_audio_seconds: number;
}

@customElement('saas-voice-sessions')
export class SaasVoiceSessions extends LitElement {
    static styles = css`
        :host {
            display: flex;
            min-height: 100vh;
            background: var(--saas-bg, #f8fafc);
            color: var(--saas-text, #1e293b);
        }

        .main-content {
            flex: 1;
            padding: 24px 32px;
            margin-left: 260px;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }

        h1 {
            font-size: 28px;
            font-weight: 700;
            margin: 0;
        }

        .actions {
            display: flex;
            gap: 12px;
        }

        .btn {
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            border: 1px solid var(--saas-border, #e2e8f0);
            background: var(--saas-surface, white);
            color: var(--saas-text, #1e293b);
        }

        .btn:hover {
            background: var(--saas-bg, #f8fafc);
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 24px;
        }

        .sessions-table {
            background: var(--saas-surface, white);
            border-radius: 12px;
            border: 1px solid var(--saas-border, #e2e8f0);
            overflow: hidden;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid var(--saas-border, #e2e8f0);
        }

        th {
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--saas-text-dim, #64748b);
            background: var(--saas-bg, #f8fafc);
        }

        td {
            font-size: 14px;
        }

        .id-cell {
            font-family: monospace;
            font-size: 12px;
            color: var(--saas-text-dim, #64748b);
        }

        .status-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }

        .status-active { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
        .status-completed { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
        .status-error { background: rgba(239, 68, 68, 0.15); color: #ef4444; }
        .status-terminated { background: rgba(148, 163, 184, 0.15); color: #94a3b8; }
        .status-created { background: rgba(251, 191, 36, 0.15); color: #f59e0b; }

        .terminate-btn {
            background: transparent;
            border: 1px solid var(--saas-danger, #ef4444);
            color: var(--saas-danger, #ef4444);
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
        }

        .terminate-btn:hover {
            background: var(--saas-danger, #ef4444);
            color: white;
        }

        .loading {
            display: flex;
            justify-content: center;
            padding: 40px;
        }

        .error-banner {
            margin-bottom: 16px;
            padding: 12px 16px;
            background: rgba(239, 68, 68, 0.1);
            color: #dc2626;
            border-radius: 8px;
            font-size: 14px;
        }
    `;

    @state() private sessions: VoiceSession[] = [];
    @state() private loading = true;
    @state() private stats = { active: 0, total: 0, tokens: 0, audio: 0 };
    @state() private error = '';

    connectedCallback() {
        super.connectedCallback();
        this._loadSessions();
    }

    private async _loadSessions() {
        this.loading = true;
        this.error = '';
        try {
            const [listData, statsData] = await Promise.all([
                apiClient.get<SessionListResponse>('/voice/sessions'),
                apiClient.get<SessionStats>('/voice/sessions/stats'),
            ]);

            this.sessions = listData.items || [];
            this.stats = {
                active: statsData.active_count || 0,
                total: statsData.total_count || 0,
                tokens: statsData.total_tokens || 0,
                audio: statsData.total_audio_seconds || 0,
            };
        } catch (e) {
            console.error('Failed to load voice sessions:', e);
            this.error = 'Unable to load voice sessions.';
            this.sessions = [];
            this.stats = { active: 0, total: 0, tokens: 0, audio: 0 };
        }
        this.loading = false;
    }

    render() {
        return html`
            <saas-sidebar></saas-sidebar>

            <div class="main-content">
                <div class="header">
                    <h1>
                        <span class="material-symbols-outlined">analytics</span>
                        Voice Sessions
                    </h1>
                    <div class="actions">
                        <button class="btn" @click=${this._loadSessions}>
                            <span class="material-symbols-outlined" style="font-size:16px;vertical-align:middle;">refresh</span>
                            Refresh
                        </button>
                    </div>
                </div>

                ${this.error ? html`<div class="error-banner">${this.error}</div>` : ''}

                <div class="stats-grid">
                    <saas-stat-card label="Active Sessions" value="${this.stats.active}" status="success"></saas-stat-card>
                    <saas-stat-card label="Total Sessions" value="${this.stats.total}"></saas-stat-card>
                    <saas-stat-card label="Total Tokens" value="${this.stats.tokens.toLocaleString()}"></saas-stat-card>
                    <saas-stat-card label="Audio (sec)" value="${this.stats.audio.toFixed(1)}"></saas-stat-card>
                </div>

                ${this.loading
                    ? html`<div class="loading">Loading...</div>`
                    : html`
                          <div class="sessions-table">
                              <table>
                                  <thead>
                                      <tr>
                                          <th>ID</th>
                                          <th>Persona</th>
                                          <th>Status</th>
                                          <th>Duration</th>
                                          <th>Tokens</th>
                                          <th>Audio</th>
                                          <th>Turns</th>
                                          <th>Created</th>
                                          <th>Actions</th>
                                      </tr>
                                  </thead>
                                  <tbody>
                                      ${this.sessions.map(
                                          (session) => html`
                                              <tr>
                                                  <td class="id-cell">${session.id}</td>
                                                  <td>${session.persona_name || '-'}</td>
                                                  <td>
                                                      <span class="status-badge status-${session.status}">
                                                          ${session.status.toUpperCase()}
                                                      </span>
                                                  </td>
                                                  <td>${this._formatDuration(session.duration_seconds)}</td>
                                                  <td>${(session.input_tokens + session.output_tokens).toLocaleString()}</td>
                                                  <td>${session.audio_seconds.toFixed(1)}s</td>
                                                  <td>${session.turn_count}</td>
                                                  <td>${new Date(session.created_at).toLocaleTimeString()}</td>
                                                  <td>
                                                      ${session.status === 'active'
                                                          ? html`
                                                                <button
                                                                    class="terminate-btn"
                                                                    @click=${() => this._terminateSession(session.id)}
                                                                >
                                                                    Terminate
                                                                </button>
                                                            `
                                                          : ''}
                                                  </td>
                                              </tr>
                                          `
                                      )}
                                  </tbody>
                              </table>
                          </div>
                      `}
            </div>
        `;
    }

    private _formatDuration(seconds: number): string {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    private async _terminateSession(id: string) {
        try {
            await apiClient.post(`/voice/sessions/${id}/terminate`, {});
            await this._loadSessions();
        } catch (e) {
            console.error('Failed to terminate session:', e);
            this.error = 'Failed to terminate session.';
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-voice-sessions': SaasVoiceSessions;
    }
}
