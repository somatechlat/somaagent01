/**
 * Tenant / Cost Metrics Panel
 * Renders the overview tab of the platform metrics dashboard.
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { MetricSnapshot } from '../controllers/platform-metrics-controller.js';

@customElement('saas-platform-metrics-tenant-panel')
export class SaasPlatformMetricsTenantPanel extends LitElement {
  @property({ attribute: false }) metrics: MetricSnapshot | null = null;

  static styles = css`
    :host { display: block; }
    * { box-sizing: border-box; }

    .material-symbols-outlined {
      font-family: 'Material Symbols Outlined';
      font-weight: normal;
      font-style: normal;
      font-size: 20px;
      line-height: 1;
      display: inline-block;
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

    .metric-value {
      font-size: 32px;
      font-weight: 700;
      line-height: 1;
      margin-bottom: 8px;
    }

    .metric-sub {
      font-size: 12px;
      color: var(--saas-text-muted, #999);
    }

    .metric-card.featured {
      background: linear-gradient(135deg, #1a1a1a 0%, #333 100%);
      color: white;
    }

    .metric-card.featured .metric-label { color: rgba(255,255,255,0.7); }
    .metric-card.featured .metric-icon { background: rgba(255,255,255,0.15); }
    .metric-card.featured .metric-icon .material-symbols-outlined { color: white; }
    .metric-card.featured .metric-sub { color: rgba(255,255,255,0.6); }

    .latency-section {
      background: var(--saas-bg-card, #ffffff);
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: 12px;
      padding: 24px;
    }

    .section-title {
      font-size: 15px;
      font-weight: 600;
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .section-title .material-symbols-outlined {
      font-size: 18px;
      color: var(--saas-text-secondary, #666);
    }

    .latency-row {
      display: flex;
      align-items: center;
      margin-bottom: 16px;
    }

    .latency-row:last-child { margin-bottom: 0; }

    .latency-label {
      width: 120px;
      font-size: 13px;
      font-weight: 500;
    }

    .latency-values {
      display: flex;
      gap: 20px;
      flex: 1;
      font-size: 12px;
      color: var(--saas-text-muted, #999);
    }

    .latency-bar {
      flex: 1;
      height: 8px;
      background: var(--saas-bg-hover, #fafafa);
      border-radius: 4px;
      overflow: hidden;
    }

    .latency-bar-fill {
      height: 100%;
      background: #1a1a1a;
      border-radius: 4px;
    }
  `;

  render() {
    if (!this.metrics) return nothing;
    const m = this.metrics;

    return html`
      <div class="metrics-grid">
        <div class="metric-card featured">
          <div class="metric-header">
            <span class="metric-label">Uptime</span>
            <div class="metric-icon"><span class="material-symbols-outlined">timer</span></div>
          </div>
          <div class="metric-value">${this.formatUptime(m.system.uptime_seconds)}</div>
          <div class="metric-sub">${(m.system.cpu_percent).toFixed(0)}% CPU</div>
        </div>
        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-label">API Requests</span>
            <div class="metric-icon"><span class="material-symbols-outlined">api</span></div>
          </div>
          <div class="metric-value">${this.formatNumber(m.gateway.requests_total)}</div>
          <div class="metric-sub">${m.gateway.requests_per_minute}/min</div>
        </div>
        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-label">LLM Calls</span>
            <div class="metric-icon"><span class="material-symbols-outlined">psychology</span></div>
          </div>
          <div class="metric-value">${this.formatNumber(m.llm.calls_total)}</div>
          <div class="metric-sub">$${m.llm.cost_estimate_usd.toFixed(0)} estimated</div>
        </div>
        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-label">Tool Executions</span>
            <div class="metric-icon"><span class="material-symbols-outlined">build</span></div>
          </div>
          <div class="metric-value">${this.formatNumber(m.tools.executions_total)}</div>
          <div class="metric-sub">${(m.tools.success_rate * 100).toFixed(0)}% success</div>
        </div>
      </div>

      <div class="latency-section">
        <h3 class="section-title">
          <span class="material-symbols-outlined">speed</span>
          Latency Distribution
        </h3>
        <div class="latency-row">
          <span class="latency-label">Gateway</span>
          <div class="latency-bar">
            <div class="latency-bar-fill" style="width: ${Math.min(m.gateway.latency_p99_ms / 500 * 100, 100)}%"></div>
          </div>
          <div class="latency-values">
            <span>p50: ${m.gateway.latency_p50_ms}ms</span>
            <span>p95: ${m.gateway.latency_p95_ms}ms</span>
            <span>p99: ${m.gateway.latency_p99_ms}ms</span>
          </div>
        </div>
        <div class="latency-row">
          <span class="latency-label">LLM</span>
          <div class="latency-bar">
            <div class="latency-bar-fill" style="width: ${Math.min(m.llm.avg_latency_ms / 5000 * 100, 100)}%"></div>
          </div>
          <div class="latency-values">
            <span>avg: ${m.llm.avg_latency_ms}ms</span>
          </div>
        </div>
        <div class="latency-row">
          <span class="latency-label">Tools</span>
          <div class="latency-bar">
            <div class="latency-bar-fill" style="width: ${Math.min(m.tools.avg_duration_ms / 2000 * 100, 100)}%"></div>
          </div>
          <div class="latency-values">
            <span>avg: ${m.tools.avg_duration_ms}ms</span>
          </div>
        </div>
        <div class="latency-row">
          <span class="latency-label">Memory</span>
          <div class="latency-bar">
            <div class="latency-bar-fill" style="width: ${Math.min(m.memory.persistence_avg_ms / 100 * 100, 100)}%"></div>
          </div>
          <div class="latency-values">
            <span>persist: ${m.memory.persistence_avg_ms}ms</span>
            <span>WAL lag: ${m.memory.wal_lag_seconds}s</span>
          </div>
        </div>
      </div>
    `;
  }

  private formatNumber(n: number): string {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
    return n.toLocaleString();
  }

  private formatUptime(seconds: number): string {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    return `${days}d ${hours}h`;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'saas-platform-metrics-tenant-panel': SaasPlatformMetricsTenantPanel;
  }
}
