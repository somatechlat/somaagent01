/**
 * SAAS Settings Field
 * Renders an individual settings form field based on its schema type.
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { SchemaField } from '../controllers/settings-form-controller.js';

@customElement('saas-settings-field')
export class SaasSettingsField extends LitElement {
  static styles = css`
    :host {
      display: block;
    }

    .field {
      margin-bottom: 20px;
    }

    .field:last-child {
      margin-bottom: 0;
    }

    .field-label {
      display: block;
      font-size: 13px;
      font-weight: 500;
      margin-bottom: 6px;
      color: var(--saas-text-primary, #1a1a1a);
    }

    .field-label .required {
      color: var(--saas-status-danger, #ef4444);
      margin-left: 2px;
    }

    .field-description {
      font-size: 11px;
      color: var(--saas-text-muted, #999);
      margin-bottom: 6px;
    }

    input, select {
      width: 100%;
      padding: 10px 14px;
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: 8px;
      font-size: 14px;
      outline: none;
      transition: border-color 0.15s ease;
      box-sizing: border-box;
    }

    input:focus, select:focus {
      border-color: #1a1a1a;
    }

    input:disabled, select:disabled {
      background: var(--saas-bg-hover, #fafafa);
      cursor: not-allowed;
    }

    input[type="password"] {
      font-family: monospace;
    }

    .toggle-row {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .toggle {
      position: relative;
      width: 44px;
      height: 24px;
      background: #e0e0e0;
      border-radius: 12px;
      cursor: pointer;
      transition: background 0.2s ease;
    }

    .toggle.active {
      background: #1a1a1a;
    }

    .toggle-knob {
      position: absolute;
      top: 2px;
      left: 2px;
      width: 20px;
      height: 20px;
      background: white;
      border-radius: 50%;
      transition: transform 0.2s ease;
      box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }

    .toggle.active .toggle-knob {
      transform: translateX(20px);
    }

    .toggle-label {
      font-size: 14px;
    }
  `;

  @property({ type: Object }) field!: SchemaField;
  @property() value: unknown = '';
  @property({ type: Boolean }) disabled = false;

  private _emitChange(value: unknown) {
    this.dispatchEvent(new CustomEvent('saas-field-change', {
      detail: { key: this.field.key, value },
      bubbles: true,
      composed: true
    }));
  }

  render() {
    const value = this.value ?? this.field.default ?? '';

    return html`
      <div class="field">
        <label class="field-label">
          ${this.field.label}
          ${this.field.required ? html`<span class="required">*</span>` : nothing}
        </label>
        ${this.field.description ? html`
          <div class="field-description">${this.field.description}</div>
        ` : nothing}
        ${this._renderInput(value)}
      </div>
    `;
  }

  private _renderInput(value: unknown) {
    switch (this.field.type) {
      case 'boolean':
        return html`
          <div class="toggle-row">
            <div
              class="toggle ${value ? 'active' : ''}"
              @click=${() => !this.disabled && this._emitChange(!value)}
            >
              <div class="toggle-knob"></div>
            </div>
            <span class="toggle-label">${value ? 'Enabled' : 'Disabled'}</span>
          </div>
        `;

      case 'enum':
        return html`
          <select
            .value=${String(value)}
            ?disabled=${this.disabled}
            @change=${(e: Event) => this._emitChange((e.target as HTMLSelectElement).value)}
          >
            ${this.field.options?.map(opt => html`
              <option value=${opt.value} ?selected=${value === opt.value}>${opt.label}</option>
            `)}
          </select>
        `;

      case 'number':
        return html`
          <input
            type="number"
            .value=${String(value)}
            ?disabled=${this.disabled}
            min=${this.field.min ?? ''}
            max=${this.field.max ?? ''}
            placeholder=${this.field.placeholder ?? ''}
            @input=${(e: InputEvent) => this._emitChange(Number((e.target as HTMLInputElement).value))}
          />
        `;

      case 'secret':
        return html`
          <input
            type="password"
            .value=${String(value)}
            ?disabled=${this.disabled}
            placeholder=${this.field.placeholder ?? '••••••••'}
            @input=${(e: InputEvent) => this._emitChange((e.target as HTMLInputElement).value)}
          />
        `;

      case 'url':
      case 'email':
        return html`
          <input
            type=${this.field.type}
            .value=${String(value)}
            ?disabled=${this.disabled}
            placeholder=${this.field.placeholder ?? ''}
            @input=${(e: InputEvent) => this._emitChange((e.target as HTMLInputElement).value)}
          />
        `;

      default: // string
        return html`
          <input
            type="text"
            .value=${String(value)}
            ?disabled=${this.disabled}
            placeholder=${this.field.placeholder ?? ''}
            @input=${(e: InputEvent) => this._emitChange((e.target as HTMLInputElement).value)}
          />
        `;
    }
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'saas-settings-field': SaasSettingsField;
  }
}
