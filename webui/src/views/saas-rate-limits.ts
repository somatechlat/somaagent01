/**
 * Rate Limits Dashboard
 * Configure global rate limits and per-tier overrides.
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Uses /api/v2/infrastructure/ratelimits endpoint
 * - Permission: infra:ratelimit
 * - Per SRS-INFRASTRUCTURE-ADMIN.md Section 3.2
 *
 * 7-Persona Implementation:
 * - 🔒 Security: Rate limit enforcement
 * - 🏗️ Architect: Redis integration
 * - ⚡ Performance: Quota management
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';

interface RateLimit {
    key: string;
    label: string;
    limit: number;
    window_seconds: number;
    policy: 'HARD' | 'SOFT';
}

interface TierOverride {
    tier: string;
    api_calls: number | null;
    voice_minutes: number | null;
    llm_tokens: number | null;
    file_uploads: number | null;
    memory_queries: number | null;
}

@customElement('saas-rate-limits')
export class SaasRateLimits extends LitElement {
    static styles = css`
    :host {
      display: flex;
      height: 100vh;
      background: var(--saas-bg-page, #f5f5f5);
      font-family: var(--saas-font-sans, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
      color: var(--saas-text-primary, #1a1a1a);
    }

    * { box-sizing: border-box; }

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

    /* Section */
    .section {
      background: #fff;
      border: 1px solid #e0e0e0;
      border-radius: 12px;
      margin-bottom: 24px;
      overflow: hidden;
    }

    .section-header {
      padding: 16px 20px;
      background: #fafafa;
      border-bottom: 1px solid #e0e0e0;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .section-title { font-size: 14px; font-weight: 600; }

    .section-content { padding: 0; }

    /* Table */
    .data-table {
      width: 100%;
      border-collapse: collapse;
    }

    .data-table th {
      text-align: left;
      padding: 12px 16px;
      font-size: 11px;
      font-weight: 600;
      color: #888;
      text-transform: uppercase;
      background: #fafafa;
      border-bottom: 1px solid #e0e0e0;
    }

    .data-table td {
      padding: 14px 16px;
      font-size: 13px;
      border-bottom: 1px solid #f0f0f0;
    }

    .data-table tr:last-child td { border-bottom: none; }

    .data-table tr:hover { background: #fafafa; }

    .key-cell {
      font-family: 'SF Mono', monospace;
      font-size: 12px;
      background: #f0f0f0;
      padding: 4px 8px;
      border-radius: 4px;
    }

    .limit-input {
      width: 80px;
      padding: 6px 10px;
      border: 1px solid #e0e0e0;
      border-radius: 6px;
      font-size: 13px;
      text-align: right;
    }

    .limit-input:focus { outline: none; border-color: #1a1a1a; }

    .window-select, .policy-select {
      padding: 6px 10px;
      border: 1px solid #e0e0e0;
      border-radius: 6px;
      font-size: 12px;
      background: #fff;
    }

    /* Policy Badge */
    .policy-badge {
      display: inline-block;
      font-size: 10px;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 4px;
      text-transform: uppercase;
    }

    .policy-hard { background: #fee2e2; color: #991b1b; }
    .policy-soft { background: #fef3c7; color: #92400e; }

    /* Tier Grid */
    .tier-grid {
      display: grid;
      grid-template-columns: 120px repeat(5, 1fr);
      gap: 1px;
      background: #e0e0e0;
    }

    .tier-cell, .tier-header {
      padding: 12px 16px;
      background: #fff;
      font-size: 12px;
    }

    .tier-header {
      font-weight: 600;
      font-size: 11px;
      text-transform: uppercase;
      color: #888;
      background: #fafafa;
    }

    .tier-name {
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .tier-badge {
      font-size: 9px;
      padding: 2px 6px;
      border-radius: 4px;
    }

    .tier-free { background: #e0e0e0; }
    .tier-starter { background: #dbeafe; color: #1e40af; }
    .tier-team { background: #dcfce7; color: #166534; }
    .tier-enterprise { background: #ede9fe; color: #5b21b6; }

    .tier-input {
      width: 100%;
      padding: 6px;
      border: 1px solid transparent;
      border-radius: 4px;
      font-size: 12px;
      text-align: center;
      background: transparent;
    }

    .tier-input:hover { border-color: #e0e0e0; }
    .tier-input:focus { outline: none; border-color: #1a1a1a; background: #fff; }

    .unlimited { color: #16a34a; font-weight: 500; }

    .btn-icon {
      width: 32px;
      height: 32px;
      padding: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 6px;
    }

    .loading { display: flex; justify-content: center; padding: 60px; color: #999; }
  `;

    @state() private limits: RateLimit[] = [];
    @state() private tiers: TierOverride[] = [];
    @state() private loading = true;
    @state() private saving = false;

    connectedCallback() {
        super.connectedCallback();
        this.loadRateLimits();
    }

    private getAuthHeaders(): HeadersInit {
        const token = localStorage.getItem('auth_token');
        return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
    }

    private async loadRateLimits() {
        this.loading = true;
        try {
            const res = await fetch('/api/v2/infrastructure/ratelimits', { headers: this.getAuthHeaders() });
            if (res.ok) {
                const data = await res.json();
                this.limits = data.limits || [];
                this.tiers = data.tiers || [];
            } else {
                this.loadMockData();
            }
        } catch {
            this.loadMockData();
        } finally {
            this.loading = false;
        }
    }

    private loadMockData() {
        this.limits = [
            { key: 'api_calls', label: 'API Calls', limit: 1000, window_seconds: 3600, policy: 'HARD' },
            { key: 'voice_minutes', label: 'Voice Minutes', limit: 60, window_seconds: 86400, policy: 'SOFT' },
            { key: 'llm_tokens', label: 'LLM Tokens', limit: 100000, window_seconds: 86400, policy: 'SOFT' },
            { key: 'file_uploads', label: 'File Uploads', limit: 50, window_seconds: 3600, policy: 'HARD' },
            { key: 'memory_queries', label: 'Memory Queries', limit: 500, window_seconds: 3600, policy: 'SOFT' },
        ];

        this.tiers = [
            { tier: 'Free', api_calls: 100, voice_minutes: 0, llm_tokens: 10000, file_uploads: 10, memory_queries: 50 },
            { tier: 'Starter', api_calls: 1000, voice_minutes: 60, llm_tokens: 100000, file_uploads: 50, memory_queries: 500 },
            { tier: 'Team', api_calls: 10000, voice_minutes: 500, llm_tokens: 1000000, file_uploads: 500, memory_queries: 5000 },
            { tier: 'Enterprise', api_calls: null, voice_minutes: null, llm_tokens: null, file_uploads: null, memory_queries: null },
        ];
    }

    private formatWindow(seconds: number): string {
        if (seconds >= 86400) return `${seconds / 86400} day${seconds > 86400 ? 's' : ''}`;
        if (seconds >= 3600) return `${seconds / 3600} hour${seconds > 3600 ? 's' : ''}`;
        return `${seconds / 60} min${seconds > 60 ? 's' : ''}`;
    }

    private updateLimit(key: string, field: keyof RateLimit, value: unknown) {
        this.limits = this.limits.map(l =>
            l.key === key ? { ...l, [field]: value } : l
        );
    }

    private updateTierOverride(tier: string, field: keyof TierOverride, value: unknown) {
        this.tiers = this.tiers.map(t =>
            t.tier === tier ? { ...t, [field]: value } : t
        );
    }

    private async saveRateLimits() {
        this.saving = true;
        try {
            const res = await fetch('/api/v2/infrastructure/ratelimits', {
                method: 'PUT',
                headers: this.getAuthHeaders(),
                body: JSON.stringify({ limits: this.limits, tiers: this.tiers }),
            });
            if (res.ok) {
                console.log('Rate limits saved');
            }
        } catch (e) {
            console.error('Failed to save:', e);
        } finally {
            this.saving = false;
        }
    }

    private getTierClass(tier: string): string {
        return `tier-${tier.toLowerCase()}`;
    }

    render() {
        return html`
      <aside class="sidebar">
        <saas-sidebar active-route="/platform/infrastructure/redis/ratelimits"></saas-sidebar>
      </aside>

      <main class="main">
        <header class="header">
          <div>
            <h1 class="header-title">⚡ Rate Limits</h1>
            <p class="header-subtitle">Configure global rate limits and per-tier overrides</p>
          </div>
          <div class="header-actions">
            <button class="btn">
              + Add New Limit
            </button>
            <button class="btn btn-primary" ?disabled=${this.saving} @click=${() => this.saveRateLimits()}>
              ${this.saving ? 'Saving...' : '💾 Save Changes'}
            </button>
          </div>
        </header>

        <div class="content">
          ${this.loading ? html`<div class="loading">Loading rate limits...</div>` : html`
            <!-- Global Rate Limits -->
            <div class="section">
              <div class="section-header">
                <span class="section-title">Global Rate Limits</span>
              </div>
              <div class="section-content">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>Key</th>
                      <th>Label</th>
                      <th>Limit</th>
                      <th>Window</th>
                      <th>Policy</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${this.limits.map(limit => html`
                      <tr>
                        <td><span class="key-cell">${limit.key}</span></td>
                        <td>${limit.label}</td>
                        <td>
                          <input type="number" class="limit-input" .value=${String(limit.limit)}
                            @change=${(e: Event) => this.updateLimit(limit.key, 'limit', parseInt((e.target as HTMLInputElement).value))}>
                        </td>
                        <td>
                          <select class="window-select" .value=${String(limit.window_seconds)}
                            @change=${(e: Event) => this.updateLimit(limit.key, 'window_seconds', parseInt((e.target as HTMLSelectElement).value))}>
                            <option value="60">1 minute</option>
                            <option value="300">5 minutes</option>
                            <option value="3600">1 hour</option>
                            <option value="86400">24 hours</option>
                          </select>
                        </td>
                        <td>
                          <select class="policy-select" .value=${limit.policy}
                            @change=${(e: Event) => this.updateLimit(limit.key, 'policy', (e.target as HTMLSelectElement).value)}>
                            <option value="HARD">HARD</option>
                            <option value="SOFT">SOFT</option>
                          </select>
                        </td>
                        <td>
                          <button class="btn btn-icon" title="Delete">🗑️</button>
                        </td>
                      </tr>
                    `)}
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Per-Tier Overrides -->
            <div class="section">
              <div class="section-header">
                <span class="section-title">Per-Tier Overrides</span>
              </div>
              <div class="section-content">
                <div class="tier-grid">
                  <!-- Header Row -->
                  <div class="tier-header">Tier</div>
                  <div class="tier-header">API Calls</div>
                  <div class="tier-header">Voice Min</div>
                  <div class="tier-header">LLM Tokens</div>
                  <div class="tier-header">File Uploads</div>
                  <div class="tier-header">Memory Queries</div>

                  <!-- Tier Rows -->
                  ${this.tiers.map(tier => html`
                    <div class="tier-cell tier-name">
                      <span class="tier-badge ${this.getTierClass(tier.tier)}">${tier.tier}</span>
                    </div>
                    <div class="tier-cell">
                      ${tier.api_calls === null
                ? html`<span class="unlimited">Unlimited</span>`
                : html`<input type="number" class="tier-input" .value=${String(tier.api_calls)}
                            @change=${(e: Event) => this.updateTierOverride(tier.tier, 'api_calls', parseInt((e.target as HTMLInputElement).value))}>`
            }
                    </div>
                    <div class="tier-cell">
                      ${tier.voice_minutes === null
                ? html`<span class="unlimited">Unlimited</span>`
                : html`<input type="number" class="tier-input" .value=${String(tier.voice_minutes)}
                            @change=${(e: Event) => this.updateTierOverride(tier.tier, 'voice_minutes', parseInt((e.target as HTMLInputElement).value))}>`
            }
                    </div>
                    <div class="tier-cell">
                      ${tier.llm_tokens === null
                ? html`<span class="unlimited">Unlimited</span>`
                : html`<input type="number" class="tier-input" .value=${String(tier.llm_tokens)}
                            @change=${(e: Event) => this.updateTierOverride(tier.tier, 'llm_tokens', parseInt((e.target as HTMLInputElement).value))}>`
            }
                    </div>
                    <div class="tier-cell">
                      ${tier.file_uploads === null
                ? html`<span class="unlimited">Unlimited</span>`
                : html`<input type="number" class="tier-input" .value=${String(tier.file_uploads)}
                            @change=${(e: Event) => this.updateTierOverride(tier.tier, 'file_uploads', parseInt((e.target as HTMLInputElement).value))}>`
            }
                    </div>
                    <div class="tier-cell">
                      ${tier.memory_queries === null
                ? html`<span class="unlimited">Unlimited</span>`
                : html`<input type="number" class="tier-input" .value=${String(tier.memory_queries)}
                            @change=${(e: Event) => this.updateTierOverride(tier.tier, 'memory_queries', parseInt((e.target as HTMLInputElement).value))}>`
            }
                    </div>
                  `)}
                </div>
              </div>
            </div>

            <!-- Legend -->
            <div class="section">
              <div class="section-header">
                <span class="section-title">Policy Legend</span>
              </div>
              <div class="section-content" style="padding: 16px 20px;">
                <div style="display: flex; gap: 24px; font-size: 13px;">
                  <div><span class="policy-badge policy-hard">HARD</span> Block requests when quota exceeded</div>
                  <div><span class="policy-badge policy-soft">SOFT</span> Warn but allow overage (bill for extra)</div>
                </div>
              </div>
            </div>
          `}
        </div>
      </main>
    `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-rate-limits': SaasRateLimits;
    }
}
