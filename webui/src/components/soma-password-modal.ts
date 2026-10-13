/**
 * SOMA Change-password modal (UI-M-01 · CM-11 §9).
 *
 * Write-only fields. Local policy gate is the privileged floor (min 14) per
 * CM-11 §10; the server remains the authority via check_password_policy.
 *
 * Target route: POST /api/v2/auth/change-password
 *   body { current_password, new_password } · bearer of the caller.
 * When that route is absent (admin/auth/api.py mounts no change-password),
 * this modal stays honest: GATED banner, submit disabled with the same reason.
 * No fake success, no invented handler.
 *
 * VIBE COMPLIANT: Lit 3.x · --skin-* tokens only · no product name "Capsule".
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { apiClient, ApiError } from '../services/api-client.js';

/** CM-11 §10 — privileged floor shown in the UI. Server re-checks policy. */
const MIN_PASSWORD_LENGTH = 14;
const MAX_PASSWORD_LENGTH = 128;

/** Verbatim GATED reason (honest absence, not a dead CTA). */
const GATED_REASON = 'Password change API not mounted';

const POLICY_READOUT =
    'Minimum 14 characters · max 128 · not your username or email · not whitespace-only · not a single repeated character. Length is the only composition rule.';

type StrengthScore = 0 | 1 | 2 | 3 | 4;

interface StrengthResult {
    score: StrengthScore;
    label: string;
}

/**
 * Length is the control (password.py). Variety only ranks among
 * already-acceptable candidates — it never loosens or tightens the gate.
 */
function scorePassword(pw: string): StrengthResult {
    if (!pw) return { score: 0, label: '—' };
    if (pw.length < MIN_PASSWORD_LENGTH) return { score: 1, label: 'Below minimum' };
    if (pw.length > MAX_PASSWORD_LENGTH) return { score: 1, label: 'Too long' };

    let variety = 0;
    if (/[a-z]/.test(pw)) variety += 1;
    if (/[A-Z]/.test(pw)) variety += 1;
    if (/[0-9]/.test(pw)) variety += 1;
    if (/[^a-zA-Z0-9]/.test(pw)) variety += 1;

    if (pw.length >= 28) {
        return { score: 4, label: 'Excellent' };
    }
    if (pw.length >= 20) {
        return variety >= 3
            ? { score: 4, label: 'Excellent' }
            : { score: 3, label: 'Strong' };
    }
    return variety >= 3
        ? { score: 3, label: 'Strong' }
        : { score: 2, label: 'Fair' };
}

@customElement('soma-password-modal')
export class SomaPasswordModal extends LitElement {
    static styles = css`
        :host {
            display: contents;
        }

        .backdrop {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.45);
            z-index: 300;
            opacity: 0;
            visibility: hidden;
            transition: opacity var(--skin-motion-normal, 200ms) var(--skin-motion-ease, ease),
                visibility var(--skin-motion-normal, 200ms) var(--skin-motion-ease, ease);
        }

        .backdrop.open {
            opacity: 1;
            visibility: visible;
        }

        .drawer {
            position: fixed;
            top: 0;
            right: 0;
            bottom: 0;
            width: 420px;
            max-width: 100vw;
            background: var(--skin-color-bg-card, #ffffff);
            color: var(--skin-color-text-primary, #1a1a1a);
            border-left: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.08));
            box-shadow: var(--skin-shadow-overlay, 0 24px 64px rgba(0, 0, 0, 0.35));
            display: flex;
            flex-direction: column;
            transform: translateX(100%);
            transition: transform var(--skin-motion-normal, 200ms) var(--skin-motion-ease, ease);
            z-index: 301;
        }

        .drawer.open {
            transform: translateX(0);
        }

        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: var(--skin-space-md, 16px) var(--skin-space-lg, 24px);
            border-bottom: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.08));
            flex-shrink: 0;
        }

        .title {
            margin: 0;
            font-size: var(--skin-text-lg, 16px);
            font-weight: var(--skin-weight-semibold, 600);
            color: var(--skin-color-text-primary, #1a1a1a);
        }

        .close-btn {
            width: 36px;
            height: 36px;
            border-radius: var(--skin-radius-md, 8px);
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.08));
            background: var(--skin-color-bg-base, #ffffff);
            color: var(--skin-color-text-secondary, #666666);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
        }

        .close-btn:hover {
            background: var(--skin-color-bg-hover, #fafafa);
            color: var(--skin-color-text-primary, #1a1a1a);
        }

        .close-btn:focus-visible {
            outline: var(--skin-focus-ring-width, 2px) solid var(--skin-focus-ring, #1a1a1a);
            outline-offset: var(--skin-focus-ring-offset, 2px);
        }

        .body {
            flex: 1;
            overflow-y: auto;
            padding: var(--skin-space-lg, 24px);
        }

        .field {
            margin-bottom: var(--skin-space-md, 16px);
        }

        .label {
            display: block;
            font-size: var(--skin-text-sm, 13px);
            font-weight: var(--skin-weight-medium, 500);
            color: var(--skin-color-text-primary, #1a1a1a);
            margin-bottom: var(--skin-space-xs, 4px);
        }

        .password-row {
            display: flex;
            gap: var(--skin-space-sm, 8px);
            align-items: stretch;
        }

        .password-input {
            flex: 1;
            min-width: 0;
            padding: 10px 12px;
            background: var(--skin-color-bg-base, #ffffff);
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.08));
            border-radius: var(--skin-radius-md, 8px);
            font-size: var(--skin-text-base, 14px);
            color: var(--skin-color-text-primary, #1a1a1a);
            box-sizing: border-box;
        }

        .password-input:focus {
            outline: none;
            border-color: var(--skin-color-accent, #1a1a1a);
            box-shadow: 0 0 0 var(--skin-focus-ring-width, 2px) var(--skin-focus-ring, #1a1a1a);
        }

        .password-input:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .reveal-btn {
            width: 42px;
            flex-shrink: 0;
            border: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.08));
            border-radius: var(--skin-radius-md, 8px);
            background: var(--skin-color-bg-base, #ffffff);
            color: var(--skin-color-text-secondary, #666666);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .reveal-btn:hover {
            background: var(--skin-color-bg-hover, #fafafa);
            color: var(--skin-color-text-primary, #1a1a1a);
        }

        .reveal-btn:focus-visible {
            outline: var(--skin-focus-ring-width, 2px) solid var(--skin-focus-ring, #1a1a1a);
            outline-offset: var(--skin-focus-ring-offset, 2px);
        }

        .strength {
            margin-top: var(--skin-space-sm, 8px);
        }

        .strength-track {
            height: 6px;
            border-radius: var(--skin-radius-full, 9999px);
            background: var(--skin-color-border-subtle, rgba(0, 0, 0, 0.05));
            overflow: hidden;
        }

        .strength-fill {
            height: 100%;
            border-radius: var(--skin-radius-full, 9999px);
            transition: width var(--skin-motion-fast, 120ms) var(--skin-motion-ease, ease),
                background var(--skin-motion-fast, 120ms) var(--skin-motion-ease, ease);
        }

        .strength-fill.score-0,
        .strength-fill.score-1 {
            width: 20%;
            background: var(--skin-color-danger, #ef4444);
        }

        .strength-fill.score-2 {
            width: 50%;
            background: var(--skin-color-warning, #eab308);
        }

        .strength-fill.score-3 {
            width: 75%;
            background: var(--skin-color-info, #3b82f6);
        }

        .strength-fill.score-4 {
            width: 100%;
            background: var(--skin-color-success, #22c55e);
        }

        .strength-meta {
            display: flex;
            justify-content: space-between;
            margin-top: var(--skin-space-xs, 4px);
            font-size: var(--skin-text-xs, 11px);
            color: var(--skin-color-text-muted, #666666);
        }

        .policy {
            margin: var(--skin-space-md, 16px) 0;
            padding: var(--skin-space-sm, 8px) var(--skin-space-md, 16px);
            border-radius: var(--skin-radius-md, 8px);
            background: var(--skin-color-bg-hover, #fafafa);
            border: 1px solid var(--skin-color-border-subtle, rgba(0, 0, 0, 0.05));
            font-size: var(--skin-text-xs, 11px);
            line-height: 1.5;
            color: var(--skin-color-text-secondary, #666666);
        }

        .counter {
            display: inline-block;
            margin-top: var(--skin-space-xs, 4px);
            font-variant-numeric: tabular-nums;
            color: var(--skin-color-text-muted, #666666);
        }

        .counter.met {
            color: var(--skin-color-success, #22c55e);
        }

        .banner {
            padding: var(--skin-space-sm, 8px) var(--skin-space-md, 16px);
            margin-bottom: var(--skin-space-md, 16px);
            border-radius: var(--skin-radius-md, 8px);
            font-size: var(--skin-text-sm, 13px);
            border: 1px solid transparent;
        }

        .banner.error {
            background: color-mix(in srgb, var(--skin-color-danger, #ef4444) 12%, transparent);
            color: var(--skin-color-danger, #ef4444);
            border-color: var(--skin-color-danger, #ef4444);
        }

        .banner.gated {
            background: color-mix(in srgb, var(--skin-color-warning, #eab308) 14%, transparent);
            color: var(--skin-color-text-primary, #1a1a1a);
            border-color: var(--skin-color-warning, #eab308);
        }

        .banner.success {
            background: color-mix(in srgb, var(--skin-color-success, #22c55e) 12%, transparent);
            color: var(--skin-color-success, #22c55e);
            border-color: var(--skin-color-success, #22c55e);
        }

        .footer {
            display: flex;
            justify-content: flex-end;
            gap: var(--skin-space-sm, 8px);
            padding: var(--skin-space-md, 16px) var(--skin-space-lg, 24px);
            border-top: 1px solid var(--skin-color-border, rgba(0, 0, 0, 0.08));
            flex-shrink: 0;
        }

        .btn {
            padding: 8px 16px;
            border-radius: var(--skin-radius-md, 8px);
            font-size: var(--skin-text-sm, 13px);
            font-weight: var(--skin-weight-medium, 500);
            cursor: pointer;
            border: 1px solid transparent;
        }

        .btn:focus-visible {
            outline: var(--skin-focus-ring-width, 2px) solid var(--skin-focus-ring, #1a1a1a);
            outline-offset: var(--skin-focus-ring-offset, 2px);
        }

        .btn:disabled {
            opacity: 0.55;
            cursor: not-allowed;
        }

        .btn-secondary {
            background: var(--skin-color-bg-base, #ffffff);
            color: var(--skin-color-text-primary, #1a1a1a);
            border-color: var(--skin-color-border, rgba(0, 0, 0, 0.08));
        }

        .btn-primary {
            background: var(--skin-color-accent, #1a1a1a);
            color: var(--skin-color-accent-text, #ffffff);
        }

        .btn-primary:hover:not(:disabled) {
            background: var(--skin-color-accent-hover, #333333);
        }

        .hint {
            margin-top: var(--skin-space-xs, 4px);
            font-size: var(--skin-text-xs, 11px);
            color: var(--skin-color-text-muted, #666666);
        }

        .hint.error {
            color: var(--skin-color-danger, #ef4444);
        }
    `;

    @property({ type: Boolean, reflect: true }) open = false;

    /** Email of the signed-in user — policy parity check only, never sent. */
    @property({ type: String, attribute: 'user-email' }) userEmail = '';

    /** Username/name of the signed-in user — policy parity check only. */
    @property({ type: String, attribute: 'user-name' }) userName = '';

    @state() private currentPassword = '';
    @state() private newPassword = '';
    @state() private confirmPassword = '';

    @state() private showCurrent = false;
    @state() private showNew = false;
    @state() private showConfirm = false;

    @state() private submitting = false;
    @state() private error = '';
    @state() private success = false;

    /**
     * Mount state of POST /api/v2/auth/change-password.
     * null = not yet probed. Probed with a real request on open (no mocks).
     */
    @state() private apiMounted: boolean | null = null;

    private _handleKeydown = (e: KeyboardEvent) => {
        if (!this.open) return;
        if (e.key === 'Escape') {
            e.preventDefault();
            this._close();
        }
    };

    connectedCallback() {
        super.connectedCallback();
        document.addEventListener('keydown', this._handleKeydown);
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        document.removeEventListener('keydown', this._handleKeydown);
    }

    updated(changed: Map<string, unknown>) {
        if (changed.has('open') && this.open) {
            document.body.style.overflow = 'hidden';
            void this._probeMount();
            this.updateComplete.then(() => {
                const first = this.renderRoot.querySelector<HTMLInputElement>(
                    'input[data-field="current"]'
                );
                first?.focus();
            });
        } else if (changed.has('open') && !this.open) {
            document.body.style.overflow = '';
        }
    }

    /**
     * Real mount probe: GET on a POST-only route.
     * 404 → route absent (GATED). 405/200/204/401/403 → route exists.
     * Network failure is treated as not mounted — never claim a live handler
     * we could not reach.
     */
    private async _probeMount(): Promise<void> {
        try {
            const res = await fetch('/api/v2/auth/change-password', {
                method: 'GET',
                credentials: 'include',
                headers: { Accept: 'application/json' },
            });
            this.apiMounted = res.status !== 404;
        } catch {
            this.apiMounted = false;
        }
    }

    private get _gated(): boolean {
        return this.apiMounted === false;
    }

    private get _newTooShort(): boolean {
        return this.newPassword.length > 0 && this.newPassword.length < MIN_PASSWORD_LENGTH;
    }

    private get _newTooLong(): boolean {
        return this.newPassword.length > MAX_PASSWORD_LENGTH;
    }

    private get _mismatch(): boolean {
        return (
            this.confirmPassword.length > 0 &&
            this.newPassword !== this.confirmPassword
        );
    }

    private get _sameAsCurrent(): boolean {
        return (
            this.currentPassword.length > 0 &&
            this.newPassword.length > 0 &&
            this.newPassword === this.currentPassword
        );
    }

    /** Client-side parity with check_password_policy (server is authority). */
    private get _policyError(): string {
        const pw = this.newPassword;
        if (!pw) return '';
        if (pw.length < MIN_PASSWORD_LENGTH) {
            return `Password must be at least ${MIN_PASSWORD_LENGTH} characters`;
        }
        if (pw.length > MAX_PASSWORD_LENGTH) {
            return `Password must be at most ${MAX_PASSWORD_LENGTH} characters`;
        }
        const stripped = pw.trim();
        if (!stripped) return 'Password must not be only whitespace';
        if (new Set(stripped).size === 1) {
            return 'Password must not be a single repeated character';
        }
        const lowered = stripped.toLowerCase();
        for (const [label, value] of [
            ['username', this.userName],
            ['email', this.userEmail],
        ] as const) {
            if (!value) continue;
            const candidate = value.trim().toLowerCase();
            if (!candidate) continue;
            if (
                lowered === candidate ||
                lowered === candidate.split('@', 1)[0]
            ) {
                return `Password must not be the ${label}`;
            }
        }
        return '';
    }

    private get _canSubmit(): boolean {
        return (
            this.apiMounted === true &&
            !this.submitting &&
            !this.success &&
            this.currentPassword.length > 0 &&
            this.newPassword.length >= MIN_PASSWORD_LENGTH &&
            this.newPassword.length <= MAX_PASSWORD_LENGTH &&
            this.confirmPassword === this.newPassword &&
            this.newPassword !== this.currentPassword &&
            this._policyError === ''
        );
    }

    private get _strength(): StrengthResult {
        return scorePassword(this.newPassword);
    }

    private _update(field: 'currentPassword' | 'newPassword' | 'confirmPassword', value: string) {
        this[field] = value;
        if (this.error) this.error = '';
    }

    private _close() {
        if (this.submitting) return;
        this.open = false;
        this.error = '';
        this.success = false;
        this.currentPassword = '';
        this.newPassword = '';
        this.confirmPassword = '';
        this.showCurrent = false;
        this.showNew = false;
        this.showConfirm = false;
        this.dispatchEvent(
            new CustomEvent('soma-password-modal-close', { bubbles: true, composed: true })
        );
    }

    private async _submit(e: Event) {
        e.preventDefault();
        if (!this._canSubmit) return;

        this.submitting = true;
        this.error = '';
        try {
            // Real handler. Body keys match CM-11 §9. No password is echoed.
            await apiClient.post('/auth/change-password', {
                current_password: this.currentPassword,
                new_password: this.newPassword,
            });
            this.success = true;
            this.currentPassword = '';
            this.newPassword = '';
            this.confirmPassword = '';
            this.dispatchEvent(
                new CustomEvent('show-toast', {
                    detail: { type: 'success', message: 'Password changed.' },
                    bubbles: true,
                    composed: true,
                })
            );
            this.dispatchEvent(
                new CustomEvent('soma-password-changed', { bubbles: true, composed: true })
            );
            window.setTimeout(() => this._close(), 600);
        } catch (err) {
            if (err instanceof ApiError && err.status === 404) {
                // Route vanished or never mounted — flip to honest GATED.
                this.apiMounted = false;
                this.error = GATED_REASON;
            } else if (err instanceof ApiError) {
                // Server-derived copy only. Uniform body for wrong-current vs
                // unknown account is the server's job (CM-07); we surface what
                // it sent without inventing account existence.
                this.error = err.message || 'Password change failed';
            } else {
                this.error = 'Password change failed';
            }
        } finally {
            this.submitting = false;
        }
    }

    private _renderReveal(
        show: boolean,
        onToggle: () => void,
        label: string
    ) {
        return html`
            <button
                type="button"
                class="reveal-btn"
                tabindex="-1"
                aria-label=${show ? `Hide ${label}` : `Show ${label}`}
                @click=${onToggle}
            >
                ${show ? 'Hide' : 'Show'}
            </button>
        `;
    }

    render() {
        const strength = this._strength;
        const counterMet = this.newPassword.length >= MIN_PASSWORD_LENGTH;

        return html`
            <div
                class="backdrop ${this.open ? 'open' : ''}"
                @click=${() => this._close()}
                aria-hidden=${!this.open}
            ></div>
            <aside
                class="drawer ${this.open ? 'open' : ''}"
                role="dialog"
                aria-modal="true"
                aria-labelledby="soma-password-modal-title"
                aria-hidden=${!this.open}
            >
                <header class="header">
                    <h2 class="title" id="soma-password-modal-title">Change password</h2>
                    <button
                        type="button"
                        class="close-btn"
                        aria-label="Close"
                        @click=${() => this._close()}
                    >
                        ×
                    </button>
                </header>

                <form class="body" @submit=${this._submit}>
                    ${this._gated
                        ? html`
                              <div class="banner gated" role="status" data-testid="pw-gated">
                                  ${GATED_REASON}
                              </div>
                          `
                        : nothing}
                    ${!this._gated && this.apiMounted === null
                        ? html`
                              <div class="banner" role="status">Checking password change API…</div>
                          `
                        : nothing}
                    ${this.error
                        ? html`<div class="banner error" role="alert" data-testid="pw-error">
                              ${this.error}
                          </div>`
                        : nothing}
                    ${this.success
                        ? html`<div class="banner success" role="status">Password changed.</div>`
                        : nothing}

                    <div class="field">
                        <label class="label" for="pw-current">Current password</label>
                        <div class="password-row">
                            <input
                                id="pw-current"
                                data-field="current"
                                class="password-input"
                                type=${this.showCurrent ? 'text' : 'password'}
                                autocomplete="current-password"
                                .value=${this.currentPassword}
                                ?disabled=${this._gated || this.submitting || this.success}
                                @input=${(e: Event) =>
                                    this._update(
                                        'currentPassword',
                                        (e.target as HTMLInputElement).value
                                    )}
                            />
                            ${this._renderReveal(
                                this.showCurrent,
                                () => (this.showCurrent = !this.showCurrent),
                                'current password'
                            )}
                        </div>
                    </div>

                    <div class="field">
                        <label class="label" for="pw-new">New password</label>
                        <div class="password-row">
                            <input
                                id="pw-new"
                                data-field="new"
                                class="password-input"
                                type=${this.showNew ? 'text' : 'password'}
                                autocomplete="new-password"
                                .value=${this.newPassword}
                                ?disabled=${this._gated || this.submitting || this.success}
                                @input=${(e: Event) =>
                                    this._update(
                                        'newPassword',
                                        (e.target as HTMLInputElement).value
                                    )}
                            />
                            ${this._renderReveal(
                                this.showNew,
                                () => (this.showNew = !this.showNew),
                                'new password'
                            )}
                        </div>
                        <div class="strength" aria-live="polite">
                            <div class="strength-track">
                                <div class="strength-fill score-${strength.score}"></div>
                            </div>
                            <div class="strength-meta">
                                <span>Strength: ${strength.label}</span>
                                <span
                                    class="counter ${counterMet ? 'met' : ''}"
                                    data-testid="pw-counter"
                                    >${this.newPassword.length}/${MIN_PASSWORD_LENGTH}</span
                                >
                            </div>
                        </div>
                        ${this._newTooShort
                            ? html`<div class="hint error">
                                  Minimum ${MIN_PASSWORD_LENGTH} characters
                              </div>`
                            : nothing}
                        ${this._newTooLong
                            ? html`<div class="hint error">
                                  Maximum ${MAX_PASSWORD_LENGTH} characters
                              </div>`
                            : nothing}
                        ${this._sameAsCurrent
                            ? html`<div class="hint error">
                                  New password must differ from current password
                              </div>`
                            : nothing}
                        ${this._policyError &&
                        !this._newTooShort &&
                        !this._newTooLong &&
                        !this._sameAsCurrent
                            ? html`<div class="hint error">${this._policyError}</div>`
                            : nothing}
                    </div>

                    <div class="field">
                        <label class="label" for="pw-confirm">Confirm new password</label>
                        <div class="password-row">
                            <input
                                id="pw-confirm"
                                data-field="confirm"
                                class="password-input"
                                type=${this.showConfirm ? 'text' : 'password'}
                                autocomplete="new-password"
                                .value=${this.confirmPassword}
                                ?disabled=${this._gated || this.submitting || this.success}
                                @input=${(e: Event) =>
                                    this._update(
                                        'confirmPassword',
                                        (e.target as HTMLInputElement).value
                                    )}
                            />
                            ${this._renderReveal(
                                this.showConfirm,
                                () => (this.showConfirm = !this.showConfirm),
                                'confirm password'
                            )}
                        </div>
                        ${this._mismatch
                            ? html`<div class="hint error">Passwords do not match</div>`
                            : nothing}
                    </div>

                    <div class="policy" data-testid="pw-policy">
                        ${POLICY_READOUT}
                    </div>
                </form>

                <footer class="footer">
                    <button
                        type="button"
                        class="btn btn-secondary"
                        @click=${() => this._close()}
                        ?disabled=${this.submitting}
                    >
                        Cancel
                    </button>
                    <button
                        type="button"
                        class="btn btn-primary"
                        data-testid="pw-submit"
                        @click=${this._submit}
                        ?disabled=${!this._canSubmit}
                        title=${this._gated ? GATED_REASON : ''}
                        aria-describedby=${this._gated ? 'pw-gated' : ''}
                    >
                        ${this.submitting ? 'Changing…' : 'Change password'}
                    </button>
                </footer>
            </aside>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-password-modal': SomaPasswordModal;
    }
}
