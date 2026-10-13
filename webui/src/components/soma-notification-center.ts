/**
 * soma-notification-center — full table view for the /notifications route.
 * Bound to GET /api/v2/notifications and POST /api/v2/notifications/{id}/read.
 *
 * Honesty: empty ≠ error. Failures render error + Retry; empty success renders
 * "You are all caught up".
 */

import { LitElement, css, html, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { apiClient, ApiError } from '../services/api-client.js';
import type { SomaNotification } from './soma-notification-tray.js';

interface NotificationListResponse {
    notifications: SomaNotification[];
}

export type SomaNotificationLoadState = 'idle' | 'loading' | 'ready' | 'error';

@customElement('soma-notification-center')
export class SomaNotificationCenter extends LitElement {
    static styles = css`
        :host {
            display: block;
            font-family: var(--skin-font-sans, system-ui, sans-serif);
            color: var(--skin-color-text-primary, #1a1a1a);
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

        .panel {
            background: var(--skin-color-bg-card, rgba(255, 255, 255, 0.92));
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.08));
            border-radius: var(--skin-radius-lg, 12px);
            box-shadow: var(--skin-shadow-md, 0 4px 6px rgba(0, 0, 0, 0.08));
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            overflow: hidden;
        }

        .toolbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: var(--skin-space-md, 16px);
            padding: var(--skin-space-md, 16px) var(--skin-space-lg, 24px);
            border-bottom: 1px solid var(--skin-color-border-subtle, rgba(0, 0, 0, 0.05));
        }

        .title {
            margin: 0;
            font-size: var(--skin-text-lg, 16px);
            font-weight: var(--skin-weight-semibold, 600);
        }

        .subtitle {
            margin: 2px 0 0;
            font-size: var(--skin-text-xs, 11px);
            color: var(--skin-color-text-secondary, #666666);
        }

        .toolbar-actions {
            display: flex;
            gap: var(--skin-space-sm, 8px);
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 14px;
            border-radius: var(--skin-radius-md, 8px);
            border: 1px solid var(--skin-color-border-strong, rgba(0, 0, 0, 0.14));
            background: var(--skin-color-accent, #1a1a1a);
            color: var(--skin-color-accent-text, #ffffff);
            font-family: inherit;
            font-size: var(--skin-text-sm, 13px);
            font-weight: var(--skin-weight-medium, 500);
            cursor: pointer;
            transition: background var(--skin-motion-fast, 0.1s) var(--skin-motion-ease, ease);
        }

        .btn:hover:not(:disabled) {
            background: var(--skin-color-accent-hover, #333333);
        }

        .btn.secondary {
            background: transparent;
            color: var(--skin-color-text-primary, #1a1a1a);
        }

        .btn.secondary:hover:not(:disabled) {
            background: var(--skin-color-bg-hover, rgba(0, 0, 0, 0.04));
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .btn .material-symbols-outlined {
            font-size: 16px;
        }

        .table-wrap {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th {
            text-align: left;
            padding: var(--skin-space-sm, 8px) var(--skin-space-md, 16px);
            font-size: var(--skin-text-xs, 11px);
            font-weight: var(--skin-weight-semibold, 600);
            color: var(--skin-color-text-secondary, #666666);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.08));
            background: var(--skin-color-bg-hover, rgba(0, 0, 0, 0.02));
            white-space: nowrap;
        }

        td {
            padding: var(--skin-space-md, 16px);
            font-size: var(--skin-text-sm, 13px);
            border-bottom: 1px solid var(--skin-color-border-subtle, rgba(0, 0, 0, 0.05));
            vertical-align: top;
        }

        tbody tr:last-child td {
            border-bottom: none;
        }

        tbody tr:hover td {
            background: var(--skin-color-bg-hover, rgba(0, 0, 0, 0.03));
        }

        tbody tr.unread td {
            background: var(--skin-color-bg-hover, rgba(0, 0, 0, 0.02));
        }

        .type-pill {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 2px 8px;
            border-radius: var(--skin-radius-full, 9999px);
            font-size: var(--skin-text-xs, 11px);
            font-weight: var(--skin-weight-medium, 500);
            white-space: nowrap;
        }

        .type-pill.success {
            background: var(--skin-color-success, #22c55e);
            color: var(--skin-color-success-text, #052e16);
        }
        .type-pill.error {
            background: var(--skin-color-danger, #ef4444);
            color: var(--skin-color-danger-text, #ffffff);
        }
        .type-pill.warning {
            background: var(--skin-color-warning, #eab308);
            color: var(--skin-color-warning-text, #422006);
        }
        .type-pill.info {
            background: var(--skin-color-info, #3b82f6);
            color: var(--skin-color-info-text, #ffffff);
        }

        .cell-title {
            font-weight: var(--skin-weight-medium, 500);
            color: var(--skin-color-text-primary, #1a1a1a);
            margin: 0 0 4px;
            word-break: break-word;
        }

        .cell-body {
            margin: 0;
            color: var(--skin-color-text-secondary, #666666);
            word-break: break-word;
        }

        .cell-time {
            white-space: nowrap;
            color: var(--skin-color-text-muted, #999999);
            font-size: var(--skin-text-xs, 11px);
        }

        .actions {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }

        .row-btn {
            padding: 4px 10px;
            border-radius: var(--skin-radius-sm, 4px);
            border: 1px solid var(--skin-color-border-strong, rgba(0, 0, 0, 0.14));
            background: transparent;
            color: var(--skin-color-text-primary, #1a1a1a);
            font-family: inherit;
            font-size: var(--skin-text-xs, 11px);
            cursor: pointer;
        }

        .row-btn:hover:not(:disabled) {
            background: var(--skin-color-bg-hover, rgba(0, 0, 0, 0.04));
        }

        .row-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .state {
            padding: var(--skin-space-2xl, 48px) var(--skin-space-lg, 24px);
            text-align: center;
            color: var(--skin-color-text-secondary, #666666);
            font-size: var(--skin-text-base, 14px);
        }

        .state .material-symbols-outlined {
            display: block;
            margin: 0 auto var(--skin-space-md, 16px);
            font-size: 36px;
            opacity: 0.7;
        }

        .error-state {
            color: var(--skin-color-danger, #ef4444);
        }

        .pagination {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: var(--skin-space-md, 16px);
            padding: var(--skin-space-md, 16px) var(--skin-space-lg, 24px);
            border-top: 1px solid var(--skin-color-border-subtle, rgba(0, 0, 0, 0.05));
            font-size: var(--skin-text-xs, 11px);
            color: var(--skin-color-text-secondary, #666666);
        }

        .page-controls {
            display: flex;
            gap: var(--skin-space-sm, 8px);
        }
    `;

    /** Max rows fetched from the API in one request. */
    @property({ type: Number, attribute: 'page-size' }) pageSize = 10;

    /** API list limit (server-side cap). */
    @property({ type: Number, attribute: 'fetch-limit' }) fetchLimit = 50;

    @state() private _notifications: SomaNotification[] = [];
    @state() private _loadState: SomaNotificationLoadState = 'idle';
    @state() private _errorMessage = '';
    @state() private _page = 1;
    @state() private _markingIds: string[] = [];

    override connectedCallback(): void {
        super.connectedCallback();
        void this.load();
    }

    /** Fetch notifications from the live API. */
    async load(): Promise<void> {
        this._loadState = 'loading';
        this._errorMessage = '';
        try {
            const path = `/notifications?limit=${encodeURIComponent(String(this.fetchLimit))}`;
            const data = await apiClient.get<NotificationListResponse>(path);
            const list = Array.isArray(data?.notifications) ? data.notifications : [];
            this._notifications = list;
            this._page = 1;
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

    private get _totalPages(): number {
        return Math.max(1, Math.ceil(this._notifications.length / this.pageSize));
    }

    private get _pageItems(): SomaNotification[] {
        const start = (this._page - 1) * this.pageSize;
        return this._notifications.slice(start, start + this.pageSize);
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
                detail: {
                    id: notification.id,
                    title: notification.title,
                    body: notification.body,
                },
                bubbles: true,
                composed: true,
            })
        );
    }

    private _formatTime(iso: string | null): string {
        if (!iso) {
            return '—';
        }
        const date = new Date(iso);
        if (Number.isNaN(date.getTime())) {
            return '—';
        }
        return date.toLocaleString();
    }

    private _severityClass(severity: string): string {
        const s = (severity || '').toLowerCase();
        if (s.includes('error') || s.includes('danger') || s.includes('fail')) {
            return 'error';
        }
        if (s.includes('warn') || s.includes('job')) {
            return 'warning';
        }
        if (s.includes('success') || s.includes('done')) {
            return 'success';
        }
        return 'info';
    }

    private _severityLabel(severity: string): string {
        return severity || 'info';
    }

    override render() {
        const unread = this._notifications.filter((n) => !n.read_at).length;
        return html`
            <section class="panel" aria-label="Notification center">
                <div class="toolbar">
                    <div>
                        <h1 class="title">Notifications</h1>
                        <p class="subtitle">
                            ${this._loadState === 'ready'
                                ? `${this._notifications.length} total · ${unread} unread`
                                : 'Live notification feed'}
                        </p>
                    </div>
                    <div class="toolbar-actions">
                        <button
                            class="btn secondary"
                            type="button"
                            ?disabled=${this._loadState === 'loading'}
                            @click=${() => void this.load()}
                        >
                            <span class="material-symbols-outlined">refresh</span>
                            Refresh
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
                                <button class="btn" type="button" @click=${() => void this.load()}>Retry</button>
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
                              <div class="table-wrap">
                                  <table>
                                      <thead>
                                          <tr>
                                              <th scope="col">Time</th>
                                              <th scope="col">Type</th>
                                              <th scope="col">Title</th>
                                              <th scope="col">Body</th>
                                              <th scope="col">Actions</th>
                                          </tr>
                                      </thead>
                                      <tbody>
                                          ${this._pageItems.map((n) => {
                                              const isUnread = !n.read_at;
                                              const marking = this._markingIds.includes(n.id);
                                              const sev = this._severityClass(n.severity);
                                              return html`
                                                  <tr class=${isUnread ? 'unread' : nothing}>
                                                      <td class="cell-time">${this._formatTime(n.created_at)}</td>
                                                      <td>
                                                          <span class="type-pill ${sev}"
                                                              >${this._severityLabel(n.severity)}</span
                                                          >
                                                      </td>
                                                      <td>
                                                          <p class="cell-title">${n.title}</p>
                                                      </td>
                                                      <td>
                                                          <p class="cell-body">${n.body}</p>
                                                      </td>
                                                      <td>
                                                          <div class="actions">
                                                              <button
                                                                  class="row-btn"
                                                                  type="button"
                                                                  @click=${() => this._openItem(n)}
                                                              >
                                                                  Open
                                                              </button>
                                                              ${isUnread
                                                                  ? html`
                                                                        <button
                                                                            class="row-btn"
                                                                            type="button"
                                                                            ?disabled=${marking}
                                                                            @click=${() => void this._markRead(n)}
                                                                        >
                                                                            ${marking ? 'Marking…' : 'Mark read'}
                                                                        </button>
                                                                    `
                                                                  : nothing}
                                                          </div>
                                                      </td>
                                                  </tr>
                                              `;
                                          })}
                                      </tbody>
                                  </table>
                              </div>
                              <div class="pagination">
                                  <span>
                                      Page ${this._page} of ${this._totalPages} ·
                                      ${this._notifications.length} loaded
                                  </span>
                                  <div class="page-controls">
                                      <button
                                          class="btn secondary"
                                          type="button"
                                          ?disabled=${this._page <= 1}
                                          @click=${() => {
                                              this._page = Math.max(1, this._page - 1);
                                          }}
                                      >
                                          Previous
                                      </button>
                                      <button
                                          class="btn secondary"
                                          type="button"
                                          ?disabled=${this._page >= this._totalPages}
                                          @click=${() => {
                                              this._page = Math.min(this._totalPages, this._page + 1);
                                          }}
                                      >
                                          Next
                                      </button>
                                  </div>
                              </div>
                          `}
            </section>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-notification-center': SomaNotificationCenter;
    }
}
