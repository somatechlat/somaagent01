/**
 * soma-profile-modal — full user Profile window (glass, one-click Chat settings).
 * Identity · photo · email accounts · WhatsApp numbers · password · sign out.
 * Product names only. Material Symbols. No emojis. No mocks.
 */
import { LitElement, css, html, nothing, TemplateResult } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { apiClient } from '../services/api-client.js';
import './soma-password-modal.js';
import './soma-chat-settings.js';

type ProfileTab = 'account' | 'channels' | 'display' | 'security';

interface ChannelRow {
    id: string;
    value: string;
    label: string;
    verified: boolean;
}

@customElement('soma-profile-modal')
export class SomaProfileModal extends LitElement {
    @property({ type: Boolean, reflect: true }) open = false;
    /** Open straight on Chat settings (Display) — one click from topbar. */
    @property({ type: String }) initialTab: ProfileTab = 'account';

    @state() private _tab: ProfileTab = 'account';
    @state() private _name = '';
    @state() private _email = '';
    @state() private _role = '';
    @state() private _initials = '';
    @state() private _avatarUrl = '';
    @state() private _passwordOpen = false;
    @state() private _chatOpen = false;
    @state() private _dirty = false;
    @state() private _saving = false;
    @state() private _status = '';
    @state() private _emails: ChannelRow[] = [];
    @state() private _phones: ChannelRow[] = [];
    @state() private _newEmail = '';
    @state() private _newPhone = '';

    static styles = css`
        :host {
            display: none;
            position: fixed;
            inset: 0;
            z-index: 300;
        }
        :host([open]) {
            display: block;
        }
        .scrim {
            position: absolute;
            inset: 0;
            background: color-mix(in srgb, var(--skin-color-bg-void, #000) 42%, transparent);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }
        .dialog {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: min(560px, 94vw);
            max-height: min(720px, 92vh);
            display: flex;
            flex-direction: column;
            background: color-mix(in srgb, var(--skin-color-bg-card, #fff) 90%, transparent);
            backdrop-filter: blur(24px) saturate(140%);
            -webkit-backdrop-filter: blur(24px) saturate(140%);
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.1));
            border-radius: var(--skin-radius-xl, 16px);
            box-shadow: var(--skin-shadow-overlay, 0 16px 48px rgba(0, 0, 0, 0.25));
            overflow: hidden;
            font-family: var(--skin-font-sans, system-ui, sans-serif);
            color: var(--skin-color-text-primary, #1a1a1a);
        }
        .head {
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 20px 20px 12px;
        }
        .avatar-wrap {
            position: relative;
            width: 64px;
            height: 64px;
            flex-shrink: 0;
        }
        .avatar {
            width: 64px;
            height: 64px;
            border-radius: 50%;
            background: var(--skin-color-accent, #FF4D00);
            color: var(--skin-color-accent-text, #fff);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
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
            right: -2px;
            bottom: -2px;
            width: 26px;
            height: 26px;
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
            font-size: 14px;
        }
        .head-meta {
            flex: 1;
            min-width: 0;
        }
        .head-meta h2 {
            margin: 0;
            font-size: 17px;
            font-weight: 600;
        }
        .head-meta .email {
            font-size: 12px;
            color: var(--skin-color-text-secondary, #666);
            margin-top: 2px;
        }
        .head-meta .role {
            display: inline-block;
            margin-top: 6px;
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 999px;
            background: var(--skin-color-bg-hover, #f0f0f0);
            color: var(--skin-color-text-secondary, #666);
        }
        .close {
            align-self: flex-start;
            width: 32px;
            height: 32px;
            border: none;
            border-radius: 50%;
            background: transparent;
            cursor: pointer;
            color: var(--skin-color-text-secondary, #666);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .close:hover {
            background: var(--skin-color-bg-hover, #f0f0f0);
        }
        .tabs {
            display: flex;
            gap: 4px;
            padding: 0 16px;
            border-bottom: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.08));
        }
        .tab {
            border: none;
            background: transparent;
            padding: 10px 14px;
            font-size: 12px;
            font-weight: 500;
            color: var(--skin-color-text-secondary, #666);
            cursor: pointer;
            border-bottom: 2px solid transparent;
        }
        .tab.active {
            color: var(--skin-color-accent, #FF4D00);
            border-bottom-color: var(--skin-color-accent, #FF4D00);
        }
        .body {
            padding: 16px 20px 20px;
            overflow: auto;
            flex: 1;
        }
        label {
            display: block;
            font-size: 11px;
            color: var(--skin-color-text-secondary, #666);
            margin: 12px 0 4px;
        }
        input {
            width: 100%;
            box-sizing: border-box;
            padding: 10px 12px;
            border-radius: var(--skin-radius-md, 8px);
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.12));
            background: var(--skin-color-bg-base, #fff);
            color: inherit;
            font-size: 13px;
        }
        input:focus-visible {
            outline: 2px solid var(--skin-focus-ring, var(--skin-color-accent, #FF4D00));
            outline-offset: 1px;
        }
        .hint {
            font-size: 11px;
            color: var(--skin-color-text-muted, #999);
            margin-top: 4px;
        }
        .row-card {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.08));
            border-radius: var(--skin-radius-md, 8px);
            margin-top: 8px;
            background: color-mix(in srgb, var(--skin-color-bg-base, #fff) 75%, transparent);
        }
        .row-card .material-symbols-outlined {
            font-size: 18px;
            color: var(--skin-color-accent, #FF4D00);
        }
        .row-card .v {
            flex: 1;
            font-size: 13px;
            word-break: break-all;
        }
        .row-card .t {
            font-size: 10px;
            color: var(--skin-color-text-muted, #999);
        }
        .chip-add {
            display: flex;
            gap: 8px;
            margin-top: 10px;
        }
        .chip-add input {
            flex: 1;
        }
        button.btn {
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.12));
            background: var(--skin-color-bg-base, #fff);
            color: inherit;
            border-radius: var(--skin-radius-md, 8px);
            padding: 9px 14px;
            font-size: 12px;
            cursor: pointer;
        }
        button.btn:hover:not(:disabled) {
            background: var(--skin-color-bg-hover, #f5f5f5);
        }
        button.btn.primary {
            background: var(--skin-color-accent, #FF4D00);
            border-color: transparent;
            color: var(--skin-color-accent-text, #fff);
        }
        button.btn.danger {
            color: var(--skin-color-danger, #b91c1c);
            border-color: var(--skin-color-danger, #b91c1c);
        }
        button.btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .foot {
            display: flex;
            justify-content: space-between;
            gap: 8px;
            padding: 12px 20px 18px;
            border-top: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.08));
        }
        .foot-right {
            display: flex;
            gap: 8px;
        }
        .panel-action {
            display: flex;
            align-items: center;
            gap: 12px;
            width: 100%;
            padding: 14px;
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.08));
            border-radius: var(--skin-radius-lg, 12px);
            background: color-mix(in srgb, var(--skin-color-bg-base, #fff) 70%, transparent);
            cursor: pointer;
            font: inherit;
            text-align: left;
            margin-top: 10px;
        }
        .panel-action:hover {
            background: var(--skin-color-bg-hover, #f5f5f5);
        }
        .panel-action .material-symbols-outlined {
            font-size: 22px;
            color: var(--skin-color-accent, #FF4D00);
        }
        .panel-action .sub {
            display: block;
            font-size: 11px;
            color: var(--skin-color-text-secondary, #666);
            margin-top: 2px;
        }
        .status {
            font-size: 12px;
            margin-top: 10px;
            color: var(--skin-color-text-secondary, #666);
        }
        .status.error {
            color: var(--skin-color-danger, #b91c1c);
        }
    `;

    override connectedCallback(): void {
        super.connectedCallback();
        if (this.open) void this._load();
    }

    override updated(changed: Map<string, unknown>): void {
        if (changed.has('open') && this.open) {
            this._tab = this.initialTab || 'account';
            void this._load();
        }
        if (changed.has('initialTab') && this.open) {
            this._tab = this.initialTab || this._tab;
        }
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
        // Channels: local profile store until a server contact API is mounted.
        try {
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
            /* keep empty — never invent channels */
        }
    }

    private _saveChannels(): void {
        localStorage.setItem(
            'soma_profile_channels',
            JSON.stringify({ emails: this._emails, phones: this._phones }),
        );
        this._status = 'Channels saved on this device.';
        this._dirty = false;
    }

    private _addEmail(): void {
        const v = this._newEmail.trim();
        if (!v) return;
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) {
            this._status = 'Enter a valid email address.';
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
            this._status = 'Enter a valid phone number.';
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
            this._status = 'Choose an image file.';
            return;
        }
        const reader = new FileReader();
        reader.onload = () => {
            this._avatarUrl = String(reader.result || '');
            try {
                localStorage.setItem('soma_profile_avatar', this._avatarUrl);
            } catch {
                /* quota — avatar stays session-only */
            }
            this._dirty = true;
            this._status = 'Photo updated on this device (server upload when profile API mounts).';
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

    private _tabBtn(id: ProfileTab, label: string): TemplateResult {
        return html`
            <button
                class="tab ${this._tab === id ? 'active' : ''}"
                @click=${() => (this._tab = id)}
                aria-selected=${this._tab === id}
            >
                ${label}
            </button>
        `;
    }

    private _renderAccount(): TemplateResult {
        return html`
            <label for="pf-name">Display name</label>
            <input
                id="pf-name"
                .value=${this._name}
                @input=${(e: Event) => {
                    this._name = (e.target as HTMLInputElement).value;
                    this._dirty = true;
                }}
            />
            <label for="pf-email">Primary email</label>
            <input id="pf-email" .value=${this._email} readonly />
            <div class="hint">Sign-in email is locked. Extra emails live under Channels.</div>
            <label for="pf-role">Role</label>
            <input id="pf-role" .value=${this._role} readonly />
            <button
                class="btn primary"
                style="margin-top:16px"
                ?disabled=${!this._dirty || this._saving}
                @click=${() => {
                    this._saving = true;
                    try {
                        localStorage.setItem(
                            'soma_profile_identity',
                            JSON.stringify({ name: this._name }),
                        );
                        this._status = 'Profile saved.';
                        this._dirty = false;
                    } catch {
                        this._status = 'Could not save profile.';
                    } finally {
                        this._saving = false;
                    }
                }}
            >
                ${this._saving ? 'Saving…' : 'Save profile'}
            </button>
        `;
    }

    private _renderChannels(): TemplateResult {
        return html`
            <div class="hint">Email and WhatsApp for later module wiring (mail, chat bridges).</div>
            <label>Email accounts</label>
            ${this._emails.map(
                (r) => html`
                    <div class="row-card">
                        <span class="material-symbols-outlined">mail</span>
                        <div>
                            <div class="v">${r.value}</div>
                            <div class="t">${r.label}${r.verified ? ' · verified' : ''}</div>
                        </div>
                        <button
                            class="btn"
                            aria-label=${`Remove ${r.value}`}
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
                <button class="btn" @click=${() => this._addEmail()}>Add email</button>
            </div>

            <label>WhatsApp / phone</label>
            ${this._phones.map(
                (r) => html`
                    <div class="row-card">
                        <span class="material-symbols-outlined">chat</span>
                        <div>
                            <div class="v">${r.value}</div>
                            <div class="t">${r.label}</div>
                        </div>
                        <button
                            class="btn"
                            aria-label=${`Remove ${r.value}`}
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
                <button class="btn" @click=${() => this._addPhone()}>Add WhatsApp</button>
            </div>
            <button
                class="btn primary"
                style="margin-top:16px"
                ?disabled=${!this._dirty}
                @click=${() => this._saveChannels()}
            >
                Save channels
            </button>
        `;
    }

    private _renderDisplay(): TemplateResult {
        return html`
            <button
                class="panel-action"
                data-testid="profile-chat-settings"
                @click=${() => (this._chatOpen = true)}
            >
                <span class="material-symbols-outlined">tune</span>
                <span>
                    <strong>Chat settings</strong>
                    <span class="sub">Tools · chain of thought · timestamps · memory chips</span>
                </span>
            </button>
            <button
                class="panel-action"
                @click=${() => {
                    this.dispatchEvent(
                        new CustomEvent('open-full-profile', { bubbles: true, composed: true }),
                    );
                    this._close();
                }}
            >
                <span class="material-symbols-outlined">open_in_new</span>
                <span>
                    <strong>Open full profile page</strong>
                    <span class="sub">Advanced account settings</span>
                </span>
            </button>
        `;
    }

    private _renderSecurity(): TemplateResult {
        return html`
            <button class="panel-action" @click=${() => (this._passwordOpen = true)}>
                <span class="material-symbols-outlined">lock</span>
                <span>
                    <strong>Change password</strong>
                    <span class="sub">Minimum 14 characters</span>
                </span>
            </button>
            <button class="panel-action" style="margin-top:10px" @click=${() => this._logout()}>
                <span class="material-symbols-outlined">logout</span>
                <span>
                    <strong>Sign out</strong>
                    <span class="sub">End this session</span>
                </span>
            </button>
        `;
    }

    override render() {
        if (!this.open) return nothing;
        return html`
            <div class="scrim" @click=${() => this._close()}></div>
            <div class="dialog" role="dialog" aria-modal="true" aria-label="Profile">
                <div class="head">
                    <div class="avatar-wrap">
                        <div class="avatar">
                            ${this._avatarUrl
                                ? html`<img src=${this._avatarUrl} alt="" />`
                                : this._initials}
                        </div>
                        <label class="cam" title="Upload photo">
                            <span class="material-symbols-outlined">photo_camera</span>
                            <input
                                type="file"
                                accept="image/*"
                                hidden
                                @change=${(e: Event) => this._onAvatarPick(e)}
                            />
                        </label>
                    </div>
                    <div class="head-meta">
                        <h2>${this._name}</h2>
                        <div class="email">${this._email}</div>
                        <span class="role">${this._role}</span>
                    </div>
                    <button class="close" aria-label="Close" @click=${() => this._close()}>
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
                <div class="tabs" role="tablist">
                    ${this._tabBtn('account', 'Account')}
                    ${this._tabBtn('channels', 'Channels')}
                    ${this._tabBtn('display', 'Display')}
                    ${this._tabBtn('security', 'Security')}
                </div>
                <div class="body">
                    ${this._tab === 'account'
                        ? this._renderAccount()
                        : this._tab === 'channels'
                          ? this._renderChannels()
                          : this._tab === 'display'
                            ? this._renderDisplay()
                            : this._renderSecurity()}
                    ${this._status
                        ? html`<div
                              class="status ${this._status.includes('Could') || this._status.includes('valid') ? 'error' : ''}"
                              role="status"
                          >
                              ${this._status}
                          </div>`
                        : nothing}
                </div>
                <div class="foot">
                    <button class="btn danger" @click=${() => this._logout()}>Sign out</button>
                    <div class="foot-right">
                        <button class="btn" @click=${() => this._close()}>Close</button>
                    </div>
                </div>
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
                ? html`<soma-chat-settings
                      open
                      @close=${() => (this._chatOpen = false)}
                  ></soma-chat-settings>`
                : nothing}
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-profile-modal': SomaProfileModal;
    }
}
