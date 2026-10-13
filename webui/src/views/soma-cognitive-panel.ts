/**
 * SomaAgent Soma — Cognitive Panel (TRN Mode)
 * Per AGENT_USER_UI_SRS.md Section 9 - Cognitive Panel
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - SomaBrain Cognitive API integration
 * - Minimal white/black design per UI_STYLE_GUIDE.md
 * - NO EMOJIS - Google Material Symbols only
 * 
 * Features:
 * - Neuromodulator gauges (Dopamine, Serotonin, Norepinephrine, etc.)
 * - Adaptation parameters sliders
 * - Learning rate configuration
 * - Sleep cycle trigger
 * - Reset adaptation
 */

import { LitElement, html, css } from 'lit';
import { glassCard } from '../styles/glass.js';
import { moduleBase } from '../styles/module-base.js';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';

/** Server shape: CognitiveStateResponse.neuromodulators is a flat dict of
 *  name -> number (admin/somabrain/cognitive.py:75-82). No min/max/unit and
 *  no last_synced_at are sent, so no percentage meter can be honest. */
interface NeuromodulatorReading {
    name: string;
    value: number;
}

/** AdaptationParams is an untyped dict on the server. Fields are optional
 *  here so a missing key stays missing — never a fabricated 0. */
interface AdaptationParams {
    learningRate?: number;
    explorationRate?: number;
    attentionSpan?: number;
    memoryConsolidation?: number;
    emotionalSensitivity?: number;
}

@customElement('soma-cognitive-panel')
export class SomaCognitivePanel extends LitElement {
    static styles = [
        glassCard,
        moduleBase,
        css`
        :host {
            display: flex;
            height: 100vh;
            background: var(--skin-color-bg-void);
            font-family: var(--skin-font-sans);
            color: var(--skin-color-text-primary);
        }

        * {
            box-sizing: border-box;
        }

        /* Material Symbols - Required for Shadow DOM */
        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: var(--skin-text-xl);
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
           SIDEBAR
           ======================================== */
        .sidebar {
            width: calc(var(--skin-space-2xl) * 5 + var(--skin-space-xl));
            background: var(--skin-color-bg-card);
            border-right: var(--skin-border-width) solid var(--skin-color-border);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
            padding: var(--skin-space-lg) calc(var(--skin-space-md) + var(--skin-space-xs));
        }

        .sidebar-header {
            margin-bottom: var(--skin-space-lg);
        }

        .sidebar-title {
            font-size: var(--skin-text-xl);
            font-weight: var(--skin-weight-semibold);
            margin: 0 0 var(--skin-space-xs) 0;
            display: flex;
            align-items: center;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs) * 0.5);
        }

        .sidebar-subtitle {
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-secondary);
        }

        .mode-badge {
            padding: var(--skin-space-xs) var(--skin-space-sm);
            border-radius: var(--skin-radius-sm);
            background: color-mix(in srgb, var(--skin-color-warning) 22%, transparent);
            color: var(--skin-color-warning-text);
            font-size: var(--skin-text-xs);
            font-weight: var(--skin-weight-semibold);
        }

        /* Status Card */
        .status-card {
            background: var(--skin-color-bg-hover);
            border-radius: var(--skin-radius-lg);
            padding: var(--skin-space-md);
            margin-bottom: calc(var(--skin-space-md) + var(--skin-space-xs));
        }

        .status-row {
            display: flex;
            justify-content: space-between;
            padding: var(--skin-space-sm) 0;
            font-size: var(--skin-text-sm);
        }

        .status-label {
            color: var(--skin-color-text-secondary);
        }

        .status-value {
            font-weight: var(--skin-weight-semibold);
        }

        .status-value.online {
            color: var(--skin-color-success);
        }

        .status-value.warning {
            color: var(--skin-color-warning);
        }

        /* Quick Actions */
        .quick-actions {
            display: flex;
            flex-direction: column;
            gap: var(--skin-space-sm);
            margin-bottom: var(--skin-space-lg);
        }

        .action-btn {
            display: flex;
            align-items: center;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs) * 0.5);
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs)) calc(var(--skin-space-md) - var(--skin-space-xs) * 0.5);
            border-radius: var(--skin-radius-md);
            border: var(--skin-border-width) solid var(--skin-color-border);
            background: var(--skin-color-bg-card);
            font-size: var(--skin-text-base);
            cursor: pointer;
            transition: all var(--skin-motion-fast) var(--skin-motion-ease);
            color: var(--skin-color-text-primary);
        }

        .action-btn:hover {
            background: var(--skin-color-bg-hover);
            border-color: var(--skin-color-border-strong);
        }

        .action-btn.primary {
            background: var(--skin-color-accent);
            color: var(--skin-color-accent-text);
            border-color: var(--skin-color-accent);
        }

        .action-btn.primary:hover {
            background: var(--skin-color-accent-hover);
        }

        .action-btn.warning {
            border-color: var(--skin-color-warning);
            color: var(--skin-color-warning);
        }

        .action-btn.warning:hover {
            background: color-mix(in srgb, var(--skin-color-warning) 12%, transparent);
        }

        .action-btn .material-symbols-outlined {
            font-size: var(--skin-text-xl);
        }

        /* Back Button */
        .back-btn {
            display: flex;
            align-items: center;
            gap: var(--skin-space-sm);
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs)) calc(var(--skin-space-md) - var(--skin-space-xs) * 0.5);
            margin-top: auto;
            border: none;
            background: transparent;
            font-size: var(--skin-text-base);
            color: var(--skin-color-text-secondary);
            cursor: pointer;
            transition: all var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .back-btn:hover {
            color: var(--skin-color-text-primary);
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

        /* Header */
        .header {
            padding: var(--skin-space-md) var(--skin-space-lg);
            background: var(--skin-color-bg-card);
            border-bottom: var(--skin-border-width) solid var(--skin-color-border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header-title {
            font-size: var(--skin-text-xl);
            font-weight: var(--skin-weight-semibold);
        }

        .header-actions {
            display: flex;
            gap: var(--skin-space-sm);
        }

        .save-btn {
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs) * 0.5) calc(var(--skin-space-md) + var(--skin-space-xs));
            border-radius: var(--skin-radius-md);
            background: var(--skin-color-accent);
            color: var(--skin-color-accent-text);
            border: none;
            font-size: var(--skin-text-base);
            font-weight: var(--skin-weight-medium);
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: var(--skin-space-sm);
            transition: all var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .save-btn:hover:not(:disabled) {
            background: var(--skin-color-accent-hover);
        }

        .save-btn:disabled {
            background: var(--skin-color-border);
            color: var(--skin-color-text-muted);
            cursor: not-allowed;
        }

        .save-btn .material-symbols-outlined {
            font-size: var(--skin-text-xl);
        }

        /* Content Area */
        .content {
            flex: 1;
            overflow-y: auto;
            padding: var(--skin-space-lg);
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: calc(var(--skin-space-md) + var(--skin-space-xs));
            align-content: start;
        }

        @media (max-width: 1000px) {
            .content {
                grid-template-columns: 1fr;
            }
        }

        /* Cards */
        .card {
            background: var(--skin-color-bg-card);
            border: var(--skin-border-width) solid var(--skin-color-border);
            border-radius: var(--skin-radius-lg);
            padding: var(--skin-space-lg);
        }

        .card.full-width {
            grid-column: 1 / -1;
        }

        .card-title {
            font-size: var(--skin-text-lg);
            font-weight: var(--skin-weight-semibold);
            margin: 0 0 var(--skin-space-md) 0;
            display: flex;
            align-items: center;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs) * 0.5);
        }

        .card-title .material-symbols-outlined {
            font-size: var(--skin-text-xl);
            color: var(--skin-color-text-secondary);
        }

        .card-desc {
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-secondary);
            margin-bottom: calc(var(--skin-space-md) + var(--skin-space-xs));
        }

        /* Neuromodulator Gauges */
        .gauge-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: var(--skin-space-md);
        }

        @media (max-width: 1200px) {
            .gauge-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        .gauge-item {
            background: var(--skin-color-bg-hover);
            border-radius: var(--skin-radius-lg);
            padding: var(--skin-space-md);
            text-align: center;
        }

        .gauge-icon {
            width: calc(var(--skin-space-xl) + var(--skin-space-sm));
            height: calc(var(--skin-space-xl) + var(--skin-space-sm));
            border-radius: var(--skin-radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto calc(var(--skin-space-sm) + var(--skin-space-xs));
            background: var(--skin-color-bg-card);
            border: var(--skin-border-width) solid var(--skin-color-border);
        }

        .gauge-icon .material-symbols-outlined {
            font-size: var(--skin-text-xl);
        }

        .gauge-name {
            font-size: var(--skin-text-sm);
            font-weight: var(--skin-weight-medium);
            margin-bottom: var(--skin-space-sm);
        }

        .gauge-bar {
            height: var(--skin-space-sm);
            background: var(--skin-color-border);
            border-radius: var(--skin-radius-sm);
            overflow: hidden;
            margin-bottom: var(--skin-space-sm);
        }

        .gauge-fill {
            height: 100%;
            border-radius: var(--skin-radius-sm);
            transition: width var(--skin-motion-slow) var(--skin-motion-ease);
        }

        .gauge-fill.dopamine { background: color-mix(in srgb, var(--skin-color-accent) 55%, var(--skin-color-info)); }
        .gauge-fill.serotonin { background: var(--skin-color-warning); }
        .gauge-fill.norepinephrine { background: var(--skin-color-danger); }
        .gauge-fill.acetylcholine { background: var(--skin-color-success); }
        .gauge-fill.gaba { background: var(--skin-color-info); }
        .gauge-fill.cortisol { background: color-mix(in srgb, var(--skin-color-danger) 55%, var(--skin-color-accent)); }

        .gauge-value {
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-muted);
        }

        /* Parameter Sliders */
        .param-list {
            display: flex;
            flex-direction: column;
            gap: calc(var(--skin-space-md) + var(--skin-space-xs));
        }

        .param-item {
            display: flex;
            flex-direction: column;
            gap: var(--skin-space-sm);
        }

        .param-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .param-label {
            font-size: var(--skin-text-base);
            font-weight: var(--skin-weight-medium);
        }

        .param-value {
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-secondary);
            font-family: var(--skin-font-mono);
            background: var(--skin-color-bg-hover);
            padding: var(--skin-space-xs) var(--skin-space-sm);
            border-radius: var(--skin-radius-sm);
        }

        .param-slider {
            -webkit-appearance: none;
            width: 100%;
            height: calc(var(--skin-space-sm) * 0.75);
            border-radius: var(--skin-radius-sm);
            background: var(--skin-color-border);
            outline: none;
        }

        .param-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: calc(var(--skin-space-md) + var(--skin-space-xs) * 0.5);
            height: calc(var(--skin-space-md) + var(--skin-space-xs) * 0.5);
            border-radius: var(--skin-radius-full);
            background: var(--skin-color-accent);
            cursor: pointer;
            transition: transform var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .param-slider::-webkit-slider-thumb:hover {
            transform: scale(1.1);
        }

        .param-desc {
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-muted);
        }

        /* Activity Log */
        .activity-log {
            max-height: calc(var(--skin-space-2xl) * 4 + var(--skin-space-sm));
            overflow-y: auto;
        }

        .log-entry {
            display: flex;
            align-items: flex-start;
            gap: calc(var(--skin-space-sm) + var(--skin-space-xs));
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs) * 0.5) 0;
            border-bottom: var(--skin-border-width) solid var(--skin-color-border);
        }

        .log-entry:last-child {
            border-bottom: none;
        }

        .log-icon {
            width: calc(var(--skin-space-lg) + var(--skin-space-xs));
            height: calc(var(--skin-space-lg) + var(--skin-space-xs));
            border-radius: var(--skin-radius-md);
            background: var(--skin-color-bg-hover);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .log-icon .material-symbols-outlined {
            font-size: var(--skin-text-base);
        }

        .log-content {
            flex: 1;
        }

        .log-message {
            font-size: var(--skin-text-sm);
            margin-bottom: var(--skin-space-xs);
        }

        .log-time {
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-muted);
        }

        /* Loading */
        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: calc(var(--skin-space-2xl) + var(--skin-space-sm) + var(--skin-space-xs));
        }

        .spinner {
            width: var(--skin-space-xl);
            height: var(--skin-space-xl);
            border: calc(var(--skin-border-width) * 3) solid var(--skin-color-border);
            border-top-color: var(--skin-color-text-primary);
            border-radius: var(--skin-radius-full);
            animation: spin var(--skin-motion-slow) linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    `
    ];

    @state() private _isLoading = false;
    @state() private _isDirty = false;
    @state() private _isSaving = false;
    /** Client-local flag for "a sleep trigger is in flight this session".
     *  It is not the agent's server-side sleep state. */
    @state() private _sleepTriggerInFlight = false;
    @state() private _brainConnected = false;

    // Live SomaBrain state only — no hardcoded defaults.
    @state() private _neuromodulators: NeuromodulatorReading[] = [];
    @state() private _loadFailed = false;

    // Empty until the server sends adaptation_params. A missing key is not 0.
    @state() private _params: AdaptationParams = {};

    /** Real sleep state from GET /somabrain/cognitive/sleep/status/{agent_id}.
     *  null = not loaded (no agent / fetch failed) — renders as "—". */
    @state() private _sleepState: boolean | null = null;

    @state() private _activityLog: { message: string; time: string; icon: string }[] = [];

    async connectedCallback() {
        super.connectedCallback();
        await this._loadCognitiveState();
    }

    /** sessionStorage first, then localStorage — the exact key/order the chat
     *  view writes (soma-chat.ts _persistSelectedAgentId). */
    private _agentId(): string {
        return sessionStorage.getItem('soma_agent_id') || localStorage.getItem('soma_agent_id') || '';
    }

    private _logActivity(message: string, icon: string) {
        this._activityLog = [
            { message, time: new Date().toLocaleTimeString(), icon },
            ...this._activityLog,
        ];
    }

    private _errorDetail(error: unknown): string {
        return error instanceof Error ? error.message : String(error);
    }

    render() {
        return html`
            <!-- Sidebar -->
            <aside class="sidebar">
                <div class="sidebar-header">
                    <h1 class="sidebar-title">
                        <span class="material-symbols-outlined">neurology</span>
                        Cognitive
                        <span class="mode-badge">TRN</span>
                    </h1>
                    <p class="sidebar-subtitle">Training Mode Controls</p>
                </div>

                <!-- Status Card -->
                <div class="status-card">
                    <div class="status-row">
                        <span class="status-label">Sleep trigger</span>
                        <span class="status-value ${this._sleepTriggerInFlight ? 'warning' : 'online'}">
                            ${this._sleepTriggerInFlight ? 'In flight (this session)' : 'Idle'}
                        </span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">Sleep state</span>
                        <span class="status-value ${this._sleepState === false ? 'online' : 'warning'}">
                            ${this._sleepState === null ? '—' : this._sleepState ? 'Sleeping' : 'Awake'}
                        </span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">SomaBrain</span>
                        <span class="status-value ${this._brainConnected ? 'online' : 'warning'}">
                            ${this._brainConnected ? 'Connected' : 'Unavailable'}
                        </span>
                    </div>
                </div>

                <!-- Quick Actions -->
                <div class="quick-actions">
                    <button class="action-btn primary" @click=${this._triggerSleepCycle}>
                        <span class="material-symbols-outlined">bedtime</span>
                        Trigger Sleep Cycle
                    </button>
                    <button class="action-btn warning" @click=${this._resetAdaptation}>
                        <span class="material-symbols-outlined">restart_alt</span>
                        Reset Adaptation
                    </button>
                </div>

                <button class="back-btn" @click=${() => window.location.href = '/chat'}>
                    <span class="material-symbols-outlined">arrow_back</span> Back to Chat
                </button>
            </aside>

            <!-- Main Content -->
            <main class="main">
                <header class="header">
                    <h2 class="header-title">Cognitive Parameters</h2>
                    <div class="header-actions">
                        <button 
                            class="save-btn" 
                            ?disabled=${!this._isDirty || this._isSaving}
                            @click=${this._saveParams}
                        >
                            <span class="material-symbols-outlined">save</span>
                            ${this._isSaving ? 'Saving...' : 'Apply Changes'}
                        </button>
                    </div>
                </header>

                <div class="content">
                    ${this._isLoading ? html`
                        <div class="loading"><div class="spinner"></div></div>
                    ` : html`
                        <!-- Neuromodulator readouts. REQ-UIX-010: no meter
                             value renders without a real sync timestamp. The
                             cognitive API sends no last_synced_at, so these
                             are raw server numbers, not percentage meters. -->
                        <div class="card full-width">
                            <h3 class="card-title">
                                <span class="material-symbols-outlined">monitoring</span>
                                Neuromodulator readings
                            </h3>
                            <p class="card-desc">
                                Raw values as reported by SomaBrain. No sync
                                timestamp is available, so percentage meters
                                are not rendered (REQ-UIX-010).
                            </p>

                            ${this._loadFailed
                                ? html`<p class="card-desc">Failed to load cognitive state. No values are shown.</p>`
                                : this._neuromodulators.length === 0
                                    ? html`<p class="card-desc">No neuromodulator readings were reported.</p>`
                                    : html`
                            <div class="gauge-grid">
                                ${this._neuromodulators.map(nm => this._renderGauge(nm))}
                            </div>`}
                        </div>

                        <!-- Adaptation Parameters -->
                        <div class="card">
                            <h3 class="card-title">
                                <span class="material-symbols-outlined">tune</span>
                                Adaptation Parameters
                            </h3>
                            <p class="card-desc">Fine-tune learning behavior</p>
                            
                            <div class="param-list">
                                ${this._renderParamInput('learningRate', 'Learning Rate', 'Controls speed of weight updates')}
                                ${this._renderParamInput('explorationRate', 'Exploration Rate', 'Balance between exploration and exploitation')}
                                ${this._renderParamInput('attentionSpan', 'Attention Span', 'How long to focus on single topics')}
                            </div>
                        </div>

                        <!-- Memory Parameters -->
                        <div class="card">
                            <h3 class="card-title">
                                <span class="material-symbols-outlined">psychology</span>
                                Memory Parameters
                            </h3>
                            <p class="card-desc">Configure memory behavior</p>
                            
                            <div class="param-list">
                                ${this._renderParamInput('memoryConsolidation', 'Consolidation Rate', 'Speed of short to long-term transfer')}
                                ${this._renderParamInput('emotionalSensitivity', 'Emotional Sensitivity', 'Weight of emotional context in memories')}
                            </div>
                        </div>

                        <!-- Activity Log -->
                        <div class="card full-width">
                            <h3 class="card-title">
                                <span class="material-symbols-outlined">history</span>
                                Activity Log
                            </h3>
                            
                            <div class="activity-log">
                                ${this._activityLog.map(entry => html`
                                    <div class="log-entry">
                                        <div class="log-icon">
                                            <span class="material-symbols-outlined">${entry.icon}</span>
                                        </div>
                                        <div class="log-content">
                                            <div class="log-message">${entry.message}</div>
                                            <div class="log-time">${entry.time}</div>
                                        </div>
                                    </div>
                                `)}
                            </div>
                        </div>
                    `}
                </div>
            </main>
        `;
    }

    private _renderGauge(nm: NeuromodulatorReading) {
        // Raw server number. The API sends no min/max/unit and no sync
        // timestamp — a percentage bar would invent a scale.
        return html`
            <div class="gauge-item">
                <div class="gauge-icon">
                    <span class="material-symbols-outlined">neurology</span>
                </div>
                <div class="gauge-name">${nm.name}</div>
                <div class="gauge-value">${nm.value}</div>
            </div>
        `;
    }

    /** AdaptationParams is an untyped dict on the server (cognitive.py:80)
     *  with no declared min/max/step. A range slider would invent a scale.
     *  A plain number input sends the raw value. */
    private _renderParamInput(
        key: keyof AdaptationParams,
        label: string,
        description: string
    ) {
        const value = this._params[key];

        return html`
            <div class="param-item">
                <div class="param-header">
                    <span class="param-label">${label}</span>
                    <span class="param-value">${value === undefined ? '—' : String(value)}</span>
                </div>
                <input
                    type="number"
                    class="param-slider"
                    .value=${value === undefined ? '' : String(value)}
                    @input=${(e: Event) => this._updateParam(key, parseFloat((e.target as HTMLInputElement).value))}
                >
                <span class="param-desc">${description}</span>
            </div>
        `;
    }

    private async _loadCognitiveState() {
        this._isLoading = true;
        this._loadFailed = false;
        try {
            // Real SomaBrain Cognitive API — agent-scoped state. The route
            // requires {agent_id}; without one we refuse rather than invent a
            // trailing-slash path the server does not serve.
            const agentId = this._agentId();
            if (!agentId) {
                this._brainConnected = false;
                this._neuromodulators = [];
                this._sleepState = null;
                this._activityLog = [
                    { message: 'No agent selected — cognitive state cannot be read.', time: new Date().toLocaleTimeString(), icon: 'block' },
                    ...this._activityLog,
                ];
                return;
            }
            // CognitiveStateResponse (admin/somabrain/cognitive.py:75-82):
            // {agent_id, neuromodulators: dict, adaptation_params: dict,
            //  memory_stats: dict, last_sleep, degraded}. No cognitiveLoad
            // field exists — a 0% load would be invented.
            const response = await apiClient.get(`/somabrain/cognitive/state/${agentId}`) as {
                neuromodulators?: Record<string, number>;
                adaptation_params?: AdaptationParams;
                memory_stats?: Record<string, number>;
                last_sleep?: string | null;
            } | null;
            this._brainConnected = response !== null && response !== undefined;
            if (response) {
                const neuro = response.neuromodulators;
                if (neuro && typeof neuro === 'object' && !Array.isArray(neuro)) {
                    this._neuromodulators = Object.entries(neuro).map(([name, value]) => ({
                        name,
                        value: Number(value),
                    }));
                } else {
                    this._neuromodulators = [];
                }
                if (response.adaptation_params) {
                    this._params = response.adaptation_params;
                }
            }
            await this._loadSleepState(agentId);
        } catch (error) {
            this._brainConnected = false;
            this._loadFailed = true;
            this._neuromodulators = [];
            this._logActivity(`Failed to load cognitive state: ${this._errorDetail(error)}`, 'error');
        } finally {
            this._isLoading = false;
        }
    }

    /** GET /somabrain/cognitive/sleep/status/{agent_id}
     *  (admin/somabrain/cognitive.py:388-416 → {is_sleeping, last_sleep,
     *  next_scheduled}). Failure is isolated from the state load above and
     *  surfaced in the activity log. */
    private async _loadSleepState(agentId: string) {
        try {
            const sleep = await apiClient.get(`/somabrain/cognitive/sleep/status/${agentId}`) as {
                is_sleeping?: boolean | null;
            } | null;
            this._sleepState = sleep && typeof sleep.is_sleeping === 'boolean' ? sleep.is_sleeping : null;
        } catch (error) {
            this._sleepState = null;
            this._logActivity(`Failed to load sleep status: ${this._errorDetail(error)}`, 'error');
        }
    }

    private _updateParam(key: keyof AdaptationParams, value: number) {
        this._params = { ...this._params, [key]: value };
        this._isDirty = true;
    }

    private async _saveParams() {
        const agentId = this._agentId();
        if (!agentId) {
            this._logActivity('No agent selected — parameters were not saved.', 'block');
            return;
        }
        this._isSaving = true;
        try {
            await apiClient.patch(`/somabrain/cognitive/params/${agentId}`, this._params);
            this._isDirty = false;
            this._activityLog = [
                { message: 'Parameters updated successfully', time: 'Just now', icon: 'check_circle' },
                ...this._activityLog,
            ];
        } catch (error) {
            this._logActivity(`Failed to save parameters: ${this._errorDetail(error)}`, 'error');
        } finally {
            this._isSaving = false;
        }
    }

    private async _triggerSleepCycle() {
        if (this._sleepTriggerInFlight) return;

        const agentId = this._agentId();
        if (!agentId) {
            this._logActivity('No agent selected — sleep cycle was not triggered.', 'block');
            return;
        }

        this._sleepTriggerInFlight = true;
        try {
            await apiClient.post(`/somabrain/cognitive/sleep/${agentId}`, {});
            this._activityLog = [
                { message: 'Sleep cycle initiated', time: 'Just now', icon: 'bedtime' },
                ...this._activityLog,
            ];
            this._sleepTriggerInFlight = false;
            await this._loadCognitiveState();
        } catch (error) {
            this._logActivity(`Failed to trigger sleep cycle: ${this._errorDetail(error)}`, 'error');
            this._sleepTriggerInFlight = false;
        }
    }

    private async _resetAdaptation() {
        const agentId = this._agentId();
        if (!agentId) {
            this._logActivity('No agent selected — adaptation was not reset.', 'block');
            return;
        }

        if (!confirm('Reset all adaptation parameters to defaults? This cannot be undone.')) {
            return;
        }

        try {
            await apiClient.post(`/somabrain/cognitive/adaptation/reset/${agentId}`, {});
            this._isDirty = false;
            this._activityLog = [
                { message: 'Adaptation parameters reset to defaults', time: 'Just now', icon: 'restart_alt' },
                ...this._activityLog,
            ];
            await this._loadCognitiveState();
        } catch (error) {
            this._logActivity(`Failed to reset adaptation: ${this._errorDetail(error)}`, 'error');
        }
    }

    private _handleCognitiveUpdate(data: unknown) {
        const update = data as { neuromodulators?: Record<string, number> };
        if (update.neuromodulators && typeof update.neuromodulators === 'object') {
            this._neuromodulators = Object.entries(update.neuromodulators).map(([name, value]) => ({
                name,
                value: Number(value),
            }));
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-cognitive-panel': SomaCognitivePanel;
    }
}
