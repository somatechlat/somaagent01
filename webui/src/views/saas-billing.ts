/**
 * SomaAgent SaaS — Billing Dashboard
 * Per SAAS_ADMIN_SRS.md Section 5.3 - Billing Dashboard
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - Minimal white/black design per UI_STYLE_GUIDE.md
 * - NO EMOJIS - Google Material Symbols only
 *
 * Features:
 * - MRR, ARPU, Churn metrics
 * - Revenue by tier breakdown
 * - Recent invoices list
 * - Usage summary
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { BillingController } from '../controllers/billing-controller.js';
import type {
  BillingControllerHost,
  BillingMetrics,
  Invoice,
  TierRevenue,
} from '../controllers/billing-controller.js';

import '../components/saas-billing-metrics-cards.js';
import '../components/saas-billing-revenue-chart.js';
import '../components/saas-billing-invoices-table.js';

@customElement('saas-billing')
export class SaasBilling extends LitElement implements BillingControllerHost {
  static styles = css`
    :host {
      display: flex;
      height: 100vh;
      background: var(--saas-bg-page, #f5f5f5);
      font-family: var(
        --saas-font-sans,
        -apple-system,
        BlinkMacSystemFont,
        'Segoe UI',
        Roboto,
        sans-serif
      );
      color: var(--saas-text-primary, #1a1a1a);
    }

    * {
      box-sizing: border-box;
    }

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
      background: var(--saas-bg-card, #ffffff);
      border-right: 1px solid var(--saas-border-light, #e0e0e0);
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
      padding: 24px 0;
    }

    .sidebar-header {
      padding: 0 20px 20px;
      border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
      margin-bottom: 16px;
    }

    .sidebar-title {
      font-size: 18px;
      font-weight: 600;
      margin: 0 0 4px 0;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .sidebar-subtitle {
      font-size: 13px;
      color: var(--saas-text-secondary, #666);
    }

    .nav-list {
      display: flex;
      flex-direction: column;
      gap: 2px;
      padding: 0 12px;
    }

    .nav-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 14px;
      border-radius: 8px;
      font-size: 14px;
      color: var(--saas-text-secondary, #666);
      cursor: pointer;
      transition: all 0.15s ease;
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

    .nav-item .material-symbols-outlined {
      font-size: 18px;
    }

    .nav-divider {
      height: 1px;
      background: var(--saas-border-light, #e0e0e0);
      margin: 12px 20px;
    }

    /* Main Content */
    .main {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .header {
      padding: 16px 24px;
      background: var(--saas-bg-card, #ffffff);
      border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .header-title {
      font-size: 18px;
      font-weight: 600;
    }

    .header-actions {
      display: flex;
      gap: 10px;
    }

    .btn {
      padding: 10px 18px;
      border-radius: 8px;
      font-size: 14px;
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

    .btn:hover {
      background: var(--saas-bg-hover, #fafafa);
    }

    .btn .material-symbols-outlined {
      font-size: 18px;
    }

    .content {
      flex: 1;
      overflow-y: auto;
      padding: 24px;
    }

    .content-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-top: 24px;
    }

    @media (max-width: 900px) {
      .content-grid {
        grid-template-columns: 1fr;
      }
    }

    .error-banner {
      padding: 12px 16px;
      margin: 0 24px 24px;
      background: #fee2e2;
      color: #b91c1c;
      border: 1px solid #fecaca;
      border-radius: 12px;
      font-size: 14px;
    }
  `;

  @state() _metrics: BillingMetrics = {
    mrr: 0,
    mrr_growth: 0,
    arpu: 0,
    churn_rate: 0,
    total_tenants: 0,
    paid_tenants: 0,
  };

  @state() _tierRevenue: TierRevenue[] = [];

  @state() _invoices: Invoice[] = [];

  @state() _isLoading = false;

  @state() _error = '';

  private _controller = new BillingController(this);

  connectedCallback() {
    super.connectedCallback();
    this._controller.connect();
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    this._controller.disconnect();
  }

  render() {
    return html`
      <!-- Sidebar -->
      <aside class="sidebar">
        <div class="sidebar-header">
          <h1 class="sidebar-title">
            <span class="material-symbols-outlined">shield_person</span>
            God Mode
          </h1>
          <p class="sidebar-subtitle">Platform Administration</p>
        </div>

        <nav class="nav-list">
          <a class="nav-item" href="/saas/dashboard">
            <span class="material-symbols-outlined">dashboard</span>
            Dashboard
          </a>
          <a class="nav-item" href="/saas/tenants">
            <span class="material-symbols-outlined">apartment</span>
            Tenants
          </a>
          <a class="nav-item" href="/saas/subscriptions">
            <span class="material-symbols-outlined">card_membership</span>
            Subscriptions
          </a>
          <a class="nav-item active" href="/saas/billing">
            <span class="material-symbols-outlined">payments</span>
            Billing
          </a>
          <div class="nav-divider"></div>
          <a class="nav-item" href="/platform/models">
            <span class="material-symbols-outlined">model_training</span>
            Models
          </a>
          <a class="nav-item" href="/platform/roles">
            <span class="material-symbols-outlined">admin_panel_settings</span>
            Roles
          </a>
          <a class="nav-item" href="/platform/flags">
            <span class="material-symbols-outlined">toggle_on</span>
            Feature Flags
          </a>
          <a class="nav-item" href="/platform/api-keys">
            <span class="material-symbols-outlined">vpn_key</span>
            API Keys
          </a>
        </nav>
      </aside>

      <!-- Main Content -->
      <main class="main">
        <header class="header">
          <h2 class="header-title">Billing & Revenue</h2>
          <div class="header-actions">
            <button class="btn" @click=${this._exportReport}>
              <span class="material-symbols-outlined">download</span>
              Export Report
            </button>
          </div>
        </header>

        ${this._error ? html`<div class="error-banner">${this._error}</div>` : ''}

        <div class="content">
          <saas-billing-metrics-cards .metrics=${this._metrics}></saas-billing-metrics-cards>

          <div class="content-grid">
            <saas-billing-revenue-chart .tierRevenue=${this._tierRevenue}></saas-billing-revenue-chart>
            <saas-billing-invoices-table .invoices=${this._invoices}></saas-billing-invoices-table>
          </div>
        </div>
      </main>
    `;
  }

  private _exportReport() {
    const report = {
      exportedAt: new Date().toISOString(),
      metrics: this._metrics,
      tierRevenue: this._tierRevenue,
      invoices: this._invoices,
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `billing-report-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'saas-billing': SaasBilling;
  }
}
