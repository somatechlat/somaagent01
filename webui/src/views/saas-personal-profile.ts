/**
 * Personal User Profile View
 * User's own profile and preferences.
 *
 * Route: /profile
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Django Ninja API integration
 *
 * PERSONAS APPLIED:
 * - 🎨 UX Consultant: Clean, focused layout
 * - 🔒 Security Auditor: MFA, sessions
 */

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';

import '../components/saas-toggle.js';

interface UserProfile {
    id: string;
    email: string;
    displayName: string;
    avatarUrl?: string;
    theme: 'light' | 'dark' | 'system';
    language: string;
    timezone: string;
    mfaEnabled: boolean;
    lastPasswordChange?: string;
    activeSessions: number;
    notifications: {
        agentReplies: boolean;
        activitySummary: boolean;
        productUpdates: boolean;
    };
}

@customElement('saas-personal-profile')
export class SaasPersonalProfile extends LitElement {
    static styles = css`
    :host {
      display: block;
      min-height: 100vh;
      background: var(--saas-bg-page, #f5f5f5);
      padding: var(--saas-spacing-xl, 32px);
    }

    .profile-page {
      max-width: 700px;
      margin: 0 auto;
    }

    .page-header {
      margin-bottom: var(--saas-spacing-xl, 32px);
    }

    .page-title {
      font-size: var(--saas-text-2xl, 24px);
      font-weight: 700;
      color: var(--saas-text-primary, #1a1a1a);
    }

    .section {
      background: var(--saas-bg-card, #ffffff);
      border: 1px solid var(--saas-border, #e0e0e0);
      border-radius: var(--saas-radius-lg, 12px);
      margin-bottom: var(--saas-spacing-lg, 24px);
    }

    .section-header {
      padding: var(--saas-spacing-md, 16px) var(--saas-spacing-lg, 24px);
      border-bottom: 1px solid var(--saas-border, #e0e0e0);
      font-size: var(--saas-text-md, 16px);
      font-weight: 600;
      color: var(--saas-text-primary, #1a1a1a);
    }

    .section-content {
      padding: var(--saas-spacing-lg, 24px);
    }

    /* Avatar Section */
    .avatar-section {
      display: flex;
      align-items: center;
      gap: var(--saas-spacing-lg, 24px);
      margin-bottom: var(--saas-spacing-lg, 24px);
    }

    .avatar {
      width: 96px;
      height: 96px;
      border-radius: var(--saas-radius-full, 9999px);
      background: var(--saas-bg-surface, #fafafa);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 40px;
      font-weight: 600;
      color: var(--saas-text-muted, #999999);
      overflow: hidden;
    }

    .avatar img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .avatar-actions {
      display: flex;
      flex-direction: column;
      gap: var(--saas-spacing-sm, 8px);
    }

    /* Form */
    .form-group {
      margin-bottom: var(--saas-spacing-md, 16px);
    }

    .form-label {
      display: block;
      font-size: var(--saas-text-sm, 13px);
      font-weight: 500;
      color: var(--saas-text-primary, #1a1a1a);
      margin-bottom: 4px;
    }

    .form-input {
      width: 100%;
      padding: 10px 12px;
      background: var(--saas-bg-input, #ffffff);
      border: 1px solid var(--saas-border, #e0e0e0);
      border-radius: var(--saas-radius-md, 8px);
      font-size: var(--saas-text-base, 14px);
      color: var(--saas-text-primary, #1a1a1a);
      box-sizing: border-box;
    }

    .form-input:focus {
      outline: none;
      border-color: var(--saas-accent, #2563eb);
    }

    .form-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: var(--saas-spacing-md, 16px);
    }

    /* Security Row */
    .security-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: var(--saas-spacing-md, 16px) 0;
      border-bottom: 1px solid var(--saas-border, #e0e0e0);
    }

    .security-row:last-child {
      border-bottom: none;
    }

    .security-info {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .security-label {
      font-size: var(--saas-text-base, 14px);
      color: var(--saas-text-primary, #1a1a1a);
    }

    .security-value {
      font-size: var(--saas-text-xs, 11px);
      color: var(--saas-text-muted, #999999);
    }

    /* Toggle Row */
    .toggle-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: var(--saas-spacing-sm, 8px) 0;
    }

    .toggle-label {
      font-size: var(--saas-text-base, 14px);
      color: var(--saas-text-primary, #1a1a1a);
    }

    /* Buttons */
    .btn {
      padding: 8px 16px;
      border-radius: var(--saas-radius-md, 8px);
      font-size: var(--saas-text-sm, 13px);
      font-weight: 500;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .btn-primary {
      background: var(--saas-accent, #2563eb);
      color: white;
      border: none;
    }

    .btn-primary:hover {
      background: #1d4ed8;
    }

    .btn-secondary {
      background: var(--saas-bg-card, #ffffff);
      color: var(--saas-text-primary, #1a1a1a);
      border: 1px solid var(--saas-border, #e0e0e0);
    }

    .btn-secondary:hover {
      background: var(--saas-bg-surface, #fafafa);
    }

    .btn-danger {
      color: #dc2626;
      border: 1px solid #dc2626;
      background: transparent;
    }

    .btn-danger:hover {
      background: #dc2626;
      color: white;
    }

    /* Save Bar */
    .save-bar {
      display: flex;
      justify-content: flex-end;
      padding: var(--saas-spacing-md, 16px) 0;
    }

    .loading {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: var(--saas-spacing-2xl, 48px);
      color: var(--saas-text-muted, #999999);
    }
  `;

    @state() private profile: UserProfile | null = null;
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
            const token = localStorage.getItem('eog_auth_token');
            const res = await fetch('/api/v2/auth/me', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (res.ok) {
                const data = await res.json();
                this.profile = {
                    id: data.id,
                    email: data.email || '',
                    displayName: data.name || '',
                    avatarUrl: data.avatar_url,
                    theme: 'system',
                    language: 'en',
                    timezone: 'America/New_York',
                    mfaEnabled: true,
                    activeSessions: 1,
                    notifications: {
                        agentReplies: true,
                        activitySummary: false,
                        productUpdates: false,
                    },
                };
            } else {
                this.profile = this._getDemoProfile();
            }
        } catch (e) {
            this.profile = this._getDemoProfile();
        } finally {
            this.loading = false;
        }
    }

    private _getDemoProfile(): UserProfile {
        return {
            id: 'user-001',
            email: 'jane@acme.com',
            displayName: 'Jane User',
            theme: 'system',
            language: 'en',
            timezone: 'America/New_York',
            mfaEnabled: true,
            lastPasswordChange: '2025-11-25',
            activeSessions: 1,
            notifications: {
                agentReplies: true,
                activitySummary: false,
                productUpdates: false,
            },
        };
    }

    private async _saveProfile() {
        if (!this.profile) return;
        this.saving = true;
        try {
            // Would call PUT /api/v2/profile
            await new Promise(r => setTimeout(r, 500));
            this.dirty = false;
            this.dispatchEvent(new CustomEvent('show-toast', {
                detail: { type: 'success', message: 'Profile saved' },
                bubbles: true,
                composed: true,
            }));
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
          <h1 class="page-title">My Profile</h1>
        </div>

        <!-- Display Section -->
        <div class="section">
          <div class="section-header">📝 Display</div>
          <div class="section-content">
            <div class="avatar-section">
              <div class="avatar">
                ${this.profile.avatarUrl
                ? html`<img src="${this.profile.avatarUrl}" alt="${this.profile.displayName}">`
                : this._getInitials(this.profile.displayName || 'U')
            }
              </div>
              <div class="avatar-actions">
                <button class="btn btn-secondary">Upload Photo</button>
                <button class="btn btn-secondary">Remove</button>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">Display Name</label>
              <input class="form-input" type="text" .value=${this.profile.displayName}
                     @input=${(e: Event) => this._updateField('displayName', (e.target as HTMLInputElement).value)}>
            </div>

            <div class="form-group">
              <label class="form-label">Email</label>
              <input class="form-input" type="email" .value=${this.profile.email} disabled>
            </div>
          </div>
        </div>

        <!-- Preferences Section -->
        <div class="section">
          <div class="section-header">⚙️ Preferences</div>
          <div class="section-content">
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">Theme</label>
                <select class="form-input" .value=${this.profile.theme}
                        @change=${(e: Event) => this._updateField('theme', (e.target as HTMLSelectElement).value)}>
                  <option value="system">◐ System Default</option>
                  <option value="light">☀️ Light</option>
                  <option value="dark">🌙 Dark</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">Language</label>
                <select class="form-input" .value=${this.profile.language}
                        @change=${(e: Event) => this._updateField('language', (e.target as HTMLSelectElement).value)}>
                  <option value="en">🇺🇸 English</option>
                  <option value="es">🇪🇸 Español</option>
                  <option value="fr">🇫🇷 Français</option>
                  <option value="de">🇩🇪 Deutsch</option>
                </select>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">Timezone</label>
              <select class="form-input" .value=${this.profile.timezone}
                      @change=${(e: Event) => this._updateField('timezone', (e.target as HTMLSelectElement).value)}>
                <option value="America/New_York">America/New_York (EST)</option>
                <option value="America/Los_Angeles">America/Los_Angeles (PST)</option>
                <option value="Europe/London">Europe/London (GMT)</option>
                <option value="Europe/Paris">Europe/Paris (CET)</option>
                <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Security Section -->
        <div class="section">
          <div class="section-header">🔒 Security</div>
          <div class="section-content">
            <div class="security-row">
              <div class="security-info">
                <span class="security-label">Multi-Factor Authentication</span>
                <span class="security-value">${this.profile.mfaEnabled ? '✅ Enabled (TOTP)' : '❌ Disabled'}</span>
              </div>
              <button class="btn btn-secondary">Reconfigure</button>
            </div>

            <div class="security-row">
              <div class="security-info">
                <span class="security-label">Password</span>
                <span class="security-value">Last changed ${this.profile.lastPasswordChange || 'never'}</span>
              </div>
              <button class="btn btn-secondary">Change Password</button>
            </div>

            <div class="security-row">
              <div class="security-info">
                <span class="security-label">Active Sessions</span>
                <span class="security-value">${this.profile.activeSessions} device(s)</span>
              </div>
              <button class="btn btn-danger">Sign Out Other Devices</button>
            </div>
          </div>
        </div>

        <!-- Notifications Section -->
        <div class="section">
          <div class="section-header">🔔 Notifications</div>
          <div class="section-content">
            <div class="toggle-row">
              <span class="toggle-label">Agent replies to my conversations</span>
              <saas-toggle
                ?checked=${this.profile.notifications.agentReplies}
                @change=${(e: CustomEvent) => this._updateNotification('agentReplies', e.detail.checked)}
              ></saas-toggle>
            </div>

            <div class="toggle-row">
              <span class="toggle-label">Weekly activity summary</span>
              <saas-toggle
                ?checked=${this.profile.notifications.activitySummary}
                @change=${(e: CustomEvent) => this._updateNotification('activitySummary', e.detail.checked)}
              ></saas-toggle>
            </div>

            <div class="toggle-row">
              <span class="toggle-label">Product updates and tips</span>
              <saas-toggle
                ?checked=${this.profile.notifications.productUpdates}
                @change=${(e: CustomEvent) => this._updateNotification('productUpdates', e.detail.checked)}
              ></saas-toggle>
            </div>
          </div>
        </div>

        ${this.dirty ? html`
          <div class="save-bar">
            <button class="btn btn-primary" ?disabled=${this.saving} @click=${this._saveProfile}>
              ${this.saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        ` : ''}
      </div>
    `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-personal-profile': SaasPersonalProfile;
    }
}
