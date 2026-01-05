/**
 * Lago Billing Service
 * Per SAAS_PLATFORM_SRS Section 2.5
 *
 * VIBE COMPLIANT:
 * - Real Lago API integration
 * - No mocked data
 * - Production-grade implementation
 * 
 * Lago API Docs: https://doc.getlago.com/api
 */

import { apiClient, ApiError } from './api-client';

// ========== LAGO ENTITY TYPES ==========

export interface LagoCustomer {
    lago_id: string;
    external_id: string;  // Our tenant_id
    name: string;
    email?: string;
    billing_configuration?: {
        invoice_grace_period?: number;
        payment_provider?: string;
        vat_rate?: number;
    };
    metadata?: Record<string, string>;
    created_at: string;
    updated_at?: string;
}

export interface LagoPlan {
    lago_id: string;
    name: string;
    code: string;  // "free", "starter", "team", "enterprise"
    description?: string;
    amount_cents: number;
    amount_currency: string;
    interval: 'monthly' | 'yearly' | 'weekly';
    interval_count: number;
    trial_period?: number;
    pay_in_advance: boolean;
    charges: LagoCharge[];
    created_at: string;
}

export interface LagoCharge {
    lago_id: string;
    billable_metric_id: string;
    billable_metric_code: string;
    charge_model: 'standard' | 'graduated' | 'package' | 'percentage';
    properties?: {
        amount?: string;
        free_units?: number;
        package_size?: number;
        fixed_amount?: string;
    };
}

export interface LagoSubscription {
    lago_id: string;
    external_id: string;
    external_customer_id: string;
    plan_code: string;
    name?: string;
    status: 'active' | 'pending' | 'terminated' | 'canceled';
    started_at: string;
    ending_at?: string;
    terminated_at?: string;
    billing_time: 'calendar' | 'anniversary';
    created_at: string;
}

export interface LagoBillableMetric {
    lago_id: string;
    name: string;
    code: string;  // "tokens_input", "api_calls", etc.
    description?: string;
    aggregation_type: 'count_agg' | 'sum_agg' | 'max_agg' | 'unique_count_agg' | 'latest_agg';
    field_name?: string;
    group?: {
        key: string;
        values: string[];
    };
    created_at: string;
}

export interface LagoInvoice {
    lago_id: string;
    sequential_id: number;
    number: string;
    amount_cents: number;
    amount_currency: string;
    vat_amount_cents: number;
    total_amount_cents: number;
    status: 'draft' | 'finalized' | 'pending' | 'paid' | 'voided';
    payment_status: 'pending' | 'succeeded' | 'failed';
    issuing_date: string;
    customer: {
        lago_id: string;
        external_id: string;
        name: string;
    };
    subscriptions: Array<{
        lago_id: string;
        external_id: string;
        plan_code: string;
    }>;
    fees: Array<{
        item: {
            type: string;
            code: string;
            name: string;
        };
        amount_cents: number;
        units: string;
    }>;
    created_at: string;
}

export interface LagoWallet {
    lago_id: string;
    external_id: string;
    name: string;
    status: 'active' | 'terminated';
    currency: string;
    rate_amount: string;
    credits_balance: string;
    balance_cents: number;
    consumed_credits: string;
    created_at: string;
    expiration_at?: string;
}

export interface LagoCoupon {
    lago_id: string;
    name: string;
    code: string;
    amount_cents?: number;
    amount_currency?: string;
    percentage_rate?: number;
    coupon_type: 'fixed_amount' | 'percentage';
    frequency: 'once' | 'recurring' | 'forever';
    frequency_duration?: number;
    expiration_at?: string;
    reusable: boolean;
    limited_plans: boolean;
    plan_codes?: string[];
    created_at: string;
}

export interface LagoUsageMetric {
    lago_id: string;
    external_id: string;
    from_datetime: string;
    to_datetime: string;
    charges_usage: Array<{
        billable_metric: {
            lago_id: string;
            name: string;
            code: string;
            aggregation_type: string;
        };
        charge: {
            lago_id: string;
            charge_model: string;
        };
        units: string;
        events_count: number;
        amount_cents: number;
        amount_currency: string;
    }>;
}

// ========== ANALYTICS TYPES ==========

export interface LagoMRR {
    month: string;
    amount_cents: number;
    currency: string;
}

export interface LagoRevenue {
    from_datetime: string;
    to_datetime: string;
    amount_cents: number;
    currency: string;
}

// ========== LAGO SERVICE ==========

class LagoService {
    private baseUrl: string;

    constructor() {
        // Lago API is proxied through our Django gateway
        this.baseUrl = '/api/v2/billing';
    }

    // ===== CUSTOMERS (Tenants) =====

    async getCustomers(): Promise<LagoCustomer[]> {
        const response = await apiClient.get<{ customers: LagoCustomer[] }>(
            `${this.baseUrl}/customers`
        );
        return response.customers;
    }

    async getCustomer(externalId: string): Promise<LagoCustomer> {
        const response = await apiClient.get<{ customer: LagoCustomer }>(
            `${this.baseUrl}/customers/${externalId}`
        );
        return response.customer;
    }

    async createCustomer(data: {
        external_id: string;
        name: string;
        email?: string;
        billing_configuration?: LagoCustomer['billing_configuration'];
    }): Promise<LagoCustomer> {
        const response = await apiClient.post<{ customer: LagoCustomer }>(
            `${this.baseUrl}/customers`,
            { customer: data }
        );
        return response.customer;
    }

    async updateCustomer(
        externalId: string,
        data: Partial<LagoCustomer>
    ): Promise<LagoCustomer> {
        const response = await apiClient.put<{ customer: LagoCustomer }>(
            `${this.baseUrl}/customers/${externalId}`,
            { customer: data }
        );
        return response.customer;
    }

    // ===== PLANS =====

    async getPlans(): Promise<LagoPlan[]> {
        const response = await apiClient.get<{ plans: LagoPlan[] }>(
            `${this.baseUrl}/plans`
        );
        return response.plans;
    }

    async getPlan(code: string): Promise<LagoPlan> {
        const response = await apiClient.get<{ plan: LagoPlan }>(
            `${this.baseUrl}/plans/${code}`
        );
        return response.plan;
    }

    // ===== SUBSCRIPTIONS =====

    async getSubscriptions(externalCustomerId?: string): Promise<LagoSubscription[]> {
        const url = externalCustomerId
            ? `${this.baseUrl}/subscriptions?external_customer_id=${externalCustomerId}`
            : `${this.baseUrl}/subscriptions`;
        const response = await apiClient.get<{ subscriptions: LagoSubscription[] }>(url);
        return response.subscriptions;
    }

    async createSubscription(data: {
        external_customer_id: string;
        plan_code: string;
        external_id?: string;
        name?: string;
        billing_time?: 'calendar' | 'anniversary';
    }): Promise<LagoSubscription> {
        const response = await apiClient.post<{ subscription: LagoSubscription }>(
            `${this.baseUrl}/subscriptions`,
            { subscription: data }
        );
        return response.subscription;
    }

    async terminateSubscription(externalId: string): Promise<LagoSubscription> {
        const response = await apiClient.delete<{ subscription: LagoSubscription }>(
            `${this.baseUrl}/subscriptions/${externalId}`
        );
        return response.subscription;
    }

    // ===== BILLABLE METRICS =====

    async getBillableMetrics(): Promise<LagoBillableMetric[]> {
        const response = await apiClient.get<{ billable_metrics: LagoBillableMetric[] }>(
            `${this.baseUrl}/billable_metrics`
        );
        return response.billable_metrics;
    }

    // ===== INVOICES =====

    async getInvoices(externalCustomerId?: string): Promise<LagoInvoice[]> {
        const url = externalCustomerId
            ? `${this.baseUrl}/invoices?external_customer_id=${externalCustomerId}`
            : `${this.baseUrl}/invoices`;
        const response = await apiClient.get<{ invoices: LagoInvoice[] }>(url);
        return response.invoices;
    }

    async getInvoice(lagoId: string): Promise<LagoInvoice> {
        const response = await apiClient.get<{ invoice: LagoInvoice }>(
            `${this.baseUrl}/invoices/${lagoId}`
        );
        return response.invoice;
    }

    async downloadInvoice(lagoId: string): Promise<Blob> {
        const response = await fetch(`/api/v2/billing/invoices/${lagoId}/download`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('saas_auth_token')}`
            }
        });
        if (!response.ok) {
            throw new ApiError(response.status, 'Failed to download invoice');
        }
        return response.blob();
    }

    // ===== WALLETS (Prepaid Credits) =====

    async getWallets(externalCustomerId: string): Promise<LagoWallet[]> {
        const response = await apiClient.get<{ wallets: LagoWallet[] }>(
            `${this.baseUrl}/wallets?external_customer_id=${externalCustomerId}`
        );
        return response.wallets;
    }

    async createWallet(data: {
        external_customer_id: string;
        name: string;
        rate_amount: string;
        paid_credits: string;
        granted_credits?: string;
        expiration_at?: string;
    }): Promise<LagoWallet> {
        const response = await apiClient.post<{ wallet: LagoWallet }>(
            `${this.baseUrl}/wallets`,
            { wallet: data }
        );
        return response.wallet;
    }

    async topUpWallet(lagoId: string, credits: string): Promise<LagoWallet> {
        const response = await apiClient.post<{ wallet: LagoWallet }>(
            `${this.baseUrl}/wallets/${lagoId}/top_up`,
            { wallet_transaction: { paid_credits: credits } }
        );
        return response.wallet;
    }

    // ===== COUPONS =====

    async getCoupons(): Promise<LagoCoupon[]> {
        const response = await apiClient.get<{ coupons: LagoCoupon[] }>(
            `${this.baseUrl}/coupons`
        );
        return response.coupons;
    }

    async applyCoupon(data: {
        external_customer_id: string;
        coupon_code: string;
    }): Promise<void> {
        await apiClient.post(`${this.baseUrl}/applied_coupons`, { applied_coupon: data });
    }

    // ===== USAGE =====

    async getCustomerUsage(
        externalCustomerId: string,
        externalSubscriptionId: string
    ): Promise<LagoUsageMetric> {
        const response = await apiClient.get<{ customer_usage: LagoUsageMetric }>(
            `${this.baseUrl}/customers/${externalCustomerId}/current_usage?external_subscription_id=${externalSubscriptionId}`
        );
        return response.customer_usage;
    }

    // ===== ANALYTICS =====

    async getMRR(): Promise<LagoMRR[]> {
        const response = await apiClient.get<{ mrrs: LagoMRR[] }>(
            `${this.baseUrl}/analytics/mrr`
        );
        return response.mrrs;
    }

    async getRevenue(
        currency: string = 'USD',
        months: number = 12
    ): Promise<LagoRevenue[]> {
        const response = await apiClient.get<{ revenues: LagoRevenue[] }>(
            `${this.baseUrl}/analytics/revenue?currency=${currency}&months=${months}`
        );
        return response.revenues;
    }

    async getInvoiceCount(): Promise<{ month: string; invoices_count: number }[]> {
        const response = await apiClient.get<{
            invoice_collections: { month: string; invoices_count: number }[]
        }>(`${this.baseUrl}/analytics/invoice_collection`);
        return response.invoice_collections;
    }
}

// Singleton instance
export const lagoService = new LagoService();
