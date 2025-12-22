/**
 * Eye of God App Shell
 * Per Eye of God UIX Design Section 2.2
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - Vaadin Router integration
 * - Responsive sidebar navigation
 */

import './components/eog-tenant-switcher.js';

// ... (rest of imports)

@customElement('eog-app')
// ... (class definition)

// Inside render():

<div class="topbar-actions" >
    ${ isPlatformAdmin ? html`<eog-tenant-switcher></eog-tenant-switcher>` : '' }
<eog-voice - button > </eog-voice-button>
    < div class="user-avatar" @click=${ this._logout }> ${ this._userInitials } </div>
        </div>

interface NavItem {
    path: string;
    label: string;
    icon: string;
    roles?: string[];
}

@customElement('eog-app')
export class EogApp extends LitElement {
    static styles = css`
        :host {
            display: flex;
            height: 100vh;
            background: var(--eog-bg-void, #0f172a);
            color: var(--eog-text-main, #e2e8f0);
        }

        .sidebar {
            width: 240px;
            min-width: 240px;
            background: var(--eog-surface, rgba(30, 41, 59, 0.85));
            border-right: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.05));
            display: flex;
            flex-direction: column;
            transition: transform 0.3s ease;
        }

        .sidebar.collapsed {
            transform: translateX(-240px);
            margin-left: -240px;
        }

        .sidebar-header {
            padding: var(--eog-spacing-lg, 24px);
            border-bottom: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.05));
        }

        .logo {
            display: flex;
            align-items: center;
            gap: var(--eog-spacing-sm, 8px);
            font-size: var(--eog-text-lg, 16px);
            font-weight: 700;
            color: var(--eog-text-main, #e2e8f0);
        }

        .logo-icon {
            font-size: 24px;
        }

        nav {
            flex: 1;
            padding: var(--eog-spacing-md, 16px);
            overflow-y: auto;
        }

        .nav-section {
            margin-bottom: var(--eog-spacing-lg, 24px);
        }

        .nav-section-title {
            font-size: var(--eog-text-xs, 11px);
            font-weight: 600;
            text-transform: uppercase;
            color: var(--eog-text-dim, #64748b);
            margin-bottom: var(--eog-spacing-sm, 8px);
            padding: 0 var(--eog-spacing-sm, 8px);
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: var(--eog-spacing-sm, 8px);
            padding: var(--eog-spacing-sm, 8px) var(--eog-spacing-md, 16px);
            border-radius: var(--eog-radius-md, 8px);
            color: var(--eog-text-dim, #64748b);
            text-decoration: none;
            transition: all 0.2s ease;
            cursor: pointer;
        }

        .nav-item:hover {
            background: rgba(255, 255, 255, 0.05);
            color: var(--eog-text-main, #e2e8f0);
        }

        .nav-item.active {
            background: rgba(148, 163, 184, 0.15);
            color: var(--eog-accent, #94a3b8);
        }

        .nav-icon {
            font-size: 18px;
        }

        .sidebar-footer {
            padding: var(--eog-spacing-md, 16px);
            border-top: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.05));
        }

        .mode-indicator {
            display: flex;
            align-items: center;
            gap: var(--eog-spacing-sm, 8px);
            padding: var(--eog-spacing-sm, 8px);
            border-radius: var(--eog-radius-md, 8px);
            background: rgba(255, 255, 255, 0.03);
            font-size: var(--eog-text-sm, 13px);
        }

        .mode-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--eog-success, #22c55e);
        }

        .mode-dot.danger {
            background: var(--eog-danger, #ef4444);
        }

        .mode-dot.training {
            background: var(--eog-warning, #f59e0b);
        }

        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .topbar {
            height: 56px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 var(--eog-spacing-lg, 24px);
            border-bottom: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.05));
            background: var(--eog-surface, rgba(30, 41, 59, 0.85));
        }

        .menu-toggle {
            background: none;
            border: none;
            color: var(--eog-text-main, #e2e8f0);
            font-size: 20px;
            cursor: pointer;
            padding: var(--eog-spacing-xs, 4px);
        }

        .topbar-actions {
            display: flex;
            align-items: center;
            gap: var(--eog-spacing-md, 16px);
        }

        .user-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: var(--eog-accent, #94a3b8);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: var(--eog-text-sm, 13px);
            cursor: pointer;
        }

        .content {
            flex: 1;
            overflow-y: auto;
            background: var(--eog-bg-base, #1e293b);
        }

        @media (max-width: 768px) {
            .sidebar {
                position: fixed;
                z-index: 100;
                height: 100vh;
            }

            .sidebar.collapsed {
                transform: translateX(-240px);
                margin-left: 0;
            }
        }
    `;

    @consume({ context: modeContext, subscribe: true })
    @property({ attribute: false })
    modeState?: ModeState;

    @state() private _sidebarCollapsed = false;
    @state() private _currentPath = '/';
    @state() private _userInitials = 'SA';

    private _mainNav: NavItem[] = [
        { path: '/chat', label: 'Chat', icon: '💬' },
        { path: '/memory', label: 'Memory', icon: '🧠' },
        { path: '/tools', label: 'Tools', icon: '🔧' },
        { path: '/cognitive', label: 'Cognitive', icon: '⚙️' },
    ];

    // Platform nav (God Mode only)
    private _platformNav: NavItem[] = [
        { path: '/platform', label: 'Dashboard', icon: '📊', roles: ['saas_admin'] },
        { path: '/platform/tenants', label: 'Tenants', icon: '🏢', roles: ['saas_admin'] },
        { path: '/platform/billing', label: 'Billing', icon: '💰', roles: ['saas_admin'] },
    ];

    private _settingsNav: NavItem[] = [
        { path: '/settings', label: 'Settings', icon: '⚙️' },
        { path: '/themes', label: 'Themes', icon: '🎨' },
    ];

    private _adminNav: NavItem[] = [
        { path: '/admin', label: 'Admin', icon: '🛡️', roles: ['admin', 'sysadmin'] },
        { path: '/audit', label: 'Audit Logs', icon: '📋', roles: ['admin', 'sysadmin'] },
    ];

    render() {
        const mode = this.modeState?.current || 'STD';
        const modeLabel = this._getModeLabel(mode);
        const modeClass = mode === 'DGR' ? 'danger' : mode === 'TRN' ? 'training' : '';
        const isPlatformAdmin = this._checkRole('saas_admin');

        return html`
            <aside class="sidebar ${this._sidebarCollapsed ? 'collapsed' : ''}">
                <header class="sidebar-header">
                    <div class="logo">
                        <span class="logo-icon">👁️</span>
                        <span>Eye of God</span>
                    </div>
                </header>

                <nav>
                    <div class="nav-section">
                        <div class="nav-section-title">Main</div>
                        ${this._mainNav.map(item => this._renderNavItem(item))}
                    </div>

                    ${isPlatformAdmin ? html`
                        <div class="nav-section">
                            <div class="nav-section-title">🔮 Platform</div>
                            ${this._platformNav.map(item => this._renderNavItem(item))}
                        </div>
                    ` : ''}

                    <div class="nav-section">
                        <div class="nav-section-title">Settings</div>
                        ${this._settingsNav.map(item => this._renderNavItem(item))}
                    </div>

                    <div class="nav-section">
                        <div class="nav-section-title">Admin</div>
                        ${this._adminNav.map(item => this._renderNavItem(item))}
                    </div>
                </nav>

                <footer class="sidebar-footer">
                    <div class="mode-indicator">
                        <span class="mode-dot ${modeClass}"></span>
                        <span>Mode: ${modeLabel}</span>
                    </div>
                </footer>
            </aside>

            <main class="main">
                <header class="topbar">
                    <button class="menu-toggle" @click=${this._toggleSidebar}>
                        ☰
                    </button>
                    <div class="topbar-actions">
                        <eog-voice-button></eog-voice-button>
                        <div class="user-avatar" @click=${this._logout}>${this._userInitials}</div>
                    </div>
                </header>

                <div class="content" id="outlet">
                    <!-- Router outlet -->
                </div>
            </main>
        `;
    }

    private _renderNavItem(item: NavItem) {
        const isActive = this._currentPath === item.path || this._currentPath.startsWith(item.path + '/');

        return html`
            <a
                class="nav-item ${isActive ? 'active' : ''}"
                href=${item.path}
                @click=${(e: Event) => this._navigate(e, item.path)}
            >
                <span class="nav-icon">${item.icon}</span>
                <span>${item.label}</span>
            </a>
        `;
    }

    private _toggleSidebar() {
        this._sidebarCollapsed = !this._sidebarCollapsed;
    }

    private _navigate(e: Event, path: string) {
        e.preventDefault();
        this._currentPath = path;
        Router.go(path);
    }

    private _getModeLabel(mode: string): string {
        const labels: Record<string, string> = {
            STD: 'Standard',
            TRN: 'Training',
            ADM: 'Admin',
            DEV: 'Developer',
            RO: 'Read Only',
            DGR: 'DANGER',
        };
        return labels[mode] || mode;
    }

    private _checkRole(role: string): boolean {
        // Check user role from localStorage
        try {
            const user = JSON.parse(localStorage.getItem('eog_user') || '{}');
            const roles = user.roles || [];
            return roles.includes(role) || roles.includes('saas_admin');
        } catch {
            return false;
        }
    }

    private _logout() {
        localStorage.removeItem('eog_auth_token');
        localStorage.removeItem('eog_user');
        window.location.href = '/login';
    }

    private _isAuthenticated(): boolean {
        return !!localStorage.getItem('eog_auth_token');
    }

    firstUpdated() {
        // Check authentication
        if (!this._isAuthenticated()) {
            window.location.href = '/login';
            return;
        }

        // Load user info
        try {
            const user = JSON.parse(localStorage.getItem('eog_user') || '{}');
            if (user.name) {
                this._userInitials = user.name.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2);
            }
        } catch {
            // Ignore
        }

        // Initialize router
        const outlet = this.shadowRoot?.getElementById('outlet');
        if (outlet) {
            const router = new Router(outlet);
            router.setRoutes([
                { path: '/', redirect: '/chat' },
                { path: '/chat', component: 'eog-chat' },
                { path: '/memory', component: 'eog-memory' },
                { path: '/tools', component: 'eog-tools' },
                { path: '/cognitive', component: 'eog-cognitive' },
                { path: '/settings', component: 'eog-settings' },
                { path: '/themes', component: 'eog-themes' },
                { path: '/admin', component: 'eog-admin' },
                // Platform routes (God Mode)
                { path: '/platform', component: 'eog-platform-dashboard' },
                { path: '/platform/tenants', component: 'eog-tenants' },
                { path: '(.*)', redirect: '/chat' },
            ]);
        }

        // Set current path
        this._currentPath = window.location.pathname;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-app': EogApp;
    }
}
