/**
 * Tenant Billing Invoices
 *
 * Renders the invoice history for the tenant billing view.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { Invoice } from '../controllers/tenant-billing-controller.js';

@customElement('saas-tenant-billing-invoices')
export class SaasTenantBillingInvoices extends LitElement {
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

        .card {
            background: var(--saas-surface, white);
            border-radius: 16px;
            border: 1px solid var(--saas-border, #e2e8f0);
            padding: 24px;
            margin-bottom: 32px;
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .card-title {
            font-size: 16px;
            font-weight: 600;
            color: var(--saas-text, #1e293b);
        }

        .invoice-list {
            max-height: 300px;
            overflow-y: auto;
        }

        .invoice-item {
            display: flex;
            align-items: center;
            padding: 14px 0;
            border-bottom: 1px solid var(--saas-border, #e2e8f0);
        }

        .invoice-item:last-child {
            border-bottom: none;
        }

        .invoice-date {
            flex: 1;
            font-size: 14px;
            color: var(--saas-text, #1e293b);
        }

        .invoice-amount {
            font-size: 14px;
            font-weight: 600;
            color: var(--saas-text, #1e293b);
            margin-right: 16px;
        }

        .invoice-status {
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
            margin-right: 12px;
        }

        .status-paid,
        .status-succeeded {
            background: rgba(34, 197, 94, 0.1);
            color: #22c55e;
        }

        .status-pending {
            background: rgba(245, 158, 11, 0.1);
            color: #f59e0b;
        }

        .status-failed,
        .status-overdue {
            background: rgba(239, 68, 68, 0.1);
            color: #ef4444;
        }

        .empty-state {
            text-align: center;
            padding: 24px;
            color: var(--saas-text-dim, #64748b);
            font-size: 14px;
        }
    `;

    @property({ type: Array })
    invoices: Invoice[] = [];

    render() {
        return html`
            <div class="card">
                <div class="card-header">
                    <span class="card-title">
                        <span class="material-symbols-outlined">description</span> Invoices
                    </span>
                </div>
                <div class="invoice-list">
                    ${this.invoices.length > 0
                        ? this.invoices.map(
                              (invoice) => html`
                                  <div class="invoice-item">
                                      <span class="invoice-date">${invoice.number || invoice.created_at}</span>
                                      <span class="invoice-amount">${this._formatCurrency(invoice.amount_cents / 100)}</span>
                                      <span class="invoice-status ${this._invoiceStatusClass(invoice.status)}">
                                          ${invoice.status}
                                      </span>
                                  </div>
                              `
                          )
                        : html`<div class="empty-state">No invoices</div>`}
                </div>
            </div>
        `;
    }

    private _formatCurrency(amount: number): string {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
        }).format(amount);
    }

    private _invoiceStatusClass(status: string): string {
        const normalized = (status || '').toLowerCase();
        if (normalized === 'paid' || normalized === 'succeeded') return 'status-paid';
        if (normalized === 'failed' || normalized === 'overdue') return 'status-failed';
        return 'status-pending';
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-tenant-billing-invoices': SaasTenantBillingInvoices;
    }
}
