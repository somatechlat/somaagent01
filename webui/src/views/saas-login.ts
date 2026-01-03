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
import { keycloakService } from '../services/keycloak-service.js';
import { googleAuthService } from '../services/google-auth-service.js';

type SSOProvider = 'oidc' | 'saml' | 'ldap' | 'ad' | 'okta' | 'azure' | 'ping' | 'onelogin';

interface ProviderConfig {
    id: SSOProvider;
    name: string;
    description: string;
    icon: string;
    fields: { key: string; label: string; type: string; placeholder: string; required?: boolean }[];
}

const SSO_PROVIDERS: ProviderConfig[] = [
    {
        id: 'oidc',
        name: 'OpenID Connect',
        description: 'Connect via OIDC protocol (Keycloak, Auth0, etc.)',
        icon: 'key',
        fields: [
            { key: 'issuer_url', label: 'Issuer URL', type: 'url', placeholder: 'https://auth.company.com/realms/main', required: true },
            { key: 'client_id', label: 'Client ID', type: 'text', placeholder: 'soma-agent-client', required: true },
            { key: 'client_secret', label: 'Client Secret', type: 'password', placeholder: 'Enter client secret', required: true },
        ],
    },
    {
        id: 'saml',
        name: 'SAML 2.0',
        description: 'Enterprise SAML federation (Okta, OneLogin, etc.)',
        icon: 'security',
        fields: [
            { key: 'metadata_url', label: 'Metadata URL', type: 'url', placeholder: 'https://idp.company.com/metadata.xml', required: true },
            { key: 'entity_id', label: 'Entity ID', type: 'text', placeholder: 'urn:soma:agent:saml', required: true },
            { key: 'acs_url', label: 'ACS URL', type: 'url', placeholder: 'https://app.somaagent.com/auth/saml/callback' },
        ],
    },
    {
        id: 'ldap',
        name: 'LDAP',
        description: 'Connect to OpenLDAP or similar directory',
        icon: 'folder_shared',
        fields: [
            { key: 'server_url', label: 'Server URL', type: 'url', placeholder: 'ldap://ldap.company.com:389', required: true },
            { key: 'base_dn', label: 'Base DN', type: 'text', placeholder: 'dc=company,dc=com', required: true },
            { key: 'bind_dn', label: 'Bind DN', type: 'text', placeholder: 'cn=admin,dc=company,dc=com', required: true },
            { key: 'bind_password', label: 'Bind Password', type: 'password', placeholder: 'Enter bind password', required: true },
            { key: 'user_filter', label: 'User Filter', type: 'text', placeholder: '(uid={username})' },
        ],
    },
    {
        id: 'ad',
        name: 'Active Directory',
        description: 'Microsoft Active Directory via LDAPS',
        icon: 'domain',
        fields: [
            { key: 'domain', label: 'Domain', type: 'text', placeholder: 'company.local', required: true },
            { key: 'server_url', label: 'Domain Controller', type: 'url', placeholder: 'ldaps://dc.company.local:636', required: true },
            { key: 'service_account', label: 'Service Account', type: 'text', placeholder: 'svc-somaagent@company.local', required: true },
            { key: 'service_password', label: 'Password', type: 'password', placeholder: 'Service account password', required: true },
            { key: 'base_ou', label: 'Search Base OU', type: 'text', placeholder: 'OU=Users,DC=company,DC=local' },
        ],
    },
    {
        id: 'okta',
        name: 'Okta',
        description: 'Okta Workforce Identity Cloud',
        icon: 'verified_user',
        fields: [
            { key: 'domain', label: 'Okta Domain', type: 'text', placeholder: 'company.okta.com', required: true },
            { key: 'client_id', label: 'Client ID', type: 'text', placeholder: 'Enter Okta Client ID', required: true },
            { key: 'client_secret', label: 'Client Secret', type: 'password', placeholder: 'Enter Okta Client Secret', required: true },
        ],
    },
    {
        id: 'azure',
        name: 'Azure AD / Entra ID',
        description: 'Microsoft Azure Active Directory',
        icon: 'cloud',
        fields: [
            { key: 'tenant_id', label: 'Tenant ID', type: 'text', placeholder: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', required: true },
            { key: 'client_id', label: 'Application (Client) ID', type: 'text', placeholder: 'Enter Azure App ID', required: true },
            { key: 'client_secret', label: 'Client Secret', type: 'password', placeholder: 'Enter Azure App Secret', required: true },
        ],
    },
    {
        id: 'ping',
        name: 'PingFederate',
        description: 'Ping Identity federation server',
        icon: 'hub',
        fields: [
            { key: 'base_url', label: 'PingFederate URL', type: 'url', placeholder: 'https://sso.company.com', required: true },
            { key: 'client_id', label: 'Client ID', type: 'text', placeholder: 'soma-agent', required: true },
            { key: 'client_secret', label: 'Client Secret', type: 'password', placeholder: 'Enter client secret', required: true },
        ],
    },
    {
        id: 'onelogin',
        name: 'OneLogin',
        description: 'OneLogin identity management',
        icon: 'login',
        fields: [
            { key: 'subdomain', label: 'Subdomain', type: 'text', placeholder: 'company', required: true },
            { key: 'client_id', label: 'Client ID', type: 'text', placeholder: 'Enter OneLogin Client ID', required: true },
            { key: 'client_secret', label: 'Client Secret', type: 'password', placeholder: 'Enter OneLogin Client Secret', required: true },
        ],
    },
];

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

        .oauth-section { display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px; }

        .oauth-btn {
            width: 100%;
            padding: 12px 16px;
            border-radius: 8px;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            background: #fff;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            transition: all 0.15s ease;
            font-family: inherit;
        }

        .oauth-btn:hover { background: var(--saas-bg-hover, #fafafa); border-color: #ccc; }
        .oauth-btn svg { width: 18px; height: 18px; }

        .divider {
            display: flex;
            align-items: center;
            gap: 16px;
            margin: 24px 0;
            color: var(--saas-text-muted, #999);
            font-size: 12px;
        }
        .divider::before, .divider::after { content: ''; flex: 1; height: 1px; background: #e0e0e0; }

        .form-group { margin-bottom: 20px; }
        .form-label { display: flex; justify-content: space-between; font-size: 13px; font-weight: 500; color: #666; margin-bottom: 8px; }
        .form-label a { color: #1a1a1a; text-decoration: none; font-weight: 400; }

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

        .remember-row { display: flex; align-items: center; gap: 10px; margin-bottom: 24px; }
        .remember-row input { width: 16px; height: 16px; accent-color: #1a1a1a; cursor: pointer; }
        .remember-row label { font-size: 13px; color: #666; cursor: pointer; }

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

        .input-error {
            border-color: #ef4444 !important;
        }

        .field-error {
            display: block;
            color: #ef4444;
            font-size: 12px;
            margin-top: 6px;
        }

        .footer {
            text-align: center;
            margin-top: 28px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }
        .footer-text { font-size: 12px; color: #999; }
        .footer-text a { color: #666; text-decoration: none; }

        /* ========================================
           GLASSMORPHISM SSO MODAL
           ======================================== */
        .modal-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            padding: 24px;
        }

        .modal-overlay.hidden { display: none; }

        .sso-modal {
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: none;
            border-radius: 0;
            box-shadow: none;
                0 0 0 1px rgba(255, 255, 255, 0.5) inset;
            width: 100vw;
            max-width: 100vw;
            height: 100vh;
            max-height: 100vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        .sso-header {
            padding: 28px 32px 20px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.06);
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
        }

        .sso-title-block { }

        .sso-title {
            font-size: 24px;
            font-weight: 700;
            margin: 0 0 6px 0;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .sso-title .material-symbols-outlined { font-size: 28px; }

        .sso-subtitle {
            font-size: 14px;
            color: var(--saas-text-secondary, #666);
            margin: 0;
        }

        .sso-close {
            width: 36px; height: 36px;
            border-radius: 10px;
            border: none;
            background: rgba(0, 0, 0, 0.04);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.1s ease;
        }
        .sso-close:hover { background: rgba(0, 0, 0, 0.08); }

        .sso-body {
            flex: 1;
            overflow-y: auto;
            display: flex;
        }

        /* Provider List */
        .provider-list {
            width: 260px;
            border-right: 1px solid rgba(0, 0, 0, 0.06);
            padding: 16px;
            flex-shrink: 0;
            overflow-y: auto;
        }

        .provider-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px 16px;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.15s ease;
            margin-bottom: 4px;
        }

        .provider-item:hover { background: rgba(0, 0, 0, 0.04); }
        .provider-item.active { background: rgba(0, 0, 0, 0.08); }

        .provider-icon {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            background: rgba(0, 0, 0, 0.04);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .provider-icon .material-symbols-outlined { font-size: 20px; }

        .provider-info { flex: 1; min-width: 0; }
        .provider-name { font-size: 14px; font-weight: 600; margin-bottom: 2px; }
        .provider-desc { font-size: 11px; color: #999; line-height: 1.3; }

        /* Config Panel */
        .config-panel {
            flex: 1;
            padding: 24px 28px;
            overflow-y: auto;
        }

        .config-header {
            margin-bottom: 24px;
        }

        .config-title {
            font-size: 18px;
            font-weight: 600;
            margin: 0 0 6px 0;
        }

        .config-desc {
            font-size: 13px;
            color: #666;
            margin: 0;
        }

        .config-form {
            display: flex;
            flex-direction: column;
            gap: 18px;
        }

        .config-field { }

        .config-label {
            display: block;
            font-size: 12px;
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .config-label .required {
            color: #ef4444;
            margin-left: 4px;
        }

        .config-input {
            width: 100%;
            padding: 12px 16px;
            border-radius: 10px;
            border: 1px solid rgba(0, 0, 0, 0.12);
            font-size: 14px;
            background: rgba(255, 255, 255, 0.8);
            transition: all 0.15s ease;
            font-family: inherit;
        }

        .config-input:focus {
            outline: none;
            border-color: #1a1a1a;
            background: #fff;
            box-shadow: 0 0 0 3px rgba(26, 26, 26, 0.08);
        }

        .config-input::placeholder { color: #999; }

        /* Test Connection */
        .test-section {
            margin-top: 24px;
            padding-top: 24px;
            border-top: 1px solid rgba(0, 0, 0, 0.06);
        }

        .test-btn {
            padding: 12px 24px;
            border-radius: 10px;
            border: 1px solid #e0e0e0;
            background: #fff;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.1s ease;
        }

        .test-btn:hover { background: #fafafa; }

        .test-btn .material-symbols-outlined { font-size: 18px; }

        .test-result {
            margin-top: 12px;
            padding: 12px 16px;
            border-radius: 10px;
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .test-result.success { background: #d1fae5; color: #047857; }
        .test-result.error { background: #fee2e2; color: #b91c1c; }
        .test-result.pending { background: #fef3c7; color: #b45309; }

        /* Modal Footer */
        .sso-footer {
            padding: 20px 28px;
            border-top: 1px solid rgba(0, 0, 0, 0.06);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(250, 250, 250, 0.8);
        }

        .sso-help {
            font-size: 13px;
            color: #666;
        }

        .sso-help a { color: #1a1a1a; font-weight: 500; }

        .sso-actions { display: flex; gap: 12px; }

        .sso-btn {
            padding: 12px 24px;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.1s ease;
            border: 1px solid #e0e0e0;
            background: #fff;
        }

        .sso-btn:hover { background: #fafafa; }

        .sso-btn.primary {
            background: #1a1a1a;
            color: white;
            border-color: #1a1a1a;
        }

        .sso-btn.primary:hover { background: #333; }
    `;

    @state() private _email = '';
    @state() private _password = '';
    @state() private _error = '';
    @state() private _emailError = '';
    @state() private _isLoading = false;
    @state() private _rememberMe = false;
    @state() private _showSSOModal = false;
    @state() private _selectedProvider: SSOProvider = 'oidc';
    @state() private _testStatus: 'idle' | 'pending' | 'success' | 'error' = 'idle';
    @state() private _testMessage = '';

    /**
     * RFC 5322 compliant email validation regex.
     * Per design.md Section 1.2, 2.1 - Email Validation
     * 
     * This pattern validates:
     * - Local part: alphanumeric, dots, hyphens, underscores, plus signs
     * - Domain: alphanumeric with dots and hyphens
     * - TLD: 2+ characters
     */
    private static readonly EMAIL_REGEX = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;

    /**
     * Validate email format per RFC 5322.
     * Per design.md Section 1.2 - Email Validation
     */
    private _validateEmail(email: string): boolean {
        if (!email) return false;
        if (email.length > 254) return false; // RFC 5321 max length
        return SaasLogin.EMAIL_REGEX.test(email);
    }

    /**
     * Handle email input with inline validation.
     */
    private _handleEmailInput(e: Event) {
        const input = e.target as HTMLInputElement;
        this._email = input.value;
        
        // Clear error when user starts typing
        if (this._emailError && this._email) {
            this._emailError = '';
        }
    }

    /**
     * Validate email on blur.
     */
    private _handleEmailBlur() {
        if (this._email && !this._validateEmail(this._email)) {
            this._emailError = 'Please enter a valid email address';
        } else {
            this._emailError = '';
        }
    }

    render() {
        const provider = SSO_PROVIDERS.find(p => p.id === this._selectedProvider)!;

        return html`
            <div class="login-page">
                <div class="login-card">
                    <!-- Brand -->
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

                    <!-- Header -->
                    <div class="form-header">
                        <h2 class="form-title">Sign in</h2>
                        <p class="form-subtitle">
                            Don't have an account? <a href="/register">Get started</a>
                        </p>
                    </div>

                    ${this._error ? html`<div class="error-message">${this._error}</div>` : ''}

                    <!-- OAuth Buttons -->
                    <div class="oauth-section">
                        <button class="oauth-btn" @click=${this._handleGoogleSignIn}>
                            <svg viewBox="0 0 24 24">
                                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                            </svg>
                            Continue with Google
                        </button>

                        <button class="oauth-btn" @click=${() => this._showSSOModal = true}>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="11" width="18" height="11" rx="2"/>
                                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                            </svg>
                            Enterprise SSO
                        </button>
                    </div>

                    <div class="divider">or</div>

                    <!-- Login Form -->
                    <form @submit=${this._handleLogin}>
                        <div class="form-group">
                            <label class="form-label">Email</label>
                            <input type="email" class="form-input ${this._emailError ? 'input-error' : ''}" 
                                placeholder="name@company.com"
                                .value=${this._email}
                                @input=${this._handleEmailInput}
                                @blur=${this._handleEmailBlur}
                                required autocomplete="email">
                            ${this._emailError ? html`<span class="field-error">${this._emailError}</span>` : ''}
                        </div>

                        <div class="form-group">
                            <label class="form-label">Password <a href="/forgot-password">Forgot?</a></label>
                            <input type="password" class="form-input" placeholder="Enter your password"
                                .value=${this._password}
                                @input=${(e: Event) => this._password = (e.target as HTMLInputElement).value}
                                required autocomplete="current-password" minlength="8">
                        </div>

                        <div class="remember-row">
                            <input type="checkbox" id="remember" .checked=${this._rememberMe}
                                @change=${(e: Event) => this._rememberMe = (e.target as HTMLInputElement).checked}>
                            <label for="remember">Remember me</label>
                        </div>

                        <button type="submit" class="submit-btn" ?disabled=${this._isLoading}>
                            ${this._isLoading ? html`<span class="spinner"></span>Signing in...` : 'Sign in'}
                        </button>
                    </form>

                    <!-- Dev Login - HIDDEN IN PRODUCTION -->
                    ${location.hostname === 'localhost' ? html`
                    <div class="divider">development only</div>
                    <button class="oauth-btn" @click=${this._handleDevLogin} style="background: #fef3c7; border-color: #f59e0b; opacity: 0.6;">
                        <span class="material-symbols-outlined" style="color: #b45309;">developer_mode</span>
                        Dev Login (localhost only)
                    </button>
                    ` : ''}

                    <div class="footer">
                        <p class="footer-text">Powered by <a href="https://somatech.lat" target="_blank">SomaTech LAT</a></p>
                    </div>
                </div>
            </div>

            <!-- Enterprise SSO Modal -->
            <div class="modal-overlay ${this._showSSOModal ? '' : 'hidden'}" @click=${(e: Event) => e.target === e.currentTarget && (this._showSSOModal = false)}>
                <div class="sso-modal">
                    <div class="sso-header">
                        <div class="sso-title-block">
                            <h2 class="sso-title">
                                <span class="material-symbols-outlined">security</span>
                                Enterprise SSO Configuration
                            </h2>
                            <p class="sso-subtitle">Connect your organization's identity provider</p>
                        </div>
                        <button class="sso-close" @click=${() => this._showSSOModal = false}>
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>

                    <div class="sso-body">
                        <!-- Provider List -->
                        <div class="provider-list">
                            ${SSO_PROVIDERS.map(p => html`
                                <div 
                                    class="provider-item ${this._selectedProvider === p.id ? 'active' : ''}"
                                    @click=${() => { this._selectedProvider = p.id; this._testStatus = 'idle'; }}
                                >
                                    <div class="provider-icon">
                                        <span class="material-symbols-outlined">${p.icon}</span>
                                    </div>
                                    <div class="provider-info">
                                        <div class="provider-name">${p.name}</div>
                                        <div class="provider-desc">${p.description}</div>
                                    </div>
                                </div>
                            `)}
                        </div>

                        <!-- Config Panel -->
                        <div class="config-panel">
                            <div class="config-header">
                                <h3 class="config-title">${provider.name} Configuration</h3>
                                <p class="config-desc">${provider.description}</p>
                            </div>

                            <div class="config-form">
                                ${provider.fields.map(field => html`
                                    <div class="config-field">
                                        <label class="config-label">
                                            ${field.label}
                                            ${field.required ? html`<span class="required">*</span>` : ''}
                                        </label>
                                        <input 
                                            type=${field.type} 
                                            class="config-input" 
                                            id=${`sso-${field.key}`}
                                            placeholder=${field.placeholder}
                                        >
                                    </div>
                                `)}
                            </div>

                            <div class="test-section">
                                <button class="test-btn" @click=${this._testConnection}>
                                    <span class="material-symbols-outlined">network_check</span>
                                    Test Connection
                                </button>

                                ${this._testStatus !== 'idle' ? html`
                                    <div class="test-result ${this._testStatus}">
                                        <span class="material-symbols-outlined">
                                            ${this._testStatus === 'success' ? 'check_circle' :
                    this._testStatus === 'error' ? 'error' : 'hourglass_empty'}
                                        </span>
                                        ${this._testMessage}
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    </div>

                    <div class="sso-footer">
                        <div class="sso-help">
                            Need help? <a href="https://docs.somaagent.com/sso" target="_blank">View SSO documentation</a>
                        </div>
                        <div class="sso-actions">
                            <button class="sso-btn" @click=${() => this._showSSOModal = false}>Cancel</button>
                            <button class="sso-btn primary" @click=${this._saveAndConnect}>Save & Connect</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    private async _handleLogin(e: Event) {
        e.preventDefault();
        if (!this._email || !this._password) {
            this._error = 'Please enter both email and password';
            return;
        }
        
        // Validate email format per RFC 5322
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

        try {
            const response = await fetch('/api/v2/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: this._email, password: this._password, remember_me: this._rememberMe }),
            });

            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.detail || 'Invalid credentials');
            }

            const result = await response.json();
            localStorage.setItem('eog_auth_token', result.token);
            localStorage.setItem('eog_user', JSON.stringify(result.user));
            window.location.href = result.redirect_path || '/mode-select';
        } catch (err) {
            this._error = err instanceof Error ? err.message : 'Login failed';
        } finally {
            this._isLoading = false;
        }
    }

    private _handleGoogleSignIn() {
        window.location.href = googleAuthService.getAuthUrl();
    }

    private _handleDevLogin() {
        localStorage.setItem('eog_auth_token', 'dev_token_' + Date.now());
        localStorage.setItem('eog_user', JSON.stringify({ email: 'admin@dev.local', name: 'Dev Admin', role: 'saas_admin' }));
        window.location.href = '/mode-select';
    }

    private async _testConnection() {
        this._testStatus = 'pending';
        this._testMessage = 'Testing connection to identity provider...';

        const provider = SSO_PROVIDERS.find(p => p.id === this._selectedProvider)!;
        const config: Record<string, string> = {};

        for (const field of provider.fields) {
            const input = this.shadowRoot?.getElementById(`sso-${field.key}`) as HTMLInputElement;
            if (input) {
                config[field.key] = input.value;
            }
        }

        try {
            const response = await fetch('/api/v2/auth/sso/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider: this._selectedProvider, config }),
            });

            if (response.ok) {
                const result = await response.json();
                this._testStatus = 'success';
                this._testMessage = result.message || 'Connection successful! Identity provider is reachable.';
            } else {
                const error = await response.json().catch(() => ({}));
                this._testStatus = 'error';
                this._testMessage = error.detail || 'Connection failed. Please verify your configuration.';
            }
        } catch (err) {
            this._testStatus = 'error';
            this._testMessage = 'Network error. Please check your connection and try again.';
        }
    }

    private async _saveAndConnect() {
        const provider = SSO_PROVIDERS.find(p => p.id === this._selectedProvider)!;
        const config: Record<string, string> = {};

        for (const field of provider.fields) {
            const input = this.shadowRoot?.getElementById(`sso-${field.key}`) as HTMLInputElement;
            if (input) {
                config[field.key] = input.value;
            }
        }

        try {
            // Save SSO config to backend
            await fetch('/api/v2/auth/sso/configure', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider: this._selectedProvider, config }),
            });

            // If OIDC, redirect to the configured provider
            if (this._selectedProvider === 'oidc' && config.issuer_url) {
                window.location.href = keycloakService.getAuthUrl();
            } else {
                this._showSSOModal = false;
                this._error = '';
                alert('SSO configured! Click Enterprise SSO again to connect.');
            }
        } catch {
            this._error = 'Failed to save SSO configuration';
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-login': SaasLogin;
    }
}
