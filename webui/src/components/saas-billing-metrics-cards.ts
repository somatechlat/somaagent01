/**
 * SaaS Billing Metrics Cards
 * Renders MRR, ARPU, churn rate, and paid tenant metric cards.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { BillingMetrics } from '../controllers/billing-controller.js';

@customElement('saas-billing-metrics-cards')
export class SaasBillingMetricsCards extends LitElement {
  static styles = css`
    :host {
      display: block;
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

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
    }

    @media (max-width: 1200px) {
      .stats-grid {
        grid-template-columns: repeat(2, 1fr);
      }
    }

    .stat-card {
      background: var(--saas-bg-card, #ffffff);
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: 12px;
      padding: 20px;
    }

    .stat-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 12px;
    }

    .stat-label {
      font-size: 13px;
      color: var(--saas-text-secondary, #666);
    }

    .stat-icon {
      width: 36px;
      height: 36px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--saas-bg-hover, #fafafa);
    }

    .stat-icon .material-symbols-outlined {
      font-size: 18px;
    }

    .stat-value {
      font-size: 28px;
      font-weight: 700;
    }
  `;

  @property({ type: Object })
  metrics?: BillingMetrics;

  render() {
    const m = this.metrics ?? {
      mrr: 0,
      mrr_growth: 0,
      arpu: 0,
      churn_rate: 0,
      total_tenants: 0,
      paid_tenants: 0,
    };

    return html`
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-label">Monthly Recurring Revenue</span>
            <div class="stat-icon">
              <span class="material-symbols-outlined">trending_up</span>
            </div>
          </div>
          <div class="stat-value">$${this._formatDollars(m.mrr)}</div>
        </div>

        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-label">Average Revenue Per User</span>
            <div class="stat-icon">
              <span class="material-symbols-outlined">person</span>
            </div>
          </div>
          <div class="stat-value">$${this._formatDollars(m.arpu)}</div>
        </div>

        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-label">Churn Rate</span>
            <div class="stat-icon">
              <span class="material-symbols-outlined">sync_problem</span>
            </div>
          </div>
          <div class="stat-value">${m.churn_rate}%</div>
        </div>

        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-label">Paid Tenants</span>
            <div class="stat-icon">
              <span class="material-symbols-outlined">verified</span>
            </div>
          </div>
          <div class="stat-value">${m.paid_tenants}/${m.total_tenants}</div>
        </div>
      </div>
    `;
  }

  private _formatDollars(amount: number): string {
    return (amount ?? 0).toLocaleString('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'saas-billing-metrics-cards': SaasBillingMetricsCards;
  }
}
