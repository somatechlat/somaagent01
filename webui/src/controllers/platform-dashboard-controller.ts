/**
 * Platform Dashboard Controller
 * Manages data loading and user session state for the SaaS platform dashboard.
 */

import { apiClient } from '../services/api-client.js';

export interface PlatformMetrics {
    totalTenants: number;
    activeTenants: number;
    trialTenants: number;
    totalAgents: number;
    activeAgents: number;
    totalUsers: number;
    mrr: number;
    mrrGrowth: number | null;
    uptime_seconds: number;
    activeAlerts: number | null;
    tokensThisMonth: number;
    storageUsedGB: number;
}

export interface RecentEvent {
    id: string;
    type: 'tenant' | 'agent' | 'billing' | 'alert' | 'user';
    message: string;
    timestamp: string;
}

export interface TopTenant {
    id: string;
    name: string;
    tier: string;
    agents: number;
    users: number;
    mrr: number;
    status: 'active' | 'trial' | 'suspended';
}

export interface PlatformDashboardData {
    metrics: PlatformMetrics;
    topTenants: TopTenant[];
    recentEvents: RecentEvent[];
    loading: boolean;
    error: string | null;
    userName: string;
    userRole: string;
}

export interface PlatformDashboardHost extends PlatformDashboardData {
    requestUpdate(): void;
}

export const DEFAULT_METRICS: PlatformMetrics = {
    totalTenants: 0,
    activeTenants: 0,
    trialTenants: 0,
    totalAgents: 0,
    activeAgents: 0,
    totalUsers: 0,
    mrr: 0,
    mrrGrowth: null,
    uptime_seconds: 0,
    activeAlerts: null,
    tokensThisMonth: 0,
    storageUsedGB: 0,
};

export class PlatformDashboardController {
    private host: PlatformDashboardHost;

    constructor(host: PlatformDashboardHost) {
        this.host = host;
    }

    connect(): void {
        this.loadUser();
        this.loadDashboardData();
    }

    async loadUser(): Promise<void> {
        try {
            const userStr = sessionStorage.getItem('saas_user');
            if (userStr) {
                const user = JSON.parse(userStr);
                this.host.userName = user.name || '';
                this.host.userRole = user.role || '';
                this.host.requestUpdate();
                return;
            }
            const user = await apiClient.get<{ name?: string; role?: string }>('/auth/me');
            this.host.userName = user?.name || '';
            this.host.userRole = user?.role || '';
            this.host.requestUpdate();
        } catch (error) {
            console.error('[PlatformDashboardController] Failed to load user:', error);
        }
    }

    async loadDashboardData(): Promise<void> {
        /**
         * VIBE Rule #5: Fail Fast - no silent fallbacks
         * VIBE Rule #9: All data from real backends
         *
         * API: GET /api/v2/aaas/dashboard/
         * Backend: admin/aaas/api/dashboard.py
         */
        this.host.loading = true;
        this.host.error = null;
        this.host.requestUpdate();

        try {
            const response = await apiClient.get<{
                metrics: PlatformMetrics;
                topTenants: TopTenant[];
                recentEvents: RecentEvent[];
            }>('/aaas/dashboard/');

            this.host.metrics = response.metrics;
            this.host.topTenants = response.topTenants;
            this.host.recentEvents = response.recentEvents;
        } catch (error) {
            // VIBE: Fail fast - show error to user, don't hide it
            this.host.error = error instanceof Error ? error.message : 'Failed to load dashboard data';
            console.error('[PlatformDashboardController] API Error:', error);
        } finally {
            this.host.loading = false;
            this.host.requestUpdate();
        }
    }

    getInitials(name: string): string {
        return name
            .split(' ')
            .map(part => part[0])
            .join('')
            .slice(0, 2)
            .toUpperCase();
    }

    logout(): void {
        sessionStorage.removeItem('saas_mode');
        window.location.href = '/login';
    }
}
