/**
 * Infrastructure Alert List
 * Renders recommendations, mitigation actions, and event history.
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { type HistoryRecord } from '../controllers/infra-dashboard-controller.js';

@customElement('soma-infra-alert-list')
export class SomaInfraAlertList extends LitElement {
  @property({ type: Array }) recommendations: string[] = [];
  @property({ type: Array }) mitigationActions: string[] = [];
  @property({ type: Array }) history: HistoryRecord[] = [];

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

    .card {
      background: var(--soma-bg-card, #ffffff);
      border: 1px solid var(--soma-border-light, #e0e0e0);
      border-radius: 12px;
    }

    table {
      width: 100%;
      border-collapse: collapse;
    }

    th {
      text-align: left;
      padding: 14px 20px;
      font-size: 11px;
      font-weight: 600;
      color: var(--soma-text-muted, #999);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      border-bottom: 1px solid var(--soma-border-light, #e0e0e0);
    }

    td {
      padding: 16px 20px;
      font-size: 14px;
      border-bottom: 1px solid var(--soma-border-light, #e0e0e0);
    }

    tr:last-child td { border-bottom: none; }
    tr:hover td { background: var(--soma-bg-hover, #fafafa); }

    .section-title {
      font-size: 15px;
      font-weight: 600;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .section-title .material-symbols-outlined {
      font-size: 18px;
      color: var(--soma-text-secondary, #666);
    }

    .recommendations-panel {
      background: var(--soma-bg-card, #ffffff);
      border: 1px solid var(--soma-border-light, #e0e0e0);
      border-radius: 12px;
      padding: 20px;
      margin-top: 24px;
    }

    .recommendations-title {
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .recommendations-list {
      list-style: none;
      padding: 0;
      margin: 0;
    }

    .recommendations-list li {
      padding: 8px 12px;
      background: var(--soma-bg-hover, #fafafa);
      border-radius: 6px;
      margin-bottom: 8px;
      font-size: 13px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .recommendations-list li .material-symbols-outlined {
      font-size: 16px;
      color: #f59e0b;
    }

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
    .status-dot.down { background: var(--soma-status-danger, #ef4444); }

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

    .policy-badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
    }

    .policy-badge.HARD { background: rgba(239, 68, 68, 0.15); color: #dc2626; }
    .policy-badge.SOFT { background: rgba(245, 158, 11, 0.15); color: #d97706; }
    .policy-badge.NONE { background: #f3f4f6; color: #6b7280; }
  `;

  render() {
    const hasRecommendations = this.recommendations.length > 0 || this.mitigationActions.length > 0;
    return html`
      ${hasRecommendations ? this.renderRecommendations() : nothing}
      ${this.history.length > 0 ? this.renderHistory() : nothing}
    `;
  }

  private renderRecommendations() {
    return html`
      <div class="recommendations-panel">
        <h4 class="recommendations-title">
          <span class="material-symbols-outlined">lightbulb</span>
          Recommendations & Actions
        </h4>
        <ul class="recommendations-list">
          ${this.recommendations.map(r => html`
            <li>
              <span class="material-symbols-outlined">tips_and_updates</span>
              ${r}
            </li>
          `)}
          ${this.mitigationActions.map(a => html`
            <li>
              <span class="material-symbols-outlined">build</span>
              ${a}
            </li>
          `)}
        </ul>
      </div>
    `;
  }

  private renderHistory() {
    return html`
      <h3 class="section-title" style="margin-top: 32px;">
        <span class="material-symbols-outlined">history</span>
        Event History
      </h3>
      <div class="card">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Component</th>
              <th>Level</th>
              <th>Status</th>
              <th>Response</th>
              <th>Event</th>
            </tr>
          </thead>
          <tbody>
            ${this.history.slice(0, 20).map(h => html`
              <tr>
                <td style="font-family: var(--soma-font-mono, monospace); font-size: 11px;">
                  ${new Date(h.timestamp * 1000).toLocaleTimeString()}
                </td>
                <td><strong style="text-transform: capitalize;">${h.component_name}</strong></td>
                <td><span class="deg-badge ${h.degradation_level}">${h.degradation_level}</span></td>
                <td>
                  <span class="status-badge ${h.healthy ? 'healthy' : 'down'}">
                    <span class="status-dot ${h.healthy ? 'healthy' : 'down'}"></span>
                    ${h.healthy ? 'healthy' : 'unhealthy'}
                  </span>
                </td>
                <td style="font-family: var(--soma-font-mono, monospace); font-size: 11px;">
                  ${h.response_time ? h.response_time.toFixed(3) + 's' : '-'}
                </td>
                <td>
                  <span class="policy-badge ${h.event_type === 'failure' ? 'HARD' : 'SOFT'}">${h.event_type}</span>
                </td>
              </tr>
            `)}
          </tbody>
        </table>
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'soma-infra-alert-list': SomaInfraAlertList;
  }
}
