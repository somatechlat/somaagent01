/**
 * Subscriptions Controller
 * Manages subscription tier loading and save mutations.
 *
 * VIBE COMPLIANT:
 * - Real API integration via apiClient
 * - Minimal logic, no UI concerns
 */

import { apiClient } from '../services/api-client.js';

export interface SubscriptionTier {
    id: string;
    name: string;
    slug: string;
    maxAgents: number;
    maxUsers: number;
    maxTokensPerMonth: number;
    maxStorageGB: number;
    priceCents: number;
    billingInterval: 'monthly' | 'yearly';
    tenantCount: number;
    isCustom: boolean;
}

export interface SubscriptionTierInput {
    name: string;
    slug: string;
    maxAgents: number;
    maxUsers: number;
    maxTokensPerMonth: number;
    maxStorageGB: number;
    priceCents: number;
    billingInterval: 'monthly' | 'yearly';
    isCustom: boolean;
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

interface BackendTierCreate {
    name: string;
    slug: string;
    price_cents: number;
    billing_interval: 'monthly' | 'yearly';
    limits: {
        agents: number;
        users: number;
        tokens_per_month: number;
        storage_gb: number;
    };
    features?: string[];
}

interface BackendTierUpdate {
    name?: string;
    price_cents?: number;
    limits?: {
        agents?: number;
        users?: number;
        tokens_per_month?: number;
        storage_gb?: number;
    };
    features?: string[];
    is_active?: boolean;
}

function toFrontendTier(t: BackendTierOut): SubscriptionTier {
    return {
        id: t.id,
        name: t.name,
        slug: t.slug,
        maxAgents: t.limits.agents,
        maxUsers: t.limits.users,
        maxTokensPerMonth: t.limits.tokens_per_month,
        maxStorageGB: t.limits.storage_gb,
        priceCents: Math.round(t.price * 100),
        billingInterval: t.billing_period as 'monthly' | 'yearly',
        tenantCount: t.active_count ?? 0,
        isCustom: false,
    };
}

function toBackendCreate(input: SubscriptionTierInput): BackendTierCreate {
    return {
        name: input.name,
        slug: input.slug,
        price_cents: input.priceCents,
        billing_interval: input.billingInterval,
        limits: {
            agents: input.maxAgents,
            users: input.maxUsers,
            tokens_per_month: input.maxTokensPerMonth,
            storage_gb: input.maxStorageGB,
        },
    };
}

function toBackendUpdate(input: SubscriptionTierInput): BackendTierUpdate {
    return {
        name: input.name,
        price_cents: input.priceCents,
        limits: {
            agents: input.maxAgents,
            users: input.maxUsers,
            tokens_per_month: input.maxTokensPerMonth,
            storage_gb: input.maxStorageGB,
        },
    };
}

export class SubscriptionsController {
    async loadTiers(): Promise<SubscriptionTier[]> {
        try {
            const data = await apiClient.get<BackendTierOut[]>('/aaas/tiers');
            return data.map(toFrontendTier);
        } catch {
            return [];
        }
    }

    async createTier(tier: SubscriptionTierInput): Promise<void> {
        await apiClient.post('/aaas/tiers', toBackendCreate(tier));
    }

    async updateTier(id: string, tier: SubscriptionTierInput): Promise<void> {
        await apiClient.patch(`/aaas/tiers/${id}`, toBackendUpdate(tier));
    }

    async deleteTier(id: string): Promise<void> {
        await apiClient.delete(`/aaas/tiers/${id}`);
    }
}
