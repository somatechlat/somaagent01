/**
 * Agent Metrics Dashboard
 * Shows usage summary, agent breakdown, and cost estimates.
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Uses /api/v2/observability endpoints
 * - Permission: tenant:read
 * - Per SRS-METRICS-DASHBOARDS.md Section 3.2
 *
 * 7-Persona Implementation:
 * - monitoring PM: Usage tracking, quota visualization
 * - account_balance CFO: Cost breakdown, budget tracking
 * - architecture Architect: Real-time metric aggregation
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';

interface UsageMetric {
    label: string;
    current: number;
    limit: number;
    unit: string;
    percentage: number;
}

interface AgentUsage {
    id: string;
    name: string;
    requests: number;
    tokens: number;
    images: number;
    voice_minutes: number;
}

interface CostBreakdown {
    category: string;
    amount: number;
    details: string;
}

@customElement('saas-agent-metrics')
export class SaasAgentMetrics extends LitElement {
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
      display: flex;
      height: 100vh;
      background: var(--saas-bg-page, #0f0f0f);
      font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
      color: #fff;
    }

    * { box-sizing: border-box; }

    .sidebar { width: 260px; flex-shrink: 0; }
    .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

    .header {
      padding: 20px 32px;
      border-bottom: 1px solid #222;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .header-title { font-size: 22px; font-weight: 600; margin: 0; }
    .header-subtitle { font-size: 13px; color: #888; margin: 4px 0 0 0; }

    .date-range {
      padding: 8px 16px;
      background: #1a1a1a;
      border: 1px solid #333;
      border-radius: 8px;
      color: #fff;
      font-size: 13px;
    }

    .content { flex: 1; overflow-y: auto; padding: 32px; }

    /* Usage Cards */
    .usage-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-bottom: 32px;
    }

    .usage-card {
      background: linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%);
      border: 1px solid #222;
      border-radius: 12px;
      padding: 20px;
    }

    .usage-label { font-size: 12px; color: #888; margin-bottom: 8px; }
    .usage-value { font-size: 24px; font-weight: 700; margin-bottom: 4px; }
    .usage-limit { font-size: 12px; color: #666; margin-bottom: 12px; }

    .progress-bar {
      height: 6px;
      background: #333;
      border-radius: 3px;
      overflow: hidden;
    }

    .progress-fill {
      height: 100%;
      border-radius: 3px;
      transition: width 0.3s ease;
    }

    .progress-fill.low { background: linear-gradient(90deg, #22c55e, #16a34a); }
    .progress-fill.medium { background: linear-gradient(90deg, #eab308, #ca8a04); }
    .progress-fill.high { background: linear-gradient(90deg, #ef4444, #dc2626); }

    .usage-percentage { font-size: 11px; color: #888; margin-top: 6px; text-align: right; }

    /* Sections */
    .section {
      background: #1a1a1a;
      border: 1px solid #222;
      border-radius: 12px;
      margin-bottom: 24px;
      overflow: hidden;
    }

    .section-header {
      padding: 16px 20px;
      border-bottom: 1px solid #222;
      font-weight: 600;
      font-size: 14px;
    }

    .section-content { padding: 20px; }

    /* Agent Table */
    .agent-table {
      width: 100%;
      border-collapse: collapse;
    }

    .agent-table th {
      text-align: left;
      padding: 12px;
      font-size: 12px;
      color: #888;
      font-weight: 500;
      border-bottom: 1px solid #333;
    }

    .agent-table td {
      padding: 12px;
      font-size: 13px;
      border-bottom: 1px solid #222;
    }

    .agent-name { font-weight: 500; }

    /* Cost Breakdown */
    .cost-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr) auto;
      gap: 16px;
    }

    .cost-item {
      background: #0d0d0d;
      border-radius: 8px;
      padding: 16px;
    }

    .cost-category { font-size: 12px; color: #888; margin-bottom: 4px; }
    .cost-amount { font-size: 20px; font-weight: 700; margin-bottom: 4px; }
    .cost-details { font-size: 11px; color: #666; }

    .cost-total {
      background: linear-gradient(135deg, #1a1a1a 0%, #262626 100%);
      border: 1px solid #333;
      border-radius: 8px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }

    .cost-total .cost-category { color: #888; }
    .cost-total .cost-amount { font-size: 28px; color: #22c55e; }

    /* Charts placeholder */
    .chart-container {
      height: 200px;
      background: #0d0d0d;
      border-radius: 8px;
      display: flex;
      align-items: flex-end;
      justify-content: space-around;
      padding: 16px;
      gap: 12px;
      color: #666;
    }

    .bar-chart-item {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: flex-end;
      height: 100%;
      min-width: 40px;
    }

    .bar-chart-bar {
      width: 100%;
      max-width: 60px;
      background: linear-gradient(180deg, #22c55e, #16a34a);
      border-radius: 4px 4px 0 0;
      min-height: 4px;
    }

    .bar-chart-label {
      font-size: 11px;
      color: #888;
      margin-top: 8px;
      text-align: center;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      width: 100%;
    }

    .bar-chart-value {
      font-size: 11px;
      color: #aaa;
      margin-bottom: 4px;
    }

    .loading { display: flex; justify-content: center; align-items: center; padding: 60px; color: #666; }

    .error-banner {
      padding: 12px 16px;
      background: rgba(239, 68, 68, 0.1);
      color: #fca5a5;
      border-radius: 8px;
      font-size: 14px;
      margin-bottom: 20px;
    }

    @media (max-width: 1200px) {
      .usage-grid { grid-template-columns: repeat(2, 1fr); }
      .cost-grid { grid-template-columns: repeat(2, 1fr); }
    }
  `;

    @state() private month = new Date().toISOString().slice(0, 7);
    @state() private loading = true;
    @state() private usage: UsageMetric[] = [];
    @state() private agents: AgentUsage[] = [];
    @state() private costs: CostBreakdown[] = [];
    @state() private error = '';

    connectedCallback() {
        super.connectedCallback();
        this.loadMetrics();
    }

    private async loadMetrics() {
        this.loading = true;
        this.error = '';
        try {
            const monthQuery = this.month ? `?month=${encodeURIComponent(this.month)}` : '';
            const data = await apiClient.get<{ usage?: UsageMetric[]; agents?: AgentUsage[]; costs?: CostBreakdown[] }>(`/observability/tenant-usage${monthQuery}`);
            this.usage = data.usage || [];
            this.agents = data.agents || [];
            this.costs = data.costs || [];
        } catch (e) {
            this.error = 'Unable to load metrics. Please try again later.';
            this.usage = [];
            this.agents = [];
            this.costs = [];
        } finally {
            this.loading = false;
        }
    }

    private getProgressClass(percentage: number): string {
        if (percentage >= 80) return 'high';
        if (percentage >= 50) return 'medium';
        return 'low';
    }

    private formatNumber(num: number): string {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(0) + 'K';
        return num.toLocaleString();
    }

    private _renderUsageBarChart() {
        if (this.usage.length === 0) {
            return html`
                <div class="chart-container" style="align-items: center; justify-content: center;">
                    No usage data available
                </div>
            `;
        }
        const max = Math.max(...this.usage.map(u => u.current || 0), 1);
        return html`
            <div class="chart-container">
                ${this.usage.map(u => {
                    const height = Math.max((u.current / max) * 100, 4);
                    return html`
                        <div class="bar-chart-item" title="${u.label}: ${u.current}">
                            <div class="bar-chart-value">${this.formatNumber(u.current)}</div>
                            <div class="bar-chart-bar" style="height: ${height}%"></div>
                            <div class="bar-chart-label">${u.label}</div>
                        </div>
                    `;
                })}
            </div>
        `;
    }

    private get totalCost(): number {
        return this.costs.reduce((sum, c) => sum + c.amount, 0);
    }

    private _onMonthChange = (e: Event) => {
        this.month = (e.target as HTMLInputElement).value;
        void this.loadMetrics();
    };

    render() {
        return html`
      <aside class="sidebar">
        <saas-sidebar active-route="/admin/metrics"></saas-sidebar>
      </aside>

      <main class="main">
        <header class="header">
          <div>
            <h1 class="header-title"><span class="material-symbols-outlined">bar_chart</span> Agent Metrics</h1>
            <p class="header-subtitle">Usage and cost breakdown for your agents</p>
          </div>
          <input type="month" class="date-range" .value=${this.month} @change=${this._onMonthChange}>
        </header>

        <div class="content">
          ${this.error ? html`<div class="error-banner">${this.error}</div>` : ''}
          ${this.loading ? html`<div class="loading">Loading metrics...</div>` : html`
            <!-- Usage Summary -->
            <div class="usage-grid">
              ${this.usage.map(u => html`
                <div class="usage-card">
                  <div class="usage-label">${u.label}</div>
                  <div class="usage-value">${this.formatNumber(u.current)}</div>
                  <div class="usage-limit">/ ${this.formatNumber(u.limit)}${u.unit ? ' ' + u.unit : ''}</div>
                  <div class="progress-bar">
                    <div class="progress-fill ${this.getProgressClass(u.percentage)}" style="width: ${u.percentage}%"></div>
                  </div>
                  <div class="usage-percentage">${u.percentage}%</div>
                </div>
              `)}
            </div>

            <!-- Usage by Agent -->
            <div class="section">
              <div class="section-header">Usage by Agent</div>
              <div class="section-content">
                <table class="agent-table">
                  <thead>
                    <tr>
                      <th>Agent</th>
                      <th>Requests</th>
                      <th>Tokens</th>
                      <th>Images</th>
                      <th>Voice</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${this.agents.map(a => html`
                      <tr>
                        <td class="agent-name">${a.name}</td>
                        <td>${this.formatNumber(a.requests)}</td>
                        <td>${this.formatNumber(a.tokens)}</td>
                        <td>${a.images}</td>
                        <td>${a.voice_minutes} min</td>
                      </tr>
                    `)}
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Cost Breakdown -->
            <div class="section">
              <div class="section-header">Cost Breakdown (Estimated)</div>
              <div class="section-content">
                <div class="cost-grid">
                  ${this.costs.map(c => html`
                    <div class="cost-item">
                      <div class="cost-category">${c.category}</div>
                      <div class="cost-amount">$${c.amount.toFixed(2)}</div>
                      <div class="cost-details">${c.details}</div>
                    </div>
                  `)}
                  <div class="cost-total">
                    <div class="cost-category">Total</div>
                    <div class="cost-amount">$${this.totalCost.toFixed(2)}</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Usage Trend Chart -->
            <div class="section">
              <div class="section-header">Usage Trend (Last 30 Days)</div>
              <div class="section-content">
                ${this._renderUsageBarChart()}
              </div>
            </div>
          `}
        </div>
      </main>
    `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-agent-metrics': SaasAgentMetrics;
    }
}
