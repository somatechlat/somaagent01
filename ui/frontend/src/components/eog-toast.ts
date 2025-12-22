/**
 * Eye of God Toast Component
 * Per Eye of God UIX Design Section 4.1
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - Auto-dismiss support
 * - Toast queue management
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

export type ToastType = 'info' | 'success' | 'warning' | 'error';

export interface ToastMessage {
    id: string;
    type: ToastType;
    title?: string;
    message: string;
    duration?: number;
}

@customElement('eog-toast')
export class EogToast extends LitElement {
    static styles = css`
        :host {
            position: fixed;
            bottom: var(--eog-spacing-lg, 24px);
            right: var(--eog-spacing-lg, 24px);
            z-index: var(--eog-z-toast, 400);
            display: flex;
            flex-direction: column;
            gap: var(--eog-spacing-sm, 8px);
            pointer-events: none;
        }

        .toast {
            background: var(--eog-surface, rgba(30, 41, 59, 0.95));
            border: 1px solid var(--eog-glass-border, rgba(255, 255, 255, 0.08));
            border-radius: var(--eog-radius-lg, 12px);
            padding: var(--eog-spacing-md, 16px);
            min-width: 320px;
            max-width: 400px;
            box-shadow: var(--eog-shadow-lg);
            display: flex;
            gap: var(--eog-spacing-sm, 8px);
            pointer-events: auto;
            animation: slideIn 0.2s ease;
        }

        .toast.closing {
            animation: slideOut 0.2s ease forwards;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(100%);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        @keyframes slideOut {
            from {
                opacity: 1;
                transform: translateX(0);
            }
            to {
                opacity: 0;
                transform: translateX(100%);
            }
        }

        .icon {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            flex-shrink: 0;
        }

        .toast.info .icon { background: var(--eog-info, #3b82f6); }
        .toast.success .icon { background: var(--eog-success, #22c55e); }
        .toast.warning .icon { background: var(--eog-warning, #eab308); }
        .toast.error .icon { background: var(--eog-danger, #ef4444); }

        .content {
            flex: 1;
        }

        .title {
            font-size: var(--eog-text-sm, 13px);
            font-weight: 600;
            color: var(--eog-text-main, #e2e8f0);
            margin: 0 0 2px 0;
        }

        .message {
            font-size: var(--eog-text-sm, 13px);
            color: var(--eog-text-dim, #64748b);
            margin: 0;
        }

        .close-btn {
            width: 20px;
            height: 20px;
            border: none;
            background: transparent;
            color: var(--eog-text-dim, #64748b);
            cursor: pointer;
            font-size: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .close-btn:hover {
            color: var(--eog-text-main, #e2e8f0);
        }
    `;

    @state() private _toasts: ToastMessage[] = [];
    @state() private _closing: Set<string> = new Set();

    private static _instance: EogToast | null = null;

    connectedCallback() {
        super.connectedCallback();
        EogToast._instance = this;
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        if (EogToast._instance === this) {
            EogToast._instance = null;
        }
    }

    render() {
        return html`
            ${this._toasts.map(toast => html`
                <div 
                    class="toast ${toast.type} ${this._closing.has(toast.id) ? 'closing' : ''}"
                    role="alert"
                    aria-live="polite"
                >
                    <div class="icon">
                        ${this._getIcon(toast.type)}
                    </div>
                    <div class="content">
                        ${toast.title ? html`<p class="title">${toast.title}</p>` : ''}
                        <p class="message">${toast.message}</p>
                    </div>
                    <button 
                        class="close-btn" 
                        @click=${() => this._dismiss(toast.id)}
                        aria-label="Dismiss"
                    >
                        ✕
                    </button>
                </div>
            `)}
        `;
    }

    private _getIcon(type: ToastType): string {
        switch (type) {
            case 'success': return '✓';
            case 'warning': return '!';
            case 'error': return '✕';
            default: return 'i';
        }
    }

    /** Add a toast to the queue */
    show(options: Omit<ToastMessage, 'id'>) {
        const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        const toast: ToastMessage = {
            id,
            duration: 5000,
            ...options,
        };

        this._toasts = [...this._toasts, toast];

        if (toast.duration && toast.duration > 0) {
            setTimeout(() => this._dismiss(id), toast.duration);
        }
    }

    /** Dismiss a specific toast */
    private _dismiss(id: string) {
        this._closing = new Set([...this._closing, id]);

        // Remove after animation
        setTimeout(() => {
            this._toasts = this._toasts.filter(t => t.id !== id);
            this._closing.delete(id);
        }, 200);
    }

    /** Clear all toasts */
    clearAll() {
        this._toasts = [];
    }

    /** Static method to show toast from anywhere */
    static show(options: Omit<ToastMessage, 'id'>) {
        if (EogToast._instance) {
            EogToast._instance.show(options);
        }
    }

    /** Static convenience methods */
    static info(message: string, title?: string) {
        EogToast.show({ type: 'info', message, title });
    }

    static success(message: string, title?: string) {
        EogToast.show({ type: 'success', message, title });
    }

    static warning(message: string, title?: string) {
        EogToast.show({ type: 'warning', message, title });
    }

    static error(message: string, title?: string) {
        EogToast.show({ type: 'error', message, title });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-toast': EogToast;
    }
}
