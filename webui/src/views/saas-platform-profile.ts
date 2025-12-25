/**
 * Platform Admin Profile View
 * SAAS Admin personal profile and settings.
 *
 * Route: /platform/profile
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Django Ninja API integration
 * - Reusable component composition
 *
 * PERSONAS APPLIED:
 * - 🔒 Security Auditor: MFA, sessions
 * - 🎨 UX Consultant: Clean profile layout
 * - 🏗️ Django Architect: API integration
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

// Import reusable components
import '../components/saas-user-profile-card.js';
import '../components/saas-toggle.js';
import '../components/soma-toast.js';

interface AdminProfile {
    id: string;
    email: string;
    displayName: string;
    avatarUrl?: string;
    role: string;
    roles: string[];
    permissions: string[];
    mfaEnabled: boolean;
    lastLogin?: string;
    sessionTimeout: number;
    activeSessions: number;
    apiKeyCount: number;
    notifications: {
        criticalAlerts: boolean;
        billingEvents: boolean;
        weeklyDigest: boolean;
        marketing: boolean;
    };
}

@customElement('saas-platform-profile')
export class SaasPlatformProfile extends LitElement {
    static styles = css`
    :host {
      display: block;
      min-height: 100vh;
      background: var(--eog-bg-void, #0f172a);
      padding: var(--eog-spacing-xl, 32px);
    }

    .profile-page {
      max-width: 1000px;
      margin: 0 auto;
    }

    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: var(--eog-spacing-xl, 32px);
    }

    .page-title {
      font-size: var(--eog-text-2xl, 24px);
      font-weight: 700;
      color: var(--eog-text-bright, #f8fafc);
    }

    .btn-save {
      padding: 10px 24px;
      background: var(--eog-info, #3b82f6);
      color: white;
      border: none;
      border-radius: var(--eog-radius-md, 8px);
      font-size: var(--eog-text-base, 14px);
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s ease;
    }

    .btn-save:hover {
      background: #2563eb;
    }

    .btn-save:disabled {
      background: var(--eog-text-dim, #64748b);
      cursor: not-allowed;
    }

    .section {
      background: var(--eog-surface, rgba(30, 41, 59, 0.85));
      border: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.05));
      border-radius: var(--eog-radius-lg, 12px);
      padding: var(--eog-spacing-lg, 24px);
      margin-bottom: var(--eog-spacing-lg, 24px);
    }

    .section-title {
      font-size: var(--eog-text-lg, 16px);
      font-weight: 600;
      color: var(--eog-text-bright, #f8fafc);
      margin-bottom: var(--eog-spacing-md, 16px);
      display: flex;
      align-items: center;
      gap: var(--eog-spacing-sm, 8px);
    }

    .form-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: var(--eog-spacing-md, 16px);
      margin-bottom: var(--eog-spacing-md, 16px);
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: var(--eog-spacing-xs, 4px);
    }

    .form-label {
      font-size: var(--eog-text-sm, 13px);
      color: var(--eog-text-dim, #64748b);
    }

    .form-input {
      padding: 10px 12px;
      background: var(--eog-bg-base, #1e293b);
      border: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.05));
      border-radius: var(--eog-radius-md, 8px);
      color: var(--eog-text-main, #e2e8f0);
      font-size: var(--eog-text-base, 14px);
    }

    .form-input:focus {
      outline: none;
      border-color: var(--eog-info, #3b82f6);
    }

    .form-input:disabled {
      opacity: 0.7;
      cursor: not-allowed;
    }

    /* Avatar upload */
    .avatar-section {
      display: flex;
      align-items: center;
      gap: var(--eog-spacing-lg, 24px);
      margin-bottom: var(--eog-spacing-lg, 24px);
    }

    .avatar-preview {
      width: 80px;
      height: 80px;
      border-radius: var(--eog-radius-full, 9999px);
      background: var(--eog-bg-base, #1e293b);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 32px;
      font-weight: 600;
      color: var(--eog-text-dim, #64748b);
      overflow: hidden;
    }

    .avatar-preview img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .avatar-actions {
      display: flex;
      flex-direction: column;
      gap: var(--eog-spacing-sm, 8px);
    }

    .btn-secondary {
      padding: 8px 16px;
      background: transparent;
      border: 1px solid var(--eog-border-hover, rgba(255, 255, 255, 0.1));
      border-radius: var(--eog-radius-md, 8px);
      color: var(--eog-text-main, #e2e8f0);
      font-size: var(--eog-text-sm, 13px);
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .btn-secondary:hover {
      background: var(--eog-surface-hover, rgba(51, 65, 85, 0.9));
    }

    /* Security section */
    .security-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: var(--eog-spacing-md, 16px) 0;
      border-bottom: 1px solid var(--eog-border-color, rgba(255, 255, 255, 0.05));
    }

    .security-item:last-child {
      border-bottom: none;
    }

    .security-info {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .security-label {
      font-size: var(--eog-text-base, 14px);
      color: var(--eog-text-main, #e2e8f0);
    }

    .security-value {
      font-size: var(--eog-text-sm, 13px);
      color: var(--eog-text-dim, #64748b);
    }

    /* Platform access */
    .access-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: var(--eog-spacing-md, 16px);
    }

    .access-item {
      background: var(--eog-bg-base, #1e293b);
      border-radius: var(--eog-radius-md, 8px);
      padding: var(--eog-spacing-md, 16px);
    }

    .access-label {
      font-size: var(--eog-text-xs, 11px);
      color: var(--eog-text-dim, #64748b);
      text-transform: uppercase;
      margin-bottom: var(--eog-spacing-xs, 4px);
    }

    .access-value {
      font-size: var(--eog-text-lg, 16px);
      font-weight: 600;
      color: var(--eog-text-bright, #f8fafc);
    }

    .role-badge {
      display: inline-block;
      padding: 4px 10px;
      background: #dc2626;
      color: white;
      border-radius: var(--eog-radius-sm, 4px);
      font-size: var(--eog-text-xs, 11px);
      font-weight: 600;
    }

    /* Notification toggles */
    .notification-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: var(--eog-spacing-sm, 8px) 0;
    }

    .notification-label {
      font-size: var(--eog-text-base, 14px);
      color: var(--eog-text-main, #e2e8f0);
    }

    /* Action buttons */
    .action-buttons {
      display: flex;
      gap: var(--eog-spacing-sm, 8px);
      flex-wrap: wrap;
    }

    .btn-danger {
      padding: 8px 16px;
      background: transparent;
      border: 1px solid var(--eog-danger, #ef4444);
      border-radius: var(--eog-radius-md, 8px);
      color: var(--eog-danger, #ef4444);
      font-size: var(--eog-text-sm, 13px);
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .btn-danger:hover {
      background: var(--eog-danger, #ef4444);
      color: white;
    }

    .loading {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: var(--eog-spacing-2xl, 48px);
      color: var(--eog-text-dim, #64748b);
    }
  `;

    @state() private profile: AdminProfile | null = null;
    @state() private loading = true;
    @state() private saving = false;
    @state() private dirty = false;

    connectedCallback() {
        super.connectedCallback();
        this._loadProfile();
    }

    private async _loadProfile() {
        this.loading = true;
        try {
            const token = localStorage.getItem('auth_token');
            const res = await fetch('/api/v2/auth/me', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (res.ok) {
                const data = await res.json();
                this.profile = {
                    id: data.id,
                    email: data.email || '',
                    displayName: data.name || data.username || '',
                    avatarUrl: data.avatar_url,
                    role: data.role,
                    roles: data.roles || [],
                    permissions: data.permissions || [],
                    mfaEnabled: data.mfa_enabled ?? true,
                    lastLogin: data.last_login,
                    sessionTimeout: data.session_timeout ?? 30,
                    activeSessions: data.active_sessions ?? 1,
                    apiKeyCount: data.api_key_count ?? 0,
                    notifications: data.notifications || {
                        criticalAlerts: true,
                        billingEvents: true,
                        weeklyDigest: false,
                        marketing: false,
                    },
                };
            }
        } catch (e) {
            console.error('Failed to load profile:', e);
        } finally {
            this.loading = false;
        }
    }

    private async _saveProfile() {
        if (!this.profile) return;

        this.saving = true;
        try {
            const token = localStorage.getItem('auth_token');
            const res = await fetch('/api/v2/platform/profile', {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    display_name: this.profile.displayName,
                    session_timeout: this.profile.sessionTimeout,
                    notifications: this.profile.notifications,
                }),
            });

            if (res.ok) {
                this.dirty = false;
                // Show success toast
                this.dispatchEvent(new CustomEvent('show-toast', {
                    detail: { type: 'success', message: 'Profile updated successfully' },
                    bubbles: true,
                    composed: true,
                }));
            }
        } catch (e) {
            console.error('Failed to save profile:', e);
        } finally {
            this.saving = false;
        }
    }

    private _updateField(field: string, value: any) {
        if (!this.profile) return;
        (this.profile as any)[field] = value;
        this.dirty = true;
        this.requestUpdate();
    }

    private _updateNotification(key: string, value: boolean) {
        if (!this.profile) return;
        (this.profile.notifications as any)[key] = value;
        this.dirty = true;
        this.requestUpdate();
    }

    private _getInitials(name: string): string {
        return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    }

    private _formatDate(date?: string): string {
        if (!date) return 'Never';
        return new Date(date).toLocaleString();
    }

    render() {
        if (this.loading) {
            return html`<div class="loading">Loading profile...</div>`;
        }

        if (!this.profile) {
            return html`<div class="loading">Failed to load profile</div>`;
        }

        return html`
      <div class="profile-page">
        <div class="page-header">
          <h1 class="page-title">Admin Profile</h1>
          <button 
            class="btn-save" 
            ?disabled=${!this.dirty || this.saving}
            @click=${this._saveProfile}
          >
            ${this.saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>

        <!-- Personal Information -->
        <div class="section">
          <div class="section-title">📝 Personal Information</div>
          
          <div class="avatar-section">
            <div class="avatar-preview">
              ${this.profile.avatarUrl
                ? html`<img src="${this.profile.avatarUrl}" alt="${this.profile.displayName}">`
                : this._getInitials(this.profile.displayName || 'SA')
            }
            </div>
            <div class="avatar-actions">
              <button class="btn-secondary">Upload Photo</button>
              <button class="btn-secondary">Remove</button>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Display Name</label>
              <input 
                class="form-input" 
                type="text"
                .value=${this.profile.displayName}
                @input=${(e: Event) => this._updateField('displayName', (e.target as HTMLInputElement).value)}
              >
            </div>
            <div class="form-group">
              <label class="form-label">Email</label>
              <input 
                class="form-input" 
                type="email"
                .value=${this.profile.email}
                disabled
              >
            </div>
          </div>
        </div>

        <!-- Security -->
        <div class="section">
          <div class="section-title">🔒 Security</div>
          
          <div class="security-item">
            <div class="security-info">
              <span class="security-label">Multi-Factor Authentication</span>
              <span class="security-value">${this.profile.mfaEnabled ? 'Enabled ✓' : 'Disabled'}</span>
            </div>
            <button class="btn-secondary">Reconfigure</button>
          </div>

          <div class="security-item">
            <div class="security-info">
              <span class="security-label">Last Login</span>
              <span class="security-value">${this._formatDate(this.profile.lastLogin)}</span>
            </div>
          </div>

          <div class="security-item">
            <div class="security-info">
              <span class="security-label">Session Timeout</span>
              <span class="security-value">${this.profile.sessionTimeout} minutes</span>
            </div>
            <select 
              class="form-input" 
              style="width: 120px;"
              .value=${String(this.profile.sessionTimeout)}
              @change=${(e: Event) => this._updateField('sessionTimeout', parseInt((e.target as HTMLSelectElement).value))}
            >
              <option value="15">15 min</option>
              <option value="30">30 min</option>
              <option value="60">1 hour</option>
              <option value="120">2 hours</option>
            </select>
          </div>

          <div class="security-item">
            <div class="security-info">
              <span class="security-label">Active Sessions</span>
              <span class="security-value">${this.profile.activeSessions} device(s)</span>
            </div>
            <button class="btn-danger">Sign Out All</button>
          </div>

          <div class="action-buttons" style="margin-top: 16px;">
            <button class="btn-secondary">Change Password</button>
          </div>
        </div>

        <!-- Platform Access -->
        <div class="section">
          <div class="section-title">🛡️ Platform Access</div>
          
          <div class="access-grid">
            <div class="access-item">
              <div class="access-label">Role</div>
              <div class="access-value">
                <span class="role-badge">${this.profile.role.toUpperCase()}</span>
              </div>
            </div>
            <div class="access-item">
              <div class="access-label">Permissions</div>
              <div class="access-value">${this.profile.permissions.includes('*') ? '* (Full Access)' : this.profile.permissions.length}</div>
            </div>
            <div class="access-item">
              <div class="access-label">API Keys</div>
              <div class="access-value">${this.profile.apiKeyCount} active</div>
            </div>
          </div>
        </div>

        <!-- Notification Preferences -->
        <div class="section">
          <div class="section-title">🔔 Notification Preferences</div>
          
          <div class="notification-item">
            <span class="notification-label">Critical alerts (downtime, security)</span>
            <saas-toggle
              ?checked=${this.profile.notifications.criticalAlerts}
              @change=${(e: CustomEvent) => this._updateNotification('criticalAlerts', e.detail.checked)}
            ></saas-toggle>
          </div>

          <div class="notification-item">
            <span class="notification-label">Billing events (new subscriptions, failed payments)</span>
            <saas-toggle
              ?checked=${this.profile.notifications.billingEvents}
              @change=${(e: CustomEvent) => this._updateNotification('billingEvents', e.detail.checked)}
            ></saas-toggle>
          </div>

          <div class="notification-item">
            <span class="notification-label">Weekly platform summary</span>
            <saas-toggle
              ?checked=${this.profile.notifications.weeklyDigest}
              @change=${(e: CustomEvent) => this._updateNotification('weeklyDigest', e.detail.checked)}
            ></saas-toggle>
          </div>

          <div class="notification-item">
            <span class="notification-label">Marketing and product updates</span>
            <saas-toggle
              ?checked=${this.profile.notifications.marketing}
              @change=${(e: CustomEvent) => this._updateNotification('marketing', e.detail.checked)}
            ></saas-toggle>
          </div>
        </div>
      </div>
    `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-platform-profile': SaasPlatformProfile;
    }
}
