/**
 * SaaS Billing Revenue Chart
 * Renders the revenue-by-tier breakdown card.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { TierRevenue } from '../controllers/billing-controller.js';

@customElement('saas-billing-revenue-chart')
export class SaasBillingRevenueChart extends LitElement {
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

    .card {
      background: var(--saas-bg-card, #ffffff);
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: 12px;
      padding: 20px;
    }

    .card-title {
      font-size: 16px;
      font-weight: 600;
      margin: 0 0 16px 0;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .card-title .material-symbols-outlined {
      font-size: 18px;
      color: var(--saas-text-secondary, #666);
    }

    .revenue-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .revenue-item {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .revenue-bar-bg {
      flex: 1;
      height: 8px;
      background: var(--saas-border-light, #e0e0e0);
      border-radius: 4px;
      overflow: hidden;
    }

    .revenue-bar {
      height: 100%;
      border-radius: 4px;
      background: #1a1a1a;
    }

    .revenue-tier {
      width: 80px;
      font-size: 13px;
      font-weight: 500;
    }

    .revenue-amount {
      width: 70px;
      font-size: 13px;
      font-weight: 600;
      text-align: right;
    }

    .revenue-pct {
      width: 45px;
      font-size: 12px;
      color: var(--saas-text-muted, #999);
      text-align: right;
    }
  `;

  @property({ type: Array })
  tierRevenue: TierRevenue[] = [];

  render() {
    return html`
      <div class="card">
        <h3 class="card-title">
          <span class="material-symbols-outlined">pie_chart</span>
          Revenue by Tier
        </h3>
        <div class="revenue-list">
          ${this.tierRevenue.map(
            (tier) => html`
              <div class="revenue-item">
                <span class="revenue-tier">${tier.tier}</span>
                <div class="revenue-bar-bg">
                  <div class="revenue-bar" style="width: ${tier.percentage}%"></div>
                </div>
                <span class="revenue-amount">$${this._formatDollars(tier.mrr)}</span>
                <span class="revenue-pct">${tier.percentage}%</span>
              </div>
            `
          )}
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
    'saas-billing-revenue-chart': SaasBillingRevenueChart;
  }
}
