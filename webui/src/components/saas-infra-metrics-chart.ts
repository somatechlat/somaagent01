/**
 * Infrastructure Metrics Chart
 * Renders the metrics grid / chart section for health and degradation tabs.
 */

import { LitElement, html, css, type TemplateResult } from 'lit';
import { customElement, property } from 'lit/decorators.js';

export interface InfraMetric {
  label: string;
  value: string | TemplateResult;
  sub: string;
  icon: string;
  featured?: boolean;
  statusClass?: string;
}

@customElement('saas-infra-metrics-chart')
export class SaasInfraMetricsChart extends LitElement {
  @property({ type: Array }) metrics: InfraMetric[] = [];

  static styles = css`
    :host { display: block; }

    * { box-sizing: border-box; }

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

    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 20px;
      margin-bottom: 32px;
    }

    @media (max-width: 1400px) {
      .metrics-grid { grid-template-columns: repeat(2, 1fr); }
    }

    .metric-card {
      background: var(--saas-bg-card, #ffffff);
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: 12px;
      padding: 24px;
      transition: all 0.15s ease;
    }

    .metric-card:hover {
      border-color: var(--saas-border-medium, #ccc);
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    }

    .metric-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 16px;
    }

    .metric-label {
      font-size: 13px;
      color: var(--saas-text-secondary, #666);
      font-weight: 500;
    }

    .metric-icon {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      background: var(--saas-bg-hover, #fafafa);
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .metric-value {
      font-size: 32px;
      font-weight: 700;
      line-height: 1;
      margin-bottom: 8px;
    }

    .metric-value.healthy { color: var(--saas-status-success, #22c55e); }
    .metric-value.degraded { color: var(--saas-status-warning, #f59e0b); }
    .metric-value.down { color: var(--saas-status-danger, #ef4444); }

    .metric-sub {
      font-size: 12px;
      color: var(--saas-text-muted, #999);
    }

    .metric-card.featured {
      background: linear-gradient(135deg, #1a1a1a 0%, #333 100%);
      color: white;
      border-color: #1a1a1a;
    }

    .metric-card.featured .metric-label { color: rgba(255,255,255,0.7); }
    .metric-card.featured .metric-icon { background: rgba(255,255,255,0.15); }
    .metric-card.featured .metric-icon .material-symbols-outlined { color: white; }
    .metric-card.featured .metric-sub { color: rgba(255,255,255,0.6); }
    .metric-card.featured .metric-value { color: white; }

    .deg-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
    }

    .deg-badge.none { background: rgba(34, 197, 94, 0.15); color: #16a34a; }
    .deg-badge.minor { background: rgba(132, 204, 22, 0.15); color: #65a30d; }
    .deg-badge.moderate { background: rgba(245, 158, 11, 0.15); color: #d97706; }
    .deg-badge.severe { background: rgba(249, 115, 22, 0.15); color: #ea580c; }
    .deg-badge.critical { background: rgba(239, 68, 68, 0.15); color: #dc2626; }
  `;

  render() {
    return html`
      <div class="metrics-grid">
        ${this.metrics.map(m => this.renderMetric(m))}
      </div>
    `;
  }

  private renderMetric(m: InfraMetric) {
    return html`
      <div class="metric-card ${m.featured ? 'featured' : ''}">
        <div class="metric-header">
          <span class="metric-label">${m.label}</span>
          <div class="metric-icon"><span class="material-symbols-outlined">${m.icon}</span></div>
        </div>
        <div class="metric-value ${m.statusClass || ''}">${m.value}</div>
        <div class="metric-sub">${m.sub}</div>
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'saas-infra-metrics-chart': SaasInfraMetricsChart;
  }
}
