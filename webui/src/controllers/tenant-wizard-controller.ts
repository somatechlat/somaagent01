/**
 * Tenant Wizard Controller
 *
 * Manages state, validation, and submission for the SaaS tenant creation wizard.
 */

import { apiClient, ApiError } from '../services/api-client.js';

export interface TenantWizardHost {
    requestUpdate(): void;
    dispatchEvent(event: Event): boolean;
}

export interface TenantFormData {
    // Step 1: Identity
    name: string;
    slug: string;
    region: string;
    compliance: string[];
    domain: string;
    // Step 2: Plan
    tier_id: string;
    quota_overrides: Record<string, number>;
    billing_email: string;
    // Step 3: Defaults
    allowed_models: string[];
    mfa_enforced: boolean;
    allow_social_login: boolean;
    session_timeout_hours: number;
    theme: string;
    accent_color: string;
    admin_email: string;
}

export interface SubscriptionTier {
    id: string;
    name: string;
    slug: string;
    price_cents: number;
    max_agents: number;
    max_users: number;
}

interface BackendTierOut {
    id: string;
    name: string;
    slug: string;
    price: number;
    billing_period: string;
    limits: {
        agents: number;
        users: number;
        tokens_per_month: number;
        storage_gb: number;
    };
    features: string[];
    popular: boolean;
    active_count: number;
}

export class TenantWizardController {
    private _host: TenantWizardHost;
    private _slugCheckTimeout: number | null = null;

    private _currentStep = 1;
    private _formData: TenantFormData = {
        name: '',
        slug: '',
        region: 'us-east',
        compliance: [],
        domain: '',
        tier_id: 'starter',
        quota_overrides: {},
        billing_email: '',
        allowed_models: ['gpt-4o', 'claude-3-sonnet'],
        mfa_enforced: false,
        allow_social_login: true,
        session_timeout_hours: 4,
        theme: 'dark-modern',
        accent_color: '#00E5FF',
        admin_email: '',
    };
    private _slugStatus: 'checking' | 'available' | 'taken' | null = null;
    private _tiers: SubscriptionTier[] = [];
    private _creating = false;
    private _error: string | null = null;

    constructor(host: TenantWizardHost) {
        this._host = host;
    }

    get currentStep(): number {
        return this._currentStep;
    }

    get formData(): TenantFormData {
        return this._formData;
    }

    get slugStatus(): 'checking' | 'available' | 'taken' | null {
        return this._slugStatus;
    }

    get tiers(): SubscriptionTier[] {
        return this._tiers;
    }

    get creating(): boolean {
        return this._creating;
    }

    get error(): string | null {
        return this._error;
    }

    connect(): void {
        this._loadTiers();
    }

    disconnect(): void {
        if (this._slugCheckTimeout) {
            clearTimeout(this._slugCheckTimeout);
            this._slugCheckTimeout = null;
        }
    }

    private async _loadTiers(): Promise<void> {
        try {
            const data = await apiClient.get<BackendTierOut[]>('/aaas/tiers');
            this._tiers = data.map(t => ({
                id: t.id,
                name: t.name,
                slug: t.slug,
                price_cents: Math.round(t.price * 100),
                max_agents: t.limits.agents,
                max_users: t.limits.users,
            }));
        } catch (e) {
            this._tiers = [];
        }
        this._host.requestUpdate();
    }

    updateField(field: keyof TenantFormData, value: unknown): void {
        switch (field) {
            case 'name':
                this._updateName(String(value));
                return;
            case 'slug':
                this._updateSlug(String(value));
                return;
            case 'compliance':
                this._toggleCompliance(String(value));
                return;
            case 'allowed_models':
                this._toggleModel(String(value));
                return;
            case 'tier_id':
                this._setFormData({ tier_id: String(value) });
                break;
            case 'billing_email':
                this._setFormData({ billing_email: String(value) });
                break;
            case 'region':
                this._setFormData({ region: String(value) });
                break;
            case 'domain':
                this._setFormData({ domain: String(value) });
                break;
            case 'mfa_enforced':
                this._setFormData({ mfa_enforced: Boolean(value) });
                break;
            case 'allow_social_login':
                this._setFormData({ allow_social_login: Boolean(value) });
                break;
            case 'session_timeout_hours':
                this._setFormData({ session_timeout_hours: Number(value) });
                break;
            case 'admin_email':
                this._setFormData({ admin_email: String(value) });
                break;
            default:
                return;
        }
        this._host.requestUpdate();
    }

    private _setFormData(partial: Partial<TenantFormData>): void {
        this._formData = { ...this._formData, ...partial };
    }

    private _updateName(name: string): void {
        const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
        this._formData = { ...this._formData, name, slug };
        this._host.requestUpdate();
        this._checkSlugAvailability(slug);
    }

    private _updateSlug(slugRaw: string): void {
        const slug = slugRaw.toLowerCase().replace(/[^a-z0-9-]/g, '');
        this._formData = { ...this._formData, slug };
        this._host.requestUpdate();
        this._checkSlugAvailability(slug);
    }

    private _checkSlugAvailability(slug: string): void {
        if (this._slugCheckTimeout) clearTimeout(this._slugCheckTimeout);
        if (!slug || slug.length < 3) {
            this._slugStatus = null;
            this._host.requestUpdate();
            return;
        }
        this._slugStatus = 'checking';
        this._host.requestUpdate();
        this._slugCheckTimeout = window.setTimeout(async () => {
            try {
                const data = await apiClient.get<{ available: boolean; slug: string; suggestions?: string[] }>(
                    `/aaas/tenants/check-slug?slug=${slug}`
                );
                this._slugStatus = data.available ? 'available' : 'taken';
            } catch {
                this._slugStatus = null;
            }
            this._host.requestUpdate();
        }, 300);
    }

    private _toggleCompliance(framework: string): void {
        const compliance = this._formData.compliance.includes(framework)
            ? this._formData.compliance.filter(c => c !== framework)
            : [...this._formData.compliance, framework];
        this._formData = { ...this._formData, compliance };
        this._host.requestUpdate();
    }

    private _toggleModel(model: string): void {
        const allowed_models = this._formData.allowed_models.includes(model)
            ? this._formData.allowed_models.filter(m => m !== model)
            : [...this._formData.allowed_models, model];
        this._formData = { ...this._formData, allowed_models };
        this._host.requestUpdate();
    }

    canProceed(): boolean {
        if (this._currentStep === 1) {
            return this._formData.name.length >= 2 && this._formData.slug.length >= 3 && this._slugStatus === 'available';
        }
        if (this._currentStep === 2) {
            return !!this._formData.tier_id;
        }
        if (this._currentStep === 3) {
            return this._formData.admin_email.includes('@');
        }
        return true;
    }

    goBack(): void {
        if (this._currentStep > 1) {
            this._currentStep--;
            this._host.requestUpdate();
        } else {
            this._host.dispatchEvent(new CustomEvent('close'));
        }
    }

    goNext(): void {
        if (this.canProceed()) {
            this._currentStep++;
            this._host.requestUpdate();
        }
    }

    async createTenant(): Promise<void> {
        this._creating = true;
        this._error = null;
        this._host.requestUpdate();

        try {
            await apiClient.post('/aaas/tenants', {
                name: this._formData.name,
                email: this._formData.admin_email || this._formData.billing_email,
                tier: this._formData.tier_id,
            });
            window.location.href = '/platform/tenants';
        } catch (e) {
            if (e instanceof ApiError) {
                this._error = e.message;
            } else {
                this._error = 'Network error. Please try again.';
            }
            this._host.requestUpdate();
        } finally {
            this._creating = false;
            this._host.requestUpdate();
        }
    }
}
