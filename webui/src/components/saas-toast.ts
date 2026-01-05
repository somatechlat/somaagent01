import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

@customElement('saas-toast')
export class SaasToast extends LitElement {
    static styles = css`
        :host {
            position: fixed;
            bottom: 24px;
            right: 24px;
            z-index: 9999;
            pointer-events: none;
        }

        .toast {
            background: var(--saas-surface, #1e293b);
            border: 1px solid var(--saas-border-color, rgba(255, 255, 255, 0.1));
            color: var(--saas-text-main, #e2e8f0);
            padding: 16px 20px;
            border-radius: 12px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 300px;
            transform: translateY(20px);
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            pointer-events: auto;
        }

        .toast.visible {
            transform: translateY(0);
            opacity: 1;
        }

        .toast.success { border-left: 4px solid var(--saas-success, #22c55e); }
        .toast.error { border-left: 4px solid var(--saas-danger, #ef4444); }
        .toast.info { border-left: 4px solid var(--saas-info, #3b82f6); }
        .toast.warning { border-left: 4px solid var(--saas-warning, #f59e0b); }

        .icon {
            font-family: 'Material Symbols Outlined';
            font-size: 20px;
        }

        .success .icon { color: var(--saas-success, #22c55e); }
        .error .icon { color: var(--saas-danger, #ef4444); }
        .info .icon { color: var(--saas-info, #3b82f6); }
        .warning .icon { color: var(--saas-warning, #f59e0b); }

        .content {
            flex: 1;
        }

        .title {
            font-weight: 600;
            font-size: 14px;
            margin-bottom: 2px;
        }

        .message {
            font-size: 13px;
            color: var(--saas-text-dim, #94a3b8);
        }

        .close {
            cursor: pointer;
            opacity: 0.5;
            transition: opacity 0.2s;
        }

        .close:hover { opacity: 1; }
    `;

    @property() type: 'success' | 'error' | 'info' | 'warning' = 'info';
    @property() title = '';
    @property() message = '';
    @property({ type: Number }) duration = 5000;
    @property({ type: Boolean }) visible = false;

    private _timer: any;

    updated(changedProperties: Map<string, any>) {
        if (changedProperties.has('visible') && this.visible) {
            this._startTimer();
        }
    }

    private _startTimer() {
        if (this._timer) clearTimeout(this._timer);
        if (this.duration > 0) {
            this._timer = setTimeout(() => {
                this.visible = false;
                this.dispatchEvent(new CustomEvent('closed'));
            }, this.duration);
        }
    }

    private _close() {
        this.visible = false;
        if (this._timer) clearTimeout(this._timer);
        this.dispatchEvent(new CustomEvent('closed'));
    }

    private _getIcon() {
        switch (this.type) {
            case 'success': return 'check_circle';
            case 'error': return 'error';
            case 'warning': return 'warning';
            default: return 'info';
        }
    }

    render() {
        return html`
            <div class="toast ${this.type} ${this.visible ? 'visible' : ''}">
                <span class="icon">${this._getIcon()}</span>
                <div class="content">
                    ${this.title ? html`<div class="title">${this.title}</div>` : ''}
                    <div class="message">${this.message}</div>
                </div>
                <span class="material-symbols-outlined close" @click="${this._close}">close</span>
            </div>
        `;
    }
}
