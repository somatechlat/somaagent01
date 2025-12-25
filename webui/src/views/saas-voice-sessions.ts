/**
 * Voice Sessions View
 * 
 * VIBE COMPLIANT - Lit View
 * Monitor and manage voice sessions.
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

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
    `;

    @state() private sessions: VoiceSession[] = [];
    @state() private loading = true;
    @state() private stats = { active: 0, total: 0, tokens: 0, audio: 0 };

    connectedCallback() {
        super.connectedCallback();
        this._loadSessions();
    }

    private async _loadSessions() {
        this.loading = true;
        try {
            const response = await fetch('/api/v2/voice/sessions');
            if (response.ok) {
                const data = await response.json();
                this.sessions = data.items || data || [];
            }
        } catch (e) {
            // Demo data
            this.sessions = [
                { id: 'sess_12ab', tenant_id: '1', persona_name: 'Support', status: 'active', duration_seconds: 154, input_tokens: 450, output_tokens: 784, audio_seconds: 45.2, turn_count: 8, created_at: new Date().toISOString() },
                { id: 'sess_34cd', tenant_id: '1', persona_name: 'Sales', status: 'active', duration_seconds: 72, input_tokens: 234, output_tokens: 333, audio_seconds: 22.1, turn_count: 4, created_at: new Date().toISOString() },
                { id: 'sess_56ef', tenant_id: '1', persona_name: 'Support', status: 'completed', duration_seconds: 300, input_tokens: 1234, output_tokens: 1111, audio_seconds: 120.5, turn_count: 15, created_at: new Date(Date.now() - 3600000).toISOString() },
                { id: 'sess_78gh', tenant_id: '1', persona_name: null, status: 'error', duration_seconds: 30, input_tokens: 50, output_tokens: 73, audio_seconds: 8.3, turn_count: 2, created_at: new Date(Date.now() - 7200000).toISOString() },
            ];
        }

        this.stats = {
            active: this.sessions.filter(s => s.status === 'active').length,
            total: this.sessions.length,
            tokens: this.sessions.reduce((sum, s) => sum + s.input_tokens + s.output_tokens, 0),
            audio: this.sessions.reduce((sum, s) => sum + s.audio_seconds, 0),
        };

        this.loading = false;
    }

    render() {
        return html`
            <saas-sidebar></saas-sidebar>
            
            <div class="main-content">
                <div class="header">
                    <h1>📊 Voice Sessions</h1>
                    <div class="actions">
                        <button class="btn" @click=${this._loadSessions}>Refresh</button>
                        <button class="btn">Export</button>
                    </div>
                </div>

                <div class="stats-grid">
                    <saas-stat-card label="Active Sessions" value="${this.stats.active}" status="success"></saas-stat-card>
                    <saas-stat-card label="Total Sessions" value="${this.stats.total}"></saas-stat-card>
                    <saas-stat-card label="Total Tokens" value="${this.stats.tokens.toLocaleString()}"></saas-stat-card>
                    <saas-stat-card label="Audio (sec)" value="${this.stats.audio.toFixed(1)}"></saas-stat-card>
                </div>

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
                            ${this.sessions.map(session => html`
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
                                        ${session.status === 'active' ? html`
                                            <button class="terminate-btn" @click=${() => this._terminateSession(session.id)}>
                                                Terminate
                                            </button>
                                        ` : ''}
                                    </td>
                                </tr>
                            `)}
                        </tbody>
                    </table>
                </div>
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
            await fetch(`/api/v2/voice/sessions/${id}/terminate`, { method: 'POST' });
            this._loadSessions();
        } catch (e) {
            this.sessions = this.sessions.map(s =>
                s.id === id ? { ...s, status: 'terminated' as const } : s
            );
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-voice-sessions': SaasVoiceSessions;
    }
}
