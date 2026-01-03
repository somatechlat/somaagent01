/**
 * Feature Catalog Dashboard
 * Manage platform features and their tier assignments.
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Uses /api/v2/saas/features endpoints
 * - Permission: platform:manage_features
 * - Per SRS-FEATURE-CATALOG.md Section 10
 *
 * 7-Persona Implementation:
 * - 📈 PM: Feature lifecycle management
 * - 🏗️ Architect: Feature/tier matrix
 * - 🔒 Security: Billable feature tracking
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';

interface Feature {
    id: string;
    code: string;
    name: string;
    description: string;
    category: string;
    is_billable: boolean;
    is_enabled: boolean;
    tiers: string[];
    created_at: string;
}

interface FeatureCategory {
    name: string;
    features: Feature[];
}

@customElement('saas-feature-catalog')
export class SaasFeatureCatalog extends LitElement {
    static styles = css`
    :host {
      display: flex;
      height: 100vh;
      background: var(--saas-bg-page, #f5f5f5);
      font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
      color: var(--saas-text-primary, #1a1a1a);
    }

    * { box-sizing: border-box; }

    .material-symbols-outlined {
      font-family: 'Material Symbols Outlined';
      font-weight: normal;
      font-style: normal;
      font-size: 20px;
      line-height: 1;
      display: inline-block;
    }

    .sidebar { width: 260px; background: #fff; border-right: 1px solid #e0e0e0; flex-shrink: 0; }
    .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

    .header {
      padding: 20px 32px;
      background: #fff;
      border-bottom: 1px solid #e0e0e0;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .header-title { font-size: 22px; font-weight: 600; margin: 0; }
    .header-subtitle { font-size: 13px; color: #999; margin: 4px 0 0 0; }

    .header-actions { display: flex; gap: 12px; }

    .btn {
      padding: 10px 18px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      border: 1px solid #e0e0e0;
      background: #fff;
      transition: all 0.15s;
    }

    .btn:hover { background: #fafafa; }
    .btn-primary { background: #1a1a1a; color: #fff; border-color: #1a1a1a; }
    .btn-primary:hover { background: #333; }

    .content { flex: 1; overflow-y: auto; padding: 32px; }

    /* Stats Row */
    .stats-row {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-bottom: 32px;
    }

    .stat-card {
      background: #fff;
      border: 1px solid #e0e0e0;
      border-radius: 12px;
      padding: 20px;
    }

    .stat-label { font-size: 12px; color: #888; margin-bottom: 4px; }
    .stat-value { font-size: 28px; font-weight: 700; }
    .stat-sublabel { font-size: 11px; color: #666; margin-top: 4px; }

    /* Category Section */
    .category {
      background: #fff;
      border: 1px solid #e0e0e0;
      border-radius: 12px;
      margin-bottom: 24px;
      overflow: hidden;
    }

    .category-header {
      padding: 16px 20px;
      background: #fafafa;
      border-bottom: 1px solid #e0e0e0;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .category-title { font-size: 14px; font-weight: 600; }
    .category-count { font-size: 12px; color: #888; }

    /* Feature Card */
    .feature-grid { padding: 16px; display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }

    .feature-card {
      background: #fafafa;
      border: 1px solid #e0e0e0;
      border-radius: 10px;
      padding: 16px;
      transition: all 0.15s;
    }

    .feature-card:hover { border-color: #999; }

    .feature-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 8px;
    }

    .feature-code {
      font-family: 'SF Mono', monospace;
      font-size: 12px;
      background: #e0e0e0;
      padding: 3px 8px;
      border-radius: 4px;
    }

    .feature-name { font-size: 15px; font-weight: 600; margin-bottom: 4px; }
    .feature-desc { font-size: 12px; color: #666; margin-bottom: 12px; line-height: 1.4; }

    /* Tags */
    .tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }

    .tag {
      font-size: 10px;
      font-weight: 500;
      padding: 3px 8px;
      border-radius: 4px;
      text-transform: uppercase;
    }

    .tag-billable { background: #fef3c7; color: #92400e; }
    .tag-enabled { background: #dcfce7; color: #166534; }
    .tag-disabled { background: #fee2e2; color: #991b1b; }

    /* Tier Pills */
    .tiers { display: flex; flex-wrap: wrap; gap: 4px; }

    .tier-pill {
      font-size: 10px;
      padding: 2px 6px;
      border-radius: 4px;
      background: #e0e0e0;
      color: #666;
    }

    .tier-pill.active { background: #1a1a1a; color: #fff; }

    /* Toggle */
    .toggle-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid #e0e0e0;
    }

    .toggle-label { font-size: 12px; color: #666; }

    .toggle-switch {
      position: relative;
      width: 44px;
      height: 24px;
    }

    .toggle-switch input { opacity: 0; width: 0; height: 0; }

    .toggle-slider {
      position: absolute;
      inset: 0;
      background: #ccc;
      border-radius: 24px;
      cursor: pointer;
      transition: 0.3s;
    }

    .toggle-slider:before {
      content: "";
      position: absolute;
      height: 18px;
      width: 18px;
      left: 3px;
      bottom: 3px;
      background: white;
      border-radius: 50%;
      transition: 0.3s;
    }

    input:checked + .toggle-slider { background: #22c55e; }
    input:checked + .toggle-slider:before { transform: translateX(20px); }

    .loading { display: flex; justify-content: center; align-items: center; padding: 60px; color: #999; }
  `;

    @state() private features: Feature[] = [];
    @state() private loading = true;
    @state() private search = '';

    private readonly tiers = ['free', 'starter', 'team', 'enterprise'];

    connectedCallback() {
        super.connectedCallback();
        this.loadFeatures();
    }

    private getAuthHeaders(): HeadersInit {
        const token = localStorage.getItem('auth_token');
        return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
    }

    private async loadFeatures() {
        this.loading = true;
        try {
            const res = await fetch('/api/v2/saas/features', { headers: this.getAuthHeaders() });
            if (res.ok) {
                const data = await res.json();
                this.features = data.features || [];
            } else {
                this.features = this.getMockFeatures();
            }
        } catch {
            this.features = this.getMockFeatures();
        } finally {
            this.loading = false;
        }
    }

    private getMockFeatures(): Feature[] {
        return [
            { id: '1', code: 'memory', name: 'Long-term Memory', description: 'Vector-based memory recall and consolidation', category: 'Core', is_billable: true, is_enabled: true, tiers: ['starter', 'team', 'enterprise'], created_at: '2025-01-01' },
            { id: '2', code: 'voice', name: 'Voice Mode', description: 'Real-time voice conversation with Whisper + Kokoro', category: 'Communication', is_billable: true, is_enabled: true, tiers: ['team', 'enterprise'], created_at: '2025-01-01' },
            { id: '3', code: 'mcp', name: 'MCP Integration', description: 'Model Context Protocol for external tools', category: 'Extensibility', is_billable: false, is_enabled: true, tiers: ['starter', 'team', 'enterprise'], created_at: '2025-01-01' },
            { id: '4', code: 'browser_agent', name: 'Browser Agent', description: 'Web browsing and automation capabilities', category: 'Capabilities', is_billable: false, is_enabled: true, tiers: ['team', 'enterprise'], created_at: '2025-01-01' },
            { id: '5', code: 'code_execution', name: 'Code Execution', description: 'Sandboxed Python/JS execution', category: 'Capabilities', is_billable: false, is_enabled: true, tiers: ['enterprise'], created_at: '2025-01-01' },
            { id: '6', code: 'vision', name: 'Vision', description: 'Image understanding and analysis', category: 'Capabilities', is_billable: true, is_enabled: true, tiers: ['starter', 'team', 'enterprise'], created_at: '2025-01-01' },
            { id: '7', code: 'delegation', name: 'Agent Delegation', description: 'Multi-agent task delegation', category: 'Advanced', is_billable: false, is_enabled: true, tiers: ['enterprise'], created_at: '2025-01-01' },
            { id: '8', code: 'file_upload', name: 'File Upload', description: 'Upload and process documents', category: 'Core', is_billable: true, is_enabled: true, tiers: ['free', 'starter', 'team', 'enterprise'], created_at: '2025-01-01' },
            { id: '9', code: 'export', name: 'Data Export', description: 'Export conversations and memories', category: 'Data', is_billable: false, is_enabled: true, tiers: ['starter', 'team', 'enterprise'], created_at: '2025-01-01' },
        ];
    }

    private async toggleFeature(feature: Feature) {
        try {
            const res = await fetch(`/api/v2/saas/features/${feature.id}`, {
                method: 'PATCH',
                headers: this.getAuthHeaders(),
                body: JSON.stringify({ is_enabled: !feature.is_enabled }),
            });
            if (res.ok) {
                feature.is_enabled = !feature.is_enabled;
                this.requestUpdate();
            }
        } catch (e) {
            console.error('Failed to toggle feature:', e);
        }
    }

    private get categories(): FeatureCategory[] {
        const filtered = this.search
            ? this.features.filter(f =>
                f.name.toLowerCase().includes(this.search.toLowerCase()) ||
                f.code.toLowerCase().includes(this.search.toLowerCase())
            )
            : this.features;

        const cats: Record<string, Feature[]> = {};
        for (const f of filtered) {
            if (!cats[f.category]) cats[f.category] = [];
            cats[f.category].push(f);
        }
        return Object.entries(cats).map(([name, features]) => ({ name, features }));
    }

    private get stats() {
        return {
            total: this.features.length,
            enabled: this.features.filter(f => f.is_enabled).length,
            billable: this.features.filter(f => f.is_billable).length,
            categories: new Set(this.features.map(f => f.category)).size,
        };
    }

    render() {
        return html`
      <aside class="sidebar">
        <saas-sidebar active-route="/platform/features"></saas-sidebar>
      </aside>

      <main class="main">
        <header class="header">
          <div>
            <h1 class="header-title">🧩 Feature Catalog</h1>
            <p class="header-subtitle">Manage platform features and tier assignments</p>
          </div>
          <div class="header-actions">
            <input type="search" class="btn" placeholder="Search features..."
              @input=${(e: Event) => this.search = (e.target as HTMLInputElement).value}
              style="width: 200px;">
            <button class="btn btn-primary">
              <span class="material-symbols-outlined">add</span>
              New Feature
            </button>
          </div>
        </header>

        <div class="content">
          ${this.loading ? html`<div class="loading">Loading features...</div>` : html`
            <!-- Stats -->
            <div class="stats-row">
              <div class="stat-card">
                <div class="stat-label">Total Features</div>
                <div class="stat-value">${this.stats.total}</div>
                <div class="stat-sublabel">${this.stats.categories} categories</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">Enabled</div>
                <div class="stat-value" style="color: #16a34a;">${this.stats.enabled}</div>
                <div class="stat-sublabel">${Math.round((this.stats.enabled / this.stats.total) * 100)}% active</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">Billable</div>
                <div class="stat-value" style="color: #ca8a04;">${this.stats.billable}</div>
                <div class="stat-sublabel">Usage-based billing</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">Categories</div>
                <div class="stat-value">${this.stats.categories}</div>
                <div class="stat-sublabel">Feature groups</div>
              </div>
            </div>

            <!-- Categories -->
            ${this.categories.map(cat => html`
              <div class="category">
                <div class="category-header">
                  <span class="category-title">${cat.name}</span>
                  <span class="category-count">${cat.features.length} features</span>
                </div>
                <div class="feature-grid">
                  ${cat.features.map(feature => html`
                    <div class="feature-card">
                      <div class="feature-header">
                        <span class="feature-code">${feature.code}</span>
                      </div>
                      <div class="feature-name">${feature.name}</div>
                      <div class="feature-desc">${feature.description}</div>
                      <div class="tags">
                        ${feature.is_billable ? html`<span class="tag tag-billable">💰 Billable</span>` : nothing}
                        <span class="tag ${feature.is_enabled ? 'tag-enabled' : 'tag-disabled'}">
                          ${feature.is_enabled ? '✓ Enabled' : '✗ Disabled'}
                        </span>
                      </div>
                      <div class="tiers">
                        ${this.tiers.map(tier => html`
                          <span class="tier-pill ${feature.tiers.includes(tier) ? 'active' : ''}">${tier}</span>
                        `)}
                      </div>
                      <div class="toggle-row">
                        <span class="toggle-label">Platform Enabled</span>
                        <label class="toggle-switch">
                          <input type="checkbox" .checked=${feature.is_enabled}
                            @change=${() => this.toggleFeature(feature)}>
                          <span class="toggle-slider"></span>
                        </label>
                      </div>
                    </div>
                  `)}
                </div>
              </div>
            `)}
          `}
        </div>
      </main>
    `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-feature-catalog': SaasFeatureCatalog;
    }
}
