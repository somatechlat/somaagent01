/**
 * YACHAQ.AI — Welcome Dashboard
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
    { icon: 'add', label: 'New Chat', description: 'Start a new conversation', action: () => window.dispatchEvent(new CustomEvent('new-conversation')) },
    { icon: 'memory', label: 'Memory', description: 'Browse agent memories', action: () => window.dispatchEvent(new CustomEvent('soma-navigate', { detail: { route: '/memory' } })) },
    { icon: 'settings', label: 'Settings', description: 'Configure agent', action: () => window.dispatchEvent(new CustomEvent('soma-navigate', { detail: { route: '/settings' } })) },
];

@customElement('soma-welcome-dashboard')
export class SomaWelcomeDashboard extends LitElement {
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
            color: var(--platform-text-primary, #ffffff);
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }

        .welcome-subtitle {
            font-size: 15px;
            color: var(--platform-text-secondary, #a1a1a1);
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
            background: var(--platform-bg-card, #1e1e1e);
            border: 1px solid var(--platform-border-light, rgba(255,255,255,0.06));
            border-radius: var(--platform-radius-xl, 16px);
            cursor: pointer;
            transition: all 200ms ease;
            text-align: center;
        }

        .action-card:hover {
            border-color: var(--platform-border-medium, rgba(255,255,255,0.1));
            background: var(--platform-bg-hover, #141414);
            transform: translateY(-2px);
            box-shadow: var(--platform-shadow-md, 0 2px 8px rgba(0,0,0,0.5));
        }

        .action-icon {
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--platform-bg-hover, #141414);
            border-radius: var(--platform-radius-lg, 12px);
            font-size: 20px;
        }

        .action-label {
            font-size: 14px;
            font-weight: 600;
            color: var(--platform-text-primary, #ffffff);
        }

        .action-desc {
            font-size: 12px;
            color: var(--platform-text-muted, #999999);
        }

        .health-section {
            margin-top: 40px;
            max-width: 640px;
            width: 100%;
        }

        .section-title {
            font-size: 13px;
            font-weight: 600;
            color: var(--platform-text-secondary, #a1a1a1);
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
            background: var(--platform-bg-card, #1e1e1e);
            border: 1px solid var(--platform-border-light, rgba(255,255,255,0.06));
            border-radius: var(--platform-radius-lg, 12px);
        }

        .health-bar {
            flex: 1;
            height: 6px;
            background: var(--platform-bg-hover, #141414);
            border-radius: var(--platform-radius-full, 9999px);
            overflow: hidden;
        }

        .health-fill {
            height: 100%;
            border-radius: var(--platform-radius-full, 9999px);
            transition: width 500ms ease;
        }

        .health-fill.success { background: var(--platform-success, #22c55e); }
        .health-fill.warning { background: var(--platform-warning, #f59e0b); }
        .health-fill.danger { background: var(--platform-danger, #ef4444); }

        .health-label {
            font-size: 13px;
            color: var(--platform-text-secondary, #a1a1a1);
            min-width: 140px;
        }

        .health-value {
            font-size: 12px;
            color: var(--platform-text-muted, #999999);
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
                <div class="welcome-title">YACHAQ.AI</div>
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

        `;
    }
}
