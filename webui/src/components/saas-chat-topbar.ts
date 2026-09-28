/**
 * SomaAgent01 — Chat topbar (CH-04 / C4).
 *
 * Title + model label + connection status chip (only when degraded)
 * + pause / stop / reset controls with Material Symbols icons.
 * Buttons dispatch `saas-chat-control` CustomEvents; the host view wires
 * them to the real transport (WS / REST).
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property } from 'lit/decorators.js';

export type ChatControlAction = 'pause' | 'resume' | 'nudge' | 'stop' | 'reset';
export type ConnectionStatus = 'ok' | 'reconnecting' | 'degraded';

@customElement('saas-chat-topbar')
export class SaasChatTopbar extends LitElement {
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
    @property({ type: String }) nudgeTitle = 'Nudge requires orchestrator interrupt (not yet available on the gateway)';

    static styles = css`
        :host {
            display: flex;
            align-items: center;
            gap: 16px;
            width: 100%;
            min-width: 0;
        }

        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: 18px;
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
            gap: 3px;
            min-width: 0;
            flex: 1;
        }

        .title {
            font-size: 15px;
            font-weight: 600;
            color: var(--aaas-text-bright, #f8fafc);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .meta {
            display: flex;
            align-items: center;
            gap: 8px;
            min-height: 20px;
        }

        .model-label {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-family: var(--aaas-font-mono, 'JetBrains Mono', monospace);
            font-size: 11px;
            color: var(--aaas-text-secondary, #a1a1a1);
            padding: 2px 8px;
            border-radius: var(--aaas-radius-full, 9999px);
            background: var(--aaas-bg-void, #f5f5f5);
            border: 1px solid var(--aaas-border-color, rgba(255,255,255,0.06));
            max-width: 220px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .model-label .material-symbols-outlined {
            font-size: 12px;
            opacity: 0.7;
        }

        /* Status pills — running/paused are turn state; connection is health */
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 2px 8px;
            border-radius: var(--aaas-radius-full, 9999px);
        }

        .status-pill.running {
            color: var(--aaas-success, #22c55e);
            background: rgba(34, 197, 94, 0.12);
        }

        .status-pill.paused {
            color: var(--aaas-warning, #eab308);
            background: rgba(234, 179, 8, 0.12);
        }

        .conn-chip {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 11px;
            padding: 3px 10px;
            border-radius: var(--aaas-radius-full, 9999px);
            border: 1px solid transparent;
            animation: chipIn 160ms ease-out;
        }

        @keyframes chipIn {
            from { opacity: 0; transform: translateY(-2px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .conn-chip.reconnecting {
            color: var(--aaas-warning, #f59e0b);
            background: rgba(245, 158, 11, 0.12);
            border-color: rgba(245, 158, 11, 0.28);
        }

        .conn-chip.degraded {
            color: var(--aaas-danger, #ef4444);
            background: rgba(239, 68, 68, 0.12);
            border-color: rgba(239, 68, 68, 0.28);
        }

        .conn-chip .dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
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
            gap: 6px;
            flex-shrink: 0;
        }

        .ctl-btn {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 6px 12px;
            border-radius: var(--aaas-radius-md, 8px);
            border: 1px solid var(--aaas-border-color, rgba(255,255,255,0.06));
            background: var(--aaas-surface, rgba(30,41,59,0.85));
            color: var(--aaas-text-main, #e2e8f0);
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 120ms ease;
            white-space: nowrap;
        }

        .ctl-btn:hover:not(:disabled) {
            background: var(--aaas-surface-hover, rgba(51,65,85,0.9));
            border-color: var(--aaas-border-hover, rgba(255,255,255,0.1));
        }

        .ctl-btn:focus-visible {
            outline: 2px solid var(--aaas-info, #3b82f6);
            outline-offset: 2px;
        }

        .ctl-btn:disabled {
            opacity: 0.4;
            cursor: not-allowed;
        }

        .ctl-btn.stop {
            color: var(--aaas-danger, #ef4444);
            border-color: rgba(239, 68, 68, 0.35);
        }

        .ctl-btn.stop:hover:not(:disabled) {
            background: rgba(239, 68, 68, 0.12);
        }

        .ctl-btn.reset {
            color: var(--aaas-text-dim, #64748b);
        }

        .ctl-btn .material-symbols-outlined {
            font-size: 16px;
        }

        @media (max-width: 720px) {
            .ctl-btn .label {
                display: none;
            }
            .ctl-btn {
                padding: 6px 8px;
            }
        }
    `;

    private _emit(action: ChatControlAction) {
        this.dispatchEvent(new CustomEvent('saas-chat-control', {
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
                              <span class="material-symbols-outlined" style="font-size:11px">pause</span>
                              Paused
                          </span>`
                        : this.busy
                            ? html`<span class="status-pill running">
                                  <span class="material-symbols-outlined" style="font-size:11px">bolt</span>
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
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'saas-chat-topbar': SaasChatTopbar;
    }
}
