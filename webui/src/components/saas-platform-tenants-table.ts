/**
 * SaaS Platform Tenants Table
 * Renders the recent/top tenants table for the platform dashboard.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { TopTenant } from '../controllers/platform-dashboard-controller.js';

@customElement('saas-platform-tenants-table')
export class SaasPlatformTenantsTable extends LitElement {
    static styles = css`
        :host { display: block; }

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

        .card {
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 12px;
        }

        .card-header {
            padding: 20px 24px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .card-title {
            font-size: 15px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .card-title .material-symbols-outlined {
            font-size: 18px;
            color: var(--saas-text-secondary, #666);
        }

        .card-body { padding: 0; }

        .tenant-table {
            width: 100%;
            border-collapse: collapse;
        }

        .tenant-table th {
            text-align: left;
            padding: 14px 20px;
            font-size: 11px;
            font-weight: 600;
            color: var(--saas-text-muted, #999);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .tenant-table td {
            padding: 16px 20px;
            font-size: 14px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .tenant-table tr:last-child td { border-bottom: none; }

        .tenant-table tr:hover td { background: var(--saas-bg-hover, #fafafa); }

        .tenant-name {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .tenant-avatar {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            background: var(--saas-bg-hover, #fafafa);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 13px;
        }

        .tenant-title { font-weight: 500; }

        .tier-badge {
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .tier-badge.free { background: #f3f4f6; color: #6b7280; }
        .tier-badge.starter { background: #dbeafe; color: #1d4ed8; }
        .tier-badge.team { background: #d1fae5; color: #047857; }
        .tier-badge.enterprise { background: #1a1a1a; color: white; }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }

        .status-dot.active { background: var(--saas-status-success, #22c55e); }
        .status-dot.trial { background: var(--saas-status-warning, #f59e0b); }
        .status-dot.suspended { background: var(--saas-status-danger, #ef4444); }

        .mrr-value { font-weight: 600; font-family: monospace; }

        .btn {
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.1s ease;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            background: var(--saas-bg-card, #ffffff);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .btn:hover { background: var(--saas-bg-hover, #fafafa); }
    `;

    @property({ type: Array }) tenants: TopTenant[] = [];

    render() {
        return html`
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        <span class="material-symbols-outlined">leaderboard</span>
                        Top Tenants by MRR
                    </h3>
                    <button class="btn" @click=${() => window.location.href = '/saas/tenants'}>
                        View All
                    </button>
                </div>
                <div class="card-body">
                    <table class="tenant-table">
                        <thead>
                            <tr>
                                <th>Tenant</th>
                                <th>Tier</th>
                                <th>Agents</th>
                                <th>Users</th>
                                <th>MRR</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${this.tenants.map(t => html`
                                <tr @click=${() => window.location.href = `/saas/tenants/${t.id}`}>
                                    <td>
                                        <div class="tenant-name">
                                            <div class="tenant-avatar">${t.name.charAt(0)}</div>
                                            <div class="tenant-title">${t.name}</div>
                                        </div>
                                    </td>
                                    <td><span class="tier-badge ${t.tier}">${t.tier}</span></td>
                                    <td>${t.agents}</td>
                                    <td>${t.users}</td>
                                    <td>
                                        <span class="mrr-value">
                                            ${t.mrr > 0 ? `$${t.mrr.toLocaleString()}` : html`<span class="status-dot trial"></span> Trial`}
                                        </span>
                                    </td>
                                </tr>
                            `)}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-platform-tenants-table': SaasPlatformTenantsTable;
    }
}
