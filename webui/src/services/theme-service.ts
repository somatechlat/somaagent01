/**
 * SaaS Admin Theme Service
 * Per SaaS Admin UIX Design Section 2.2
 *
 * VIBE COMPLIANT:
 * - Real API integration
 * - XSS validation
 * - Type-safe requests
 */

import { apiClient, type ApiResponse } from './api-client.js';

export interface Theme {
    id: string;
    tenant_id: string;
    name: string;
    description?: string;
    version: string;
    author: string;
    variables: Record<string, string>;
    is_approved: boolean;
    downloads: number;
    created_at: string;
    updated_at: string;
}

export interface ThemeCreateRequest {
    name: string;
    description?: string;
    version?: string;
    author?: string;
    variables: Record<string, string>;
}

export interface ThemeUpdateRequest {
    name?: string;
    description?: string;
    variables?: Record<string, string>;
}

/**
 * Theme Service handles all theme-related API calls
 */
class ThemeService {
    private readonly basePath = '/api/v2/themes';

    // XSS patterns to reject
    private readonly xssPatterns = [
        /<script/i,
        /javascript:/i,
        /url\s*\(/i,
        /expression\s*\(/i,
        /on\w+\s*=/i,
    ];

    /**
     * Get all themes
     */
    async getAll(options?: {
        search?: string;
        approved_only?: boolean;
        page?: number;
        page_size?: number;
    }): Promise<ApiResponse<Theme[]>> {
        const params = new URLSearchParams();

        if (options?.search) params.set('search', options.search);
        if (options?.approved_only !== undefined) params.set('approved_only', String(options.approved_only));
        if (options?.page) params.set('page', String(options.page));
        if (options?.page_size) params.set('page_size', String(options.page_size));

        const query = params.toString();
        return apiClient.get<Theme[]>(`${this.basePath}${query ? `?${query}` : ''}`);
    }

    /**
     * Get theme by ID
     */
    async getById(id: string): Promise<ApiResponse<Theme>> {
        return apiClient.get<Theme>(`${this.basePath}/${id}`);
    }

    /**
     * Create new theme
     */
    async create(theme: ThemeCreateRequest): Promise<ApiResponse<Theme>> {
        // Validate for XSS before sending
        const validation = this.validateTheme(theme);
        if (!validation.valid) {
            if (!validation.valid) {
                throw new Error(validation.error || 'Validation failed');
            }
        }

        return apiClient.post<Theme>(this.basePath, theme);
    }

    /**
     * Update existing theme
     */
    async update(id: string, theme: ThemeUpdateRequest): Promise<ApiResponse<Theme>> {
        if (theme.variables) {
            const validation = this.validateVariables(theme.variables);
            if (!validation.valid) {
                if (!validation.valid) {
                    throw new Error(validation.error || 'Validation failed');
                }
            }
        }

        return apiClient.patch<Theme>(`${this.basePath}/${id}`, theme);
    }

    /**
     * Delete theme
     */
    async delete(id: string): Promise<ApiResponse<void>> {
        return apiClient.delete<void>(`${this.basePath}/${id}`);
    }

    /**
     * Approve theme (admin only)
     */
    async approve(id: string): Promise<ApiResponse<Theme>> {
        return apiClient.post<Theme>(`${this.basePath}/${id}/approve`, {});
    }

    /**
     * Apply theme and track download
     */
    async apply(id: string): Promise<ApiResponse<{ success: boolean; variables: Record<string, string> }>> {
        return apiClient.post<{ success: boolean; variables: Record<string, string> }>(`${this.basePath}/${id}/apply`, {});
    }

    /**
     * Validate theme for XSS and schema
     */
    validateTheme(theme: ThemeCreateRequest): { valid: boolean; error?: string } {
        // Name validation
        if (!theme.name || theme.name.length < 1 || theme.name.length > 100) {
            return { valid: false, error: 'Name must be 1-100 characters' };
        }

        // Variables validation
        return this.validateVariables(theme.variables);
    }

    /**
     * Validate CSS variables for XSS
     */
    validateVariables(variables: Record<string, string>): { valid: boolean; error?: string } {
        for (const [key, value] of Object.entries(variables)) {
            // Key must start with --
            if (!key.startsWith('--')) {
                return { valid: false, error: `Invalid variable name: ${key}` };
            }

            // Check for XSS patterns
            for (const pattern of this.xssPatterns) {
                if (pattern.test(value)) {
                    return { valid: false, error: `XSS pattern detected in ${key}` };
                }
            }

            // Value length limit
            if (value.length > 500) {
                return { valid: false, error: `Value too long for ${key}` };
            }
        }

        return { valid: true };
    }

    /**
     * Check WCAG contrast ratio
     */
    checkContrast(foreground: string, background: string): number {
        const getLuminance = (color: string): number => {
            // Parse hex color
            const hex = color.replace('#', '');
            const r = parseInt(hex.slice(0, 2), 16) / 255;
            const g = parseInt(hex.slice(2, 4), 16) / 255;
            const b = parseInt(hex.slice(4, 6), 16) / 255;

            const toLinear = (c: number) =>
                c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);

            return 0.2126 * toLinear(r) + 0.7152 * toLinear(g) + 0.0722 * toLinear(b);
        };

        const l1 = getLuminance(foreground);
        const l2 = getLuminance(background);
        const lighter = Math.max(l1, l2);
        const darker = Math.min(l1, l2);

        return (lighter + 0.05) / (darker + 0.05);
    }

    /**
     * Validate AA contrast compliance
     */
    isAACompliant(foreground: string, background: string, largeText = false): boolean {
        const ratio = this.checkContrast(foreground, background);
        return largeText ? ratio >= 3 : ratio >= 4.5;
    }

    /**
     * Export theme to JSON file
     */
    exportToFile(theme: Theme): void {
        const data = {
            name: theme.name,
            description: theme.description,
            version: theme.version,
            author: theme.author,
            variables: theme.variables,
        };

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `${theme.name.toLowerCase().replace(/\s+/g, '-')}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    /**
     * Import theme from file
     */
    async importFromFile(file: File): Promise<ThemeCreateRequest | null> {
        return new Promise((resolve) => {
            const reader = new FileReader();

            reader.onload = (e) => {
                try {
                    const data = JSON.parse(e.target?.result as string);

                    if (!data.name || !data.variables) {
                        resolve(null);
                        return;
                    }

                    const validation = this.validateVariables(data.variables);
                    if (!validation.valid) {
                        resolve(null);
                        return;
                    }

                    resolve({
                        name: data.name,
                        description: data.description,
                        version: data.version || '1.0.0',
                        author: data.author || 'Imported',
                        variables: data.variables,
                    });
                } catch {
                    resolve(null);
                }
            };

            reader.onerror = () => resolve(null);
            reader.readAsText(file);
        });
    }
}

export const themeService = new ThemeService();
