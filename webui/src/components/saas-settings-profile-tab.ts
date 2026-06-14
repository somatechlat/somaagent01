/**
 * Settings Profile Tab
 * Agent model and memory configuration.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { ModelConfig } from '../controllers/settings-controller.js';

export interface ChatModelChangeDetail {
  field: keyof ModelConfig;
  value: string | number;
}

export interface UtilityModelChangeDetail {
  field: keyof ModelConfig;
  value: string | number;
}

@customElement('saas-settings-profile-tab')
export class SaasSettingsProfileTab extends LitElement {
  static styles = css`
    :host {
      display: block;
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

    .section {
      background: var(--saas-bg-card, #ffffff);
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 20px;
    }

    .section-title {
      font-size: 16px;
      font-weight: 600;
      margin: 0 0 16px 0;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .section-title .material-symbols-outlined {
      font-size: 20px;
      color: var(--saas-text-secondary, #666);
    }

    .section-desc {
      font-size: 13px;
      color: var(--saas-text-secondary, #666);
      margin-bottom: 20px;
    }

    .settings-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 20px;
    }

    @media (max-width: 800px) {
      .settings-grid {
        grid-template-columns: 1fr;
      }
    }

    .form-group {
      margin-bottom: 20px;
    }

    .form-group:last-child {
      margin-bottom: 0;
    }

    .form-label {
      display: block;
      font-size: 13px;
      font-weight: 500;
      margin-bottom: 8px;
      color: var(--saas-text-primary, #1a1a1a);
    }

    .form-input,
    .form-select {
      width: 100%;
      padding: 10px 14px;
      border-radius: 8px;
      border: 1px solid var(--saas-border-light, #e0e0e0);
      font-size: 14px;
      background: var(--saas-bg-card, #ffffff);
      color: var(--saas-text-primary, #1a1a1a);
      transition: border-color 0.15s ease;
    }

    .form-input:focus,
    .form-select:focus {
      outline: none;
      border-color: var(--saas-text-primary, #1a1a1a);
    }

    .form-hint {
      font-size: 12px;
      color: var(--saas-text-muted, #999);
      margin-top: 6px;
    }
  `;

  @property({ type: Object })
  chatModel!: ModelConfig;

  @property({ type: Object })
  utilityModel!: ModelConfig;

  render() {
    return html`
      <!-- Chat Model -->
      <div class="section">
        <h3 class="section-title">
          <span class="material-symbols-outlined">chat</span>
          Chat Model
        </h3>
        <p class="section-desc">Primary model for conversations and complex tasks.</p>

        <div class="settings-grid">
          <div class="form-group">
            <label class="form-label">Provider</label>
            <select
              class="form-select"
              .value=${this.chatModel.provider}
              @change=${(e: Event) => this._emitChatChange('provider', (e.target as HTMLSelectElement).value)}
            >
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="google">Google AI</option>
              <option value="ollama">Ollama (Local)</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Model</label>
            <select
              class="form-select"
              .value=${this.chatModel.model}
              @change=${(e: Event) => this._emitChatChange('model', (e.target as HTMLSelectElement).value)}
            >
              <option value="gpt-4-turbo">GPT-4 Turbo</option>
              <option value="gpt-4o">GPT-4o</option>
              <option value="claude-3-opus">Claude 3 Opus</option>
              <option value="claude-3-sonnet">Claude 3 Sonnet</option>
              <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Context Window</label>
            <input
              type="number"
              class="form-input"
              .value=${String(this.chatModel.contextWindow)}
              @input=${(e: Event) => this._emitChatChange('contextWindow', parseInt((e.target as HTMLInputElement).value))}
            />
            <p class="form-hint">Maximum tokens for context</p>
          </div>
          <div class="form-group">
            <label class="form-label">Max Output Tokens</label>
            <input
              type="number"
              class="form-input"
              .value=${String(this.chatModel.maxTokens)}
              @input=${(e: Event) => this._emitChatChange('maxTokens', parseInt((e.target as HTMLInputElement).value))}
            />
            <p class="form-hint">Maximum tokens per response</p>
          </div>
        </div>
      </div>

      <!-- Utility Model -->
      <div class="section">
        <h3 class="section-title">
          <span class="material-symbols-outlined">build</span>
          Utility Model
        </h3>
        <p class="section-desc">Lightweight model for quick tasks and summarization.</p>

        <div class="settings-grid">
          <div class="form-group">
            <label class="form-label">Provider</label>
            <select
              class="form-select"
              .value=${this.utilityModel.provider}
              @change=${(e: Event) => this._emitUtilityChange('provider', (e.target as HTMLSelectElement).value)}
            >
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="google">Google AI</option>
              <option value="ollama">Ollama (Local)</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Model</label>
            <select
              class="form-select"
              .value=${this.utilityModel.model}
              @change=${(e: Event) => this._emitUtilityChange('model', (e.target as HTMLSelectElement).value)}
            >
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              <option value="gpt-4o-mini">GPT-4o Mini</option>
              <option value="claude-3-haiku">Claude 3 Haiku</option>
              <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Memory Settings -->
      <div class="section">
        <h3 class="section-title">
          <span class="material-symbols-outlined">psychology</span>
          Memory / SomaBrain
        </h3>
        <p class="section-desc">Configure agent memory and knowledge base.</p>

        <div class="settings-grid">
          <div class="form-group">
            <label class="form-label">SomaBrain URL</label>
            <input type="text" class="form-input" value="http://localhost:9696" readonly />
          </div>
          <div class="form-group">
            <label class="form-label">Collection</label>
            <input type="text" class="form-input" value="default" />
          </div>
        </div>
      </div>
    `;
  }

  private _emitChatChange(field: keyof ModelConfig, value: string | number): void {
    this.dispatchEvent(
      new CustomEvent<ChatModelChangeDetail>('chat-model-change', {
        detail: { field, value },
        bubbles: true,
        composed: true,
      })
    );
  }

  private _emitUtilityChange(field: keyof ModelConfig, value: string | number): void {
    this.dispatchEvent(
      new CustomEvent<UtilityModelChangeDetail>('utility-model-change', {
        detail: { field, value },
        bubbles: true,
        composed: true,
      })
    );
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'saas-settings-profile-tab': SaasSettingsProfileTab;
  }
}
