/**
 * SaaS Cognitive — Training Panel
 * Renders adaptation parameter controls for cognitive training.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { AdaptationParams, ParamChangeDetail } from '../controllers/cognitive-panel-controller.js';

@customElement('saas-cognitive-training-panel')
export class SaasCognitiveTrainingPanel extends LitElement {
  static styles = css`
    :host {
      display: block;
      height: 100%;
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
      height: 100%;
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
  `;

  @property({ type: Object })
  params: AdaptationParams = {
    learningRate: 0.001,
    explorationRate: 0.15,
    attentionSpan: 0.8,
    memoryConsolidation: 0.7,
    emotionalSensitivity: 0.5,
  };

  @property({ type: Boolean })
  isDirty = false;

  @property({ type: Boolean })
  isSaving = false;

  render() {
    return html`
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
    const value = this.params[key];
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
          @input=${(e: Event) => this._emitChange(key, parseFloat((e.target as HTMLInputElement).value))}
        />
        <span class="param-desc">${description}</span>
      </div>
    `;
  }

  private _emitChange(key: keyof AdaptationParams, value: number) {
    this.dispatchEvent(
      new CustomEvent<ParamChangeDetail>('param-change', {
        detail: { key, value },
        bubbles: true,
        composed: true,
      })
    );
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'saas-cognitive-training-panel': SaasCognitiveTrainingPanel;
  }
}
