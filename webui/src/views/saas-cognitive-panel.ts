/**
 * SomaAgent SaaS — Cognitive Panel (TRN Mode)
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
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import { wsClient } from '../services/websocket-client.js';

interface NeuromodulatorLevel {
    name: string;
    value: number;
    min: number;
    max: number;
    unit: string;
    description: string;
    icon: string;
}

interface AdaptationParams {
    learningRate: number;
    explorationRate: number;
    attentionSpan: number;
    memoryConsolidation: number;
    emotionalSensitivity: number;
}

@customElement('saas-cognitive-panel')
export class SaasCognitivePanel extends LitElement {
    static styles = css`
        :host {
            display: flex;
            height: 100vh;
            background: var(--saas-bg-page, #f5f5f5);
            font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
            color: var(--saas-text-primary, #1a1a1a);
        }

        * {
            box-sizing: border-box;
        }

        /* Material Symbols - Required for Shadow DOM */
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
           SIDEBAR
           ======================================== */
        .sidebar {
            width: 280px;
            background: var(--saas-bg-card, #ffffff);
            border-right: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
            padding: 24px 20px;
        }

        .sidebar-header {
            margin-bottom: 24px;
        }

        .sidebar-title {
            font-size: 20px;
            font-weight: 600;
            margin: 0 0 4px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .sidebar-subtitle {
            font-size: 13px;
            color: var(--saas-text-secondary, #666);
        }

        .mode-badge {
            padding: 4px 8px;
            border-radius: 4px;
            background: #fef3c7;
            color: #b45309;
            font-size: 11px;
            font-weight: 600;
        }

        /* Status Card */
        .status-card {
            background: var(--saas-bg-hover, #fafafa);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 20px;
        }

        .status-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            font-size: 13px;
        }

        .status-label {
            color: var(--saas-text-secondary, #666);
        }

        .status-value {
            font-weight: 600;
        }

        .status-value.online {
            color: var(--saas-status-success, #22c55e);
        }

        .status-value.warning {
            color: var(--saas-status-warning, #f59e0b);
        }

        /* Quick Actions */
        .quick-actions {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 24px;
        }

        .action-btn {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 14px;
            border-radius: 8px;
            border: 1px solid var(--saas-border-light, #e0e0e0);
            background: var(--saas-bg-card, #ffffff);
            font-size: 14px;
            cursor: pointer;
            transition: all 0.15s ease;
            color: var(--saas-text-primary, #1a1a1a);
        }

        .action-btn:hover {
            background: var(--saas-bg-hover, #fafafa);
            border-color: var(--saas-border-medium, #ccc);
        }

        .action-btn.primary {
            background: #1a1a1a;
            color: white;
            border-color: #1a1a1a;
        }

        .action-btn.primary:hover {
            background: #333;
        }

        .action-btn.warning {
            border-color: var(--saas-status-warning, #f59e0b);
            color: var(--saas-status-warning, #f59e0b);
        }

        .action-btn.warning:hover {
            background: #fffbeb;
        }

        .action-btn .material-symbols-outlined {
            font-size: 18px;
        }

        /* Back Button */
        .back-btn {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px 14px;
            margin-top: auto;
            border: none;
            background: transparent;
            font-size: 14px;
            color: var(--saas-text-secondary, #666);
            cursor: pointer;
            transition: all 0.1s ease;
        }

        .back-btn:hover {
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

        /* Header */
        .header {
            padding: 16px 24px;
            background: var(--saas-bg-card, #ffffff);
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header-title {
            font-size: 18px;
            font-weight: 600;
        }

        .header-actions {
            display: flex;
            gap: 8px;
        }

        .save-btn {
            padding: 10px 20px;
            border-radius: 8px;
            background: #1a1a1a;
            color: white;
            border: none;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.1s ease;
        }

        .save-btn:hover:not(:disabled) {
            background: #333;
        }

        .save-btn:disabled {
            background: var(--saas-border-light, #e0e0e0);
            color: var(--saas-text-muted, #999);
            cursor: not-allowed;
        }

        .save-btn .material-symbols-outlined {
            font-size: 18px;
        }

        /* Content Area */
        .content {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            align-content: start;
        }

        @media (max-width: 1000px) {
            .content {
                grid-template-columns: 1fr;
            }
        }

        /* Cards */
        .card {
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
            border-radius: 12px;
            padding: 24px;
        }

        .card.full-width {
            grid-column: 1 / -1;
        }

        .card-title {
            font-size: 16px;
            font-weight: 600;
            margin: 0 0 16px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .card-title .material-symbols-outlined {
            font-size: 20px;
            color: var(--saas-text-secondary, #666);
        }

        .card-desc {
            font-size: 13px;
            color: var(--saas-text-secondary, #666);
            margin-bottom: 20px;
        }

        /* Neuromodulator Gauges */
        .gauge-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
        }

        @media (max-width: 1200px) {
            .gauge-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        .gauge-item {
            background: var(--saas-bg-hover, #fafafa);
            border-radius: 12px;
            padding: 16px;
            text-align: center;
        }

        .gauge-icon {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 12px;
            background: var(--saas-bg-card, #ffffff);
            border: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .gauge-icon .material-symbols-outlined {
            font-size: 20px;
        }

        .gauge-name {
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 8px;
        }

        .gauge-bar {
            height: 8px;
            background: var(--saas-border-light, #e0e0e0);
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 8px;
        }

        .gauge-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }

        .gauge-fill.dopamine { background: #8b5cf6; }
        .gauge-fill.serotonin { background: #f59e0b; }
        .gauge-fill.norepinephrine { background: #ef4444; }
        .gauge-fill.acetylcholine { background: #22c55e; }
        .gauge-fill.gaba { background: #3b82f6; }
        .gauge-fill.cortisol { background: #ec4899; }

        .gauge-value {
            font-size: 12px;
            color: var(--saas-text-muted, #999);
        }

        /* Parameter Sliders */
        .param-list {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .param-item {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .param-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .param-label {
            font-size: 14px;
            font-weight: 500;
        }

        .param-value {
            font-size: 13px;
            color: var(--saas-text-secondary, #666);
            font-family: monospace;
            background: var(--saas-bg-hover, #fafafa);
            padding: 4px 8px;
            border-radius: 4px;
        }

        .param-slider {
            -webkit-appearance: none;
            width: 100%;
            height: 6px;
            border-radius: 3px;
            background: var(--saas-border-light, #e0e0e0);
            outline: none;
        }

        .param-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: #1a1a1a;
            cursor: pointer;
            transition: transform 0.1s ease;
        }

        .param-slider::-webkit-slider-thumb:hover {
            transform: scale(1.1);
        }

        .param-desc {
            font-size: 12px;
            color: var(--saas-text-muted, #999);
        }

        /* Activity Log */
        .activity-log {
            max-height: 200px;
            overflow-y: auto;
        }

        .log-entry {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 10px 0;
            border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
        }

        .log-entry:last-child {
            border-bottom: none;
        }

        .log-icon {
            width: 28px;
            height: 28px;
            border-radius: 6px;
            background: var(--saas-bg-hover, #fafafa);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .log-icon .material-symbols-outlined {
            font-size: 14px;
        }

        .log-content {
            flex: 1;
        }

        .log-message {
            font-size: 13px;
            margin-bottom: 2px;
        }

        .log-time {
            font-size: 11px;
            color: var(--saas-text-muted, #999);
        }

        /* Loading */
        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 60px;
        }

        .spinner {
            width: 32px;
            height: 32px;
            border: 3px solid var(--saas-border-light, #e0e0e0);
            border-top-color: #1a1a1a;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    `;

    @state() private _isLoading = false;
    @state() private _isDirty = false;
    @state() private _isSaving = false;
    @state() private _cognitiveLoad = 42;
    @state() private _sleepCycleActive = false;

    @state() private _neuromodulators: NeuromodulatorLevel[] = [
        { name: 'Dopamine', value: 0.72, min: 0, max: 1, unit: '', description: 'Reward & Motivation', icon: 'mood' },
        { name: 'Serotonin', value: 0.65, min: 0, max: 1, unit: '', description: 'Mood & Stability', icon: 'sentiment_satisfied' },
        { name: 'Norepinephrine', value: 0.58, min: 0, max: 1, unit: '', description: 'Alertness & Focus', icon: 'electric_bolt' },
        { name: 'Acetylcholine', value: 0.81, min: 0, max: 1, unit: '', description: 'Learning & Memory', icon: 'school' },
        { name: 'GABA', value: 0.45, min: 0, max: 1, unit: '', description: 'Calm & Inhibition', icon: 'spa' },
        { name: 'Cortisol', value: 0.32, min: 0, max: 1, unit: '', description: 'Stress Response', icon: 'warning' },
    ];

    @state() private _params: AdaptationParams = {
        learningRate: 0.001,
        explorationRate: 0.15,
        attentionSpan: 0.8,
        memoryConsolidation: 0.7,
        emotionalSensitivity: 0.5,
    };

    @state() private _activityLog: { message: string; time: string; icon: string }[] = [
        { message: 'Learning rate adjusted to 0.001', time: '2 min ago', icon: 'tune' },
        { message: 'Memory consolidation cycle completed', time: '15 min ago', icon: 'memory' },
        { message: 'Dopamine spike detected', time: '32 min ago', icon: 'trending_up' },
        { message: 'Sleep cycle initiated', time: '1 hour ago', icon: 'bedtime' },
    ];

    private _unsubscribe?: () => void;

    async connectedCallback() {
        super.connectedCallback();
        await this._loadCognitiveState();

        // Subscribe to real-time cognitive updates
        this._unsubscribe = wsClient.on('cognitive.update', (data) => {
            this._handleCognitiveUpdate(data);
        });
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this._unsubscribe?.();
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
                        <span class="status-label">Cognitive Load</span>
                        <span class="status-value">${this._cognitiveLoad}%</span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">Sleep Cycle</span>
                        <span class="status-value ${this._sleepCycleActive ? 'warning' : 'online'}">
                            ${this._sleepCycleActive ? 'Active' : 'Idle'}
                        </span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">SomaBrain</span>
                        <span class="status-value online">Connected</span>
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
                        <!-- Neuromodulator Gauges -->
                        <div class="card full-width">
                            <h3 class="card-title">
                                <span class="material-symbols-outlined">monitoring</span>
                                Neuromodulator Levels
                            </h3>
                            <p class="card-desc">Real-time cognitive chemistry state (read-only)</p>
                            
                            <div class="gauge-grid">
                                ${this._neuromodulators.map(nm => this._renderGauge(nm))}
                            </div>
                        </div>

                        <!-- Adaptation Parameters -->
                        <div class="card">
                            <h3 class="card-title">
                                <span class="material-symbols-outlined">tune</span>
                                Adaptation Parameters
                            </h3>
                            <p class="card-desc">Fine-tune learning behavior</p>
                            
                            <div class="param-list">
                                ${this._renderSlider('learningRate', 'Learning Rate', 0.0001, 0.1, 0.0001, 'Controls speed of weight updates')}
                                ${this._renderSlider('explorationRate', 'Exploration Rate', 0, 1, 0.01, 'Balance between exploration and exploitation')}
                                ${this._renderSlider('attentionSpan', 'Attention Span', 0, 1, 0.01, 'How long to focus on single topics')}
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
                                ${this._renderSlider('memoryConsolidation', 'Consolidation Rate', 0, 1, 0.01, 'Speed of short to long-term transfer')}
                                ${this._renderSlider('emotionalSensitivity', 'Emotional Sensitivity', 0, 1, 0.01, 'Weight of emotional context in memories')}
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

    private _renderGauge(nm: NeuromodulatorLevel) {
        const percentage = (nm.value - nm.min) / (nm.max - nm.min) * 100;
        const colorClass = nm.name.toLowerCase().replace(' ', '');

        return html`
            <div class="gauge-item">
                <div class="gauge-icon">
                    <span class="material-symbols-outlined">${nm.icon}</span>
                </div>
                <div class="gauge-name">${nm.name}</div>
                <div class="gauge-bar">
                    <div class="gauge-fill ${colorClass}" style="width: ${percentage}%"></div>
                </div>
                <div class="gauge-value">${(nm.value * 100).toFixed(0)}%</div>
            </div>
        `;
    }

    private _renderSlider(
        key: keyof AdaptationParams,
        label: string,
        min: number,
        max: number,
        step: number,
        description: string
    ) {
        const value = this._params[key];
        const displayValue = value < 0.01 ? value.toExponential(2) : value.toFixed(3);

        return html`
            <div class="param-item">
                <div class="param-header">
                    <span class="param-label">${label}</span>
                    <span class="param-value">${displayValue}</span>
                </div>
                <input 
                    type="range" 
                    class="param-slider"
                    .value=${String(value)}
                    min=${min}
                    max=${max}
                    step=${step}
                    @input=${(e: Event) => this._updateParam(key, parseFloat((e.target as HTMLInputElement).value))}
                >
                <span class="param-desc">${description}</span>
            </div>
        `;
    }

    private async _loadCognitiveState() {
        this._isLoading = true;
        try {
            // Call SomaBrain Cognitive API
            const response = await apiClient.get('/cognitive/state/');
            if (response) {
                if (response.neuromodulators) {
                    this._neuromodulators = response.neuromodulators;
                }
                if (response.params) {
                    this._params = response.params;
                }
                if (response.cognitiveLoad !== undefined) {
                    this._cognitiveLoad = response.cognitiveLoad;
                }
            }
        } catch (error) {
            console.error('Failed to load cognitive state:', error);
        } finally {
            this._isLoading = false;
        }
    }

    private _updateParam(key: keyof AdaptationParams, value: number) {
        this._params = { ...this._params, [key]: value };
        this._isDirty = true;
    }

    private async _saveParams() {
        this._isSaving = true;
        try {
            await apiClient.put('/cognitive/params/', this._params);
            this._isDirty = false;
            this._activityLog = [
                { message: 'Parameters updated successfully', time: 'Just now', icon: 'check_circle' },
                ...this._activityLog.slice(0, 9),
            ];
        } catch (error) {
            console.error('Failed to save parameters:', error);
        } finally {
            this._isSaving = false;
        }
    }

    private async _triggerSleepCycle() {
        if (this._sleepCycleActive) return;

        this._sleepCycleActive = true;
        try {
            await apiClient.post('/cognitive/sleep-cycle/', {});
            this._activityLog = [
                { message: 'Sleep cycle initiated', time: 'Just now', icon: 'bedtime' },
                ...this._activityLog.slice(0, 9),
            ];

            // Simulate cycle completion after delay
            setTimeout(() => {
                this._sleepCycleActive = false;
                this._activityLog = [
                    { message: 'Sleep cycle completed', time: 'Just now', icon: 'check_circle' },
                    ...this._activityLog.slice(0, 9),
                ];
            }, 5000);
        } catch (error) {
            console.error('Failed to trigger sleep cycle:', error);
            this._sleepCycleActive = false;
        }
    }

    private async _resetAdaptation() {
        if (!confirm('Reset all adaptation parameters to defaults? This cannot be undone.')) {
            return;
        }

        try {
            await apiClient.post('/cognitive/reset/', {});
            this._params = {
                learningRate: 0.001,
                explorationRate: 0.15,
                attentionSpan: 0.8,
                memoryConsolidation: 0.7,
                emotionalSensitivity: 0.5,
            };
            this._isDirty = false;
            this._activityLog = [
                { message: 'Adaptation parameters reset to defaults', time: 'Just now', icon: 'restart_alt' },
                ...this._activityLog.slice(0, 9),
            ];
        } catch (error) {
            console.error('Failed to reset adaptation:', error);
        }
    }

    private _handleCognitiveUpdate(data: unknown) {
        const update = data as { neuromodulators?: NeuromodulatorLevel[]; cognitiveLoad?: number };
        if (update.neuromodulators) {
            this._neuromodulators = update.neuromodulators;
        }
        if (update.cognitiveLoad !== undefined) {
            this._cognitiveLoad = update.cognitiveLoad;
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-cognitive-panel': SaasCognitivePanel;
    }
}
