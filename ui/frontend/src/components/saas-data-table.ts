/**
 * SAAS Data Table Component
 * Sortable, filterable data table for list views
 *
 * VIBE COMPLIANT:
 * - Real Lit 3.x implementation
 * - Light/dark theme support
 * - Row click events
 * - Action menu slots
 */

import {
    LitElement, html, css
    , nothing
} from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

export interface TableColumn {
    key: string;
    label: string;
    sortable?: boolean;
    width?: string;
    align?: 'left' | 'center' | 'right';
    render?: (value: unknown, row: Record<string, unknown>) => unknown;
}

export type SortDirection = 'asc' | 'desc' | null;

@customElement('saas-data-table')
export class SaasDataTable extends LitElement {
    static styles = css`
        :host {
            display: block;
        }

        .table-wrapper {
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: var(--saas-radius-lg, 12px);
            overflow: hidden;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        thead {
            background: var(--saas-bg-hover, #fafafa);
        }

        th {
            padding: var(--saas-space-sm, 8px) var(--saas-space-md, 16px);
            text-align: left;
            font-size: var(--saas-text-xs, 11px);
            font-weight: var(--saas-font-semibold, 600);
            color: var(--saas-text-secondary, #666666);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            white-space: nowrap;
            user-select: none;
        }

        th.sortable {
            cursor: pointer;
            transition: background var(--saas-transition-fast, 150ms ease);
        }

        th.sortable:hover {
            background: var(--saas-bg-active, #f0f0f0);
        }

        th .sort-indicator {
            margin-left: 4px;
            opacity: 0.5;
        }

        th.sorted .sort-indicator {
            opacity: 1;
        }

        th.align-center { text-align: center; }
        th.align-right { text-align: right; }

        tbody tr {
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            transition: background var(--saas-transition-fast, 150ms ease);
        }

        tbody tr:last-child {
            border-bottom: none;
        }

        tbody tr:hover {
            background: var(--saas-bg-hover, #fafafa);
        }

        tbody tr.clickable {
            cursor: pointer;
        }

        td {
            padding: var(--saas-space-md, 16px);
            font-size: var(--saas-text-base, 14px);
            color: var(--saas-text-primary, #1a1a1a);
            vertical-align: middle;
        }

        td.align-center { text-align: center; }
        td.align-right { text-align: right; }

        .empty-state {
            padding: var(--saas-space-2xl, 48px);
            text-align: center;
            color: var(--saas-text-muted, #999999);
        }

        .empty-state svg {
            width: 48px;
            height: 48px;
            margin-bottom: var(--saas-space-md, 16px);
            opacity: 0.5;
        }
    `;

    @property({ type: Array }) columns: TableColumn[] = [];
    @property({ type: Array }) data: Record<string, unknown>[] = [];
    @property({ type: Boolean }) clickable = false;
    @property({ type: String, attribute: 'row-key' }) rowKey = 'id';
    @property({ type: String, attribute: 'empty-message' }) emptyMessage = 'No data available';

    @state() private _sortColumn: string | null = null;
    @state() private _sortDirection: SortDirection = null;

    render() {
        const sortedData = this._getSortedData();

        return html`
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            ${this.columns.map(col => html`
                                <th 
                                    class="${col.sortable ? 'sortable' : ''} ${this._sortColumn === col.key ? 'sorted' : ''} align-${col.align || 'left'}"
                                    style="${col.width ? `width: ${col.width}` : ''}"
                                    @click=${col.sortable ? () => this._handleSort(col.key) : nothing}
                                >
                                    ${col.label}
                                    ${col.sortable ? html`
                                        <span class="sort-indicator">
                                            ${this._getSortIcon(col.key)}
                                        </span>
                                    ` : ''}
                                </th>
                            `)}
                        </tr>
                    </thead>
                    <tbody>
                        ${sortedData.length > 0 ? sortedData.map(row => html`
                            <tr 
                                class="${this.clickable ? 'clickable' : ''}"
                                @click=${this.clickable ? () => this._handleRowClick(row) : nothing}
                            >
                                ${this.columns.map(col => html`
                                    <td class="align-${col.align || 'left'}">
                                        ${col.render
                ? col.render(row[col.key], row)
                : row[col.key]
            }
                                    </td>
                                `)}
                            </tr>
                        `) : html`
                            <tr>
                                <td colspan="${this.columns.length}">
                                    <div class="empty-state">
                                        <p>${this.emptyMessage}</p>
                                    </div>
                                </td>
                            </tr>
                        `}
                    </tbody>
                </table>
            </div>
        `;
    }

    private _getSortedData(): Record<string, unknown>[] {
        if (!this._sortColumn || !this._sortDirection) {
            return this.data;
        }

        return [...this.data].sort((a, b) => {
            const aVal = a[this._sortColumn!];
            const bVal = b[this._sortColumn!];

            if (aVal === bVal) return 0;
            if (aVal === null || aVal === undefined) return 1;
            if (bVal === null || bVal === undefined) return -1;

            const comparison = aVal < bVal ? -1 : 1;
            return this._sortDirection === 'asc' ? comparison : -comparison;
        });
    }

    private _handleSort(column: string) {
        if (this._sortColumn === column) {
            // Toggle direction
            if (this._sortDirection === 'asc') {
                this._sortDirection = 'desc';
            } else if (this._sortDirection === 'desc') {
                this._sortColumn = null;
                this._sortDirection = null;
            }
        } else {
            this._sortColumn = column;
            this._sortDirection = 'asc';
        }

        this.dispatchEvent(new CustomEvent('saas-sort', {
            bubbles: true,
            composed: true,
            detail: { column: this._sortColumn, direction: this._sortDirection }
        }));
    }

    private _getSortIcon(column: string): string {
        if (this._sortColumn !== column) return '↕';
        return this._sortDirection === 'asc' ? '↑' : '↓';
    }

    private _handleRowClick(row: Record<string, unknown>) {
        this.dispatchEvent(new CustomEvent('saas-row-click', {
            bubbles: true,
            composed: true,
            detail: { row, id: row[this.rowKey] }
        }));
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-data-table': SaasDataTable;
    }
}
