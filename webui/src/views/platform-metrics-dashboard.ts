/**
 * Platform Metrics Dashboard
 * Real-time observability for SomaAgent platform
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Real Prometheus metrics visualization
 * - Tab-based composition pattern
 * - Light theme, minimal, professional
 * - Material Symbols icons
 *
 * Metrics from:
 * - Django gateway (requests, latency)
 * - LLM calls (tokens, latency, costs)
 * - Tools (execution time, success rate)
 * - Memory (SomaBrain operations)
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import {
  PlatformMetricsController,
  type MetricSnapshot,
  type SLAStatus,
} from '../controllers/platform-metrics-controller.js';
import '../components/saas-platform-metrics-tenant-panel.js';
import '../components/saas-platform-metrics-llm-panel.js';
import '../components/saas-platform-metrics-tools-panel.js';

@customElement('saas-platform-metrics-dashboard')
export class PlatformMetricsDashboard extends LitElement {
  static styles = css`
    :host {
      display: flex;
      height: 100vh;
      background: var(--saas-bg-page, #f5f5f5);
      font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
      color: var(--saas-text-primary, #1a1a1a);
    }

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

    /* Sidebar */
    .sidebar {
      width: 260px;
      background: var(--saas-bg-card, #ffffff);
      border-right: 1px solid var(--saas-border-light, #e0e0e0);
      flex-shrink: 0;
    }

    /* Main Content */
    .main {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .header {
      padding: 20px 32px;
      background: var(--saas-bg-card, #ffffff);
      border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .header-title { font-size: 22px; font-weight: 600; margin: 0; }
    .header-subtitle { font-size: 13px; color: var(--saas-text-muted, #999); margin: 4px 0 0 0; }

    .header-actions { display: flex; gap: 12px; align-items: center; }

    .time-range {
      font-size: 12px;
      padding: 8px 14px;
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: 8px;
      background: var(--saas-bg-card, #ffffff);
      cursor: pointer;
    }

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
    }

    .btn:hover { background: var(--saas-bg-hover, #fafafa); }

    /* Tabs */
    .tabs {
      display: flex;
      padding: 0 32px;
      background: var(--saas-bg-card, #ffffff);
      border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
    }

    .tab {
      padding: 14px 20px;
      cursor: pointer;
      font-size: 13px;
      font-weight: 500;
      color: var(--saas-text-secondary, #666);
      border-bottom: 2px solid transparent;
      margin-bottom: -1px;
    }

    .tab:hover { color: var(--saas-text-primary, #1a1a1a); }
    .tab.active {
      color: var(--saas-text-primary, #1a1a1a);
      border-bottom-color: #1a1a1a;
    }

    .content {
      flex: 1;
      overflow-y: auto;
      padding: 32px;
    }

    /* Metrics Grid */
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

    /* SLA Grid */
    .sla-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
    }

    .sla-card {
      background: var(--saas-bg-card, #ffffff);
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: 12px;
      padding: 20px;
    }

    .sla-name {
      font-size: 13px;
      font-weight: 500;
      margin-bottom: 12px;
    }

    .sla-value {
      font-size: 28px;
      font-weight: 700;
      margin-bottom: 4px;
    }

    .sla-value.ok { color: #22c55e; }
    .sla-value.warning { color: #f59e0b; }
    .sla-value.critical { color: #ef4444; }

    .sla-target {
      font-size: 12px;
      color: var(--saas-text-muted, #999);
    }

    /* Loading */
    .loading {
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 60px;
      color: var(--saas-text-muted, #999);
    }
  `;

  @state() metrics: MetricSnapshot | null = null;
  @state() sla: SLAStatus[] = [];
  @state() loading = true;
  @state() activeTab: 'overview' | 'llm' | 'tools' | 'memory' | 'sla' = 'overview';
  @state() lastRefresh: Date | null = null;

  private controller = new PlatformMetricsController(this);

  connectedCallback() {
    super.connectedCallback();
    this.controller.connect();
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    this.controller.disconnect();
  }

  render() {
    return html`
      <aside class="sidebar">
        <saas-sidebar active-route="/platform/metrics"></saas-sidebar>
      </aside>

      <main class="main">
        <header class="header">
          <div>
            <h1 class="header-title">Platform Metrics</h1>
            <p class="header-subtitle">Real-time observability dashboard</p>
          </div>
          <div class="header-actions">
            <select class="time-range">
              <option value="1h">Last 1 hour</option>
              <option value="24h" selected>Last 24 hours</option>
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
            </select>
            ${this.lastRefresh ? html`
              <span style="font-size: 11px; color: var(--saas-text-muted, #999);">
                ${this.lastRefresh.toLocaleTimeString()}
              </span>
            ` : nothing}
            <button class="btn" @click=${() => this.controller.fetchMetrics()}>
              <span class="material-symbols-outlined">refresh</span>
              Refresh
            </button>
          </div>
        </header>

        <div class="tabs">
          <div class="tab ${this.activeTab === 'overview' ? 'active' : ''}" @click=${() => this.activeTab = 'overview'}>
            Overview
          </div>
          <div class="tab ${this.activeTab === 'llm' ? 'active' : ''}" @click=${() => this.activeTab = 'llm'}>
            LLM
          </div>
          <div class="tab ${this.activeTab === 'tools' ? 'active' : ''}" @click=${() => this.activeTab = 'tools'}>
            Tools
          </div>
          <div class="tab ${this.activeTab === 'memory' ? 'active' : ''}" @click=${() => this.activeTab = 'memory'}>
            Memory
          </div>
          <div class="tab ${this.activeTab === 'sla' ? 'active' : ''}" @click=${() => this.activeTab = 'sla'}>
            SLA
          </div>
        </div>

        <div class="content">
          ${this.loading ? html`<div class="loading">Loading metrics...</div>` : nothing}
          ${!this.loading && this.activeTab === 'overview' ? html`
            <saas-platform-metrics-tenant-panel .metrics=${this.metrics}></saas-platform-metrics-tenant-panel>
          ` : nothing}
          ${!this.loading && this.activeTab === 'llm' ? html`
            <saas-platform-metrics-llm-panel .metrics=${this.metrics}></saas-platform-metrics-llm-panel>
          ` : nothing}
          ${!this.loading && this.activeTab === 'tools' ? html`
            <saas-platform-metrics-tools-panel .metrics=${this.metrics}></saas-platform-metrics-tools-panel>
          ` : nothing}
          ${!this.loading && this.activeTab === 'memory' ? this.renderMemory() : nothing}
          ${!this.loading && this.activeTab === 'sla' ? this.renderSLA() : nothing}
        </div>
      </main>
    `;
  }

  private renderMemory() {
    if (!this.metrics) return nothing;
    const m = this.metrics.memory;

    return html`
      <div class="metrics-grid">
        <div class="metric-card featured">
          <div class="metric-header">
            <span class="metric-label">Operations</span>
            <div class="metric-icon"><span class="material-symbols-outlined">neurology</span></div>
          </div>
          <div class="metric-value">${this.formatNumber(m.operations_total)}</div>
          <div class="metric-sub">memory operations</div>
        </div>
        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-label">WAL Lag</span>
            <div class="metric-icon"><span class="material-symbols-outlined">sync</span></div>
          </div>
          <div class="metric-value">${m.wal_lag_seconds}s</div>
          <div class="metric-sub">replication lag</div>
        </div>
        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-label">Persistence</span>
            <div class="metric-icon"><span class="material-symbols-outlined">save</span></div>
          </div>
          <div class="metric-value">${m.persistence_avg_ms}ms</div>
          <div class="metric-sub">avg write time</div>
        </div>
        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-label">Policy Checks</span>
            <div class="metric-icon"><span class="material-symbols-outlined">policy</span></div>
          </div>
          <div class="metric-value">${this.formatNumber(m.policy_decisions)}</div>
          <div class="metric-sub">authorization checks</div>
        </div>
      </div>
    `;
  }

  private renderSLA() {
    return html`
      <div class="sla-grid">
        ${this.sla.map(s => html`
          <div class="sla-card">
            <div class="sla-name">${s.name}</div>
            <div class="sla-value ${s.status}">${s.actual.toFixed(2)}%</div>
            <div class="sla-target">Target: ${s.target}%</div>
          </div>
        `)}
      </div>
    `;
  }

  private formatNumber(n: number): string {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
    return n.toLocaleString();
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'saas-platform-metrics-dashboard': PlatformMetricsDashboard;
  }
}
