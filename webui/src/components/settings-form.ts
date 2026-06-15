/**
 * Settings Form Component
 * Dynamic form generation from JSON Schema
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Permission-aware read/write modes
 * - JSON Schema driven form fields
 * - Light theme, minimal, professional
 * - Material Symbols icons
 *
 * Usage:
 * <settings-form
 *   entity="postgresql"
 *   schema-url="/api/v2/schemas/postgresql"
 *   values-url="/api/v2/settings/postgresql"
 *   .permissions=${['settings:edit']}
 * />
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { SettingsFormController, type SettingsSchema, type SchemaField } from '../controllers/settings-form-controller.js';
import './saas-settings-section.js';

export class SettingsForm extends LitElement {
  static styles = css`
    :host {
      display: block;
    }

    .header {
      margin-bottom: 24px;
    }

    .title {
      font-size: 20px;
      font-weight: 600;
      margin: 0 0 8px 0;
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .title-icon {
      width: 36px;
      height: 36px;
      background: var(--saas-bg-hover, #fafafa);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .material-symbols-outlined {
      font-family: 'Material Symbols Outlined';
      font-weight: normal;
      font-style: normal;
      font-size: 20px;
      line-height: 1;
      display: inline-block;
      -webkit-font-smoothing: antialiased;
    }

    .description {
      color: var(--saas-text-muted, #999);
      font-size: 14px;
      margin: 0;
    }

    .form-card {
      background: var(--saas-bg-card, #ffffff);
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: 12px;
      overflow: hidden;
    }

    .form-actions {
      padding: 16px 24px;
      border-top: 1px solid var(--saas-border-light, #e0e0e0);
      display: flex;
      justify-content: flex-end;
      gap: 12px;
    }

    .btn {
      padding: 10px 20px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.1s ease;
      border: 1px solid var(--saas-border-light, #e0e0e0);
      background: var(--saas-bg-card, #ffffff);
      color: var(--saas-text-primary, #1a1a1a);
    }

    .btn:hover {
      background: var(--saas-bg-hover, #fafafa);
    }

    .btn.primary {
      background: #1a1a1a;
      color: white;
      border-color: #1a1a1a;
    }

    .btn.primary:hover {
      background: #333;
    }

    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .read-only-notice {
      padding: 12px 24px;
      background: var(--saas-bg-hover, #fafafa);
      border-top: 1px solid var(--saas-border-light, #e0e0e0);
      font-size: 12px;
      color: var(--saas-text-muted, #999);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .loading {
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 60px;
      color: var(--saas-text-muted, #999);
    }

    .success-message {
      padding: 12px 16px;
      background: rgba(34, 197, 94, 0.1);
      border: 1px solid rgba(34, 197, 94, 0.3);
      border-radius: 8px;
      color: #16a34a;
      font-size: 13px;
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .error-message {
      padding: 12px 16px;
      background: rgba(239, 68, 68, 0.1);
      border: 1px solid rgba(239, 68, 68, 0.3);
      border-radius: 8px;
      color: #dc2626;
      font-size: 13px;
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
  `;

  @property({ type: String }) entity = 'postgresql';
  @property({ type: String, attribute: 'schema-url' }) schemaUrl = '';
  @property({ type: String, attribute: 'values-url' }) valuesUrl = '';
  @property({ type: Array }) permissions: string[] = [];

  @state() schema: SettingsSchema | null = null;
  @state() values: Record<string, unknown> = {};
  @state() loading = true;
  @state() saving = false;
  @state() successMessage = '';
  @state() errorMessage = '';
  @state() dirty = false;

  private controller = new SettingsFormController(this);

  get canEdit(): boolean {
    return this.controller.canEdit;
  }

  async connectedCallback() {
    super.connectedCallback();
    await this.controller.loadData();
  }

  render() {
    if (this.loading) {
      return html`<div class="loading">Loading settings...</div>`;
    }

    if (!this.schema) {
      return html`<div class="loading">No schema available for ${this.entity}</div>`;
    }

    const groups = this.schema.groups || [{ key: 'default', label: 'Settings' }];
    const fieldsByGroup = this._groupFields(this.schema.fields);
    const disabled = !this.canEdit;

    return html`
      <div class="header">
        <h2 class="title">
          <span class="title-icon">
            <span class="material-symbols-outlined">${this.schema.icon}</span>
          </span>
          ${this.schema.title}
        </h2>
        ${this.schema.description ? html`
          <p class="description">${this.schema.description}</p>
        ` : nothing}
      </div>

      ${this.successMessage ? html`
        <div class="success-message">
          <span class="material-symbols-outlined">check_circle</span>
          ${this.successMessage}
        </div>
      ` : nothing}

      ${this.errorMessage ? html`
        <div class="error-message">
          <span class="material-symbols-outlined">error</span>
          ${this.errorMessage}
        </div>
      ` : nothing}

      <div class="form-card" @saas-field-change=${this._handleFieldChange}>
        ${groups.map(group => {
          const fields = fieldsByGroup[group.key] || [];
          if (fields.length === 0) return nothing;

          return html`
            <saas-settings-section
              .group=${group}
              .fields=${fields}
              .values=${this.values}
              ?disabled=${disabled}
              ?show-header=${groups.length > 1}
            ></saas-settings-section>
          `;
        })}

        ${this.canEdit ? html`
          <div class="form-actions">
            <button
              class="btn"
              ?disabled=${!this.dirty}
              @click=${() => this.controller.revertChanges()}
            >
              Revert
            </button>
            <button
              class="btn primary"
              ?disabled=${!this.dirty || this.saving}
              @click=${() => this.controller.saveSettings()}
            >
              ${this.saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        ` : html`
          <div class="read-only-notice">
            <span class="material-symbols-outlined">lock</span>
            You don't have permission to edit these settings
          </div>
        `}
      </div>
    `;
  }

  private _groupFields(fields: SchemaField[]): Record<string, SchemaField[]> {
    const result: Record<string, SchemaField[]> = {};

    for (const field of fields) {
      const groupKey = field.group || 'default';
      if (!result[groupKey]) result[groupKey] = [];
      result[groupKey].push(field);
    }

    return result;
  }

  private _handleFieldChange(e: CustomEvent) {
    const { key, value } = e.detail as { key: string; value: unknown };
    this.controller.handleFieldChange(key, value);
  }
}

// Backward-compatible alias for the original tag used by routes and consumers.
if (!customElements.get('settings-form')) {
  customElements.define('settings-form', SettingsForm);
}

declare global {
  interface HTMLElementTagNameMap {
    'settings-form': SettingsForm;
  }
}
