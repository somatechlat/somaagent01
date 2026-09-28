/**
 * Tenant Settings Controller
 * Manages data loading, mutation, and save logic for the tenant settings view.
 */

import { apiClient } from '../services/api-client.js';

export interface TenantSettings {
  id: string;
  name: string;
  slug: string;
  logoUrl?: string;
  billingEmail: string;
  tier: {
    id: string;
    name: string;
    slug: string;
  };
  status: 'active' | 'suspended' | 'pending';
  quotas: {
    agents: { used: number; limit: number };
    users: { used: number; limit: number };
    storage: { used: number; limit: number };
  };
  branding: {
    primaryColor: string;
    accentColor: string;
    customDomain?: string;
  };
  security: {
    mfaRequired: boolean;
    ssoEnabled: boolean;
    ssoProvider?: string;
    sessionTimeout: number;
  };
  featureOverrides: Record<string, boolean>;
}

export type SettingsTab = 'general' | 'branding' | 'security' | 'features' | 'danger';

export interface TenantSettingsHost {
  requestUpdate(): void;
  dispatchEvent(event: Event): boolean;
}

export class TenantSettingsController {
  private _host: TenantSettingsHost;
  private _settings: TenantSettings | null = null;
  private _tenantId = '';
  private _loading = true;
  private _saving = false;
  private _dirty = false;

  constructor(host: TenantSettingsHost) {
    this._host = host;
  }

  get settings(): TenantSettings | null {
    return this._settings;
  }

  get tenantId(): string {
    return this._tenantId;
  }

  get loading(): boolean {
    return this._loading;
  }

  get saving(): boolean {
    return this._saving;
  }

  get dirty(): boolean {
    return this._dirty;
  }

  async loadSettings(): Promise<void> {
    this._loading = true;
    this._host.requestUpdate();
    try {
      const listData = await apiClient.get<{ items?: Array<{ id: string }> }>(
        '/aaas/tenants?page=1&per_page=1'
      );
      const tenant = listData.items?.[0];
      if (!tenant) {
        throw new Error('No tenant found');
      }
      this._tenantId = tenant.id;

      const data = await apiClient.get<{
        id: string;
        name: string;
        slug: string;
        tier: string;
        status: 'active' | 'suspended' | 'pending';
        agents?: number;
        users?: number;
      }>(`/aaas/tenants/${tenant.id}`);

      this._settings = {
        id: data.id,
        name: data.name,
        slug: data.slug,
        billingEmail: '',
        tier: { id: data.tier, name: data.tier, slug: data.tier },
        status: data.status,
        quotas: {
          agents: { used: data.agents || 0, limit: 0 },
          users: { used: data.users || 0, limit: 0 },
          storage: { used: 0, limit: 0 },
        },
        branding: { primaryColor: '#2563eb', accentColor: '#3b82f6' },
        security: { mfaRequired: false, ssoEnabled: false, sessionTimeout: 30 },
        featureOverrides: {},
      };
      this._dirty = false;
    } catch (e) {
      console.error('Failed to load settings:', e);
      this._settings = null;
    } finally {
      this._loading = false;
      this._host.requestUpdate();
    }
  }

  updateSetting(path: string, value: unknown): void {
    if (!this._settings) return;
    this._settings = this._setPath(this._settings, path, value);
    this._dirty = true;
    this._host.requestUpdate();
  }

  async saveSettings(): Promise<void> {
    if (!this._settings || !this._tenantId) return;
    this._saving = true;
    this._host.requestUpdate();
    try {
      const payload = {
        name: this._settings.name,
        status: this._settings.status,
        tier: this._settings.tier.slug,
      };
      await apiClient.patch(`/aaas/tenants/${this._tenantId}`, payload);
      this._dirty = false;
      this._host.dispatchEvent(
        new CustomEvent('show-toast', {
          detail: { type: 'success', message: 'Settings saved successfully' },
          bubbles: true,
          composed: true,
        })
      );
    } catch (e) {
      console.error('Failed to save:', e);
    } finally {
      this._saving = false;
      this._host.requestUpdate();
    }
  }

  private _setPath<T>(obj: T, path: string, value: unknown): T {
    const parts = path.split('.');
    const clone: unknown = { ...obj };
    let current: any = clone;
    for (let i = 0; i < parts.length - 1; i++) {
      const key = parts[i];
      current[key] = { ...current[key] };
      current = current[key];
    }
    current[parts[parts.length - 1]] = value;
    return clone as T;
  }
}
