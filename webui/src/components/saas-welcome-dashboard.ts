/**
 * SomaAgent01 — Welcome Dashboard
 * Shown when no chat is active
 */

import { LitElement, html, css } from 'lit';
import { customElement } from 'lit/decorators.js';

interface ActionCard {
    icon: string;
    label: string;
    description: string;
    action: () => void;
}

const ACTIONS: ActionCard[] = [
    { icon: '+', label: 'New Chat', description: 'Start a new conversation', action: () => window.dispatchEvent(new CustomEvent('new-conversation')) },
    { icon: '📁', label: 'Projects', description: 'Manage agent projects', action: () => {} },
    { icon: '🧠', label: 'Memory', description: 'Browse agent memories', action: () => window.dispatchEvent(new CustomEvent('saas-navigate', { detail: { route: '/memory' } })) },
    { icon: '⏱', label: 'Tasks', description: 'View scheduled tasks', action: () => {} },
    { icon: '⚙', label: 'Settings', description: 'Configure agent', action: () => window.dispatchEvent(new CustomEvent('saas-navigate', { detail: { route: '/settings' } })) },
    { icon: '🎨', label: 'Skins', description: 'Customize appearance', action: () => window.dispatchEvent(new CustomEvent('saas-navigate', { detail: { route: '/themes' } })) },
    { icon: '💊', label: 'Capsules', description: 'Manage agent identity', action: () => {} },
    { icon: '🌐', label: 'Browser', description: 'Open web browser', action: () => {} },
];

@customElement('saas-welcome-dashboard')
export class SaasWelcomeDashboard extends LitElement {
    static styles = css`
        :host {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            padding: 40px;
            overflow-y: auto;
        }

        .welcome {
            text-align: center;
            margin-bottom: 40px;
        }

        .welcome-title {
            font-size: 28px;
            font-weight: 700;
            color: var(--aaas-text-primary, #ffffff);
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }

        .welcome-subtitle {
            font-size: 15px;
            color: var(--aaas-text-secondary, #a1a1a1);
        }

        .actions-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            max-width: 640px;
            width: 100%;
        }

        .action-card {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
            padding: 24px 16px;
            background: var(--aaas-bg-card, #1e1e1e);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            border-radius: var(--aaas-radius-xl, 16px);
            cursor: pointer;
            transition: all 200ms ease;
            text-align: center;
        }

        .action-card:hover {
            border-color: var(--aaas-border-medium, rgba(255,255,255,0.1));
            background: var(--aaas-bg-hover, #141414);
            transform: translateY(-2px);
            box-shadow: var(--aaas-shadow-md, 0 2px 8px rgba(0,0,0,0.5));
        }

        .action-icon {
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--aaas-bg-hover, #141414);
            border-radius: var(--aaas-radius-lg, 12px);
            font-size: 20px;
        }

        .action-label {
            font-size: 14px;
            font-weight: 600;
            color: var(--aaas-text-primary, #ffffff);
        }

        .action-desc {
            font-size: 12px;
            color: var(--aaas-text-muted, #6b6b6b);
        }

        .health-section {
            margin-top: 40px;
            max-width: 640px;
            width: 100%;
        }

        .section-title {
            font-size: 13px;
            font-weight: 600;
            color: var(--aaas-text-secondary, #a1a1a1);
            margin-bottom: 16px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .health-grid {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .health-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            background: var(--aaas-bg-card, #1e1e1e);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            border-radius: var(--aaas-radius-lg, 12px);
        }

        .health-bar {
            flex: 1;
            height: 6px;
            background: var(--aaas-bg-hover, #141414);
            border-radius: var(--aaas-radius-full, 9999px);
            overflow: hidden;
        }

        .health-fill {
            height: 100%;
            border-radius: var(--aaas-radius-full, 9999px);
            transition: width 500ms ease;
        }

        .health-fill.success { background: var(--aaas-success, #22c55e); }
        .health-fill.warning { background: var(--aaas-warning, #f59e0b); }
        .health-fill.danger { background: var(--aaas-danger, #ef4444); }

        .health-label {
            font-size: 13px;
            color: var(--aaas-text-secondary, #a1a1a1);
            min-width: 140px;
        }

        .health-value {
            font-size: 12px;
            color: var(--aaas-text-muted, #6b6b6b);
            min-width: 80px;
            text-align: right;
        }

        @media (max-width: 600px) {
            .actions-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    `;

    render() {
        return html`
            <div class="welcome">
                <div class="welcome-title">SomaAgent01</div>
                <div class="welcome-subtitle">Autonomous AI Agent Workspace</div>
            </div>

            <div class="actions-grid">
                ${ACTIONS.map(a => html`
                    <div class="action-card" @click=${a.action}>
                        <div class="action-icon">${a.icon}</div>
                        <div class="action-label">${a.label}</div>
                        <div class="action-desc">${a.description}</div>
                    </div>
                `)}
            </div>

            <div class="health-section">
                <div class="section-title">System Health</div>
                <div class="health-grid">
                    <div class="health-item">
                        <span class="health-label">SomaBrain</span>
                        <div class="health-bar"><div class="health-fill success" style="width:92%"></div></div>
                        <span class="health-value">Connected</span>
                    </div>
                    <div class="health-item">
                        <span class="health-label">Memory</span>
                        <div class="health-bar"><div class="health-fill success" style="width:100%"></div></div>
                        <span class="health-value">Healthy</span>
                    </div>
                    <div class="health-item">
                        <span class="health-label">Cognitive Load</span>
                        <div class="health-bar"><div class="health-fill warning" style="width:62%"></div></div>
                        <span class="health-value">Medium</span>
                    </div>
                </div>
            </div>
        `;
    }
}
