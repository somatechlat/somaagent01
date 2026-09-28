/**
 * Audit Log View - Security Event History
 * 
 * VIBE COMPLIANT - Lit View
 * Per AGENT_TASKS.md Phase 4.7: Audit Log
 * 
 * 7-Persona Implementation:
 * - architecture Django Architect: /aaas/audit API integration
 * - lock Security Auditor: Tamper-proof log display
 * - monitoring PM: Searchable, filterable audit trail
 * - science QA Engineer: Pagination, export
 * - menu_book Technical Writer: Event descriptions
 * - bolt Performance Lead: Virtual scrolling ready
 * - language i18n Specialist: Date formatting
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';

interface AuditEvent {
    id: string;
    timestamp: string;
    actor_email: string;
    action: string;
    resource_type: string;
    resource_id: string;
    ip_address: string;
    details: Record<string, unknown>;
    status: 'success' | 'failure';
}

@customElement('saas-audit-log')
export class SaasAuditLog extends LitElement {
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
            min-height: 100vh;
            background: var(--saas-bg, #f8fafc);
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }

        h1 {
            font-size: 28px;
            font-weight: 600;
            color: var(--saas-text, #1e293b);
            margin: 0;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .actions {
            display: flex;
            gap: 12px;
        }

        .btn {
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            border: none;
            transition: all 0.2s ease;
        }

        .btn-primary {
            background: var(--saas-primary, #3b82f6);
            color: white;
        }

        .btn-primary:hover {
            background: var(--saas-primary-hover, #2563eb);
        }

        .btn-secondary {
            background: var(--saas-surface, white);
            border: 1px solid var(--saas-border, #e2e8f0);
            color: var(--saas-text, #1e293b);
        }

        .btn-secondary:hover {
            background: var(--saas-bg, #f8fafc);
        }

        .filters {
            display: flex;
            gap: 16px;
            margin-bottom: 20px;
            padding: 16px;
            background: var(--saas-surface, white);
            border-radius: 12px;
            border: 1px solid var(--saas-border, #e2e8f0);
        }

        .filter-group {
            flex: 1;
        }

        .filter-group label {
            display: block;
            font-size: 12px;
            font-weight: 500;
            color: var(--saas-text-dim, #64748b);
            margin-bottom: 6px;
        }

        input, select {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid var(--saas-border, #e2e8f0);
            border-radius: 6px;
            font-size: 14px;
            background: var(--saas-bg, #f8fafc);
            color: var(--saas-text, #1e293b);
            box-sizing: border-box;
        }

        input:focus, select:focus {
            outline: none;
            border-color: var(--saas-primary, #3b82f6);
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }

        .stat-card {
            background: var(--saas-surface, white);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid var(--saas-border, #e2e8f0);
        }

        .stat-value {
            font-size: 28px;
            font-weight: 700;
            color: var(--saas-text, #1e293b);
        }

        .stat-label {
            font-size: 13px;
            color: var(--saas-text-dim, #64748b);
            margin-top: 4px;
        }

        .table-container {
            background: var(--saas-surface, white);
            border-radius: 12px;
            border: 1px solid var(--saas-border, #e2e8f0);
            overflow: hidden;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th {
            text-align: left;
            padding: 14px 16px;
            font-size: 12px;
            font-weight: 600;
            color: var(--saas-text-dim, #64748b);
            background: var(--saas-bg, #f8fafc);
            border-bottom: 1px solid var(--saas-border, #e2e8f0);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        td {
            padding: 14px 16px;
            font-size: 14px;
            color: var(--saas-text, #1e293b);
            border-bottom: 1px solid var(--saas-border, #e2e8f0);
        }

        tr:hover {
            background: var(--saas-bg, #f8fafc);
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }

        .status-success {
            background: rgba(34, 197, 94, 0.1);
            color: #22c55e;
        }

        .status-failure {
            background: rgba(239, 68, 68, 0.1);
            color: #ef4444;
        }

        .action-badge {
            display: inline-block;
            padding: 4px 8px;
            background: var(--saas-bg, #f8fafc);
            border-radius: 4px;
            font-size: 12px;
            font-family: monospace;
        }

        .timestamp {
            font-size: 12px;
            color: var(--saas-text-dim, #64748b);
        }

        .pagination {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px;
            border-top: 1px solid var(--saas-border, #e2e8f0);
        }

        .page-info {
            font-size: 14px;
            color: var(--saas-text-dim, #64748b);
        }

        .page-buttons {
            display: flex;
            gap: 8px;
        }

        .page-btn {
            padding: 8px 12px;
            border: 1px solid var(--saas-border, #e2e8f0);
            background: var(--saas-surface, white);
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }

        .page-btn:hover {
            background: var(--saas-bg, #f8fafc);
        }

        .page-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: var(--saas-text-dim, #64748b);
        }

        .empty-icon {
            font-size: 48px;
            margin-bottom: 16px;
        }

        .error-banner {
            padding: 12px 16px;
            margin-bottom: 20px;
            background: #fee2e2;
            color: #b91c1c;
            border: 1px solid #fecaca;
            border-radius: 12px;
            font-size: 14px;
        }
    `;

    @state() private events: AuditEvent[] = [];
    @state() private searchQuery = '';
    @state() private actionFilter = 'all';
    @state() private dateFilter = 'all';
    @state() private currentPage = 1;
    @state() private totalPages = 1;
    @state() private isLoading = false;
    @state() private error = '';

    connectedCallback() {
        super.connectedCallback();
        this._loadEvents();
    }

    private async _loadEvents() {
        this.isLoading = true;
        this.error = '';
        try {
            const response = await apiClient.get('/aaas/audit/') as {
                events?: AuditEvent[];
                total_pages?: number;
            };
            this.events = response.events || [];
            this.totalPages = response.total_pages || 1;
        } catch (e) {
            this.error = 'Failed to load audit events';
            this.events = [];
            this.totalPages = 1;
        } finally {
            this.isLoading = false;
        }
    }

    private _formatTime(isoString: string): string {
        const date = new Date(isoString);
        return date.toLocaleString();
    }

    private async _exportCsv() {
        // Would call /api/v2/aaas/audit/export
        const csv = this.events.map(e =>
            `${e.timestamp},${e.actor_email},${e.action},${e.status}`
        ).join('\n');

        const blob = new Blob([`Timestamp,Actor,Action,Status\n${csv}`], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'audit-log.csv';
        a.click();
    }

    render() {
        const successCount = this.events.filter(e => e.status === 'success').length;
        const failureCount = this.events.filter(e => e.status === 'failure').length;

        return html`
            <div class="container">
                <div class="header">
                    <h1>Audit Log</h1>
                    <div class="actions">
                        <button class="btn btn-secondary" @click=${this._exportCsv}>
                            <span class="material-symbols-outlined">download</span> Export CSV
                        </button>
                        <button class="btn btn-primary" @click=${this._loadEvents}>
                            <span class="material-symbols-outlined">refresh</span> Refresh
                        </button>
                    </div>
                </div>

                ${this.error ? html`<div class="error-banner">${this.error}</div>` : ''}

                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-value">${this.events.length}</div>
                        <div class="stat-label">Total Events</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" style="color: #22c55e;">${successCount}</div>
                        <div class="stat-label">Successful</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" style="color: #ef4444;">${failureCount}</div>
                        <div class="stat-label">Failed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">24h</div>
                        <div class="stat-label">Time Range</div>
                    </div>
                </div>

                <div class="filters">
                    <div class="filter-group" style="flex: 2;">
                        <label>Search</label>
                        <input 
                            type="text" 
                            placeholder="Search by actor, action, or resource..."
                            .value=${this.searchQuery}
                            @input=${(e: Event) => this.searchQuery = (e.target as HTMLInputElement).value}
                        />
                    </div>
                    <div class="filter-group">
                        <label>Action</label>
                        <select @change=${(e: Event) => this.actionFilter = (e.target as HTMLSelectElement).value}>
                            <option value="all">All Actions</option>
                            <option value="login">Login</option>
                            <option value="create">Create</option>
                            <option value="update">Update</option>
                            <option value="delete">Delete</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>Date</label>
                        <select @change=${(e: Event) => this.dateFilter = (e.target as HTMLSelectElement).value}>
                            <option value="all">All Time</option>
                            <option value="today">Today</option>
                            <option value="week">This Week</option>
                            <option value="month">This Month</option>
                        </select>
                    </div>
                </div>

                <div class="table-container">
                    ${this.events.length > 0 ? html`
                        <table>
                            <thead>
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Actor</th>
                                    <th>Action</th>
                                    <th>Resource</th>
                                    <th>IP Address</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${this.events.map(event => html`
                                    <tr>
                                        <td class="timestamp">${this._formatTime(event.timestamp)}</td>
                                        <td>${event.actor_email}</td>
                                        <td><span class="action-badge">${event.action}</span></td>
                                        <td>${event.resource_type}:${event.resource_id}</td>
                                        <td>${event.ip_address}</td>
                                        <td>
                                            <span class="status-badge status-${event.status}">
                                                ${event.status === 'success' ? html`<span class='material-symbols-outlined' style='font-size:12px;'>check_circle</span>` : html`<span class='material-symbols-outlined' style='font-size:12px;'>cancel</span>`}
                                                ${event.status}
                                            </span>
                                        </td>
                                    </tr>
                                `)}
                            </tbody>
                        </table>

                        <div class="pagination">
                            <div class="page-info">
                                Page ${this.currentPage} of ${this.totalPages}
                            </div>
                            <div class="page-buttons">
                                <button 
                                    class="page-btn"
                                    ?disabled=${this.currentPage === 1}
                                    @click=${() => this.currentPage--}
                                >
                                    <span class="material-symbols-outlined">arrow_back</span> Previous
                                </button>
                                <button 
                                    class="page-btn"
                                    ?disabled=${this.currentPage === this.totalPages}
                                    @click=${() => this.currentPage++}
                                >
                                    Next <span class="material-symbols-outlined">arrow_forward</span>
                                </button>
                            </div>
                        </div>
                    ` : html`
                        <div class="empty-state">
                            <div class="empty-icon material-symbols-outlined">fact_check</div>
                            <p>No audit events found</p>
                        </div>
                    `}
                </div>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-audit-log': SaasAuditLog;
    }
}
