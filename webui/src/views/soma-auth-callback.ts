/**
 * Eye of God Auth Callback Page
 * Per Eye of God UIX Design - Authentication
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - OIDC callback handling (Keycloak + Google)
 * - Token exchange
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { keycloakService } from '../services/keycloak-service.js';
import { googleAuthService } from '../services/google-auth-service.js';
import { Router } from '@vaadin/router';

@customElement('soma-auth-callback')
export class SomaAuthCallback extends LitElement {
    static styles = css`
        :host {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: var(--soma-bg-void, #0f172a);
            color: var(--soma-text-main, #e2e8f0);
        }

        .callback-container {
            text-align: center;
            padding: var(--soma-spacing-xl, 32px);
        }

        .spinner {
            width: 48px;
            height: 48px;
            border: 4px solid var(--soma-border-color, rgba(255, 255, 255, 0.1));
            border-top-color: var(--soma-accent, #94a3b8);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto var(--soma-spacing-lg, 24px);
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .status {
            font-size: var(--soma-text-lg, 16px);
            margin-bottom: var(--soma-spacing-sm, 8px);
        }

        .detail {
            font-size: var(--soma-text-sm, 13px);
            color: var(--soma-text-dim, #64748b);
        }

        .error {
            color: var(--soma-danger, #ef4444);
        }

        .error-box {
            padding: var(--soma-spacing-md, 16px);
            border-radius: var(--soma-radius-md, 8px);
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid var(--soma-danger, #ef4444);
            margin-top: var(--soma-spacing-md, 16px);
        }

        .retry-btn {
            margin-top: var(--soma-spacing-lg, 24px);
            padding: var(--soma-spacing-sm, 8px) var(--soma-spacing-lg, 24px);
            border-radius: var(--soma-radius-md, 8px);
            background: var(--soma-accent, #94a3b8);
            color: var(--soma-bg-void, #0f172a);
            border: none;
            font-weight: 600;
            cursor: pointer;
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
                    <p class="status">Success!</p>
                    <p class="detail">Redirecting to application...</p>
                `}
            </div>
        `;
    }

    private async _handleCallback() {
        try {
            // Detect which OAuth provider by checking stored state
            const isGoogleAuth = sessionStorage.getItem('eog_google_state') !== null;
            const isKeycloakAuth = sessionStorage.getItem('eog_auth_state') !== null;

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
        localStorage.setItem('eog_auth_token', result.access_token);
        localStorage.setItem('eog_user', JSON.stringify(result.user));

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
            localStorage.setItem('eog_user', JSON.stringify({
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
            window.location.href = '/';
        }, 1000);
    }

    private _retry() {
        window.location.href = '/login';
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-auth-callback': SomaAuthCallback;
    }
}
