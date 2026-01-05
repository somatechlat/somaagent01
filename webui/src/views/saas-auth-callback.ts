/**
 * SomaAgent SaaS — Auth Callback Page
 * Per UI_STYLE_GUIDE.md - Minimal White/Black Design
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - OIDC callback handling (Keycloak + Google)
 * - Token exchange
 * - Light theme design
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { keycloakService } from '../services/keycloak-service.js';
import { googleAuthService } from '../services/google-auth-service.js';
import { Router } from '@vaadin/router';

@customElement('saas-auth-callback')
export class SaasAuthCallback extends LitElement {
    static styles = css`
        :host {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: var(--saas-bg-page, #f5f5f5);
            color: var(--saas-text-primary, #1a1a1a);
            font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
        }

        .callback-container {
            text-align: center;
            padding: 48px;
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 12px;
            box-shadow: var(--saas-shadow-md, 0 2px 8px rgba(0,0,0,0.06));
            max-width: 400px;
            width: 100%;
            margin: 24px;
        }

        .spinner {
            width: 48px;
            height: 48px;
            border: 3px solid var(--saas-border-light, #e0e0e0);
            border-top-color: var(--saas-accent, #1a1a1a);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 24px;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .status {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
            color: var(--saas-text-primary, #1a1a1a);
        }

        .detail {
            font-size: 14px;
            color: var(--saas-text-secondary, #666);
        }

        .error {
            color: var(--saas-status-danger, #ef4444);
        }

        .error-box {
            padding: 16px;
            border-radius: 8px;
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.2);
            margin-top: 20px;
            font-size: 13px;
            color: var(--saas-status-danger, #ef4444);
        }

        .retry-btn {
            margin-top: 24px;
            padding: 12px 24px;
            border-radius: 8px;
            background: var(--saas-accent, #1a1a1a);
            color: white;
            border: none;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            transition: background 0.15s ease;
            font-family: inherit;
        }

        .retry-btn:hover {
            background: #333;
        }

        .success-icon {
            width: 48px;
            height: 48px;
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.2);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 24px;
            font-size: 24px;
        }
    `;

    @state() private _status = 'Processing authentication...';
    @state() private _error: string | null = null;
    @state() private _isLoading = true;

    connectedCallback() {
        super.connectedCallback();
        this._handleCallback();
    }

    render() {
        return html`
            <div class="callback-container">
                ${this._isLoading ? html`
                    <div class="spinner"></div>
                    <p class="status">${this._status}</p>
                    <p class="detail">Please wait while we complete your sign-in</p>
                ` : this._error ? html`
                    <p class="status error">Authentication Failed</p>
                    <div class="error-box">${this._error}</div>
                    <button class="retry-btn" @click=${this._retry}>
                        Return to Login
                    </button>
                ` : html`
                    <div class="success-icon">✓</div>
                    <p class="status">Success!</p>
                    <p class="detail">Redirecting to application...</p>
                `}
            </div>
        `;
    }

    private async _handleCallback() {
        try {
            // Detect which OAuth provider by checking stored state
            const isGoogleAuth = sessionStorage.getItem('saas_google_state') !== null;
            const isKeycloakAuth = sessionStorage.getItem('saas_auth_state') !== null;

            if (isGoogleAuth) {
                await this._handleGoogleCallback();
            } else if (isKeycloakAuth) {
                await this._handleKeycloakCallback();
            } else {
                throw new Error('No authentication session found');
            }

        } catch (error) {
            this._isLoading = false;
            this._error = error instanceof Error ? error.message : 'Authentication failed';
        }
    }

    /**
     * Handle Google OAuth callback
     */
    private async _handleGoogleCallback() {
        const callback = googleAuthService.parseCallback(window.location.href);

        if (callback.error) {
            throw new Error(callback.error);
        }

        if (callback.state && !googleAuthService.verifyState(callback.state)) {
            throw new Error('Invalid state parameter - possible CSRF attack');
        }

        if (!callback.code) {
            throw new Error('No authorization code received');
        }

        this._status = 'Exchanging authorization code...';

        // Exchange code via backend (keeps client_secret secure)
        const result = await googleAuthService.exchangeCode(callback.code);

        // Store token and user info
        localStorage.setItem('saas_auth_token', result.access_token);
        localStorage.setItem('saas_user', JSON.stringify(result.user));

        // Clear state
        googleAuthService.clearState();

        this._isLoading = false;

        // Redirect based on role
        setTimeout(() => {
            Router.go(result.redirect_path || '/chat');
        }, 1000);
    }

    /**
     * Handle Keycloak OIDC callback
     */
    private async _handleKeycloakCallback() {
        const callback = keycloakService.parseCallback(window.location.href);

        if (callback.error) {
            throw new Error(callback.error);
        }

        if (callback.state && !keycloakService.verifyState(callback.state)) {
            throw new Error('Invalid state parameter - possible CSRF attack');
        }

        if (!callback.code) {
            throw new Error('No authorization code received');
        }

        this._status = 'Exchanging authorization code...';
        await keycloakService.exchangeCode(callback.code);

        this._status = 'Fetching user information...';
        const userInfo = await keycloakService.getUserInfo();

        if (userInfo) {
            localStorage.setItem('saas_user', JSON.stringify({
                id: userInfo.sub,
                username: userInfo.preferred_username,
                email: userInfo.email,
                name: userInfo.name,
                roles: userInfo.realm_access?.roles || [],
            }));
        }

        this._isLoading = false;

        // Redirect to app
        setTimeout(() => {
            window.location.href = '/chat';
        }, 1000);
    }

    private _retry() {
        window.location.href = '/login';
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-auth-callback': SaasAuthCallback;
    }
}
