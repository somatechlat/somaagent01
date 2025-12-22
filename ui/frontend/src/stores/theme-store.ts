/**
 * Eye of God Theme Store
 * Per Eye of God UIX Design Section 2.2
 *
 * VIBE COMPLIANT:
 * - Real Lit Context implementation
 * - CSS variable injection
 * - Theme persistence
 */

import { createContext } from '@lit/context';
import { LitElement, html } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { provide } from '@lit/context';

export interface Theme {
    id: string;
    name: string;
    description?: string;
    version: string;
    author: string;
    variables: Record<string, string>;
    is_approved: boolean;
}

export interface ThemeStateData {
    activeTheme: Theme | null;
    availableThemes: Theme[];
    isLoading: boolean;
    error: string | null;
}

export const themeContext = createContext<ThemeStateData>('theme-context');

const ACTIVE_THEME_KEY = 'eog_active_theme';

// Default theme variables
const DEFAULT_THEME: Theme = {
    id: 'default-dark',
    name: 'Default Dark',
    description: 'Eye of God default dark theme',
    version: '1.0.0',
    author: 'SomaStack',
    is_approved: true,
    variables: {
        '--eog-bg-void': '#0f172a',
        '--eog-bg-base': '#1e293b',
        '--eog-surface': 'rgba(30, 41, 59, 0.85)',
        '--eog-text-main': '#e2e8f0',
        '--eog-text-dim': '#64748b',
        '--eog-accent': '#94a3b8',
        '--eog-danger': '#ef4444',
        '--eog-success': '#22c55e',
        '--eog-warning': '#f59e0b',
        '--eog-info': '#3b82f6',
        '--eog-border-color': 'rgba(255, 255, 255, 0.05)',
        '--eog-radius-sm': '4px',
        '--eog-radius-md': '8px',
        '--eog-radius-lg': '12px',
        '--eog-radius-full': '9999px',
        '--eog-spacing-xs': '4px',
        '--eog-spacing-sm': '8px',
        '--eog-spacing-md': '16px',
        '--eog-spacing-lg': '24px',
        '--eog-spacing-xl': '32px',
    },
};

@customElement('eog-theme-provider')
export class EogThemeProvider extends LitElement {
    @provide({ context: themeContext })
    @state()
    themeState: ThemeStateData = {
        activeTheme: null,
        availableThemes: [DEFAULT_THEME],
        isLoading: true,
        error: null,
    };

    connectedCallback() {
        super.connectedCallback();
        this._initializeTheme();
    }

    render() {
        return html`<slot></slot>`;
    }

    /**
     * Initialize theme from storage or default
     */
    private async _initializeTheme() {
        try {
            // Load saved theme ID
            const savedThemeId = localStorage.getItem(ACTIVE_THEME_KEY);

            // Load available themes from API
            await this._loadThemes();

            // Find and apply saved theme or default
            if (savedThemeId) {
                const savedTheme = this.themeState.availableThemes.find(t => t.id === savedThemeId);
                if (savedTheme) {
                    this._applyTheme(savedTheme);
                    return;
                }
            }

            // Apply default theme
            this._applyTheme(DEFAULT_THEME);

        } catch (error) {
            console.error('Theme initialization failed:', error);
            this._applyTheme(DEFAULT_THEME);
        }
    }

    /**
     * Load themes from API
     */
    private async _loadThemes() {
        try {
            const token = localStorage.getItem('eog_auth_token');
            const response = await fetch('/api/v2/themes/', {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {},
            });

            if (response.ok) {
                const themes = await response.json();
                this.themeState = {
                    ...this.themeState,
                    availableThemes: [DEFAULT_THEME, ...themes],
                    isLoading: false,
                };
            } else {
                this.themeState = {
                    ...this.themeState,
                    isLoading: false,
                };
            }
        } catch (error) {
            console.error('Failed to load themes:', error);
            this.themeState = {
                ...this.themeState,
                isLoading: false,
                error: 'Failed to load themes',
            };
        }
    }

    /**
     * Apply theme CSS variables to document
     */
    private _applyTheme(theme: Theme) {
        const root = document.documentElement;

        // Remove previous custom properties
        const style = root.style;
        for (let i = style.length - 1; i >= 0; i--) {
            const prop = style[i];
            if (prop.startsWith('--eog-')) {
                style.removeProperty(prop);
            }
        }

        // Apply new theme variables
        for (const [key, value] of Object.entries(theme.variables)) {
            root.style.setProperty(key, value);
        }

        // Update state
        this.themeState = {
            ...this.themeState,
            activeTheme: theme,
        };

        // Persist selection
        localStorage.setItem(ACTIVE_THEME_KEY, theme.id);

        // Dispatch event
        this.dispatchEvent(new CustomEvent('eog-theme-changed', {
            detail: { theme },
            bubbles: true,
            composed: true,
        }));
    }

    /**
     * Set active theme by ID
     */
    async setTheme(themeId: string): Promise<boolean> {
        const theme = this.themeState.availableThemes.find(t => t.id === themeId);

        if (!theme) {
            console.error('Theme not found:', themeId);
            return false;
        }

        this._applyTheme(theme);

        // Track theme application via API
        try {
            const token = localStorage.getItem('eog_auth_token');
            await fetch(`/api/v2/themes/${themeId}/apply`, {
                method: 'POST',
                headers: token ? { 'Authorization': `Bearer ${token}` } : {},
            });
        } catch {
            // Non-critical error
        }

        return true;
    }

    /**
     * Preview theme without persisting
     */
    previewTheme(theme: Theme) {
        const root = document.documentElement;

        for (const [key, value] of Object.entries(theme.variables)) {
            root.style.setProperty(key, value);
        }
    }

    /**
     * Cancel preview and restore active theme
     */
    cancelPreview() {
        if (this.themeState.activeTheme) {
            this._applyTheme(this.themeState.activeTheme);
        }
    }

    /**
     * Add a new custom theme
     */
    async addTheme(theme: Omit<Theme, 'id'>): Promise<Theme | null> {
        try {
            const token = localStorage.getItem('eog_auth_token');
            const response = await fetch('/api/v2/themes/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify(theme),
            });

            if (response.ok) {
                const newTheme = await response.json() as Theme;

                this.themeState = {
                    ...this.themeState,
                    availableThemes: [...this.themeState.availableThemes, newTheme],
                };

                return newTheme;
            }

            return null;
        } catch (error) {
            console.error('Failed to create theme:', error);
            return null;
        }
    }

    /**
     * Export theme as JSON
     */
    exportTheme(theme: Theme): string {
        return JSON.stringify({
            name: theme.name,
            description: theme.description,
            version: theme.version,
            author: theme.author,
            variables: theme.variables,
        }, null, 2);
    }

    /**
     * Import theme from JSON
     */
    async importTheme(jsonString: string): Promise<Theme | null> {
        try {
            const data = JSON.parse(jsonString);

            // Validate required fields
            if (!data.name || !data.variables) {
                throw new Error('Invalid theme format');
            }

            return await this.addTheme({
                name: data.name,
                description: data.description || '',
                version: data.version || '1.0.0',
                author: data.author || 'Imported',
                variables: data.variables,
                is_approved: false,
            });
        } catch (error) {
            console.error('Theme import failed:', error);
            this.themeState = {
                ...this.themeState,
                error: 'Invalid theme file',
            };
            return null;
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'eog-theme-provider': EogThemeProvider;
    }
}
