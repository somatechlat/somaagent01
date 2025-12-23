/**
 * Eye of God Login View
 * Per Eye of God UIX Design - Authentication
 *
 * VIBE COMPLIANT:
 * - Real Auth Integration
 * - White Glassmorphism Theme
 * - Responsive Animation
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { consume } from '@lit-labs/context';
import { Router } from '@vaadin/router';
import { authContext, AuthStateData } from '../stores/auth-store.js';
import { keycloakService } from '../services/keycloak-service.js';
import '../components/eog-button.js';
import '../components/eog-input.js';

@customElement('eog-login')
export class EogLogin extends LitElement {
    static styles = css`
        :host {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            width: 100vw;
            background: #f8fafc; /* Slate 50 */
            font-family: 'Inter', sans-serif;
            position: relative;
            overflow: hidden;
        }

        /* ========== Background Ambience ========== */
        .ambient-bg {
            position: absolute;
            width: 100%;
            height: 100%;
            z-index: 0;
            pointer-events: none;
        }

        .orb {
            position: absolute;
            border-radius: 50%;
            filter: blur(80px);
            opacity: 0.6;
            animation: float 20s infinite ease-in-out;
        }

        .orb-1 {
            top: -10%;
            left: -10%;
            width: 50vw;
            height: 50vw;
            background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%); /* Light Blue */
            animation-delay: 0s;
        }

        .orb-2 {
            bottom: -10%;
            right: -10%;
            width: 50vw;
            height: 50vw;
            background: linear-gradient(135deg, #f0fdf4 0%, #bbf7d0 100%); /* Light Green */
            animation-delay: -5s;
        }

        .orb-3 {
            top: 40%;
            left: 40%;
            width: 30vw;
            height: 30vw;
            background: linear-gradient(135deg, #f5f3ff 0%, #ddd6fe 100%); /* Light Violet */
            animation-delay: -10s;
        }

        @keyframes float {
            0%, 100% { transform: translate(0, 0) rotate(0deg); }
            33% { transform: translate(30px, -50px) rotate(10deg); }
            66% { transform: translate(-20px, 20px) rotate(-5deg); }
        }

        /* ========== Login Card ========== */
        .login-card {
            position: relative;
            z-index: 10;
            width: 100%;
            max-width: 420px;
            padding: 48px;
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            border: 1px solid rgba(255, 255, 255, 0.5);
            border-radius: 32px;
            box-shadow: 
                0 20px 40px -10px rgba(0, 0, 0, 0.05),
                0 0 0 1px rgba(255, 255, 255, 0.8) inset;
            display: flex;
            flex-direction: column;
            gap: 24px;
            animation: cardEnter 0.8s cubic-bezier(0.2, 0.8, 0.2, 1);
        }

        @keyframes cardEnter {
            from { opacity: 0; transform: translateY(40px) scale(0.95); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }

        .brand-header {
            text-align: center;
            margin-bottom: 8px;
        }

        .brand-icon {
            font-size: 48px;
            margin-bottom: 16px;
            display: inline-block;
            animation: pulse 4s infinite ease-in-out;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.1); opacity: 0.8; }
        }

        h1 {
            font-size: 24px;
            font-weight: 600;
            color: #0f172a;
            margin: 0 0 8px 0;
            letter-spacing: -0.5px;
        }

        .subtitle {
            font-size: 14px;
            color: #64748b;
            line-height: 1.5;
        }

        /* ========== Form ========== */
        .login-form {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .form-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
            color: #64748b;
        }

        .link {
            color: #0f172a;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.2s;
            cursor: pointer;
        }
        .link:hover { color: #3b82f6; }

        .divider {
            display: flex;
            align-items: center;
            gap: 16px;
            font-size: 12px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin: 8px 0;
        }
        .divider::before, .divider::after {
            content: '';
            flex: 1;
            height: 1px;
            background: #e2e8f0;
        }

        /* ========== Error ========== */
        .error-message {
            background: #fee2e2;
            color: #ef4444;
            padding: 12px;
            border-radius: 8px;
            font-size: 13px;
            text-align: center;
            animation: shake 0.4s cubic-bezier(.36,.07,.19,.97) both;
        }

        @keyframes shake {
            10%, 90% { transform: translate3d(-1px, 0, 0); }
            20%, 80% { transform: translate3d(2px, 0, 0); }
            30%, 50%, 70% { transform: translate3d(-4px, 0, 0); }
            40%, 60% { transform: translate3d(4px, 0, 0); }
        }
    `;

    @consume({ context: authContext, subscribe: true })
    @state()
    authState?: AuthStateData;

    @state() private _username = '';
    @state() private _password = '';
    @state() private _isLoading = false;
    @state() private _error = '';

    render() {
        return html`
            <div class="ambient-bg">
                <div class="orb orb-1"></div>
                <div class="orb orb-2"></div>
                <div class="orb orb-3"></div>
            </div>

            <main class="login-card">
                <div class="brand-header">
                    <div class="brand-icon">👁️</div>
                    <h1>Eye of God</h1>
                    <div class="subtitle">Enter the Omniscience Platform</div>
                </div>

                ${this._error ? html`<div class="error-message">${this._error}</div>` : ''}

                <form class="login-form" @submit=${this._handleLogin}>
                    <eog-input
                        label="Username"
                        placeholder="agent.smith"
                        .value=${this._username}
                        @eog-input=${(e: CustomEvent) => this._username = e.detail.value}
                    ></eog-input>

                    <eog-input
                        label="Password"
                        type="password"
                        placeholder="••••••••"
                        .value=${this._password}
                        @eog-input=${(e: CustomEvent) => this._password = e.detail.value}
                    ></eog-input>

                    <div class="form-footer">
                        <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                            <input type="checkbox" style="accent-color: #0f172a;">
                            Remember me
                        </label>
                        <a class="link" href="#">Forgot password?</a>
                    </div>

                    <eog-button
                        variant="primary"
                        type="submit"
                        ?loading=${this._isLoading}
                        style="width: 100%;"
                    >
                        Sign In
                    </eog-button>
                </form>

                <div class="divider">or</div>

                <eog-button
                    variant="glass"
                    @eog-click=${this._handleSSO}
                    style="width: 100%;"
                >
                    <span style="display: flex; align-items: center; gap: 8px; justify-content: center;">
                        <span>🔐</span> Sign in with SSO
                    </span>
                </eog-button>
            </main>
        `;
    }

    private async _handleLogin(e: Event) {
        e.preventDefault();
        if (!this._username || !this._password) {
            this._error = 'Please enter both username and password';
            return;
        }

        this._isLoading = true;
        this._error = '';

        try {
            // Locate the auth provider in global scope if needed, or dispatch event
            // Using a custom event to bubble up to provider, or direct call if available via context actions (not in data)
            // For now, assume we can access the provider element or dispatch

            // Dispatch login event which eog-auth-provider listens to, OR simpler:
            const authProvider = document.querySelector('eog-auth-provider') as any;
            if (authProvider) {
                const success = await authProvider.login(this._username, this._password);
                if (success) {
                    Router.go('/chat');
                } else {
                    this._error = authProvider.authState.error || 'Invalid credentials';
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
        const url = keycloakService.getAuthUrl();
        window.location.href = url;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-login': EogLogin;
    }
}
