/**
 * SaaS Sys Admin — Not Found View
 *
 * Friendly 404 fallback shown for unknown routes.
 */

import { LitElement, html, css } from 'lit';
import { customElement } from 'lit/decorators.js';

@customElement('saas-not-found')
export class SaasNotFound extends LitElement {
    static styles = css`
        :host {
            display: block;
            min-height: 100vh;
            font-family: var(--aaas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
            background: var(--aaas-bg-page, #0a0a0a);
            color: var(--aaas-text-primary, #ffffff);
        }

        * {
            box-sizing: border-box;
        }

        .container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: var(--aaas-space-lg, 24px);
            text-align: center;
        }

        .status-code {
            font-size: clamp(80px, 15vw, 140px);
            font-weight: 700;
            line-height: 1;
            color: var(--aaas-text-muted, #6b6b6b);
            margin: 0 0 var(--aaas-space-md, 16px) 0;
        }

        .title {
            font-size: var(--aaas-text-xl, 22px);
            font-weight: 600;
            margin: 0 0 var(--aaas-space-sm, 8px) 0;
        }

        .message {
            font-size: var(--aaas-text-base, 14px);
            color: var(--aaas-text-secondary, #a1a1a1);
            margin: 0 0 var(--aaas-space-xl, 32px) 0;
            max-width: 400px;
        }

        .home-link {
            display: inline-flex;
            align-items: center;
            gap: var(--aaas-space-sm, 8px);
            padding: 12px 24px;
            border-radius: var(--aaas-radius-md, 8px);
            background: var(--aaas-accent, #e8e4dc);
            color: var(--aaas-text-inverse, #0a0a0a);
            font-size: var(--aaas-text-base, 14px);
            font-weight: 600;
            text-decoration: none;
            transition: background var(--aaas-transition-fast, 150ms ease);
        }

        .home-link:hover {
            background: var(--aaas-accent-hover, #ffffff);
        }
    `;

    render() {
        return html`
            <div class="container">
                <div class="status-code">404</div>
                <h1 class="title">Page not found</h1>
                <p class="message">
                    The page you're looking for doesn't exist or has been moved.
                </p>
                <a class="home-link" href="/saas/dashboard">Go to Dashboard</a>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-not-found': SaasNotFound;
    }
}
