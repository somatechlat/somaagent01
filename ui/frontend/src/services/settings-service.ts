/**
 * Eye of God Settings Service
 * Per Eye of God UIX Design Section 2.2
 *
 * VIBE COMPLIANT:
 * - Real API integration
 * - Type-safe requests
 * - Error handling
 */

import { apiClient, type ApiResponse } from './api-client.js';

export type SettingsTab = 'agent' | 'external' | 'connectivity' | 'system';

export interface SettingsResponse {
    tab: SettingsTab;
    data: Record<string, unknown>;
    updated_at: string;
    version: number;
}

export interface SettingsUpdateRequest {
    data: Record<string, unknown>;
    version: number;
}

/**
 * Settings Service handles all settings-related API calls
 */
class SettingsService {
    private readonly basePath = '/api/v2/settings';

    /**
     * Get all settings for current tenant
     */
    async getAll(): Promise<ApiResponse<SettingsResponse[]>> {
        return apiClient.get<SettingsResponse[]>(this.basePath);
    }

    /**
     * Get settings for a specific tab
     */
    async getByTab(tab: SettingsTab): Promise<ApiResponse<SettingsResponse>> {
        return apiClient.get<SettingsResponse>(`${this.basePath}/${tab}`);
    }

    /**
     * Update settings for a specific tab
     */
    async update(
        tab: SettingsTab,
        data: Record<string, unknown>,
        version: number
    ): Promise<ApiResponse<SettingsResponse>> {
        return apiClient.put<SettingsResponse>(`${this.basePath}/${tab}`, {
            data,
            version,
        });
    }

    /**
     * Reset settings tab to defaults
     */
    async reset(tab: SettingsTab): Promise<ApiResponse<SettingsResponse>> {
        return apiClient.post<SettingsResponse>(`${this.basePath}/${tab}/reset`);
    }

    /**
     * Validate setting value
     */
    validateSetting(tab: SettingsTab, key: string, value: unknown): boolean {
        const validators: Record<string, Record<string, (v: unknown) => boolean>> = {
            agent: {
                temperature: (v) => typeof v === 'number' && v >= 0 && v <= 2,
                max_tokens: (v) => typeof v === 'number' && v >= 1 && v <= 32000,
                recall_interval: (v) => typeof v === 'number' && v >= 1 && v <= 3600,
                max_memories: (v) => typeof v === 'number' && v >= 1 && v <= 10000,
            },
            connectivity: {
                timeout_ms: (v) => typeof v === 'number' && v >= 1000 && v <= 300000,
                retry_attempts: (v) => typeof v === 'number' && v >= 0 && v <= 10,
            },
            system: {
                log_level: (v) => ['DEBUG', 'INFO', 'WARNING', 'ERROR'].includes(v as string),
            },
        };

        const tabValidators = validators[tab];
        if (!tabValidators || !tabValidators[key]) {
            return true; // No validator = always valid
        }

        return tabValidators[key](value);
    }
}

export const settingsService = new SettingsService();
