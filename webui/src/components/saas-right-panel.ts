/**
 * SomaAgent01 — Right Panel (Agent Toolkit)
 * Surfaces: Capsule, Brain
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { workspaceStore } from '../stores/workspace-store.js';

type SurfaceKey = 'capsule' | 'brain';

interface SurfaceDef {
    key: SurfaceKey;
    icon: string;
    label: string;
}

const SURFACES: SurfaceDef[] = [
    { key: 'capsule', icon: 'medication', label: 'Capsule' },
    { key: 'brain', icon: 'neurology', label: 'Brain' },
];

@customElement('saas-right-panel')
export class SaasRightPanel extends LitElement {
    @state() private _activeTab: SurfaceKey = 'capsule';
    @state() private _workspaceState = workspaceStore.state;

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
            height: 100%;
            background: var(--aaas-bg-card, #1e1e1e);
        }

        .panel {
            display: flex;
            width: 100%;
            height: 100%;
        }

        .tab-rail {
            width: 44px;
            flex-shrink: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 8px 0;
            gap: 4px;
            border-right: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            background: var(--aaas-bg-sidebar, #ffffff);
        }

        .tab-btn {
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: var(--aaas-radius-md, 8px);
            cursor: pointer;
            font-size: 16px;
            background: transparent;
            border: none;
            color: var(--aaas-text-muted, #999999);
            transition: all 150ms ease;
            position: relative;
        }

        .tab-btn:hover {
            background: var(--aaas-bg-hover, #141414);
            color: var(--aaas-text-secondary, #a1a1a1);
        }

        .tab-btn.active {
            background: var(--aaas-bg-active, #1a1a1a);
            color: var(--aaas-accent, #e8e4dc);
        }

        .tab-btn.active::before {
            content: '';
            position: absolute;
            left: -8px;
            top: 50%;
            transform: translateY(-50%);
            width: 3px;
            height: 20px;
            background: var(--aaas-accent, #e8e4dc);
            border-radius: 0 2px 2px 0;
        }

        .tab-tooltip {
            position: absolute;
            left: 44px;
            top: 50%;
            transform: translateY(-50%);
            background: var(--aaas-bg-hover, #141414);
            color: var(--aaas-text-secondary, #a1a1a1);
            padding: 4px 10px;
            border-radius: var(--aaas-radius-sm, 4px);
            font-size: 12px;
            white-space: nowrap;
            pointer-events: none;
            opacity: 0;
            transition: opacity 150ms ease;
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            z-index: 100;
        }

        .tab-btn:hover .tab-tooltip {
            opacity: 1;
        }

        .surface-content {
            flex: 1;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 16px;
        }

        .surface-header {
            font-size: 14px;
            font-weight: 600;
            color: var(--aaas-text-primary, #ffffff);
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
        }

        .placeholder {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 200px;
            color: var(--aaas-text-muted, #999999);
            font-size: 13px;
            text-align: center;
            gap: 8px;
        }

        .placeholder-icon {
            font-size: 32px;
            opacity: 0.5;
        }
    `;

    connectedCallback() {
        super.connectedCallback();
        workspaceStore.subscribe(() => {
            this._workspaceState = workspaceStore.state;
            const s = this._workspaceState.activeSurface;
            // Only honour surfaces that still exist; persisted values may name
            // tabs that have since been removed.
            if (s === 'capsule' || s === 'brain') {
                this._activeTab = s;
            }
        });
    }

    private _selectTab(tab: SurfaceKey) {
        this._activeTab = tab;
        workspaceStore.setSurface(tab);
    }

    render() {
        return html`
            <div class="panel">
                <div class="tab-rail">
                    ${SURFACES.map(s => html`
                        <button 
                            class="tab-btn ${this._activeTab === s.key ? 'active' : ''}"
                            @click=${() => this._selectTab(s.key)}
                            title="${s.label}"
                        >
                            <span class="material-symbols-outlined tab-icon">${s.icon}</span>
                            <span class="tab-tooltip">${s.label}</span>
                        </button>
                    `)}
                </div>
                <div class="surface-content">
                    ${this._renderSurface()}
                </div>
            </div>
        `;
    }

    private _renderSurface() {
        switch (this._activeTab) {
            case 'capsule':
                return html`<saas-capsule-editor></saas-capsule-editor>`;
            case 'brain':
                return html`<saas-brain-panel></saas-brain-panel>`;
            default:
                return html``;
        }
    }
}
