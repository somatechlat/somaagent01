/**
 * Tenant Creation Wizard
 * 4-step wizard for creating new tenants with full configuration.
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Uses /api/v2/saas/tenants endpoints
 * - Real-time slug validation
 * - Per SRS-SAAS-TENANT-CREATION.md
 *
 * 7-Persona Implementation:
 * - 🏗️ Django Architect: CRUD integration
 * - 🔒 Security Auditor: Slug validation, MFA defaults
 * - 📈 PM: Multi-step wizard UX
 * - 🧪 QA: Error handling, rollback messaging
 * - ⚡ Performance: Debounced validation
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement } from 'lit/decorators.js';
import { TenantWizardController } from '../controllers/tenant-wizard-controller.js';
import type { TenantFormData } from '../controllers/tenant-wizard-controller.js';
import type { WizardFieldChangeDetail } from '../components/saas-tenant-wizard-form.js';
import '../components/saas-tenant-wizard-steps.js';
import '../components/saas-tenant-wizard-form.js';
import '../components/saas-tenant-wizard-tier-select.js';

@customElement('saas-tenant-wizard')
export class SaasTenantWizard extends LitElement {
    static styles = css`
        :host {
            display: block;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
        }

        * { box-sizing: border-box; }

        .wizard {
            background: #fff;
            border-radius: 16px;
            width: 90%;
            max-width: 720px;
            max-height: 90vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }

        .wizard-header {
            padding: 24px 32px;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .wizard-title { font-size: 20px; font-weight: 600; margin: 0; }
        .close-btn { background: none; border: none; font-size: 24px; cursor: pointer; color: #999; }
        .close-btn:hover { color: #333; }

        .wizard-content {
            flex: 1;
            overflow-y: auto;
            padding: 32px;
        }

        .form-group { margin-bottom: 24px; }
        .form-label { display: block; font-size: 13px; font-weight: 500; margin-bottom: 8px; color: #333; }
        .form-hint { font-size: 12px; color: #888; margin-top: 4px; }

        .form-input {
            width: 100%;
            padding: 12px 14px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.15s;
        }

        .form-input:focus { outline: none; border-color: #1a1a1a; }
        .form-select {
            width: 100%;
            padding: 12px 14px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            background: #fff;
            cursor: pointer;
        }

        .checkbox-group { display: flex; flex-wrap: wrap; gap: 12px; }

        .checkbox-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 14px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.15s;
        }

        .checkbox-item:hover { border-color: #999; }
        .checkbox-item.selected { border-color: #1a1a1a; background: #f8f8f8; }

        .toggle-row { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #f0f0f0; }
        .toggle-label { font-size: 14px; }
        .toggle-switch { position: relative; width: 44px; height: 24px; }
        .toggle-switch input { opacity: 0; width: 0; height: 0; }
        .toggle-slider {
            position: absolute; inset: 0;
            background: #ccc; border-radius: 24px; cursor: pointer; transition: 0.3s;
        }
        .toggle-slider:before {
            content: ""; position: absolute; height: 18px; width: 18px; left: 3px; bottom: 3px;
            background: white; border-radius: 50%; transition: 0.3s;
        }
        input:checked + .toggle-slider { background: #1a1a1a; }
        input:checked + .toggle-slider:before { transform: translateX(20px); }

        .review-section { margin-bottom: 24px; }
        .review-section-title { font-size: 14px; font-weight: 600; margin-bottom: 12px; color: #333; }
        .review-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f0f0f0; font-size: 13px; }
        .review-label { color: #666; }
        .review-value { font-weight: 500; }

        .wizard-footer {
            padding: 16px 32px;
            border-top: 1px solid #e0e0e0;
            display: flex;
            justify-content: space-between;
        }

        .btn {
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            border: 1px solid #e0e0e0;
            background: #fff;
            transition: all 0.15s;
        }

        .btn:hover { background: #f5f5f5; }
        .btn-primary { background: #1a1a1a; color: #fff; border-color: #1a1a1a; }
        .btn-primary:hover { background: #333; }
        .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

        .loading { display: flex; align-items: center; gap: 8px; }
    `;

    private _controller = new TenantWizardController(this);

    connectedCallback(): void {
        super.connectedCallback();
        this._controller.connect();
    }

    disconnectedCallback(): void {
        this._controller.disconnect();
        super.disconnectedCallback();
    }

    private _onFieldChange(e: CustomEvent<WizardFieldChangeDetail>): void {
        this._controller.updateField(e.detail.field, e.detail.value);
    }

    private _renderStep3() {
        const models = ['gpt-4o', 'gpt-4o-mini', 'claude-3-sonnet', 'claude-3-opus', 'llama-3', 'somabrain-v1'];
        const d = this._controller.formData;
        return html`
            <div class="form-group">
                <label class="form-label">🤖 Model Whitelist</label>
                <div class="checkbox-group">
                    ${models.map(model => html`
                        <div class="checkbox-item ${d.allowed_models.includes(model) ? 'selected' : ''}"
                            @click=${() => this._controller.updateField('allowed_models', model)}>
                            <input type="checkbox" .checked=${d.allowed_models.includes(model)}>
                            ${model}
                        </div>
                    `)}
                </div>
            </div>

            <div class="form-group">
                <label class="form-label">🔐 Authentication Settings</label>
                <div class="toggle-row">
                    <span class="toggle-label">Enforce MFA for all users?</span>
                    <label class="toggle-switch">
                        <input type="checkbox" .checked=${d.mfa_enforced}
                            @change=${(e: Event) => this._controller.updateField('mfa_enforced', (e.target as HTMLInputElement).checked)}>
                        <span class="toggle-slider"></span>
                    </label>
                </div>
                <div class="toggle-row">
                    <span class="toggle-label">Allow Social Login (Google/GitHub)?</span>
                    <label class="toggle-switch">
                        <input type="checkbox" .checked=${d.allow_social_login}
                            @change=${(e: Event) => this._controller.updateField('allow_social_login', (e.target as HTMLInputElement).checked)}>
                        <span class="toggle-slider"></span>
                    </label>
                </div>
            </div>

            <div class="form-group">
                <label class="form-label">Session Timeout</label>
                <select class="form-select" .value=${String(d.session_timeout_hours)}
                    @change=${(e: Event) => this._controller.updateField('session_timeout_hours', (e.target as HTMLSelectElement).value)}>
                    <option value="1">1 hour</option>
                    <option value="4">4 hours</option>
                    <option value="8">8 hours</option>
                    <option value="24">24 hours</option>
                </select>
            </div>

            <div class="form-group">
                <label class="form-label">👥 Initial Admin User *</label>
                <input type="email" class="form-input" .value=${d.admin_email}
                    @input=${(e: Event) => this._controller.updateField('admin_email', (e.target as HTMLInputElement).value)}
                    placeholder="admin@acme.com">
                <div class="form-hint">This user will receive a magic link to set up their account.</div>
            </div>
        `;
    }

    private _renderStep4() {
        const d = this._controller.formData;
        const selectedTier = this._controller.tiers.find(t => t.id === d.tier_id);
        return html`
            <div class="review-section">
                <div class="review-section-title">📋 Identity</div>
                <div class="review-row"><span class="review-label">Organization</span><span class="review-value">${d.name}</span></div>
                <div class="review-row"><span class="review-label">Slug</span><span class="review-value">${d.slug}</span></div>
                <div class="review-row"><span class="review-label">Region</span><span class="review-value">${d.region.toUpperCase()}</span></div>
                ${d.compliance.length ? html`<div class="review-row"><span class="review-label">Compliance</span><span class="review-value">${d.compliance.join(', ')}</span></div>` : nothing}
                ${d.domain ? html`<div class="review-row"><span class="review-label">Custom Domain</span><span class="review-value">${d.domain}</span></div>` : nothing}
            </div>

            <div class="review-section">
                <div class="review-section-title">💳 Plan</div>
                <div class="review-row"><span class="review-label">Tier</span><span class="review-value">${selectedTier?.name || d.tier_id}</span></div>
                <div class="review-row"><span class="review-label">Price</span><span class="review-value">$${selectedTier ? (selectedTier.price_cents / 100).toFixed(0) : '?'}/mo</span></div>
            </div>

            <div class="review-section">
                <div class="review-section-title">⚙️ Defaults</div>
                <div class="review-row"><span class="review-label">Models</span><span class="review-value">${d.allowed_models.join(', ')}</span></div>
                <div class="review-row"><span class="review-label">MFA Enforced</span><span class="review-value">${d.mfa_enforced ? 'Yes' : 'No'}</span></div>
                <div class="review-row"><span class="review-label">Social Login</span><span class="review-value">${d.allow_social_login ? 'Allowed' : 'Disabled'}</span></div>
                <div class="review-row"><span class="review-label">Admin Email</span><span class="review-value">${d.admin_email}</span></div>
            </div>

            ${this._controller.error ? html`<div style="color: #ef4444; padding: 12px; background: #fef2f2; border-radius: 8px; margin-top: 16px;">⚠️ ${this._controller.error}</div>` : nothing}
        `;
    }

    private _renderContent() {
        switch (this._controller.currentStep) {
            case 1:
                return html`
                    <saas-tenant-wizard-form
                        .formData=${this._controller.formData}
                        .slugStatus=${this._controller.slugStatus}
                        @wizard-field-change=${this._onFieldChange}>
                    </saas-tenant-wizard-form>
                `;
            case 2:
                return html`
                    <saas-tenant-wizard-tier-select
                        .tiers=${this._controller.tiers}
                        .selectedTierId=${this._controller.formData.tier_id}
                        .billingEmail=${this._controller.formData.billing_email}
                        @wizard-field-change=${this._onFieldChange}>
                    </saas-tenant-wizard-tier-select>
                `;
            case 3:
                return this._renderStep3();
            case 4:
                return this._renderStep4();
            default:
                return nothing;
        }
    }

    render() {
        const steps = ['Identity', 'Plan', 'Defaults', 'Review'];
        return html`
            <div class="wizard">
                <header class="wizard-header">
                    <h2 class="wizard-title">Create New Tenant (Step ${this._controller.currentStep} of 4)</h2>
                    <button class="close-btn" @click=${() => this.dispatchEvent(new CustomEvent('close'))}>&times;</button>
                </header>

                <saas-tenant-wizard-steps
                    .currentStep=${this._controller.currentStep}
                    .steps=${steps}>
                </saas-tenant-wizard-steps>

                <div class="wizard-content">
                    ${this._renderContent()}
                </div>

                <footer class="wizard-footer">
                    <button class="btn" @click=${() => this._controller.goBack()}>
                        ${this._controller.currentStep > 1 ? '← Back' : 'Cancel'}
                    </button>
                    ${this._controller.currentStep < 4 ? html`
                        <button class="btn btn-primary" ?disabled=${!this._controller.canProceed()} @click=${() => this._controller.goNext()}>
                            Next: ${steps[this._controller.currentStep]} →
                        </button>
                    ` : html`
                        <button class="btn btn-primary" ?disabled=${this._controller.creating} @click=${() => this._controller.createTenant()}>
                            ${this._controller.creating ? html`<span class="loading">Creating...</span>` : '⚡ Create Tenant'}
                        </button>
                    `}
                </footer>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-tenant-wizard': SaasTenantWizard;
    }
}
