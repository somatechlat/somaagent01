/**
 * Personal User Profile View — UI-S-34 · CM-11.
 * User's own profile and preferences. Self-service only (CM-11 R-1…R-7).
 *
 * Route: /profile (also /admin/profile, /platform/profile)
 *
 * Tabs: Account (AC-*) · Security (SC-*) · Notifications (NT-*) · Sessions (SS-*)
 * Change-password drawer: UI-M-01 → soma-password-modal (PW-*)
 *
 * VIBE COMPLIANT:
 * - Lit 3.x implementation
 * - Django Ninja API integration
 * - --skin-* tokens only
 * - Real handlers or GATED with a verbatim reason (no dead CTAs)
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import { glassCard } from '../styles/glass.js';
import { moduleBase } from '../styles/module-base.js';

import '../components/soma-toggle.js';
import '../components/soma-password-modal.js';
import '../components/soma-chat-settings.js';

interface UserProfile {
    id: string;
    email: string;
    displayName: string;
    avatarUrl?: string;
    theme: 'light' | 'dark' | 'system';
    language: string;
    timezone: string;
    mfaEnabled: boolean;
    mfaEnrolled: boolean;
    tenantId: string;
    tenantName: string;
    phone: string;
    /** Unbound until ProfileOut exposes last_password_change (CM-11 SC-05). */
    lastPasswordChange?: string | null;
    activeSessions: number;
    notifications: {
        agentReplies: boolean;
        activitySummary: boolean;
        productUpdates: boolean;
    };
}

type ProfileTab = 'account' | 'security' | 'notifications' | 'sessions';

/** Verbatim GATED reasons (CM-11 honesty notes). Never a dead control. */
const GATED_NO_AVATAR = 'Avatar upload has no API on this deployment.';
const GATED_NO_PASSWORD_CHANGE = 'Password change API not mounted';
const GATED_NO_SESSION_LIST =
    'Session list has no self-service API on this deployment.';

@customElement('soma-personal-profile')
export class SomaPersonalProfile extends LitElement {
    static styles = [
        glassCard,
        moduleBase,
        css`
        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: calc(var(--skin-space-md) + var(--skin-space-xs));
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
            min-height: 100vh;
            background: var(--skin-color-bg-void);
            padding: var(--skin-space-xl);
            color: var(--skin-color-text-primary);
            font-family: var(--skin-font-sans);
        }

        .profile-page {
            max-width: calc(var(--skin-space-md) * 43.75);
            margin: 0 auto;
        }

        .page-header {
            margin-bottom: var(--skin-space-lg);
        }

        .page-title {
            font-size: var(--skin-text-2xl);
            font-weight: var(--skin-weight-bold);
            color: var(--skin-color-text-primary);
            margin: 0;
        }

        /* Tabs (CM-11 sections as tab panes) */
        .tabs {
            display: flex;
            border-bottom: var(--skin-border-width) solid var(--skin-color-border);
            margin-bottom: var(--skin-space-lg);
            gap: var(--skin-space-xs);
        }

        .tab {
            padding: var(--skin-space-md) var(--skin-space-lg);
            font-size: var(--skin-text-sm);
            font-weight: var(--skin-weight-medium);
            color: var(--skin-color-text-secondary);
            background: none;
            border: none;
            border-bottom: calc(var(--skin-space-xs) / 2) solid transparent;
            cursor: pointer;
            transition: color var(--skin-motion-fast) var(--skin-motion-ease),
                border-color var(--skin-motion-fast) var(--skin-motion-ease);
        }

        .tab:hover {
            color: var(--skin-color-text-primary);
        }

        .tab:focus-visible {
            outline: var(--skin-focus-ring-width) solid var(--skin-focus-ring);
            outline-offset: var(--skin-focus-ring-offset);
        }

        .tab.active {
            color: var(--skin-color-accent);
            border-bottom-color: var(--skin-color-accent);
        }

        .section {
            background: var(--skin-color-bg-card);
            border: var(--skin-border-width) solid var(--skin-color-border);
            border-radius: var(--skin-radius-lg);
            margin-bottom: var(--skin-space-lg);
        }

        .section-header {
            padding: var(--skin-space-md) var(--skin-space-lg);
            border-bottom: var(--skin-border-width) solid var(--skin-color-border);
            font-size: var(--skin-text-base);
            font-weight: var(--skin-weight-semibold);
            color: var(--skin-color-text-primary);
            display: flex;
            align-items: center;
            gap: var(--skin-space-sm);
        }

        .section-content {
            padding: var(--skin-space-lg);
        }

        /* Avatar Section — AC-01 / AC-02 */
        .avatar-section {
            display: flex;
            align-items: center;
            gap: var(--skin-space-lg);
            margin-bottom: var(--skin-space-lg);
        }

        .avatar {
            width: calc(var(--skin-space-md) * 6);
            height: calc(var(--skin-space-md) * 6);
            border-radius: var(--skin-radius-full);
            background: var(--skin-color-bg-base);
            border: var(--skin-border-width) solid var(--skin-color-border);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: calc(var(--skin-space-xl) + var(--skin-space-sm));
            font-weight: var(--skin-weight-semibold);
            color: var(--skin-color-text-muted);
            overflow: hidden;
            flex-shrink: 0;
        }

        .avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .avatar-actions {
            display: flex;
            flex-direction: column;
            gap: var(--skin-space-sm);
        }

        .muted {
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-muted);
        }

        .gated-note {
            display: inline-flex;
            align-items: center;
            gap: var(--skin-space-xs);
            padding: var(--skin-space-xs) calc(var(--skin-space-sm) + var(--skin-space-xs) / 2);
            border-radius: var(--skin-radius-md);
            border: var(--skin-border-width) solid var(--skin-color-warning);
            background: color-mix(in srgb, var(--skin-color-warning) 12%, transparent);
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-primary);
        }

        /* Form */
        .form-group {
            margin-bottom: var(--skin-space-md);
        }

        .form-label {
            display: block;
            font-size: var(--skin-text-sm);
            font-weight: var(--skin-weight-medium);
            color: var(--skin-color-text-primary);
            margin-bottom: var(--skin-space-xs);
        }

        .form-input {
            width: 100%;
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs) / 2) calc(var(--skin-space-sm) + var(--skin-space-xs));
            background: var(--skin-color-bg-base);
            border: var(--skin-border-width) solid var(--skin-color-border);
            border-radius: var(--skin-radius-md);
            font-size: var(--skin-text-base);
            color: var(--skin-color-text-primary);
            box-sizing: border-box;
        }

        .form-input:focus {
            outline: none;
            border-color: var(--skin-color-accent);
            box-shadow: 0 0 0 var(--skin-focus-ring-width) var(--skin-focus-ring);
        }

        .form-input:disabled {
            opacity: 0.65;
            cursor: not-allowed;
            background: var(--skin-color-bg-hover);
        }

        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: var(--skin-space-md);
        }

        /* Security Row — SC-01…SC-07 */
        .security-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: var(--skin-space-md) 0;
            border-bottom: var(--skin-border-width) solid var(--skin-color-border);
            gap: var(--skin-space-md);
        }

        .security-row:last-child {
            border-bottom: none;
        }

        .security-info {
            display: flex;
            flex-direction: column;
            gap: calc(var(--skin-space-xs) / 2);
        }

        .security-label {
            font-size: var(--skin-text-base);
            color: var(--skin-color-text-primary);
        }

        .security-value {
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-muted);
        }

        /* Toggle Row — NT-01…NT-03 */
        .toggle-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: var(--skin-space-sm) 0;
        }

        .toggle-label {
            font-size: var(--skin-text-base);
            color: var(--skin-color-text-primary);
        }

        /* Sessions — SS-01…SS-07 */
        .stat-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: var(--skin-space-md);
            padding: var(--skin-space-md) 0;
        }

        .stat-value {
            font-size: var(--skin-text-2xl);
            font-weight: var(--skin-weight-bold);
            font-variant-numeric: tabular-nums;
        }

        .empty-state {
            padding: var(--skin-space-lg);
            text-align: center;
            color: var(--skin-color-text-muted);
            font-size: var(--skin-text-sm);
        }

        /* Buttons */
        .btn {
            padding: var(--skin-space-sm) var(--skin-space-md);
            border-radius: var(--skin-radius-md);
            font-size: var(--skin-text-sm);
            font-weight: var(--skin-weight-medium);
            cursor: pointer;
            transition: background var(--skin-motion-fast) var(--skin-motion-ease);
            border: var(--skin-border-width) solid transparent;
            white-space: nowrap;
        }

        .btn:focus-visible {
            outline: var(--skin-focus-ring-width) solid var(--skin-focus-ring);
            outline-offset: var(--skin-focus-ring-offset);
        }

        .btn:disabled {
            opacity: 0.55;
            cursor: not-allowed;
        }

        .btn-primary {
            background: var(--skin-color-accent);
            color: var(--skin-color-accent-text);
            border: none;
        }

        .btn-primary:hover:not(:disabled) {
            background: var(--skin-color-accent-hover);
        }

        .btn-secondary {
            background: var(--skin-color-bg-base);
            color: var(--skin-color-text-primary);
            border: var(--skin-border-width) solid var(--skin-color-border);
        }

        .btn-secondary:hover:not(:disabled) {
            background: var(--skin-color-bg-hover);
        }

        .btn-danger {
            color: var(--skin-color-danger);
            border: var(--skin-border-width) solid var(--skin-color-danger);
            background: transparent;
        }

        .btn-danger:hover:not(:disabled) {
            background: var(--skin-color-danger);
            color: var(--skin-color-danger-text);
        }

        /* Save Bar — PG-03 / PG-04 */
        .save-bar {
            display: flex;
            justify-content: flex-end;
            padding: var(--skin-space-md) 0;
        }

        .error-banner {
            padding: calc(var(--skin-space-sm) + var(--skin-space-xs)) var(--skin-space-md);
            margin-bottom: var(--skin-space-lg);
            background: color-mix(in srgb, var(--skin-color-danger) 12%, transparent);
            color: var(--skin-color-danger);
            border: var(--skin-border-width) solid var(--skin-color-danger);
            border-radius: var(--skin-radius-md);
            font-size: var(--skin-text-sm);
        }

        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: var(--skin-space-2xl);
            color: var(--skin-color-text-muted);
        }
    `,
    ];

    @state() private profile: UserProfile | null = null;
    @state() private loading = true;
    @state() private saving = false;
    @state() private dirty = false;
    @state() private error = '';
    @state() private activeTab: ProfileTab = 'account';
    @state() private passwordModalOpen = false;
    @state() private chatSettingsOpen = false;

    connectedCallback() {
        super.connectedCallback();
        this._loadProfile();
        this.addEventListener('soma-password-changed', this._onPasswordChanged);
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this.removeEventListener('soma-password-changed', this._onPasswordChanged);
    }

    private _onPasswordChanged = () => {
        // CM-11: SC-05 last-changed refreshes after success. The field is still
        // unbound in ProfileOut — reload keeps the honest "unknown" readout.
        void this._loadProfile();
    };

    private async _loadProfile() {
        this.loading = true;
        this.error = '';
        try {
            // Identity from the auth principal; display prefs from
            // UserPreferences; MFA / session counts from the admin profile.
            // Each field is bound to the API that actually owns it.
            const [me, prefs, adminProfile] = await Promise.all([
                apiClient.get<{ id: string; email?: string; name?: string; avatar_url?: string }>(
                    '/auth/me'
                ),
                apiClient.get<{
                    display_name?: string;
                    theme?: string;
                    language?: string;
                    timezone?: string;
                    notifications?: UserProfile['notifications'];
                }>('/platform/admin/preferences'),
                apiClient.get<{
                    mfa_enabled?: boolean;
                    mfa_enrolled?: boolean;
                    tenant_id?: string | null;
                    tenant_name?: string | null;
                    phone?: string;
                    active_sessions?: number;
                    avatar_url?: string | null;
                    last_password_change?: string | null;
                }>('/platform/admin/profile'),
            ]);

            this.profile = {
                id: me.id,
                email: me.email || '',
                displayName: prefs.display_name || me.name || '',
                avatarUrl: adminProfile.avatar_url || me.avatar_url,
                theme: (prefs.theme as UserProfile['theme']) || 'system',
                language: prefs.language || '',
                timezone: prefs.timezone || '',
                mfaEnabled: Boolean(adminProfile.mfa_enabled),
                mfaEnrolled: Boolean(adminProfile.mfa_enrolled),
                tenantId: adminProfile.tenant_id || '',
                tenantName: adminProfile.tenant_name || '',
                phone: adminProfile.phone || '',
                // CM-11 SC-05 / honesty note 2: undefined field is "unknown";
                // only a present-null value may render "never".
                lastPasswordChange: adminProfile.last_password_change,
                activeSessions: adminProfile.active_sessions ?? 0,
                notifications: prefs.notifications ?? {
                    agentReplies: false,
                    activitySummary: false,
                    productUpdates: false,
                },
            };
        } catch (e) {
            this.error = 'Failed to load profile';
            this.profile = null;
        } finally {
            this.loading = false;
        }
    }

    private async _saveProfile() {
        if (!this.profile) return;
        this.saving = true;
        this.error = '';
        try {
            // Appearance and notifications live on UserPreferences. Identity
            // (email) is owned by the IdP and is not written here.
            await apiClient.put('/platform/admin/preferences', {
                display_name: this.profile.displayName,
                theme: this.profile.theme,
                language: this.profile.language,
                timezone: this.profile.timezone,
                notifications: this.profile.notifications,
            });
            await apiClient.put('/platform/admin/profile', {
                display_name: this.profile.displayName,
                phone: this.profile.phone,
            });
            this.dirty = false;
            this.dispatchEvent(new CustomEvent('show-toast', {
                detail: { type: 'success', message: 'Profile saved' },
                bubbles: true,
                composed: true,
            }));
        } catch (e) {
            this.error = 'Failed to save profile';
            this.dispatchEvent(new CustomEvent('show-toast', {
                detail: { type: 'error', message: 'Failed to save profile' },
                bubbles: true,
                composed: true,
            }));
        } finally {
            this.saving = false;
        }
    }

    private _updateField(field: string, value: unknown) {
        if (!this.profile) return;
        this.profile = {
            ...this.profile,
            [field]: value,
        } as UserProfile;
        this.dirty = true;
    }

    private _updateNotification(key: keyof UserProfile['notifications'], value: boolean) {
        if (!this.profile) return;
        this.profile = {
            ...this.profile,
            notifications: {
                ...this.profile.notifications,
                [key]: value,
            },
        };
        this.dirty = true;
    }

    private _getInitials(name: string): string {
        return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    }

    private _setTab(tab: ProfileTab) {
        this.activeTab = tab;
    }

    private _openPasswordModal() {
        this.passwordModalOpen = true;
    }

    /** SC-05 — never invent a timestamp the API did not send. */
    private _renderLastPasswordChange(): string {
        const value = this.profile?.lastPasswordChange;
        if (value === undefined) return 'unknown';
        if (value === null) return 'never';
        return value;
    }

    private _renderAccountTab() {
        const p = this.profile!;
        return html`
            <div class="section" data-control="AC">
                <div class="section-header">
                    <span class="material-symbols-outlined">person</span>
                    Account
                </div>
                <div class="section-content">
                    <div class="avatar-section">
                        <div class="avatar">
                            ${p.avatarUrl
                                ? html`<img src="${p.avatarUrl}" alt="${p.displayName}">`
                                : this._getInitials(p.displayName || 'U')}
                        </div>
                        <div class="avatar-actions">
                            <!-- AC-02 GATED notice (verbatim) -->
                            <span class="gated-note" data-control="AC-02">${GATED_NO_AVATAR}</span>
                        </div>
                    </div>

                    <div class="form-group">
                        <label class="form-label" for="ac-display-name">Display name</label>
                        <input
                            id="ac-display-name"
                            data-control="AC-03"
                            class="form-input"
                            type="text"
                            .value=${p.displayName}
                            @input=${(e: Event) =>
                                this._updateField('displayName', (e.target as HTMLInputElement).value)}
                        />
                    </div>

                    <div class="form-group">
                        <label class="form-label" for="ac-email">Email</label>
                        <input
                            id="ac-email"
                            data-control="AC-04"
                            class="form-input"
                            type="email"
                            .value=${p.email}
                            disabled
                            title="Permanently read-only — email is IdP-owned"
                        />
                    </div>

                    <div class="form-group">
                        <label class="form-label" for="ac-phone">Phone</label>
                        <input
                            id="ac-phone"
                            data-control="AC-05"
                            class="form-input"
                            type="tel"
                            .value=${p.phone}
                            @input=${(e: Event) =>
                                this._updateField('phone', (e.target as HTMLInputElement).value)}
                        />
                    </div>

                    <div class="form-group">
                        <label class="form-label" for="ac-tenant">Tenant</label>
                        <input
                            id="ac-tenant"
                            data-control="AC-06"
                            class="form-input"
                            type="text"
                            .value=${p.tenantName || p.tenantId || '—'}
                            disabled
                            title="Read-only — tenant assignment is platform admin"
                        />
                    </div>

                    <div class="form-group">
                        <label class="form-label" for="ac-tenant-id">Tenant ID</label>
                        <input
                            id="ac-tenant-id"
                            data-control="AC-07"
                            class="form-input"
                            type="text"
                            .value=${p.tenantId || '—'}
                            disabled
                            title="Read-only — identifier, not editable here"
                        />
                    </div>
                </div>
            </div>

            <div class="section" data-control="AC-display-prefs">
                <div class="section-header">
                    <span class="material-symbols-outlined">settings</span>
                    Display preferences
                </div>
                <div class="section-content">
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label" for="ac-theme">Theme</label>
                            <select
                                id="ac-theme"
                                data-control="AC-08"
                                class="form-input"
                                .value=${p.theme}
                                @change=${(e: Event) =>
                                    this._updateField('theme', (e.target as HTMLSelectElement).value)}
                            >
                                <option value="system">System Default</option>
                                <option value="light">Light</option>
                                <option value="dark">Dark</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="ac-language">Language</label>
                            <select
                                id="ac-language"
                                data-control="AC-09"
                                class="form-input"
                                .value=${p.language}
                                @change=${(e: Event) =>
                                    this._updateField('language', (e.target as HTMLSelectElement).value)}
                            >
                                <option value="en">🇺🇸 English</option>
                                <option value="es">🇪🇸 Español</option>
                                <option value="fr">🇫🇷 Français</option>
                                <option value="de">🇩🇪 Deutsch</option>
                            </select>
                        </div>
                    </div>

                    <div class="form-group">
                        <label class="form-label" for="ac-timezone">Timezone</label>
                        <select
                            id="ac-timezone"
                            data-control="AC-10"
                            class="form-input"
                            .value=${p.timezone}
                            @change=${(e: Event) =>
                                this._updateField('timezone', (e.target as HTMLSelectElement).value)}
                        >
                            <option value="America/New_York">America/New_York (EST)</option>
                            <option value="America/Los_Angeles">America/Los_Angeles (PST)</option>
                            <option value="Europe/London">Europe/London (GMT)</option>
                            <option value="Europe/Paris">Europe/Paris (CET)</option>
                            <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
                        </select>
                    </div>
                </div>
            </div>
        `;
    }

    private _renderSecurityTab() {
        const p = this.profile!;
        return html`
            <div class="section" data-control="SC">
                <div class="section-header">
                    <span class="material-symbols-outlined">lock</span>
                    Security
                </div>
                <div class="section-content">
                    <div class="security-row" data-control="SC-01">
                        <div class="security-info">
                            <span class="security-label">Multi-Factor Authentication</span>
                            <span class="security-value" data-control="SC-02">
                                ${p.mfaEnabled
                                    ? html`<span class="material-symbols-outlined">check_circle</span>
                                          Enabled (TOTP)`
                                    : p.mfaEnrolled
                                        ? html`<span class="material-symbols-outlined">check_circle</span>
                                              Enrolled (TOTP not yet active)`
                                        : html`<span class="material-symbols-outlined">cancel</span>
                                              Disabled`}
                            </span>
                        </div>
                        <button
                            class="btn btn-secondary"
                            data-control="SC-03"
                            @click=${() =>
                                window.dispatchEvent(
                                    new CustomEvent('soma-navigate', {
                                        detail: { route: '/mfa/setup' },
                                    })
                                )}
                        >
                            Reconfigure
                        </button>
                    </div>

                    <div class="security-row" data-control="SC-04">
                        <div class="security-info">
                            <span class="security-label">Password</span>
                            <span class="security-value" data-control="SC-05">
                                Last changed ${this._renderLastPasswordChange()}
                            </span>
                        </div>
                        <div class="avatar-actions">
                            <!-- SC-06 GATED notice -->
                            <span class="gated-note" data-control="SC-06"
                                >${GATED_NO_PASSWORD_CHANGE}</span
                            >
                            <button
                                class="btn btn-primary"
                                data-control="SC-07"
                                @click=${this._openPasswordModal}
                                title=${GATED_NO_PASSWORD_CHANGE}
                            >
                                Change password
                            </button>
                        </div>
                    </div>

                    <div class="security-row" data-control="SC-08">
                        <div class="security-info">
                            <span class="security-label">Chat display</span>
                            <span class="security-value">
                                Tools · chain of thought · timestamps · memory chips
                            </span>
                        </div>
                        <div class="avatar-actions">
                            <button
                                class="btn"
                                data-control="SC-08-open"
                                @click=${() => {
                                    this.chatSettingsOpen = true;
                                }}
                                title="Choose which chat data to show"
                            >
                                Chat settings
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    private _renderNotificationsTab() {
        const p = this.profile!;
        return html`
            <div class="section" data-control="NT">
                <div class="section-header">
                    <span class="material-symbols-outlined">notifications</span>
                    Notifications
                </div>
                <div class="section-content">
                    <div class="toggle-row" data-control="NT-01">
                        <span class="toggle-label">Agent replies to my conversations</span>
                        <soma-toggle
                            ?checked=${p.notifications.agentReplies}
                            @soma-change=${(e: CustomEvent<{ checked: boolean }>) =>
                                this._updateNotification('agentReplies', e.detail.checked)}
                        ></soma-toggle>
                    </div>

                    <div class="toggle-row" data-control="NT-02">
                        <span class="toggle-label">Weekly activity summary</span>
                        <soma-toggle
                            ?checked=${p.notifications.activitySummary}
                            @soma-change=${(e: CustomEvent<{ checked: boolean }>) =>
                                this._updateNotification('activitySummary', e.detail.checked)}
                        ></soma-toggle>
                    </div>

                    <div class="toggle-row" data-control="NT-03">
                        <span class="toggle-label">Product updates and tips</span>
                        <soma-toggle
                            ?checked=${p.notifications.productUpdates}
                            @soma-change=${(e: CustomEvent<{ checked: boolean }>) =>
                                this._updateNotification('productUpdates', e.detail.checked)}
                        ></soma-toggle>
                    </div>
                </div>
            </div>
        `;
    }

    private _renderSessionsTab() {
        const p = this.profile!;
        return html`
            <div class="section" data-control="SS">
                <div class="section-header">
                    <span class="material-symbols-outlined">devices</span>
                    Sessions
                </div>
                <div class="section-content">
                    <div class="stat-row" data-control="SS-01">
                        <div class="security-info">
                            <span class="security-label">Active sessions</span>
                            <span class="stat-value">${p.activeSessions}</span>
                        </div>
                        <button
                            class="btn btn-danger"
                            data-control="SS-05"
                            disabled
                            title=${GATED_NO_SESSION_LIST}
                        >
                            Sign out everywhere
                        </button>
                    </div>

                    <!-- SS-02…SS-04 / SS-07: no self session list endpoint.
                         Refuse to invent device/IP rows (CM-11 honesty note 4). -->
                    <div class="empty-state" data-control="SS-02">
                        <span class="gated-note" data-control="SS-07"
                            >${GATED_NO_SESSION_LIST}</span
                        >
                        <p class="muted" style="margin-top: var(--skin-space-sm)">
                            Session rows (device · ip · last seen · current) require
                            GET /api/v2/auth/sessions. Count above is live; rows are not.
                        </p>
                    </div>
                </div>
            </div>
        `;
    }

    render() {
        if (this.loading) {
            return html`<div class="loading" role="status">Loading profile...</div>`;
        }

        if (!this.profile) {
            return html`<div class="loading" role="alert">Failed to load profile</div>`;
        }

        return html`
            <div class="profile-page">
                <div class="page-header">
                    <h1 class="page-title" data-control="PG-01">Personal profile</h1>
                </div>

                ${this.error
                    ? html`<div class="error-banner" role="alert" data-control="PG-02">
                          ${this.error}
                      </div>`
                    : ''}

                <div class="tabs" role="tablist" aria-label="Profile sections">
                    <button
                        class="tab ${this.activeTab === 'account' ? 'active' : ''}"
                        role="tab"
                        aria-selected=${this.activeTab === 'account'}
                        @click=${() => this._setTab('account')}
                    >
                        Account
                    </button>
                    <button
                        class="tab ${this.activeTab === 'security' ? 'active' : ''}"
                        role="tab"
                        aria-selected=${this.activeTab === 'security'}
                        @click=${() => this._setTab('security')}
                    >
                        Security
                    </button>
                    <button
                        class="tab ${this.activeTab === 'notifications' ? 'active' : ''}"
                        role="tab"
                        aria-selected=${this.activeTab === 'notifications'}
                        @click=${() => this._setTab('notifications')}
                    >
                        Notifications
                    </button>
                    <button
                        class="tab ${this.activeTab === 'sessions' ? 'active' : ''}"
                        role="tab"
                        aria-selected=${this.activeTab === 'sessions'}
                        @click=${() => this._setTab('sessions')}
                    >
                        Sessions
                    </button>
                </div>

                <div role="tabpanel">
                    ${this.activeTab === 'account' ? this._renderAccountTab() : nothing}
                    ${this.activeTab === 'security' ? this._renderSecurityTab() : nothing}
                    ${this.activeTab === 'notifications'
                        ? this._renderNotificationsTab()
                        : nothing}
                    ${this.activeTab === 'sessions' ? this._renderSessionsTab() : nothing}
                </div>

                ${this.dirty
                    ? html`
                          <div class="save-bar" data-control="PG-03">
                              <button
                                  class="btn btn-primary"
                                  data-control="PG-04"
                                  ?disabled=${this.saving}
                                  @click=${this._saveProfile}
                              >
                                  ${this.saving ? 'Saving...' : 'Save Changes'}
                              </button>
                          </div>
                      `
                    : ''}
            </div>

            <soma-password-modal
                .open=${this.passwordModalOpen}
                .userEmail=${this.profile.email}
                .userName=${this.profile.displayName}
                @soma-password-modal-close=${() => (this.passwordModalOpen = false)}
            ></soma-password-modal>
            ${this.chatSettingsOpen
                ? html`<soma-chat-settings
                      open
                      @close=${() => (this.chatSettingsOpen = false)}
                      @soma-chat-settings-close=${() => (this.chatSettingsOpen = false)}
                  ></soma-chat-settings>`
                : nothing}
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-personal-profile': SomaPersonalProfile;
    }
}
