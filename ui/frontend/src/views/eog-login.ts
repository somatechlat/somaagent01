/**
 * Eye of God Login Page
 * Per Eye of God UIX Design - Authentication
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - Keycloak OIDC integration
 * - Secure token handling
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import '../components/eog-input.js';
import '../components/eog-button.js';
import './eog-enterprise-settings.js';

@customElement('eog-login')
export class EogLogin extends LitElement {
    static styles = css`
        :host {
            display: flex;
            min-height: 100vh;
            background: var(--eog-bg-void, #0f172a);
            color: var(--eog-text-main, #e2e8f0);
        }

        .login-container {
            display: flex;
            width: 100%;
        }

        .login-left {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: var(--eog-spacing-2xl, 48px);
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        }

        .login-right {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: var(--eog-spacing-2xl, 48px);
            background: var(--eog-surface, rgba(30, 41, 59, 0.85));
        }

        @media (max-width: 768px) {
            .login-container {
                flex-direction: column;
            }
            .login-left {
                padding: var(--eog-spacing-lg, 24px);
            }
        }

        .brand {
            text-align: center;
            margin-bottom: var(--eog-spacing-xl, 32px);
        }

        .brand-icon {
            font-size: 72px;
            margin-bottom: var(--eog-spacing-md, 16px);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.05); opacity: 0.8; }
        }

        .brand-name {
            font-size: var(--eog-text-3xl, 30px);
            font-weight: 700;
            color: var(--eog-text-main, #e2e8f0);
            margin-bottom: var(--eog-spacing-sm, 8px);
        }

        .brand-tagline {
            font-size: var(--eog-text-base, 14px);
            color: var(--eog-text-dim, #64748b);
            max-width: 300px;
        }

        .features {
            display: flex;
            flex-direction: column;
            gap: var(--eog-spacing-md, 16px);
            margin-top: var(--eog-spacing-xl, 32px);
        }

        .feature {
            display: flex;
            align-items: center;
            gap: var(--eog-spacing-sm, 8px);
            font-size: var(--eog-text-sm, 13px);
            color: var(--eog-text-dim, #64748b);
        }

        .feature-icon {
            font-size: 20px;
        }

        .login-form {
            width: 100%;
            max-width: 400px;
        }

        .form-header {
            text-align: center;
            margin-bottom: var(--eog-spacing-xl, 32px);
        }

        .form-title {
            font-size: var(--eog-text-2xl, 24px);
            font-weight: 600;
            color: var(--eog-text-main, #e2e8f0);
            margin-bottom: var(--eog-spacing-xs, 4px);
        }

        .form-subtitle {
            font-size: var(--eog-text-sm, 13px);
            color: var(--eog-text-dim, #64748b);
        }

        .form-fields {
            display: flex;
            flex-direction: column;
            gap: var(--eog-spacing-md, 16px);
            margin-bottom: var(--eog-spacing-lg, 24px);
        }

        .form-options {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--eog-spacing-lg, 24px);
            font-size: var(--eog-text-sm, 13px);
        }

        .remember-me {
            display: flex;
            align-items: center;
            gap: var(--eog-spacing-xs, 4px);
            color: var(--eog-text-dim, #64748b);
        }

        .forgot-link {
            color: var(--eog-accent, #94a3b8);
            text-decoration: none;
            transition: color 0.2s;
        }

        .forgot-link:hover {
            color: var(--eog-text-main, #e2e8f0);
        }

        .submit-btn {
            width: 100%;
            margin-bottom: var(--eog-spacing-md, 16px);
        }

        .divider {
            display: flex;
            align-items: center;
            gap: var(--eog-spacing-md, 16px);
            margin: var(--eog-spacing-lg, 24px) 0;
            color: var(--eog-text-dim, #64748b);
            font-size: var(--eog-text-sm, 13px);
        }

        .divider::before,
        .divider::after {
            content: '';
            flex: 1;
            height: 1px;
            background: var(--eog-border-color, rgba(255, 255, 255, 0.1));
        }

        .sso-options {
            display: flex;
            flex-direction: column;
            gap: var(--eog-spacing-sm, 8px);
        }

        .sso-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: var(--eog-spacing-sm, 8px);
            padding: var(--eog-spacing-sm, 8px) var(--eog-spacing-md, 16px);
            border-radius: var(--eog-radius-md, 8px);
            border: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.1));
            background: transparent;
            color: var(--eog-text-main, #e2e8f0);
            font-size: var(--eog-text-sm, 13px);
            cursor: pointer;
            transition: all 0.2s;
        }

        .sso-btn:hover {
            border-color: var(--eog-accent, #94a3b8);
            background: rgba(148, 163, 184, 0.1);
        }

        .sso-icon {
            font-size: 18px;
        }

        .error-message {
            padding: var(--eog-spacing-md, 16px);
            border-radius: var(--eog-radius-md, 8px);
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid var(--eog-danger, #ef4444);
            color: var(--eog-danger, #ef4444);
            font-size: var(--eog-text-sm, 13px);
            margin-bottom: var(--eog-spacing-md, 16px);
        }

        .footer {
            margin-top: var(--eog-spacing-xl, 32px);
            text-align: center;
            font-size: var(--eog-text-xs, 11px);
            color: var(--eog-text-dim, #64748b);
        }

        .footer a {
            color: var(--eog-accent, #94a3b8);
            text-decoration: none;
        }

        .enterprise-cog {
            position: fixed;
            bottom: 24px;
            left: 24px;
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 20px;
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 9999px;
            color: rgba(255, 255, 255, 0.5);
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            z-index: 100;
            outline: none;
        }

        .enterprise-cog::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(
                90deg,
                transparent,
                rgba(255, 255, 255, 0.1),
                transparent
            );
            transition: 0.5s;
        }

        .enterprise-cog:hover {
            background: rgba(255, 255, 255, 0.1);
            color: white;
            border-color: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2), 0 4px 6px -2px rgba(0, 0, 0, 0.1);
        }

        .enterprise-cog:hover::before {
            left: 100%;
        }

        .cog-icon {
            font-size: 18px;
            animation: spin 10s linear infinite;
        }

        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .cog-label {
            letter-spacing: 0.5px;
            text-transform: uppercase;
            font-size: 11px;
        }
    `;

    @state() private _username = '';
    @state() private _password = '';
    @state() private _rememberMe = false;
    @state() private _isLoading = false;
    @state() private _error: string | null = null;

    @property({ type: String }) keycloakUrl = '/auth';
    @property({ type: String }) realm = 'somaagent';
    @property({ type: String }) clientId = 'eye-of-god';

    @state() private _showEnterpriseSettings = false;

    render() {
        return html`
            <div class="login-container">
                <aside class="login-left">
                    <div class="brand">
                        <div class="brand-icon">👁️</div>
                        <h1 class="brand-name">Eye of God</h1>
                        <p class="brand-tagline">
                            Advanced AI Agent Interface with cognitive enhancement and memory persistence
                        </p>
                    </div>
                    <div class="features">
                        <div class="feature">
                            <span class="feature-icon">🧠</span>
                            <span>Persistent memory with SomaBrain</span>
                        </div>
                        <div class="feature">
                            <span class="feature-icon">🔧</span>
                            <span>Integrated tool ecosystem</span>
                        </div>
                        <div class="feature">
                            <span class="feature-icon">🎨</span>
                            <span>Customizable themes</span>
                        </div>
                        <div class="feature">
                            <span class="feature-icon">🎤</span>
                            <span>Voice-first interaction</span>
                        </div>
                        <div class="feature">
                            <span class="feature-icon">🔒</span>
                            <span>Enterprise SSO with Keycloak</span>
                        </div>
                    </div>

                    <!-- Enterprise Settings Cog using Creative Glassmorphism -->
                    <button 
                        class="enterprise-cog" 
                        @click=${() => this._showEnterpriseSettings = true}
                        title="Enterprise Configuration"
                    >
                        <span class="cog-icon">⚙️</span>
                        <span class="cog-label">Enterprise</span>
                    </button>
                </aside>

                <main class="login-right">
                    <div class="login-form">
                        <header class="form-header">
                            <h2 class="form-title">Welcome Back</h2>
                            <p class="form-subtitle">Sign in to access your agent</p>
                        </header>

                        ${this._error ? html`
                            <div class="error-message">${this._error}</div>
                        ` : ''}

                        <form @submit=${this._handleSubmit}>
                            <div class="form-fields">
                                <eog-input
                                    label="Username or Email"
                                    type="text"
                                    placeholder="Enter your username"
                                    .value=${this._username}
                                    @eog-input=${(e: CustomEvent) => this._username = e.detail.value}
                                    required
                                ></eog-input>

                                <eog-input
                                    label="Password"
                                    type="password"
                                    placeholder="Enter your password"
                                    .value=${this._password}
                                    @eog-input=${(e: CustomEvent) => this._password = e.detail.value}
                                    required
                                ></eog-input>
                            </div>

                            <div class="form-options">
                                <label class="remember-me">
                                    <input 
                                        type="checkbox" 
                                        .checked=${this._rememberMe}
                                        @change=${(e: Event) => this._rememberMe = (e.target as HTMLInputElement).checked}
                                    />
                                    Remember me
                                </label>
                                <a href="/forgot-password" class="forgot-link">Forgot password?</a>
                            </div>

                            <eog-button 
                                class="submit-btn" 
                                type="submit"
                                ?loading=${this._isLoading}
                            >
                                Sign In
                            </eog-button>
                        </form>

                        <div class="divider">or continue with</div>

                        <div class="sso-options">
                            <button class="sso-btn" @click=${this._handleKeycloakLogin}>
                                <span class="sso-icon">🔑</span>
                                Sign in with Keycloak SSO
                            </button>
                            <button class="sso-btn" @click=${this._handleSAMLLogin}>
                                <span class="sso-icon">🏢</span>
                                Enterprise SAML
                            </button>
                        </div>

                        <footer class="footer">
                            <p>
                                By signing in, you agree to our
                                <a href="/terms">Terms of Service</a> and
                                <a href="/privacy">Privacy Policy</a>
                            </p>
                            <p style="margin-top: 8px;">
                                Don't have an account? <a href="/register">Contact Admin</a>
                            </p>
                        </footer>
                    </div>
                </main>
            </div>

            <eog-enterprise-settings
                .open=${this._showEnterpriseSettings}
                @close=${() => this._showEnterpriseSettings = false}
            ></eog-enterprise-settings>
        `;
    }

    private async _handleSubmit(e: Event) {
        e.preventDefault();

        if (!this._username || !this._password) {
            this._error = 'Please enter username and password';
            return;
        }

        this._isLoading = true;
        this._error = null;

        try {
            const response = await fetch('/api/v2/auth/token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: this._username,
                    password: this._password,
                }),
            });

            if (!response.ok) {
                throw new Error('Invalid credentials');
            }

            const data = await response.json();

            // Store token
            localStorage.setItem('eog_auth_token', data.access_token);

            if (this._rememberMe) {
                localStorage.setItem('eog_remember_user', this._username);
            }

            // Fetch user info
            const userResponse = await fetch('/api/v2/auth/me', {
                headers: { 'Authorization': `Bearer ${data.access_token}` }
            });

            if (userResponse.ok) {
                const user = await userResponse.json();
                localStorage.setItem('eog_user', JSON.stringify(user));
            }

            // Redirect to app
            window.location.href = '/mode-select';

        } catch (error) {
            this._error = error instanceof Error ? error.message : 'Login failed';
        } finally {
            this._isLoading = false;
        }
    }

    private _handleKeycloakLogin() {
        // Redirect to Keycloak OIDC login
        const redirectUri = encodeURIComponent(window.location.origin + '/auth/callback');
        const keycloakAuthUrl = `${this.keycloakUrl}/realms/${this.realm}/protocol/openid-connect/auth`;
        const params = new URLSearchParams({
            client_id: this.clientId,
            redirect_uri: redirectUri,
            response_type: 'code',
            scope: 'openid profile email',
        });

        window.location.href = `${keycloakAuthUrl}?${params.toString()}`;
    }

    private _handleSAMLLogin() {
        // Redirect to SAML SSO
        window.location.href = `${this.keycloakUrl}/realms/${this.realm}/protocol/saml`;
    }

    connectedCallback() {
        super.connectedCallback();

        // Check for remembered user
        const rememberedUser = localStorage.getItem('eog_remember_user');
        if (rememberedUser) {
            this._username = rememberedUser;
            this._rememberMe = true;
        }

        // Check for existing valid token
        const token = localStorage.getItem('eog_auth_token');
        if (token) {
            this._validateExistingToken(token);
        }
    }

    private async _validateExistingToken(token: string) {
        try {
            const response = await fetch('/api/v2/auth/me', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                window.location.href = '/mode-select';
            } else {
                localStorage.removeItem('eog_auth_token');
            }
        } catch {
            localStorage.removeItem('eog_auth_token');
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-login': EogLogin;
    }
}
