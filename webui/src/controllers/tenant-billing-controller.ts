/**
 * Tenant Billing Controller
 *
 * Manages billing data loading and upgrade mutation for the tenant billing view.
 */

import { apiClient } from '../services/api-client.js';

export interface Invoice {
    id: string;
    number: string;
    created_at: string;
    amount_cents: number;
    currency: string;
    status: string;
}

export interface UsageStat {
    metric: string;
    /**
     * Measured value, or the string '—' when this system has no meter for it.
     * Unmeasured metrics are never rendered as 0.
     */
    used: number | string;
    limit: number;
    unit: string;
}

export interface TierLimits {
    agents: number;
    users: number;
    tokens_per_month: number;
    storage_gb: number;
}

export interface SubscriptionPlan {
    id: string;
    name: string;
    price: number;
    features: string[];
    is_current: boolean;
}

export interface TenantBilling {
    tenant_id: string;
    tenant_name: string;
    current_tier: string;
    price_cents: number;
    billing_cycle: string;
    next_billing_date?: string;
    payment_method?: string;
    payment_last4?: string;
}

export interface UpgradePlanDetail {
    plan: SubscriptionPlan;
}

export interface TenantBillingHost {
    requestUpdate(): void;
    dispatchEvent(event: Event): boolean;
}

export class TenantBillingController {
    private _host: TenantBillingHost;

    private _tenantId = '';
    private _loading = true;
    private _error = '';
    private _currentPlan: TenantBilling | null = null;
    private _usage: UsageStat[] = [];
    private _invoices: Invoice[] = [];
    private _plans: SubscriptionPlan[] = [];
    private _upgrading = false;

    constructor(host: TenantBillingHost) {
        this._host = host;
    }

    get tenantId(): string {
        return this._tenantId;
    }

    get loading(): boolean {
        return this._loading;
    }

    get error(): string {
        return this._error;
    }

    get currentPlan(): TenantBilling | null {
        return this._currentPlan;
    }

    get usage(): UsageStat[] {
        return this._usage;
    }

    get invoices(): Invoice[] {
        return this._invoices;
    }

    get plans(): SubscriptionPlan[] {
        return this._plans;
    }

    get upgrading(): boolean {
        return this._upgrading;
    }

    async resolveTenantId(): Promise<string | null> {
        const stored = sessionStorage.getItem('saas_tenant_id');
        if (stored) return stored;

        try {
            const data = await apiClient.get<{ items?: Array<{ id: string }> }>(
                '/aaas/tenants?page=1&per_page=1'
            );
            const tenant = data.items?.[0];
            if (tenant?.id) {
                sessionStorage.setItem('saas_tenant_id', tenant.id);
                return tenant.id;
            }
        } catch (e) {
            console.error('[TenantBillingController] Failed to resolve tenant:', e);
        }
        return null;
    }

    async loadBillingData(): Promise<void> {
        this._loading = true;
        this._error = '';
        this._host.requestUpdate();

        const tenantId = await this.resolveTenantId();
        if (!tenantId) {
            this._error = 'No tenant selected.';
            this._loading = false;
            this._host.requestUpdate();
            return;
        }
        this._tenantId = tenantId;

        try {
            // No invoice source exists in this system: the external billing
            // integration was removed, and the former /aaas/billing/.../invoices
            // route was a stub that always returned []. Invoices are reported
            // as empty rather than invented.
            const [billingData, usageData, tiersData] = await Promise.all([
                apiClient.get<TenantBilling>(`/aaas/billing/tenant/${tenantId}`),
                apiClient.get<{
                    tokens_used: number;
                    storage_used_gb: number;
                    api_calls: number | null;
                    agents_active: number;
                    users_active: number | null;
                }>(`/aaas/billing/usage/${tenantId}`),
                apiClient.get<
                    Array<{
                        id: string;
                        name: string;
                        price: number;
                        features: string[];
                    }>
                >('/aaas/tiers'),
            ]);

            this._currentPlan = billingData;
            this._invoices = [];
            this._plans = (tiersData || []).map((tier) => ({
                id: tier.id,
                name: tier.name,
                price: tier.price,
                features: tier.features || [],
                is_current: tier.name === billingData.current_tier,
            }));

            // api_calls / users_active are Optional on the backend: null means
            // this system has no meter for them. Surface that as '—', never 0.
            this._usage = [
                { metric: 'Agents Active', used: usageData.agents_active ?? 0, limit: 0, unit: '' },
                {
                    metric: 'Users Active',
                    used: usageData.users_active ?? '—',
                    limit: 0,
                    unit: '',
                },
                {
                    metric: 'API Calls',
                    used: usageData.api_calls ?? '—',
                    limit: 0,
                    unit: '',
                },
                { metric: 'Tokens Used', used: usageData.tokens_used ?? 0, limit: 0, unit: '' },
                { metric: 'Storage', used: usageData.storage_used_gb ?? 0, limit: 0, unit: 'GB' },
            ];
        } catch (e) {
            console.error('[TenantBillingController] Failed to load billing data:', e);
            this._error = 'Failed to load billing data. Please try again later.';
        } finally {
            this._loading = false;
            this._host.requestUpdate();
        }
    }

    async upgradePlan(plan: SubscriptionPlan): Promise<void> {
        if (plan.is_current || !this._tenantId) return;

        this._upgrading = true;
        this._error = '';
        this._host.requestUpdate();

        try {
            await apiClient.post(`/aaas/billing/tenant/${this._tenantId}/upgrade`, {
                new_tier_id: plan.id,
                prorate: true,
            });
            await this.loadBillingData();
        } catch (e) {
            console.error('[TenantBillingController] Failed to upgrade plan:', e);
            this._error = 'Failed to upgrade plan. Please try again later.';
            this._host.requestUpdate();
        } finally {
            this._upgrading = false;
        }
    }
}
