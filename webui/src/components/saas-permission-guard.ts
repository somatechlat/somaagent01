/**
 * Permission Guard Component
 * Wraps content and shows/hides based on user permissions.
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Integrates with Django permission API
 * - Supports multiple fallback modes
 *
 * PERSONAS APPLIED:
 * - 🔒 Security Auditor: Permission enforcement
 * - 🎨 UX Consultant: Fallback modes for better UX
 * - 🏗️ Django Architect: Backend integration
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

@customElement('saas-permission-guard')
export class SaasPermissionGuard extends LitElement {
    static styles = css`
    :host {
      display: contents;
    }

    .guard-hidden {
      display: none !important;
    }

    .guard-disabled {
      pointer-events: none;
      opacity: 0.5;
      cursor: not-allowed;
    }

    .guard-message {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: var(--saas-space-xl, 32px);
      background: var(--saas-bg-surface, #fafafa);
      border: 1px dashed var(--saas-border-light, #e0e0e0);
      border-radius: var(--saas-radius-lg, 12px);
      text-align: center;
    }

    .guard-icon {
      font-size: 48px;
      margin-bottom: var(--saas-space-md, 16px);
      opacity: 0.5;
    }

    .guard-title {
      font-size: var(--saas-text-lg, 16px);
      font-weight: var(--saas-font-semibold, 600);
      color: var(--saas-text-primary, #1a1a1a);
      margin-bottom: var(--saas-space-sm, 8px);
    }

    .guard-desc {
      font-size: var(--saas-text-sm, 13px);
      color: var(--saas-text-muted, #999999);
      margin-bottom: var(--saas-space-md, 16px);
    }

    .guard-permission {
      font-family: var(--saas-font-mono, monospace);
      font-size: var(--saas-text-xs, 11px);
      color: var(--saas-text-secondary, #666666);
      background: var(--saas-bg-code, #f0f0f0);
      padding: 2px 8px;
      border-radius: var(--saas-radius-sm, 4px);
    }

    .guard-actions {
      display: flex;
      gap: var(--saas-space-sm, 8px);
      margin-top: var(--saas-space-md, 16px);
    }

    .btn {
      padding: 8px 16px;
      border-radius: var(--saas-radius-md, 8px);
      font-size: var(--saas-text-sm, 13px);
      font-weight: var(--saas-font-medium, 500);
      cursor: pointer;
      border: 1px solid var(--saas-border-light, #e0e0e0);
      background: var(--saas-bg-card, #ffffff);
      color: var(--saas-text-primary, #1a1a1a);
      transition: all 0.15s ease;
    }

    .btn:hover {
      background: var(--saas-bg-hover, #fafafa);
    }
  `;

    /** Required permission to view content */
    @property({ type: String }) permission = '';

    /** Multiple permissions (OR logic) */
    @property({ type: Array }) permissions: string[] = [];

    /** Fallback behavior: hide, disable, or message */
    @property({ type: String }) fallback: 'hide' | 'disable' | 'message' = 'hide';

    /** Cached user permissions from backend */
    @state() private userPermissions: Set<string> = new Set();

    /** Loading state */
    @state() private loading = true;

    /** Has permission */
    @state() private hasPermission = false;

    connectedCallback() {
        super.connectedCallback();
        this._checkPermissions();
    }

    private async _checkPermissions() {
        this.loading = true;
        try {
            // Check cache first
            const cached = sessionStorage.getItem('user_permissions');
            if (cached) {
                this.userPermissions = new Set(JSON.parse(cached));
            } else {
                // Fetch from Django API
                const token = localStorage.getItem('auth_token');
                const res = await fetch('/api/v2/auth/permissions', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    const data = await res.json();
                    this.userPermissions = new Set(data.permissions || []);
                    sessionStorage.setItem('user_permissions', JSON.stringify(data.permissions));
                }
            }

            // Check if user has required permission
            const requiredPerms = this.permission ? [this.permission] : this.permissions;
            this.hasPermission = requiredPerms.length === 0 ||
                requiredPerms.some(p => this.userPermissions.has(p) || this.userPermissions.has('*'));
        } catch (e) {
            console.error('Failed to check permissions:', e);
            // Fail secure - deny access on error
            this.hasPermission = false;
        } finally {
            this.loading = false;
        }
    }

    private _goBack() {
        window.history.back();
    }

    private _requestAccess() {
        // Could trigger a request access flow
        const event = new CustomEvent('request-access', {
            detail: { permission: this.permission || this.permissions },
            bubbles: true,
            composed: true
        });
        this.dispatchEvent(event);
    }

    render() {
        if (this.loading) {
            return html`<slot></slot>`;
        }

        if (this.hasPermission) {
            return html`<slot></slot>`;
        }

        // No permission - apply fallback
        switch (this.fallback) {
            case 'hide':
                return nothing;

            case 'disable':
                return html`
          <div class="guard-disabled">
            <slot></slot>
          </div>
        `;

            case 'message':
                return html`
          <div class="guard-message">
            <div class="guard-icon">🔒</div>
            <div class="guard-title">Permission Required</div>
            <div class="guard-desc">You don't have permission to access this content.</div>
            <div class="guard-permission">${this.permission || this.permissions.join(' or ')}</div>
            <div class="guard-actions">
              <button class="btn" @click=${this._goBack}>Go Back</button>
              <button class="btn" @click=${this._requestAccess}>Request Access</button>
            </div>
          </div>
        `;

            default:
                return nothing;
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-permission-guard': SaasPermissionGuard;
    }
}
