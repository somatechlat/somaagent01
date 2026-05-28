/**
 * SomaAgent01 — SomaBrain Cognitive Panel
 * Neuromodulators, sleep cycles, memory config
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { brainStore } from '../stores/brain-store.js';

@customElement('saas-brain-panel')
export class SaasBrainPanel extends LitElement {
    @state() private _brainState = brainStore.state;
    @state() private _retentionDays = 30;
    @state() private _archivalDays = 365;
    @state() private _snapshotHours = 24;

    static styles = css`
        :host {
            display: block;
        }

        .header {
            font-size: 14px;
            font-weight: 600;
            color: var(--aaas-text-primary, #ffffff);
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .connection-badge {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            font-weight: 500;
            color: var(--aaas-success, #22c55e);
        }

        .connection-badge .dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--aaas-success, #22c55e);
            animation: pulse 2s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .section {
            background: var(--aaas-bg-hover, #141414);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            border-radius: var(--aaas-radius-lg, 12px);
            padding: 16px;
            margin-bottom: 16px;
        }

        .section-title {
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--aaas-text-muted, #6b6b6b);
            margin-bottom: 14px;
        }

        .neuro-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .neuro-row {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .neuro-icon {
            font-size: 16px;
            width: 24px;
            text-align: center;
        }

        .neuro-info {
            flex: 1;
        }

        .neuro-name {
            font-size: 12px;
            color: var(--aaas-text-secondary, #a1a1a1);
            margin-bottom: 4px;
        }

        .neuro-bar {
            height: 6px;
            background: var(--aaas-bg-active, #1a1a1a);
            border-radius: var(--aaas-radius-full, 9999px);
            overflow: hidden;
        }

        .neuro-fill {
            height: 100%;
            border-radius: var(--aaas-radius-full, 9999px);
            transition: width 500ms ease;
        }

        .neuro-value {
            font-size: 13px;
            font-weight: 600;
            color: var(--aaas-text-primary, #ffffff);
            min-width: 40px;
            text-align: right;
            font-variant-numeric: tabular-nums;
        }

        .neuro-status {
            font-size: 10px;
            color: var(--aaas-text-muted, #6b6b6b);
            min-width: 50px;
            text-align: right;
        }

        .stat-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
        }

        .stat-row:last-child {
            border-bottom: none;
        }

        .stat-label {
            font-size: 13px;
            color: var(--aaas-text-secondary, #a1a1a1);
        }

        .stat-value {
            font-size: 13px;
            font-weight: 600;
            color: var(--aaas-text-primary, #ffffff);
        }

        .sleep-controls {
            display: flex;
            gap: 8px;
            margin-top: 12px;
        }

        .btn {
            padding: 8px 14px;
            border-radius: var(--aaas-radius-md, 8px);
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 150ms ease;
            border: none;
        }

        .btn-primary {
            background: var(--aaas-accent, #e8e4dc);
            color: var(--aaas-bg-void, #0a0a0a);
        }

        .btn-primary:hover {
            background: var(--aaas-accent-hover, #ffffff);
        }

        .btn-secondary {
            background: var(--aaas-bg-active, #1a1a1a);
            color: var(--aaas-text-secondary, #a1a1a1);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
        }

        .btn-secondary:hover {
            color: var(--aaas-text-primary, #ffffff);
        }

        .field {
            margin-bottom: 12px;
        }

        .field-label {
            font-size: 12px;
            color: var(--aaas-text-muted, #6b6b6b);
            margin-bottom: 6px;
            display: block;
        }

        .field-input {
            width: 100%;
            background: var(--aaas-bg-active, #1a1a1a);
            border: 1px solid var(--aaas-border-light, rgba(255,255,255,0.06));
            border-radius: var(--aaas-radius-md, 8px);
            padding: 8px 12px;
            color: var(--aaas-text-primary, #ffffff);
            font-size: 13px;
            outline: none;
            transition: border-color 150ms ease;
        }

        .field-input:focus {
            border-color: var(--aaas-border-medium, rgba(255,255,255,0.1));
        }
    `;

    connectedCallback() {
        super.connectedCallback();
        brainStore.subscribe(() => {
            this._brainState = brainStore.state;
        });
    }

    render() {
        const state = this._brainState;
        const neuro = state.neuromodulators;

        const neuroData = [
            { name: 'Dopamine', value: neuro.dopamine, icon: '🧪', status: neuro.dopamine > 0.5 ? 'active' : 'low', color: '#22c55e' },
            { name: 'Serotonin', value: neuro.serotonin, icon: '😌', status: neuro.serotonin > 0.8 ? 'stable' : 'low', color: '#3b82f6' },
            { name: 'Noradrenaline', value: neuro.noradrenaline, icon: '⚡', status: neuro.noradrenaline > 0.1 ? 'alert' : 'calm', color: '#f59e0b' },
            { name: 'Acetylcholine', value: neuro.acetylcholine, icon: '🎯', status: neuro.acetylcholine > 0.4 ? 'focused' : 'low', color: '#8b5cf6' },
        ];

        return html`
            <div class="header">
                <span>SomaBrain</span>
                <span class="connection-badge">
                    <span class="dot"></span>
                    Connected
                </span>
            </div>

            <div class="section">
                <div class="section-title">Cognitive State</div>
                <div class="neuro-list">
                    ${neuroData.map(n => html`
                        <div class="neuro-row">
                            <span class="neuro-icon">${n.icon}</span>
                            <div class="neuro-info">
                                <div class="neuro-name">${n.name}</div>
                                <div class="neuro-bar">
                                    <div class="neuro-fill" style="width: ${n.value * 100}%; background: ${n.color}"></div>
                                </div>
                            </div>
                            <span class="neuro-value">${n.value.toFixed(2)}</span>
                            <span class="neuro-status">${n.status}</span>
                        </div>
                    `)}
                </div>

                <div class="stat-row" style="margin-top:12px;padding-top:12px;border-top:1px solid var(--aaas-border-light)">
                    <span class="stat-label">Adaptation</span>
                    <span class="stat-value">${state.adaptation}%</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Memory Vectors</span>
                    <span class="stat-value">${state.memoryUsage.toLocaleString()}</span>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Sleep Cycle</div>
                <div class="stat-row">
                    <span class="stat-label">Status</span>
                    <span class="stat-value" style="text-transform:capitalize;color:var(--aaas-success)">${state.sleepStatus}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Last Consolidation</span>
                    <span class="stat-value">${state.lastConsolidation ? new Date(state.lastConsolidation).toLocaleTimeString() : 'Never'}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Next Scheduled</span>
                    <span class="stat-value">${state.nextScheduled ? new Date(state.nextScheduled).toLocaleTimeString() : '—'}</span>
                </div>
                <div class="sleep-controls">
                    <button class="btn btn-primary">Trigger Sleep</button>
                    <button class="btn btn-secondary">Force Wake</button>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Memory Config</div>
                <div class="field">
                    <label class="field-label">Retention (days)</label>
                    <input class="field-input" type="number" .value=${this._retentionDays.toString()} @input=${(e: Event) => this._retentionDays = parseInt((e.target as HTMLInputElement).value)} />
                </div>
                <div class="field">
                    <label class="field-label">Archival (days)</label>
                    <input class="field-input" type="number" .value=${this._archivalDays.toString()} @input=${(e: Event) => this._archivalDays = parseInt((e.target as HTMLInputElement).value)} />
                </div>
                <div class="field">
                    <label class="field-label">Snapshot (hours)</label>
                    <input class="field-input" type="number" .value=${this._snapshotHours.toString()} @input=${(e: Event) => this._snapshotHours = parseInt((e.target as HTMLInputElement).value)} />
                </div>
                <button class="btn btn-primary" style="width:100%;margin-top:4px">Save Config</button>
            </div>
        `;
    }
}
