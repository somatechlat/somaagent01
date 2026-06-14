/**
 * Settings Form Controller
 *
 * Manages validation, dirty state, and submission for the settings form.
 * Hosts a SettingsForm component and delegates data/logic to this controller.
 */

// JSON Schema field definition
export interface SchemaField {
  key: string;
  label: string;
  type: 'string' | 'number' | 'boolean' | 'enum' | 'secret' | 'url' | 'email';
  description?: string;
  required?: boolean;
  default?: unknown;
  min?: number;
  max?: number;
  options?: { value: string; label: string }[];
  placeholder?: string;
  group?: string;
}

export interface SettingsSchemaGroup {
  key: string;
  label: string;
  icon?: string;
}

export interface SettingsSchema {
  title: string;
  description?: string;
  icon: string;
  fields: SchemaField[];
  groups?: SettingsSchemaGroup[];
}

export interface SettingsFormHost {
  entity: string;
  schemaUrl: string;
  valuesUrl: string;
  permissions: string[];
  schema: SettingsSchema | null;
  values: Record<string, unknown>;
  loading: boolean;
  saving: boolean;
  successMessage: string;
  errorMessage: string;
  dirty: boolean;
  requestUpdate(): void;
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

export class SettingsFormController {
  constructor(private host: SettingsFormHost) {}

  get canEdit(): boolean {
    return this.host.permissions.includes('settings:edit') ||
      this.host.permissions.includes('settings:write') ||
      this.host.permissions.includes(`${this.host.entity}:configure`) ||
      this.host.permissions.includes('*');
  }

  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('auth_token') || localStorage.getItem('saas_auth_token');
    return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
  }

  async loadData(): Promise<void> {
    this.host.loading = true;
    this.host.requestUpdate();

    // Load schema (from URL or builtin)
    if (this.host.schemaUrl) {
      try {
        const res = await fetch(this.host.schemaUrl, { headers: this.getAuthHeaders() });
        if (res.ok) {
          this.host.schema = await res.json();
        }
      } catch (err) {
        console.error(`Failed to load schema from ${this.host.schemaUrl}:`, err);
      }
    }

    // Fall back to builtin schema
    if (!this.host.schema && BUILTIN_SCHEMAS[this.host.entity]) {
      this.host.schema = BUILTIN_SCHEMAS[this.host.entity];
    }

    // Load values
    const effectiveValuesUrl = this.host.valuesUrl || `/api/v2/settings/${this.host.entity}`;
    try {
      const res = await fetch(effectiveValuesUrl, { headers: this.getAuthHeaders() });
      if (res.ok) {
        this.host.values = await res.json();
      }
    } catch (err) {
      console.error(`Failed to load values from ${effectiveValuesUrl}:`, err);
      // Initialize with defaults from schema
      if (this.host.schema) {
        this.host.values = {};
        for (const field of this.host.schema.fields) {
          if (field.default !== undefined) {
            this.host.values[field.key] = field.default;
          }
        }
      }
    }

    this.host.loading = false;
    this.host.dirty = false;
    this.host.successMessage = '';
    this.host.errorMessage = '';
    this.host.requestUpdate();
  }

  handleFieldChange(key: string, value: unknown): void {
    this.host.values = { ...this.host.values, [key]: value };
    this.host.dirty = true;
    this.host.successMessage = '';
    this.host.errorMessage = '';
    this.host.requestUpdate();
  }

  validate(): Record<string, string> {
    const errors: Record<string, string> = {};
    if (!this.host.schema) return errors;

    for (const field of this.host.schema.fields) {
      if (!field.required) continue;
      const value = this.host.values[field.key];
      if (value === undefined || value === '' || value === null) {
        errors[field.key] = `${field.label} is required`;
      }
    }

    return errors;
  }

  async saveSettings(): Promise<void> {
    if (!this.canEdit) return;

    this.host.saving = true;
    this.host.errorMessage = '';
    this.host.requestUpdate();

    const effectiveValuesUrl = this.host.valuesUrl || `/api/v2/settings/${this.host.entity}`;

    try {
      const res = await fetch(effectiveValuesUrl, {
        method: 'PUT',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(this.host.values),
      });

      if (res.ok) {
        this.host.successMessage = 'Settings saved successfully';
        this.host.dirty = false;
      } else {
        const error = await res.json().catch(() => ({ detail: 'Save failed' }));
        this.host.errorMessage = error.detail || 'Failed to save settings';
      }
    } catch (err) {
      this.host.errorMessage = 'Network error occurred';
      console.error('Save settings error:', err);
    } finally {
      this.host.saving = false;
      this.host.requestUpdate();
    }
  }

  revertChanges(): void {
    this.loadData();
  }
}
