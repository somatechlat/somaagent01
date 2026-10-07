/**
 * Platform Metrics Dashboard
 * Real-time observability for SomaAgent platform
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Renders exactly what /observability/metrics/json returns
 * - Tab-based composition pattern
 * - Light theme, minimal, professional
 * - Material Symbols icons
 *
 * Server contract (admin/observability/api.py:325-356, :365-403):
 *   GET /metrics/json -> MetricsJsonResponse{metrics: list[MetricValue]}
 *     MetricValue = {name, value, labels?, timestamp}
 *   GET /sla -> {timestamp, metrics:[{name, target, actual, status}],
 *                overall_status}
 *     status is "pass" | "fail". No nested gateway/llm/tools/memory/system
 *     snapshot exists — a nested shape was invented here and every tile was
 *     a fabricated number.
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';

/** Matches admin/observability/api.py MetricValue. */
interface MetricValue {
  name: string;
  value: number;
  labels?: Record<string, string> | null;
  timestamp: string;
}

/** Matches the /sla payload row. `target` is omitted from the UI: the server
 *  hardcodes 99.9 and 80.0 and both rows compute healthy/total — one number
 *  presented as two SLAs. Targets are not sourced from an operator setting. */
interface SlaRow {
  name: string;
  /** Present only when the server sent a number. Never defaulted. */
  actual?: number;
  status: 'pass' | 'fail';
}

@customElement('platform-metrics-dashboard')
export class PlatformMetricsDashboard extends LitElement {
  static styles = css`
    :host {
      display: flex;
      height: 100vh;
      background: var(--soma-bg-page, #f5f5f5);
      font-family: var(--soma-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
      color: var(--soma-text-primary, #1a1a1a);
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
      background: var(--soma-bg-card, #ffffff);
      border-right: 1px solid var(--soma-border-light, #e0e0e0);
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
      background: var(--soma-bg-card, #ffffff);
      border-bottom: 1px solid var(--soma-border-light, #e0e0e0);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .header-title { font-size: 22px; font-weight: 600; margin: 0; }
    .header-subtitle { font-size: 13px; color: var(--soma-text-muted, #999); margin: 4px 0 0 0; }

    .header-actions { display: flex; gap: 12px; align-items: center; }

    .time-range {
      font-size: 12px;
      padding: 8px 14px;
      border: 1px solid var(--soma-border-light, #e0e0e0);
      border-radius: 8px;
      background: var(--soma-bg-card, #ffffff);
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
      border: 1px solid var(--soma-border-light, #e0e0e0);
      background: var(--soma-bg-card, #ffffff);
    }

    .btn:hover { background: var(--soma-bg-hover, #fafafa); }

    /* Tabs */
    .tabs {
      display: flex;
      padding: 0 32px;
      background: var(--soma-bg-card, #ffffff);
      border-bottom: 1px solid var(--soma-border-light, #e0e0e0);
    }

    .tab {
      padding: 14px 20px;
      cursor: pointer;
      font-size: 13px;
      font-weight: 500;
      color: var(--soma-text-secondary, #666);
      border-bottom: 2px solid transparent;
      margin-bottom: -1px;
    }

    .tab:hover { color: var(--soma-text-primary, #1a1a1a); }
    .tab.active {
      color: var(--soma-text-primary, #1a1a1a);
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
      background: var(--soma-bg-card, #ffffff);
      border: 1px solid var(--soma-border-light, #e0e0e0);
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
      color: var(--soma-text-secondary, #666);
      font-weight: 500;
    }

    .metric-icon {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      background: var(--soma-bg-hover, #fafafa);
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
      color: var(--soma-text-muted, #999);
    }

    .metric-card.featured {
      background: linear-gradient(135deg, #1a1a1a 0%, #333 100%);
      color: white;
    }

    .metric-card.featured .metric-label { color: rgba(255,255,255,0.7); }
    .metric-card.featured .metric-icon { background: rgba(255,255,255,0.15); }
    .metric-card.featured .metric-icon .material-symbols-outlined { color: white; }
    .metric-card.featured .metric-sub { color: rgba(255,255,255,0.6); }

    /* Latency Bar */
    .latency-section {
      background: var(--soma-bg-card, #ffffff);
      border: 1px solid var(--soma-border-light, #e0e0e0);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
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
      color: var(--soma-text-secondary, #666);
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
      color: var(--soma-text-muted, #999);
    }

    .latency-bar {
      flex: 1;
      height: 8px;
      background: var(--soma-bg-hover, #fafafa);
      border-radius: 4px;
      overflow: hidden;
    }

    .latency-bar-fill {
      height: 100%;
      background: #1a1a1a;
      border-radius: 4px;
    }

    /* SLA Table */
    .sla-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
    }

    .sla-card {
      background: var(--soma-bg-card, #ffffff);
      border: 1px solid var(--soma-border-light, #e0e0e0);
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

    .sla-value.pass { color: #22c55e; }
    .sla-value.fail { color: #ef4444; }

    .sla-status-row {
      font-size: 12px;
      color: var(--soma-text-muted, #999);
    }

    .sla-status {
      text-transform: uppercase;
      font-weight: 600;
      letter-spacing: 0.04em;
    }

    .sla-status.pass { color: #22c55e; }
    .sla-status.fail { color: #ef4444; }

    .metric-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }

    .metric-table th,
    .metric-table td {
      text-align: left;
      padding: 8px 12px;
      border-bottom: 1px solid var(--soma-border-light, #e0e0e0);
    }

    .metric-table th {
      font-weight: 600;
      color: var(--soma-text-secondary, #666);
    }

    .metric-name {
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 12px;
    }

    .empty-note {
      margin: 0;
      padding: 16px;
      color: var(--soma-text-muted, #999);
      font-size: 13px;
      line-height: 1.5;
    }

    /* Loading */
    .loading {
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 60px;
      color: var(--soma-text-muted, #999);
    }
  `;

  @state() private metrics: MetricValue[] = [];
  @state() private sla: SlaRow[] = [];
  @state() private loading = true;
  @state() private error: string | null = null;
  @state() private activeTab: 'overview' | 'llm' | 'tools' | 'memory' | 'sla' = 'overview';
  @state() private lastRefresh: Date | null = null;

  // No auto-poll. A refresh interval is latency policy and must come from a
  // named setting, never a call-site literal. The Refresh button is the only
  // trigger until an interval setting is wired.

  connectedCallback() {
    super.connectedCallback();
    this.fetchMetrics();
  }

  private async fetchMetrics() {
    this.error = null;
    try {
      // Mounted at /api/v2/observability (admin/api.py).
      // /metrics/json returns MetricsJsonResponse{metrics:[...]} — a flat
      // list of MetricValue. There is no nested snapshot shape.
      const [metricsRes, slaRes] = await Promise.all([
        fetch('/api/v2/observability/metrics/json', { credentials: 'include' }),
        fetch('/api/v2/observability/sla', { credentials: 'include' }),
      ]);

      if (metricsRes.ok) {
        const body = await metricsRes.json() as { metrics?: MetricValue[] };
        this.metrics = Array.isArray(body.metrics) ? body.metrics : [];
      } else {
        this.metrics = [];
        this.error = `Failed to load metrics (HTTP ${metricsRes.status})`;
      }

      if (slaRes.ok) {
        // /sla returns a WRAPPER object {timestamp, metrics, overall_status},
        // not an array. Rows use status "pass" | "fail".
        const body = await slaRes.json() as { metrics?: { name: string; actual: number; status: string }[] };
        const rows = Array.isArray(body.metrics) ? body.metrics : [];
        // The server emits two rows over the same healthy/total ratio
        // (api.py:384-403). Each row's own pass/fail verdict is kept under
        // its server name; the invented target column is not rendered.
        this.sla = rows.map(r => ({
          name: r.name,
          // A missing actual is not zero. Keep it absent.
          actual: typeof r.actual === 'number' ? r.actual : undefined,
          status: r.status === 'pass' ? 'pass' : 'fail',
        }));
      } else {
        this.sla = [];
        if (!this.error) this.error = `Failed to load SLA (HTTP ${slaRes.status})`;
      }

      this.lastRefresh = new Date();
    } catch (err) {
      console.error('Failed to fetch metrics:', err);
      this.metrics = [];
      this.sla = [];
      this.error = 'Failed to load metrics';
    } finally {
      this.loading = false;
    }
  }

  private formatNumber(n: number): string {
    // Compact notation from the platform locale. No hand-rolled
    // 1000/1000000 thresholds — those are call-site numbers.
    return new Intl.NumberFormat(undefined, { notation: 'compact' }).format(n);
  }

  /** Filter the flat metric list by a name prefix. No synthetic grouping. */
  private metricsNamed(prefix: string): MetricValue[] {
    return this.metrics.filter(m => m.name.startsWith(prefix));
  }

  private renderMetricRows(rows: MetricValue[]) {
    if (rows.length === 0) {
      return html`<p class="empty-note">No metrics with this name prefix were reported.</p>`;
    }
    return html`
      <table class="metric-table">
        <thead>
          <tr><th>Name</th><th>Value</th><th>Labels</th><th>Timestamp</th></tr>
        </thead>
        <tbody>
          ${rows.map(m => html`
            <tr>
              <td class="metric-name">${m.name}</td>
              <td>${this.formatNumber(m.value)}</td>
              <td>${m.labels && Object.keys(m.labels).length
                ? Object.entries(m.labels).map(([k, v]) => `${k}=${v}`).join(', ')
                : '—'}</td>
              <td>${m.timestamp || '—'}</td>
            </tr>
          `)}
        </tbody>
      </table>
    `;
  }

  render() {
    return html`
      <aside class="sidebar">
        <soma-sidebar active-route="/platform/metrics"></soma-sidebar>
      </aside>

      <main class="main">
        <header class="header">
          <div>
            <h1 class="header-title">Platform Metrics</h1>
            <p class="header-subtitle">Real-time observability dashboard</p>
          </div>
          <div class="header-actions">
            ${this.lastRefresh ? html`
              <span style="font-size: 11px; color: var(--soma-text-muted, #999);">
                ${this.lastRefresh.toLocaleTimeString()}
              </span>
            ` : nothing}
            <button class="btn" @click=${() => this.fetchMetrics()}>
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
          ${this.error ? html`<div class="loading">${this.error}</div>` : nothing}
          ${!this.loading && this.activeTab === 'overview' ? this.renderOverview() : nothing}
          ${!this.loading && this.activeTab === 'llm' ? this.renderLLM() : nothing}
          ${!this.loading && this.activeTab === 'tools' ? this.renderTools() : nothing}
          ${!this.loading && this.activeTab === 'memory' ? this.renderMemory() : nothing}
          ${!this.loading && this.activeTab === 'sla' ? this.renderSLA() : nothing}
        </div>
      </main>
    `;
  }

  private renderOverview() {
    if (this.metrics.length === 0) {
      return html`<p class="empty-note">No metrics were reported by the server.</p>`;
    }
    return html`
      <div class="latency-section">
        <h3 class="section-title">
          <span class="material-symbols-outlined">monitoring</span>
          All metrics
        </h3>
        ${this.renderMetricRows(this.metrics)}
      </div>
    `;
  }

  private renderLLM() {
    return html`
      <div class="latency-section">
        <h3 class="section-title">
          <span class="material-symbols-outlined">psychology</span>
          LLM metrics
        </h3>
        ${this.renderMetricRows(this.metricsNamed('llm'))}
      </div>
    `;
  }

  private renderTools() {
    return html`
      <div class="latency-section">
        <h3 class="section-title">
          <span class="material-symbols-outlined">build</span>
          Tool metrics
        </h3>
        ${this.renderMetricRows(this.metricsNamed('tool'))}
      </div>
    `;
  }

  private renderMemory() {
    return html`
      <div class="latency-section">
        <h3 class="section-title">
          <span class="material-symbols-outlined">neurology</span>
          Memory metrics
        </h3>
        ${this.renderMetricRows(this.metricsNamed('memory'))}
      </div>
    `;
  }

  private renderSLA() {
    if (this.sla.length === 0) {
      return html`<p class="empty-note">No SLA rows were reported by the server.</p>`;
    }
    // Both server rows are computed from the same healthy/total ratio
    // (api.py:384-403). They are shown under their server names with their
    // own pass/fail verdicts. The server's hardcoded targets (99.9, 80.0)
    // are not rendered — they are not sourced from any operator setting.
    return html`
      <div class="sla-grid">
        ${this.sla.map(s => html`
          <div class="sla-card">
            <div class="sla-name">${s.name}</div>
            <div class="sla-value ${s.status}">${s.actual === undefined ? '—' : s.actual}</div>
            <div class="sla-status-row">
              <span class="sla-status ${s.status}">${s.status}</span>
            </div>
          </div>
        `)}
      </div>
      <p class="empty-note">
        Both SLA rows are computed by the server from the same services-healthy
        ratio. No target column is shown: the server hardcodes its targets and
        no operator-configured SLA target is available.
      </p>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'platform-metrics-dashboard': PlatformMetricsDashboard;
  }
}
