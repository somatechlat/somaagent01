/**
 * SomaAgent01 — Workspace Sidebar
 * Navigation, agent list, activity feed
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import { activityStore } from '../stores/activity-store.js';

interface NavItem {
    icon: string;
    label: string;
    route: string;
}

const NAV_ITEMS: NavItem[] = [
    { icon: 'diamond', label: 'Workspace', route: '/workspace' },
    { icon: 'smart_toy', label: 'Agents', route: '/admin/agents' },
    { icon: 'neurology', label: 'Memory', route: '/memory' },
    { icon: 'medication', label: 'Capsules', route: '/workspace?tab=capsule' },
    { icon: 'settings', label: 'Settings', route: '/settings' },
];

@customElement('saas-sidebar-workspace')
export class SaasSidebarWorkspace extends LitElement {
    @state() private _activeRoute = '/workspace';
    @state() private _events = activityStore.state.events;
    @state() private _agents: { id: string; name: string; statusClass: string }[] = [];
    @state() private _userName = '';
    @state() private _userRole = '';

    static styles = css`
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
        :host {
            display: flex;
            flex-direction: column;
            width: 260px;
            flex-shrink: 0;
            background: var(--aaas-bg-sidebar, #0a0a0a);
            border-right: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            height: 100%;
        }

        .brand {
            padding: 16px 20px;
            display: flex;
            align-items: center;
            gap: 10px;
            border-bottom: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
        }

        .brand-icon {
            width: 28px;
            height: 28px;
            background: linear-gradient(135deg, var(--aaas-accent, #e8e4dc), var(--aaas-text-muted, #6b6b6b));
            border-radius: var(--aaas-radius-md, 8px);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
        }

        .brand-name {
            font-size: 15px;
            font-weight: 700;
            color: var(--aaas-text-primary, #ffffff);
            letter-spacing: -0.3px;
        }

        .brand-version {
            font-size: 10px;
            color: var(--aaas-text-muted, #6b6b6b);
            margin-left: auto;
            padding: 2px 6px;
            background: var(--aaas-bg-hover, #141414);
            border-radius: var(--aaas-radius-sm, 4px);
        }

        .nav-section {
            padding: 8px 12px;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 9px 14px;
            border-radius: var(--aaas-radius-md, 8px);
            cursor: pointer;
            font-size: 13px;
            color: var(--aaas-text-secondary, #a1a1a1);
            transition: all 150ms ease;
            text-decoration: none;
        }

        .nav-item:hover {
            background: var(--aaas-bg-hover, #141414);
            color: var(--aaas-text-primary, #ffffff);
        }

        .nav-item.active {
            background: var(--aaas-bg-active, #1a1a1a);
            color: var(--aaas-accent, #e8e4dc);
            position: relative;
        }

        .nav-item.active::before {
            content: '';
            position: absolute;
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            width: 3px;
            height: 18px;
            background: var(--aaas-accent, #e8e4dc);
            border-radius: 0 2px 2px 0;
        }

        .nav-icon {
            font-size: 16px;
            width: 20px;
            text-align: center;
        }

        .section-title {
            padding: 16px 20px 8px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--aaas-text-muted, #6b6b6b);
        }

        .agent-list {
            padding: 0 12px;
        }

        .agent-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 14px;
            border-radius: var(--aaas-radius-md, 8px);
            cursor: pointer;
            font-size: 13px;
            color: var(--aaas-text-secondary, #a1a1a1);
            transition: all 150ms ease;
        }

        .agent-item:hover {
            background: var(--aaas-bg-hover, #141414);
            color: var(--aaas-text-primary, #ffffff);
        }

        .agent-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            flex-shrink: 0;
        }

        .agent-dot.active { background: var(--aaas-success, #22c55e); }
        .agent-dot.paused { background: var(--aaas-warning, #f59e0b); }
        .agent-dot.error { background: var(--aaas-danger, #ef4444); }

        .activity-feed {
            flex: 1;
            min-height: 0;
            overflow-y: auto;
            padding: 0 12px;
        }

        .activity-item {
            display: flex;
            gap: 10px;
            padding: 8px 10px;
            border-radius: var(--aaas-radius-md, 8px);
            font-size: 12px;
            color: var(--aaas-text-secondary, #a1a1a1);
            transition: background 150ms ease;
        }

        .activity-item:hover {
            background: var(--aaas-bg-hover, #141414);
        }

        .activity-icon {
            font-size: 14px;
            flex-shrink: 0;
            margin-top: 1px;
        }

        .activity-text {
            line-height: 1.4;
        }

        .activity-time {
            font-size: 11px;
            color: var(--aaas-text-muted, #6b6b6b);
            margin-top: 2px;
        }

        .user-section {
            padding: 12px 16px;
            border-top: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .user-avatar {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--aaas-accent, #e8e4dc), var(--aaas-text-muted, #6b6b6b));
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            flex-shrink: 0;
        }

        .user-meta {
            flex: 1;
            min-width: 0;
        }

        .user-name {
            font-size: 13px;
            font-weight: 500;
            color: var(--aaas-text-primary, #ffffff);
        }

        .user-role {
            font-size: 11px;
            color: var(--aaas-text-muted, #6b6b6b);
        }

        .user-actions {
            display: flex;
            gap: 4px;
        }

        .user-action-btn {
            width: 28px;
            height: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: var(--aaas-radius-sm, 4px);
            background: transparent;
            border: none;
            color: var(--aaas-text-muted, #6b6b6b);
            cursor: pointer;
            font-size: 14px;
            transition: all 150ms ease;
        }

        .user-action-btn:hover {
            background: var(--aaas-bg-hover, #141414);
            color: var(--aaas-text-secondary, #a1a1a1);
        }
    `;

    connectedCallback() {
        super.connectedCallback();
        activityStore.subscribe(() => {
            this._events = activityStore.state.events;
        });
        this._loadAgents();
        this._loadUser();
    }

    private _navigate(route: string) {
        this._activeRoute = route;
        window.dispatchEvent(new CustomEvent('saas-navigate', { detail: { route } }));
    }

    private _formatTime(timestamp: string): string {
        const diff = Date.now() - new Date(timestamp).getTime();
        const minutes = Math.floor(diff / 60000);
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}h ago`;
        return `${Math.floor(hours / 24)}d ago`;
    }

    private async _loadAgents() {
        try {
            const data = await apiClient.get<{ data?: Array<{ id: string; name: string; status?: string }> }>('/aaas/admin/agents');
            this._agents = (data.data || []).map(a => ({
                id: a.id,
                name: a.name,
                statusClass: this._statusClass(a.status),
            }));
        } catch (error) {
            console.error('[SaasSidebarWorkspace] Failed to load agents:', error);
            this._agents = [];
        }
    }

    private _statusClass(status?: string): string {
        if (status === 'active') return 'active';
        if (status === 'paused') return 'paused';
        if (status === 'error') return 'error';
        return '';
    }

    private async _loadUser() {
        try {
            const userStr = sessionStorage.getItem('saas_user');
            if (userStr) {
                const user = JSON.parse(userStr);
                this._userName = user.name || '';
                this._userRole = user.role || '';
                return;
            }
            const user = await apiClient.get<{ name?: string; role?: string }>('/auth/me');
            this._userName = user?.name || '';
            this._userRole = user?.role || '';
        } catch (error) {
            console.error('[SaasSidebarWorkspace] Failed to load user:', error);
        }
    }

    private _getInitials(name: string): string {
        return name
            .split(' ')
            .map(part => part[0])
            .join('')
            .slice(0, 2)
            .toUpperCase();
    }

    render() {
        return html`
            <div class="brand">
                <div class="brand-icon"><span class="material-symbols-outlined">diamond</span></div>
                <div class="brand-name">SomaAgent</div>
                <div class="brand-version">01</div>
            </div>

            <div class="nav-section">
                ${NAV_ITEMS.map(item => html`
                    <div 
                        class="nav-item ${this._activeRoute === item.route ? 'active' : ''}"
                        @click=${() => this._navigate(item.route)}
                    >
                        <span class="nav-icon material-symbols-outlined">${item.icon}</span>
                        <span>${item.label}</span>
                    </div>
                `)}
            </div>

            <div class="section-title">Agents</div>
            <div class="agent-list">
                ${this._agents.map(agent => html`
                    <div class="agent-item">
                        <span class="agent-dot ${agent.statusClass}"></span>
                        <span>${agent.name}</span>
                    </div>
                `)}
            </div>

            <div class="section-title">Activity</div>
            <div class="activity-feed">
                ${this._events.map(e => html`
                    <div class="activity-item">
                        <span class="activity-icon">
                            ${e.type === 'tool' ? html`<span class='material-symbols-outlined'>bolt</span>` : e.type === 'memory' ? html`<span class='material-symbols-outlined'>neurology</span>` : e.type === 'error' ? html`<span class='material-symbols-outlined'>cancel</span>` : e.type === 'warning' ? html`<span class='material-symbols-outlined'>warning</span>` : html`<span class='material-symbols-outlined'>chat</span>`}
                        </span>
                        <div>
                            <div class="activity-text">${e.description}</div>
                            <div class="activity-time">${this._formatTime(e.timestamp)}</div>
                        </div>
                    </div>
                `)}
            </div>

            <div class="user-section">
                <div class="user-avatar">${this._getInitials(this._userName)}</div>
                <div class="user-meta">
                    <div class="user-name">${this._userName}</div>
                    <div class="user-role">${this._userRole}</div>
                </div>
                <div class="user-actions">
                    <button class="user-action-btn" title="Theme" @click=${() => document.documentElement.toggleAttribute('data-theme-light')}>
                        <span class="material-symbols-outlined">contrast</span>
                    </button>
                    <button class="user-action-btn" title="Logout" @click=${() => this._navigate('/logout')}>
                        <span class="material-symbols-outlined">logout</span>
                    </button>
                </div>
            </div>
        `;
    }
}
