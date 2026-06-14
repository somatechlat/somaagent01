/**
 * SomaAgent SaaS — Login Page
 * Per UI_SCREENS_SRS.md Section 3.1 and UI_STYLE_GUIDE.md
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - OAuth integration (Google, Keycloak SSO)
 * - Minimal white/black design
 * - Glassmorphism Enterprise SSO Modal
 * - LDAP, Active Directory, SAML, OIDC support
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { LoginController } from '../controllers/login-controller.js';
import '../components/saas-login-form.js';
import '../components/saas-login-mfa-form.js';
import '../components/saas-login-sso-panel.js';

@customElement('saas-login')
export class SaasLogin extends LitElement {
    static styles = css`
        :host {
            display: block;
            min-height: 100vh;
            font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
            background: var(--saas-bg-page, #f5f5f5);
            color: var(--saas-text-primary, #1a1a1a);
        }

        * { box-sizing: border-box; }

        .login-page {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 24px;
        }

        .login-card {
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

        .brand-name {
            font-size: 18px;
            font-weight: 600;
        }

        .form-header { margin-bottom: 28px; }
        .form-title { font-size: 22px; font-weight: 600; margin: 0 0 8px 0; }
        .form-subtitle { font-size: 14px; color: var(--saas-text-secondary, #666); margin: 0; }
        .form-subtitle a { color: #1a1a1a; font-weight: 500; text-decoration: underline; }

        .error-message {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.2);
            border-radius: 8px;
            padding: 12px 14px;
            margin-bottom: 20px;
            color: #ef4444;
            font-size: 13px;
        }

        .divider {
            display: flex;
            align-items: center;
            gap: 16px;
            margin: 24px 0;
            color: var(--saas-text-muted, #999);
            font-size: 12px;
        }
        .divider::before, .divider::after { content: ''; flex: 1; height: 1px; background: #e0e0e0; }

        .footer {
            text-align: center;
            margin-top: 28px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }
        .footer-text { font-size: 12px; color: #999; }
        .footer-text a { color: #666; text-decoration: none; }
    `;

    @state() private _email = '';
    @state() private _password = '';
    @state() private _error = '';
    @state() private _emailError = '';
    @state() private _isLoading = false;
    @state() private _rememberMe = false;
    @state() private _showSSOModal = false;
    @state() private _mfaStep = false;
    @state() private _mfaToken = '';

    private _controller = new LoginController();

    /**
     * RFC 5322 compliant email validation regex.
     * Per design.md Section 1.2, 2.1 - Email Validation
     */
    private static readonly EMAIL_REGEX = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;

    private _validateEmail(email: string): boolean {
        if (!email) return false;
        if (email.length > 254) return false;
        return SaasLogin.EMAIL_REGEX.test(email);
    }

    private _onEmailInput(e: Event) {
        const detail = (e as CustomEvent<{ value: string }>).detail;
        this._email = detail.value;
        if (this._emailError && this._email) {
            this._emailError = '';
        }
    }

    private _onEmailBlur() {
        if (this._email && !this._validateEmail(this._email)) {
            this._emailError = 'Please enter a valid email address';
        } else {
            this._emailError = '';
        }
    }

    private _onPasswordInput(e: Event) {
        const detail = (e as CustomEvent<{ value: string }>).detail;
        this._password = detail.value;
    }

    private _onRememberChange(e: Event) {
        const detail = (e as CustomEvent<{ checked: boolean }>).detail;
        this._rememberMe = detail.checked;
    }

    private async _onSubmitLogin() {
        if (!this._email || !this._password) {
            this._error = 'Please enter both email and password';
            return;
        }

        if (!this._validateEmail(this._email)) {
            this._emailError = 'Please enter a valid email address';
            return;
        }

        if (this._password.length < 8) {
            this._error = 'Password must be at least 8 characters';
            return;
        }

        this._isLoading = true;
        this._error = '';

        const result = await this._controller.login({
            email: this._email,
            password: this._password,
            rememberMe: this._rememberMe,
        });

        this._isLoading = false;

        if (!result.success) {
            this._error = result.error || 'Login failed';
            return;
        }

        if (result.requiresMfa) {
            this._mfaStep = true;
            this._mfaToken = result.mfaToken || '';
        }
    }

    private async _onVerifyMfa(e: Event) {
        const detail = (e as CustomEvent<{ code: string }>).detail;
        this._isLoading = true;
        this._error = '';

        const result = await this._controller.verifyMfa(detail.code, this._mfaToken);

        this._isLoading = false;

        if (!result.success) {
            this._error = result.error || 'MFA verification failed';
        }
    }

    private _onBackFromMfa() {
        this._mfaStep = false;
        this._error = '';
    }

    private _onSsoError(e: Event) {
        const detail = (e as CustomEvent<{ message: string }>).detail;
        this._error = detail.message;
    }

    render() {
        return html`
            <div class="login-page">
                <div class="login-card">
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
                        <h2 class="form-title">Sign in</h2>
                        <p class="form-subtitle">
                            Don't have an account? <a href="/register">Get started</a>
                        </p>
                    </div>

                    ${this._error ? html`<div class="error-message">${this._error}</div>` : ''}

                    <saas-login-sso-panel
                        .open=${this._showSSOModal}
                        .controller=${this._controller}
                        @close=${() => { this._showSSOModal = false; }}
                        @sso-error=${this._onSsoError}
                    ></saas-login-sso-panel>

                    <div class="divider">or</div>

                    ${this._mfaStep
                        ? html`
                            <saas-login-mfa-form
                                .error=${this._error}
                                .isLoading=${this._isLoading}
                                @verify-mfa=${this._onVerifyMfa}
                                @back-to-credentials=${this._onBackFromMfa}
                            ></saas-login-mfa-form>
                        `
                        : html`
                            <saas-login-form
                                .email=${this._email}
                                .password=${this._password}
                                .emailError=${this._emailError}
                                .isLoading=${this._isLoading}
                                .rememberMe=${this._rememberMe}
                                @email-input=${this._onEmailInput}
                                @email-blur=${this._onEmailBlur}
                                @password-input=${this._onPasswordInput}
                                @remember-change=${this._onRememberChange}
                                @submit-login=${this._onSubmitLogin}
                            ></saas-login-form>
                        `
                    }

                    <div class="footer">
                        <p class="footer-text">Powered by <a href="https://somatech.lat" target="_blank">SomaTech LAT</a></p>
                    </div>
                </div>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-login': SaasLogin;
    }
}
