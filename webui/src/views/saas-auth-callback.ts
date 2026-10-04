/**
 * Auth callback landing — session check only.
 *
 * Federated sign-in is completed by the server OAuth router
 * (`GET /api/v2/auth/oauth/callback` in `admin/auth/api_oauth.py`), which
 * exchanges the code, sets httpOnly cookies and redirects into the app. This
 * page is the SPA landing if a provider or proxy sends the browser here; it
 * never holds an issuer URL and never exchanges a code in the browser.
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

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
        .status { font-size: 18px; font-weight: 600; margin-bottom: 8px; }
        .detail { font-size: 14px; color: var(--saas-text-secondary, #666); }
        .error { color: var(--saas-status-danger, #ef4444); }
        .retry-btn {
            margin-top: 24px;
            padding: 12px 24px;
            background: var(--saas-accent, #1a1a1a);
            color: #fff;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
        }
    `;

    @state() private _isLoading = true;
    @state() private _error = '';
    @state() private _status = 'Completing sign-in…';

    override connectedCallback() {
        super.connectedCallback();
        void this._complete();
    }

    private async _complete() {
        // The server callback already set the session cookies when it landed
        // here. Confirm the session exists, then enter the app. A provider
        // error in the query string is shown as-is — never invented.
        const params = new URLSearchParams(window.location.search);
        const providerError = params.get('error') || params.get('error_description');
        if (providerError) {
            this._isLoading = false;
            this._error = providerError;
            return;
        }
        try {
            this._status = 'Checking your session…';
            const res = await fetch('/api/v2/auth/me', { credentials: 'include' });
            if (!res.ok) {
                this._isLoading = false;
                this._error = 'No active session. Sign in again.';
                return;
            }
            this._status = 'Signed in. Opening chat…';
            window.location.assign('/chat');
        } catch (err) {
            this._isLoading = false;
            this._error = err instanceof Error ? err.message : 'Could not confirm the session';
        }
    }

    private _retry() {
        window.location.assign('/login');
    }

    override render() {
        return html`
            <div class="callback-container">
                ${this._isLoading
                    ? html`
                          <div class="spinner"></div>
                          <p class="status">${this._status}</p>
                      `
                    : html`
                          <p class="status ${this._error ? 'error' : ''}">
                              ${this._error || 'Success!'}
                          </p>
                          ${this._error
                              ? html`
                                    <p class="detail">${this._error}</p>
                                    <button class="retry-btn" @click=${this._retry}>
                                        Return to Login
                                    </button>
                                `
                              : html`<p class="detail">Redirecting to application...</p>`}
                      `}
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-auth-callback': SaasAuthCallback;
    }
}
