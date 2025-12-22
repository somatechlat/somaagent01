/**
 * Eye of God Tenant Switcher
 * Feature for God Mode users to switch context.
 */

import { LitElement, html, css } from 'lit';
import { customElement, state, property } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';

interface TenantSimple {
    id: string;
    name: string;
    slug: string;
}

@customElement('eog-tenant-switcher')
export class EogTenantSwitcher extends LitElement {
    static styles = css`
        :host {
            position: relative;
            display: inline-block;
        }

        .trigger {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            color: var(--eog-text-main, #e2e8f0);
            font-size: 13px;
        }

        .trigger:hover, .trigger.active {
            background: rgba(255, 255, 255, 0.1);
            border-color: rgba(255, 255, 255, 0.2);
        }

        .icon {
            font-size: 14px;
            color: var(--eog-text-dim, #64748b);
        }

        .dropdown {
            position: absolute;
            top: calc(100% + 8px);
            right: 0;
            width: 280px;
            background: #1e293b;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
            padding: 8px;
            z-index: 1000;
            display: none;
            flex-direction: column;
            gap: 4px;
        }

        .dropdown.open {
            display: flex;
            animation: slideDown 0.2s ease-out;
        }

        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .search-box {
            padding: 8px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            margin-bottom: 4px;
        }

        .search-input {
            width: 100%;
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            padding: 8px 12px;
            color: white;
            font-size: 12px;
            box-sizing: border-box;
        }

        .search-input:focus {
            outline: none;
            border-color: #3b82f6;
        }

        .tenant-list {
            max-height: 200px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .tenant-item {
            padding: 8px 12px;
            display: flex;
            align-items: center;
            gap: 12px;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.2s;
            color: #94a3b8;
        }

        .tenant-item:hover {
            background: rgba(255, 255, 255, 0.05);
            color: white;
        }

        .tenant-item.selected {
            background: rgba(59, 130, 246, 0.1);
            color: #60a5fa;
        }

        .tenant-initial {
            width: 24px;
            height: 24px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            font-weight: 700;
        }

        .header-label {
            font-size: 11px;
            text-transform: uppercase;
            color: #64748b;
            padding: 8px;
            font-weight: 600;
        }

        /* Scrollbar */
        .tenant-list::-webkit-scrollbar {
            width: 4px;
        }
        .tenant-list::-webkit-scrollbar-track {
            background: transparent;
        }
        .tenant-list::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }
    `;

    @state() private _isOpen = false;
    @state() private _tenants: TenantSimple[] = [];
    @state() private _currentTenant: TenantSimple | null = null;
    @state() private _filter = '';

    connectedCallback() {
        super.connectedCallback();
        this._loadTenants();
        this._loadCurrentTenant();

        // Close on click outside
        document.addEventListener('click', this._handleClickOutside);
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        document.removeEventListener('click', this._handleClickOutside);
    }

    private _handleClickOutside = (e: MouseEvent) => {
        if (!this.shadowRoot?.contains(e.target as Node)) {
            this._isOpen = false;
        }
    };

    private async _loadTenants() {
        try {
            const response = await apiClient.get<{ tenants: TenantSimple[] }>('/saas/tenants');
            this._tenants = response.tenants;
        } catch (e) {
            console.error('Failed to load tenants for switcher', e);
        }
    }

    private _loadCurrentTenant() {
        const stored = localStorage.getItem('eog_current_tenant');
        if (stored) {
            this._currentTenant = JSON.parse(stored);
        }
    }

    private _toggle(e: Event) {
        e.stopPropagation();
        this._isOpen = !this._isOpen;
    }

    private _selectTenant(tenant: TenantSimple | null) {
        if (tenant) {
            this._currentTenant = tenant;
            localStorage.setItem('eog_current_tenant', JSON.stringify(tenant));
            // Trigger app reload or event
            window.location.reload();
        } else {
            // "Platform" context
            this._currentTenant = null;
            localStorage.removeItem('eog_current_tenant');
            window.location.href = '/platform';
        }
        this._isOpen = false;
    }

    render() {
        const filteredTenants = this._tenants.filter(t =>
            t.name.toLowerCase().includes(this._filter.toLowerCase())
        );

        return html`
            <div class="trigger ${this._isOpen ? 'active' : ''}" @click=${this._toggle}>
                <span class="icon">🏢</span>
                <span>${this._currentTenant ? this._currentTenant.name : 'Platform Context'}</span>
                <span class="icon" style="font-size: 10px; margin-left: auto;">▼</span>
            </div>

            <div class="dropdown ${this._isOpen ? 'open' : ''}" @click=${(e: Event) => e.stopPropagation()}>
                <div class="header-label">Switch Context</div>
                
                <div class="search-box">
                    <input 
                        class="search-input" 
                        type="text" 
                        placeholder="Find tenant..."
                        .value=${this._filter}
                        @input=${(e: any) => this._filter = e.target.value}
                    >
                </div>

                <div class="tenant-list">
                    <div 
                        class="tenant-item ${!this._currentTenant ? 'selected' : ''}"
                        @click=${() => this._selectTenant(null)}
                    >
                        <div class="tenant-initial">⚡</div>
                        <span>Platform (Global)</span>
                    </div>

                    ${filteredTenants.map(tenant => html`
                        <div 
                            class="tenant-item ${this._currentTenant?.id === tenant.id ? 'selected' : ''}"
                            @click=${() => this._selectTenant(tenant)}
                        >
                            <div class="tenant-initial">${tenant.name[0]}</div>
                            <span>${tenant.name}</span>
                        </div>
                    `)}
                </div>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-tenant-switcher': EogTenantSwitcher;
    }
}
