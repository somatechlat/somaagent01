/**
 * Infrastructure Dashboard - Soma Platform Admin
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Matches existing SOMA design system (tokens.css)
 * - Light theme, minimal, professional
 * - Google Material Symbols icons (NO EMOJIS)
 * - Sidebar + Header pattern
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import {
  InfraDashboardController,
  type InfrastructureHealth,
  type RateLimitPolicy,
  type DegradationStatus,
  type ComponentHealth,
  type ServiceDependency,
  type HistoryRecord,
} from '../controllers/infra-dashboard-controller.js';
import '../components/soma-infra-status-card.js';
import { type InfraMetric } from '../components/soma-infra-metrics-chart.js';
import '../components/soma-infra-metrics-chart.js';
import '../components/soma-infra-alert-list.js';

@customElement('soma-infrastructure-dashboard')
export class SomaInfrastructureDashboard extends LitElement {
  @state() health: InfrastructureHealth | null = null;
  @state() rateLimits: RateLimitPolicy[] = [];
  @state() degradation: DegradationStatus | null = null;
  @state() components: ComponentHealth[] = [];
  @state() dependencies: ServiceDependency[] = [];
  @state() history: HistoryRecord[] = [];
  @state() loading = true;
  @state() error = '';
  /** Public so the router can open this dashboard on a named tab. */
  @property({ type: String }) activeTab: 'health' | 'ratelimits' | 'degradation' = 'health';
  @state() refreshing = false;
  @state() lastRefresh: Date | null = null;

  private controller = new InfraDashboardController(this);

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
      letter-spacing: normal;
      text-transform: none;
      display: inline-block;
      white-space: nowrap;
      word-wrap: normal;
      direction: ltr;
      -webkit-font-feature-settings: 'liga';
      -webkit-font-smoothing: antialiased;
    }

    /* Sidebar */
    .sidebar {
      width: 260px;
      background: var(--soma-bg-card, #ffffff);
      border-right: 1px solid var(--soma-border-light, #e0e0e0);
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
    }

    .sidebar-header {
      padding: 24px 20px;
      border-bottom: 1px solid var(--soma-border-light, #e0e0e0);
    }

    .logo {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .logo-icon {
      width: 36px;
      height: 36px;
      background: #1a1a1a;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .logo-icon .material-symbols-outlined {
      color: white;
      font-size: 18px;
    }

    .logo-text {
      font-size: 16px;
      font-weight: 600;
    }

    .logo-badge {
      font-size: 10px;
      padding: 2px 6px;
      background: #1a1a1a;
      color: white;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      font-weight: 600;
      margin-left: 4px;
    }

    .nav {
      flex: 1;
      padding: 16px 12px;
      overflow-y: auto;
    }

    .nav-section { margin-bottom: 24px; }

    .nav-section-title {
      font-size: 10px;
      font-weight: 600;
      color: var(--soma-text-muted, #999);
      text-transform: uppercase;
      letter-spacing: 1px;
      padding: 0 12px;
      margin-bottom: 8px;
    }

    .nav-list {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .nav-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 11px 14px;
      border-radius: 8px;
      font-size: 14px;
      color: var(--soma-text-secondary, #666);
      cursor: pointer;
      transition: all 0.1s ease;
      text-decoration: none;
    }

    .nav-item:hover {
      background: var(--soma-bg-hover, #fafafa);
      color: var(--soma-text-primary, #1a1a1a);
    }

    .nav-item.active {
      background: var(--soma-bg-active, #f0f0f0);
      color: var(--soma-text-primary, #1a1a1a);
      font-weight: 500;
    }

    .nav-item .material-symbols-outlined { font-size: 18px; }

    /* Main content */
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

    .header-left { display: flex; align-items: center; gap: 16px; }
    .header-title { font-size: 22px; font-weight: 600; margin: 0; }
    .header-subtitle { font-size: 13px; color: var(--soma-text-muted, #999); margin: 0; }

    .header-actions { display: flex; gap: 12px; align-items: center; }

    .last-refresh {
      font-size: 11px;
      color: var(--soma-text-muted, #999);
      font-family: var(--soma-font-mono, monospace);
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
      color: var(--soma-text-primary, #1a1a1a);
    }

    .btn:hover { background: var(--soma-bg-hover, #fafafa); }

    .btn.primary {
      background: #1a1a1a;
      color: white;
      border-color: #1a1a1a;
    }

    .btn.primary:hover { background: #333; }

    .btn .material-symbols-outlined { font-size: 16px; }

    .btn.spinning .material-symbols-outlined {
      animation: spin 1s linear infinite;
    }

    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }

    .tabs {
      display: flex;
      gap: 0;
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
      transition: all 0.1s ease;
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

    .section-title {
      font-size: 15px;
      font-weight: 600;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .section-title .material-symbols-outlined {
      font-size: 18px;
      color: var(--soma-text-secondary, #666);
    }

    .services-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 16px;
    }

    .component-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
      gap: 16px;
      margin-bottom: 32px;
    }

    /* Rate limits table */
    .card {
      background: var(--soma-bg-card, #ffffff);
      border: 1px solid var(--soma-border-light, #e0e0e0);
      border-radius: 12px;
    }

    .card-header {
      padding: 20px 24px;
      border-bottom: 1px solid var(--soma-border-light, #e0e0e0);
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
      color: var(--soma-text-secondary, #666);
    }

    table {
      width: 100%;
      border-collapse: collapse;
    }

    th {
      text-align: left;
      padding: 14px 20px;
      font-size: 11px;
      font-weight: 600;
      color: var(--soma-text-muted, #999);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      border-bottom: 1px solid var(--soma-border-light, #e0e0e0);
    }

    td {
      padding: 16px 20px;
      font-size: 14px;
      border-bottom: 1px solid var(--soma-border-light, #e0e0e0);
    }

    tr:last-child td { border-bottom: none; }
    tr:hover td { background: var(--soma-bg-hover, #fafafa); }

    .policy-badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
    }

    .policy-badge.HARD { background: rgba(239, 68, 68, 0.15); color: #dc2626; }
    .policy-badge.SOFT { background: rgba(245, 158, 11, 0.15); color: #d97706; }
    .policy-badge.NONE { background: #f3f4f6; color: #6b7280; }

    .tier-tags { display: flex; gap: 4px; flex-wrap: wrap; }

    .tier-tag {
      font-size: 10px;
      padding: 2px 6px;
      background: #f3f4f6;
      border-radius: 4px;
      color: #374151;
      font-family: var(--soma-font-mono, monospace);
    }

    .active-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--soma-status-success, #22c55e);
    }

    .active-dot.inactive { background: #e5e7eb; }

    .loading {
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 60px;
      color: var(--soma-text-muted, #999);
    }

    .empty-state {
      text-align: center;
      padding: 40px;
      color: var(--soma-text-muted, #999);
    }
  `;

  connectedCallback() {
    super.connectedCallback();
    this.controller.connect();
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    this.controller.disconnect();
  }

  fetchData(): Promise<void> {
    return this.controller.fetchData();
  }

  fetchHealth(): Promise<void> {
    return this.controller.fetchHealth();
  }

  fetchRateLimits(): Promise<void> {
    return this.controller.fetchRateLimits();
  }

  fetchDegradation(): Promise<void> {
    return this.controller.fetchDegradation();
  }

  seedRateLimits(): Promise<void> {
    return this.controller.seedRateLimits();
  }

  private navigate(path: string) {
    window.dispatchEvent(new CustomEvent('soma-navigate', { detail: { route: path } }));
  }

  render() {
    return html`
      <aside class="sidebar">
        <div class="sidebar-header">
          <div class="logo">
            <div class="logo-icon">
              <span class="material-symbols-outlined">visibility</span>
            </div>
            <span class="logo-text">SomaAgent<span class="logo-badge">God</span></span>
          </div>
        </div>

        <nav class="nav">
          <div class="nav-section">
            <div class="nav-section-title">Overview</div>
            <div class="nav-list">
              <a class="nav-item" href="/soma/dashboard">
                <span class="material-symbols-outlined">visibility</span>
                Dashboard
              </a>
            </div>
          </div>

          <div class="nav-section">
            <div class="nav-section-title">Infrastructure</div>
            <div class="nav-list">
              <a class="nav-item active" href="/platform/infrastructure">
                <span class="material-symbols-outlined">dns</span>
                Services
              </a>
              <a class="nav-item" href="/platform/permissions">
                <span class="material-symbols-outlined">admin_panel_settings</span>
                Permissions
              </a>
            </div>
          </div>
        </nav>
      </aside>

      <main class="main">
        <header class="header">
          <div class="header-left">
            <div>
              <h1 class="header-title">Infrastructure</h1>
              <p class="header-subtitle">Service health and rate limiting</p>
            </div>
          </div>
          <div class="header-actions">
            ${this.lastRefresh ? html`
              <span class="last-refresh">${this.lastRefresh.toLocaleTimeString()}</span>
            ` : nothing}
            <button class="btn ${this.refreshing ? 'spinning' : ''}" @click=${() => this.fetchData()}>
              <span class="material-symbols-outlined">refresh</span>
              Refresh
            </button>
          </div>
        </header>

        <div class="tabs">
          <div class="tab ${this.activeTab === 'health' ? 'active' : ''}" @click=${() => this.activeTab = 'health'}>
            Service Health
          </div>
          <div class="tab ${this.activeTab === 'ratelimits' ? 'active' : ''}" @click=${() => this.activeTab = 'ratelimits'}>
            Rate Limits
          </div>
          <div class="tab ${this.activeTab === 'degradation' ? 'active' : ''}" @click=${() => this.activeTab = 'degradation'}>
            Degradation Mode
          </div>
        </div>

        <div class="content">
          ${this.loading ? html`<div class="loading">Loading...</div>` : nothing}
          ${!this.loading && this.activeTab === 'health' ? this.renderHealth() : nothing}
          ${!this.loading && this.activeTab === 'ratelimits' ? this.renderRateLimits() : nothing}
          ${!this.loading && this.activeTab === 'degradation' ? this.renderDegradation() : nothing}
        </div>
      </main>
    `;
  }

  private get healthMetrics(): InfraMetric[] {
    if (!this.health) return [];
    const h = this.health.services.filter(s => s.status === 'healthy').length;
    const d = this.health.services.filter(s => s.status === 'degraded').length;
    const x = this.health.services.filter(s => s.status === 'down').length;
    return [
      { label: 'Overall Status', value: this.health.overall_status.toUpperCase(), sub: `${this.health.duration_ms.toFixed(0)}ms check time`, icon: 'monitoring', featured: true },
      { label: 'Healthy', value: String(h), sub: 'services operational', icon: 'check_circle', statusClass: 'healthy' },
      { label: 'Degraded', value: String(d), sub: 'services degraded', icon: 'warning', statusClass: 'degraded' },
      { label: 'Down', value: String(x), sub: 'services down', icon: 'error', statusClass: 'down' },
    ];
  }

  private get degradationMetrics(): InfraMetric[] {
    if (!this.degradation) return [];
    const level = this.degradation.overall_level;
    const healthy = this.degradation.healthy_components.length;
    const affected = this.degradation.affected_components.length;
    return [
      { label: 'Degradation Level', value: html`<span class="deg-badge ${level}">${level.toUpperCase()}</span>`, sub: 'System status assessment', icon: 'thermostat', featured: true },
      { label: 'Healthy', value: String(healthy), sub: 'components operational', icon: 'check_circle', statusClass: 'healthy' },
      { label: 'Affected', value: String(affected), sub: 'components impacted', icon: 'warning', statusClass: affected > 0 ? 'degraded' : '' },
      { label: 'Total', value: String(this.degradation.total_components), sub: 'monitored components', icon: 'grid_view' },
    ];
  }

  private renderHealth() {
    if (!this.health) return html`<div class="empty-state">No health data</div>`;

    return html`
      <soma-infra-metrics-chart .metrics=${this.healthMetrics}></soma-infra-metrics-chart>

      <h3 class="section-title">
        <span class="material-symbols-outlined">dns</span>
        Service Details
      </h3>

      <div class="services-grid">
        ${this.health.services.map(s => html`
          <soma-infra-status-card .service=${s}></soma-infra-status-card>
        `)}
      </div>
    `;
  }

  private renderRateLimits() {
    return html`
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            <span class="material-symbols-outlined">speed</span>
            Rate Limit Policies
          </h3>
          <button class="btn primary" @click=${() => this.seedRateLimits()}>
            <span class="material-symbols-outlined">add</span>
            Seed Defaults
          </button>
        </div>
        <table>
          <thead>
            <tr>
              <th>Key</th>
              <th>Description</th>
              <th>Limit</th>
              <th>Window</th>
              <th>Policy</th>
              <th>Tiers</th>
              <th>Active</th>
            </tr>
          </thead>
          <tbody>
            ${this.rateLimits.length === 0 ? html`
              <tr><td colspan="7" class="empty-state">No rate limits. Click Seed Defaults.</td></tr>
            ` : this.rateLimits.map(l => html`
              <tr>
                <td><strong>${l.key}</strong></td>
                <td>${l.description}</td>
                <td>${l.limit.toLocaleString()}</td>
                <td>${l.window_display}</td>
                <td><span class="policy-badge ${l.policy}">${l.policy}</span></td>
                <td>
                  <div class="tier-tags">
                    ${Object.entries(l.tier_overrides || {}).map(([t, v]) => html`
                      <span class="tier-tag">${t}: ${(v as number).toLocaleString()}</span>
                    `)}
                  </div>
                </td>
                <td><span class="active-dot ${l.is_active ? '' : 'inactive'}"></span></td>
              </tr>
            `)}
          </tbody>
        </table>
      </div>
    `;
  }

  private renderDegradation() {
    if (!this.degradation) return html`<div class="empty-state">No degradation data</div>`;

    return html`
      <soma-infra-metrics-chart .metrics=${this.degradationMetrics}></soma-infra-metrics-chart>

      <h3 class="section-title">
        <span class="material-symbols-outlined">memory</span>
        Component Health
      </h3>
      <div class="component-grid">
        ${this.components.map(c => html`
          <soma-infra-status-card .component=${c}></soma-infra-status-card>
        `)}
      </div>

      <soma-infra-alert-list
        .recommendations=${this.degradation.recommendations}
        .mitigationActions=${this.degradation.mitigation_actions}
        .history=${this.history}
      ></soma-infra-alert-list>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'soma-infrastructure-dashboard': SomaInfrastructureDashboard;
  }
}
