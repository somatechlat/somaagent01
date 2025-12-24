/**
 * Eye of God - Mode Selection Screen
 * For "God Mode" users (Platform Admins) to choose their context.
 *
 * VIBE COMPLIANT:
 * - Glassmorphism UI
 * - Lit Component
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import '../components/soma-button.js'; // Assuming basic button component exists

@customElement('soma-mode-selection')
export class SomaModeSelection extends LitElement {
    static styles = css`
        :host {
            display: flex;
            min-height: 100vh;
            width: 100%;
            align-items: center;
            justify-content: center;
            background: var(--soma-bg-void, #0f172a);
            color: var(--soma-text-main, #e2e8f0);
            position: relative;
            overflow: hidden;
        }

        /* Ambient Mesh Background (Simplified for CSS) */
        :host::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 50% 50%, rgba(76, 29, 149, 0.2), transparent 50%),
                        radial-gradient(circle at 10% 10%, rgba(56, 189, 248, 0.1), transparent 40%);
            animation: rotate 60s linear infinite;
            z-index: 0;
            pointer-events: none;
        }

        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .container {
            position: relative;
            z-index: 10;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 48px;
            padding: 24px;
            width: 100%;
            max-width: 1000px;
        }

        .header {
            text-align: center;
        }

        .title {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 8px;
            background: linear-gradient(135deg, #fff 0%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .subtitle {
            color: var(--soma-text-dim, #64748b);
            font-size: 16px;
        }

        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 40px;
            width: 100%;
            perspective: 1000px;
        }

        .card {
            display: flex;
            flex-direction: column;
            padding: 0; /* Content padding handled inside */
            border-radius: 24px;
            background: rgba(30, 41, 59, 0.4);
            backdrop-filter: blur(24px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            cursor: pointer;
            position: relative;
            overflow: hidden;
            height: 100%;
        }

        .card:hover {
            transform: translateY(-8px) scale(1.02);
            background: rgba(30, 41, 59, 0.6);
            border-color: rgba(255, 255, 255, 0.2);
            box-shadow: 
                0 20px 40px -12px rgba(0, 0, 0, 0.5),
                0 0 0 1px rgba(255,255,255,0.1) inset;
        }

        .card-header {
            padding: 32px;
            display: flex;
            align-items: center;
            gap: 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            background: rgba(255, 255, 255, 0.02);
        }

        .icon-wrapper {
            width: 60px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.05);
            box-shadow: inset 0 0 12px rgba(0,0,0,0.2);
            font-size: 28px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .header-text {
            flex: 1;
        }

        .card-title {
            font-size: 22px;
            font-weight: 700;
            color: var(--soma-text-main, #e2e8f0);
            margin: 0 0 4px 0;
            letter-spacing: -0.5px;
        }

        .badge {
            font-size: 11px;
            text-transform: uppercase;
            padding: 4px 8px;
            border-radius: 999px;
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        .badge.admin {
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }

        .badge.user {
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }

        .card-body {
            padding: 32px;
            flex: 1;
            display: flex;
            flex-direction: column;
        }

        .card-desc {
            font-size: 15px;
            color: var(--soma-text-dim, #94a3b8);
            margin-bottom: 24px;
            line-height: 1.6;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-top: auto;
        }

        .stat-item {
            display: flex;
            flex-direction: column;
            padding: 12px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.03);
        }

        .stat-value {
            font-size: 18px;
            font-weight: 700;
            color: #f1f5f9;
        }

        .stat-value.success { color: #4ade80; }
        .stat-value.warning { color: #fbbf24; }
        .stat-value.highlight { color: #38bdf8; }

        .stat-label {
            font-size: 11px;
            color: #64748b;
            margin-top: 4px;
            text-transform: uppercase;
        }

        .card-footer {
            padding: 20px 32px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            background: rgba(0, 0, 0, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
        }

        .access-level {
            color: #64748b;
        }
        
        strong { color: #94a3b8; }

        .action-arrow {
            color: var(--soma-accent, #38bdf8);
            font-weight: 600;
            opacity: 0.7;
            transition: all 0.3s;
        }

        .card:hover .action-arrow {
            opacity: 1;
            transform: translateX(4px);
        }

        /* Modal Styles */
        .modal-backdrop {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(8px);
            z-index: 100;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.3s ease-out;
        }

        .modal-content {
            width: 100%;
            max-width: 500px;
            background: rgba(30, 41, 59, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            padding: 32px;
            animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }

        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }

        .modal-header h3 {
            font-size: 20px;
            font-weight: 700;
            margin: 0;
            color: white;
        }

        .close-btn {
            background: none;
            border: none;
            color: #94a3b8;
            font-size: 24px;
            cursor: pointer;
            padding: 4px;
        }

        .modal-body {
            text-align: center;
            margin-bottom: 32px;
        }

        .modal-icon {
            font-size: 48px;
            margin-bottom: 16px;
        }

        .modal-body h4 {
            color: white;
            margin: 0 0 12px 0;
        }

        .modal-body p {
            color: #94a3b8;
            font-size: 14px;
            line-height: 1.6;
        }

        .info-box {
            margin-top: 24px;
            padding: 16px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .info-row {
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            color: #cbd5e1;
            margin-bottom: 8px;
        }

        .info-row:last-child { margin-bottom: 0; }

        .mono {
            font-family: monospace;
            color: #94a3b8;
        }
        
        .success { color: #4ade80; }

        .modal-footer {
            display: flex;
            gap: 12px;
        }

        .btn-cancel, .btn-confirm {
            flex: 1;
            padding: 12px;
            border-radius: 10px;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-cancel {
            background: transparent;
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #cbd5e1;
        }

        .btn-cancel:hover {
            background: rgba(255, 255, 255, 0.05);
        }

        .btn-confirm {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            border: none;
            color: white;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }

        .btn-confirm:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4);
        }
    `;

    private _handleMouseMove(e: MouseEvent) {
        // Simple spotlight effect
        const cards = this.shadowRoot?.querySelectorAll('.card');
        cards?.forEach((card: Element) => {
            const rect = (card as HTMLElement).getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            (card as HTMLElement).style.setProperty('--mouse-x', `${x}px`);
            (card as HTMLElement).style.setProperty('--mouse-y', `${y}px`);
        });
    }

    @state() private _selectedMode: 'platform' | 'tenant' | null = null;
    @state() private _showModal = false;

    // Simulated data for "lots of info"
    private _platformStats = {
        tenants: 124,
        agents: 4502,
        systemHealth: '99.9%',
        alerts: 2
    };

    private _tenantStats = {
        lastAccessed: 'Acme Corp',
        role: 'Owner',
        activeAgents: 5,
        notifications: 12
    };

    private _handleCardClick(mode: 'platform' | 'tenant') {
        this._selectedMode = mode;
        this._showModal = true;
    }

    private _proceed() {
        if (!this._selectedMode) return;

        if (this._selectedMode === 'platform') {
            window.location.href = '/saas/dashboard';
        } else {
            window.location.href = '/dashboard';
        }
    }

    render() {
        return html`
            <div class="container" @mousemove=${this._handleMouseMove}>
                <header class="header">
                    <h1 class="title">Select Interface Mode</h1>
                    <p class="subtitle">Access your specialized workspace</p>
                </header>

                <div class="cards">
                    <!-- Platform Admin Card -->
                    <div class="card" @click=${() => this._handleCardClick('platform')}>
                        <div class="card-header">
                            <div class="icon-wrapper">⚡</div>
                            <div class="header-text">
                                <h2 class="card-title">God Mode</h2>
                                <span class="badge admin">Super Admin</span>
                            </div>
                        </div>
                        
                        <div class="card-body">
                            <p class="card-desc">
                                Full infrastructure control, multi-tenant oversight, and system-wide configuration.
                            </p>
                            
                            <div class="stats-grid">
                                <div class="stat-item">
                                    <span class="stat-value">${this._platformStats.tenants}</span>
                                    <span class="stat-label">Tenants</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-value">${this._platformStats.agents}</span>
                                    <span class="stat-label">Agents</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-value success">${this._platformStats.systemHealth}</span>
                                    <span class="stat-label">Uptime</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-value warning">${this._platformStats.alerts}</span>
                                    <span class="stat-label">Alerts</span>
                                </div>
                            </div>
                        </div>

                        <div class="card-footer">
                            <span class="access-level">Access Level: <strong>Tier 0 (Root)</strong></span>
                            <span class="action-arrow">Configure System →</span>
                        </div>
                    </div>

                    <!-- Tenant View Card -->
                    <div class="card" @click=${() => this._handleCardClick('tenant')}>
                        <div class="card-header">
                            <div class="icon-wrapper">🏢</div>
                            <div class="header-text">
                                <h2 class="card-title">Tenant Viewer</h2>
                                <span class="badge user">Standard View</span>
                            </div>
                        </div>

                        <div class="card-body">
                            <p class="card-desc">
                                Focused workspace for agent management, conversation flows, and memory visualization.
                            </p>

                            <div class="stats-grid">
                                <div class="stat-item">
                                    <span class="stat-value">${this._tenantStats.lastAccessed}</span>
                                    <span class="stat-label">Last Viewed</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-value">${this._tenantStats.role}</span>
                                    <span class="stat-label">Current Role</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-value">${this._tenantStats.activeAgents}</span>
                                    <span class="stat-label">Active Agents</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-value highlight">${this._tenantStats.notifications}</span>
                                    <span class="stat-label">New Events</span>
                                </div>
                            </div>
                        </div>

                        <div class="card-footer">
                            <span class="access-level">Context: <strong>Single Tenant</strong></span>
                            <span class="action-arrow">Enter Workspace →</span>
                        </div>
                    </div>
                </div>

                <!-- Detail Modal -->
                ${this._showModal ? html`
                    <div class="modal-backdrop" @click=${() => this._showModal = false}>
                        <div class="modal-content" @click=${(e: Event) => e.stopPropagation()}>
                            <div class="modal-header">
                                <h3>Confirm Navigation</h3>
                                <button class="close-btn" @click=${() => this._showModal = false}>×</button>
                            </div>
                            
                            <div class="modal-body">
                                <div class="modal-icon">
                                    ${this._selectedMode === 'platform' ? '⚡' : '🏢'}
                                </div>
                                <h4>Entering ${this._selectedMode === 'platform' ? 'God Mode' : 'Tenant Workspace'}</h4>
                                <p>
                                    ${this._selectedMode === 'platform'
                    ? 'You are about to access the global system backend. All actions will be audited. Ensure you are authorized for high-level configuration changes.'
                    : 'You will be redirected to the specific tenant dashboard. Your session will be scoped to this tenant environment.'}
                                </p>
                                
                                <div class="info-box">
                                    <div class="info-row">
                                        <span>Session ID:</span>
                                        <span class="mono">${crypto.randomUUID().split('-')[0]}</span>
                                    </div>
                                    <div class="info-row">
                                        <span>Gateway Region:</span>
                                        <span class="mono">us-east-1</span>
                                    </div>
                                    <div class="info-row">
                                        <span>Latency:</span>
                                        <span class="success">12ms</span>
                                    </div>
                                </div>
                            </div>

                            <div class="modal-footer">
                                <button class="btn-cancel" @click=${() => this._showModal = false}>Cancel</button>
                                <button class="btn-confirm" @click=${this._proceed}>
                                    Initialize & Enter
                                </button>
                            </div>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-mode-selection': SomaModeSelection;
    }
}
