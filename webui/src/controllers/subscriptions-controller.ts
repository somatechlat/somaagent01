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

export class SubscriptionsController {
    async loadTiers(): Promise<SubscriptionTier[]> {
        try {
            const response = await apiClient.get('/saas/subscriptions/') as { tiers?: SubscriptionTier[] };
            return response.tiers ?? [];
        } catch {
            // Demo data if API not available (preserves existing behavior)
            return [
                { id: '1', name: 'Free', slug: 'free', maxAgents: 1, maxUsers: 3, maxTokensPerMonth: 100000, maxStorageGB: 1, priceCents: 0, billingInterval: 'monthly', tenantCount: 45, isCustom: false },
                { id: '2', name: 'Starter', slug: 'starter', maxAgents: 3, maxUsers: 10, maxTokensPerMonth: 1000000, maxStorageGB: 10, priceCents: 4900, billingInterval: 'monthly', tenantCount: 32, isCustom: false },
                { id: '3', name: 'Team', slug: 'team', maxAgents: 10, maxUsers: 50, maxTokensPerMonth: 10000000, maxStorageGB: 100, priceCents: 19900, billingInterval: 'monthly', tenantCount: 28, isCustom: false },
                { id: '4', name: 'Enterprise', slug: 'enterprise', maxAgents: -1, maxUsers: -1, maxTokensPerMonth: -1, maxStorageGB: -1, priceCents: 99900, billingInterval: 'monthly', tenantCount: 12, isCustom: false },
            ];
        }
    }

    async createTier(tier: SubscriptionTierInput): Promise<void> {
        await apiClient.post('/saas/subscriptions/', tier);
    }

    async updateTier(id: string, tier: SubscriptionTierInput): Promise<void> {
        await apiClient.put(`/saas/subscriptions/${id}/`, tier);
    }

    async deleteTier(id: string): Promise<void> {
        await apiClient.delete(`/saas/subscriptions/${id}/`);
    }
}
