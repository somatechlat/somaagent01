/**
 * SomaAgent01 — Agent Header
 * Agent name, IQ badge, profile selector, model preset selector
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { agentStore } from '../stores/agent-store.js';
import { iqStore } from '../stores/iq-store.js';
import { workspaceStore } from '../stores/workspace-store.js';

@customElement('soma-agent-header')
export class SomaAgentHeader extends LitElement {
    @state() private _profileDropdownOpen = false;
    @state() private _presetDropdownOpen = false;
    @state() private _agentState = agentStore.state;
    @state() private _iqState = iqStore.knobs?.intelligence_level ?? null;

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
            display: block;
            background: var(--aaas-bg-card, #1e1e1e);
            border-bottom: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            padding: 12px 20px;
        }

        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
        }

        .agent-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .agent-avatar {
            width: 36px;
            height: 36px;
            border-radius: var(--aaas-radius-lg, 12px);
            background: linear-gradient(135deg, var(--aaas-accent, #e8e4dc), var(--aaas-text-muted, #999999));
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            flex-shrink: 0;
        }

        .agent-meta {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .agent-name {
            font-size: 15px;
            font-weight: 600;
            color: var(--aaas-text-primary, #ffffff);
        }

        .agent-status {
            font-size: 12px;
            color: var(--aaas-text-muted, #999999);
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .status-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--aaas-success, #22c55e);
        }

        .status-dot.paused { background: var(--aaas-warning, #f59e0b); }
        .status-dot.error { background: var(--aaas-danger, #ef4444); }

        .iq-badge {
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 3px 10px;
            border-radius: var(--aaas-radius-full, 9999px);
            font-size: 12px;
            font-weight: 600;
            background: rgba(34, 197, 94, 0.15);
            color: #4ade80;
            cursor: pointer;
            transition: all 150ms ease;
            border: none;
        }

        .iq-badge:hover {
            background: rgba(34, 197, 94, 0.25);
        }

        .iq-badge.medium {
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
        }

        .iq-badge.high {
            background: rgba(239, 68, 68, 0.15);
            color: #f87171;
        }

        .controls {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .pill-select {
            position: relative;
        }

        .pill-btn {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 6px 14px;
            border-radius: var(--aaas-radius-full, 9999px);
            background: var(--aaas-bg-hover, #141414);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            color: var(--aaas-text-secondary, #a1a1a1);
            font-size: 13px;
            cursor: pointer;
            transition: all 150ms ease;
        }

        .pill-btn:hover {
            border-color: var(--aaas-border-medium, rgba(255,255,255,0.1));
            color: var(--aaas-text-primary, #ffffff);
        }

        .pill-btn .chevron {
            font-size: 10px;
            transition: transform 150ms ease;
        }

        .pill-btn.open .chevron {
            transform: rotate(180deg);
        }

        .dropdown {
            position: absolute;
            top: calc(100% + 6px);
            right: 0;
            min-width: 220px;
            background: var(--aaas-bg-card, #1e1e1e);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            border-radius: var(--aaas-radius-lg, 12px);
            padding: 6px;
            z-index: 200;
            box-shadow: var(--aaas-shadow-lg, 0 8px 24px rgba(0,0,0,0.6));
        }

        .dropdown-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 12px;
            border-radius: var(--aaas-radius-md, 8px);
            cursor: pointer;
            font-size: 13px;
            color: var(--aaas-text-secondary, #a1a1a1);
            transition: all 100ms ease;
        }

        .dropdown-item:hover {
            background: var(--aaas-bg-hover, #141414);
            color: var(--aaas-text-primary, #ffffff);
        }

        .dropdown-item.active {
            background: var(--aaas-bg-active, #1a1a1a);
            color: var(--aaas-accent, #e8e4dc);
        }

        .dropdown-item .item-icon {
            font-size: 14px;
        }

        .dropdown-divider {
            height: 1px;
            background: var(--aaas-border-light, rgba(255,255,255,0.06));
            margin: 4px 0;
        }

        .icon-btn {
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: var(--aaas-radius-md, 8px);
            background: transparent;
            border: none;
            color: var(--aaas-text-muted, #999999);
            cursor: pointer;
            font-size: 16px;
            transition: all 150ms ease;
        }

        .icon-btn:hover {
            background: var(--aaas-bg-hover, #141414);
            color: var(--aaas-text-secondary, #a1a1a1);
        }
    `;

    connectedCallback() {
        super.connectedCallback();
        agentStore.subscribe(() => {
            this._agentState = agentStore.state;
        });
        iqStore.subscribe(() => {
            this._iqState = iqStore.knobs?.intelligence_level ?? null;
        });
    }

    render() {
        const agent = this._agentState.currentAgent;
        const iq = this._iqState;
        const profiles = this._agentState.profiles;
        const presets = this._agentState.presets;
        const activeProfile = profiles.find(p => p.id === this._agentState.activeProfileId);
        const activePreset = presets.find(p => p.id === this._agentState.activePresetId);

        const iqClass = iq === null ? '' : iq <= 3 ? '' : iq <= 7 ? 'medium' : 'high';

        return html`
            <div class="header">
                <div class="agent-info">
                    <div class="agent-avatar material-symbols-outlined">smart_toy</div>
                    <div class="agent-meta">
                        <div class="agent-name">${agent?.name ?? '—'}</div>
                        <div class="agent-status">
                            ${agent?.status
                                ? html`<span class="status-dot ${agent.status}"></span>
                                      <span>${agent.status === 'active' ? 'Online' : agent.status}</span>`
                                : html`<span class="muted">status —</span>`}
                        </div>
                    </div>
                </div>

                <div class="controls">
                    <button class="iq-badge ${iqClass}" @click=${() => workspaceStore.setSurface('brain')} title="AgentIQ intelligence level">
                        ${iq === null ? 'IQ —' : `IQ ${iq}`}
                    </button>

                    <div class="pill-select">
                        <button 
                            class="pill-btn ${this._profileDropdownOpen ? 'open' : ''}"
                            @click=${() => { this._profileDropdownOpen = !this._profileDropdownOpen; this._presetDropdownOpen = false; }}
                        >
                            <span>${activeProfile?.name || 'Default'}</span>
                            <span class="chevron material-symbols-outlined">expand_more</span>
                        </button>
                        ${this._profileDropdownOpen ? html`
                            <div class="dropdown">
                                ${profiles.map(p => html`
                                    <div 
                                        class="dropdown-item ${p.id === this._agentState.activeProfileId ? 'active' : ''}"
                                        @click=${() => { agentStore.setActiveProfile(p.id); this._profileDropdownOpen = false; }}
                                    >
                                        <span class="item-icon material-symbols-outlined">smart_toy</span>
                                        <span>${p.name}</span>
                                    </div>
                                `)}
                                <div class="dropdown-divider"></div>
                                <div class="dropdown-item" @click=${() => { this._profileDropdownOpen = false; }}>
                                    <span class="item-icon material-symbols-outlined">add</span>
                                    <span>Create Profile</span>
                                </div>
                            </div>
                        ` : ''}
                    </div>

                    <div class="pill-select">
                        <button 
                            class="pill-btn ${this._presetDropdownOpen ? 'open' : ''}"
                            @click=${() => { this._presetDropdownOpen = !this._presetDropdownOpen; this._profileDropdownOpen = false; }}
                        >
                            <span><span class="material-symbols-outlined">bolt</span> ${activePreset?.name || 'Balanced'}</span>
                            <span class="chevron material-symbols-outlined">expand_more</span>
                        </button>
                        ${this._presetDropdownOpen ? html`
                            <div class="dropdown">
                                ${presets.map(p => html`
                                    <div 
                                        class="dropdown-item ${p.id === this._agentState.activePresetId ? 'active' : ''}"
                                        @click=${() => { agentStore.setActivePreset(p.id); this._presetDropdownOpen = false; }}
                                    >
                                        <span class="item-icon material-symbols-outlined">bolt</span>
                                        <span>${p.name}</span>
                                        <span style="margin-left:auto;color:var(--aaas-text-muted);font-size:11px">${p.model}</span>
                                    </div>
                                `)}
                            </div>
                        ` : ''}
                    </div>

                    <button class="icon-btn" @click=${() => workspaceStore.setSurface('capsule')} title="Capsule Settings">
                        <span class="material-symbols-outlined">settings</span>
                    </button>
                </div>
            </div>
        `;
    }
}
