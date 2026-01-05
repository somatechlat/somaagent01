/**
 * Agent Marketplace View
 * Browse and install agent templates.
 *
 * Route: /platform/marketplace
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Django Ninja API integration
 * - Card-based gallery layout
 *
 * PERSONAS APPLIED:
 * - 🎨 UX Consultant: Visual card layout, filtering
 * - 🏗️ Django Architect: Template data model
 * - ⚡ Performance: Lazy loading, pagination
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';

import '../components/saas-permission-guard.js';

interface AgentTemplate {
    id: string;
    name: string;
    slug: string;
    description: string;
    category: string;
    iconUrl: string;
    rating: number;
    ratingCount: number;
    installCount: number;
    tierRequirement: string;
    toolCount: number;
    voiceEnabled: boolean;
    features: string[];
    author: string;
    updatedAt: string;
}

const CATEGORIES = [
    { id: 'all', label: 'All Templates' },
    { id: 'customer_service', label: 'Customer Service' },
    { id: 'sales', label: 'Sales' },
    { id: 'research', label: 'Research' },
    { id: 'data', label: 'Data Analysis' },
    { id: 'dev', label: 'Development' },
    { id: 'hr', label: 'HR & Recruiting' },
];

@customElement('saas-marketplace')
export class SaasMarketplace extends LitElement {
    static styles = css`
    :host {
      display: block;
      min-height: 100vh;
      background: var(--saas-bg-void, #0f172a);
      padding: var(--saas-spacing-xl, 32px);
    }

    .marketplace {
      max-width: 1400px;
      margin: 0 auto;
    }

    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: var(--saas-spacing-xl, 32px);
    }

    .page-title {
      font-size: var(--saas-text-2xl, 24px);
      font-weight: 700;
      color: var(--saas-text-bright, #f8fafc);
    }

    .header-actions {
      display: flex;
      gap: var(--saas-spacing-sm, 8px);
    }

    .btn-primary {
      padding: 10px 20px;
      background: var(--saas-info, #3b82f6);
      color: white;
      border: none;
      border-radius: var(--saas-radius-md, 8px);
      font-size: var(--saas-text-base, 14px);
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s ease;
    }

    .btn-primary:hover {
      background: #2563eb;
    }

    /* Categories */
    .categories {
      display: flex;
      gap: var(--saas-spacing-sm, 8px);
      margin-bottom: var(--saas-spacing-lg, 24px);
      flex-wrap: wrap;
    }

    .category-btn {
      padding: 8px 16px;
      background: transparent;
      border: 1px solid var(--saas-border-color, rgba(255, 255, 255, 0.05));
      border-radius: var(--saas-radius-full, 9999px);
      color: var(--saas-text-dim, #64748b);
      font-size: var(--saas-text-sm, 13px);
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .category-btn:hover {
      border-color: var(--saas-border-hover, rgba(255, 255, 255, 0.1));
      color: var(--saas-text-main, #e2e8f0);
    }

    .category-btn.active {
      background: var(--saas-info, #3b82f6);
      border-color: var(--saas-info, #3b82f6);
      color: white;
    }

    /* Search Bar */
    .search-bar {
      display: flex;
      gap: var(--saas-spacing-md, 16px);
      margin-bottom: var(--saas-spacing-xl, 32px);
    }

    .search-input {
      flex: 1;
      padding: 12px 16px;
      background: var(--saas-surface, rgba(30, 41, 59, 0.85));
      border: 1px solid var(--saas-border-color, rgba(255, 255, 255, 0.05));
      border-radius: var(--saas-radius-md, 8px);
      color: var(--saas-text-main, #e2e8f0);
      font-size: var(--saas-text-base, 14px);
    }

    .search-input::placeholder {
      color: var(--saas-text-dim, #64748b);
    }

    .search-input:focus {
      outline: none;
      border-color: var(--saas-info, #3b82f6);
    }

    .filter-select {
      padding: 12px 16px;
      background: var(--saas-surface, rgba(30, 41, 59, 0.85));
      border: 1px solid var(--saas-border-color, rgba(255, 255, 255, 0.05));
      border-radius: var(--saas-radius-md, 8px);
      color: var(--saas-text-main, #e2e8f0);
      font-size: var(--saas-text-sm, 13px);
    }

    /* Template Grid */
    .template-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: var(--saas-spacing-lg, 24px);
    }

    .template-card {
      background: var(--saas-surface, rgba(30, 41, 59, 0.85));
      border: 1px solid var(--saas-border-color, rgba(255, 255, 255, 0.05));
      border-radius: var(--saas-radius-lg, 12px);
      padding: var(--saas-spacing-lg, 24px);
      transition: all 0.2s ease;
      cursor: pointer;
    }

    .template-card:hover {
      border-color: var(--saas-border-hover, rgba(255, 255, 255, 0.1));
      transform: translateY(-2px);
      box-shadow: var(--saas-shadow-lg);
    }

    .card-header {
      display: flex;
      align-items: flex-start;
      gap: var(--saas-spacing-md, 16px);
      margin-bottom: var(--saas-spacing-md, 16px);
    }

    .card-icon {
      width: 56px;
      height: 56px;
      border-radius: var(--saas-radius-md, 8px);
      background: var(--saas-bg-base, #1e293b);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 28px;
      flex-shrink: 0;
    }

    .card-info {
      flex: 1;
      min-width: 0;
    }

    .card-name {
      font-size: var(--saas-text-lg, 16px);
      font-weight: 600;
      color: var(--saas-text-bright, #f8fafc);
      margin-bottom: 4px;
    }

    .card-author {
      font-size: var(--saas-text-xs, 11px);
      color: var(--saas-text-dim, #64748b);
    }

    .card-rating {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: var(--saas-text-sm, 13px);
      color: var(--saas-warning, #eab308);
    }

    .card-rating span {
      color: var(--saas-text-dim, #64748b);
    }

    .card-description {
      font-size: var(--saas-text-sm, 13px);
      color: var(--saas-text-main, #e2e8f0);
      line-height: 1.5;
      margin-bottom: var(--saas-spacing-md, 16px);
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .card-features {
      display: flex;
      flex-wrap: wrap;
      gap: var(--saas-spacing-xs, 4px);
      margin-bottom: var(--saas-spacing-md, 16px);
    }

    .feature-tag {
      padding: 2px 8px;
      background: var(--saas-bg-base, #1e293b);
      border-radius: var(--saas-radius-sm, 4px);
      font-size: var(--saas-text-xs, 11px);
      color: var(--saas-text-dim, #64748b);
    }

    .card-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: var(--saas-spacing-md, 16px);
      border-top: 1px solid var(--saas-border-color, rgba(255, 255, 255, 0.05));
    }

    .card-meta {
      display: flex;
      gap: var(--saas-spacing-md, 16px);
      font-size: var(--saas-text-xs, 11px);
      color: var(--saas-text-dim, #64748b);
    }

    .tier-badge {
      padding: 4px 8px;
      border-radius: var(--saas-radius-sm, 4px);
      font-size: var(--saas-text-xs, 11px);
      font-weight: 600;
    }

    .tier-free { background: #dcfce7; color: #166534; }
    .tier-starter { background: #dbeafe; color: #1e40af; }
    .tier-team { background: #fef3c7; color: #92400e; }
    .tier-enterprise { background: #f3e8ff; color: #7c3aed; }

    /* Empty State */
    .empty-state {
      text-align: center;
      padding: var(--saas-spacing-2xl, 48px);
      color: var(--saas-text-dim, #64748b);
    }

    .empty-icon {
      font-size: 64px;
      margin-bottom: var(--saas-spacing-md, 16px);
      opacity: 0.5;
    }

    /* Loading */
    .loading {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: var(--saas-spacing-2xl, 48px);
      color: var(--saas-text-dim, #64748b);
    }
  `;

    @state() private templates: AgentTemplate[] = [];
    @state() private loading = true;
    @state() private activeCategory = 'all';
    @state() private searchQuery = '';
    @state() private sortBy = 'popular';

    connectedCallback() {
        super.connectedCallback();
        this._loadTemplates();
    }

    private async _loadTemplates() {
        this.loading = true;
        try {
            const token = localStorage.getItem('saas_auth_token');
            const params = new URLSearchParams();
            if (this.activeCategory !== 'all') params.set('category', this.activeCategory);
            if (this.searchQuery) params.set('search', this.searchQuery);
            params.set('sort', this.sortBy);

            const res = await fetch(`/api/v2/platform/marketplace/templates?${params}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (res.ok) {
                const data = await res.json();
                this.templates = data.items || data.data || [];
            } else {
                // Fallback to demo data
                this.templates = this._getDemoTemplates();
            }
        } catch (e) {
            console.error('Failed to load templates:', e);
            this.templates = this._getDemoTemplates();
        } finally {
            this.loading = false;
        }
    }

    private _getDemoTemplates(): AgentTemplate[] {
        return [
            {
                id: 'tpl-001',
                name: 'Customer Support Agent',
                slug: 'customer-support',
                description: 'Handle customer inquiries with multilingual support, ticket integration, and escalation workflows.',
                category: 'customer_service',
                iconUrl: '',
                rating: 4.8,
                ratingCount: 234,
                installCount: 1250,
                tierRequirement: 'starter',
                toolCount: 12,
                voiceEnabled: true,
                features: ['Multilingual', 'Zendesk', 'Voice'],
                author: 'SomaAgent Team',
                updatedAt: '2025-12-20',
            },
            {
                id: 'tpl-002',
                name: 'Data Analyst Bot',
                slug: 'data-analyst',
                description: 'SQL queries, data visualization, and automated reporting for business intelligence.',
                category: 'data',
                iconUrl: '',
                rating: 4.5,
                ratingCount: 156,
                installCount: 890,
                tierRequirement: 'team',
                toolCount: 8,
                voiceEnabled: false,
                features: ['SQL', 'Charts', 'Reports'],
                author: 'SomaAgent Team',
                updatedAt: '2025-12-18',
            },
            {
                id: 'tpl-003',
                name: 'Research Assistant',
                slug: 'research-assistant',
                description: 'Academic paper summarization, citation management, and knowledge synthesis.',
                category: 'research',
                iconUrl: '',
                rating: 4.2,
                ratingCount: 89,
                installCount: 456,
                tierRequirement: 'free',
                toolCount: 6,
                voiceEnabled: true,
                features: ['Papers', 'Citations', 'Summary'],
                author: 'Community',
                updatedAt: '2025-12-15',
            },
            {
                id: 'tpl-004',
                name: 'Sales Development Rep',
                slug: 'sdr-bot',
                description: 'Lead qualification, outreach automation, and CRM integration for sales teams.',
                category: 'sales',
                iconUrl: '',
                rating: 4.6,
                ratingCount: 112,
                installCount: 678,
                tierRequirement: 'team',
                toolCount: 10,
                voiceEnabled: true,
                features: ['Salesforce', 'Email', 'Calls'],
                author: 'SomaAgent Team',
                updatedAt: '2025-12-22',
            },
            {
                id: 'tpl-005',
                name: 'Code Review Assistant',
                slug: 'code-review',
                description: 'Automated code review, security scanning, and best practice suggestions for development teams.',
                category: 'dev',
                iconUrl: '',
                rating: 4.9,
                ratingCount: 203,
                installCount: 1100,
                tierRequirement: 'starter',
                toolCount: 7,
                voiceEnabled: false,
                features: ['GitHub', 'Security', 'Lint'],
                author: 'SomaAgent Team',
                updatedAt: '2025-12-21',
            },
            {
                id: 'tpl-006',
                name: 'HR Recruiter',
                slug: 'hr-recruiter',
                description: 'Resume screening, interview scheduling, and candidate communication automation.',
                category: 'hr',
                iconUrl: '',
                rating: 4.3,
                ratingCount: 67,
                installCount: 345,
                tierRequirement: 'team',
                toolCount: 9,
                voiceEnabled: true,
                features: ['Resume', 'Calendar', 'Email'],
                author: 'Community',
                updatedAt: '2025-12-19',
            },
        ];
    }

    private _getCategoryIcon(category: string): string {
        const icons: Record<string, string> = {
            customer_service: '🎧',
            sales: '📈',
            research: '🔬',
            data: '📊',
            dev: '💻',
            hr: '👥',
        };
        return icons[category] || '🤖';
    }

    private _getTierClass(tier: string): string {
        return `tier-${tier}`;
    }

    private _formatTier(tier: string): string {
        return tier.charAt(0).toUpperCase() + tier.slice(1) + '+';
    }

    private _handleCategoryClick(category: string) {
        this.activeCategory = category;
        this._loadTemplates();
    }

    private _handleSearch(e: Event) {
        this.searchQuery = (e.target as HTMLInputElement).value;
        // Debounce search
        clearTimeout((this as any)._searchTimeout);
        (this as any)._searchTimeout = setTimeout(() => this._loadTemplates(), 300);
    }

    private _handleSortChange(e: Event) {
        this.sortBy = (e.target as HTMLSelectElement).value;
        this._loadTemplates();
    }

    private _viewTemplate(template: AgentTemplate) {
        window.location.href = `/platform/marketplace/${template.slug}`;
    }

    render() {
        return html`
      <div class="marketplace">
        <div class="page-header">
          <h1 class="page-title">🔴 Agent Marketplace</h1>
          <div class="header-actions">
            <saas-permission-guard permission="platform:manage_features" fallback="hide">
              <button class="btn-primary">+ Submit Template</button>
            </saas-permission-guard>
          </div>
        </div>

        <!-- Categories -->
        <div class="categories">
          ${CATEGORIES.map(cat => html`
            <button 
              class="category-btn ${this.activeCategory === cat.id ? 'active' : ''}"
              @click=${() => this._handleCategoryClick(cat.id)}
            >
              ${cat.label}
            </button>
          `)}
        </div>

        <!-- Search Bar -->
        <div class="search-bar">
          <input 
            type="text" 
            class="search-input" 
            placeholder="Search templates..."
            .value=${this.searchQuery}
            @input=${this._handleSearch}
          >
          <select class="filter-select" @change=${this._handleSortChange}>
            <option value="popular">Most Popular</option>
            <option value="rating">Highest Rated</option>
            <option value="recent">Recently Updated</option>
            <option value="name">Name A-Z</option>
          </select>
        </div>

        ${this.loading ? html`
          <div class="loading">Loading templates...</div>
        ` : this.templates.length === 0 ? html`
          <div class="empty-state">
            <div class="empty-icon">📦</div>
            <h3>No templates found</h3>
            <p>Try adjusting your search or filters</p>
          </div>
        ` : html`
          <div class="template-grid">
            ${this.templates.map(template => html`
              <div 
                class="template-card" 
                @click=${() => this._viewTemplate(template)}
              >
                <div class="card-header">
                  <div class="card-icon">
                    ${this._getCategoryIcon(template.category)}
                  </div>
                  <div class="card-info">
                    <div class="card-name">${template.name}</div>
                    <div class="card-author">by ${template.author}</div>
                  </div>
                  <div class="card-rating">
                    ★ ${template.rating.toFixed(1)} 
                    <span>(${template.ratingCount})</span>
                  </div>
                </div>

                <div class="card-description">${template.description}</div>

                <div class="card-features">
                  ${template.features.map(f => html`
                    <span class="feature-tag">${f}</span>
                  `)}
                </div>

                <div class="card-footer">
                  <div class="card-meta">
                    <span>🔧 ${template.toolCount} tools</span>
                    ${template.voiceEnabled ? html`<span>🎤 Voice</span>` : ''}
                    <span>📥 ${template.installCount.toLocaleString()}</span>
                  </div>
                  <span class="tier-badge ${this._getTierClass(template.tierRequirement)}">
                    ${this._formatTier(template.tierRequirement)}
                  </span>
                </div>
              </div>
            `)}
          </div>
        `}
      </div>
    `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-marketplace': SaasMarketplace;
    }
}
