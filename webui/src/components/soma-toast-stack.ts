/**
 * soma-toast-stack — global toast host (M-008).
 * Listens for `soma-toast` CustomEvents and renders a glass toast stack.
 *
 * Contract:
 *   window.dispatchEvent(new CustomEvent('soma-toast', {
 *     detail: { kind: 'success'|'error'|'info'|'job', message, action?, id?, timeoutMs? }
 *   }))
 *
 * Dismiss: success/info/job auto-dismiss · error sticky until dismissed.
 * Capacity: max 3 visible (oldest non-sticky yields first).
 * Events out: `soma-toast-action` { id, actionLabel } · `soma-toast-dismiss` { id }
 */

import { LitElement, css, html, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';

export type SomaToastKind = 'success' | 'error' | 'info' | 'job';

export interface SomaToastAction {
    label: string;
    /** Echoed back on `soma-toast-action`. Defaults to the toast id. */
    id?: string;
}

export interface SomaToastDetail {
    kind: SomaToastKind;
    message: string;
    action?: SomaToastAction;
    /** Stable id; generated when omitted. */
    id?: string;
    /** Auto-dismiss delay in ms. Ignored for sticky (error) toasts. */
    timeoutMs?: number;
}

export interface SomaToastItem extends SomaToastDetail {
    id: string;
    sticky: boolean;
}

const MAX_VISIBLE = 3;

const DEFAULT_TIMEOUT_MS: Record<SomaToastKind, number> = {
    success: 3000,
    info: 4000,
    job: 5000,
    error: 0, // sticky
};

/** Dispatch a toast onto the global stack. */
export function pushToast(detail: SomaToastDetail): string {
    const id = detail.id ?? `toast-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    window.dispatchEvent(
        new CustomEvent<SomaToastDetail & { id: string }>('soma-toast', {
            detail: { ...detail, id },
            bubbles: true,
            composed: true,
        })
    );
    return id;
}

@customElement('soma-toast-stack')
export class SomaToastStack extends LitElement {
    static styles = css`
        :host {
            display: contents;
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

        .stack {
            position: fixed;
            right: var(--skin-space-lg, 24px);
            bottom: var(--skin-space-lg, 24px);
            z-index: 400;
            display: flex;
            flex-direction: column;
            gap: var(--skin-space-sm, 8px);
            width: min(380px, calc(100vw - 32px));
            pointer-events: none;
        }

        .toast {
            pointer-events: auto;
            display: flex;
            align-items: flex-start;
            gap: var(--skin-space-sm, 8px);
            padding: var(--skin-space-md, 16px);
            border-radius: var(--skin-radius-md, 8px);
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.08));
            background: var(--skin-color-bg-card, rgba(255, 255, 255, 0.92));
            box-shadow: var(--skin-shadow-md, 0 4px 6px rgba(0, 0, 0, 0.1));
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            font-family: var(--skin-font-sans, system-ui, sans-serif);
            color: var(--skin-color-text-primary, #1a1a1a);
            animation: toast-in var(--skin-motion-normal, 0.2s) var(--skin-motion-ease, ease);
        }

        @keyframes toast-in {
            from {
                opacity: 0;
                transform: translateY(8px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .toast.success {
            border-left: 3px solid var(--skin-color-success, #22c55e);
        }
        .toast.error {
            border-left: 3px solid var(--skin-color-danger, #ef4444);
        }
        .toast.info {
            border-left: 3px solid var(--skin-color-info, #3b82f6);
        }
        .toast.job {
            border-left: 3px solid var(--skin-color-warning, #eab308);
        }

        .icon {
            flex-shrink: 0;
            margin-top: 1px;
        }
        .toast.success .icon {
            color: var(--skin-color-success, #22c55e);
        }
        .toast.error .icon {
            color: var(--skin-color-danger, #ef4444);
        }
        .toast.info .icon {
            color: var(--skin-color-info, #3b82f6);
        }
        .toast.job .icon {
            color: var(--skin-color-warning, #eab308);
        }

        .body {
            flex: 1;
            min-width: 0;
            display: flex;
            flex-direction: column;
            gap: var(--skin-space-xs, 4px);
        }

        .message {
            font-size: var(--skin-text-sm, 13px);
            line-height: var(--skin-leading-normal, 1.5);
            color: var(--skin-color-text-primary, #1a1a1a);
            word-break: break-word;
        }

        .action-btn {
            align-self: flex-start;
            margin-top: var(--skin-space-xs, 4px);
            padding: 4px 10px;
            border-radius: var(--skin-radius-sm, 4px);
            border: 1px solid var(--skin-color-border-strong, rgba(0, 0, 0, 0.14));
            background: transparent;
            color: var(--skin-color-accent, #1a1a1a);
            font-family: inherit;
            font-size: var(--skin-text-xs, 11px);
            font-weight: var(--skin-weight-medium, 500);
            cursor: pointer;
            transition: background var(--skin-motion-fast, 0.1s) var(--skin-motion-ease, ease);
        }

        .action-btn:hover {
            background: var(--skin-color-bg-hover, rgba(0, 0, 0, 0.04));
        }

        .dismiss-btn {
            flex-shrink: 0;
            width: 28px;
            height: 28px;
            border: none;
            border-radius: var(--skin-radius-sm, 4px);
            background: transparent;
            color: var(--skin-color-text-secondary, #666666);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background var(--skin-motion-fast, 0.1s) var(--skin-motion-ease, ease);
        }

        .dismiss-btn:hover {
            background: var(--skin-color-bg-hover, rgba(0, 0, 0, 0.04));
            color: var(--skin-color-text-primary, #1a1a1a);
        }

        .dismiss-btn .material-symbols-outlined {
            font-size: 18px;
        }

        .counter {
            align-self: flex-end;
            padding: 2px 8px;
            border-radius: var(--skin-radius-full, 9999px);
            background: var(--skin-color-bg-card, rgba(255, 255, 255, 0.92));
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.08));
            color: var(--skin-color-text-secondary, #666666);
            font-size: var(--skin-text-xs, 11px);
            pointer-events: auto;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
        }
    `;

    @state() private _toasts: SomaToastItem[] = [];

    private _timers = new Map<string, number>();

    override connectedCallback(): void {
        super.connectedCallback();
        window.addEventListener('soma-toast', this._onToast as EventListener);
    }

    override disconnectedCallback(): void {
        super.disconnectedCallback();
        window.removeEventListener('soma-toast', this._onToast as EventListener);
        for (const timer of this._timers.values()) {
            window.clearTimeout(timer);
        }
        this._timers.clear();
    }

    private _onToast = (event: Event): void => {
        const detail = (event as CustomEvent<SomaToastDetail & { id?: string }>).detail;
        if (!detail || typeof detail.message !== 'string' || !detail.kind) {
            return;
        }
        this._push({
            kind: detail.kind,
            message: detail.message,
            action: detail.action,
            id: detail.id,
            timeoutMs: detail.timeoutMs,
        });
    };

    private _push(detail: SomaToastDetail & { id?: string }): void {
        const id = detail.id ?? `toast-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
        const sticky = detail.kind === 'error';
        const item: SomaToastItem = {
            kind: detail.kind,
            message: detail.message,
            action: detail.action,
            id,
            sticky,
            timeoutMs: detail.timeoutMs,
        };

        let next = [...this._toasts.filter((t) => t.id !== id), item];
        while (next.length > MAX_VISIBLE) {
            const evictIndex = next.findIndex((t) => !t.sticky);
            const dropIndex = evictIndex >= 0 ? evictIndex : 0;
            const dropped = next[dropIndex];
            this._clearTimer(dropped.id);
            next = next.filter((_, i) => i !== dropIndex);
        }
        this._toasts = next;

        if (!sticky) {
            const timeout = detail.timeoutMs ?? DEFAULT_TIMEOUT_MS[detail.kind];
            if (timeout > 0) {
                const timer = window.setTimeout(() => this._dismiss(id), timeout);
                this._timers.set(id, timer);
            }
        }
    }

    private _clearTimer(id: string): void {
        const timer = this._timers.get(id);
        if (timer !== undefined) {
            window.clearTimeout(timer);
            this._timers.delete(id);
        }
    }

    private _dismiss(id: string): void {
        this._clearTimer(id);
        this._toasts = this._toasts.filter((t) => t.id !== id);
        this.dispatchEvent(
            new CustomEvent('soma-toast-dismiss', {
                detail: { id },
                bubbles: true,
                composed: true,
            })
        );
    }

    private _runAction(toast: SomaToastItem): void {
        const actionLabel = toast.action?.label ?? '';
        const actionId = toast.action?.id ?? toast.id;
        this.dispatchEvent(
            new CustomEvent('soma-toast-action', {
                detail: { id: actionId, actionLabel },
                bubbles: true,
                composed: true,
            })
        );
        this._dismiss(toast.id);
    }

    private _iconFor(kind: SomaToastKind): string {
        switch (kind) {
            case 'success':
                return 'check_circle';
            case 'error':
                return 'error';
            case 'job':
                return 'schedule';
            case 'info':
            default:
                return 'info';
        }
    }

    override render() {
        return html`
            <div class="stack" aria-live="polite" aria-relevant="additions text">
                ${this._toasts.map(
                    (toast) => html`
                        <div class="toast ${toast.kind}" role="${toast.kind === 'error' ? 'alert' : 'status'}">
                            <span class="material-symbols-outlined icon">${this._iconFor(toast.kind)}</span>
                            <div class="body">
                                <div class="message">${toast.message}</div>
                                ${toast.action
                                    ? html`
                                          <button
                                              class="action-btn"
                                              type="button"
                                              @click=${() => this._runAction(toast)}
                                          >
                                              ${toast.action.label}
                                          </button>
                                      `
                                    : nothing}
                            </div>
                            <button
                                class="dismiss-btn"
                                type="button"
                                aria-label="Dismiss notification"
                                @click=${() => this._dismiss(toast.id)}
                            >
                                <span class="material-symbols-outlined">close</span>
                            </button>
                        </div>
                    `
                )}
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-toast-stack': SomaToastStack;
    }
}
