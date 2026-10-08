/**
 * SomaAgent01 — ambient status micro-indicator (Brain / Sync / Memory).
 *
 * 12px circle, A0 sync-status language: filled disc (ok/warn) or stroked ring
 * (pending/bad). Tooltip on hover + aria-label for AT. Never a banner.
 */

import { LitElement, html, css, nothing } from 'lit';
import { customElement, property } from 'lit/decorators.js';

export type StatusDotState = 'ok' | 'warn' | 'pending' | 'bad' | 'idle';

@customElement('soma-status-dot')
export class SomaStatusDot extends LitElement {
    @property({ type: String }) state: StatusDotState = 'idle';
    @property({ type: String }) label = '';
    @property({ type: String }) title = '';
    @property({ type: String }) kind: 'brain' | 'sync' | 'memory' = 'brain';

    static styles = css`
        :host {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 18px;
            height: 18px;
            cursor: default;
            vertical-align: middle;
        }
        :host([interactive]) {
            cursor: pointer;
        }
        svg {
            display: block;
            overflow: visible;
        }
        .pending-ring {
            animation: pendingPulse 1.2s infinite ease-in-out;
        }
        @keyframes pendingPulse {
            0% {
                stroke-opacity: 1;
                stroke-width: 3;
            }
            50% {
                stroke-opacity: 0.25;
                stroke-width: 5;
            }
            100% {
                stroke-opacity: 1;
                stroke-width: 3;
            }
        }
    `;

    private get colors(): { fill: string; stroke: string } {
        switch (this.state) {
            case 'ok':
                return { fill: '#10B981', stroke: 'transparent' };
            case 'warn':
                return { fill: '#F59E0B', stroke: 'transparent' };
            case 'pending':
                return { fill: 'none', stroke: '#FBBF24' };
            case 'bad':
                return { fill: 'none', stroke: '#F43F5E' };
            default:
                return { fill: 'none', stroke: '#64748B' };
        }
    }

    private get tooltip(): string {
        return this.title || this.label || this.kind;
    }

    render() {
        const c = this.colors;
        const filled = this.state === 'ok' || this.state === 'warn';
        const r = filled ? 6 : 7;
        return html`
            <svg
                viewBox="0 0 30 30"
                width="12"
                height="12"
                role="img"
                aria-label=${this.tooltip}
                class=${this.state === 'pending' ? 'pending-ring' : nothing}
            >
                <circle
                    cx="15"
                    cy="15"
                    r=${r}
                    fill=${c.fill}
                    stroke=${c.stroke}
                    stroke-width=${this.state === 'bad' || this.state === 'pending' ? 3 : 0}
                />
            </svg>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        'soma-status-dot': SomaStatusDot;
    }
}
