/**
 * Tenant Settings Controller
 * Manages data loading, mutation, and save logic for the tenant settings view.
 */

import { apiClient } from '../services/api-client.js';

/**
 * Mirrors `TenantOut` — every field here is one the API actually returns.
 *
 * `TenantOut` is: id, name, slug, status, tier, created_at, agents, users,
 * mrr, email. `TenantUpdate` accepts: name, status, tier, email.
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

/** One selectable plan from `GET /aaas/tiers` (`SubscriptionTierOut`). */
export interface TierOption {
  /** SubscriptionTier UUID — what `UpgradeRequest.new_tier_id` needs. */
  id: string;
  name: string;
  slug: string;
  /** Monthly price in dollars, from `base_price_cents / 100`. */
  price: number;
}

export interface TenantSettings {
  id: string;
  name: string;
  slug: string;
  /** Tenant billing contact. Null when the tenant has none on record. */
  billingEmail: string | null;
  tier: {
    /** SubscriptionTier UUID, or null when the tenant's tier has no row. */
    id: string | null;
    name: string;
    slug: string;
  };
  status: 'active' | 'suspended' | 'pending' | 'churned';
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
  private _tiers: TierOption[] = [];
  private _tenantId = '';
  private _loading = true;
  private _saving = false;
  private _busy = false;
  private _dirty = false;

  constructor(host: TenantSettingsHost) {
    this._host = host;
  }

  get settings(): TenantSettings | null {
    return this._settings;
  }

  get tiers(): TierOption[] {
    return this._tiers;
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

  /** True while a lifecycle action (plan change / suspend / delete) is in flight. */
  get busy(): boolean {
    return this._busy;
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

      // Tiers are fetched alongside the tenant: the plan picker needs real
      // SubscriptionTier UUIDs for `UpgradeRequest.new_tier_id`, and the
      // badge wants a display name. `TenantOut.tier` is only a slug.
      const tiers = await apiClient.get<
        Array<{ id: string; name: string; slug: string; price: number }>
      >('/aaas/tiers');
      this._tiers = (tiers ?? []).map((t) => ({
        id: t.id,
        name: t.name,
        slug: t.slug,
        price: t.price ?? 0,
      }));

      const data = await apiClient.get<{
        id: string;
        name: string;
        slug: string;
        tier: string;
        status: 'active' | 'suspended' | 'pending' | 'churned';
        agents?: number;
        users?: number;
        mrr?: number;
        email?: string | null;
      }>(`/aaas/tenants/${tenant.id}`);

      const matched = this._tiers.find((t) => t.slug === data.tier);
      this._settings = {
        id: data.id,
        name: data.name,
        slug: data.slug,
        // TenantOut.email — the real billing contact, or null when absent.
        billingEmail: data.email ?? null,
        // TenantOut.tier is the slug. Resolve the UUID and display name from
        // the tier catalogue so the plan can actually be changed; when the
        // slug matches no row the id stays null rather than being invented.
        tier: {
          id: matched?.id ?? null,
          name: matched?.name ?? data.tier,
          slug: data.tier,
        },
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
        // Sent only when the operator actually set one: `email: null` would
        // mean "clear the contact" and an empty string is not a contact.
        ...(this._settings.billingEmail ? { email: this._settings.billingEmail } : {}),
      };
      // `tier` is deliberately absent. Changing the plan goes through
      // `upgradeTier()` → `POST /billing/tenant/{id}/upgrade`, which is the
      // atomic, audited path. PATCHing the slug here would silently swap
      // plans with no AuditLog entry and no proration record.
      await apiClient.patch(`/aaas/tenants/${this._tenantId}`, payload);
      this._dirty = false;
      this._toast('success', 'Settings saved successfully');
    } catch (e) {
      console.error('Failed to save:', e);
      this._toast('error', 'Failed to save settings');
    } finally {
      this._saving = false;
      this._host.requestUpdate();
    }
  }

  /**
   * Change the tenant's subscription plan.
   *
   * `POST /billing/tenant/{tenant_id}/upgrade` is real: it runs in a DB
   * transaction, updates `tenant.tier`, and writes an AuditLog row. There is
   * no payment provider integrated, so the API reports `prorated_amount_cents`
   * as 0 rather than inventing a charge — nothing here claims otherwise.
   */
  async upgradeTier(newTierId: string): Promise<boolean> {
    if (!this._tenantId || !newTierId) return false;
    this._busy = true;
    this._host.requestUpdate();
    try {
      const res = await apiClient.post<{
        success: boolean;
        message: string;
        old_tier: string;
        new_tier: string;
        prorated_amount_cents: number;
      }>(`/aaas/billing/tenant/${this._tenantId}/upgrade`, {
        new_tier_id: newTierId,
      });
      this._toast('success', res.message || `Plan changed to ${res.new_tier}`);
      await this.loadSettings();
      return true;
    } catch (e) {
      console.error('Failed to change plan:', e);
      this._toast('error', 'Failed to change plan');
      return false;
    } finally {
      this._busy = false;
      this._host.requestUpdate();
    }
  }

  /**
   * Suspend the tenant. The API also pauses every agent under it; a
   * suspended tenant can be brought back with `POST /aaas/tenants/{id}/activate`.
   */
  async suspendTenant(): Promise<boolean> {
    return this._lifecycle('suspend', 'Organization archived');
  }

  /**
   * Soft-delete the tenant: the API sets `status = "churned"` and keeps the
   * row. The UI must not claim a hard purge it cannot perform.
   */
  async deleteTenant(): Promise<boolean> {
    if (!this._tenantId) return false;
    this._busy = true;
    this._host.requestUpdate();
    try {
      const res = await apiClient.delete<{ message: string }>(
        `/aaas/tenants/${this._tenantId}`
      );
      this._toast('success', res.message || 'Organization removed');
      window.dispatchEvent(
        new CustomEvent('saas-navigate', { detail: { route: '/saas/tenants' } })
      );
      return true;
    } catch (e) {
      console.error('Failed to delete tenant:', e);
      this._toast('error', 'Failed to remove organization');
      return false;
    } finally {
      this._busy = false;
      this._host.requestUpdate();
    }
  }

  private async _lifecycle(
    action: 'suspend' | 'activate',
    successMessage: string
  ): Promise<boolean> {
    if (!this._tenantId) return false;
    this._busy = true;
    this._host.requestUpdate();
    try {
      await apiClient.post(`/aaas/tenants/${this._tenantId}/${action}`, {});
      this._toast('success', successMessage);
      await this.loadSettings();
      return true;
    } catch (e) {
      console.error(`Failed to ${action} tenant:`, e);
      this._toast('error', `Failed to ${action} organization`);
      return false;
    } finally {
      this._busy = false;
      this._host.requestUpdate();
    }
  }

  private _toast(type: 'success' | 'error', message: string): void {
    this._host.dispatchEvent(
      new CustomEvent('show-toast', {
        detail: { type, message },
        bubbles: true,
        composed: true,
      })
    );
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
