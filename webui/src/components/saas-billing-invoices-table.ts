/**
 * SaaS Billing Invoices Table
 * Renders the recent invoices history card and table.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { Invoice } from '../controllers/billing-controller.js';

@customElement('saas-billing-invoices-table')
export class SaasBillingInvoicesTable extends LitElement {
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

    .invoices-table {
      width: 100%;
      border-collapse: collapse;
    }

    .invoices-table th {
      text-align: left;
      padding: 10px 12px;
      font-size: 12px;
      font-weight: 500;
      color: var(--saas-text-muted, #999);
      border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .invoices-table td {
      padding: 12px;
      font-size: 13px;
      border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
    }

    .invoices-table tr:last-child td {
      border-bottom: none;
    }

    .invoice-tenant {
      font-weight: 500;
    }

    .invoice-amount {
      font-weight: 600;
    }

    .invoice-status {
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
    }

    .invoice-status.paid {
      background: #d1fae5;
      color: #047857;
    }

    .invoice-status.pending {
      background: #fef3c7;
      color: #b45309;
    }

    .invoice-status.overdue {
      background: #fee2e2;
      color: #b91c1c;
    }

    .invoice-status.void {
      background: #f3f4f6;
      color: #6b7280;
    }

    .view-all {
      display: block;
      text-align: center;
      padding: 12px;
      font-size: 13px;
      color: var(--saas-text-secondary, #666);
      text-decoration: none;
      border-top: 1px solid var(--saas-border-light, #e0e0e0);
      margin-top: 8px;
      transition: color 0.1s ease;
    }

    .view-all:hover {
      color: var(--saas-text-primary, #1a1a1a);
    }
  `;

  @property({ type: Array })
  invoices: Invoice[] = [];

  render() {
    return html`
      <div class="card">
        <h3 class="card-title">
          <span class="material-symbols-outlined">receipt_long</span>
          Recent Invoices
        </h3>
        <table class="invoices-table">
          <thead>
            <tr>
              <th>Invoice</th>
              <th>Amount</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            ${this.invoices.slice(0, 5).map(
              (inv) => html`
                <tr>
                  <td class="invoice-tenant">${inv.number}</td>
                  <td class="invoice-amount">$${(inv.amount_cents / 100).toFixed(2)}</td>
                  <td>
                    <span class="invoice-status ${inv.status}">${inv.status}</span>
                  </td>
                  <td>${new Date(inv.created_at).toLocaleDateString()}</td>
                </tr>
              `
            )}
          </tbody>
        </table>
        <a href="/saas/invoices" class="view-all">View all invoices</a>
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'saas-billing-invoices-table': SaasBillingInvoicesTable;
  }
}
