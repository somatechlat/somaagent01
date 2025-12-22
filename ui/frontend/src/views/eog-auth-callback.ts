/**
 * Eye of God Auth Callback Page
 * Per Eye of God UIX Design - Authentication
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - OIDC callback handling
 * - Token exchange
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { keycloakService } from '../services/keycloak-service.js';

@customElement('eog-auth-callback')
export class EogAuthCallback extends LitElement {
    static styles = css`
        :host {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: var(--eog-bg-void, #0f172a);
            color: var(--eog-text-main, #e2e8f0);
        }

        .callback-container {
            text-align: center;
            padding: var(--eog-spacing-xl, 32px);
        }

        .spinner {
            width: 48px;
            height: 48px;
            border: 4px solid var(--eog-border-color, rgba(255, 255, 255, 0.1));
            border-top-color: var(--eog-accent, #94a3b8);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto var(--eog-spacing-lg, 24px);
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .status {
            font-size: var(--eog-text-lg, 16px);
            margin-bottom: var(--eog-spacing-sm, 8px);
        }

        .detail {
            font-size: var(--eog-text-sm, 13px);
            color: var(--eog-text-dim, #64748b);
        }

        .error {
            color: var(--eog-danger, #ef4444);
        }

        .error-box {
            padding: var(--eog-spacing-md, 16px);
            border-radius: var(--eog-radius-md, 8px);
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid var(--eog-danger, #ef4444);
            margin-top: var(--eog-spacing-md, 16px);
        }

        .retry-btn {
            margin-top: var(--eog-spacing-lg, 24px);
            padding: var(--eog-spacing-sm, 8px) var(--eog-spacing-lg, 24px);
            border-radius: var(--eog-radius-md, 8px);
            background: var(--eog-accent, #94a3b8);
            color: var(--eog-bg-void, #0f172a);
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
            // Parse callback URL
            const callback = keycloakService.parseCallback(window.location.href);

            // Check for errors
            if (callback.error) {
                throw new Error(callback.error);
            }

            // Verify state
            if (callback.state && !keycloakService.verifyState(callback.state)) {
                throw new Error('Invalid state parameter - possible CSRF attack');
            }

            // Exchange code for tokens
            if (callback.code) {
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
            } else {
                throw new Error('No authorization code received');
            }

        } catch (error) {
            this._isLoading = false;
            this._error = error instanceof Error ? error.message : 'Authentication failed';
        }
    }

    private _retry() {
        window.location.href = '/login';
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-auth-callback': EogAuthCallback;
    }
}
