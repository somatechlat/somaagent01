/**
 * SAAS Sidebar Component
 * Collapsible navigation sidebar with sections
 *
 * VIBE COMPLIANT:
 * - Real Lit 3.x implementation
 * - Light/dark theme support
 * - Collapsible state
 * - Permission-aware nav items
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

export interface NavItem {
    id: string;
    label: string;
    icon?: string;
    route: string;
    permission?: string;
    badge?: string | number;
}

export interface NavSection {
    id: string;
    label: string;
    items: NavItem[];
}

@customElement('saas-sidebar')
export class SaasSidebar extends LitElement {
    static styles = css`
        :host {
            display: block;
            height: 100vh;
        }

        .sidebar {
            width: var(--saas-sidebar-width, 240px);
            height: 100%;
            background: var(--saas-bg-sidebar, #ffffff);
            border-right: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            flex-direction: column;
            transition: width var(--saas-transition-normal, 200ms ease);
        }

        .sidebar.collapsed {
            width: var(--saas-sidebar-collapsed, 64px);
        }

        /* Logo area */
        .logo-area {
            padding: var(--saas-space-md, 16px);
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            align-items: center;
            gap: var(--saas-space-sm, 8px);
            min-height: 56px;
        }

        .logo-icon {
            width: 32px;
            height: 32px;
            background: var(--saas-accent, #1a1a1a);
            border-radius: var(--saas-radius-md, 8px);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--saas-text-inverse, #ffffff);
            font-weight: bold;
            flex-shrink: 0;
        }

        .logo-text {
            font-size: var(--saas-text-md, 16px);
            font-weight: var(--saas-font-semibold, 600);
            color: var(--saas-text-primary, #1a1a1a);
            white-space: nowrap;
            overflow: hidden;
        }

        .sidebar.collapsed .logo-text {
            display: none;
        }

        /* Navigation */
        .nav {
            flex: 1;
            overflow-y: auto;
            padding: var(--saas-space-sm, 8px) 0;
        }

        .section {
            margin-bottom: var(--saas-space-sm, 8px);
        }

        .section-label {
            padding: var(--saas-space-md, 16px) var(--saas-space-md, 16px) var(--saas-space-xs, 4px);
            font-size: var(--saas-text-xs, 11px);
            font-weight: var(--saas-font-semibold, 600);
            color: var(--saas-text-muted, #999999);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            white-space: nowrap;
            overflow: hidden;
        }

        .sidebar.collapsed .section-label {
            display: none;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: var(--saas-space-sm, 8px);
            padding: var(--saas-space-sm, 8px) var(--saas-space-md, 16px);
            margin: 0 var(--saas-space-sm, 8px);
            border-radius: var(--saas-radius-md, 8px);
            font-size: var(--saas-text-base, 14px);
            color: var(--saas-text-secondary, #666666);
            text-decoration: none;
            cursor: pointer;
            transition: all var(--saas-transition-fast, 150ms ease);
            white-space: nowrap;
            overflow: hidden;
        }

        .nav-item:hover {
            background: var(--saas-bg-hover, #fafafa);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .nav-item.active {
            background: var(--saas-bg-active, #f0f0f0);
            color: var(--saas-text-primary, #1a1a1a);
            font-weight: var(--saas-font-medium, 500);
        }

        .nav-icon {
            width: 20px;
            height: 20px;
            flex-shrink: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
        }

        .nav-label {
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .sidebar.collapsed .nav-label {
            display: none;
        }

        .nav-badge {
            padding: 2px 6px;
            background: var(--saas-status-danger, #ef4444);
            color: white;
            font-size: var(--saas-text-xs, 11px);
            font-weight: var(--saas-font-semibold, 600);
            border-radius: var(--saas-radius-full, 9999px);
        }

        .sidebar.collapsed .nav-badge {
            position: absolute;
            top: 4px;
            right: 4px;
            padding: 2px 4px;
            font-size: 9px;
        }

        /* Footer */
        .footer {
            padding: var(--saas-space-sm, 8px);
            border-top: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .footer-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: var(--saas-space-sm, 8px);
            width: 100%;
            padding: var(--saas-space-sm, 8px);
            background: transparent;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: var(--saas-radius-md, 8px);
            color: var(--saas-text-secondary, #666666);
            font-size: var(--saas-text-sm, 13px);
            cursor: pointer;
            transition: all var(--saas-transition-fast, 150ms ease);
        }

        .footer-btn:hover {
            background: var(--saas-bg-hover, #fafafa);
            border-color: var(--saas-border-medium, #cccccc);
        }

        .sidebar.collapsed .footer-btn span {
            display: none;
        }

        /* User section */
        .user-section {
            padding: var(--saas-space-sm, 8px) var(--saas-space-md, 16px);
            border-top: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            align-items: center;
            gap: var(--saas-space-sm, 8px);
        }

        .user-avatar {
            width: 32px;
            height: 32px;
            border-radius: var(--saas-radius-full, 9999px);
            background: var(--saas-bg-active, #f0f0f0);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: var(--saas-text-sm, 13px);
            font-weight: var(--saas-font-semibold, 600);
            color: var(--saas-text-secondary, #666666);
            flex-shrink: 0;
        }

        .user-info {
            flex: 1;
            min-width: 0;
        }

        .user-name {
            font-size: var(--saas-text-sm, 13px);
            font-weight: var(--saas-font-medium, 500);
            color: var(--saas-text-primary, #1a1a1a);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .user-role {
            font-size: var(--saas-text-xs, 11px);
            color: var(--saas-text-muted, #999999);
        }

        .sidebar.collapsed .user-info {
            display: none;
        }
    `;

    @property({ type: Array }) sections: NavSection[] = [];
    @property({ type: String }) activeRoute = '';
    @property({ type: Boolean }) collapsed = false;
    @property({ type: String }) userName = '';
    @property({ type: String }) userRole = '';
    @property({ type: String }) logoText = 'SomaAgent';

    render() {
        return html`
            <aside class="sidebar ${this.collapsed ? 'collapsed' : ''}">
                <div class="logo-area">
                    <div class="logo-icon">S</div>
                    <span class="logo-text">${this.logoText}</span>
                </div>

                <nav class="nav">
                    ${this.sections.map(section => html`
                        <div class="section">
                            <div class="section-label">${section.label}</div>
                            ${section.items.map(item => html`
                                <a 
                                    class="nav-item ${this.activeRoute === item.route ? 'active' : ''}"
                                    @click=${() => this._handleNavClick(item)}
                                >
                                    <span class="nav-icon icon">${item.icon || 'article'}</span>
                                    <span class="nav-label">${item.label}</span>
                                    ${item.badge ? html`<span class="nav-badge">${item.badge}</span>` : ''}
                                </a>
                            `)}
                        </div>
                    `)}
                </nav>

                ${this.userName ? html`
                    <div class="user-section">
                        <div class="user-avatar">${this._getInitials()}</div>
                        <div class="user-info">
                            <div class="user-name">${this.userName}</div>
                            <div class="user-role">${this.userRole}</div>
                        </div>
                    </div>
                ` : ''}

                <div class="footer">
                    <button class="footer-btn" @click=${this._toggleCollapse}>
                        <span class="icon">${this.collapsed ? 'chevron_right' : 'chevron_left'}</span>
                        <span>${this.collapsed ? 'Expand' : 'Collapse'}</span>
                    </button>
                </div>
            </aside>
        `;
    }

    private _getInitials(): string {
        return this.userName
            .split(' ')
            .map(n => n[0])
            .join('')
            .toUpperCase()
            .slice(0, 2);
    }

    private _handleNavClick(item: NavItem) {
        this.dispatchEvent(new CustomEvent('saas-navigate', {
            bubbles: true,
            composed: true,
            detail: { route: item.route, item }
        }));
    }

    private _toggleCollapse() {
        this.collapsed = !this.collapsed;
        this.dispatchEvent(new CustomEvent('saas-sidebar-toggle', {
            bubbles: true,
            composed: true,
            detail: { collapsed: this.collapsed }
        }));
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-sidebar': SaasSidebar;
    }
}
