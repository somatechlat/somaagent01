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

// JSON Schema field definition
interface SchemaField {
  key: string;
  label: string;
  type: 'string' | 'number' | 'boolean' | 'enum' | 'secret' | 'url' | 'email';
  description?: string;
  required?: boolean;
  default?: unknown;
  min?: number;
  max?: number;
  options?: { value: string; label: string }[];  // For enum type
  placeholder?: string;
  group?: string;  // For grouping fields
}

interface SettingsSchema {
  title: string;
  description?: string;
  icon: string;
  fields: SchemaField[];
  groups?: { key: string; label: string; icon?: string }[];
}

// Common settings schemas (built-in)
const BUILTIN_SCHEMAS: Record<string, SettingsSchema> = {
  postgresql: {
    title: 'PostgreSQL Configuration',
    description: 'Primary database connection settings',
    icon: 'database',
    groups: [
      { key: 'connection', label: 'Connection', icon: 'link' },
      { key: 'pool', label: 'Connection Pool', icon: 'hub' },
    ],
    fields: [
      { key: 'host', label: 'Host', type: 'string', required: true, group: 'connection', placeholder: 'localhost' },
      { key: 'port', label: 'Port', type: 'number', required: true, group: 'connection', default: 5432, min: 1, max: 65535 },
      { key: 'database', label: 'Database', type: 'string', required: true, group: 'connection' },
      { key: 'user', label: 'Username', type: 'string', required: true, group: 'connection' },
      { key: 'password', label: 'Password', type: 'secret', required: true, group: 'connection' },
      { key: 'pool_size', label: 'Pool Size', type: 'number', group: 'pool', default: 20, min: 1, max: 100 },
      { key: 'max_overflow', label: 'Max Overflow', type: 'number', group: 'pool', default: 10, min: 0, max: 50 },
      { key: 'timeout', label: 'Connection Timeout (s)', type: 'number', group: 'pool', default: 30, min: 5, max: 120 },
    ],
  },
  redis: {
    title: 'Redis Configuration',
    description: 'Cache and session storage settings',
    icon: 'bolt',
    fields: [
      { key: 'url', label: 'Redis URL', type: 'url', required: true, placeholder: 'redis://localhost:6379' },
      { key: 'max_connections', label: 'Max Connections', type: 'number', default: 100, min: 10, max: 500 },
      { key: 'ttl_default', label: 'Default TTL (s)', type: 'number', default: 3600, min: 60, max: 86400 },
    ],
  },
  kafka: {
    title: 'Kafka Configuration',
    description: 'Event streaming settings',
    icon: 'mail',
    fields: [
      { key: 'brokers', label: 'Bootstrap Servers', type: 'string', required: true, placeholder: 'localhost:9092' },
      { key: 'group_id', label: 'Consumer Group ID', type: 'string', default: 'somaagent-group' },
      {
        key: 'auto_offset_reset', label: 'Auto Offset Reset', type: 'enum', options: [
          { value: 'earliest', label: 'Earliest' },
          { value: 'latest', label: 'Latest' },
        ], default: 'latest'
      },
    ],
  },
  temporal: {
    title: 'Temporal Configuration',
    description: 'Workflow orchestration settings',
    icon: 'schedule',
    fields: [
      { key: 'host', label: 'Temporal Host', type: 'string', required: true, placeholder: 'temporal:7233' },
      { key: 'namespace', label: 'Namespace', type: 'string', default: 'default' },
      { key: 'task_queue', label: 'Task Queue', type: 'string', default: 'saas-tasks' },
      { key: 'workflow_timeout', label: 'Workflow Timeout (s)', type: 'number', default: 3600 },
      { key: 'activity_timeout', label: 'Activity Timeout (s)', type: 'number', default: 300 },
      { key: 'retry_max', label: 'Max Retries', type: 'number', default: 3, min: 0, max: 10 },
    ],
  },
  keycloak: {
    title: 'Keycloak Configuration',
    description: 'Authentication and SSO settings',
    icon: 'lock',
    fields: [
      { key: 'url', label: 'Keycloak URL', type: 'url', required: true },
      { key: 'realm', label: 'Realm', type: 'string', required: true, default: 'master' },
      { key: 'client_id', label: 'Client ID', type: 'string', required: true },
      { key: 'client_secret', label: 'Client Secret', type: 'secret', required: true },
    ],
  },
  somabrain: {
    title: 'SomaBrain Configuration',
    description: 'Cognitive memory service settings',
    icon: 'neurology',
    fields: [
      { key: 'url', label: 'SomaBrain URL', type: 'url', required: true },
      { key: 'retention_days', label: 'Memory Retention (days)', type: 'number', default: 365, min: 30, max: 730 },
      { key: 'sleep_interval', label: 'Sleep Cycle Interval (s)', type: 'number', default: 21600 },
      { key: 'consolidation_enabled', label: 'Enable Consolidation', type: 'boolean', default: true },
    ],
  },
  voice: {
    title: 'Voice Services Configuration',
    description: 'Speech-to-Text and Text-to-Speech settings',
    icon: 'mic',
    groups: [
      { key: 'stt', label: 'Speech-to-Text', icon: 'hearing' },
      { key: 'tts', label: 'Text-to-Speech', icon: 'volume_up' },
    ],
    fields: [
      { key: 'whisper_url', label: 'Whisper URL', type: 'url', group: 'stt' },
      {
        key: 'whisper_model', label: 'Whisper Model', type: 'enum', group: 'stt', options: [
          { value: 'tiny', label: 'Tiny (fast)' },
          { value: 'base', label: 'Base' },
          { value: 'small', label: 'Small' },
          { value: 'medium', label: 'Medium' },
          { value: 'large', label: 'Large (best)' },
        ], default: 'base'
      },
      { key: 'kokoro_url', label: 'Kokoro URL', type: 'url', group: 'tts' },
      { key: 'kokoro_voice', label: 'Default Voice', type: 'string', group: 'tts', default: 'af_nicole' },
    ],
  },
};

@customElement('settings-form')
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
      font-size: 16px;
      color: var(--saas-text-secondary, #666);
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

  @state() private schema: SettingsSchema | null = null;
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
    return this.permissions.includes('settings:edit') ||
      this.permissions.includes('settings:write') ||
      this.permissions.includes(`${this.entity}:configure`) ||
      this.permissions.includes('*');
  }

  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('auth_token') || localStorage.getItem('saas_auth_token');
    return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
  }

  private async loadData() {
    this.loading = true;

    // Load schema (from URL or builtin)
    if (this.schemaUrl) {
      try {
        const res = await fetch(this.schemaUrl, { headers: this.getAuthHeaders() });
        if (res.ok) {
          this.schema = await res.json();
        }
      } catch (err) {
        console.error(`Failed to load schema from ${this.schemaUrl}:`, err);
      }
    }

    // Fall back to builtin schema
    if (!this.schema && BUILTIN_SCHEMAS[this.entity]) {
      this.schema = BUILTIN_SCHEMAS[this.entity];
    }

    // Load values
    const effectiveValuesUrl = this.valuesUrl || `/api/v2/settings/${this.entity}`;
    try {
      const res = await fetch(effectiveValuesUrl, { headers: this.getAuthHeaders() });
      if (res.ok) {
        this.values = await res.json();
      }
    } catch (err) {
      console.error(`Failed to load values from ${effectiveValuesUrl}:`, err);
      // Initialize with defaults from schema
      if (this.schema) {
        this.values = {};
        for (const field of this.schema.fields) {
          if (field.default !== undefined) {
            this.values[field.key] = field.default;
          }
        }
      }
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

    const effectiveValuesUrl = this.valuesUrl || `/api/v2/settings/${this.entity}`;

    try {
      const res = await fetch(effectiveValuesUrl, {
        method: 'PUT',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(this.values),
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
      return html`<div class="loading">No schema available for ${this.entity}</div>`;
    }

    const groups = this.schema.groups || [{ key: 'default', label: 'Settings' }];
    const fieldsByGroup: Record<string, SchemaField[]> = {};

    for (const field of this.schema.fields) {
      const groupKey = field.group || 'default';
      if (!fieldsByGroup[groupKey]) fieldsByGroup[groupKey] = [];
      fieldsByGroup[groupKey].push(field);
    }

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

      <div class="form-card">
        ${groups.map(group => {
      const fields = fieldsByGroup[group.key] || [];
      if (fields.length === 0) return nothing;

      return html`
            ${groups.length > 1 ? html`
              <div class="group-header">
                ${group.icon ? html`<span class="material-symbols-outlined">${group.icon}</span>` : nothing}
                ${group.label}
              </div>
            ` : nothing}
            <div class="fields">
              ${fields.map(field => this.renderField(field))}
            </div>
          `;
    })}

        ${this.canEdit ? html`
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
        ` : html`
          <div class="read-only-notice">
            <span class="material-symbols-outlined">lock</span>
            You don't have permission to edit these settings
          </div>
        `}
      </div>
    `;
  }

  private renderField(field: SchemaField) {
    const value = this.values[field.key] ?? field.default ?? '';

    return html`
      <div class="field">
        <label class="field-label">
          ${field.label}
          ${field.required ? html`<span class="required">*</span>` : nothing}
        </label>
        ${field.description ? html`
          <div class="field-description">${field.description}</div>
        ` : nothing}
        ${this.renderFieldInput(field, value)}
      </div>
    `;
  }

  private renderFieldInput(field: SchemaField, value: unknown) {
    const disabled = !this.canEdit;

    switch (field.type) {
      case 'boolean':
        return html`
          <div class="toggle-row">
            <div 
              class="toggle ${value ? 'active' : ''}"
              @click=${() => !disabled && this.handleFieldChange(field.key, !value)}
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
            ?disabled=${disabled}
            @change=${(e: Event) => this.handleFieldChange(field.key, (e.target as HTMLSelectElement).value)}
          >
            ${field.options?.map(opt => html`
              <option value=${opt.value} ?selected=${value === opt.value}>${opt.label}</option>
            `)}
          </select>
        `;

      case 'number':
        return html`
          <input 
            type="number"
            .value=${String(value)}
            ?disabled=${disabled}
            min=${field.min ?? ''}
            max=${field.max ?? ''}
            placeholder=${field.placeholder ?? ''}
            @input=${(e: InputEvent) => this.handleFieldChange(field.key, Number((e.target as HTMLInputElement).value))}
          />
        `;

      case 'secret':
        return html`
          <input 
            type="password"
            .value=${String(value)}
            ?disabled=${disabled}
            placeholder=${field.placeholder ?? '••••••••'}
            @input=${(e: InputEvent) => this.handleFieldChange(field.key, (e.target as HTMLInputElement).value)}
          />
        `;

      case 'url':
      case 'email':
        return html`
          <input 
            type=${field.type}
            .value=${String(value)}
            ?disabled=${disabled}
            placeholder=${field.placeholder ?? ''}
            @input=${(e: InputEvent) => this.handleFieldChange(field.key, (e.target as HTMLInputElement).value)}
          />
        `;

      default: // string
        return html`
          <input 
            type="text"
            .value=${String(value)}
            ?disabled=${disabled}
            placeholder=${field.placeholder ?? ''}
            @input=${(e: InputEvent) => this.handleFieldChange(field.key, (e.target as HTMLInputElement).value)}
          />
        `;
    }
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'settings-form': SettingsForm;
  }
}
