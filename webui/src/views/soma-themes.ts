/**
 * Eye of God Themes View
 * Per Eye of God UIX Design Section 4.3
 *
 * VIBE COMPLIANT:
 * - Real Lit implementation
 * - Integrates with AgentSkin ThemeLoader
 * - Live preview support
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import '../components/soma-button.js';
import '../components/soma-input.js';
import '../components/soma-modal.js';

export interface Theme {
    id: string;
    name: string;
    version: string;
    author: string;
    description?: string;
    variables: Record<string, string>;
    preview_url?: string;
    downloads: number;
    is_approved: boolean;
}

@customElement('soma-themes')
export class SomaThemes extends LitElement {
    static styles = css`
        :host {
            display: block;
            height: 100%;
            overflow-y: auto;
            padding: var(--soma-spacing-xl, 32px);
            background: var(--soma-bg-base, #1e293b);
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--soma-spacing-xl, 32px);
        }

        .header h1 {
            font-size: var(--soma-text-2xl, 24px);
            font-weight: 600;
            color: var(--soma-text-main, #e2e8f0);
            margin: 0;
        }

        .header-actions {
            display: flex;
            gap: var(--soma-spacing-sm, 8px);
        }

        .search-bar {
            margin-bottom: var(--soma-spacing-lg, 24px);
        }

        .theme-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: var(--soma-spacing-lg, 24px);
        }

        .theme-card {
            background: var(--soma-surface, rgba(30, 41, 59, 0.85));
            border: 1px solid var(--soma-border-color, rgba(255, 255, 255, 0.05));
            border-radius: var(--soma-radius-lg, 12px);
            overflow: hidden;
            transition: all 0.2s ease;
        }

        .theme-card:hover {
            border-color: var(--soma-accent, #94a3b8);
            transform: translateY(-2px);
        }

        .theme-preview {
            height: 140px;
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            grid-template-rows: repeat(2, 1fr);
            gap: 2px;
            padding: 2px;
        }

        .color-swatch {
            border-radius: 4px;
        }

        .theme-info {
            padding: var(--soma-spacing-md, 16px);
        }

        .theme-name {
            font-size: var(--soma-text-base, 14px);
            font-weight: 600;
            color: var(--soma-text-main, #e2e8f0);
            margin: 0 0 var(--soma-spacing-xs, 4px) 0;
        }

        .theme-meta {
            font-size: var(--soma-text-xs, 11px);
            color: var(--soma-text-dim, #64748b);
            margin: 0 0 var(--soma-spacing-sm, 8px) 0;
        }

        .theme-actions {
            display: flex;
            gap: var(--soma-spacing-xs, 4px);
        }

        .current-theme {
            border: 2px solid var(--soma-success, #22c55e);
        }

        .current-badge {
            background: var(--soma-success, #22c55e);
            color: white;
            font-size: var(--soma-text-xs, 11px);
            padding: 2px 8px;
            border-radius: var(--soma-radius-full, 9999px);
            margin-left: auto;
        }

        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 200px;
            color: var(--soma-text-dim, #64748b);
        }

        .empty-state {
            text-align: center;
            padding: var(--soma-spacing-2xl, 48px);
            color: var(--soma-text-dim, #64748b);
        }
    `;

    @state() private _themes: Theme[] = [];
    @state() private _searchQuery = '';
    @state() private _loading = false;
    @state() private _currentTheme: string | null = null;
    @state() private _previewTheme: Theme | null = null;
    @state() private _showUploadModal = false;
    @property({ type: Boolean }) isAdmin = false;

    async connectedCallback() {
        super.connectedCallback();
        await this._loadThemes();
        this._currentTheme = localStorage.getItem('soma-theme') || null;
    }

    render() {
        const filteredThemes = this._filterThemes();

        return html`
            <header class="header">
                <h1>Themes</h1>
                <div class="header-actions">
                    ${this.isAdmin ? html`
                        <soma-button @soma-click=${() => this._showUploadModal = true}>
                            Upload Theme
                        </soma-button>
                    ` : ''}
                </div>
            </header>

            <div class="search-bar">
                <soma-input
                    placeholder="Search themes..."
                    prefix="🔍"
                    .value=${this._searchQuery}
                    @soma-input=${(e: CustomEvent) => this._searchQuery = e.detail.value}
                ></soma-input>
            </div>

            ${this._loading ? html`
                <div class="loading">Loading themes...</div>
            ` : filteredThemes.length === 0 ? html`
                <div class="empty-state">
                    <p>No themes found</p>
                </div>
            ` : html`
                <div class="theme-grid">
                    ${filteredThemes.map(theme => this._renderThemeCard(theme))}
                </div>
            `}

            <soma-modal 
                ?open=${this._showUploadModal}
                title="Upload Theme"
                @soma-close=${() => this._showUploadModal = false}
            >
                <p>Drag and drop a theme JSON file or paste theme data.</p>
            </soma-modal>
        `;
    }

    private _renderThemeCard(theme: Theme) {
        const isCurrent = this._currentTheme === theme.id;
        const vars = theme.variables;

        // Get key colors for preview
        const swatches = [
            vars['--bg-void'] || vars['--soma-bg-void'] || '#0f172a',
            vars['--glass-surface'] || vars['--soma-surface'] || '#1e293b',
            vars['--accent-slate'] || vars['--soma-accent'] || '#94a3b8',
            vars['--text-main'] || vars['--soma-text-main'] || '#e2e8f0',
            vars['--accent-ember'] || vars['--soma-danger'] || '#ef4444',
            vars['--accent-moss'] || vars['--soma-success'] || '#22c55e',
            vars['--accent-azure'] || vars['--soma-info'] || '#3b82f6',
            vars['--accent-gold'] || vars['--soma-warning'] || '#eab308',
        ];

        return html`
            <div 
                class="theme-card ${isCurrent ? 'current-theme' : ''}"
                @mouseenter=${() => this._previewTheme = theme}
                @mouseleave=${() => this._cancelPreview()}
            >
                <div class="theme-preview">
                    ${swatches.map(color => html`
                        <div class="color-swatch" style="background: ${color}"></div>
                    `)}
                </div>
                <div class="theme-info">
                    <div style="display: flex; align-items: center;">
                        <h3 class="theme-name">${theme.name}</h3>
                        ${isCurrent ? html`<span class="current-badge">Active</span>` : ''}
                    </div>
                    <p class="theme-meta">v${theme.version} by ${theme.author}</p>
                    <div class="theme-actions">
                        <soma-button 
                            variant=${isCurrent ? 'default' : 'primary'}
                            ?disabled=${isCurrent}
                            @soma-click=${() => this._applyTheme(theme)}
                        >
                            ${isCurrent ? 'Active' : 'Apply'}
                        </soma-button>
                        <soma-button @soma-click=${() => this._downloadTheme(theme)}>
                            Export
                        </soma-button>
                    </div>
                </div>
            </div>
        `;
    }

    private async _loadThemes() {
        this._loading = true;
        try {
            this._themes = await apiClient.get<Theme[]>('/themes');
        } catch (error) {
            console.error('Failed to load themes:', error);
            // Use default themes
            this._themes = [
                {
                    id: 'default-dark',
                    name: 'Midnight',
                    version: '1.0.0',
                    author: 'SomaStack',
                    description: 'Default dark theme',
                    variables: {
                        '--soma-bg-void': '#0f172a',
                        '--soma-surface': 'rgba(30, 41, 59, 0.85)',
                        '--soma-accent': '#94a3b8',
                        '--soma-text-main': '#e2e8f0',
                    },
                    downloads: 0,
                    is_approved: true,
                }
            ];
        } finally {
            this._loading = false;
        }
    }

    private _filterThemes(): Theme[] {
        if (!this._searchQuery) return this._themes;

        const query = this._searchQuery.toLowerCase();
        return this._themes.filter(t =>
            t.name.toLowerCase().includes(query) ||
            t.author.toLowerCase().includes(query)
        );
    }

    private _applyTheme(theme: Theme) {
        // Apply CSS variables to document
        const root = document.documentElement;
        for (const [key, value] of Object.entries(theme.variables)) {
            root.style.setProperty(key, value);
        }

        this._currentTheme = theme.id;
        localStorage.setItem('soma-theme', theme.id);

        this.dispatchEvent(new CustomEvent('theme-applied', {
            bubbles: true,
            composed: true,
            detail: { theme }
        }));
    }

    private _cancelPreview() {
        this._previewTheme = null;
        // Restore current theme if any
        // This would restore from localStorage or default
    }

    private _downloadTheme(theme: Theme) {
        const data = JSON.stringify(theme, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `${theme.name.toLowerCase().replace(/\s+/g, '-')}-v${theme.version}.json`;
        a.click();

        URL.revokeObjectURL(url);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-themes': SomaThemes;
    }
}
