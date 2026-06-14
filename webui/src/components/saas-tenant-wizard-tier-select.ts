/**
 * SaaS Tenant Wizard Tier Select
 *
 * Renders the Step 2 subscription tier selection.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { SubscriptionTier, TenantFormData } from '../controllers/tenant-wizard-controller.js';

export interface WizardFieldChangeDetail {
    field: keyof TenantFormData;
    value: unknown;
}

@customElement('saas-tenant-wizard-tier-select')
export class SaasTenantWizardTierSelect extends LitElement {
    static styles = css`
        :host {
            display: block;
        }

        * {
            box-sizing: border-box;
        }

        .form-group {
            margin-bottom: 24px;
        }

        .form-label {
            display: block;
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 8px;
            color: #333;
        }

        .form-input {
            width: 100%;
            padding: 12px 14px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.15s;
        }

        .form-input:focus {
            outline: none;
            border-color: #1a1a1a;
        }

        .tier-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }

        .tier-card {
            padding: 20px;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.15s;
        }

        .tier-card:hover {
            border-color: #999;
        }

        .tier-card.selected {
            border-color: #1a1a1a;
            background: #fafafa;
        }

        .tier-name {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 4px;
        }

        .tier-price {
            font-size: 20px;
            font-weight: 700;
            color: #1a1a1a;
        }

        .tier-price span {
            font-size: 13px;
            font-weight: 400;
            color: #666;
        }

        .tier-limits {
            font-size: 12px;
            color: #666;
            margin-top: 8px;
        }
    `;

    @property({ type: Array })
    tiers: SubscriptionTier[] = [];

    @property({ type: String })
    selectedTierId = '';

    @property({ type: String })
    billingEmail = '';

    render() {
        return html`
            <div class="form-group">
                <label class="form-label">Select Subscription Tier *</label>
                <div class="tier-grid">
                    ${this.tiers.map(tier => html`
                        <div class="tier-card ${this.selectedTierId === tier.id ? 'selected' : ''}"
                            @click=${() => this._emit('tier_id', tier.id)}>
                            <div class="tier-name">${tier.name}</div>
                            <div class="tier-price">
                                $${(tier.price_cents / 100).toFixed(0)}<span>/mo</span>
                            </div>
                            <div class="tier-limits">
                                ${tier.max_agents} agents • ${tier.max_users} users
                            </div>
                        </div>
                    `)}
                </div>
            </div>

            <div class="form-group">
                <label class="form-label">Billing Contact Email</label>
                <input type="email" class="form-input" .value=${this.billingEmail}
                    @input=${(e: Event) => this._emit('billing_email', (e.target as HTMLInputElement).value)}
                    placeholder="billing@acme.com">
            </div>
        `;
    }

    private _emit(field: keyof TenantFormData, value: unknown): void {
        this.dispatchEvent(new CustomEvent<WizardFieldChangeDetail>('wizard-field-change', {
            detail: { field, value },
        }));
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-tenant-wizard-tier-select': SaasTenantWizardTierSelect;
    }
}
