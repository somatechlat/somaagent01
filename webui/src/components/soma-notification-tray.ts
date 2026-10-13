/**
 * soma-notification-tray — popover list bound to the live notifications API.
 *
 * GET  /api/v2/notifications          (via services/api-client.js)
 * POST /api/v2/notifications/{id}/read
 *
 * Honesty: empty ≠ error. A failed load renders an explicit error + Retry and
 * never pretends "0 notifications". Empty success renders "You are all caught up".
 */

import { LitElement, css, html, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { apiClient, ApiError } from '../services/api-client.js';

export interface SomaNotification {
    id: string;
    user_id?: string | null;
    title: string;
    body: string;
    severity: string;
    read_at: string | null;
    created_at: string | null;
}

interface NotificationListResponse {
    notifications: SomaNotification[];
}

export type SomaNotificationLoadState = 'idle' | 'loading' | 'ready' | 'error';

@customElement('soma-notification-tray')
export class SomaNotificationTray extends LitElement {
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

        .scrim {
            position: fixed;
            inset: 0;
            z-index: 390;
        }

        .panel {
            position: fixed;
            top: calc(var(--skin-space-lg, 24px) + 48px);
            right: var(--skin-space-lg, 24px);
            z-index: 400;
            width: min(380px, calc(100vw - 32px));
            max-height: min(480px, calc(100vh - 96px));
            display: flex;
            flex-direction: column;
            background: var(--skin-color-bg-card, rgba(255, 255, 255, 0.92));
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.08));
            border-radius: var(--skin-radius-lg, 12px);
            box-shadow: var(--skin-shadow-overlay, 0 24px 64px rgba(0, 0, 0, 0.18));
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            font-family: var(--skin-font-sans, system-ui, sans-serif);
            color: var(--skin-color-text-primary, #1a1a1a);
            overflow: hidden;
        }

        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: var(--skin-space-sm, 8px);
            padding: var(--skin-space-md, 16px);
            border-bottom: 1px solid var(--skin-color-border-subtle, rgba(0, 0, 0, 0.05));
        }

        .title {
            margin: 0;
            font-size: var(--skin-text-base, 14px);
            font-weight: var(--skin-weight-semibold, 600);
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: var(--skin-space-xs, 4px);
        }

        .icon-btn {
            width: 32px;
            height: 32px;
            border: none;
            border-radius: var(--skin-radius-sm, 4px);
            background: transparent;
            color: var(--skin-color-text-secondary, #666666);
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }

        .icon-btn:hover {
            background: var(--skin-color-bg-hover, rgba(0, 0, 0, 0.04));
            color: var(--skin-color-text-primary, #1a1a1a);
        }

        .icon-btn .material-symbols-outlined {
            font-size: 18px;
        }

        .list {
            flex: 1;
            overflow-y: auto;
            margin: 0;
            padding: 0;
            list-style: none;
        }

        .row {
            display: flex;
            gap: var(--skin-space-sm, 8px);
            padding: var(--skin-space-md, 16px);
            border-bottom: 1px solid var(--skin-color-border-subtle, rgba(0, 0, 0, 0.05));
            cursor: pointer;
            transition: background var(--skin-motion-fast, 0.1s) var(--skin-motion-ease, ease);
        }

        .row:hover {
            background: var(--skin-color-bg-hover, rgba(0, 0, 0, 0.04));
        }

        .row.unread {
            background: var(--skin-color-bg-hover, rgba(0, 0, 0, 0.03));
        }

        .row-icon {
            flex-shrink: 0;
            width: 28px;
            height: 28px;
            border-radius: var(--skin-radius-full, 9999px);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .row-icon .material-symbols-outlined {
            font-size: 16px;
        }

        .row-icon.success {
            background: var(--skin-color-success, #22c55e);
            color: var(--skin-color-success-text, #052e16);
        }
        .row-icon.error {
            background: var(--skin-color-danger, #ef4444);
            color: var(--skin-color-danger-text, #ffffff);
        }
        .row-icon.warning {
            background: var(--skin-color-warning, #eab308);
            color: var(--skin-color-warning-text, #422006);
        }
        .row-icon.info {
            background: var(--skin-color-info, #3b82f6);
            color: var(--skin-color-info-text, #ffffff);
        }

        .row-body {
            flex: 1;
            min-width: 0;
        }

        .row-title {
            font-size: var(--skin-text-sm, 13px);
            font-weight: var(--skin-weight-medium, 500);
            color: var(--skin-color-text-primary, #1a1a1a);
            margin: 0 0 2px;
            word-break: break-word;
        }

        .row-text {
            font-size: var(--skin-text-xs, 11px);
            color: var(--skin-color-text-secondary, #666666);
            margin: 0;
            word-break: break-word;
        }

        .row-time {
            margin-top: 4px;
            font-size: var(--skin-text-xs, 11px);
            color: var(--skin-color-text-muted, #999999);
        }

        .unread-dot {
            flex-shrink: 0;
            width: 8px;
            height: 8px;
            margin-top: 6px;
            border-radius: var(--skin-radius-full, 9999px);
            background: var(--skin-color-accent, #1a1a1a);
        }

        .state {
            padding: var(--skin-space-xl, 32px) var(--skin-space-md, 16px);
            text-align: center;
            color: var(--skin-color-text-secondary, #666666);
            font-size: var(--skin-text-sm, 13px);
        }

        .state .material-symbols-outlined {
            display: block;
            margin: 0 auto var(--skin-space-sm, 8px);
            font-size: 28px;
            opacity: 0.7;
        }

        .error-state {
            color: var(--skin-color-danger, #ef4444);
        }

        .retry-btn {
            margin-top: var(--skin-space-md, 16px);
            padding: 8px 16px;
            border-radius: var(--skin-radius-md, 8px);
            border: 1px solid var(--skin-color-border-strong, rgba(0, 0, 0, 0.14));
            background: var(--skin-color-accent, #1a1a1a);
            color: var(--skin-color-accent-text, #ffffff);
            font-family: inherit;
            font-size: var(--skin-text-sm, 13px);
            font-weight: var(--skin-weight-medium, 500);
            cursor: pointer;
        }

        .retry-btn:hover {
            background: var(--skin-color-accent-hover, #333333);
        }

        .footer {
            display: flex;
            justify-content: center;
            padding: var(--skin-space-sm, 8px);
            border-top: 1px solid var(--skin-color-border-subtle, rgba(0, 0, 0, 0.05));
        }

        .footer-btn {
            border: none;
            background: transparent;
            color: var(--skin-color-text-link, #1a1a1a);
            font-family: inherit;
            font-size: var(--skin-text-xs, 11px);
            font-weight: var(--skin-weight-medium, 500);
            cursor: pointer;
            padding: 6px 10px;
            border-radius: var(--skin-radius-sm, 4px);
        }

        .footer-btn:hover {
            background: var(--skin-color-bg-hover, rgba(0, 0, 0, 0.04));
        }
    `;

    @property({ type: Boolean, reflect: true }) open = false;

    @state() private _notifications: SomaNotification[] = [];
    @state() private _loadState: SomaNotificationLoadState = 'idle';
    @state() private _errorMessage = '';
    @state() private _markingIds: string[] = [];

    override updated(changed: Map<string, unknown>): void {
        if (changed.has('open') && this.open && this._loadState === 'idle') {
            void this.load();
        }
    }

    /** Fetch notifications from the live API. */
    async load(): Promise<void> {
        this._loadState = 'loading';
        this._errorMessage = '';
        try {
            const data = await apiClient.get<NotificationListResponse>('/notifications');
            const list = Array.isArray(data?.notifications) ? data.notifications : [];
            this._notifications = list;
            this._loadState = 'ready';
            this.dispatchEvent(
                new CustomEvent('soma-notifications-loaded', {
                    detail: {
                        items: list,
                        unread: list.filter((n) => !n.read_at).length,
                    },
                    bubbles: true,
                    composed: true,
                })
            );
        } catch (error) {
            this._notifications = [];
            this._loadState = 'error';
            if (error instanceof ApiError && (error.status === 404 || error.status === 0)) {
                this._errorMessage = 'Notifications API is not available.';
            } else if (error instanceof Error && error.message) {
                this._errorMessage = error.message;
            } else {
                this._errorMessage = 'Failed to load notifications.';
            }
            this.dispatchEvent(
                new CustomEvent('soma-notifications-error', {
                    detail: { message: this._errorMessage },
                    bubbles: true,
                    composed: true,
                })
            );
        }
    }

    private async _markRead(notification: SomaNotification): Promise<void> {
        if (notification.read_at || this._markingIds.includes(notification.id)) {
            return;
        }
        this._markingIds = [...this._markingIds, notification.id];
        try {
            await apiClient.post(`/notifications/${encodeURIComponent(notification.id)}/read`, {});
            this._notifications = this._notifications.map((n) =>
                n.id === notification.id
                    ? { ...n, read_at: new Date().toISOString() }
                    : n
            );
            this.dispatchEvent(
                new CustomEvent('soma-notification-read', {
                    detail: { id: notification.id },
                    bubbles: true,
                    composed: true,
                })
            );
        } catch (error) {
            const message =
                error instanceof Error && error.message
                    ? error.message
                    : 'Failed to mark notification read.';
            this.dispatchEvent(
                new CustomEvent('soma-toast', {
                    detail: { kind: 'error', message },
                    bubbles: true,
                    composed: true,
                })
            );
        } finally {
            this._markingIds = this._markingIds.filter((id) => id !== notification.id);
        }
    }

    private _openItem(notification: SomaNotification): void {
        void this._markRead(notification);
        this.dispatchEvent(
            new CustomEvent('soma-notification-open', {
                detail: { id: notification.id },
                bubbles: true,
                composed: true,
            })
        );
    }

    private _close(): void {
        this.open = false;
        this.dispatchEvent(
            new CustomEvent('soma-notification-close', {
                bubbles: true,
                composed: true,
            })
        );
    }

    private _openCenter(): void {
        this._close();
        this.dispatchEvent(
            new CustomEvent('soma-open-notification-center', {
                bubbles: true,
                composed: true,
            })
        );
    }

    private _formatTime(iso: string | null): string {
        if (!iso) {
            return '';
        }
        const date = new Date(iso);
        if (Number.isNaN(date.getTime())) {
            return '';
        }
        return date.toLocaleString();
    }

    private _severityIcon(severity: string): { cls: string; icon: string } {
        const s = (severity || '').toLowerCase();
        if (s.includes('error') || s.includes('danger') || s.includes('fail')) {
            return { cls: 'error', icon: 'error' };
        }
        if (s.includes('warn') || s.includes('job')) {
            return { cls: 'warning', icon: 'schedule' };
        }
        if (s.includes('success') || s.includes('done')) {
            return { cls: 'success', icon: 'check_circle' };
        }
        return { cls: 'info', icon: 'info' };
    }

    private _renderRow(notification: SomaNotification) {
        const unread = !notification.read_at;
        const sev = this._severityIcon(notification.severity);
        const marking = this._markingIds.includes(notification.id);
        return html`
            <li
                class="row ${unread ? 'unread' : ''}"
                tabindex="0"
                role="button"
                aria-label=${notification.title}
                @click=${() => this._openItem(notification)}
                @keydown=${(e: KeyboardEvent) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        this._openItem(notification);
                    }
                }}
            >
                <div class="row-icon ${sev.cls}">
                    <span class="material-symbols-outlined">${sev.icon}</span>
                </div>
                <div class="row-body">
                    <p class="row-title">${notification.title}</p>
                    <p class="row-text">${notification.body}</p>
                    <div class="row-time">${this._formatTime(notification.created_at)}</div>
                    ${unread
                        ? html`
                              <button
                                  class="footer-btn"
                                  type="button"
                                  ?disabled=${marking}
                                  @click=${(e: Event) => {
                                      e.stopPropagation();
                                      void this._markRead(notification);
                                  }}
                              >
                                  ${marking ? 'Marking…' : 'Mark read'}
                              </button>
                          `
                        : nothing}
                </div>
                ${unread ? html`<span class="unread-dot" aria-hidden="true"></span>` : nothing}
            </li>
        `;
    }

    override render() {
        if (!this.open) {
            return nothing;
        }
        return html`
            <div class="scrim" @click=${this._close}></div>
            <div class="panel" role="dialog" aria-label="Notifications">
                <div class="header">
                    <h2 class="title">Notifications</h2>
                    <div class="header-actions">
                        <button
                            class="icon-btn"
                            type="button"
                            aria-label="Refresh notifications"
                            @click=${() => void this.load()}
                        >
                            <span class="material-symbols-outlined">refresh</span>
                        </button>
                        <button class="icon-btn" type="button" aria-label="Close notifications" @click=${this._close}>
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                </div>

                ${this._loadState === 'loading'
                    ? html`
                          <div class="state" role="status">
                              <span class="material-symbols-outlined">hourglass_empty</span>
                              Loading notifications…
                          </div>
                      `
                    : this._loadState === 'error'
                      ? html`
                            <div class="state error-state" role="alert">
                                <span class="material-symbols-outlined">error</span>
                                <div>${this._errorMessage}</div>
                                <button class="retry-btn" type="button" @click=${() => void this.load()}>Retry</button>
                            </div>
                        `
                      : this._notifications.length === 0
                        ? html`
                              <div class="state" role="status">
                                  <span class="material-symbols-outlined">done_all</span>
                                  You are all caught up
                              </div>
                          `
                        : html`
                              <ul class="list">
                                  ${this._notifications.map((n) => this._renderRow(n))}
                              </ul>
                          `}

                <div class="footer">
                    <button class="footer-btn" type="button" @click=${this._openCenter}>
                        Open notification center
                    </button>
                </div>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-notification-tray': SomaNotificationTray;
    }
}
