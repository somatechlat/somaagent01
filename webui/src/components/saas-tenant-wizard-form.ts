/**
 * SaaS Tenant Wizard Form
 *
 * Renders the Step 1 tenant identity form.
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { TenantFormData } from '../controllers/tenant-wizard-controller.js';

export interface WizardFieldChangeDetail {
    field: keyof TenantFormData;
    value: unknown;
}

@customElement('saas-tenant-wizard-form')
export class SaasTenantWizardForm extends LitElement {
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

        .form-hint {
            font-size: 12px;
            color: #888;
            margin-top: 4px;
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

        .form-input.error {
            border-color: #ef4444;
        }

        .form-input.success {
            border-color: #16a34a;
        }

        .slug-wrapper {
            display: flex;
            gap: 0;
        }

        .slug-prefix {
            padding: 12px 14px;
            background: #f5f5f5;
            border: 1px solid #e0e0e0;
            border-right: none;
            border-radius: 8px 0 0 8px;
            font-size: 13px;
            color: #666;
            white-space: nowrap;
        }

        .slug-input {
            border-radius: 0 8px 8px 0;
            flex: 1;
        }

        .slug-status {
            font-size: 12px;
            margin-top: 6px;
        }

        .slug-status.available {
            color: #16a34a;
        }

        .slug-status.taken {
            color: #ef4444;
        }

        .form-select {
            width: 100%;
            padding: 12px 14px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            background: #fff;
            cursor: pointer;
        }

        .checkbox-group {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
        }

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

        .checkbox-item:hover {
            border-color: #999;
        }

        .checkbox-item.selected {
            border-color: #1a1a1a;
            background: #f8f8f8;
        }
    `;

    @property({ type: Object })
    formData!: TenantFormData;

    @property({ type: String })
    slugStatus: 'checking' | 'available' | 'taken' | null = null;

    render() {
        const slugClass = this.slugStatus === 'available'
            ? 'success'
            : this.slugStatus === 'taken'
                ? 'error'
                : '';

        return html`
            <div class="form-group">
                <label class="form-label">Organization Name *</label>
                <input type="text" class="form-input" .value=${this.formData.name}
                    @input=${(e: Event) => this._emit('name', (e.target as HTMLInputElement).value)}
                    placeholder="Acme Health Solutions">
            </div>

            <div class="form-group">
                <label class="form-label">Tenant Slug (URL Namespace) *</label>
                <div class="slug-wrapper">
                    <span class="slug-prefix">https://app.soma.ai/tenant/</span>
                    <input type="text" class="form-input slug-input ${slugClass}"
                        .value=${this.formData.slug}
                        @input=${(e: Event) => this._emit('slug', (e.target as HTMLInputElement).value)}>
                </div>
                ${this.slugStatus === 'checking' ? html`<div class="slug-status">Checking availability...</div>` : nothing}
                ${this.slugStatus === 'available' ? html`<div class="slug-status available">✅ Available</div>` : nothing}
                ${this.slugStatus === 'taken' ? html`<div class="slug-status taken">❌ Already taken</div>` : nothing}
            </div>

            <div class="form-group">
                <label class="form-label">Data Residency (Region) *</label>
                <select class="form-select" .value=${this.formData.region}
                    @change=${(e: Event) => this._emit('region', (e.target as HTMLSelectElement).value)}>
                    <option value="us-east">🇺🇸 US-East (N. Virginia)</option>
                    <option value="us-west">🇺🇸 US-West (Oregon)</option>
                    <option value="eu-west">🇪🇺 EU-West (Ireland)</option>
                    <option value="ap-southeast">🇸🇬 Asia-Pacific (Singapore)</option>
                </select>
                <div class="form-hint">Determines where database and vector storage are located.</div>
            </div>

            <div class="form-group">
                <label class="form-label">Compliance Frameworks</label>
                <div class="checkbox-group">
                    ${['GDPR', 'HIPAA', 'SOC2'].map(fw => html`
                        <div class="checkbox-item ${this.formData.compliance.includes(fw) ? 'selected' : ''}"
                            @click=${() => this._emit('compliance', fw)}>
                            <input type="checkbox" .checked=${this.formData.compliance.includes(fw)}>
                            ${fw}
                        </div>
                    `)}
                </div>
            </div>

            <div class="form-group">
                <label class="form-label">Custom Domain (Optional)</label>
                <input type="text" class="form-input" .value=${this.formData.domain}
                    @input=${(e: Event) => this._emit('domain', (e.target as HTMLInputElement).value)}
                    placeholder="console.acme-health.com">
                <div class="form-hint">Requires DNS CNAME verification after creation.</div>
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
        'saas-tenant-wizard-form': SaasTenantWizardForm;
    }
}
