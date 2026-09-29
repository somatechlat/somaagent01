/**
 * Tenant Settings Controller
 * Manages data loading, mutation, and save logic for the tenant settings view.
 */

import { apiClient } from '../services/api-client.js';

/**
 * Mirrors `TenantOut` — every field here is one the API actually returns.
 *
 * `TenantOut` is: id, name, slug, status, tier, created_at, agents, users,
 * mrr, email. `TenantUpdate` accepts only: name, status, tier.
 *
 * A previous version of this shape also carried `branding`, `security` and
 * `featureOverrides`, and filled them with invented defaults (`#2563eb`,
 * `mfaRequired: false`, `sessionTimeout: 30`). No endpoint stores any of
 * that, so the tabs that edited it silently discarded the changes on save.
 * They are gone rather than faked.
 */
export interface TenantQuota {
  used: number;
  /** Null when the API reports no quota ceiling for this resource. */
  limit: number | null;
}

export interface TenantSettings {
  id: string;
  name: string;
  slug: string;
  /** Tenant billing contact. Null when the tenant has none on record. */
  billingEmail: string | null;
  tier: {
    id: string;
    name: string;
    slug: string;
  };
  status: 'active' | 'suspended' | 'pending';
  /** The tenant's real monthly recurring revenue, in dollars. */
  mrr: number;
  quotas: {
    agents: TenantQuota;
    users: TenantQuota;
  };
}

export type SettingsTab = 'general' | 'danger';

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
        mrr?: number;
        email?: string | null;
      }>(`/aaas/tenants/${tenant.id}`);

      this._settings = {
        id: data.id,
        name: data.name,
        slug: data.slug,
        // TenantOut.email — the real billing contact, or null when absent.
        billingEmail: data.email ?? null,
        tier: { id: data.tier, name: data.tier, slug: data.tier },
        status: data.status,
        mrr: data.mrr ?? 0,
        // TenantOut carries the counts but no per-resource ceilings. `limit`
        // is null, not 0: a ceiling of 0 would render as "3/0" and a quota bar
        // that divides by zero. The view draws no bar for an unknown limit.
        quotas: {
          agents: { used: data.agents ?? 0, limit: null },
          users: { used: data.users ?? 0, limit: null },
        },
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
        // Sent only when the operator actually set one: `email: null` would
        // mean "clear the contact" and an empty string is not a contact.
        ...(this._settings.billingEmail ? { email: this._settings.billingEmail } : {}),
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
