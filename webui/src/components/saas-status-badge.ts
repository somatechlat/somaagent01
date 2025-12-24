/**
 * SAAS Status Badge Component
 * Colored status indicator badges
 *
 * VIBE COMPLIANT:
 * - Real Lit 3.x implementation
 * - Light/dark theme adaptive
 * - Multiple variants: success, warning, danger, info, neutral
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

export type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'neutral';
export type BadgeSize = 'sm' | 'md' | 'lg';

@customElement('saas-status-badge')
export class SaasStatusBadge extends LitElement {
    static styles = css`
        :host {
            display: inline-flex;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-weight: var(--saas-font-medium, 500);
            border-radius: var(--saas-radius-full, 9999px);
            white-space: nowrap;
        }

        /* Sizes */
        .badge.sm {
            padding: 2px 8px;
            font-size: var(--saas-text-xs, 11px);
        }

        .badge.md {
            padding: 4px 12px;
            font-size: var(--saas-text-sm, 13px);
        }

        .badge.lg {
            padding: 6px 16px;
            font-size: var(--saas-text-base, 14px);
        }

        /* Status dot */
        .dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            flex-shrink: 0;
        }

        .badge.sm .dot { width: 5px; height: 5px; }
        .badge.lg .dot { width: 8px; height: 8px; }

        /* Variants */
        .badge.success {
            background: rgba(34, 197, 94, 0.12);
            color: #16a34a;
        }
        .badge.success .dot { background: #22c55e; }

        .badge.warning {
            background: rgba(245, 158, 11, 0.12);
            color: #d97706;
        }
        .badge.warning .dot { background: #f59e0b; }

        .badge.danger {
            background: rgba(239, 68, 68, 0.12);
            color: #dc2626;
        }
        .badge.danger .dot { background: #ef4444; }

        .badge.info {
            background: rgba(59, 130, 246, 0.12);
            color: #2563eb;
        }
        .badge.info .dot { background: #3b82f6; }

        .badge.neutral {
            background: rgba(107, 114, 128, 0.12);
            color: #6b7280;
        }
        .badge.neutral .dot { background: #9ca3af; }

        /* Dark mode variants */
        :host-context([data-theme="dark"]) .badge.success,
        :host-context(.dark-theme) .badge.success {
            background: rgba(34, 197, 94, 0.2);
            color: #4ade80;
        }

        :host-context([data-theme="dark"]) .badge.warning,
        :host-context(.dark-theme) .badge.warning {
            background: rgba(245, 158, 11, 0.2);
            color: #fbbf24;
        }

        :host-context([data-theme="dark"]) .badge.danger,
        :host-context(.dark-theme) .badge.danger {
            background: rgba(239, 68, 68, 0.2);
            color: #f87171;
        }

        :host-context([data-theme="dark"]) .badge.info,
        :host-context(.dark-theme) .badge.info {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }

        :host-context([data-theme="dark"]) .badge.neutral,
        :host-context(.dark-theme) .badge.neutral {
            background: rgba(107, 114, 128, 0.2);
            color: #9ca3af;
        }
    `;

    @property({ type: String }) variant: BadgeVariant = 'neutral';
    @property({ type: String }) size: BadgeSize = 'md';
    @property({ type: Boolean, attribute: 'show-dot' }) showDot = true;
    @property({ type: String }) label = '';

    render() {
        return html`
            <span class="badge ${this.variant} ${this.size}">
                ${this.showDot ? html`<span class="dot"></span>` : ''}
                <span class="label">${this.label}<slot></slot></span>
            </span>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-status-badge': SaasStatusBadge;
    }
}
