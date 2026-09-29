/**
 * Rate Limits Dashboard
 * Configure global rate limits and per-tier overrides.
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Uses /api/v2/core/infrastructure/ratelimits endpoint
 * - Permission: infra:ratelimit
 * - Per SRS-INFRASTRUCTURE-ADMIN.md Section 3.2
 *
 * 7-Persona Implementation:
 * - lock Security: Rate limit enforcement
 * - architecture Architect: Redis integration
 * - bolt Performance: Quota management
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';

interface RateLimit {
  key: string;
  label: string;
  limit: number;
  window_seconds: number;
  policy: 'HARD' | 'SOFT';
}

@customElement('saas-rate-limits')
export class SaasRateLimits extends LitElement {
  static styles = css`
        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: 20px;
            line-height: 1;
            letter-spacing: normal;
            text-transform: none;
            display: inline-block;
            white-space: nowrap;
            word-wrap: normal;
            direction: ltr;
            -webkit-font-feature-settings: 'liga';
            -webkit-font-smoothing: antialiased;
        }
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

    .loading { display: flex; justify-content: center; padding: 60px; color: #999; }
  `;

  @state() private limits: RateLimit[] = [];
  @state() private loading = true;
  @state() private saving = false;

  connectedCallback() {
    super.connectedCallback();
    this.loadRateLimits();
  }

  private async loadRateLimits() {
    this.loading = true;
    try {
      const data = await apiClient.get<{ limits?: any[] }>('/core/infrastructure/ratelimits');
      this.limits = (data.limits || []).map((l: any) => ({
        key: l.key,
        label: l.description || l.key,
        limit: l.limit,
        window_seconds: l.window_seconds,
        policy: l.policy,
      }));
    } catch {
      this.limits = [];
    } finally {
      this.loading = false;
    }
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

  private async saveRateLimits() {
    this.saving = true;
    try {
      await Promise.all(
        this.limits.map((limit) =>
          apiClient.put(`/core/infrastructure/ratelimits/${limit.key}`, {
            description: limit.label,
            limit: limit.limit,
            window_seconds: limit.window_seconds,
            policy: limit.policy,
          })
        )
      );
    } catch (e) {
      console.error('Failed to save:', e);
    } finally {
      this.saving = false;
    }
  }

  render() {
    return html`
      <aside class="sidebar">
        <saas-sidebar active-route="/platform/infrastructure/redis/ratelimits"></saas-sidebar>
      </aside>

      <main class="main">
        <header class="header">
          <div>
            <h1 class="header-title"><span class="material-symbols-outlined">bolt</span> Rate Limits</h1>
            <p class="header-subtitle">Configure global rate limits and per-tier overrides</p>
          </div>
          <div class="header-actions">
            <button class="btn">
              + Add New Limit
            </button>
            <button class="btn btn-primary" ?disabled=${this.saving} @click=${() => this.saveRateLimits()}>
              ${this.saving ? 'Saving...' : html`<span class='material-symbols-outlined'>save</span> Save Changes`}
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
                          <button class="btn btn-icon" title="Delete"><span class="material-symbols-outlined">delete</span></button>
                        </td>
                      </tr>
                    `)}
                  </tbody>
                </table>
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
                  <div><span class="policy-badge policy-soft">SOFT</span> Warn but allow overage</div>
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
