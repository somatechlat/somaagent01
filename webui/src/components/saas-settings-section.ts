/**
 * SAAS Settings Section
 * Renders a grouped section of settings fields.
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import type { SchemaField, SettingsSchemaGroup } from '../controllers/settings-form-controller.js';
import './saas-settings-field.js';

@customElement('saas-settings-section')
export class SaasSettingsSection extends LitElement {
  static styles = css`
    :host {
      display: block;
    }

    .group-header {
      padding: 16px 24px;
      background: var(--saas-bg-hover, #fafafa);
      border-bottom: 1px solid var(--saas-border-light, #e0e0e0);
      font-weight: 600;
      font-size: 13px;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .group-header .material-symbols-outlined {
      font-family: 'Material Symbols Outlined';
      font-size: 16px;
      line-height: 1;
      color: var(--saas-text-secondary, #666);
      -webkit-font-smoothing: antialiased;
    }

    .fields {
      padding: 24px;
    }
  `;

  @property({ type: Object }) group!: SettingsSchemaGroup;
  @property({ type: Array }) fields: SchemaField[] = [];
  @property({ type: Object }) values: Record<string, unknown> = {};
  @property({ type: Boolean }) disabled = false;
  @property({ type: Boolean, attribute: 'show-header' }) showHeader = false;

  render() {
    if (this.fields.length === 0) {
      return nothing;
    }

    return html`
      ${this.showHeader ? html`
        <div class="group-header">
          ${this.group.icon ? html`<span class="material-symbols-outlined">${this.group.icon}</span>` : nothing}
          ${this.group.label}
        </div>
      ` : nothing}
      <div class="fields">
        ${this.fields.map(field => html`
          <saas-settings-field
            .field=${field}
            .value=${this.values[field.key]}
            ?disabled=${this.disabled}
          ></saas-settings-field>
        `)}
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'saas-settings-section': SaasSettingsSection;
  }
}
