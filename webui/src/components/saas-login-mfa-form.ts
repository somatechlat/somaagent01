/**
 * SaaS Login MFA Form
 *
 * Renders the MFA verification step during login.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

@customElement('saas-login-mfa-form')
export class SaasLoginMfaForm extends LitElement {
    static styles = css`
        * { box-sizing: border-box; }

        .mfa-header {
            margin-bottom: 20px;
        }

        .mfa-title {
            font-size: 18px;
            font-weight: 600;
            margin: 0 0 6px 0;
        }

        .mfa-subtitle {
            font-size: 14px;
            color: #666;
            margin: 0;
        }

        .form-group { margin-bottom: 20px; }

        .form-label {
            display: block;
            font-size: 13px;
            font-weight: 500;
            color: #666;
            margin-bottom: 8px;
        }

        .form-input {
            width: 100%;
            padding: 12px 14px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            font-size: 18px;
            letter-spacing: 8px;
            text-align: center;
            transition: border-color 0.15s ease;
            background: #fff;
            font-family: inherit;
        }

        .form-input:focus {
            outline: none;
            border-color: #1a1a1a;
        }

        .submit-btn {
            width: 100%;
            padding: 12px 16px;
            border-radius: 8px;
            background: #1a1a1a;
            color: white;
            font-size: 14px;
            font-weight: 600;
            border: none;
            cursor: pointer;
            transition: background 0.15s ease;
            font-family: inherit;
            margin-bottom: 12px;
        }

        .submit-btn:hover:not(:disabled) { background: #333; }
        .submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }

        .back-btn {
            width: 100%;
            padding: 12px 16px;
            border-radius: 8px;
            background: #fff;
            color: #1a1a1a;
            font-size: 14px;
            font-weight: 600;
            border: 1px solid #e0e0e0;
            cursor: pointer;
            transition: background 0.15s ease;
            font-family: inherit;
        }

        .back-btn:hover { background: #fafafa; }

        .spinner {
            width: 14px;
            height: 14px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.6s linear infinite;
            display: inline-block;
            margin-right: 8px;
        }

        @keyframes spin { to { transform: rotate(360deg); } }
    `;

    @property({ type: String }) error = '';
    @property({ type: Boolean }) isLoading = false;

    @state() private _code = '';

    private _handleInput(e: Event) {
        this._code = (e.target as HTMLInputElement).value;
    }

    private _handleSubmit(e: Event) {
        e.preventDefault();
        this.dispatchEvent(new CustomEvent('verify-mfa', {
            detail: { code: this._code },
            bubbles: true,
            composed: true,
        }));
    }

    private _handleBack() {
        this._code = '';
        this.dispatchEvent(new CustomEvent('back-to-credentials', {
            bubbles: true,
            composed: true,
        }));
    }

    render() {
        return html`
            <form @submit=${this._handleSubmit}>
                <div class="mfa-header">
                    <h3 class="mfa-title">Two-Factor Authentication</h3>
                    <p class="mfa-subtitle">Enter the 6-digit code from your authenticator app.</p>
                </div>

                <div class="form-group">
                    <label class="form-label" for="mfa-code">Verification Code</label>
                    <input
                        id="mfa-code"
                        type="text"
                        class="form-input"
                        placeholder="000000"
                        maxlength="6"
                        .value=${this._code}
                        @input=${this._handleInput}
                        required
                        autocomplete="one-time-code"
                    />
                </div>

                <button
                    type="submit"
                    class="submit-btn"
                    ?disabled=${this.isLoading || this._code.length !== 6}
                >
                    ${this.isLoading ? html`<span class="spinner"></span>Verifying...` : 'Verify'}
                </button>

                <button
                    type="button"
                    class="back-btn"
                    ?disabled=${this.isLoading}
                    @click=${this._handleBack}
                >
                    Back to sign in
                </button>
            </form>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-login-mfa-form': SaasLoginMfaForm;
    }
}
