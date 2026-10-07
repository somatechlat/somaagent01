/**
 * SOMA Action Menu Component
 * Dropdown menu for row actions
 *
 * VIBE COMPLIANT:
 * - Real Lit 3.x Web Component
 * - Light/dark theme support
 * - Material Icons support
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

export interface ActionItem {
    id: string;
    label: string;
    icon?: string;
    variant?: 'default' | 'danger';
    /** REQ-UIX-005: a disabled control states its blocking reason. */
    disabled?: boolean;
    disabledReason?: string;
}

@customElement('soma-action-menu')
export class SomaActionMenu extends LitElement {
    static styles = css`
        :host {
            display: inline-block;
            position: relative;
        }

        .trigger {
            width: 32px;
            height: 32px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: var(--soma-text-secondary, #666666);
            transition: background 150ms;
        }

        .trigger:hover {
            background: var(--soma-bg-hover, #fafafa);
            color: var(--soma-text-primary, #1a1a1a);
        }

        .icon {
            font-family: 'Material Symbols Outlined';
            font-size: 20px;
        }

        .menu {
            position: absolute;
            top: 100%;
            right: 0;
            margin-top: 4px;
            min-width: 160px;
            background: var(--soma-bg-card, #ffffff);
            border: 1px solid var(--soma-border-light, #e0e0e0);
            border-radius: var(--soma-radius-md, 8px);
            box-shadow: var(--soma-shadow-lg);
            z-index: 100;
            padding: 4px;
            
            opacity: 0;
            transform: translateY(-8px) scale(0.95);
            pointer-events: none;
            transition: all 150ms cubic-bezier(0.4, 0, 0.2, 1);
            transform-origin: top right;
        }

        .menu.open {
            opacity: 1;
            transform: translateY(0) scale(1);
            pointer-events: auto;
        }

        .item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            font-size: 13px;
            color: var(--soma-text-primary, #1a1a1a);
            border-radius: 4px;
            cursor: pointer;
            transition: background 100ms;
        }

        .item:hover {
            background: var(--soma-bg-hover, #fafafa);
        }

        .item.danger {
            color: var(--soma-status-danger, #ef4444);
        }

        .item.danger:hover {
            background: rgba(239, 68, 68, 0.05);
        }

        .item.is-disabled {
            opacity: 0.55;
            cursor: not-allowed;
        }

        .item.is-disabled:hover {
            background: transparent;
        }

        .item-reason {
            display: block;
            font-size: 11px;
            color: var(--soma-text-muted, #888);
            margin-top: 2px;
            line-height: 1.35;
            max-width: 220px;
        }

        .item-icon {
            font-family: 'Material Symbols Outlined';
            font-size: 18px;
            opacity: 0.7;
        }

        /* Overlay to close menu when clicking outside */
        .overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 99;
            display: none;
        }

        .overlay.open {
            display: block;
        }
    `;

    @property({ type: Array }) actions: ActionItem[] = [];

    @state() private _isOpen = false;

    private _toggle(e: Event) {
        e.stopPropagation();
        this._isOpen = !this._isOpen;
    }

    private _close() {
        this._isOpen = false;
    }

    private _handleAction(e: Event, action: ActionItem) {
        e.stopPropagation();
        if (action.disabled) {
            // REQ-UIX-005: a disabled control never fires. Its blocking
            // reason is printed inline in the menu item.
            return;
        }
        this._close();
        this.dispatchEvent(new CustomEvent('soma-action', {
            detail: { action: action.id },
            bubbles: true,
            composed: true
        }));
    }

    render() {
        return html`
            <div class="overlay ${this._isOpen ? 'open' : ''}" @click=${this._close}></div>

            <div class="trigger" @click=${this._toggle}>
                <span class="icon">more_horiz</span>
            </div>

            <div class="menu ${this._isOpen ? 'open' : ''}">
                ${this.actions.map(action => html`
                    <div
                        class="item ${action.variant === 'danger' ? 'danger' : ''} ${action.disabled ? 'is-disabled' : ''}"
                        title=${action.disabled ? (action.disabledReason || 'Blocked') : action.label}
                        @click=${(e: Event) => this._handleAction(e, action)}
                    >
                        ${action.icon ? html`<span class="item-icon">${action.icon}</span>` : nothing}
                        <span>
                            ${action.label}
                            ${action.disabled && action.disabledReason
                                ? html`<span class="item-reason">${action.disabledReason}</span>`
                                : nothing}
                        </span>
                    </div>
                `)}
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-action-menu': SomaActionMenu;
    }
}
