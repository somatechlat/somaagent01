/**
 * Infrastructure Dashboard - SaaS Platform Admin Platform Admin
 * 
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Matches existing SAAS design system (tokens.css)
 * - Light theme, minimal, professional
 * - Google Material Symbols icons (NO EMOJIS)
 * - Sidebar + Header pattern per saas-platform-dashboard.ts
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';

interface ServiceHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'down';
  latency_ms: number | null;
  details: Record<string, any> | null;
  error: string | null;
}

interface InfrastructureHealth {
  overall_status: string;
  timestamp: string;
  duration_ms: number;
  services: ServiceHealth[];
}

interface RateLimitPolicy {
  id: string;
  key: string;
  description: string;
  limit: number;
  window_seconds: number;
  window_display: string;
  policy: 'HARD' | 'SOFT' | 'NONE';
  tier_overrides: Record<string, number>;
  is_active: boolean;
}

// Degradation monitoring types
interface DegradationStatus {
  overall_level: string;
  affected_components: string[];
  healthy_components: string[];
  total_components: number;
  timestamp: number;
  recommendations: string[];
  mitigation_actions: string[];
}

interface ComponentHealth {
  name: string;
  healthy: boolean;
  response_time: number;
  error_rate: number;
  degradation_level: string;
  circuit_state: string;
  last_check: number;
}

interface ServiceDependency {
  service: string;
  depends_on: string[];
  depended_by: string[];
}

interface HistoryRecord {
  timestamp: number;
  component_name: string;
  degradation_level: string;
  healthy: boolean;
  response_time: number;
  error_rate: number;
  event_type: string;
}

// Material Symbol names for each service
const SERVICE_ICONS: Record<string, string> = {
  postgresql: 'database',
  redis: 'bolt',
  kafka: 'mail',
  flink: 'stream',
  temporal: 'schedule',
  qdrant: 'psychology',
  keycloak: 'lock',
  lago: 'payments',
  somabrain: 'neurology',
  whisper: 'mic',
  kokoro: 'volume_up',
};

@customElement('saas-infrastructure-dashboard')
export class SaasInfrastructureDashboard extends LitElement {
  @state() health: InfrastructureHealth | null = null;
  @state() rateLimits: RateLimitPolicy[] = [];
  @state() degradation: DegradationStatus | null = null;
  @state() components: ComponentHealth[] = [];
  @state() dependencies: ServiceDependency[] = [];
  @state() history: HistoryRecord[] = [];
  @state() loading = true;
  @state() error = '';
  @state() activeTab: 'health' | 'ratelimits' | 'degradation' = 'health';
  @state() refreshing = false;
  @state() lastRefresh: Date | null = null;

  private pollInterval: number | null = null;

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
      letter-spacing: normal;
      text-transform: none;
      display: inline-block;
      white-space: nowrap;
      word-wrap: normal;
      direction: ltr;
      -webkit-font-feature-settings: 'liga';
      -webkit-font-smoothing: antialiased;
    }

    /* ========================================
       SIDEBAR - Minimal Navigation
       ======================================== */
    .sidebar {
      width: 260px;
      background: var(--saas-bg-card, #ffffff);
      border-right: 1px solid var(--saas-border-light, #e0e0e0);
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
    }

    .sidebar-header {
      padding: 24px 20px;
      border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
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
      color: var(--saas-text-muted, #999);
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
      color: var(--saas-text-secondary, #666);
      cursor: pointer;
      transition: all 0.1s ease;
      text-decoration: none;
    }

    .nav-item:hover {
      background: var(--saas-bg-hover, #fafafa);
      color: var(--saas-text-primary, #1a1a1a);
    }

    .nav-item.active {
      background: var(--saas-bg-active, #f0f0f0);
      color: var(--saas-text-primary, #1a1a1a);
      font-weight: 500;
    }

    .nav-item .material-symbols-outlined { font-size: 18px; }

    /* ========================================
       MAIN CONTENT
       ======================================== */
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

    .header-left { display: flex; align-items: center; gap: 16px; }
    .header-title { font-size: 22px; font-weight: 600; margin: 0; }
    .header-subtitle { font-size: 13px; color: var(--saas-text-muted, #999); margin: 0; }

    .header-actions { display: flex; gap: 12px; align-items: center; }

    .last-refresh {
      font-size: 11px;
      color: var(--saas-text-muted, #999);
      font-family: var(--saas-font-mono, monospace);
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
      color: var(--saas-text-primary, #1a1a1a);
    }

    .btn:hover { background: var(--saas-bg-hover, #fafafa); }

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

    /* Tabs */
    .tabs {
      display: flex;
      gap: 0;
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
      transition: all 0.1s ease;
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

    /* ========================================
       METRICS GRID
       ======================================== */
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

    .metric-value {
      font-size: 32px;
      font-weight: 700;
      line-height: 1;
      margin-bottom: 8px;
    }

    .metric-value.healthy { color: var(--saas-status-success, #22c55e); }
    .metric-value.degraded { color: var(--saas-status-warning, #f59e0b); }
    .metric-value.down { color: var(--saas-status-danger, #ef4444); }

    .metric-sub {
      font-size: 12px;
      color: var(--saas-text-muted, #999);
    }

    .metric-card.featured {
      background: linear-gradient(135deg, #1a1a1a 0%, #333 100%);
      color: white;
      border-color: #1a1a1a;
    }

    .metric-card.featured .metric-label { color: rgba(255,255,255,0.7); }
    .metric-card.featured .metric-icon { background: rgba(255,255,255,0.15); }
    .metric-card.featured .metric-icon .material-symbols-outlined { color: white; }
    .metric-card.featured .metric-sub { color: rgba(255,255,255,0.6); }
    .metric-card.featured .metric-value { color: white; }

    /* ========================================
       SERVICES GRID
       ======================================== */
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
      color: var(--saas-text-secondary, #666);
    }

    .services-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 16px;
    }

    .service-card {
      background: var(--saas-bg-card, #ffffff);
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: 12px;
      padding: 20px;
      transition: all 0.15s ease;
    }

    .service-card:hover {
      border-color: var(--saas-border-medium, #ccc);
      box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    }

    .service-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }

    .service-name {
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: 600;
      font-size: 14px;
      text-transform: capitalize;
    }

    .service-icon {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      background: var(--saas-bg-hover, #fafafa);
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .service-icon .material-symbols-outlined { font-size: 16px; }

    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
    }

    .status-badge.healthy {
      background: rgba(34, 197, 94, 0.15);
      color: #16a34a;
    }

    .status-badge.degraded {
      background: rgba(245, 158, 11, 0.15);
      color: #d97706;
    }

    .status-badge.down {
      background: rgba(239, 68, 68, 0.15);
      color: #dc2626;
    }

    .status-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
    }

    .status-dot.healthy { background: var(--saas-status-success, #22c55e); }
    .status-dot.degraded { background: var(--saas-status-warning, #f59e0b); }
    .status-dot.down { background: var(--saas-status-danger, #ef4444); }

    .service-details {
      font-size: 12px;
      color: var(--saas-text-muted, #999);
      margin-bottom: 8px;
    }

    .latency {
      font-size: 11px;
      font-family: var(--saas-font-mono, monospace);
      color: var(--saas-text-muted, #999);
    }

    .error-box {
      margin-top: 10px;
      padding: 10px;
      background: rgba(239, 68, 68, 0.08);
      border: 1px solid rgba(239, 68, 68, 0.2);
      border-radius: 6px;
      font-size: 11px;
      color: #dc2626;
    }

    /* ========================================
       TABLE
       ======================================== */
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

    table {
      width: 100%;
      border-collapse: collapse;
    }

    th {
      text-align: left;
      padding: 14px 20px;
      font-size: 11px;
      font-weight: 600;
      color: var(--saas-text-muted, #999);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
    }

    td {
      padding: 16px 20px;
      font-size: 14px;
      border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
    }

    tr:last-child td { border-bottom: none; }
    tr:hover td { background: var(--saas-bg-hover, #fafafa); }

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
      font-family: var(--saas-font-mono, monospace);
    }

    .active-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--saas-status-success, #22c55e);
    }

    .active-dot.inactive { background: #e5e7eb; }

    /* Loading */
    .loading {
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 60px;
      color: var(--saas-text-muted, #999);
    }

    .empty-state {
      text-align: center;
      padding: 40px;
      color: var(--saas-text-muted, #999);
    }

    /* ========================================
       DEGRADATION LEVEL STYLES
       ======================================== */
    .deg-none { color: #22c55e; }
    .deg-minor { color: #84cc16; }
    .deg-moderate { color: #f59e0b; }
    .deg-severe { color: #f97316; }
    .deg-critical { color: #ef4444; }

    .deg-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
    }

    .deg-badge.none { background: rgba(34, 197, 94, 0.15); color: #16a34a; }
    .deg-badge.minor { background: rgba(132, 204, 22, 0.15); color: #65a30d; }
    .deg-badge.moderate { background: rgba(245, 158, 11, 0.15); color: #d97706; }
    .deg-badge.severe { background: rgba(249, 115, 22, 0.15); color: #ea580c; }
    .deg-badge.critical { background: rgba(239, 68, 68, 0.15); color: #dc2626; }

    .component-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
      gap: 16px;
      margin-bottom: 32px;
    }

    .component-card {
      background: var(--saas-bg-card, #ffffff);
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: 12px;
      padding: 16px;
      transition: all 0.15s ease;
    }

    .component-card:hover {
      border-color: var(--saas-border-medium, #ccc);
      box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    }

    .component-card.unhealthy {
      border-color: rgba(239, 68, 68, 0.3);
      background: rgba(239, 68, 68, 0.02);
    }

    .component-name {
      font-weight: 600;
      font-size: 14px;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 8px;
      text-transform: capitalize;
    }

    .component-stats {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      font-size: 11px;
      color: var(--saas-text-muted, #999);
    }

    .component-stat {
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .component-stat .material-symbols-outlined { font-size: 14px; }

    .recommendations-panel {
      background: var(--saas-bg-card, #ffffff);
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: 12px;
      padding: 20px;
      margin-top: 24px;
    }

    .recommendations-title {
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .recommendations-list {
      list-style: none;
      padding: 0;
      margin: 0;
    }

    .recommendations-list li {
      padding: 8px 12px;
      background: var(--saas-bg-hover, #fafafa);
      border-radius: 6px;
      margin-bottom: 8px;
      font-size: 13px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .recommendations-list li .material-symbols-outlined {
      font-size: 16px;
      color: #f59e0b;
    }

    .circuit-badge {
      font-size: 10px;
      padding: 2px 6px;
      border-radius: 4px;
      text-transform: uppercase;
      font-weight: 600;
    }

    .circuit-badge.closed { background: rgba(34, 197, 94, 0.15); color: #16a34a; }
    .circuit-badge.open { background: rgba(239, 68, 68, 0.15); color: #dc2626; }
    .circuit-badge.half_open { background: rgba(245, 158, 11, 0.15); color: #d97706; }
  `;

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
    this.pollInterval = window.setInterval(() => this.fetchHealth(), 30000);
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    if (this.pollInterval) clearInterval(this.pollInterval);
  }

  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('auth_token') || localStorage.getItem('saas_auth_token');
    return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
  }

  async fetchData() {
    this.loading = true;
    await Promise.all([this.fetchHealth(), this.fetchRateLimits(), this.fetchDegradation()]);
    this.loading = false;
  }

  async fetchHealth() {
    try {
      this.refreshing = true;
      const res = await fetch('/api/v2/observability/infrastructure/health', { headers: this.getAuthHeaders() });
      if (res.ok) {
        this.health = await res.json();
        this.lastRefresh = new Date();
      }
    } catch (err) {
      console.error('Health fetch failed:', err);
    } finally {
      this.refreshing = false;
    }
  }

  async fetchRateLimits() {
    try {
      const res = await fetch('/api/v2/core/infrastructure/ratelimits', { headers: this.getAuthHeaders() });
      if (res.ok) {
        const data = await res.json();
        this.rateLimits = data.limits || [];
      }
    } catch (err) {
      console.error('Rate limits fetch failed:', err);
    }
  }

  async fetchDegradation() {
    try {
      const [statusRes, componentsRes, historyRes] = await Promise.all([
        fetch('/api/v2/core/infrastructure/degradation/status', { headers: this.getAuthHeaders() }),
        fetch('/api/v2/core/infrastructure/degradation/components', { headers: this.getAuthHeaders() }),
        fetch('/api/v2/core/infrastructure/degradation/history?limit=50', { headers: this.getAuthHeaders() }),
      ]);
      if (statusRes.ok) {
        this.degradation = await statusRes.json();
      }
      if (componentsRes.ok) {
        this.components = await componentsRes.json();
      }
      if (historyRes.ok) {
        this.history = await historyRes.json();
      }
    } catch (err) {
      console.error('Degradation fetch failed:', err);
    }
  }

  async seedRateLimits() {
    const res = await fetch('/api/v2/core/infrastructure/ratelimits/seed', {
      method: 'POST',
      headers: this.getAuthHeaders()
    });
    if (res.ok) await this.fetchRateLimits();
  }

  private navigate(path: string) {
    window.dispatchEvent(new CustomEvent('saas-navigate', { detail: { route: path } }));
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
              <a class="nav-item" href="/saas/dashboard">
                <span class="material-symbols-outlined">visibility</span>
                Dashboard
              </a>
              <a class="nav-item" href="/saas/tenants">
                <span class="material-symbols-outlined">apartment</span>
                Tenants
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

  renderHealth() {
    if (!this.health) return html`<div class="empty-state">No health data</div>`;

    const h = this.health.services.filter(s => s.status === 'healthy').length;
    const d = this.health.services.filter(s => s.status === 'degraded').length;
    const x = this.health.services.filter(s => s.status === 'down').length;

    return html`
      <div class="metrics-grid">
        <div class="metric-card featured">
          <div class="metric-header">
            <span class="metric-label">Overall Status</span>
            <div class="metric-icon"><span class="material-symbols-outlined">monitoring</span></div>
          </div>
          <div class="metric-value">${this.health.overall_status.toUpperCase()}</div>
          <div class="metric-sub">${this.health.duration_ms.toFixed(0)}ms check time</div>
        </div>
        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-label">Healthy</span>
            <div class="metric-icon"><span class="material-symbols-outlined">check_circle</span></div>
          </div>
          <div class="metric-value healthy">${h}</div>
          <div class="metric-sub">services operational</div>
        </div>
        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-label">Degraded</span>
            <div class="metric-icon"><span class="material-symbols-outlined">warning</span></div>
          </div>
          <div class="metric-value degraded">${d}</div>
          <div class="metric-sub">services degraded</div>
        </div>
        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-label">Down</span>
            <div class="metric-icon"><span class="material-symbols-outlined">error</span></div>
          </div>
          <div class="metric-value down">${x}</div>
          <div class="metric-sub">services down</div>
        </div>
      </div>

      <h3 class="section-title">
        <span class="material-symbols-outlined">dns</span>
        Service Details
      </h3>

      <div class="services-grid">
        ${this.health.services.map(s => html`
          <div class="service-card">
            <div class="service-header">
              <span class="service-name">
                <div class="service-icon">
                  <span class="material-symbols-outlined">${SERVICE_ICONS[s.name] || 'settings'}</span>
                </div>
                ${s.name}
              </span>
              <span class="status-badge ${s.status}">
                <span class="status-dot ${s.status}"></span>
                ${s.status}
              </span>
            </div>
            ${s.details && Object.keys(s.details).length > 0 ? html`
              <div class="service-details">
                ${Object.entries(s.details).map(([k, v]) => html`${k}: ${v}<br>`)}
              </div>
            ` : nothing}
            ${s.latency_ms ? html`<div class="latency">${s.latency_ms.toFixed(0)}ms</div>` : nothing}
            ${s.error ? html`<div class="error-box">${s.error}</div>` : nothing}
          </div>
        `)}
      </div>
    `;
  }

  renderRateLimits() {
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

  renderDegradation() {
    if (!this.degradation) return html`<div class="empty-state">No degradation data</div>`;

    const level = this.degradation.overall_level;
    const healthy = this.degradation.healthy_components.length;
    const affected = this.degradation.affected_components.length;

    return html`
      <!-- Status Cards -->
      <div class="metrics-grid">
        <div class="metric-card featured">
          <div class="metric-header">
            <span class="metric-label">Degradation Level</span>
            <div class="metric-icon"><span class="material-symbols-outlined">thermostat</span></div>
          </div>
          <div class="metric-value">
            <span class="deg-badge ${level}">${level.toUpperCase()}</span>
          </div>
          <div class="metric-sub">System status assessment</div>
        </div>
        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-label">Healthy</span>
            <div class="metric-icon"><span class="material-symbols-outlined">check_circle</span></div>
          </div>
          <div class="metric-value healthy">${healthy}</div>
          <div class="metric-sub">components operational</div>
        </div>
        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-label">Affected</span>
            <div class="metric-icon"><span class="material-symbols-outlined">warning</span></div>
          </div>
          <div class="metric-value ${affected > 0 ? 'degraded' : ''}">${affected}</div>
          <div class="metric-sub">components impacted</div>
        </div>
        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-label">Total</span>
            <div class="metric-icon"><span class="material-symbols-outlined">grid_view</span></div>
          </div>
          <div class="metric-value">${this.degradation.total_components}</div>
          <div class="metric-sub">monitored components</div>
        </div>
      </div>

      <!-- Component Grid -->
      <h3 class="section-title">
        <span class="material-symbols-outlined">memory</span>
        Component Health
      </h3>
      <div class="component-grid">
        ${this.components.map(c => html`
          <div class="component-card ${!c.healthy ? 'unhealthy' : ''}">
            <div class="component-name">
              <div class="service-icon">
                <span class="material-symbols-outlined">${SERVICE_ICONS[c.name] || 'settings'}</span>
              </div>
              ${c.name}
              <span class="deg-badge ${c.degradation_level}">${c.degradation_level}</span>
            </div>
            <div class="component-stats">
              <span class="component-stat">
                <span class="material-symbols-outlined">speed</span>
                ${c.response_time ? c.response_time.toFixed(2) + 's' : '0s'}
              </span>
              <span class="component-stat">
                <span class="material-symbols-outlined">error_outline</span>
                ${(c.error_rate * 100).toFixed(0)}% errors
              </span>
              <span class="circuit-badge ${c.circuit_state}">${c.circuit_state}</span>
            </div>
          </div>
        `)}
      </div>

      <!-- Recommendations -->
      ${this.degradation.recommendations.length > 0 || this.degradation.mitigation_actions.length > 0 ? html`
        <div class="recommendations-panel">
          <h4 class="recommendations-title">
            <span class="material-symbols-outlined">lightbulb</span>
            Recommendations & Actions
          </h4>
          <ul class="recommendations-list">
            ${this.degradation.recommendations.map(r => html`
              <li>
                <span class="material-symbols-outlined">tips_and_updates</span>
                ${r}
              </li>
            `)}
            ${this.degradation.mitigation_actions.map(a => html`
              <li>
                <span class="material-symbols-outlined">build</span>
                ${a}
              </li>
            `)}
          </ul>
        </div>
      ` : nothing}

      <!-- History Timeline -->
      ${this.history.length > 0 ? html`
        <h3 class="section-title" style="margin-top: 32px;">
          <span class="material-symbols-outlined">history</span>
          Event History
        </h3>
        <div class="card">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Component</th>
                <th>Level</th>
                <th>Status</th>
                <th>Response</th>
                <th>Event</th>
              </tr>
            </thead>
            <tbody>
              ${this.history.slice(0, 20).map(h => html`
                <tr>
                  <td style="font-family: var(--saas-font-mono, monospace); font-size: 11px;">
                    ${new Date(h.timestamp * 1000).toLocaleTimeString()}
                  </td>
                  <td><strong style="text-transform: capitalize;">${h.component_name}</strong></td>
                  <td><span class="deg-badge ${h.degradation_level}">${h.degradation_level}</span></td>
                  <td>
                    <span class="status-badge ${h.healthy ? 'healthy' : 'down'}">
                      <span class="status-dot ${h.healthy ? 'healthy' : 'down'}"></span>
                      ${h.healthy ? 'healthy' : 'unhealthy'}
                    </span>
                  </td>
                  <td style="font-family: var(--saas-font-mono, monospace); font-size: 11px;">
                    ${h.response_time ? h.response_time.toFixed(3) + 's' : '-'}
                  </td>
                  <td>
                    <span class="policy-badge ${h.event_type === 'failure' ? 'HARD' : 'SOFT'}">${h.event_type}</span>
                  </td>
                </tr>
              `)}
            </tbody>
          </table>
        </div>
      ` : nothing}
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'saas-infrastructure-dashboard': SaasInfrastructureDashboard;
  }
}
