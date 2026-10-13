/**
 * soma-notification-bell — topbar notifications control.
 * Material "notifications" icon + unread badge; click opens the tray.
 * Brand logo art is intentionally not used here.
 */

import { LitElement, css, html } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import './soma-notification-tray.js';

@customElement('soma-notification-bell')
export class SomaNotificationBell extends LitElement {
    static styles = css`
        :host {
            display: inline-block;
            position: relative;
            font-family: var(--skin-font-sans, system-ui, sans-serif);
        }

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

        .bell-btn {
            position: relative;
            width: 40px;
            height: 40px;
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.08));
            border-radius: var(--skin-radius-md, 8px);
            background: var(--skin-color-bg-card, rgba(255, 255, 255, 0.7));
            color: var(--skin-color-text-primary, #1a1a1a);
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            transition: background var(--skin-motion-fast, 0.1s) var(--skin-motion-ease, ease),
                border-color var(--skin-motion-fast, 0.1s) var(--skin-motion-ease, ease);
        }

        .bell-btn:hover {
            background: var(--skin-color-bg-hover, rgba(0, 0, 0, 0.04));
            border-color: var(--skin-color-border-strong, rgba(0, 0, 0, 0.14));
        }

        .bell-btn[aria-expanded='true'] {
            background: var(--skin-color-bg-active, rgba(0, 0, 0, 0.06));
            border-color: var(--skin-color-accent, #1a1a1a);
        }

        .bell-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .badge {
            position: absolute;
            top: -6px;
            right: -6px;
            min-width: 18px;
            height: 18px;
            padding: 0 5px;
            border-radius: var(--skin-radius-full, 9999px);
            background: var(--skin-color-danger, #ef4444);
            color: var(--skin-color-danger-text, #ffffff);
            font-size: 10px;
            font-weight: var(--skin-weight-semibold, 600);
            line-height: 18px;
            text-align: center;
            box-shadow: var(--skin-shadow-sm, 0 1px 2px rgba(0, 0, 0, 0.1));
            pointer-events: none;
        }

        .badge[hidden] {
            display: none;
        }
    `;

    /** Unread count shown on the badge. */
    @property({ type: Number, attribute: 'unread-count' }) unreadCount = 0;

    /** Present-but-disabled when the notifications API is known absent. */
    @property({ type: Boolean, reflect: true }) disabled = false;

    /** Why the control is disabled (shown as the button's title). */
    @property({ type: String, attribute: 'disabled-reason' }) disabledReason =
        'Notifications API is not available.';

    @state() private _open = false;

    private _onToggle(): void {
        if (this.disabled) {
            return;
        }
        this._open = !this._open;
        this.dispatchEvent(
            new CustomEvent('soma-notifications-open-change', {
                detail: { open: this._open },
                bubbles: true,
                composed: true,
            })
        );
    }

    private _onTrayClose(): void {
        this._open = false;
        this.dispatchEvent(
            new CustomEvent('soma-notifications-open-change', {
                detail: { open: false },
                bubbles: true,
                composed: true,
            })
        );
    }

    private _onTrayLoaded(event: Event): void {
        const detail = (event as CustomEvent<{ unread: number }>).detail;
        if (detail && typeof detail.unread === 'number') {
            this.unreadCount = detail.unread;
        }
    }

    /** Open the tray programmatically. */
    openTray(): void {
        if (this.disabled) {
            return;
        }
        this._open = true;
    }

    /** Close the tray programmatically. */
    closeTray(): void {
        this._open = false;
    }

    override render() {
        const badgeLabel =
            this.unreadCount > 99 ? '99+' : String(this.unreadCount);
        return html`
            <button
                class="bell-btn"
                type="button"
                aria-label=${this.unreadCount > 0
                    ? `Notifications, ${this.unreadCount} unread`
                    : 'Notifications'}
                aria-expanded=${this._open ? 'true' : 'false'}
                aria-haspopup="dialog"
                ?disabled=${this.disabled}
                title=${this.disabled ? this.disabledReason : 'Notifications'}
                @click=${this._onToggle}
            >
                <span class="material-symbols-outlined">notifications</span>
                <span class="badge" ?hidden=${this.unreadCount <= 0} aria-hidden="true">${badgeLabel}</span>
            </button>
            <soma-notification-tray
                .open=${this._open && !this.disabled}
                @soma-notification-close=${this._onTrayClose}
                @soma-notifications-loaded=${this._onTrayLoaded}
            ></soma-notification-tray>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-notification-bell': SomaNotificationBell;
    }
}
