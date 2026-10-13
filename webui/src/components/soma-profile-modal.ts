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
        css`
        :host {
            display: none;
            position: fixed;
            inset: 0;
            z-index: 320;
        }
        :host([open]) {
            display: block;
        }

        /* Full-screen workspace — not a small dialog */
        .scrim {
            position: absolute;
            inset: 0;
            background: color-mix(in srgb, var(--skin-color-bg-void, #0f1115) 55%, transparent);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
        }
        .shell {
            position: absolute;
            inset: 12px;
            display: flex;
            flex-direction: column;
            background: var(--skin-color-bg-base, var(--platform-bg-base, #ffffff));
            color: var(--skin-color-text-primary, var(--platform-text-main, #1a1a1a));
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.12));
            border-radius: var(--skin-radius-xl, 16px);
            box-shadow: var(--skin-shadow-overlay, 0 16px 48px rgba(0, 0, 0, 0.28));
            overflow: hidden;
            font-family: var(--skin-font-sans, system-ui, sans-serif);
        }

        .top {
            display: flex;
            align-items: center;
            gap: 18px;
            padding: 22px 28px;
            border-bottom: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.08));
            background: var(--skin-color-bg-card, var(--platform-bg-card, #fff));
        }
        .avatar-wrap {
            position: relative;
            width: 72px;
            height: 72px;
            flex-shrink: 0;
        }
        .avatar {
            width: 72px;
            height: 72px;
            border-radius: 50%;
            background: var(--skin-color-accent, #FF4D00);
            color: var(--skin-color-accent-text, #fff);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 26px;
            font-weight: 600;
            overflow: hidden;
        }
        .avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .cam {
            position: absolute;
            right: -4px;
            bottom: -4px;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            border: 2px solid var(--skin-color-bg-card, #fff);
            background: var(--skin-color-accent, #FF4D00);
            color: var(--skin-color-accent-text, #fff);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .cam .material-symbols-outlined {
            font-size: 15px;
        }
        .who {
            flex: 1;
            min-width: 0;
        }
        .who h1 {
            margin: 0;
            font-size: 22px;
            font-weight: 650;
            letter-spacing: -0.02em;
        }
        .who .sub {
            margin-top: 4px;
            font-size: 13px;
            color: var(--skin-color-text-secondary, #5b6470);
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: center;
        }
        .pill {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 11px;
            background: var(--skin-color-bg-hover, #f0f2f5);
            color: var(--skin-color-text-secondary, #5b6470);
        }
        .top-actions {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        .scroll {
            flex: 1;
            overflow: auto;
            padding: 22px 28px 32px;
        }

        /* Expert grid: every section visible — change anything, no tab hops */
        .grid {
            display: grid;
            grid-template-columns: repeat(12, 1fr);
            gap: 16px;
        }
        .card {
            grid-column: span 6;
            background: var(--skin-color-bg-card, var(--platform-bg-card, #fff));
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.1));
            border-radius: var(--skin-radius-lg, 12px);
            padding: 18px 18px 16px;
            box-shadow: var(--skin-shadow-sm, 0 1px 2px rgba(0, 0, 0, 0.04));
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
            margin: 0 0 4px;
            font-size: 14px;
            font-weight: 650;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .card h2 .material-symbols-outlined {
            font-size: 18px;
            color: var(--skin-color-accent, #FF4D00);
        }
        .card .desc {
            margin: 0 0 14px;
            font-size: 12px;
            color: var(--skin-color-text-secondary, #5b6470);
        }

        label {
            display: block;
            font-size: 11px;
            font-weight: 500;
            color: var(--skin-color-text-secondary, #5b6470);
            margin: 12px 0 5px;
        }
        input {
            width: 100%;
            box-sizing: border-box;
            padding: 11px 12px;
            border-radius: var(--skin-radius-md, 8px);
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.14));
            background: var(--skin-color-bg-base, #fff);
            color: inherit;
            font-size: 13px;
        }
        input:focus-visible {
            outline: 2px solid var(--skin-focus-ring, var(--skin-color-accent, #FF4D00));
            outline-offset: 1px;
        }
        input[readonly] {
            background: var(--skin-color-bg-hover, #f4f6f8);
            color: var(--skin-color-text-secondary, #5b6470);
        }

        .hint {
            font-size: 11px;
            color: var(--skin-color-text-muted, #6b7280);
            margin-top: 5px;
        }

        .row-card {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.08));
            border-radius: var(--skin-radius-md, 8px);
            margin-top: 8px;
            background: var(--skin-color-bg-base, #fff);
        }
        .row-card .material-symbols-outlined {
            font-size: 18px;
            color: var(--skin-color-accent, #FF4D00);
        }
        .row-card .v {
            flex: 1;
            font-size: 13px;
            word-break: break-all;
            color: var(--skin-color-text-primary, #1a1a1a);
        }
        .row-card .t {
            font-size: 10px;
            color: var(--skin-color-text-secondary, #5b6470);
        }

        .chip-add {
            display: flex;
            gap: 8px;
            margin-top: 10px;
        }
        .chip-add input {
            flex: 1;
        }

        button {
            border-radius: var(--skin-radius-md, 8px);
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.14));
            background: var(--skin-color-bg-base, #fff);
            color: inherit;
            padding: 9px 14px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
        }
        button:hover:not(:disabled) {
            background: var(--skin-color-bg-hover, #f3f5f7);
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        button.primary {
            background: var(--skin-color-accent, #FF4D00);
            border-color: transparent;
            color: var(--skin-color-accent-text, #fff);
        }
        button.danger {
            color: var(--skin-color-danger, #b91c1c);
            border-color: color-mix(in srgb, var(--skin-color-danger, #b91c1c) 40%, transparent);
        }
        button.ghost {
            border-color: transparent;
            background: transparent;
        }
        .close {
            width: 36px;
            height: 36px;
            padding: 0;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .panel-action {
            display: flex;
            align-items: center;
            gap: 12px;
            width: 100%;
            padding: 13px 14px;
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.1));
            border-radius: var(--skin-radius-md, 8px);
            background: var(--skin-color-bg-base, #fff);
            cursor: pointer;
            margin-top: 8px;
            text-align: left;
        }
        .panel-action:hover {
            background: var(--skin-color-bg-hover, #f5f7fa);
        }
        .panel-action .material-symbols-outlined {
            font-size: 20px;
            color: var(--skin-color-accent, #FF4D00);
        }
        .panel-action strong {
            display: block;
            font-size: 13px;
        }
        .panel-action .sub {
            display: block;
            font-size: 11px;
            color: var(--skin-color-text-secondary, #5b6470);
            margin-top: 2px;
        }

        .status {
            margin-top: 12px;
            font-size: 12px;
            padding: 8px 10px;
            border-radius: var(--skin-radius-md, 8px);
            background: var(--skin-color-bg-hover, #f3f5f7);
            color: var(--skin-color-text-secondary, #5b6470);
        }
        .status.error {
            background: color-mix(in srgb, var(--skin-color-danger, #ef4444) 12%, transparent);
            color: var(--skin-color-danger, #b91c1c);
        }

        .footer-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            padding: 14px 28px;
            border-top: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.08));
            background: var(--skin-color-bg-card, var(--platform-bg-card, #fff));
        }

        @media (max-width: 900px) {
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
                                <span class="material-symbols-outlined" style="font-size:12px">badge</span>
                                ${this._role || t('profile.role')}
                            </span>
                        </div>
                    </div>
                    <div class="top-actions">
                        <button
                            class="primary"
                            ?disabled=${!this._dirty || this._saving}
                            @click=${() => this._saveAll()}
                        >
                            ${this._saving ? t('profile.saving') : t('profile.saveAll')}
                        </button>
                        <button class="close ghost" aria-label=${t('common.close')} @click=${() => this._close()}>
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
                            <label for="pf-name">${t('profile.displayName')}</label>
                            <input
                                id="pf-name"
                                .value=${this._name}
                                @input=${(e: Event) => {
                                    this._name = (e.target as HTMLInputElement).value;
                                    this._dirty = true;
                                }}
                            />
                            <label for="pf-email">${t('profile.primaryEmail')}</label>
                            <input id="pf-email" .value=${this._email} readonly />
                            <div class="hint">${t('profile.emailLockedHint')}</div>
                            <label for="pf-role">${t('profile.role')}</label>
                            <input id="pf-role" .value=${this._role} readonly />
                        </section>

                        <!-- Channels -->
                        <section class="card half-right">
                            <h2>
                                <span class="material-symbols-outlined">alternate_email</span>
                                ${t('profile.channels')}
                            </h2>
                            <p class="desc">${t('profile.channelsHint')}</p>
                            <label>${t('profile.emailAccounts')}</label>
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
                                            class="ghost"
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
                                    placeholder="name@company.com"
                                    .value=${this._newEmail}
                                    @input=${(e: Event) => {
                                        this._newEmail = (e.target as HTMLInputElement).value;
                                    }}
                                    @keydown=${(e: KeyboardEvent) => {
                                        if (e.key === 'Enter') this._addEmail();
                                    }}
                                />
                                <button @click=${() => this._addEmail()}>${t('profile.addEmail')}</button>
                            </div>

                            <label>${t('profile.whatsapp')}</label>
                            ${this._phones.map(
                                (r) => html`
                                    <div class="row-card">
                                        <span class="material-symbols-outlined">chat</span>
                                        <div>
                                            <div class="v">${r.value}</div>
                                            <div class="t">${this._channelLabel(r.label)}</div>
                                        </div>
                                        <button
                                            class="ghost"
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
                                    placeholder="+593 99 000 0000"
                                    .value=${this._newPhone}
                                    @input=${(e: Event) => {
                                        this._newPhone = (e.target as HTMLInputElement).value;
                                    }}
                                    @keydown=${(e: KeyboardEvent) => {
                                        if (e.key === 'Enter') this._addPhone();
                                    }}
                                />
                                <button @click=${() => this._addPhone()}>${t('profile.addWhatsapp')}</button>
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
                                  <div class="status ${this._statusError ? 'error' : ''}" role="status">
                                      ${t(this._statusKey)}
                                  </div>
                              </div>`
                            : nothing}
                    </div>
                </div>

                <footer class="footer-bar">
                    <button class="danger" @click=${() => this._logout()}>${t('profile.signOut')}</button>
                    <div style="display:flex;gap:8px">
                        <button @click=${() => this._close()}>${t('common.close')}</button>
                        <button
                            class="primary"
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
