/**
 * User Profile Card Component  
 * Displays user avatar, info, and actions.
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Reusable across all admin levels
 * - Action slots for customization
 *
 * PERSONAS APPLIED:
 * - palette UX Consultant: Clear visual hierarchy
 * - lock Security: Role and permission display
 * - bolt Performance: Efficient rendering
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property } from 'lit/decorators.js';

export interface UserProfileData {
    id: string;
    email: string;
    displayName: string;
    avatarUrl?: string;
    role: string;
    roleLabel: string;
    status: 'active' | 'pending' | 'suspended' | 'archived';
    lastSeen?: string;
    mfaEnabled?: boolean;
}

@customElement('saas-user-profile-card')
export class SaasUserProfileCard extends LitElement {
    static styles = css`
        .status-icon {
            font-size: 8px;
            line-height: 1;
            vertical-align: middle;
        }
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

    .profile-card {
      display: flex;
      align-items: flex-start;
      gap: var(--saas-space-lg, 24px);
      padding: var(--saas-space-lg, 24px);
      background: var(--saas-bg-card, #ffffff);
      border: 1px solid var(--saas-border-light, #e0e0e0);
      border-radius: var(--saas-radius-lg, 12px);
    }

    .avatar {
      width: 80px;
      height: 80px;
      border-radius: var(--saas-radius-full, 9999px);
      background: var(--saas-bg-surface, #fafafa);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 32px;
      font-weight: 600;
      color: var(--saas-text-secondary, #666666);
      flex-shrink: 0;
      overflow: hidden;
    }

    .avatar img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .profile-info {
      flex: 1;
      min-width: 0;
    }

    .profile-header {
      display: flex;
      align-items: center;
      gap: var(--saas-space-sm, 8px);
      margin-bottom: var(--saas-space-xs, 4px);
    }

    .profile-name {
      font-size: var(--saas-text-xl, 18px);
      font-weight: var(--saas-font-semibold, 600);
      color: var(--saas-text-primary, #1a1a1a);
    }

    .profile-status {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 8px;
      border-radius: var(--saas-radius-full, 9999px);
      font-size: var(--saas-text-xs, 11px);
      font-weight: var(--saas-font-medium, 500);
    }

    .status-active {
      background: #dcfce7;
      color: #166534;
    }

    .status-pending {
      background: #fef3c7;
      color: #92400e;
    }

    .status-suspended {
      background: #fee2e2;
      color: #991b1b;
    }

    .status-archived {
      background: #f3f4f6;
      color: #6b7280;
    }

    .profile-email {
      font-size: var(--saas-text-sm, 13px);
      color: var(--saas-text-secondary, #666666);
      margin-bottom: var(--saas-space-md, 16px);
    }

    .profile-meta {
      display: flex;
      flex-wrap: wrap;
      gap: var(--saas-space-lg, 24px);
      font-size: var(--saas-text-sm, 13px);
    }

    .meta-item {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .meta-label {
      color: var(--saas-text-muted, #999999);
      font-size: var(--saas-text-xs, 11px);
      text-transform: uppercase;
    }

    .meta-value {
      color: var(--saas-text-primary, #1a1a1a);
      font-weight: var(--saas-font-medium, 500);
    }

    .role-badge {
      display: inline-block;
      padding: 4px 10px;
      background: var(--saas-bg-accent, #2563eb);
      color: white;
      border-radius: var(--saas-radius-sm, 4px);
      font-size: var(--saas-text-xs, 11px);
      font-weight: var(--saas-font-semibold, 600);
      text-transform: uppercase;
    }

    .role-sysadmin { background: #dc2626; }
    .role-admin { background: #f97316; }
    .role-developer { background: #8b5cf6; }
    .role-trainer { background: #06b6d4; }
    .role-user { background: #22c55e; }
    .role-viewer { background: #6b7280; }

    .mfa-indicator {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-size: var(--saas-text-xs, 11px);
    }

    .mfa-enabled { color: #16a34a; }
    .mfa-disabled { color: #dc2626; }

    .profile-actions {
      display: flex;
      flex-direction: column;
      gap: var(--saas-space-sm, 8px);
    }

    .profile-actions ::slotted(button) {
      min-width: 120px;
    }
  `;

    @property({ type: Object }) user: UserProfileData | null = null;

    @property({ type: Boolean }) showActions = true;

    private _getInitials(name: string): string {
        return name
            .split(' ')
            .map(n => n[0])
            .join('')
            .toUpperCase()
            .slice(0, 2);
    }

    private _getRoleClass(role: string): string {
        return `role-${role.toLowerCase()}`;
    }

    private _getStatusClass(status: string): string {
        return `status-${status}`;
    }

    private _formatLastSeen(lastSeen?: string): string {
        if (!lastSeen) return 'Never';
        const date = new Date(lastSeen);
        const now = new Date();
        const diff = now.getTime() - date.getTime();

        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)} min ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)} hours ago`;
        return date.toLocaleDateString();
    }

    render() {
        if (!this.user) return nothing;

        return html`
      <div class="profile-card">
        <div class="avatar">
          ${this.user.avatarUrl
                ? html`<img src="${this.user.avatarUrl}" alt="${this.user.displayName}">`
                : this._getInitials(this.user.displayName)
            }
        </div>

        <div class="profile-info">
          <div class="profile-header">
            <span class="profile-name">${this.user.displayName}</span>
            <span class="profile-status ${this._getStatusClass(this.user.status)}">
              ${this.user.status === 'active' ? html`<span class="material-symbols-outlined status-icon" style="color: #22c55e">circle</span>` :
                this.user.status === 'pending' ? html`<span class="material-symbols-outlined status-icon" style="color: #f59e0b">circle</span>` :
                    this.user.status === 'suspended' ? html`<span class="material-symbols-outlined status-icon" style="color: #ef4444">circle</span>` : html`<span class="material-symbols-outlined status-icon" style="color: #6b7280">circle</span>`}
              ${this.user.status.charAt(0).toUpperCase() + this.user.status.slice(1)}
            </span>
          </div>
          <div class="profile-email">${this.user.email}</div>

          <div class="profile-meta">
            <div class="meta-item">
              <span class="meta-label">Role</span>
              <span class="role-badge ${this._getRoleClass(this.user.role)}">
                ${this.user.roleLabel}
              </span>
            </div>
            <div class="meta-item">
              <span class="meta-label">Last Seen</span>
              <span class="meta-value">${this._formatLastSeen(this.user.lastSeen)}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">MFA</span>
              <span class="mfa-indicator ${this.user.mfaEnabled ? 'mfa-enabled' : 'mfa-disabled'}">
                ${this.user.mfaEnabled ? html`<span class='material-symbols-outlined'>check_circle</span> Enabled` : html`<span class='material-symbols-outlined'>cancel</span> Disabled`}
              </span>
            </div>
          </div>
        </div>

        ${this.showActions ? html`
          <div class="profile-actions">
            <slot name="actions"></slot>
          </div>
        ` : ''}
      </div>
    `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-user-profile-card': SaasUserProfileCard;
    }
}
