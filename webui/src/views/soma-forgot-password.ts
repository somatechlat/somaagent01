/**
 * SomaAgent Soma — Forgot Password Page
 * Per UI_SCREENS_SRS.md Section 3.3
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - Minimal white/black design per UI_STYLE_GUIDE.md
 * - NO EMOJIS - Material Symbols only
 *
 * BLOCKED (REQ-UIX-005): password reset is not available on this deployment.
 * `admin/auth/api.py` mounts /token /refresh /me /logout /login /register
 * /impersonate plus /sso /oauth /mfa. No password-reset handler is mounted,
 * so this screen renders present-but-disabled with that blocking reason and
 * never POSTs to a route that does not exist.
 */

import { LitElement, html, css } from 'lit';
import { customElement } from 'lit/decorators.js';

@customElement('soma-forgot-password')
export class SomaForgotPassword extends LitElement {
    static styles = css`
        :host {
            display: block;
            min-height: 100vh;
            font-family: var(--soma-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
            background: var(--soma-bg-page, #f5f5f5);
            color: var(--soma-text-primary, #1a1a1a);
        }

        * { box-sizing: border-box; }

        .forgot-page {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 24px;
        }

        .forgot-card {
            background: var(--soma-bg-card, #ffffff);
            border: 1px solid var(--soma-border-light, #e0e0e0);
            border-radius: 12px;
            box-shadow: var(--soma-shadow-md, 0 2px 8px rgba(0,0,0,0.06));
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
        .form-subtitle { font-size: 14px; color: var(--soma-text-secondary, #666); margin: 0; line-height: 1.5; }

        .form-group { margin-bottom: 24px; }
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

        .back-link {
            display: flex;
            align-items: center;
            gap: 6px;
            color: #666;
            text-decoration: none;
            font-size: 14px;
            margin-top: 24px;
            transition: color 0.15s ease;
        }
        .back-link:hover { color: #1a1a1a; }

        .footer {
            text-align: center;
            margin-top: 28px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }
        .footer-text { font-size: 12px; color: #999; }
        .footer-text a { color: #666; text-decoration: none; }
    `;

    private static readonly BLOCKING_REASON =
        'Password reset is not available on this deployment. No password-reset ' +
        'route is mounted in admin/auth/api.py (mounted: /token /refresh /me ' +
        '/logout /login /register /impersonate plus /sso /oauth /mfa). ' +
        'Contact your administrator.';

    render() {
        return html`
            <div class="forgot-page">
                <div class="forgot-card">
                    <div class="brand">
                        <div class="brand-icon">
                            <svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="3" y="3" width="7" height="7" rx="1"/>
                                <rect x="14" y="3" width="7" height="7" rx="1"/>
                                <rect x="14" y="14" width="7" height="7" rx="1"/>
                                <rect x="3" y="14" width="7" height="7" rx="1"/>
                            </svg>
                        </div>
                        <span class="brand-name">SomaAgent Soma</span>
                    </div>

                    <div class="form-header">
                        <h2 class="form-title">Reset password</h2>
                        <p class="form-subtitle" data-control="forgot-password-blocked">
                            This screen is present but disabled.
                        </p>
                    </div>

                    <div class="error-message" role="status" data-control="blocking-reason">
                        <strong>Blocking reason:</strong>
                        ${SomaForgotPassword.BLOCKING_REASON}
                    </div>

                    <form @submit=${(e: Event) => e.preventDefault()}>
                        <div class="form-group">
                            <label class="form-label" for="forgot-email">Email</label>
                            <input id="forgot-email" type="email" class="form-input"
                                placeholder="name@company.com"
                                disabled
                                title=${SomaForgotPassword.BLOCKING_REASON}
                                autocomplete="email">
                        </div>

                        <button type="submit" class="submit-btn" disabled
                            title=${SomaForgotPassword.BLOCKING_REASON}>
                            Send reset link
                        </button>
                    </form>

                    <a href="/login" class="back-link">
                        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M19 12H5M12 19l-7-7 7-7"/>
                        </svg>
                        Back to login
                    </a>

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
        'soma-forgot-password': SomaForgotPassword;
    }
}
