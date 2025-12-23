/**
 * SomaAgent SaaS Admin — Login Page
 * Clean White/Black Minimal Design
 *
 * DESIGN: Light gray background, white card, black text
 * Simple, professional SaaS aesthetic
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { consume } from '@lit-labs/context';
import { Router } from '@vaadin/router';
import { authContext, AuthStateData } from '../stores/auth-store.js';
import { keycloakService } from '../services/keycloak-service.js';
import { googleAuthService } from '../services/google-auth-service.js';

@customElement('eog-login')
export class EogLogin extends LitElement {
    static styles = css`
        :host {
            display: block;
            min-height: 100vh;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #1a1a1a;
        }

        * {
            box-sizing: border-box;
        }

        .login-page {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 24px;
        }

        .login-card {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            width: 100%;
            max-width: 400px;
            padding: 40px;
        }

        /* ========================================
           LOGO/BRANDING
           ======================================== */
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
            color: #1a1a1a;
        }

        /* ========================================
           HEADER
           ======================================== */
        .form-header {
            margin-bottom: 28px;
        }

        .form-title {
            font-size: 22px;
            font-weight: 600;
            color: #1a1a1a;
            margin: 0 0 8px 0;
        }

        .form-subtitle {
            font-size: 14px;
            color: #666;
            margin: 0;
        }

        .form-subtitle a {
            color: #1a1a1a;
            font-weight: 500;
            text-decoration: underline;
        }

        /* ========================================
           OAUTH BUTTONS
           ======================================== */
        .oauth-section {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-bottom: 24px;
        }

        .oauth-btn {
            width: 100%;
            padding: 12px 16px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            background: white;
            font-size: 14px;
            font-weight: 500;
            color: #1a1a1a;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            transition: all 0.15s ease;
            font-family: inherit;
        }

        .oauth-btn:hover {
            background: #fafafa;
            border-color: #ccc;
        }

        .oauth-btn svg {
            width: 18px;
            height: 18px;
        }

        /* ========================================
           DIVIDER
           ======================================== */
        .divider {
            display: flex;
            align-items: center;
            gap: 16px;
            margin: 24px 0;
            color: #999;
            font-size: 12px;
        }

        .divider::before,
        .divider::after {
            content: '';
            flex: 1;
            height: 1px;
            background: #e0e0e0;
        }

        /* ========================================
           FORM INPUTS
           ======================================== */
        .form-group {
            margin-bottom: 20px;
        }

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
        }

        .form-label a:hover {
            text-decoration: underline;
        }

        .form-input {
            width: 100%;
            padding: 12px 14px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            font-size: 14px;
            color: #1a1a1a;
            transition: border-color 0.15s ease;
            background: white;
            font-family: inherit;
        }

        .form-input::placeholder {
            color: #999;
        }

        .form-input:focus {
            outline: none;
            border-color: #1a1a1a;
        }

        /* ========================================
           CHECKBOX
           ======================================== */
        .remember-row {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 24px;
        }

        .remember-row input[type="checkbox"] {
            width: 16px;
            height: 16px;
            border-radius: 4px;
            accent-color: #1a1a1a;
            cursor: pointer;
        }

        .remember-row label {
            font-size: 13px;
            color: #666;
            cursor: pointer;
        }

        /* ========================================
           SUBMIT BUTTON
           ======================================== */
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

        .submit-btn:hover {
            background: #333;
        }

        .submit-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* Loading Spinner */
        .submit-btn .spinner {
            display: none;
            width: 14px;
            height: 14px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.6s linear infinite;
            margin-right: 8px;
        }

        .submit-btn.loading .spinner {
            display: inline-block;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* ========================================
           ERROR MESSAGE
           ======================================== */
        .error-message {
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 8px;
            padding: 12px 14px;
            margin-bottom: 20px;
            color: #dc2626;
            font-size: 13px;
        }

        /* ========================================
           FOOTER
           ======================================== */
        .footer {
            text-align: center;
            margin-top: 28px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }

        .footer-text {
            font-size: 12px;
            color: #999;
        }

        .footer-text a {
            color: #666;
            text-decoration: none;
        }

        .footer-text a:hover {
            text-decoration: underline;
        }
    `;

    @consume({ context: authContext, subscribe: true })
    authState!: AuthStateData;

    @state() private _email = '';
    @state() private _password = '';
    @state() private _error = '';
    @state() private _isLoading = false;
    @state() private _rememberMe = false;

    render() {
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
                        <span class="brand-name">SomaAgent SaaS Admin</span>
                    </div>

                    <!-- Header -->
                    <div class="form-header">
                        <h2 class="form-title">Sign in</h2>
                        <p class="form-subtitle">
                            Don't have an account? <a href="/register">Get started</a>
                        </p>
                    </div>

                    <!-- Error Display -->
                    ${this._error ? html`
                        <div class="error-message">${this._error}</div>
                    ` : ''}

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

                        <button class="oauth-btn" @click=${this._handleSSO}>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="11" width="18" height="11" rx="2"/>
                                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                            </svg>
                            Enterprise SSO
                        </button>
                    </div>

                    <!-- Divider -->
                    <div class="divider">or</div>

                    <!-- Login Form -->
                    <form @submit=${this._handleLogin}>
                        <div class="form-group">
                            <label class="form-label">Email</label>
                            <input 
                                type="email" 
                                class="form-input"
                                placeholder="name@company.com"
                                .value=${this._email}
                                @input=${(e: Event) => this._email = (e.target as HTMLInputElement).value}
                                required
                                autocomplete="email"
                            >
                        </div>

                        <div class="form-group">
                            <label class="form-label">
                                Password
                                <a href="/forgot-password">Forgot?</a>
                            </label>
                            <input 
                                type="password" 
                                class="form-input"
                                placeholder="••••••••"
                                .value=${this._password}
                                @input=${(e: Event) => this._password = (e.target as HTMLInputElement).value}
                                required
                                autocomplete="current-password"
                            >
                        </div>

                        <div class="remember-row">
                            <input 
                                type="checkbox" 
                                id="remember"
                                .checked=${this._rememberMe}
                                @change=${(e: Event) => this._rememberMe = (e.target as HTMLInputElement).checked}
                            >
                            <label for="remember">Remember me</label>
                        </div>

                        <button 
                            type="submit" 
                            class="submit-btn ${this._isLoading ? 'loading' : ''}"
                            ?disabled=${this._isLoading}
                        >
                            <span class="spinner"></span>
                            ${this._isLoading ? 'Signing in...' : 'Sign in'}
                        </button>
                    </form>

                    <!-- Footer -->
                    <div class="footer">
                        <p class="footer-text">
                            Powered by <a href="https://somatech.lat" target="_blank">SomaTech LAT</a>
                        </p>
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

        this._isLoading = true;
        this._error = '';

        try {
            const authProvider = document.querySelector('eog-auth-provider') as any;
            if (authProvider) {
                const result = await authProvider.login(this._email, this._password);
                if (result && result.success) {
                    Router.go(result.redirect_path || '/chat');
                } else {
                    this._error = result?.error || 'Invalid credentials';
                }
            } else {
                throw new Error('Auth provider not found');
            }
        } catch (err) {
            this._error = err instanceof Error ? err.message : 'Login failed';
        } finally {
            this._isLoading = false;
        }
    }

    private _handleSSO() {
        window.location.href = keycloakService.getAuthUrl();
    }

    private _handleGoogleSignIn() {
        window.location.href = googleAuthService.getAuthUrl();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-login': EogLogin;
    }
}
