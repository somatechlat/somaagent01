/**
 * SaaS Login Form
 *
 * Renders the username / password form.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('saas-login-form')
export class SaasLoginForm extends LitElement {
    static styles = css`
        * { box-sizing: border-box; }

        .form-group { margin-bottom: 20px; }

        .form-label {
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            font-weight: 500;
            color: #666;
            margin-bottom: 8px;
        }

        .form-label a {
            color: #1a1a1a;
            text-decoration: none;
            font-weight: 400;
        }

        .form-input {
            width: 100%;
            padding: 12px 14px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            font-size: 14px;
            transition: border-color 0.15s ease;
            background: #fff;
            font-family: inherit;
        }

        .form-input:focus {
            outline: none;
            border-color: #1a1a1a;
        }

        .input-error {
            border-color: #ef4444 !important;
        }

        .field-error {
            display: block;
            color: #ef4444;
            font-size: 12px;
            margin-top: 6px;
        }

        .remember-row {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 24px;
        }

        .remember-row input {
            width: 16px;
            height: 16px;
            accent-color: #1a1a1a;
            cursor: pointer;
        }

        .remember-row label {
            font-size: 13px;
            color: #666;
            cursor: pointer;
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
        }

        .submit-btn:hover:not(:disabled) { background: #333; }
        .submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }

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

    @property({ type: String }) email = '';
    @property({ type: String }) password = '';
    @property({ type: String }) emailError = '';
    @property({ type: String }) error = '';
    @property({ type: Boolean }) isLoading = false;
    @property({ type: Boolean }) rememberMe = false;

    private _handleEmailInput(e: Event) {
        const value = (e.target as HTMLInputElement).value;
        this.email = value;
        this.dispatchEvent(new CustomEvent('email-input', {
            detail: { value },
            bubbles: true,
            composed: true,
        }));
    }

    private _handleEmailBlur() {
        this.dispatchEvent(new CustomEvent('email-blur', {
            bubbles: true,
            composed: true,
        }));
    }

    private _handlePasswordInput(e: Event) {
        const value = (e.target as HTMLInputElement).value;
        this.password = value;
        this.dispatchEvent(new CustomEvent('password-input', {
            detail: { value },
            bubbles: true,
            composed: true,
        }));
    }

    private _handleRememberChange(e: Event) {
        const checked = (e.target as HTMLInputElement).checked;
        this.rememberMe = checked;
        this.dispatchEvent(new CustomEvent('remember-change', {
            detail: { checked },
            bubbles: true,
            composed: true,
        }));
    }

    private _handleSubmit(e: Event) {
        e.preventDefault();
        this.dispatchEvent(new CustomEvent('submit-login', {
            bubbles: true,
            composed: true,
        }));
    }

    render() {
        return html`
            <form @submit=${this._handleSubmit}>
                <div class="form-group">
                    <label class="form-label">Email</label>
                    <input
                        type="email"
                        class="form-input ${this.emailError ? 'input-error' : ''}"
                        placeholder="name@company.com"
                        .value=${this.email}
                        @input=${this._handleEmailInput}
                        @blur=${this._handleEmailBlur}
                        required
                        autocomplete="email"
                    />
                    ${this.emailError ? html`<span class="field-error">${this.emailError}</span>` : ''}
                </div>

                <div class="form-group">
                    <label class="form-label">Password <a href="/forgot-password">Forgot?</a></label>
                    <input
                        type="password"
                        class="form-input"
                        placeholder="Enter your password"
                        .value=${this.password}
                        @input=${this._handlePasswordInput}
                        required
                        autocomplete="current-password"
                        minlength="8"
                    />
                </div>

                <div class="remember-row">
                    <input
                        type="checkbox"
                        id="remember"
                        .checked=${this.rememberMe}
                        @change=${this._handleRememberChange}
                    />
                    <label for="remember">Remember me</label>
                </div>

                <button type="submit" class="submit-btn" ?disabled=${this.isLoading}>
                    ${this.isLoading ? html`<span class="spinner"></span>Signing in...` : 'Sign in'}
                </button>
            </form>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-login-form': SaasLoginForm;
    }
}
