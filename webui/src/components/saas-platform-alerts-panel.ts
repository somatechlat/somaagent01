/**
 * SaaS Platform Alerts Panel
 * Renders active platform alerts derived from dashboard data.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { RecentEvent } from '../controllers/platform-dashboard-controller.js';

@customElement('saas-platform-alerts-panel')
export class SaasPlatformAlertsPanel extends LitElement {
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

        .alert-count {
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 20px;
            background: var(--saas-bg-hover, #fafafa);
            color: var(--saas-text-secondary, #666);
        }

        .alert-count.has-alerts {
            background: #fee2e2;
            color: #b91c1c;
        }

        .card-body { padding: 0; }

        .alert-list { padding: 0; }

        .alert-item {
            display: flex;
            gap: 14px;
            padding: 16px 20px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .alert-item:last-child { border-bottom: none; }

        .alert-icon {
            width: 36px;
            height: 36px;
            border-radius: 10px;
            background: #fee2e2;
            color: #b91c1c;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .alert-icon .material-symbols-outlined { font-size: 18px; }

        .alert-content { flex: 1; }

        .alert-text {
            font-size: 13px;
            line-height: 1.4;
        }

        .alert-time {
            font-size: 11px;
            color: var(--saas-text-muted, #999);
            margin-top: 4px;
        }

        .alert-empty {
            padding: 32px 24px;
            text-align: center;
            color: var(--saas-text-muted, #999);
            font-size: 13px;
        }

        .alert-empty .material-symbols-outlined {
            font-size: 32px;
            margin-bottom: 12px;
            color: var(--saas-status-success, #22c55e);
        }

        .view-all {
            display: block;
            text-align: center;
            padding: 16px;
            font-size: 13px;
            color: var(--saas-text-secondary, #666);
            text-decoration: none;
            border-top: 1px solid var(--saas-border-light, #e0e0e0);
            transition: color 0.1s ease;
        }

        .view-all:hover {
            color: var(--saas-text-primary, #1a1a1a);
            background: var(--saas-bg-hover, #fafafa);
        }
    `;

    @property({ type: Number }) activeAlerts = 0;
    @property({ type: Array }) alerts: RecentEvent[] = [];

    render() {
        return html`
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        <span class="material-symbols-outlined">warning</span>
                        Active Alerts
                    </h3>
                    <span class="alert-count ${this.activeAlerts > 0 ? 'has-alerts' : ''}">
                        ${this.activeAlerts}
                    </span>
                </div>
                <div class="card-body alert-list">
                    ${this.alerts.length > 0
                        ? this.alerts.map(alert => html`
                            <div class="alert-item">
                                <div class="alert-icon">
                                    <span class="material-symbols-outlined">warning</span>
                                </div>
                                <div class="alert-content">
                                    <div class="alert-text">${alert.message}</div>
                                    <div class="alert-time">${alert.timestamp}</div>
                                </div>
                            </div>
                        `)
                        : html`
                            <div class="alert-empty">
                                <span class="material-symbols-outlined">check_circle</span>
                                <div>No active alerts</div>
                            </div>
                        `}
                </div>
                <a href="/saas/audit" class="view-all">View all activity</a>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-platform-alerts-panel': SaasPlatformAlertsPanel;
    }
}
