/**
 * SomaAgent SaaS — Register Page
 * Per UI_SCREENS_SRS.md Section 3.2
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - Real API integration (/api/v2/auth/register)
 * - Minimal white/black design per UI_STYLE_GUIDE.md
 * - NO EMOJIS - Material Symbols only
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

@customElement('saas-register')
export class SaasRegister extends LitElement {
    static styles = css`
        :host {
            display: block;
            min-height: 100vh;
            font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
            background: var(--saas-bg-page, #f5f5f5);
            color: var(--saas-text-primary, #1a1a1a);
        }

        * { box-sizing: border-box; }

        .register-page {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 24px;
        }

        .register-card {
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 12px;
            box-shadow: var(--saas-shadow-md, 0 2px 8px rgba(0,0,0,0.06));
            width: 100%;
            max-width: 400px;
            padding: 40px;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 32px;
        }

        .brand-icon {
            width: 40px;
            height: 40px;
            background: #1a1a1a;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .brand-icon svg {
            width: 20px;
            height: 20px;
            stroke: white;
            fill: none;
        }

        .brand-name { font-size: 18px; font-weight: 600; }

        .form-header { margin-bottom: 28px; }
        .form-title { font-size: 22px; font-weight: 600; margin: 0 0 8px 0; }
        .form-subtitle { font-size: 14px; color: var(--saas-text-secondary, #666); margin: 0; }
        .form-subtitle a { color: #1a1a1a; font-weight: 500; text-decoration: underline; }

        .form-group { margin-bottom: 20px; }
        .form-label { display: block; font-size: 13px; font-weight: 500; color: #666; margin-bottom: 8px; }

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
        .form-input:focus { outline: none; border-color: #1a1a1a; }
        .form-input.error { border-color: #ef4444; }

        .form-hint { font-size: 12px; color: #999; margin-top: 6px; }

        .terms-row { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 24px; }
        .terms-row input { width: 16px; height: 16px; accent-color: #1a1a1a; cursor: pointer; margin-top: 2px; }
        .terms-row label { font-size: 13px; color: #666; cursor: pointer; line-height: 1.4; }
        .terms-row a { color: #1a1a1a; text-decoration: underline; }

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
            width: 14px; height: 14px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.6s linear infinite;
            display: inline-block;
            margin-right: 8px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        .error-message {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.2);
            border-radius: 8px;
            padding: 12px 14px;
            margin-bottom: 20px;
            color: #ef4444;
            font-size: 13px;
        }

        .success-message {
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.2);
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }
        .success-message h3 { margin: 0 0 8px 0; color: #16a34a; font-size: 18px; }
        .success-message p { margin: 0; color: #666; font-size: 14px; }

        .footer {
            text-align: center;
            margin-top: 28px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }
        .footer-text { font-size: 12px; color: #999; }
        .footer-text a { color: #666; text-decoration: none; }
    `;

    @state() private _name = '';
    @state() private _email = '';
    @state() private _password = '';
    @state() private _termsAccepted = false;
    @state() private _error = '';
    @state() private _isLoading = false;
    @state() private _success = false;

    render() {
        if (this._success) {
            return html`
                <div class="register-page">
                    <div class="register-card">
                        <div class="brand">
                            <div class="brand-icon">
                                <svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <rect x="3" y="3" width="7" height="7" rx="1"/>
                                    <rect x="14" y="3" width="7" height="7" rx="1"/>
                                    <rect x="14" y="14" width="7" height="7" rx="1"/>
                                    <rect x="3" y="14" width="7" height="7" rx="1"/>
                                </svg>
                            </div>
                            <span class="brand-name">SomaAgent SaaS</span>
                        </div>
                        
                        <div class="success-message">
                            <h3>Check your email</h3>
                            <p>We've sent a verification link to <strong>${this._email}</strong>. Please check your inbox and click the link to complete your registration.</p>
                        </div>

                        <div class="footer">
                            <p class="footer-text">
                                <a href="/login">Return to login</a>
                            </p>
                        </div>
                    </div>
                </div>
            `;
        }

        return html`
            <div class="register-page">
                <div class="register-card">
                    <div class="brand">
                        <div class="brand-icon">
                            <svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="3" y="3" width="7" height="7" rx="1"/>
                                <rect x="14" y="3" width="7" height="7" rx="1"/>
                                <rect x="14" y="14" width="7" height="7" rx="1"/>
                                <rect x="3" y="14" width="7" height="7" rx="1"/>
                            </svg>
                        </div>
                        <span class="brand-name">SomaAgent SaaS</span>
                    </div>

                    <div class="form-header">
                        <h2 class="form-title">Create account</h2>
                        <p class="form-subtitle">
                            Already have an account? <a href="/login">Sign in</a>
                        </p>
                    </div>

                    ${this._error ? html`<div class="error-message">${this._error}</div>` : ''}

                    <form @submit=${this._handleRegister}>
                        <div class="form-group">
                            <label class="form-label">Full Name</label>
                            <input type="text" class="form-input" placeholder="John Doe"
                                .value=${this._name}
                                @input=${(e: Event) => this._name = (e.target as HTMLInputElement).value}
                                required autocomplete="name" minlength="2">
                        </div>

                        <div class="form-group">
                            <label class="form-label">Work Email</label>
                            <input type="email" class="form-input" placeholder="name@company.com"
                                .value=${this._email}
                                @input=${(e: Event) => this._email = (e.target as HTMLInputElement).value}
                                required autocomplete="email">
                        </div>

                        <div class="form-group">
                            <label class="form-label">Password</label>
                            <input type="password" class="form-input" placeholder="Create a strong password"
                                .value=${this._password}
                                @input=${(e: Event) => this._password = (e.target as HTMLInputElement).value}
                                required autocomplete="new-password" minlength="8">
                            <p class="form-hint">Minimum 8 characters</p>
                        </div>

                        <div class="terms-row">
                            <input type="checkbox" id="terms" .checked=${this._termsAccepted}
                                @change=${(e: Event) => this._termsAccepted = (e.target as HTMLInputElement).checked}>
                            <label for="terms">
                                I agree to the <a href="/terms" target="_blank">Terms of Service</a> 
                                and <a href="/privacy" target="_blank">Privacy Policy</a>
                            </label>
                        </div>

                        <button type="submit" class="submit-btn" ?disabled=${this._isLoading || !this._termsAccepted}>
                            ${this._isLoading ? html`<span class="spinner"></span>Creating account...` : 'Create account'}
                        </button>
                    </form>

                    <div class="footer">
                        <p class="footer-text">Powered by <a href="https://somatech.lat" target="_blank">SomaTech LAT</a></p>
                    </div>
                </div>
            </div>
        `;
    }

    private async _handleRegister(e: Event) {
        e.preventDefault();

        if (!this._name || this._name.length < 2) {
            this._error = 'Please enter your full name';
            return;
        }
        if (!this._email) {
            this._error = 'Please enter your email address';
            return;
        }
        if (!this._password || this._password.length < 8) {
            this._error = 'Password must be at least 8 characters';
            return;
        }
        if (!this._termsAccepted) {
            this._error = 'Please accept the Terms of Service';
            return;
        }

        this._isLoading = true;
        this._error = '';

        try {
            const response = await fetch('/api/v2/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: this._name,
                    email: this._email,
                    password: this._password
                }),
            });

            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.detail || 'Registration failed');
            }

            this._success = true;
        } catch (err) {
            this._error = err instanceof Error ? err.message : 'Registration failed';
        } finally {
            this._isLoading = false;
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-register': SaasRegister;
    }
}
