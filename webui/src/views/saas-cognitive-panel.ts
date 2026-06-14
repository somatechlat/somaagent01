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
 * Layout shell that hosts the training, memory, and evaluation sub-panels.
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import {
  CognitivePanelController,
  type NeuromodulatorLevel,
  type AdaptationParams,
  type ActivityLogEntry,
  type ParamChangeDetail,
} from '../controllers/cognitive-panel-controller.js';
import '../components/saas-cognitive-training-panel.js';
import '../components/saas-cognitive-memory-panel.js';
import '../components/saas-cognitive-evaluation-panel.js';

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

    .main {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

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

    .loading {
      grid-column: 1 / -1;
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

    .empty-state {
      grid-column: 1 / -1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 40px;
    }

    .empty-icon {
      width: 64px;
      height: 64px;
      background: var(--saas-bg-hover, #fafafa);
      border-radius: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 20px;
    }

    .empty-icon .material-symbols-outlined {
      font-size: 28px;
      color: var(--saas-text-secondary, #666);
    }

    .empty-title {
      font-size: 18px;
      font-weight: 600;
      margin-bottom: 8px;
    }

    .empty-desc {
      font-size: 14px;
      color: var(--saas-text-secondary, #666);
      max-width: 320px;
    }
  `;

  private _controller = new CognitivePanelController();

  @state() private _agentId = '';
  @state() private _isLoading = false;
  @state() private _isDirty = false;
  @state() private _isSaving = false;
  @state() private _cognitiveLoad = 0;
  @state() private _sleepCycleActive = false;
  @state() private _loadError = '';
  @state() private _neuromodulators: NeuromodulatorLevel[] = [];
  @state() private _params: AdaptationParams = this._controller.defaultParams();
  @state() private _activityLog: ActivityLogEntry[] = [];

  async connectedCallback() {
    super.connectedCallback();
    this._agentId = this._controller.parseAgentId();
    if (this._agentId) {
      sessionStorage.setItem('cognitive_agent_id', this._agentId);
      await this._loadCognitiveState();
    } else {
      this._loadError = 'No agent selected. Open /cognitive?agent=AGENT_ID';
    }
  }

  render() {
    return html`
      <aside class="sidebar">
        <div class="sidebar-header">
          <h1 class="sidebar-title">
            <span class="material-symbols-outlined">neurology</span>
            Cognitive
            <span class="mode-badge">TRN</span>
          </h1>
          <p class="sidebar-subtitle">Training Mode Controls</p>
        </div>

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

        <button class="back-btn" @click=${() => (window.location.href = '/chat')}>
          <span class="material-symbols-outlined">arrow_back</span> Back to Chat
        </button>
      </aside>

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
          ${this._loadError
            ? html`
                <div class="empty-state">
                  <div class="empty-icon"><span class="material-symbols-outlined">error</span></div>
                  <div class="empty-title">Unable to load cognitive panel</div>
                  <div class="empty-desc">${this._loadError}</div>
                </div>
              `
            : this._isLoading
              ? html`<div class="loading"><div class="spinner"></div></div>`
              : html`
                  <saas-cognitive-evaluation-panel
                    .neuromodulators=${this._neuromodulators}
                    .cognitiveLoad=${this._cognitiveLoad}
                    .activityLog=${this._activityLog}
                  ></saas-cognitive-evaluation-panel>

                  <saas-cognitive-training-panel
                    .params=${this._params}
                    .isDirty=${this._isDirty}
                    .isSaving=${this._isSaving}
                    @param-change=${(e: CustomEvent<ParamChangeDetail>) =>
                      this._updateParam(e.detail.key, e.detail.value)}
                  ></saas-cognitive-training-panel>

                  <saas-cognitive-memory-panel
                    .params=${this._params}
                    .sleepCycleActive=${this._sleepCycleActive}
                    @param-change=${(e: CustomEvent<ParamChangeDetail>) =>
                      this._updateParam(e.detail.key, e.detail.value)}
                  ></saas-cognitive-memory-panel>
                `}
        </div>
      </main>
    `;
  }

  private _updateParam(key: keyof AdaptationParams, value: number) {
    this._params = { ...this._params, [key]: value };
    this._isDirty = true;
  }

  private async _loadCognitiveState() {
    this._isLoading = true;
    try {
      const state = await this._controller.loadState(this._agentId);
      this._neuromodulators = state.neuromodulators;
      this._params = state.params;
      this._cognitiveLoad = state.cognitiveLoad;
      this._sleepCycleActive = state.sleepCycleActive;
      this._activityLog = [];
    } catch (error) {
      console.error('Failed to load cognitive state:', error);
      this._loadError = 'Failed to load cognitive state from SomaBrain';
    } finally {
      this._isLoading = false;
    }
  }

  private async _saveParams() {
    if (!this._agentId) return;
    this._isSaving = true;
    try {
      await this._controller.saveParams(this._agentId, this._params);
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
    if (!this._agentId || this._sleepCycleActive) return;

    this._sleepCycleActive = true;
    try {
      const response = await this._controller.triggerSleepCycle(this._agentId);
      this._activityLog = [
        { message: `Sleep cycle ${response.status || 'initiated'}`, time: 'Just now', icon: 'bedtime' },
        ...this._activityLog.slice(0, 9),
      ];
      if (response.status === 'completed') {
        this._sleepCycleActive = false;
      }
    } catch (error) {
      console.error('Failed to trigger sleep cycle:', error);
      this._sleepCycleActive = false;
    }
  }

  private async _resetAdaptation() {
    if (
      !this._agentId ||
      !confirm('Reset all adaptation parameters to defaults? This cannot be undone.')
    ) {
      return;
    }

    try {
      this._params = await this._controller.resetAdaptation(this._agentId);
      this._isDirty = false;
      this._activityLog = [
        { message: 'Adaptation parameters reset to defaults', time: 'Just now', icon: 'restart_alt' },
        ...this._activityLog.slice(0, 9),
      ];
    } catch (error) {
      console.error('Failed to reset adaptation:', error);
    }
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'saas-cognitive-panel': SaasCognitivePanel;
  }
}
