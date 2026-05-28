/**
 * SomaAgent01 — Workspace Sidebar
 * Navigation, agent list, activity feed
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { activityStore } from '../stores/activity-store.js';

interface NavItem {
    icon: string;
    label: string;
    route: string;
}

const NAV_ITEMS: NavItem[] = [
    { icon: '◆', label: 'Workspace', route: '/workspace' },
    { icon: '🤖', label: 'Agents', route: '/admin/agents' },
    { icon: '🧠', label: 'Memory', route: '/memory' },
    { icon: '💊', label: 'Capsules', route: '/workspace?tab=capsule' },
    { icon: '🎨', label: 'Skins', route: '/themes' },
    { icon: '⚙', label: 'Settings', route: '/settings' },
];

@customElement('saas-sidebar-workspace')
export class SaasSidebarWorkspace extends LitElement {
    @state() private _activeRoute = '/workspace';
    @state() private _events = activityStore.state.events;

    static styles = css`
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

    render() {
        return html`
            <div class="brand">
                <div class="brand-icon">◆</div>
                <div class="brand-name">SomaAgent</div>
                <div class="brand-version">01</div>
            </div>

            <div class="nav-section">
                ${NAV_ITEMS.map(item => html`
                    <div 
                        class="nav-item ${this._activeRoute === item.route ? 'active' : ''}"
                        @click=${() => this._navigate(item.route)}
                    >
                        <span class="nav-icon">${item.icon}</span>
                        <span>${item.label}</span>
                    </div>
                `)}
            </div>

            <div class="section-title">Agents</div>
            <div class="agent-list">
                <div class="agent-item">
                    <span class="agent-dot active"></span>
                    <span>Dev-1</span>
                </div>
                <div class="agent-item">
                    <span class="agent-dot active"></span>
                    <span>Support-AI</span>
                </div>
                <div class="agent-item">
                    <span class="agent-dot paused"></span>
                    <span>Researcher</span>
                </div>
            </div>

            <div class="section-title">Activity</div>
            <div class="activity-feed">
                ${this._events.map(e => html`
                    <div class="activity-item">
                        <span class="activity-icon">
                            ${e.type === 'tool' ? '⚡' : e.type === 'memory' ? '🧠' : e.type === 'error' ? '❌' : e.type === 'warning' ? '⚠️' : '💬'}
                        </span>
                        <div>
                            <div class="activity-text">${e.description}</div>
                            <div class="activity-time">${this._formatTime(e.timestamp)}</div>
                        </div>
                    </div>
                `)}
            </div>

            <div class="user-section">
                <div class="user-avatar">👤</div>
                <div class="user-meta">
                    <div class="user-name">Admin</div>
                    <div class="user-role">SaaS Admin</div>
                </div>
                <div class="user-actions">
                    <button class="user-action-btn" title="Theme" @click=${() => document.documentElement.toggleAttribute('data-theme-light')}>
                        ◐
                    </button>
                    <button class="user-action-btn" title="Logout" @click=${() => this._navigate('/logout')}>
                        →
                    </button>
                </div>
            </div>
        `;
    }
}
