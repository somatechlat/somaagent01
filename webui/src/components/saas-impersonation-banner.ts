/**
 * Impersonation Banner Component
 * Shows persistent banner when admin is impersonating another user.
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Security-focused design
 * - Audit logging integration
 *
 * PERSONAS APPLIED:
 * - lock Security Auditor: Session isolation, audit trail
 * - palette UX Consultant: Clear visual indicator
 * - bar_chart Analyst: Time tracking, reason display
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';

@customElement('saas-impersonation-banner')
export class SaasImpersonationBanner extends LitElement {
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
      display: block;
    }

    .banner {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 20px;
      background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
      border-bottom: 2px solid #f59e0b;
      color: #92400e;
      font-size: 13px;
      position: sticky;
      top: 0;
      z-index: 1000;
    }

    .banner-content {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .banner-icon {
      font-size: 18px;
    }

    .banner-text {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .banner-title {
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .banner-user {
      font-weight: 700;
      color: #78350f;
    }

    .banner-meta {
      font-size: 11px;
      color: #a16207;
    }

    .banner-reason {
      font-style: italic;
    }

    .banner-actions {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .banner-timer {
      font-family: var(--saas-font-mono, monospace);
      font-size: 12px;
      background: rgba(255, 255, 255, 0.5);
      padding: 4px 8px;
      border-radius: 4px;
    }

    .btn-end {
      padding: 6px 16px;
      background: #92400e;
      color: white;
      border: none;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s ease;
    }

    .btn-end:hover {
      background: #78350f;
    }
  `;

    /** Email of impersonated user */
    @property({ type: String }) userEmail = '';

    /** Name of impersonated user */
    @property({ type: String }) userName = '';

    /** Tenant being impersonated */
    @property({ type: String }) tenantName = '';

    /** Reason for impersonation */
    @property({ type: String }) reason = '';

    /** ISO timestamp when impersonation started */
    @property({ type: String }) startTime = '';

    /** Timer display */
    @state() private elapsed = '00:00:00';

    /** Timer interval */
    private timerInterval?: number;

    connectedCallback() {
        super.connectedCallback();
        this._startTimer();
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }
    }

    private _startTimer() {
        const start = this.startTime ? new Date(this.startTime).getTime() : Date.now();

        this.timerInterval = window.setInterval(() => {
            const now = Date.now();
            const diff = now - start;

            const hours = Math.floor(diff / 3600000).toString().padStart(2, '0');
            const minutes = Math.floor((diff % 3600000) / 60000).toString().padStart(2, '0');
            const seconds = Math.floor((diff % 60000) / 1000).toString().padStart(2, '0');

            this.elapsed = `${hours}:${minutes}:${seconds}`;
        }, 1000);
    }

    private async _endImpersonation() {
        try {
            await apiClient.post('/auth/impersonate/end', {});

            // Clear impersonation state
            sessionStorage.removeItem('impersonation');
            sessionStorage.removeItem('user_permissions');

            // Dispatch event
            this.dispatchEvent(new CustomEvent('impersonation-ended', {
                bubbles: true,
                composed: true
            }));

            // Redirect back to platform admin
            window.location.href = '/platform/tenants';
        } catch (e) {
            console.error('Failed to end impersonation:', e);
        }
    }

    render() {
        return html`
      <div class="banner">
        <div class="banner-content">
          <span class="banner-icon material-symbols-outlined">warning</span>
          <div class="banner-text">
            <div class="banner-title">
              IMPERSONATING: 
              <span class="banner-user">${this.userName || this.userEmail}</span>
              ${this.tenantName ? html`<span>(${this.tenantName})</span>` : ''}
            </div>
            <div class="banner-meta">
              ${this.reason ? html`<span class="banner-reason">Reason: ${this.reason}</span>` : ''}
            </div>
          </div>
        </div>
        <div class="banner-actions">
          <span class="banner-timer"><span class="material-symbols-outlined">timer</span> ${this.elapsed}</span>
          <button class="btn-end" @click=${this._endImpersonation}>
            End Impersonation
          </button>
        </div>
      </div>
    `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-impersonation-banner': SaasImpersonationBanner;
    }
}
