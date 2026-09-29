/**
 * SaaS Platform Stats Grid
 * Renders the top metrics cards for the platform dashboard.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { PlatformMetrics } from '../controllers/platform-dashboard-controller.js';

@customElement('saas-platform-stats-grid')
export class SaasPlatformStatsGrid extends LitElement {
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

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 32px;
        }

        @media (max-width: 1400px) {
            .metrics-grid { grid-template-columns: repeat(2, 1fr); }
        }

        .metric-card {
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 12px;
            padding: 24px;
            transition: all 0.15s ease;
            cursor: pointer;
        }

        .metric-card:hover {
            border-color: var(--saas-border-medium, #ccc);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        }

        .metric-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 16px;
        }

        .metric-label {
            font-size: 13px;
            color: var(--saas-text-secondary, #666);
            font-weight: 500;
        }

        .metric-icon {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            background: var(--saas-bg-hover, #fafafa);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .metric-icon .material-symbols-outlined { font-size: 20px; }

        .metric-value {
            font-size: 32px;
            font-weight: 700;
            line-height: 1;
            margin-bottom: 8px;
        }

        .metric-sub {
            font-size: 12px;
            color: var(--saas-text-muted, #999);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .metric-trend {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-weight: 500;
        }

        .metric-trend.up { color: var(--saas-status-success, #22c55e); }
        .metric-trend.down { color: var(--saas-status-danger, #ef4444); }

        .metric-trend .material-symbols-outlined { font-size: 14px; }

        .metric-card.featured {
            background: linear-gradient(135deg, #1a1a1a 0%, #333 100%);
            color: white;
            border-color: #1a1a1a;
        }

        .metric-card.featured .metric-label { color: rgba(255,255,255,0.7); }
        .metric-card.featured .metric-icon { background: rgba(255,255,255,0.15); }
        .metric-card.featured .metric-icon .material-symbols-outlined { color: white; }
        .metric-card.featured .metric-sub { color: rgba(255,255,255,0.6); }
        .metric-card.featured .metric-trend.up { color: #86efac; }
    `;

    @property({ type: Object }) metrics!: PlatformMetrics;

    render() {
        return html`
            <div class="metrics-grid">
                <div class="metric-card featured" @click=${() => window.location.href = '/saas/billing'}>
                    <div class="metric-header">
                        <span class="metric-label">Monthly Recurring Revenue</span>
                        <div class="metric-icon">
                            <span class="material-symbols-outlined">payments</span>
                        </div>
                    </div>
                    <div class="metric-value">$${this._formatNumber(this.metrics.mrr)}</div>
                    <div class="metric-sub">
                        ${this.metrics.mrrGrowth == null
                            ? html`<span>—</span>`
                            : html`
                                <span class="metric-trend up">
                                    <span class="material-symbols-outlined">trending_up</span>
                                    +${this.metrics.mrrGrowth}%
                                </span>
                                from last month
                            `}
                    </div>
                </div>

                <div class="metric-card" @click=${() => window.location.href = '/saas/tenants'}>
                    <div class="metric-header">
                        <span class="metric-label">Total Tenants</span>
                        <div class="metric-icon">
                            <span class="material-symbols-outlined">apartment</span>
                        </div>
                    </div>
                    <div class="metric-value">${this.metrics.totalTenants}</div>
                    <div class="metric-sub">
                        ${this.metrics.activeTenants} active, ${this.metrics.trialTenants} trial
                    </div>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        <span class="metric-label">Active Agents</span>
                        <div class="metric-icon">
                            <span class="material-symbols-outlined">smart_toy</span>
                        </div>
                    </div>
                    <div class="metric-value">${this.metrics.activeAgents}</div>
                    <div class="metric-sub">
                        of ${this.metrics.totalAgents} total
                    </div>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        <span class="metric-label">Platform Uptime</span>
                        <div class="metric-icon">
                            <span class="material-symbols-outlined">speed</span>
                        </div>
                    </div>
                    <div class="metric-value">${this._formatUptime(this.metrics.uptime_seconds)}</div>
                    <div class="metric-sub">
                        ${this.metrics.activeAlerts == null
                            ? 'Alerting not configured'
                            : this.metrics.activeAlerts > 0
                                ? html`<span style="color: var(--saas-status-warning)">${this.metrics.activeAlerts} active alerts</span>`
                                : 'No active alerts'}
                    </div>
                </div>
            </div>
        `;
    }

    private _formatNumber(num: number): string {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
        return num.toLocaleString();
    }

    /** Seconds since process start, as a duration (never a percent). */
    private _formatUptime(seconds: number): string {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        if (days > 0) return `${days}d ${hours}h`;
        return `${hours}h ${minutes}m`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-platform-stats-grid': SaasPlatformStatsGrid;
    }
}
