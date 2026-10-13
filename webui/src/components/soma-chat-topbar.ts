/**
 * SomaAgent01 — Chat topbar (CH-04 / C4).
 *
 * Title + model label + connection status chip (only when degraded)
 * + pause / stop / reset controls with Material Symbols icons.
 * Buttons dispatch `soma-chat-control` CustomEvents; the host view wires
 * them to the real transport (WS / REST).
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { glassCard } from '../styles/glass.js';
import { moduleBase } from '../styles/module-base.js';

export type ChatControlAction = 'pause' | 'resume' | 'nudge' | 'stop' | 'reset' | 'chat-settings';
export type ConnectionStatus = 'ok' | 'reconnecting' | 'degraded';

@customElement('soma-chat-topbar')
export class SomaChatTopbar extends LitElement {
    @property({ type: String }) title = '';
    @property({ type: String }) modelLabel = '';
    @property({ type: Boolean }) busy = false;
    @property({ type: Boolean }) paused = false;
    @property({ type: Boolean }) canNudge = false;
    /**
     * Connection health. The status chip renders ONLY when not 'ok', so a
     * healthy chat stays visually quiet (no permanent green/red pill).
     */
    @property({ type: String, attribute: 'connection-status' }) connectionStatus: ConnectionStatus = 'ok';
    /**
     * Nudge IS wired: the topbar dispatches `soma-chat-control` with
     * `action: 'nudge'`, and the chat view forwards it as a `chat.nudge` WS
     * frame which the gateway handles (`services/gateway/consumers/chat.py`
     * `MSG_CHAT_NUDGE` → `chat.nudged`). This title must describe that
     * behaviour, not claim the gateway lacks it.
     */
    @property({ type: String }) nudgeTitle = 'Nudge — ask the agent to continue the current turn';

    static styles = [
        glassCard,
        moduleBase,
        css`
        :host {
            display: flex;
            align-items: center;
            gap: var(--skin-space-md);
            width: 100%;
            min-width: 0;
        }

        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: var(--skin-text-lg);
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

        .title-block {
            display: flex;
            flex-direction: column;
            gap: var(--skin-space-xs);
            min-width: 0;
            flex: 1;
        }

        .title {
            font-size: var(--skin-text-lg);
            font-weight: var(--skin-weight-semibold);
            color: var(--skin-color-text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .meta {
            display: flex;
            align-items: center;
            gap: var(--skin-space-sm);
            min-height: var(--skin-space-lg);
        }

        .model-label {
            display: inline-flex;
            align-items: center;
            gap: var(--skin-space-xs);
            font-family: var(--skin-font-mono);
            font-size: var(--skin-text-xs);
            color: var(--skin-color-text-secondary);
            padding: 2px var(--skin-space-sm);
            border-radius: var(--skin-radius-full);
            background: var(--skin-color-bg-void);
            border: var(--skin-border-width) solid var(--skin-color-border-subtle);
            max-width: 14rem;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .model-label .material-symbols-outlined {
            font-size: var(--skin-text-xs);
            opacity: 0.7;
        }

        /* Status pills — running/paused are turn state; connection is health */
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: var(--skin-space-xs);
            font-size: var(--skin-text-xs);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 2px var(--skin-space-sm);
            border-radius: var(--skin-radius-full);
        }

        .status-pill.running {
            color: var(--skin-color-success);
            background: color-mix(in srgb, var(--skin-color-success) 12%, transparent);
        }

        .status-pill.paused {
            color: var(--skin-color-warning);
            background: color-mix(in srgb, var(--skin-color-warning) 12%, transparent);
        }

        .conn-chip {
            display: inline-flex;
            align-items: center;
            gap: var(--skin-space-xs);
            font-size: var(--skin-text-xs);
            padding: var(--skin-space-xs) var(--skin-space-sm);
            border-radius: var(--skin-radius-full);
            border: var(--skin-border-width) solid transparent;
            animation: chipIn var(--skin-motion-fast) var(--skin-motion-ease);
        }

        @keyframes chipIn {
            from { opacity: 0; transform: translateY(-2px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .conn-chip.reconnecting {
            color: var(--skin-color-warning);
            background: color-mix(in srgb, var(--skin-color-warning) 12%, transparent);
            border-color: color-mix(in srgb, var(--skin-color-warning) 28%, transparent);
        }

        .conn-chip.degraded {
            color: var(--skin-color-danger);
            background: color-mix(in srgb, var(--skin-color-danger) 12%, transparent);
            border-color: color-mix(in srgb, var(--skin-color-danger) 28%, transparent);
        }

        .conn-chip .dot {
            width: var(--skin-space-xs);
            height: var(--skin-space-xs);
            border-radius: var(--skin-radius-full);
            background: currentColor;
        }

        .conn-chip.reconnecting .dot {
            animation: pulse 1.1s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.35; }
        }

        .controls {
            display: flex;
            align-items: center;
            gap: var(--skin-space-xs);
            flex-shrink: 0;
        }

        .ctl-btn {
            display: inline-flex;
            align-items: center;
            gap: var(--skin-space-xs);
            padding: var(--skin-space-xs) var(--skin-space-md);
            border-radius: var(--skin-radius-md);
            border: var(--skin-border-width) solid var(--skin-color-border);
            background: var(--skin-glass-bg);
            color: var(--skin-color-text-primary);
            font-size: var(--skin-text-sm);
            font-weight: var(--skin-weight-medium);
            cursor: pointer;
            transition: all var(--skin-motion-fast) var(--skin-motion-ease);
            white-space: nowrap;
        }

        .ctl-btn:hover:not(:disabled) {
            background: var(--skin-color-bg-hover);
            border-color: var(--skin-color-border-strong);
        }

        .ctl-btn:focus-visible {
            outline: var(--skin-focus-ring-width) solid var(--skin-focus-ring);
            outline-offset: var(--skin-focus-ring-offset);
        }

        .ctl-btn:disabled {
            opacity: 0.4;
            cursor: not-allowed;
        }

        .ctl-btn.stop {
            color: var(--skin-color-danger);
            border-color: color-mix(in srgb, var(--skin-color-danger) 35%, transparent);
        }

        .ctl-btn.stop:hover:not(:disabled) {
            background: color-mix(in srgb, var(--skin-color-danger) 12%, transparent);
        }

        .ctl-btn.reset {
            color: var(--skin-color-text-muted);
        }

        .ctl-btn .material-symbols-outlined {
            font-size: var(--skin-text-base);
        }

        @media (max-width: 45rem) {
            .ctl-btn .label {
                display: none;
            }
            .ctl-btn {
                padding: var(--skin-space-xs) var(--skin-space-sm);
            }
        }
    `,
    ];

    private _emit(action: ChatControlAction) {
        this.dispatchEvent(new CustomEvent('soma-chat-control', {
            detail: { action },
            bubbles: true,
            composed: true,
        }));
    }

    private _connLabel(): string {
        return this.connectionStatus === 'reconnecting' ? 'Reconnecting…' : 'Connection degraded';
    }

    render() {
        return html`
            <div class="title-block">
                <div class="title">${this.title || 'Chat'}</div>
                <div class="meta">
                    ${this.modelLabel ? html`
                        <span class="model-label" title="Active model">
                            <span class="material-symbols-outlined">memory</span>
                            ${this.modelLabel}
                        </span>
                    ` : nothing}
                    ${this.paused
                        ? html`<span class="status-pill paused">
                              <span class="material-symbols-outlined">pause</span>
                              Paused
                          </span>`
                        : this.busy
                            ? html`<span class="status-pill running">
                                  <span class="material-symbols-outlined">bolt</span>
                                  Running
                              </span>`
                            : nothing}
                    ${this.connectionStatus !== 'ok' ? html`
                        <span
                            class="conn-chip ${this.connectionStatus}"
                            role="status"
                            title=${this._connLabel()}
                        >
                            <span class="dot"></span>
                            ${this._connLabel()}
                        </span>
                    ` : nothing}
                </div>
            </div>

            <div class="controls" role="group" aria-label="Chat controls">
                <button
                    class="ctl-btn"
                    @click=${() => this._emit(this.paused ? 'resume' : 'pause')}
                    ?disabled=${!this.busy && !this.paused}
                    title=${this.paused ? 'Resume rendering of the stream' : 'Pause rendering of the stream'}
                    aria-label=${this.paused ? 'Resume' : 'Pause'}
                >
                    <span class="material-symbols-outlined">${this.paused ? 'play_arrow' : 'pause'}</span>
                    <span class="label">${this.paused ? 'Resume' : 'Pause'}</span>
                </button>

                <button
                    class="ctl-btn"
                    @click=${() => this._emit('nudge')}
                    ?disabled=${!this.canNudge}
                    title=${this.nudgeTitle}
                    aria-label="Nudge"
                >
                    <span class="material-symbols-outlined">waving_hand</span>
                    <span class="label">Nudge</span>
                </button>

                <button
                    class="ctl-btn stop"
                    @click=${() => this._emit('stop')}
                    ?disabled=${!this.busy}
                    title="Stop the current turn"
                    aria-label="Stop"
                >
                    <span class="material-symbols-outlined">stop</span>
                    <span class="label">Stop</span>
                </button>

                <button
                    class="ctl-btn reset"
                    @click=${() => this._emit('reset')}
                    title="Reset chat — start a fresh conversation"
                    aria-label="Reset"
                >
                    <span class="material-symbols-outlined">restart_alt</span>
                    <span class="label">Reset</span>
                </button>

                <button
                    class="ctl-btn"
                    data-testid="chat-settings-btn"
                    @click=${() => this._emit('chat-settings')}
                    title="Chat settings — tools, chain of thought, timestamps"
                    aria-label="Chat settings"
                >
                    <span class="material-symbols-outlined">tune</span>
                    <span class="label">Display</span>
                </button>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-chat-topbar': SomaChatTopbar;
    }
}
