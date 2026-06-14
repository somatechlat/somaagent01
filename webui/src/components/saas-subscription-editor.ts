/**
 * SaaS Subscription Editor
 * Renders the tier builder/editor modal.
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - CSS custom properties
 * - Material Symbols only
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, query } from 'lit/decorators.js';
import type { SubscriptionTier, SubscriptionTierInput } from '../controllers/subscriptions-controller.js';

@customElement('saas-subscription-editor')
export class SaasSubscriptionEditor extends LitElement {
    static styles = css`
        :host {
            display: block;
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

        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }

        .modal-overlay.hidden {
            display: none;
        }

        .modal {
            background: var(--saas-bg-card, #ffffff);
            border-radius: 16px;
            width: 100%;
            max-width: 500px;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: var(--saas-shadow-lg, 0 8px 24px rgba(0,0,0,0.12));
        }

        .modal-header {
            padding: 20px 24px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-title {
            font-size: 18px;
            font-weight: 600;
        }

        .modal-close {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            border: none;
            background: transparent;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .modal-close:hover {
            background: var(--saas-bg-hover, #fafafa);
        }

        .modal-body {
            padding: 24px;
        }

        .modal-footer {
            padding: 16px 24px;
            border-top: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            justify-content: flex-end;
            gap: 10px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-label {
            display: block;
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 8px;
        }

        .form-input {
            width: 100%;
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            font-size: 14px;
            background: var(--saas-bg-card, #ffffff);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .form-input:focus {
            outline: none;
            border-color: var(--saas-text-primary, #1a1a1a);
        }

        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }

        .form-hint {
            font-size: 12px;
            color: var(--saas-text-muted, #999);
            margin-top: 6px;
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

        .btn.primary {
            background: #1a1a1a;
            color: white;
            border-color: #1a1a1a;
        }

        .btn.primary:hover {
            background: #333;
        }
    `;

    @property({ type: Boolean }) open = false;
    @property({ attribute: false }) editingTier: SubscriptionTier | null = null;

    @query('#tierName') private _nameEl!: HTMLInputElement;
    @query('#maxAgents') private _maxAgentsEl!: HTMLInputElement;
    @query('#maxUsers') private _maxUsersEl!: HTMLInputElement;
    @query('#maxTokens') private _maxTokensEl!: HTMLInputElement;
    @query('#maxStorage') private _maxStorageEl!: HTMLInputElement;
    @query('#price') private _priceEl!: HTMLInputElement;
    @query('#interval') private _intervalEl!: HTMLSelectElement;

    render() {
        return html`
            <div class="modal-overlay ${this.open ? '' : 'hidden'}" @click=${this._handleBackdropClick}>
                <div class="modal">
                    <div class="modal-header">
                        <h3 class="modal-title">${this.editingTier ? 'Edit Tier' : 'Create Custom Tier'}</h3>
                        <button class="modal-close" @click=${this._close}>
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label class="form-label">Tier Name</label>
                            <input type="text" class="form-input" id="tierName"
                                .value=${this.editingTier?.name || ''}
                                placeholder="e.g., Premium Plus">
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Max Agents</label>
                                <input type="number" class="form-input" id="maxAgents"
                                    .value=${String(this.editingTier?.maxAgents || 5)}
                                    min="1">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Max Users</label>
                                <input type="number" class="form-input" id="maxUsers"
                                    .value=${String(this.editingTier?.maxUsers || 25)}
                                    min="1">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Tokens/Month</label>
                                <input type="number" class="form-input" id="maxTokens"
                                    .value=${String(this.editingTier?.maxTokensPerMonth || 5000000)}
                                    min="100000" step="100000">
                                <p class="form-hint">In tokens (1M = 1,000,000)</p>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Storage (GB)</label>
                                <input type="number" class="form-input" id="maxStorage"
                                    .value=${String(this.editingTier?.maxStorageGB || 50)}
                                    min="1">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Price (USD)</label>
                                <input type="number" class="form-input" id="price"
                                    .value=${String((this.editingTier?.priceCents || 9900) / 100)}
                                    min="0" step="0.01">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Billing Interval</label>
                                <select class="form-input" id="interval">
                                    <option value="monthly" ?selected=${this.editingTier?.billingInterval === 'monthly'}>Monthly</option>
                                    <option value="yearly" ?selected=${this.editingTier?.billingInterval === 'yearly'}>Yearly</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn" @click=${this._close}>Cancel</button>
                        <button class="btn primary" @click=${this._save}>
                            ${this.editingTier ? 'Save Changes' : 'Create Tier'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    private _handleBackdropClick = (e: Event) => {
        if (e.target === e.currentTarget) {
            this._close();
        }
    };

    private _close = () => {
        this.dispatchEvent(new CustomEvent('close-editor', {
            bubbles: true,
            composed: true,
        }));
    };

    private _save = () => {
        const tierData: SubscriptionTierInput = {
            name: this._nameEl.value,
            slug: this._nameEl.value.toLowerCase().replace(/\s+/g, '-'),
            maxAgents: parseInt(this._maxAgentsEl.value),
            maxUsers: parseInt(this._maxUsersEl.value),
            maxTokensPerMonth: parseInt(this._maxTokensEl.value),
            maxStorageGB: parseInt(this._maxStorageEl.value),
            priceCents: Math.round(parseFloat(this._priceEl.value) * 100),
            billingInterval: this._intervalEl.value as 'monthly' | 'yearly',
            isCustom: true,
        };

        this.dispatchEvent(new CustomEvent('save-tier', {
            detail: tierData,
            bubbles: true,
            composed: true,
        }));
    };
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-subscription-editor': SaasSubscriptionEditor;
    }
}
