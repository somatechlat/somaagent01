/**
 * SomaAgent — SAAS Super Admin Dashboard
 * THE EYE OF GOD — Platform Command Center
 *
 * VIBE COMPLIANT:
 * - Real Lit 3.x implementation
 * - Minimal white/black design per UI_STYLE_GUIDE.md
 * - NO EMOJIS - Google Material Symbols only
 * - Self-contained, no external dependencies
 *
 * This is the SaaS Platform Admin - where the SAAS Super Admin
 * sees EVERYTHING across the entire platform.
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import {
    PlatformDashboardController,
    DEFAULT_METRICS,
    type PlatformMetrics,
    type RecentEvent,
    type TopTenant,
    type PlatformDashboardHost,
} from '../controllers/platform-dashboard-controller.js';
import '../components/saas-platform-stats-grid.js';
import '../components/saas-platform-tenants-table.js';
import '../components/saas-platform-activity-feed.js';
import '../components/saas-platform-alerts-panel.js';

@customElement('saas-platform-dashboard')
export class SaasPlatformDashboard extends LitElement implements PlatformDashboardHost {
    static styles = css`
        :host {
            display: flex;
            height: 100vh;
            background: var(--saas-bg-page, #f5f5f5);
            font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
            color: var(--saas-text-primary, #1a1a1a);
        }

        * { box-sizing: border-box; }

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

        /* ========================================
           SIDEBAR — Minimal Navigation
           ======================================== */
        .sidebar {
            width: 260px;
            background: var(--saas-bg-card, #ffffff);
            border-right: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
        }

        .sidebar-header {
            padding: 24px 20px;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo-icon {
            width: 36px;
            height: 36px;
            background: #1a1a1a;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .logo-icon svg {
            width: 18px;
            height: 18px;
            stroke: white;
            fill: none;
        }

        .logo-text {
            font-size: 16px;
            font-weight: 600;
        }

        .logo-badge {
            font-size: 10px;
            padding: 2px 6px;
            background: #1a1a1a;
            color: white;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
            margin-left: 4px;
        }

        .nav {
            flex: 1;
            padding: 16px 12px;
            overflow-y: auto;
        }

        .nav-section { margin-bottom: 24px; }

        .nav-section-title {
            font-size: 10px;
            font-weight: 600;
            color: var(--saas-text-muted, #999);
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 0 12px;
            margin-bottom: 8px;
        }

        .nav-list {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 11px 14px;
            border-radius: 8px;
            font-size: 14px;
            color: var(--saas-text-secondary, #666);
            cursor: pointer;
            transition: all 0.1s ease;
            text-decoration: none;
        }

        .nav-item:hover {
            background: var(--saas-bg-hover, #fafafa);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .nav-item.active {
            background: var(--saas-bg-active, #f0f0f0);
            color: var(--saas-text-primary, #1a1a1a);
            font-weight: 500;
        }

        .nav-item .material-symbols-outlined { font-size: 18px; }

        .sidebar-footer {
            padding: 16px 20px;
            border-top: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .user-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: var(--saas-bg-hover, #fafafa);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 14px;
        }

        .user-details { flex: 1; min-width: 0; }
        .user-name { font-size: 13px; font-weight: 500; }
        .user-role { font-size: 11px; color: var(--saas-text-muted, #999); }

        .logout-btn {
            width: 32px;
            height: 32px;
            border-radius: 6px;
            border: none;
            background: transparent;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--saas-text-muted, #999);
        }

        .logout-btn:hover {
            background: var(--saas-bg-hover, #fafafa);
            color: var(--saas-text-primary, #1a1a1a);
        }

        /* ========================================
           MAIN CONTENT
           ======================================== */
        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .header {
            padding: 20px 32px;
            background: var(--saas-bg-card, #ffffff);
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .header-title {
            font-size: 22px;
            font-weight: 600;
        }

        .header-subtitle {
            font-size: 13px;
            color: var(--saas-text-muted, #999);
        }

        .header-actions {
            display: flex;
            gap: 12px;
        }

        .btn {
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.1s ease;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            background: var(--saas-bg-card, #ffffff);
            color: var(--saas-text-primary, #1a1a1a);
        }

        .btn:hover { background: var(--saas-bg-hover, #fafafa); }

        .btn.primary {
            background: #1a1a1a;
            color: white;
            border-color: #1a1a1a;
        }

        .btn.primary:hover { background: #333; }

        .btn .material-symbols-outlined { font-size: 16px; }

        .content {
            flex: 1;
            overflow-y: auto;
            padding: 32px;
        }

        .content-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 24px;
            margin-bottom: 24px;
        }

        @media (max-width: 1200px) {
            .content-grid { grid-template-columns: 1fr; }
        }

        .alerts-row {
            margin-top: 24px;
        }
    `;

    @state() metrics: PlatformMetrics = DEFAULT_METRICS;
    @state() topTenants: TopTenant[] = [];
    @state() recentEvents: RecentEvent[] = [];
    @state() loading = true;
    @state() error: string | null = null;
    @state() userName = '';
    @state() userRole = '';

    private controller = new PlatformDashboardController(this);

    connectedCallback() {
        super.connectedCallback();
        this.controller.connect();
    }

    render() {
        const alerts = this.recentEvents.filter(e => e.type === 'alert');

        return html`
            <!-- Sidebar -->
            <aside class="sidebar">
                <div class="sidebar-header">
                    <div class="logo">
                        <div class="logo-icon">
                            <svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <circle cx="12" cy="12" r="10"/>
                                <circle cx="12" cy="12" r="4"/>
                                <line x1="12" y1="2" x2="12" y2="6"/>
                                <line x1="12" y1="18" x2="12" y2="22"/>
                                <line x1="2" y1="12" x2="6" y2="12"/>
                                <line x1="18" y1="12" x2="22" y2="12"/>
                            </svg>
                        </div>
                        <span class="logo-text">SomaAgent<span class="logo-badge">God</span></span>
                    </div>
                </div>

                <nav class="nav">
                    <div class="nav-section">
                        <div class="nav-section-title">Overview</div>
                        <div class="nav-list">
                            <a class="nav-item active" href="/saas/dashboard">
                                <span class="material-symbols-outlined">visibility</span>
                                Dashboard
                            </a>
                            <a class="nav-item" href="/saas/tenants">
                                <span class="material-symbols-outlined">apartment</span>
                                Tenants
                            </a>
                        </div>
                    </div>

                    <div class="nav-section">
                        <div class="nav-section-title">Finance</div>
                        <div class="nav-list">
                            <a class="nav-item" href="/saas/subscriptions">
                                <span class="material-symbols-outlined">card_membership</span>
                                Subscriptions
                            </a>
                            <a class="nav-item" href="/saas/billing">
                                <span class="material-symbols-outlined">payments</span>
                                Billing
                            </a>
                        </div>
                    </div>

                    <div class="nav-section">
                        <div class="nav-section-title">Platform</div>
                        <div class="nav-list">
                            <a class="nav-item" href="/platform/models">
                                <span class="material-symbols-outlined">model_training</span>
                                Models
                            </a>
                            <a class="nav-item" href="/platform/roles">
                                <span class="material-symbols-outlined">admin_panel_settings</span>
                                Roles
                            </a>
                            <a class="nav-item" href="/platform/flags">
                                <span class="material-symbols-outlined">toggle_on</span>
                                Feature Flags
                            </a>
                            <a class="nav-item" href="/platform/api-keys">
                                <span class="material-symbols-outlined">vpn_key</span>
                                API Keys
                            </a>
                        </div>
                    </div>
                </nav>

                <div class="sidebar-footer">
                    <div class="user-info">
                        <div class="user-avatar">${this.controller.getInitials(this.userName)}</div>
                        <div class="user-details">
                            <div class="user-name">${this.userName}</div>
                            <div class="user-role">${this.userRole}</div>
                        </div>
                        <button class="logout-btn" @click=${() => this.controller.logout()}>
                            <span class="material-symbols-outlined">logout</span>
                        </button>
                    </div>
                </div>
            </aside>

            <!-- Main -->
            <main class="main">
                <header class="header">
                    <div class="header-left">
                        <div>
                            <h1 class="header-title">Platform Overview</h1>
                            <p class="header-subtitle">Real-time metrics across all tenants</p>
                        </div>
                    </div>
                    <div class="header-actions">
                        <button class="btn" @click=${() => window.location.href = '/saas/tenants'}>
                            <span class="material-symbols-outlined">apartment</span>
                            View Tenants
                        </button>
                        <button class="btn primary">
                            <span class="material-symbols-outlined">add</span>
                            New Tenant
                        </button>
                    </div>
                </header>

                <div class="content">
                    <saas-platform-stats-grid .metrics=${this.metrics}></saas-platform-stats-grid>

                    <div class="content-grid">
                        <saas-platform-tenants-table .tenants=${this.topTenants}></saas-platform-tenants-table>
                        <saas-platform-activity-feed .events=${this.recentEvents}></saas-platform-activity-feed>
                    </div>

                    <div class="alerts-row">
                        <saas-platform-alerts-panel
                            .activeAlerts=${this.metrics.activeAlerts}
                            .alerts=${alerts}
                        ></saas-platform-alerts-panel>
                    </div>
                </div>
            </main>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-platform-dashboard': SaasPlatformDashboard;
    }
}
