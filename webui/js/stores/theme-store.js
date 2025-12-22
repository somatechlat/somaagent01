/**
 * Theme Alpine Store
 * Per AgentSkin UIX TR-AGS-003
 * 
 * VIBE COMPLIANT:
 * - Real implementations only
 * - Integrates with ThemeLoader SDK
 * - Reactive state management via Alpine.js
 * 
 * Features:
 * - Fetch themes from API
 * - Apply/preview themes
 * - Search/filter themes
 * - Admin upload functionality
 */

document.addEventListener('alpine:init', () => {
    Alpine.store('theme', {
        // State
        themes: [],
        currentTheme: localStorage.getItem('ui-config')
            ? JSON.parse(localStorage.getItem('ui-config')).theme || 'default'
            : 'default',
        previewTheme: null,
        isAdmin: false,
        searchQuery: '',
        isLoading: false,
        error: null,

        /**
         * Initialize store on load.
         */
        async init() {
            await this.loadThemes();
            await this.applyCurrentTheme();
        },

        /**
         * Load themes from backend API.
         */
        async loadThemes() {
            this.isLoading = true;
            this.error = null;

            try {
                const response = await fetch('/v1/skins');
                if (!response.ok) {
                    throw new Error(`Failed to load themes: ${response.status}`);
                }
                this.themes = await response.json();
            } catch (e) {
                console.error('Failed to load themes:', e);
                this.error = e.message;

                // Fallback to local themes if API unavailable
                this.themes = [
                    { name: 'default', description: 'Default light theme', version: '1.0.0' },
                    { name: 'midnight', description: 'Dark midnight theme', version: '1.0.0' },
                ];
            } finally {
                this.isLoading = false;
            }
        },

        /**
         * Apply the currently selected theme.
         */
        async applyCurrentTheme() {
            if (window.Theme) {
                await window.Theme.switch(this.currentTheme);
            }
        },

        /**
         * Apply a theme by name.
         * @param {string} name - Theme name
         */
        async applyTheme(name) {
            if (window.Theme) {
                const success = await window.Theme.switch(name);
                if (success) {
                    this.currentTheme = name;
                    this.previewTheme = null;
                }
            }
        },

        /**
         * Preview a theme temporarily.
         * @param {object} theme - Theme object with variables
         */
        async previewThemeSkin(theme) {
            if (window.Theme && theme.variables) {
                window.Theme.preview(theme);
                this.previewTheme = theme.name;
            }
        },

        /**
         * Cancel preview and restore previous theme.
         */
        cancelPreview() {
            if (window.Theme) {
                window.Theme.cancelPreview();
                this.previewTheme = null;
            }
        },

        /**
         * Upload a theme file (admin only).
         * @param {File} file - JSON file
         */
        async uploadTheme(file) {
            if (!this.isAdmin) {
                console.error('Upload requires admin privileges');
                return false;
            }

            try {
                const text = await file.text();
                const theme = JSON.parse(text);

                // Validate locally first
                if (window.Theme && !window.Theme.validate(theme)) {
                    throw new Error('Theme validation failed');
                }

                // Upload to backend
                const response = await fetch('/v1/skins', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(theme),
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Upload failed');
                }

                // Reload themes
                await this.loadThemes();
                return true;
            } catch (e) {
                console.error('Theme upload failed:', e);
                this.error = e.message;
                return false;
            }
        },

        /**
         * Delete a theme (admin only).
         * @param {string} id - Theme ID
         */
        async deleteTheme(id) {
            if (!this.isAdmin) {
                console.error('Delete requires admin privileges');
                return false;
            }

            try {
                const response = await fetch(`/v1/skins/${id}`, {
                    method: 'DELETE',
                });

                if (!response.ok) {
                    throw new Error('Delete failed');
                }

                // Reload themes
                await this.loadThemes();
                return true;
            } catch (e) {
                console.error('Theme delete failed:', e);
                this.error = e.message;
                return false;
            }
        },

        /**
         * Approve a theme (admin only).
         * @param {string} id - Theme ID
         */
        async approveTheme(id) {
            if (!this.isAdmin) {
                console.error('Approve requires admin privileges');
                return false;
            }

            try {
                const response = await fetch(`/v1/skins/${id}/approve`, {
                    method: 'PATCH',
                });

                if (!response.ok) {
                    throw new Error('Approve failed');
                }

                // Reload themes
                await this.loadThemes();
                return true;
            } catch (e) {
                console.error('Theme approve failed:', e);
                this.error = e.message;
                return false;
            }
        },

        /**
         * Get filtered themes based on search query.
         */
        get filteredThemes() {
            if (!this.searchQuery) return this.themes;

            const q = this.searchQuery.toLowerCase();
            return this.themes.filter(t =>
                t.name.toLowerCase().includes(q) ||
                (t.description || '').toLowerCase().includes(q) ||
                (t.author || '').toLowerCase().includes(q)
            );
        },

        /**
         * Check if a theme is currently active.
         * @param {string} name - Theme name
         * @returns {boolean}
         */
        isActive(name) {
            return this.currentTheme === name;
        },

        /**
         * Check if a theme is being previewed.
         * @param {string} name - Theme name
         * @returns {boolean}
         */
        isPreviewing(name) {
            return this.previewTheme === name;
        },

        /**
         * Set admin mode (checked via OPA policy).
         * @param {boolean} isAdmin
         */
        setAdminMode(isAdmin) {
            this.isAdmin = isAdmin;
        },

        /**
         * Clear any error state.
         */
        clearError() {
            this.error = null;
        }
    });
});
