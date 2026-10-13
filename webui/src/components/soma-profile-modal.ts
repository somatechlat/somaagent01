/**
 * soma-profile-modal — FULL-SCREEN Profile workspace.
 * All sections visible at once (no tabs). Modern glass cards.
 * Expert layout: identity · photo · channels · display · security.
 * Soma law · Material Symbols · I18N · no mocks.
 */
import { LitElement, css, html, nothing, TemplateResult } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import { t, onLocaleChange } from '../i18n/index.js';
import { glassCard } from '../styles/glass.js';
import { moduleBase } from '../styles/module-base.js';
import './soma-password-modal.js';
import './soma-chat-settings.js';

interface ChannelRow {
    id: string;
    value: string;
    label: string;
    verified: boolean;
}

@customElement('soma-profile-modal')
export class SomaProfileModal extends LitElement {
    @property({ type: Boolean, reflect: true }) open = false;

    @state() private _name = '';
    @state() private _email = '';
    @state() private _role = '';
    @state() private _initials = '';
    @state() private _avatarUrl = '';
    @state() private _passwordOpen = false;
    @state() private _chatOpen = false;
    @state() private _dirty = false;
    @state() private _saving = false;
    @state() private _statusKey = '';
    @state() private _statusError = false;
    @state() private _emails: ChannelRow[] = [];
    @state() private _phones: ChannelRow[] = [];
    @state() private _newEmail = '';
    @state() private _newPhone = '';

    private _offLocale?: () => void;

    static styles = [
        glassCard,
        moduleBase,
        css`
        :host {
            display: none;
            position: fixed;
            inset: 0;
            z-index: var(--skin-z-modal);
        }
        :host([open]) {
            display: block;
        }

        /* Full-screen workspace — not a small dialog */
        .scrim {
            position: absolute;
            inset: 0;
            background: color-mix(in srgb, var(--skin-color-bg-void) 55%, transparent);
            backdrop-filter: var(--skin-glass-backdrop);
            -webkit-backdrop-filter: var(--skin-glass-backdrop);
        }
        .shell {
            position: absolute;
            inset: var(--skin-space-sm);
            display: flex;
            flex-direction: column;
            background: var(--skin-color-bg-base);
            color: var(--skin-color-text-primary);
            border: var(--skin-border-width) solid var(--skin-color-border);
            border-radius: var(--skin-radius-xl);
            box-shadow: var(--skin-shadow-overlay);
            overflow: hidden;
            font-family: var(--skin-font-sans);
        }

        .top {
            display: flex;
            align-items: center;
            gap: var(--skin-space-lg);
            padding: var(--skin-space-lg) var(--skin-space-xl);
            border-bottom: var(--skin-border-width) solid var(--skin-color-border);
            background: var(--skin-color-bg-card);
        }
        .avatar-wrap {
            position: relative;
            width: var(--skin-space-2xl);
            height: var(--skin-space-2xl);
            flex-shrink: 0;
        }
        .avatar {
            width: var(--skin-space-2xl);
            height: var(--skin-space-2xl);
            border-radius: var(--skin-radius-full);
            background: var(--skin-color-accent);
            color: var(--skin-color-accent-text);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: var(--skin-text-2xl);
            font-weight: var(--skin-weight-semibold);
            overflow: hidden;
        }
        .avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .cam {
            position: absolute;
            right: calc(-1 * var(--skin-space-xs));
            bottom: calc(-1 * var(--skin-space-xs));
            width: var(--skin-space-lg);
            height: var(--skin-space-lg);
            border-radius: var(--skin-radius-full);
            border: calc(var(--skin-border-width) * 2) solid var(--skin-color-bg-card);
            background: var(--skin-color-accent);
            color: var(--skin-color-accent-text);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .cam .material-symbols-outlined {
            font-size: var(--skin-text-xs);
        }
        .who {
            flex: 1;
            min-width: 0;
        }
        .who h1 {
            margin: 0;
            font-size: var(--skin-text-2xl);
            font-weight: var(--skin-weight-semibold);
            letter-spacing: -0.02em;
        }
        .who .sub {
            margin-top: var(--skin-space-xs);
            font-size: var(--skin-text-sm);
            color: var(--skin-color-text-secondary);
            display: flex;
            flex-wrap: wrap;
            gap: var(--skin-space-sm);
            align-items: center;
        }
        .pill {
            display: inline-flex;
            align-items: center;
            gap: var(--skin-space-xs);
            padding: var(--skin-space-xs) var(--skin-space-sm);
            border-radius: var(--skin-radius-full);
            font-size: var(--skin-text-xs);
            background: var(--skin-color-bg-hover);
            color: var(--skin-color-text-secondary);
        }
        .pill .material-symbols-outlined {
            font-size: var(--skin-text-xs);
        }
        .top-actions {
            display: flex;
            gap: var(--skin-space-sm);
            align-items: center;
        }

        .scroll {
            flex: 1;
            overflow: auto;
            padding: var(--skin-space-lg) var(--skin-space-xl) var(--skin-space-2xl);
        }

        /* Expert grid: every section visible — change anything, no tab hops */
        .grid {
            display: grid;
            grid-template-columns: repeat(12, 1fr);
            gap: var(--skin-space-md);
        }
        .card {
            grid-column: span 6;
            background: var(--skin-color-bg-card);
            border: var(--skin-border-width) solid var(--skin-color-border);
            border-radius: var(--skin-radius-lg);
            padding: var(--skin-space-lg) var(--skin-space-lg) var(--skin-space-md);
            box-shadow: var(--skin-shadow-sm);
        }
        .card.wide {
            grid-column: span 12;
        }
        .card.half-left {
            grid-column: span 5;
        }
        .card.half-right {
            grid-column: span 7;
        }
        .card h2 {
            margin: 0 0 var(--skin-space-xs);
            font-size: var(--skin-text-base);
            font-weight: var(--skin-weight-semibold);
            display: flex;
            align-items: center;
            gap: var(--skin-space-sm);
        }
        .card h2 .material-symbols-outlined {
            font-size: var(--skin-text-lg);
            color: var(--skin-color-accent);
        }
        .card .desc {
            margin: 0 0 var(--skin-space-md);
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-secondary);
        }

        .row-card {
            display: flex;
            align-items: center;
            gap: var(--skin-space-sm);
            padding: var(--skin-space-sm) var(--skin-space-md);
            border: var(--skin-border-width) solid var(--skin-color-border);
            border-radius: var(--skin-radius-md);
            margin-top: var(--skin-space-sm);
            background: var(--skin-color-bg-base);
        }
        .row-card .material-symbols-outlined {
            font-size: var(--skin-text-lg);
            color: var(--skin-color-accent);
        }
        .row-card .v {
            flex: 1;
            font-size: var(--skin-text-sm);
            word-break: break-all;
            color: var(--skin-color-text-primary);
        }
        .row-card .t {
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-secondary);
        }

        .chip-add {
            display: flex;
            gap: var(--skin-space-sm);
            margin-top: var(--skin-space-sm);
        }
        .chip-add input {
            flex: 1;
        }

        .close {
            width: var(--skin-space-xl);
            height: var(--skin-space-xl);
            padding: 0;
            border-radius: var(--skin-radius-full);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .panel-action {
            display: flex;
            align-items: center;
            gap: var(--skin-space-md);
            width: 100%;
            padding: var(--skin-space-md);
            border: var(--skin-border-width) solid var(--skin-color-border);
            border-radius: var(--skin-radius-md);
            background: var(--skin-color-bg-base);
            cursor: pointer;
            margin-top: var(--skin-space-sm);
            text-align: left;
            color: inherit;
            font-family: var(--skin-font-sans);
            font-size: var(--skin-text-sm);
        }
        .panel-action:hover {
            background: var(--skin-color-bg-hover);
        }
        .panel-action .material-symbols-outlined {
            font-size: var(--skin-text-xl);
            color: var(--skin-color-accent);
        }
        .panel-action strong {
            display: block;
            font-size: var(--skin-text-sm);
        }
        .panel-action .sub {
            display: block;
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-secondary);
            margin-top: calc(var(--skin-border-width) * 2);
        }

        .footer-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: var(--skin-space-md);
            padding: var(--skin-space-md) var(--skin-space-xl);
            border-top: var(--skin-border-width) solid var(--skin-color-border);
            background: var(--skin-color-bg-card);
        }
        .footer-actions {
            display: flex;
            gap: var(--skin-space-sm);
        }

        .card .mb-status {
            margin-top: var(--skin-space-md);
        }

        @media (max-width: 56em) {
            .card,
            .card.half-left,
            .card.half-right {
                grid-column: span 12;
            }
            .shell {
                inset: 0;
                border-radius: 0;
            }
        }
        `,
    ];

    override connectedCallback(): void {
        super.connectedCallback();
        this._offLocale = onLocaleChange(() => this.requestUpdate());
        if (this.open) void this._load();
    }

    override disconnectedCallback(): void {
        this._offLocale?.();
        super.disconnectedCallback();
    }

    override updated(changed: Map<string, unknown>): void {
        if (changed.has('open') && this.open) {
            void this._load();
        }
    }

    private _setStatus(key: string, error = false): void {
        this._statusKey = key;
        this._statusError = error;
    }

    private async _load(): Promise<void> {
        try {
            const me = await apiClient.get<{
                email?: string;
                name?: string;
                username?: string;
                role?: string;
                roles?: string[];
                avatar_url?: string;
            }>('/auth/me');
            this._email = me.email || '';
            this._name = me.name || me.username || me.email || 'User';
            this._role = me.role || me.roles?.[0] || '';
            this._avatarUrl = me.avatar_url || '';
            const parts = this._name.split(/[\s@.]+/).filter(Boolean);
            this._initials = ((parts[0]?.[0] || '') + (parts[1]?.[0] || '')).toUpperCase() || 'U';
        } catch {
            this._name = this._name || 'User';
            this._initials = 'U';
        }
        try {
            const storedAvatar = localStorage.getItem('soma_profile_avatar');
            if (storedAvatar && !this._avatarUrl) this._avatarUrl = storedAvatar;
            const raw = localStorage.getItem('soma_profile_channels');
            if (raw) {
                const parsed = JSON.parse(raw) as { emails?: ChannelRow[]; phones?: ChannelRow[] };
                this._emails = parsed.emails ?? [];
                this._phones = parsed.phones ?? [];
            }
            if (this._email && !this._emails.some((e) => e.value === this._email)) {
                this._emails = [
                    { id: 'primary', value: this._email, label: 'Primary', verified: true },
                    ...this._emails,
                ];
            }
        } catch {
            /* never invent */
        }
    }

    private _saveAll(): void {
        this._saving = true;
        try {
            localStorage.setItem('soma_profile_identity', JSON.stringify({ name: this._name }));
            localStorage.setItem(
                'soma_profile_channels',
                JSON.stringify({ emails: this._emails, phones: this._phones }),
            );
            if (this._avatarUrl) {
                try {
                    localStorage.setItem('soma_profile_avatar', this._avatarUrl);
                } catch {
                    /* quota */
                }
            }
            this._setStatus('profile.saved');
            this._dirty = false;
        } catch {
            this._setStatus('profile.saveFailed', true);
        } finally {
            this._saving = false;
        }
    }

    private _addEmail(): void {
        const v = this._newEmail.trim();
        if (!v) return;
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) {
            this._setStatus('profile.invalidEmail', true);
            return;
        }
        this._emails = [
            ...this._emails,
            { id: `e-${Date.now()}`, value: v, label: 'Work', verified: false },
        ];
        this._newEmail = '';
        this._dirty = true;
    }

    private _addPhone(): void {
        const v = this._newPhone.trim();
        if (!v) return;
        if (!/^\+?[\d\s()-]{8,}$/.test(v)) {
            this._setStatus('profile.invalidPhone', true);
            return;
        }
        this._phones = [
            ...this._phones,
            { id: `p-${Date.now()}`, value: v, label: 'WhatsApp', verified: false },
        ];
        this._newPhone = '';
        this._dirty = true;
    }

    private _onAvatarPick(e: Event): void {
        const input = e.target as HTMLInputElement;
        const file = input.files?.[0];
        if (!file) return;
        if (!file.type.startsWith('image/')) {
            this._setStatus('profile.invalidImage', true);
            return;
        }
        const reader = new FileReader();
        reader.onload = () => {
            this._avatarUrl = String(reader.result || '');
            this._dirty = true;
            this._setStatus('profile.photoPendingSave');
        };
        reader.readAsDataURL(file);
        input.value = '';
    }

    private _close(): void {
        this.open = false;
        this.dispatchEvent(new CustomEvent('close', { bubbles: true, composed: true }));
    }

    private _logout(): void {
        this.dispatchEvent(new CustomEvent('logout', { bubbles: true, composed: true }));
        this._close();
    }

    private _channelLabel(label: string): string {
        const map: Record<string, string> = {
            Primary: 'profile.chPrimary',
            Work: 'profile.chWork',
            WhatsApp: 'profile.chWhatsapp',
        };
        return map[label] ? t(map[label]) : label;
    }

    override render() {
        if (!this.open) return nothing;
        return html`
            <div class="scrim" @click=${() => this._close()}></div>
            <div class="shell" role="dialog" aria-modal="true" aria-label=${t('profile.title')}>
                <header class="top">
                    <div class="avatar-wrap">
                        <div class="avatar">
                            ${this._avatarUrl
                                ? html`<img src=${this._avatarUrl} alt="" />`
                                : this._initials}
                        </div>
                        <label class="cam" title=${t('profile.uploadPhoto')}>
                            <span class="material-symbols-outlined">photo_camera</span>
                            <input
                                type="file"
                                accept="image/*"
                                hidden
                                @change=${(e: Event) => this._onAvatarPick(e)}
                            />
                        </label>
                    </div>
                    <div class="who">
                        <h1>${this._name}</h1>
                        <div class="sub">
                            <span>${this._email}</span>
                            <span class="pill">
                                <span class="material-symbols-outlined" style="font-size:var(--skin-text-xs)">badge</span>
                                ${this._role || t('profile.role')}
                            </span>
                        </div>
                    </div>
                    <div class="top-actions">
                        <button
                            class="mb-btn primary"
                            ?disabled=${!this._dirty || this._saving}
                            @click=${() => this._saveAll()}
                        >
                            ${this._saving ? t('profile.saving') : t('profile.saveAll')}
                        </button>
                        <button class="mb-btn ghost close" aria-label=${t('common.close')} @click=${() => this._close()}>
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                </header>

                <div class="scroll">
                    <div class="grid">
                        <!-- Identity -->
                        <section class="card half-left">
                            <h2>
                                <span class="material-symbols-outlined">person</span>
                                ${t('profile.account')}
                            </h2>
                            <p class="desc">${t('profile.accountDesc')}</p>
                            <label class="mb-label" for="pf-name">${t('profile.displayName')}</label>
                            <input
                                class="mb-input"
                                id="pf-name"
                                .value=${this._name}
                                @input=${(e: Event) => {
                                    this._name = (e.target as HTMLInputElement).value;
                                    this._dirty = true;
                                }}
                            />
                            <label class="mb-label" for="pf-email">${t('profile.primaryEmail')}</label>
                            <input class="mb-input" id="pf-email" .value=${this._email} readonly />
                            <div class="mb-hint">${t('profile.emailLockedHint')}</div>
                            <label class="mb-label" for="pf-role">${t('profile.role')}</label>
                            <input class="mb-input" id="pf-role" .value=${this._role} readonly />
                        </section>

                        <!-- Channels -->
                        <section class="card half-right">
                            <h2>
                                <span class="material-symbols-outlined">alternate_email</span>
                                ${t('profile.channels')}
                            </h2>
                            <p class="desc">${t('profile.channelsHint')}</p>
                            <label class="mb-label">${t('profile.emailAccounts')}</label>
                            ${this._emails.map(
                                (r) => html`
                                    <div class="row-card">
                                        <span class="material-symbols-outlined">mail</span>
                                        <div>
                                            <div class="v">${r.value}</div>
                                            <div class="t">
                                                ${this._channelLabel(r.label)}${r.verified
                                                    ? ` · ${t('profile.verified')}`
                                                    : ''}
                                            </div>
                                        </div>
                                        <button
                                            class="mb-btn ghost"
                                            aria-label=${t('profile.removeChannel', { value: r.value })}
                                            @click=${() => {
                                                this._emails = this._emails.filter((x) => x.id !== r.id);
                                                this._dirty = true;
                                            }}
                                        >
                                            <span class="material-symbols-outlined">close</span>
                                        </button>
                                    </div>
                                `,
                            )}
                            <div class="chip-add">
                                <input
                                    class="mb-input"
                                    placeholder="name@company.com"
                                    .value=${this._newEmail}
                                    @input=${(e: Event) => {
                                        this._newEmail = (e.target as HTMLInputElement).value;
                                    }}
                                    @keydown=${(e: KeyboardEvent) => {
                                        if (e.key === 'Enter') this._addEmail();
                                    }}
                                />
                                <button class="mb-btn" @click=${() => this._addEmail()}>${t('profile.addEmail')}</button>
                            </div>

                            <label class="mb-label">${t('profile.whatsapp')}</label>
                            ${this._phones.map(
                                (r) => html`
                                    <div class="row-card">
                                        <span class="material-symbols-outlined">chat</span>
                                        <div>
                                            <div class="v">${r.value}</div>
                                            <div class="t">${this._channelLabel(r.label)}</div>
                                        </div>
                                        <button
                                            class="mb-btn ghost"
                                            aria-label=${t('profile.removeChannel', { value: r.value })}
                                            @click=${() => {
                                                this._phones = this._phones.filter((x) => x.id !== r.id);
                                                this._dirty = true;
                                            }}
                                        >
                                            <span class="material-symbols-outlined">close</span>
                                        </button>
                                    </div>
                                `,
                            )}
                            <div class="chip-add">
                                <input
                                    class="mb-input"
                                    placeholder="+593 99 000 0000"
                                    .value=${this._newPhone}
                                    @input=${(e: Event) => {
                                        this._newPhone = (e.target as HTMLInputElement).value;
                                    }}
                                    @keydown=${(e: KeyboardEvent) => {
                                        if (e.key === 'Enter') this._addPhone();
                                    }}
                                />
                                <button class="mb-btn" @click=${() => this._addPhone()}>${t('profile.addWhatsapp')}</button>
                            </div>
                        </section>

                        <!-- Display -->
                        <section class="card">
                            <h2>
                                <span class="material-symbols-outlined">tune</span>
                                ${t('profile.display')}
                            </h2>
                            <p class="desc">${t('profile.displayDesc')}</p>
                            <button class="panel-action" data-testid="profile-chat-settings"
                                @click=${() => (this._chatOpen = true)}>
                                <span class="material-symbols-outlined">tune</span>
                                <span>
                                    <strong>${t('chat.settings')}</strong>
                                    <span class="sub">${t('chat.settingsHint')}</span>
                                </span>
                            </button>
                        </section>

                        <!-- Security -->
                        <section class="card">
                            <h2>
                                <span class="material-symbols-outlined">shield</span>
                                ${t('profile.security')}
                            </h2>
                            <p class="desc">${t('profile.securityDesc')}</p>
                            <button class="panel-action" @click=${() => (this._passwordOpen = true)}>
                                <span class="material-symbols-outlined">lock</span>
                                <span>
                                    <strong>${t('profile.changePassword')}</strong>
                                    <span class="sub">${t('profile.passwordHint')}</span>
                                </span>
                            </button>
                            <button class="panel-action" @click=${() => this._logout()}>
                                <span class="material-symbols-outlined">logout</span>
                                <span>
                                    <strong>${t('profile.signOut')}</strong>
                                    <span class="sub">${t('profile.signOutHint')}</span>
                                </span>
                            </button>
                        </section>

                        ${this._statusKey
                            ? html`<div class="card wide">
                                  <div class="mb-status ${this._statusError ? 'error' : ''}" role="status">
                                      ${t(this._statusKey)}
                                  </div>
                              </div>`
                            : nothing}
                    </div>
                </div>

                <footer class="footer-bar">
                    <button class="mb-btn danger" @click=${() => this._logout()}>${t('profile.signOut')}</button>
                    <div class="footer-actions">
                        <button class="mb-btn" @click=${() => this._close()}>${t('common.close')}</button>
                        <button
                            class="mb-btn primary"
                            ?disabled=${!this._dirty || this._saving}
                            @click=${() => this._saveAll()}
                        >
                            ${this._saving ? t('profile.saving') : t('profile.saveAll')}
                        </button>
                    </div>
                </footer>
            </div>

            ${this._passwordOpen
                ? html`<soma-password-modal
                      open
                      .userEmail=${this._email}
                      .userName=${this._name}
                      @soma-password-modal-close=${() => (this._passwordOpen = false)}
                      @close=${() => (this._passwordOpen = false)}
                  ></soma-password-modal>`
                : nothing}
            ${this._chatOpen
                ? html`<soma-chat-settings open @close=${() => (this._chatOpen = false)}></soma-chat-settings>`
                : nothing}
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-profile-modal': SomaProfileModal;
    }
}
