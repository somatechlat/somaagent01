/**
 * Infrastructure Status Card
 * Renders an individual service or component status card.
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import {
  SERVICE_ICONS,
  type ServiceHealth,
  type ComponentHealth,
} from '../controllers/infra-dashboard-controller.js';

@customElement('soma-infra-status-card')
export class SomaInfraStatusCard extends LitElement {
  @property({ type: Object }) service?: ServiceHealth;
  @property({ type: Object }) component?: ComponentHealth;

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

    .service-card {
      background: var(--soma-bg-card, #ffffff);
      border: 1px solid var(--soma-border-light, #e0e0e0);
      border-radius: 12px;
      padding: 20px;
      transition: all 0.15s ease;
    }

    .service-card:hover {
      border-color: var(--soma-border-medium, #ccc);
      box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    }

    .service-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }

    .service-name {
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: 600;
      font-size: 14px;
      text-transform: capitalize;
    }

    .service-icon {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      background: var(--soma-bg-hover, #fafafa);
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .service-icon .material-symbols-outlined { font-size: 16px; }

    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
    }

    .status-badge.healthy {
      background: rgba(34, 197, 94, 0.15);
      color: #16a34a;
    }

    .status-badge.degraded {
      background: rgba(245, 158, 11, 0.15);
      color: #d97706;
    }

    .status-badge.down {
      background: rgba(239, 68, 68, 0.15);
      color: #dc2626;
    }

    .status-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
    }

    .status-dot.healthy { background: var(--soma-status-success, #22c55e); }
    .status-dot.degraded { background: var(--soma-status-warning, #f59e0b); }
    .status-dot.down { background: var(--soma-status-danger, #ef4444); }

    .service-details {
      font-size: 12px;
      color: var(--soma-text-muted, #999);
      margin-bottom: 8px;
    }

    .latency {
      font-size: 11px;
      font-family: var(--soma-font-mono, monospace);
      color: var(--soma-text-muted, #999);
    }

    .error-box {
      margin-top: 10px;
      padding: 10px;
      background: rgba(239, 68, 68, 0.08);
      border: 1px solid rgba(239, 68, 68, 0.2);
      border-radius: 6px;
      font-size: 11px;
      color: #dc2626;
    }

    .component-card {
      background: var(--soma-bg-card, #ffffff);
      border: 1px solid var(--soma-border-light, #e0e0e0);
      border-radius: 12px;
      padding: 16px;
      transition: all 0.15s ease;
    }

    .component-card:hover {
      border-color: var(--soma-border-medium, #ccc);
      box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    }

    .component-card.unhealthy {
      border-color: rgba(239, 68, 68, 0.3);
      background: rgba(239, 68, 68, 0.02);
    }

    .component-name {
      font-weight: 600;
      font-size: 14px;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 8px;
      text-transform: capitalize;
    }

    .component-stats {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      font-size: 11px;
      color: var(--soma-text-muted, #999);
    }

    .component-stat {
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .component-stat .material-symbols-outlined { font-size: 14px; }

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

    .circuit-badge {
      font-size: 10px;
      padding: 2px 6px;
      border-radius: 4px;
      text-transform: uppercase;
      font-weight: 600;
    }

    .circuit-badge.closed { background: rgba(34, 197, 94, 0.15); color: #16a34a; }
    .circuit-badge.open { background: rgba(239, 68, 68, 0.15); color: #dc2626; }
    .circuit-badge.half_open { background: rgba(245, 158, 11, 0.15); color: #d97706; }
  `;

  render() {
    if (this.service) return this.renderService(this.service);
    if (this.component) return this.renderComponent(this.component);
    return nothing;
  }

  private renderService(s: ServiceHealth) {
    return html`
      <div class="service-card">
        <div class="service-header">
          <span class="service-name">
            <div class="service-icon">
              <span class="material-symbols-outlined">${SERVICE_ICONS[s.name] || 'settings'}</span>
            </div>
            ${s.name}
          </span>
          <span class="status-badge ${s.status}">
            <span class="status-dot ${s.status}"></span>
            ${s.status}
          </span>
        </div>
        ${s.details && Object.keys(s.details).length > 0 ? html`
          <div class="service-details">
            ${Object.entries(s.details).map(([k, v]) => html`${k}: ${v}<br>`)}
          </div>
        ` : nothing}
        ${typeof s.latency_ms === 'number' ? html`<div class="latency">${s.latency_ms}ms</div>` : nothing}
        ${s.error ? html`<div class="error-box">${s.error}</div>` : nothing}
      </div>
    `;
  }

  private renderComponent(c: ComponentHealth) {
    return html`
      <div class="component-card ${!c.healthy ? 'unhealthy' : ''}">
        <div class="component-name">
          <div class="service-icon">
            <span class="material-symbols-outlined">${SERVICE_ICONS[c.name] || 'settings'}</span>
          </div>
          ${c.name}
          <span class="deg-badge ${c.degradation_level}">${c.degradation_level}</span>
        </div>
        <div class="component-stats">
          <span class="component-stat">
            <span class="material-symbols-outlined">speed</span>
            ${typeof c.response_time === 'number' ? c.response_time + 's' : '—'}
          </span>
          <span class="component-stat">
            <span class="material-symbols-outlined">error_outline</span>
            {typeof c.error_rate === 'number' ? c.error_rate : '—'} error rate
          </span>
          <span class="circuit-badge ${c.circuit_state}">${c.circuit_state}</span>
        </div>
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'soma-infra-status-card': SomaInfraStatusCard;
  }
}
