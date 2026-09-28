/**
 * SaaS Cognitive — Evaluation Panel
 * Renders neuromodulator metrics and activity log.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { NeuromodulatorLevel, ActivityLogEntry } from '../controllers/cognitive-panel-controller.js';

@customElement('saas-cognitive-evaluation-panel')
export class SaasCognitiveEvaluationPanel extends LitElement {
  static styles = css`
    :host {
      display: block;
      grid-column: 1 / -1;
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

    .card {
      background: var(--saas-bg-card, #ffffff);
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 20px;
    }

    .card:last-child {
      margin-bottom: 0;
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

    @media (max-width: 600px) {
      .gauge-grid {
        grid-template-columns: 1fr;
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
  `;

  @property({ type: Array })
  neuromodulators: NeuromodulatorLevel[] = [];

  @property({ type: Number })
  cognitiveLoad = 0;

  @property({ type: Array })
  activityLog: ActivityLogEntry[] = [];

  render() {
    return html`
      <div class="card">
        <h3 class="card-title">
          <span class="material-symbols-outlined">monitoring</span>
          Neuromodulator Levels
        </h3>
        <p class="card-desc">Real-time cognitive chemistry state (read-only)</p>

        <div class="gauge-grid">
          ${this.neuromodulators.map((nm) => this._renderGauge(nm))}
        </div>
      </div>

      <div class="card">
        <h3 class="card-title">
          <span class="material-symbols-outlined">history</span>
          Activity Log
        </h3>

        <div class="activity-log">
          ${this.activityLog.map(
            (entry) => html`
              <div class="log-entry">
                <div class="log-icon">
                  <span class="material-symbols-outlined">${entry.icon}</span>
                </div>
                <div class="log-content">
                  <div class="log-message">${entry.message}</div>
                  <div class="log-time">${entry.time}</div>
                </div>
              </div>
            `
          )}
        </div>
      </div>
    `;
  }

  private _renderGauge(nm: NeuromodulatorLevel) {
    const percentage = ((nm.value - nm.min) / (nm.max - nm.min)) * 100;
    const colorClass = nm.name.toLowerCase().replace(/\s+/g, '');

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
}

declare global {
  interface HTMLElementTagNameMap {
    'saas-cognitive-evaluation-panel': SaasCognitiveEvaluationPanel;
  }
}
