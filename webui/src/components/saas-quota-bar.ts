/**
 * Quota Bar Component
 * Displays usage progress with color-coded status.
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Reusable across views
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('saas-quota-bar')
export class SaasQuotaBar extends LitElement {
    static styles = css`
    :host {
      display: block;
    }

    .quota-container {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .quota-header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
    }

    .quota-label {
      font-size: var(--saas-text-sm, 13px);
      font-weight: 500;
      color: var(--saas-text-primary, #1a1a1a);
    }

    .quota-value {
      font-size: var(--saas-text-sm, 13px);
      color: var(--saas-text-secondary, #666666);
    }

    .quota-value .current {
      font-weight: 600;
    }

    .bar-container {
      width: 100%;
      height: 6px;
      background: var(--saas-border, #e0e0e0);
      border-radius: 3px;
      overflow: hidden;
    }

    .bar-fill {
      height: 100%;
      border-radius: 3px;
      transition: width 0.3s ease;
    }

    .bar-fill.status-ok {
      background: var(--saas-success, #22c55e);
    }

    .bar-fill.status-warning {
      background: var(--saas-warning, #f59e0b);
    }

    .bar-fill.status-danger {
      background: var(--saas-error, #dc2626);
    }

    .quota-sublabel {
      font-size: var(--saas-text-xs, 11px);
      color: var(--saas-text-muted, #999999);
    }
  `;

    @property({ type: String }) label = '';
    @property({ type: Number }) used = 0;
    @property({ type: Number }) limit = 100;
    @property({ type: String }) unit = '';
    @property({ type: Boolean }) showLabel = true;
    @property({ type: Boolean }) showValue = true;

    private _getPercentage(): number {
        if (this.limit <= 0) return 0;
        return Math.min((this.used / this.limit) * 100, 100);
    }

    private _getStatus(): 'ok' | 'warning' | 'danger' {
        const pct = this._getPercentage();
        if (pct >= 90) return 'danger';
        if (pct >= 75) return 'warning';
        return 'ok';
    }

    private _formatValue(value: number): string {
        if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
        if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
        return value.toString();
    }

    render() {
        const pct = this._getPercentage();
        const status = this._getStatus();
        const limitDisplay = this.limit > 999999 ? '∞' : this._formatValue(this.limit);

        return html`
      <div class="quota-container">
        ${this.showLabel || this.showValue ? html`
          <div class="quota-header">
            ${this.showLabel ? html`<span class="quota-label">${this.label}</span>` : ''}
            ${this.showValue ? html`
              <span class="quota-value">
                <span class="current">${this._formatValue(this.used)}</span>
                / ${limitDisplay}${this.unit ? ` ${this.unit}` : ''}
              </span>
            ` : ''}
          </div>
        ` : ''}
        <div class="bar-container">
          <div class="bar-fill status-${status}" style="width: ${pct}%"></div>
        </div>
      </div>
    `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-quota-bar': SaasQuotaBar;
    }
}
