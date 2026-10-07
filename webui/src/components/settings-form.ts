/**
 * Settings Form Component
 * Dynamic form generation from the server-owned field catalog.
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Permission-aware read/write modes
 * - Field catalog comes from GET /api/v2/core/settings/schema/{entity}
 * - Values come from GET /api/v2/core/settings/{entity}
 * - Light theme, minimal, professional
 * - Material Symbols icons
 *
 * Usage:
 * <settings-form
 *   entity="somabrain"
 *   .permissions=${['system:configure']}
 * />
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

// Field catalog entry as the server renders it (admin/core/api/settings_v2.py).
interface SchemaField {
  key: string;
  setting: string;
  label: string;
  type: string;
  editable: boolean;
  description?: string;
}

interface EntitySchema {
  entity: string;
  name: string;
  icon: string;
  fields: SchemaField[];
}

interface SettingsResponse {
  entity: string;
  values: Record<string, unknown>;
  source: string;
  last_modified?: string | null;
}

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
      background: var(--soma-bg-hover, #fafafa);
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
      color: var(--soma-text-muted, #999);
      font-size: 14px;
      margin: 0;
    }

    .form-card {
      background: var(--soma-bg-card, #ffffff);
      border: 1px solid var(--soma-border-light, #e0e0e0);
      border-radius: 12px;
      overflow: hidden;
    }

    .group-header {
      padding: 16px 24px;
      background: var(--soma-bg-hover, #fafafa);
      border-bottom: 1px solid var(--soma-border-light, #e0e0e0);
      font-weight: 600;
      font-size: 13px;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .group-header .material-symbols-outlined {
      font-size: 16px;
      color: var(--soma-text-secondary, #666);
    }

    .fields {
      padding: 24px;
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
      color: var(--soma-text-primary, #1a1a1a);
    }

    .field-label .required {
      color: var(--soma-status-danger, #ef4444);
      margin-left: 2px;
    }

    .field-description {
      font-size: 11px;
      color: var(--soma-text-muted, #999);
      margin-bottom: 6px;
    }

    input, select {
      width: 100%;
      padding: 10px 14px;
      border: 1px solid var(--soma-border-light, #e0e0e0);
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
      background: var(--soma-bg-hover, #fafafa);
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

    .form-actions {
      padding: 16px 24px;
      border-top: 1px solid var(--soma-border-light, #e0e0e0);
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
      border: 1px solid var(--soma-border-light, #e0e0e0);
      background: var(--soma-bg-card, #ffffff);
      color: var(--soma-text-primary, #1a1a1a);
    }

    .btn:hover {
      background: var(--soma-bg-hover, #fafafa);
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
      background: var(--soma-bg-hover, #fafafa);
      border-top: 1px solid var(--soma-border-light, #e0e0e0);
      font-size: 12px;
      color: var(--soma-text-muted, #999);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .loading {
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 60px;
      color: var(--soma-text-muted, #999);
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

  @property({ type: String }) entity = 'somabrain';
  @property({ type: String, attribute: 'schema-url' }) schemaUrl = '';
  @property({ type: String, attribute: 'values-url' }) valuesUrl = '';
  @property({ type: Array }) permissions: string[] = [];

  @state() private schema: EntitySchema | null = null;
  @state() private values: Record<string, unknown> = {};
  @state() private loading = true;
  @state() private saving = false;
  @state() private successMessage = '';
  @state() private errorMessage = '';
  @state() private dirty = false;

  async connectedCallback() {
    super.connectedCallback();
    await this.loadData();
  }

  private get canEdit(): boolean {
    // Exact catalog names only. The old form accepted `settings:edit`,
    // `settings:write`, a constructed `<entity>:configure` and `*`. None of
    // those are permissions this product defines, and `*` would have granted
    // edit on every settings screen to anyone whose permission list contained
    // a single wildcard.
    return this.permissions.includes('system:configure');
  }

  private async loadData() {
    this.loading = true;
    this.errorMessage = '';

    const effectiveSchemaUrl =
      this.schemaUrl || `/api/v2/core/settings/schema/${this.entity}`;
    try {
      const res = await fetch(effectiveSchemaUrl, { credentials: 'include' });
      if (res.ok) {
        this.schema = (await res.json()) as EntitySchema;
      } else {
        this.errorMessage = `Failed to load the field catalog (HTTP ${res.status})`;
      }
    } catch (err) {
      console.error(`Failed to load schema from ${effectiveSchemaUrl}:`, err);
      this.errorMessage = 'Failed to load the field catalog from the server';
    }

    const effectiveValuesUrl =
      this.valuesUrl || `/api/v2/core/settings/${this.entity}`;
    try {
      const res = await fetch(effectiveValuesUrl, { credentials: 'include' });
      if (res.ok) {
        const parsed = (await res.json()) as SettingsResponse &
          Record<string, unknown>;
        if (
          parsed &&
          typeof parsed === 'object' &&
          parsed.values &&
          typeof parsed.values === 'object'
        ) {
          this.values = { ...(parsed.values as Record<string, unknown>) };
        } else {
          this.values = { ...(parsed as Record<string, unknown>) };
        }
      } else {
        this.errorMessage = `Failed to load settings (HTTP ${res.status})`;
      }
    } catch (err) {
      console.error(`Failed to load values from ${effectiveValuesUrl}:`, err);
      this.errorMessage = 'Failed to load settings from the server';
    }

    this.loading = false;
  }

  private handleFieldChange(key: string, value: unknown) {
    this.values = { ...this.values, [key]: value };
    this.dirty = true;
    this.successMessage = '';
    this.errorMessage = '';
  }

  private async saveSettings() {
    if (!this.canEdit) return;

    this.saving = true;
    this.errorMessage = '';

    const effectiveValuesUrl =
      this.valuesUrl || `/api/v2/core/settings/${this.entity}`;

    try {
      const res = await fetch(effectiveValuesUrl, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ values: this.values }),
      });

      if (res.ok) {
        this.successMessage = 'Settings saved successfully';
        this.dirty = false;
      } else {
        const error = await res.json().catch(() => ({ detail: 'Save failed' }));
        this.errorMessage = error.detail || 'Failed to save settings';
      }
    } catch (err) {
      this.errorMessage = 'Network error occurred';
      console.error('Save settings error:', err);
    } finally {
      this.saving = false;
    }
  }

  private revertChanges() {
    this.loadData();
    this.dirty = false;
    this.successMessage = '';
    this.errorMessage = '';
  }

  render() {
    if (this.loading) {
      return html`<div class="loading">Loading settings...</div>`;
    }

    if (!this.schema) {
      return html`<div class="loading">No field catalog for ${this.entity}</div>`;
    }

    return html`
      <div class="header">
        <h2 class="title">
          <span class="title-icon">
            <span class="material-symbols-outlined">${this.schema.icon}</span>
          </span>
          ${this.schema.name}
        </h2>
      </div>

      ${this.successMessage
        ? html`
            <div class="success-message">
              <span class="material-symbols-outlined">check_circle</span>
              ${this.successMessage}
            </div>
          `
        : nothing}

      ${this.errorMessage
        ? html`
            <div class="error-message">
              <span class="material-symbols-outlined">error</span>
              ${this.errorMessage}
            </div>
          `
        : nothing}

      <div class="form-card">
        <div class="fields">
          ${this.schema.fields.map((field) => this.renderField(field))}
        </div>

        ${this.canEdit
          ? html`
              <div class="form-actions">
                <button
                  class="btn"
                  ?disabled=${!this.dirty}
                  @click=${() => this.revertChanges()}
                >
                  Revert
                </button>
                <button
                  class="btn primary"
                  ?disabled=${!this.dirty || this.saving}
                  @click=${() => this.saveSettings()}
                >
                  ${this.saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            `
          : html`
              <div class="read-only-notice">
                <span class="material-symbols-outlined">lock</span>
                You don't have permission to edit these settings
              </div>
            `}
      </div>
    `;
  }

  private renderField(field: SchemaField) {
    const raw = this.values[field.key];
    const value = raw === undefined || raw === null ? '' : raw;
    const disabled = !this.canEdit || !field.editable;

    return html`
      <div class="field">
        <label class="field-label"> ${field.label} </label>
        ${field.description
          ? html`<div class="field-description">${field.description}</div>`
          : nothing}
        ${!field.editable
          ? html`<div class="field-description">Deployment topology — changes
              with a deploy, not a request.</div>`
          : nothing}
        ${this.renderFieldInput(field, value, disabled)}
      </div>
    `;
  }

  private renderFieldInput(field: SchemaField, value: unknown, disabled: boolean) {
    const text = value === undefined || value === null ? '' : String(value);

    switch (field.type) {
      case 'boolean':
        return html`
          <div class="toggle-row">
            <div
              class="toggle ${value ? 'active' : ''}"
              @click=${() =>
                !disabled && this.handleFieldChange(field.key, !value)}
            >
              <div class="toggle-knob"></div>
            </div>
            <span class="toggle-label">${value ? 'Enabled' : 'Disabled'}</span>
          </div>
        `;

      case 'integer':
      case 'number':
        return html`
          <input
            type="number"
            .value=${text}
            ?disabled=${disabled}
            @input=${(e: InputEvent) =>
              this.handleFieldChange(
                field.key,
                Number((e.target as HTMLInputElement).value)
              )}
          />
        `;

      case 'url':
        return html`
          <input
            type="url"
            .value=${text}
            ?disabled=${disabled}
            @input=${(e: InputEvent) =>
              this.handleFieldChange(
                field.key,
                (e.target as HTMLInputElement).value
              )}
          />
        `;

      default:
        return html`
          <input
            type="text"
            .value=${text}
            ?disabled=${disabled}
            @input=${(e: InputEvent) =>
              this.handleFieldChange(
                field.key,
                (e.target as HTMLInputElement).value
              )}
          />
        `;
    }
  }
}

// Guard against double registration (barrel re-exports can cause this)
if (!customElements.get('settings-form')) {
  customElements.define('settings-form', SettingsForm);
}

declare global {
  interface HTMLElementTagNameMap {
    'settings-form': SettingsForm;
  }
}
