/**
 * SaaS Platform Activity Feed
 * Renders the recent activity/revenue feed for the platform dashboard.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { RecentEvent } from '../controllers/platform-dashboard-controller.js';

@customElement('saas-platform-activity-feed')
export class SaasPlatformActivityFeed extends LitElement {
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

        .activity-feed { padding: 0; }

        .activity-item {
            display: flex;
            gap: 14px;
            padding: 16px 20px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .activity-item:last-child { border-bottom: none; }

        .activity-icon {
            width: 36px;
            height: 36px;
            border-radius: 10px;
            background: var(--saas-bg-hover, #fafafa);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .activity-icon .material-symbols-outlined { font-size: 18px; }

        .activity-icon.tenant { background: #dbeafe; color: #1d4ed8; }
        .activity-icon.agent { background: #d1fae5; color: #047857; }
        .activity-icon.billing { background: #fef3c7; color: #b45309; }
        .activity-icon.alert { background: #fee2e2; color: #b91c1c; }
        .activity-icon.user { background: #e0e7ff; color: #4338ca; }

        .activity-content { flex: 1; }

        .activity-text {
            font-size: 13px;
            line-height: 1.4;
        }

        .activity-time {
            font-size: 11px;
            color: var(--saas-text-muted, #999);
            margin-top: 4px;
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

    @property({ type: Array }) events: RecentEvent[] = [];

    render() {
        return html`
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        <span class="material-symbols-outlined">history</span>
                        Recent Activity
                    </h3>
                </div>
                <div class="card-body activity-feed">
                    ${this.events.map(event => html`
                        <div class="activity-item">
                            <div class="activity-icon ${event.type}">
                                <span class="material-symbols-outlined">${this._getEventIcon(event.type)}</span>
                            </div>
                            <div class="activity-content">
                                <div class="activity-text">${event.message}</div>
                                <div class="activity-time">${event.timestamp}</div>
                            </div>
                        </div>
                    `)}
                </div>
                <a href="/saas/audit" class="view-all">View all activity</a>
            </div>
        `;
    }

    private _getEventIcon(type: string): string {
        const icons: Record<string, string> = {
            tenant: 'apartment',
            agent: 'smart_toy',
            billing: 'payments',
            alert: 'warning',
            user: 'person',
        };
        return icons[type] || 'info';
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-platform-activity-feed': SaasPlatformActivityFeed;
    }
}
